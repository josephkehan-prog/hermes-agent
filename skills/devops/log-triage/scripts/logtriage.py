#!/usr/bin/env python3
"""Parse, classify, and summarize log files for incident triage. stdlib only,
no network, no shell-out.

Subcommands:
    scan <logfile> [--since-lines N] [--level LEVEL]
        Tail the last N lines, classify each by severity, count by level,
        and extract matching lines (ERROR+FATAL by default, or a single
        --level).
    cluster <logfile> [--since-lines N] [--top-n N]
        Tail the last N lines, group ERROR/FATAL lines into templates by
        normalizing numbers/UUIDs/timestamps, report the top-N templates
        by frequency.
    summary <logfile> [--since-lines N]
        scan + cluster combined into one compact JSON incident summary:
        level counts, top error templates, and the log's time span.

The log file is never fully loaded into memory — reading is capped at
MAX_LOG_BYTES and seeks from the end, so a multi-gigabyte file only ever
costs the last chunk. Exits 2 on any validation or read error.
"""
import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

MAX_LOG_BYTES = 50_000_000
CHUNK_SIZE_BYTES = 65_536
DEFAULT_TAIL_LINES = 200
DEFAULT_TOP_N = 10
MAX_MATCHES_RETURNED = 500

VALID_LEVELS = ("DEBUG", "INFO", "WARN", "ERROR", "FATAL")

# Checked in this order — most severe first — so a line matching more than
# one keyword (rare, but "ERROR" appearing inside an INFO-level message
# about a past error) still gets the more severe classification.
LEVEL_ALIASES = {
    "FATAL": ("FATAL", "CRITICAL", "CRIT", "PANIC", "EMERGENCY", "EMERG"),
    "ERROR": ("ERROR", "ERR", "SEVERE"),
    "WARN": ("WARN", "WARNING"),
    "INFO": ("INFO", "NOTICE"),
    "DEBUG": ("DEBUG", "TRACE"),
}
_LEVEL_PATTERNS = {
    level: re.compile(r"\b(?:" + "|".join(aliases) + r")\b", re.IGNORECASE)
    for level, aliases in LEVEL_ALIASES.items()
}
_JSON_ALIAS_TO_LEVEL = {
    alias.upper(): level for level, aliases in LEVEL_ALIASES.items() for alias in aliases
}
_JSON_LEVEL_KEYS = ("level", "severity", "loglevel", "log_level")

_TS_RE = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?")
_SYSLOG_TS_RE = re.compile(r"^[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}")
_UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
_HEX_RE = re.compile(r"\b0x[0-9a-fA-F]+\b")
_NUM_RE = re.compile(r"\b\d+\b")


def _fail(message):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(2)


def validate_log_path(raw_path):
    """Resolve raw_path and confirm it's a readable regular file.

    Rejects missing paths, directories, and non-regular files (FIFOs,
    sockets, devices) — Path.is_file() follows symlinks but only reports
    True for a regular file, which is exactly the check we want here since
    the path is caller-supplied and this tool never shells out.
    """
    path = Path(raw_path)
    if not path.exists():
        _fail(f"path not found: {raw_path}")
    resolved = path.resolve()
    if resolved.is_dir():
        _fail(f"path is a directory, not a log file: {raw_path}")
    if not resolved.is_file():
        _fail(f"not a regular file (device/fifo/socket?): {raw_path}")
    if not os.access(resolved, os.R_OK):
        _fail(f"file is not readable: {raw_path}")
    return resolved


def tail_lines(path, max_lines, max_bytes=MAX_LOG_BYTES):
    """Read at most the last max_lines lines, never reading more than
    max_bytes from the end of the file regardless of its total size."""
    with open(path, "rb") as handle:
        handle.seek(0, os.SEEK_END)
        remaining = handle.tell()
        data = b""
        bytes_read = 0
        while remaining > 0 and bytes_read < max_bytes and data.count(b"\n") <= max_lines:
            read_size = min(CHUNK_SIZE_BYTES, remaining, max_bytes - bytes_read)
            remaining -= read_size
            handle.seek(remaining)
            data = handle.read(read_size) + data
            bytes_read += read_size
    text = data.decode("utf-8", errors="replace")
    lines = text.splitlines()
    return lines[-max_lines:] if len(lines) > max_lines else lines


def _extract_json_level(line):
    stripped = line.strip()
    if not stripped.startswith("{"):
        return None
    try:
        payload = json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    for key in _JSON_LEVEL_KEYS:
        value = payload.get(key)
        if isinstance(value, str):
            level = _JSON_ALIAS_TO_LEVEL.get(value.strip().upper())
            if level:
                return level
    return None


def classify_severity(line):
    json_level = _extract_json_level(line)
    if json_level:
        return json_level
    for level in ("FATAL", "ERROR", "WARN", "INFO", "DEBUG"):
        if _LEVEL_PATTERNS[level].search(line):
            return level
    return "UNKNOWN"


def normalize_template(line):
    """Collapse numbers/UUIDs/hex addrs/timestamps to placeholders so
    repeated errors that only differ by an ID or clock tick cluster
    together under one template."""
    text = _TS_RE.sub("<TS>", line)
    text = _UUID_RE.sub("<UUID>", text)
    text = _HEX_RE.sub("<HEX>", text)
    text = _NUM_RE.sub("<NUM>", text)
    return text


def cluster_lines(lines, top_n=DEFAULT_TOP_N):
    error_lines = [line for line in lines if classify_severity(line) in ("ERROR", "FATAL")]
    counts = Counter()
    examples = {}
    for line in error_lines:
        template = normalize_template(line)
        counts[template] += 1
        examples.setdefault(template, line)
    return [
        {"template": template, "count": count, "example": examples[template]}
        for template, count in counts.most_common(top_n)
    ]


def _find_timestamp(line):
    match = _TS_RE.search(line)
    if match:
        return match.group(0)
    match = _SYSLOG_TS_RE.match(line)
    return match.group(0) if match else None


def extract_time_span(lines):
    start = next((ts for ts in map(_find_timestamp, lines) if ts), None)
    end = next((ts for ts in map(_find_timestamp, reversed(lines)) if ts), None)
    if start is None and end is None:
        return None
    return {"start": start, "end": end}


def cmd_scan(args):
    path = validate_log_path(args.logfile)
    lines = tail_lines(path, args.since_lines)
    counts = Counter(classify_severity(line) for line in lines)

    level_filter = args.level.upper() if args.level else None
    if level_filter and level_filter not in VALID_LEVELS:
        _fail(f"--level must be one of {VALID_LEVELS}, got {args.level!r}")
    wanted_levels = (level_filter,) if level_filter else ("ERROR", "FATAL")
    matches = [line for line in lines if classify_severity(line) in wanted_levels]

    print(json.dumps({
        "file": str(path),
        "lines_scanned": len(lines),
        "counts": dict(counts),
        "matches": matches[:MAX_MATCHES_RETURNED],
    }, indent=2))


def cmd_cluster(args):
    path = validate_log_path(args.logfile)
    lines = tail_lines(path, args.since_lines)
    clusters = cluster_lines(lines, top_n=args.top_n)
    print(json.dumps({"file": str(path), "lines_scanned": len(lines), "clusters": clusters}, indent=2))


def cmd_summary(args):
    path = validate_log_path(args.logfile)
    lines = tail_lines(path, args.since_lines)
    counts = Counter(classify_severity(line) for line in lines)
    clusters = cluster_lines(lines, top_n=5)

    print(json.dumps({
        "file": str(path),
        "lines_scanned": len(lines),
        "counts": dict(counts),
        "top_errors": clusters,
        "time_span": extract_time_span(lines),
    }, indent=2))


def build_parser():
    parser = argparse.ArgumentParser(description="Parse, classify, and summarize log files for incident triage.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="classify and count log lines by severity")
    scan_parser.add_argument("logfile")
    scan_parser.add_argument("--since-lines", type=int, default=DEFAULT_TAIL_LINES, help="how many trailing lines to read")
    scan_parser.add_argument("--level", help="only extract lines at this severity (default: ERROR+FATAL)")
    scan_parser.set_defaults(func=cmd_scan)

    cluster_parser = subparsers.add_parser("cluster", help="group similar error lines into templates")
    cluster_parser.add_argument("logfile")
    cluster_parser.add_argument("--since-lines", type=int, default=DEFAULT_TAIL_LINES, help="how many trailing lines to read")
    cluster_parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N, help="how many templates to report")
    cluster_parser.set_defaults(func=cmd_cluster)

    summary_parser = subparsers.add_parser("summary", help="scan + cluster combined into one incident summary")
    summary_parser.add_argument("logfile")
    summary_parser.add_argument("--since-lines", type=int, default=DEFAULT_TAIL_LINES, help="how many trailing lines to read")
    summary_parser.set_defaults(func=cmd_summary)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
