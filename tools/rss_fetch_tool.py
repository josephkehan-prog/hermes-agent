#!/usr/bin/env python3
"""Fetch and parse RSS 2.0 and Atom feeds.

``fetch_feed`` and ``fetch_feeds`` use only the stdlib: ``urllib.request`` for
the HTTP fetch and ``xml.etree.ElementTree`` for parsing. The RSS2/Atom field
mapping (which element maps to ``title``/``link``/``published``/``summary``
across the two formats) is modeled on feedparser's approach
(https://github.com/kurtmckee/feedparser, BSD-2-Clause License — Copyright
(c) Kurt McKee) — no feedparser code is vendored here, only the mapping idea.

XXE defense: feedparser and defusedxml both guard against XML entity-expansion
and external-entity attacks. ``xml.etree.ElementTree`` does not resolve
external entities by default, but a malicious feed could still carry a
``<!DOCTYPE`` / ``<!ENTITY`` block designed to abuse a parser that does. This
module rejects any feed body containing a DTD or entity declaration before it
ever reaches ``ElementTree.fromstring`` (defusedxml-style guard), rather than
relying on ElementTree's default behavior alone.

SSRF note: only ``http``/``https`` URLs are accepted (``file://``, ``ftp://``,
etc. are rejected), and the resolved host is rejected if it's private/
reserved/loopback/link-local/multicast/unspecified (blocks loopback,
RFC1918, and cloud metadata endpoints like 169.254.169.254) via
``tools._net_guard``. Redirects are re-validated hop-by-hop through
``_net_guard.build_safe_opener`` rather than followed blindly.
"""

import codecs
import json
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

from tools import _net_guard
from tools.registry import registry

_USER_AGENT = "Hermes-Agent (https://github.com/NousResearch/hermes-agent)"
_TIMEOUT_S = 15
_ALLOWED_SCHEMES = {"http", "https"}
_DEFAULT_LIMIT = 20
_MIN_LIMIT = 1
_MAX_LIMIT = 100
_DEFAULT_LIMIT_PER_FEED = 10
_MAX_RESPONSE_BYTES = _net_guard.MAX_RESPONSE_BYTES
_ATOM_NS = "{http://www.w3.org/2005/Atom}"
_DANGEROUS_XML_MARKERS = ("<!doctype", "<!entity")
_DANGEROUS_XML_MARKERS_BYTES = tuple(marker.encode("ascii") for marker in _DANGEROUS_XML_MARKERS)
_UTF16_BOMS = (codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)


def _validate_url(url: Any) -> Optional[str]:
    """Return url if it's a well-formed http(s) URL, else None."""
    if not isinstance(url, str) or not url.strip():
        return None
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme.lower() not in _ALLOWED_SCHEMES or not parsed.netloc:
        return None
    return url


def _validate_limit(limit: Any, default: int) -> int:
    """Clamp limit into [_MIN_LIMIT, _MAX_LIMIT]."""
    try:
        limit_int = int(limit)
    except (TypeError, ValueError):
        limit_int = default
    return max(_MIN_LIMIT, min(_MAX_LIMIT, limit_int))


def _reject_dangerous_xml_bytes(raw_bytes: bytes) -> Optional[str]:
    """Return an error string if raw_bytes smuggles a DTD/entity declaration
    past a naive UTF-8-decode scan, else None.

    A UTF-16-encoded feed hides '<!DOCTYPE'/'<!ENTITY' from a scan of the
    force-decoded-as-UTF-8 string: each ASCII byte of the marker comes out
    as byte+0x00 (UTF-16LE) or 0x00+byte (UTF-16BE), so the literal marker
    substring never appears in that decoded text even though the bytes are
    right there. Stripping NUL bytes out of the raw response before
    scanning collapses that smuggling back down to the plain-ASCII marker
    regardless of which encoding produced it (a leading BOM doesn't affect
    this — it's just extra prefix bytes, not NULs). This runs on the raw
    bytes before any decoding happens, ahead of the decoded-string check in
    ``_reject_dangerous_xml`` below (defense in depth).
    """
    denulled = raw_bytes.replace(b"\x00", b"").lower()
    for marker in _DANGEROUS_XML_MARKERS_BYTES:
        if marker in denulled:
            return f"rejected feed: contains disallowed XML construct ({marker.decode().strip('<!')})"
    return None


def _reject_dangerous_xml(raw_text: str) -> Optional[str]:
    """Return an error string if raw_text carries a DTD or entity declaration,
    else None.

    ElementTree.fromstring doesn't resolve external entities by default, but
    we refuse to hand it anything DOCTYPE/ENTITY-bearing at all — a
    defusedxml-style guard against XXE/billion-laughs-style payloads rather
    than trusting the parser's default posture.
    """
    lowered = raw_text.lower()
    for marker in _DANGEROUS_XML_MARKERS:
        if marker in lowered:
            return f"rejected feed: contains disallowed XML construct ({marker.strip('<!')})"
    return None


def _decode_feed_bytes(raw_bytes: bytes) -> str:
    """Decode feed bytes into text, honoring a UTF-16 BOM if present.

    Feed responses are almost always UTF-8, but a well-formed UTF-16 feed
    (BOM + XML declaration) is legitimate too. Force-decoding UTF-16 bytes
    as UTF-8 doesn't raise — every ASCII byte value decodes fine on its
    own — it just mangles the text into byte+NUL pairs that never parse as
    XML. Detect the BOM and decode with the matching codec instead.
    """
    if raw_bytes[:2] in _UTF16_BOMS:
        return raw_bytes.decode("utf-16", errors="replace")
    return raw_bytes.decode("utf-8", errors="replace")


def _local_tag(tag: str) -> str:
    """Strip a namespace prefix off an ElementTree tag, e.g. '{ns}item' -> 'item'."""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _text_of(el: Optional[ET.Element]) -> str:
    return (el.text or "").strip() if el is not None else ""


def _find_child(parent: ET.Element, *names: str) -> Optional[ET.Element]:
    """Find the first direct child whose local tag name matches one of names."""
    for child in parent:
        if _local_tag(child.tag) in names:
            return child
    return None


def _rss2_entry(item: ET.Element) -> Dict[str, str]:
    return {
        "title": _text_of(_find_child(item, "title")),
        "link": _text_of(_find_child(item, "link")),
        "published": _text_of(_find_child(item, "pubDate", "date")),
        "summary": _text_of(_find_child(item, "description", "summary")),
    }


def _atom_link(entry: ET.Element) -> str:
    """Atom links are attributes (href), not text; prefer rel="alternate"."""
    links = [c for c in entry if _local_tag(c.tag) == "link"]
    for link in links:
        if link.get("rel") in (None, "alternate"):
            return (link.get("href") or "").strip()
    return (links[0].get("href") or "").strip() if links else ""


def _atom_entry(entry: ET.Element) -> Dict[str, str]:
    return {
        "title": _text_of(_find_child(entry, "title")),
        "link": _atom_link(entry),
        "published": _text_of(_find_child(entry, "published", "updated")),
        "summary": _text_of(_find_child(entry, "summary", "content")),
    }


def _parse_feed_xml(raw_text: str, limit: int) -> Dict[str, Any]:
    """Parse RSS 2.0 or Atom XML text into {feed_title, entries}."""
    root = ET.fromstring(raw_text)
    root_tag = _local_tag(root.tag)

    if root_tag == "rss":
        channel = _find_child(root, "channel")
        if channel is None:
            raise ValueError("rss feed missing <channel>")
        feed_title = _text_of(_find_child(channel, "title"))
        items = [c for c in channel if _local_tag(c.tag) == "item"][:limit]
        entries = [_rss2_entry(item) for item in items]
    elif root_tag == "feed":
        feed_title = _text_of(_find_child(root, "title"))
        items = [c for c in root if _local_tag(c.tag) == "entry"][:limit]
        entries = [_atom_entry(item) for item in items]
    else:
        raise ValueError(f"unrecognized feed root element: <{root_tag}>")

    return {"feed_title": feed_title, "entries": entries}


def fetch_feed(url: Any, limit: Any = _DEFAULT_LIMIT) -> Dict[str, Any]:
    """Fetch and parse a single RSS 2.0 or Atom feed.

    Returns {ok, feed_title, entries} on success, {ok: False, error} on
    invalid input, network failure, or a malformed/rejected feed body.
    """
    valid_url = _validate_url(url)
    if valid_url is None:
        return {"ok": False, "error": f"invalid or disallowed url: {url!r} (http/https only)"}

    try:
        _net_guard.reject_private_target(valid_url)
    except _net_guard.NetGuardError as exc:
        return {"ok": False, "error": str(exc)}

    limit_int = _validate_limit(limit, _DEFAULT_LIMIT)

    req = urllib.request.Request(valid_url, headers={"User-Agent": _USER_AGENT})
    opener = _net_guard.build_safe_opener()
    try:
        with opener.open(req, timeout=_TIMEOUT_S) as resp:
            raw_bytes = _net_guard.read_capped(resp)
    except _net_guard.NetGuardError:
        return {"ok": False, "error": f"feed body exceeds {_MAX_RESPONSE_BYTES} byte limit"}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error": f"http error {exc.code}: {exc.reason}"}
    except urllib.error.URLError as exc:
        return {"ok": False, "error": f"could not reach feed: {exc.reason}"}
    except (TimeoutError, OSError) as exc:
        return {"ok": False, "error": str(exc)}

    danger = _reject_dangerous_xml_bytes(raw_bytes)
    if danger is not None:
        return {"ok": False, "error": danger}

    raw_text = _decode_feed_bytes(raw_bytes)

    danger = _reject_dangerous_xml(raw_text)
    if danger is not None:
        return {"ok": False, "error": danger}

    try:
        parsed = _parse_feed_xml(raw_text, limit_int)
    except ET.ParseError as exc:
        return {"ok": False, "error": f"malformed feed xml: {exc}"}
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    return {"ok": True, "feed_title": parsed["feed_title"], "entries": parsed["entries"]}


def fetch_feeds(urls: Any, limit_per_feed: Any = _DEFAULT_LIMIT_PER_FEED) -> Dict[str, Any]:
    """Fetch multiple feeds sequentially, isolating failures per-feed.

    Returns {ok, results: [{url, ok, feed_title?, entries?, error?}, ...]}.
    ``ok`` at the top level is True as long as urls was a valid list — a
    per-feed failure only marks that entry's own ``ok`` False, it never
    aborts the batch.
    """
    if not isinstance(urls, (list, tuple)):
        return {"ok": False, "error": "urls must be a list of feed urls"}

    results: List[Dict[str, Any]] = []
    for url in urls:
        feed_result = fetch_feed(url, limit=limit_per_feed)
        results.append({"url": url, **feed_result})

    return {"ok": True, "results": results}


registry.register(
    name="fetch_feed",
    toolset="web",
    schema={
        "name": "fetch_feed",
        "description": (
            "Fetch and parse a single RSS 2.0 or Atom feed over http/https. "
            "Returns the feed title and up to `limit` entries, each with "
            "title, link, published date, and summary. Stdlib-only "
            "(urllib + xml.etree), with XXE and SSRF (private-IP) guards. "
            "Use `fetch_feeds` instead to pull several feeds in one call."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Feed URL (http or https only)."},
                "limit": {
                    "type": "integer",
                    "description": f"Max entries to return ({_MIN_LIMIT}-{_MAX_LIMIT}). Defaults to {_DEFAULT_LIMIT}.",
                },
            },
            "required": ["url"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        fetch_feed(url=args.get("url", ""), limit=args.get("limit", _DEFAULT_LIMIT)),
        ensure_ascii=False,
    ),
    emoji="📡",
)

registry.register(
    name="fetch_feeds",
    toolset="web",
    schema={
        "name": "fetch_feeds",
        "description": (
            "Fetch and parse multiple RSS 2.0 / Atom feeds sequentially. "
            "Each feed is isolated — one failing feed doesn't abort the "
            "others. Returns a list of per-feed results in `results`, each "
            "shaped like `fetch_feed`'s return value plus the source `url`."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Feed URLs to fetch (http or https only).",
                },
                "limit_per_feed": {
                    "type": "integer",
                    "description": f"Max entries per feed ({_MIN_LIMIT}-{_MAX_LIMIT}). Defaults to {_DEFAULT_LIMIT_PER_FEED}.",
                },
            },
            "required": ["urls"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        fetch_feeds(urls=args.get("urls", []), limit_per_feed=args.get("limit_per_feed", _DEFAULT_LIMIT_PER_FEED)),
        ensure_ascii=False,
    ),
    emoji="📡",
)
