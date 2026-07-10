#!/usr/bin/env python3
"""evidence_check.py — anti-hallucination gate for OSINT reports (stdlib only).

Local models (ornith 35B et al.) can invent names, employers, URLs, emails, and
handles that were never in a fetched payload. This checker extracts every
concrete factual token from a drafted report and flags any that do NOT appear in
the collected evidence corpus. Run it BEFORE emitting an OSINT report.

Usage:
    evidence_check.py --report report.md --evidence <file-or-dir> [more...]
    cat report.md | evidence_check.py --evidence ./evidence/ --stdin

Evidence sources: any .json / .txt / .md / .html files (footprint.py --json
output, saved page text, dork-hit dumps). All are concatenated case-folded into
one haystack; a report token is "supported" if it appears there verbatim.

Exit codes: 0 = every factual token supported (or none found); 2 = one or more
UNSUPPORTED tokens (likely hallucinated — verify or delete before shipping).

This is a guard, not proof: it catches invented *specifics*. It cannot vouch for
a claim's truth, only that the specific string was actually fetched. Narrative
sentences with no concrete token are not checked — keep claims concrete.
"""
import argparse
import json
import re
import sys
from pathlib import Path

# Factual-token extractors. Each returns a list of (kind, raw) from report text.
URL_RE = re.compile(r"https?://[^\s)\]\"'<>]+", re.I)
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
HANDLE_RE = re.compile(r"(?<![\w@])@([A-Za-z0-9_]{2,30})\b")
PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
# Proper nouns: 2+ consecutive Capitalized words (candidate person/org/place).
PROPER_RE = re.compile(r"\b([A-Z][a-z]{1,}(?:[ \t]+[A-Z][a-z]{1,}){1,3})\b")

# Report scaffolding words that start capitalized but are not evidence claims.
STOPWORDS = {
    "executive summary", "primary findings", "extended intelligence",
    "geographic distribution", "actionable recommendations", "key patterns",
    "social media", "professional network", "cross platform", "deep path",
    "open source", "digital footprint", "not found", "no match", "manual check",
    "sherlock layer", "confidence level", "united states", "new york",
}


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().casefold()


def strip_url_scheme(u: str) -> str:
    return re.sub(r"^https?://(www\.)?", "", u.casefold()).rstrip("/")


def load_evidence(paths):
    exts = {".json", ".txt", ".md", ".html", ".htm", ".log"}
    chunks = []
    files = []
    for p in paths:
        pp = Path(p)
        if pp.is_dir():
            files.extend(f for f in pp.rglob("*") if f.suffix.lower() in exts)
        elif pp.is_file():
            files.append(pp)
        else:
            print(f"warning: evidence path not found: {p}", file=sys.stderr)
    for f in files:
        try:
            chunks.append(f.read_text(errors="replace"))
        except OSError as e:
            print(f"warning: cannot read {f}: {e}", file=sys.stderr)
    return normalize(" ".join(chunks)), len(files)


def extract_tokens(report: str):
    tokens = []
    for m in URL_RE.finditer(report):
        tokens.append(("url", m.group(0).rstrip(".,);]")))
    for m in EMAIL_RE.finditer(report):
        tokens.append(("email", m.group(0)))
    for m in HANDLE_RE.finditer(report):
        tokens.append(("handle", m.group(1)))
    for m in PHONE_RE.finditer(report):
        tokens.append(("phone", m.group(0)))
    for m in PROPER_RE.finditer(report):
        raw = m.group(1)
        if normalize(raw) not in STOPWORDS:
            tokens.append(("name", raw))
    return tokens


def supported(kind: str, raw: str, hay: str) -> bool:
    if kind == "url":
        return strip_url_scheme(raw) in hay or normalize(raw) in hay
    if kind == "phone":
        digits = re.sub(r"\D", "", raw)
        return digits in re.sub(r"\D", "", hay) if digits else True
    return normalize(raw) in hay


def line_of(report: str, raw: str) -> int:
    for i, ln in enumerate(report.splitlines(), 1):
        if raw in ln:
            return i
    return 0


def main():
    ap = argparse.ArgumentParser(description="Anti-hallucination gate for OSINT reports.")
    ap.add_argument("--report", help="drafted report file (markdown/text)")
    ap.add_argument("--stdin", action="store_true", help="read report from stdin")
    ap.add_argument("--evidence", nargs="+", required=True,
                    help="evidence file(s) or dir(s): fetched json/txt/md/html")
    ap.add_argument("--json", action="store_true", help="emit JSON verdict")
    args = ap.parse_args()

    if args.stdin:
        report = sys.stdin.read()
    elif args.report:
        report = Path(args.report).read_text(errors="replace")
    else:
        ap.error("provide --report FILE or --stdin")

    hay, nfiles = load_evidence(args.evidence)
    if not hay:
        print("ERROR: evidence corpus is empty — cannot verify anything.", file=sys.stderr)
        return 2

    seen = set()
    unsupported = []
    checked = 0
    for kind, raw in extract_tokens(report):
        key = (kind, normalize(raw))
        if key in seen:
            continue
        seen.add(key)
        checked += 1
        if not supported(kind, raw, hay):
            unsupported.append({"kind": kind, "token": raw, "line": line_of(report, raw)})

    if args.json:
        print(json.dumps({
            "evidence_files": nfiles, "tokens_checked": checked,
            "unsupported": unsupported,
            "verdict": "PASS" if not unsupported else "UNSUPPORTED_FOUND",
        }, indent=2))
    else:
        print(f"evidence files: {nfiles} | factual tokens checked: {checked}")
        if not unsupported:
            print("PASS — every concrete token appears in fetched evidence.")
        else:
            print(f"UNSUPPORTED ({len(unsupported)}) — NOT in any fetched payload; "
                  "verify against a live source or delete before shipping:")
            for u in unsupported:
                loc = f"L{u['line']}" if u["line"] else "?"
                print(f"  [{u['kind']:5}] {loc}: {u['token']}")
    return 2 if unsupported else 0


if __name__ == "__main__":
    sys.exit(main())
