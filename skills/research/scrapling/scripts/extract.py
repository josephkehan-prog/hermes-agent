#!/usr/bin/env python3
"""Fetch a URL and optionally run local-model extraction on the text.

Fetches with scrapling.fetchers.Fetcher when scrapling is importable, else
falls back to urllib with an honest User-Agent. Text can be piped through a
local model for structured extraction (agent1, via Ollama) or analysis
(ornith, via llama-swap).

Usage:
    python3 extract.py <url> [--css SELECTOR] [--model agent1|ornith|none]

stdlib only; scrapling is an optional import.
"""
import argparse
import html.parser
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_TIMEOUT_SECONDS = 15
MODEL_TIMEOUT_SECONDS = 120
MAX_CHARS_FOR_MODEL = 8000
MAX_RESPONSE_BYTES = 10_000_000
ALLOWED_SCHEMES = {"http", "https"}
USER_AGENT = "Mozilla/5.0 (compatible; hermes-scrapling-extract/1.1)"

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "hf.co/InternScience/Agents-A1-Q4_K_M-GGUF:latest"

LLAMA_SWAP_URL = "http://localhost:1235/v1/chat/completions"
LLAMA_SWAP_MODEL = "ornith-uncensored"

try:
    from scrapling.fetchers import Fetcher

    SCRAPLING_AVAILABLE = True
except ImportError:
    SCRAPLING_AVAILABLE = False


class _TextExtractor(html.parser.HTMLParser):
    """stdlib fallback: strips tags, skips script/style, keeps visible text."""

    def __init__(self):
        super().__init__()
        self._skip_depth = 0
        self._chunks = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth == 0 and data.strip():
            self._chunks.append(data.strip())

    def get_text(self):
        return "\n".join(self._chunks)


def _strip_html(html_content):
    parser = _TextExtractor()
    parser.feed(html_content)
    return parser.get_text()


def _pretty_json(body):
    try:
        return json.dumps(json.loads(body), indent=2, ensure_ascii=False)
    except (json.JSONDecodeError, ValueError):
        return body.strip()


def _read_capped(response):
    """Read the response body, rejecting bodies over MAX_RESPONSE_BYTES."""
    raw = response.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        print(f"error: response exceeds {MAX_RESPONSE_BYTES} byte limit", file=sys.stderr)
        sys.exit(2)
    return raw


def _handle_urllib_response(response):
    """Branch on Content-Type: text/markup stripped, JSON pretty-printed, binary rejected."""
    content_type = (response.headers.get("Content-Type") or "").split(";")[0].strip().lower()
    charset = response.headers.get_content_charset() or "utf-8"

    if "json" in content_type:
        body = _read_capped(response).decode(charset, errors="replace")
        return {"method": "json", "page": _pretty_json(body)}
    if not content_type or content_type.startswith("text/") or "html" in content_type or "xml" in content_type:
        body = _read_capped(response).decode(charset, errors="replace")
        return {"method": "urllib", "page": body}

    print(f"error: cannot extract text from non-text content (Content-Type: {content_type})", file=sys.stderr)
    sys.exit(2)


def _require_http_scheme(url):
    """Exit with an error unless url is http(s) — blocks file:// local-file reads
    and other schemes urllib/scrapling would otherwise happily fetch."""
    scheme = urllib.parse.urlparse(url).scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        print(f"error: unsupported URL scheme {scheme!r} (only http/https allowed)", file=sys.stderr)
        sys.exit(2)


def fetch_page(url):
    """Fetch page HTML. Prefers scrapling.Fetcher, falls back to urllib."""
    _require_http_scheme(url)

    if SCRAPLING_AVAILABLE:
        try:
            page = Fetcher.get(url, timeout=DEFAULT_TIMEOUT_SECONDS)
            return {"method": "scrapling", "page": page}
        except Exception as exc:
            print(f"warning: scrapling fetch failed ({exc}); falling back to urllib", file=sys.stderr)

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
        return _handle_urllib_response(response)


def extract_text(fetched, css_selector):
    """Extract visible text, applying a CSS selector when scrapling did the fetch."""
    if css_selector and fetched["method"] != "scrapling":
        print("warning: --css requires scrapling (pip install scrapling); ignoring selector", file=sys.stderr)

    if fetched["method"] == "scrapling":
        return _extract_from_scrapling(fetched["page"], css_selector)
    if fetched["method"] == "json":
        return fetched["page"]
    return _strip_html(fetched["page"])


def _extract_from_scrapling(page, css_selector):
    if css_selector:
        try:
            matches = page.css(css_selector)
            texts = [m.get_all_text() if hasattr(m, "get_all_text") else str(m) for m in matches]
            texts = [t.strip() for t in texts if t and t.strip()]
            if texts:
                return "\n".join(texts)
            print(f"warning: css selector '{css_selector}' matched nothing, using full page text", file=sys.stderr)
        except Exception as exc:
            print(f"warning: css selection failed ({exc}), using full page text", file=sys.stderr)

    get_all_text = getattr(page, "get_all_text", None)
    if callable(get_all_text):
        try:
            return get_all_text()
        except Exception:
            pass
    html_content = getattr(page, "html_content", None)
    if isinstance(html_content, str):
        return _strip_html(html_content)
    return _strip_html(str(page))


def trim_text(text, max_chars=MAX_CHARS_FOR_MODEL):
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[truncated]"


def _post_json(url, payload):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=MODEL_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        print(f"error: cannot reach {url} ({exc.reason}). Is the local model server running?", file=sys.stderr)
        sys.exit(2)


def call_agent1(text, instruction):
    """Deterministic structured JSON extraction via Ollama, temperature 0."""
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": "Extract structured data as JSON only. No prose, no markdown fences."},
            {"role": "user", "content": f"{instruction}\n\n---\n{text}"},
        ],
        "options": {"temperature": 0},
        "stream": False,
    }
    response = _post_json(OLLAMA_URL, payload)
    return response["message"]["content"]


def call_ornith(text, instruction):
    """Analytical/summarization pass via llama-swap, thinking disabled."""
    payload = {
        "model": LLAMA_SWAP_MODEL,
        "messages": [{"role": "user", "content": f"{instruction}\n\n---\n{text}"}],
        "chat_template_kwargs": {"enable_thinking": False},
        "stream": False,
    }
    response = _post_json(LLAMA_SWAP_URL, payload)
    return response["choices"][0]["message"]["content"]


def build_parser():
    parser = argparse.ArgumentParser(description="Fetch a URL and optionally extract with a local model.")
    parser.add_argument("url", help="Page URL to fetch")
    parser.add_argument("--css", default=None, help="CSS selector to scope extraction (requires scrapling)")
    parser.add_argument(
        "--model",
        choices=["agent1", "ornith", "none"],
        default="none",
        help="agent1 = structured JSON (Ollama, temp 0); ornith = analysis/summary (llama-swap); none = raw text",
    )
    parser.add_argument(
        "--instruction",
        default="Extract the key structured data from this page.",
        help="Task instruction sent to the model (ignored when --model none)",
    )
    return parser


def main():
    args = build_parser().parse_args()

    try:
        fetched = fetch_page(args.url)
    except urllib.error.URLError as exc:
        print(f"error: failed to fetch {args.url}: {exc.reason}", file=sys.stderr)
        sys.exit(2)

    text = trim_text(extract_text(fetched, args.css))

    if args.model == "none":
        print(text)
        return
    if args.model == "agent1":
        print(call_agent1(text, args.instruction))
    else:
        print(call_ornith(text, args.instruction))


if __name__ == "__main__":
    main()
