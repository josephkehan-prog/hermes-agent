#!/usr/bin/env python3
"""Fetch a clearnet or .onion URL through the local Tor SOCKS proxy.

Works regardless of the global `hermes-tor` toggle: it always sends THIS
request through Tor explicitly, so .onion resolves even when Hermes'
normal traffic is direct. Localhost is never proxied.
"""
import argparse
import os
import sys

PROXY = os.environ.get("TOR_SOCKS_URL", "socks5h://127.0.0.1:9050")
VENV_PY = os.path.expanduser("~/.hermes/hermes-agent/venv/bin/python")


def _ensure_httpx():
    # Need httpx AND socksio (for SOCKS/.onion). System python often has httpx
    # but not socksio, so check both and re-exec under the Hermes venv if needed.
    try:
        import httpx  # noqa
        import socksio  # noqa
        return
    except ImportError:
        if os.path.realpath(sys.executable) != os.path.realpath(VENV_PY) and os.path.exists(VENV_PY):
            os.execv(VENV_PY, [VENV_PY, os.path.abspath(__file__), *sys.argv[1:]])
        sys.exit("ERROR: need httpx[socks]; Hermes venv not found. "
                 "Install with: pip install 'httpx[socks]'")


def main():
    ap = argparse.ArgumentParser(description="Fetch a URL over Tor (SOCKS5h).")
    ap.add_argument("url", help="http(s):// URL — clearnet or .onion")
    ap.add_argument("--save", metavar="PATH", help="write response body to PATH")
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--max-bytes", type=int, default=20000,
                    help="max body chars to print (default 20000; 0 = all)")
    ap.add_argument("--headers-only", action="store_true")
    args = ap.parse_args()

    _ensure_httpx()
    import httpx

    try:
        try:
            client = httpx.Client(proxy=PROXY, timeout=args.timeout, follow_redirects=True)
        except TypeError:  # older httpx uses `proxies=`
            client = httpx.Client(proxies=PROXY, timeout=args.timeout, follow_redirects=True)
        with client:
            r = client.get(args.url, headers={"User-Agent": "curl/8"})
    except Exception as e:  # noqa
        msg = str(e)
        print(f"ERROR fetching {args.url}\n  {type(e).__name__}: {msg}", file=sys.stderr)
        if "Connection refused" in msg or "connect" in msg.lower():
            print("  Hint: is tor running?  `hermes-tor status` / `brew services start tor`",
                  file=sys.stderr)
        sys.exit(2)

    print(f"HTTP {r.status_code}  {r.reason_phrase}")
    print(f"final-url: {r.url}")
    print(f"content-type: {r.headers.get('content-type','?')}")
    body = r.content
    print(f"bytes: {len(body)}")
    if args.headers_only:
        for k, v in r.headers.items():
            print(f"{k}: {v}")
        return
    if args.save:
        with open(args.save, "wb") as f:
            f.write(body)
        print(f"saved: {os.path.abspath(args.save)}")
        return
    text = r.text
    if args.max_bytes and len(text) > args.max_bytes:
        print("--- body (truncated) ---")
        print(text[:args.max_bytes])
        print(f"... [truncated {len(text) - args.max_bytes} chars; use --save to keep all]")
    else:
        print("--- body ---")
        print(text)


if __name__ == "__main__":
    main()
