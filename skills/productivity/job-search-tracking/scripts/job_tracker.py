#!/usr/bin/env python3
"""Local, dependency-free job application tracker (CSV-backed).

No cloud API, no account. State lives in a single CSV file under
$HERMES_HOME/job-search/applications.csv (default ~/.hermes/job-search/).
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import fcntl
import os
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

FIELDS = [
    "id", "date_applied", "company", "role", "url", "status",
    "remote", "cert_required", "next_action", "next_action_date", "notes",
]
VALID_STATUS = ["saved", "applied", "screen", "interview", "offer", "rejected", "withdrawn"]


def data_path() -> Path:
    home = os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))
    p = Path(home) / "job-search" / "applications.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


@contextlib.contextmanager
def locked(path: Path):
    """Exclusive advisory lock guarding read-modify-write on the CSV file."""
    lock_path = Path(str(path) + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "w") as lockfile:
        fcntl.flock(lockfile, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lockfile, fcntl.LOCK_UN)


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save(path: Path, rows: list[dict]) -> None:
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=".csv")
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        os.replace(tmp_name, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp_name)
        raise


def cmd_init(args: argparse.Namespace) -> None:
    path = data_path()
    if not path.exists():
        save(path, [])
    print(f"ready: {path}")


def cmd_add(args: argparse.Namespace) -> None:
    path = data_path()
    with locked(path):
        rows = load(path)
        new_id = str(max((int(r["id"]) for r in rows if r["id"].isdigit()), default=0) + 1)
        row = {
            "id": new_id,
            "date_applied": args.date or date.today().isoformat(),
            "company": args.company,
            "role": args.role,
            "url": args.url or "",
            "status": args.status,
            "remote": "yes" if args.remote else "no",
            "cert_required": "yes" if args.cert_required else "no",
            "next_action": args.next_action or "",
            "next_action_date": args.next_action_date or "",
            "notes": args.notes or "",
        }
        rows.append(row)
        save(path, rows)
    print(f"added #{new_id}: {args.company} - {args.role}")


def cmd_update(args: argparse.Namespace) -> None:
    path = data_path()
    with locked(path):
        rows = load(path)
        for r in rows:
            if r["id"] == args.id:
                for field in ("status", "next_action", "next_action_date", "notes", "url"):
                    val = getattr(args, field)
                    if val is not None:
                        r[field] = val
                save(path, rows)
                print(f"updated #{args.id}")
                return
    sys.exit(f"no application with id {args.id}")


def cmd_list(args: argparse.Namespace) -> None:
    rows = load(data_path())
    if args.status:
        rows = [r for r in rows if r["status"] == args.status]
    if args.upcoming is not None:
        cutoff = date.today() + timedelta(days=args.upcoming)
        filtered = []
        for r in rows:
            if not r["next_action_date"]:
                continue
            try:
                nad = date.fromisoformat(r["next_action_date"])
            except ValueError:
                print(
                    f"warning: skipping #{r.get('id', '?')} with malformed "
                    f"next_action_date {r['next_action_date']!r}",
                    file=sys.stderr,
                )
                continue
            if nad <= cutoff:
                filtered.append(r)
        rows = filtered
    if not rows:
        print("(no matching applications)")
        return
    for r in rows:
        na = f" -> {r['next_action']} by {r['next_action_date']}" if r["next_action"] else ""
        print(f"#{r['id']:>3} [{r['status']:<10}] {r['company']} - {r['role']} ({r['date_applied']}){na}")


def cmd_stats(args: argparse.Namespace) -> None:
    rows = load(data_path())
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    total = len(rows)
    print(f"total: {total}")
    for status in VALID_STATUS:
        if counts.get(status):
            print(f"  {status:<10} {counts[status]}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="Create the CSV file if missing").set_defaults(func=cmd_init)

    a = sub.add_parser("add", help="Log a new application")
    a.add_argument("--company", required=True)
    a.add_argument("--role", required=True)
    a.add_argument("--url", default=None)
    a.add_argument("--status", default="applied", choices=VALID_STATUS)
    a.add_argument("--date", default=None, help="date_applied, YYYY-MM-DD (default today)")
    a.add_argument("--remote", action="store_true", default=True)
    a.add_argument("--no-remote", dest="remote", action="store_false")
    a.add_argument("--cert-required", action="store_true", default=False)
    a.add_argument("--next-action", default=None)
    a.add_argument("--next-action-date", default=None, help="YYYY-MM-DD")
    a.add_argument("--notes", default=None)
    a.set_defaults(func=cmd_add)

    u = sub.add_parser("update", help="Update status / next action on an existing row")
    u.add_argument("id")
    u.add_argument("--status", default=None, choices=VALID_STATUS)
    u.add_argument("--next-action", default=None)
    u.add_argument("--next-action-date", default=None)
    u.add_argument("--notes", default=None)
    u.add_argument("--url", default=None)
    u.set_defaults(func=cmd_update)

    l = sub.add_parser("list", help="List applications")
    l.add_argument("--status", default=None, choices=VALID_STATUS)
    l.add_argument("--upcoming", type=int, default=None, metavar="DAYS",
                    help="Only rows with next_action_date within DAYS")
    l.set_defaults(func=cmd_list)

    sub.add_parser("stats", help="Counts by status").set_defaults(func=cmd_stats)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
