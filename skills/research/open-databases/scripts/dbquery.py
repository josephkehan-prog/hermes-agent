#!/usr/bin/env python3
"""dbquery.py -- keyless CLI for free public research databases.

Subcommands: openalex, crossref, wikidata, edgar, wayback.
Stdlib only (json, sqlite3, urllib). See scripts/README.md for usage.
"""
import argparse
import json
import re
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request

MAILTO = "research-agent@example.com"  # replace with a real contact address before heavy use
USER_AGENT = f"open-databases-skill/1.0 (mailto:{MAILTO})"
TIMEOUT_SECONDS = 20
TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
QUERY_FILE_EXTENSIONS = (".rq", ".sparql")
_MAX_RESPONSE_BYTES = 10_000_000

OPENALEX_WORKS = "https://api.openalex.org/works"
OPENALEX_AUTHORS = "https://api.openalex.org/authors"
CROSSREF_WORKS = "https://api.crossref.org/works"
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
EDGAR_FULLTEXT = "https://efts.sec.gov/LATEST/search-index"
WAYBACK_CDX = "https://web.archive.org/cdx/search/cdx"


def fetch_json(url, headers=None):
    """GET url and return parsed JSON. Exits 2 on any network/parse failure."""
    request_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(url, headers=request_headers)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read(_MAX_RESPONSE_BYTES + 1)
            if len(raw) > _MAX_RESPONSE_BYTES:
                print(f"error: response exceeds {_MAX_RESPONSE_BYTES} bytes for {url}", file=sys.stderr)
                sys.exit(2)
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(f"error: HTTP {exc.code} for {url}", file=sys.stderr)
        sys.exit(2)
    except urllib.error.URLError as exc:
        print(f"error: request failed for {url}: {exc.reason}", file=sys.stderr)
        sys.exit(2)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"error: invalid response from {url}: {exc}", file=sys.stderr)
        sys.exit(2)


def print_table(rows, columns):
    """Print rows (list of dicts) as a compact aligned table, or a placeholder if empty."""
    if not rows:
        print("(no results)")
        return
    widths = {c: max(len(c), max(len(str(r.get(c, ""))) for r in rows)) for c in columns}
    print("  ".join(c.ljust(widths[c]) for c in columns))
    print("  ".join("-" * widths[c] for c in columns))
    for row in rows:
        print("  ".join(str(row.get(c, "")).ljust(widths[c]) for c in columns))


def dump_sqlite(path, table, rows, columns):
    """Insert rows into an SQLite table via parameterized INSERTs only.

    Table name is validated against TABLE_NAME_RE; column names come from
    our own fixed per-source schemas below, never from user input.
    """
    if not TABLE_NAME_RE.match(table):
        print(f"error: invalid --table name {table!r}", file=sys.stderr)
        sys.exit(2)
    connection = sqlite3.connect(path)
    try:
        column_defs = ", ".join(f'"{c}" TEXT' for c in columns)
        connection.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({column_defs})')
        column_names = ", ".join(f'"{c}"' for c in columns)
        placeholders = ", ".join("?" for _ in columns)
        insert_sql = f'INSERT INTO "{table}" ({column_names}) VALUES ({placeholders})'
        values = [tuple(str(row.get(c, "")) for c in columns) for row in rows]
        connection.executemany(insert_sql, values)
        connection.commit()
    finally:
        connection.close()
    print(f"wrote {len(rows)} row(s) to {path}::{table}")


def cmd_openalex(args):
    """Search OpenAlex works or authors by keyword."""
    base = OPENALEX_WORKS if args.type == "works" else OPENALEX_AUTHORS
    params = {"search": args.query, "per-page": str(args.limit), "mailto": MAILTO}
    url = f"{base}?{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"
    data = fetch_json(url)
    if not isinstance(data, dict):
        print("error: unexpected OpenAlex response shape", file=sys.stderr)
        sys.exit(2)
    results = data.get("results", [])
    if not isinstance(results, list):
        print("error: unexpected OpenAlex response shape", file=sys.stderr)
        sys.exit(2)
    if args.type == "works":
        columns = ["id", "display_name", "publication_year", "cited_by_count", "doi"]
        rows = [{c: w.get(c, "") for c in columns} for w in results if isinstance(w, dict)]
    else:
        columns = ["id", "display_name", "works_count", "cited_by_count"]
        rows = [{c: a.get(c, "") for c in columns} for a in results if isinstance(a, dict)]
    return rows, columns


def cmd_crossref(args):
    """Search Crossref works by keyword."""
    params = {"query": args.query, "rows": str(args.limit), "mailto": MAILTO}
    url = f"{CROSSREF_WORKS}?{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"
    data = fetch_json(url)
    if not isinstance(data, dict):
        print("error: unexpected Crossref response shape", file=sys.stderr)
        sys.exit(2)
    message = data.get("message", {})
    items = message.get("items", []) if isinstance(message, dict) else []
    columns = ["doi", "title", "published", "type"]
    rows = []
    for item in items:
        if not isinstance(item, dict):
            continue
        title = "; ".join(item.get("title", []))
        parts = item.get("published", {}).get("date-parts", [[]])[0]
        published = "-".join(str(p) for p in parts)
        rows.append({
            "doi": item.get("DOI", ""),
            "title": title,
            "published": published,
            "type": item.get("type", ""),
        })
    return rows, columns


def read_query_file(path):
    """Read a SPARQL query from path. Exits 2 if the extension isn't .rq/.sparql."""
    if not path.endswith(QUERY_FILE_EXTENSIONS):
        print(f"error: --query-file must end in {QUERY_FILE_EXTENSIONS}, got {path!r}", file=sys.stderr)
        sys.exit(2)
    with open(path, encoding="utf-8") as f:
        return f.read()


def cmd_wikidata(args):
    """Run a SPARQL query: the positional arg is always a literal query string.

    Pass --query-file to load the query from a .rq/.sparql file instead.
    """
    if not args.query_file and not args.query:
        print("error: provide a SPARQL query string or --query-file", file=sys.stderr)
        sys.exit(2)
    query_text = read_query_file(args.query_file) if args.query_file else args.query
    params = {"query": query_text, "format": "json"}
    url = f"{WIKIDATA_SPARQL}?{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"
    data = fetch_json(url, headers={"Accept": "application/sparql-results+json"})
    if not isinstance(data, dict):
        print("error: unexpected Wikidata response shape", file=sys.stderr)
        sys.exit(2)
    head = data.get("head", {})
    variables = head.get("vars", []) if isinstance(head, dict) else []
    results_block = data.get("results", {})
    bindings = results_block.get("bindings", []) if isinstance(results_block, dict) else []
    rows = []
    for binding in bindings:
        if not isinstance(binding, dict):
            continue
        rows.append({v: binding.get(v, {}).get("value", "") for v in variables})
    return rows, variables


def cmd_edgar(args):
    """Full-text search of SEC EDGAR filings for a company/keyword."""
    params = {"q": args.query}
    if args.forms:
        params["forms"] = args.forms
    url = f"{EDGAR_FULLTEXT}?{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"
    data = fetch_json(url)
    if not isinstance(data, dict):
        print("error: unexpected EDGAR response shape", file=sys.stderr)
        sys.exit(2)
    hits_block = data.get("hits", {})
    hits = hits_block.get("hits", []) if isinstance(hits_block, dict) else []
    columns = ["form", "display_names", "file_date", "adsh"]
    rows = []
    for hit in hits[: args.limit]:
        if not isinstance(hit, dict):
            continue
        source = hit.get("_source", {})
        rows.append({
            "form": source.get("form", ""),
            "display_names": "; ".join(source.get("display_names", [])),
            "file_date": source.get("file_date", ""),
            "adsh": source.get("adsh", ""),
        })
    return rows, columns


def cmd_wayback(args):
    """List Wayback Machine snapshots for a URL via the CDX API."""
    params = {"url": args.url, "output": "json", "limit": str(args.limit)}
    url = f"{WAYBACK_CDX}?{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"
    data = fetch_json(url)
    columns = ["timestamp", "original", "statuscode", "digest"]
    if not data:
        return [], columns
    if not isinstance(data, list):
        print("error: unexpected Wayback CDX response shape", file=sys.stderr)
        sys.exit(2)
    header, *records = data
    rows = [dict(zip(header, record)) for record in records]
    return rows, columns


def add_sqlite_args(subparser):
    """Attach the shared --sqlite/--table dump flags to a subcommand parser."""
    subparser.add_argument("--sqlite", help="SQLite file to dump results into")
    subparser.add_argument("--table", help="Table name (required with --sqlite)")


def build_parser():
    parser = argparse.ArgumentParser(description="Query free, keyless public research databases.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_openalex = subparsers.add_parser("openalex", help="Search OpenAlex works/authors")
    p_openalex.add_argument("query")
    p_openalex.add_argument("--type", choices=["works", "authors"], default="works")
    p_openalex.add_argument("--limit", type=int, default=5)
    add_sqlite_args(p_openalex)

    p_crossref = subparsers.add_parser("crossref", help="Search Crossref works")
    p_crossref.add_argument("query")
    p_crossref.add_argument("--limit", type=int, default=5)
    add_sqlite_args(p_crossref)

    p_wikidata = subparsers.add_parser("wikidata", help="Run a Wikidata SPARQL query")
    p_wikidata.add_argument("query", nargs="?", default=None, help="Literal SPARQL query string")
    p_wikidata.add_argument("--query-file", help="Path to a .rq/.sparql file containing the query")
    add_sqlite_args(p_wikidata)

    p_edgar = subparsers.add_parser("edgar", help="Full-text search SEC EDGAR filings")
    p_edgar.add_argument("query")
    p_edgar.add_argument("--forms", help="Comma-separated form types, e.g. 10-K,10-Q")
    p_edgar.add_argument("--limit", type=int, default=10)
    add_sqlite_args(p_edgar)

    p_wayback = subparsers.add_parser("wayback", help="List Wayback Machine snapshots for a URL")
    p_wayback.add_argument("url")
    p_wayback.add_argument("--limit", type=int, default=20)
    add_sqlite_args(p_wayback)

    return parser


COMMAND_HANDLERS = {
    "openalex": cmd_openalex,
    "crossref": cmd_crossref,
    "wikidata": cmd_wikidata,
    "edgar": cmd_edgar,
    "wayback": cmd_wayback,
}


def main():
    parser = build_parser()
    args = parser.parse_args()

    if getattr(args, "sqlite", None) and not args.table:
        print("error: --sqlite requires --table", file=sys.stderr)
        sys.exit(2)

    handler = COMMAND_HANDLERS[args.command]
    rows, columns = handler(args)
    print_table(rows, columns)

    if getattr(args, "sqlite", None):
        dump_sqlite(args.sqlite, args.table, rows, columns)


if __name__ == "__main__":
    main()
