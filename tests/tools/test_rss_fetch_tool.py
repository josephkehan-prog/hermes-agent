"""Tests for tools/rss_fetch_tool.py — RSS 2.0 / Atom feed fetch+parse."""

import textwrap

from tools import rss_fetch_tool

RSS2_SAMPLE = textwrap.dedent(
    """
    <?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>Deals Feed</title>
        <item>
          <title>50% off widgets</title>
          <link>https://example.com/widgets</link>
          <pubDate>Fri, 10 Jul 2026 12:00:00 GMT</pubDate>
          <description>Widgets are on sale.</description>
        </item>
        <item>
          <title>Free shipping on gadgets</title>
          <link>https://example.com/gadgets</link>
          <pubDate>Thu, 09 Jul 2026 12:00:00 GMT</pubDate>
          <description>Gadgets ship free.</description>
        </item>
      </channel>
    </rss>
    """
).strip()

ATOM_SAMPLE = textwrap.dedent(
    """
    <?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <title>Blogwatcher Feed</title>
      <entry>
        <title>New post about widgets</title>
        <link rel="alternate" href="https://example.com/blog/widgets"/>
        <published>2026-07-10T12:00:00Z</published>
        <summary>A post about widgets.</summary>
      </entry>
      <entry>
        <title>New post about gadgets</title>
        <link rel="alternate" href="https://example.com/blog/gadgets"/>
        <published>2026-07-09T12:00:00Z</published>
        <summary>A post about gadgets.</summary>
      </entry>
    </feed>
    """
).strip()

DOCTYPE_SAMPLE = textwrap.dedent(
    """
    <?xml version="1.0"?>
    <!DOCTYPE rss [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
    <rss version="2.0"><channel><title>&xxe;</title></channel></rss>
    """
).strip()


class _FakeResponse:
    """Minimal stand-in for the object urllib.request.urlopen returns."""

    def __init__(self, body: str, encoding: str = "utf-8"):
        self._body = body.encode(encoding)

    def read(self, *_args, **_kwargs):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


class TestFetchFeedParsing:
    """fetch_feed parses RSS2/Atom XML with no network involved — urlopen is
    monkeypatched to return an in-memory sample."""

    def test_parses_rss2_feed(self, monkeypatch):
        monkeypatch.setattr(
            rss_fetch_tool.urllib.request, "urlopen", lambda *a, **kw: _FakeResponse(RSS2_SAMPLE)
        )

        result = rss_fetch_tool.fetch_feed("https://example.com/feed.xml")

        assert result["ok"] is True
        assert result["feed_title"] == "Deals Feed"
        assert len(result["entries"]) == 2
        assert result["entries"][0]["title"] == "50% off widgets"
        assert result["entries"][0]["link"] == "https://example.com/widgets"
        assert result["entries"][0]["published"] == "Fri, 10 Jul 2026 12:00:00 GMT"
        assert result["entries"][0]["summary"] == "Widgets are on sale."

    def test_parses_atom_feed(self, monkeypatch):
        monkeypatch.setattr(
            rss_fetch_tool.urllib.request, "urlopen", lambda *a, **kw: _FakeResponse(ATOM_SAMPLE)
        )

        result = rss_fetch_tool.fetch_feed("https://example.com/atom.xml")

        assert result["ok"] is True
        assert result["feed_title"] == "Blogwatcher Feed"
        assert len(result["entries"]) == 2
        assert result["entries"][0]["title"] == "New post about widgets"
        assert result["entries"][0]["link"] == "https://example.com/blog/widgets"
        assert result["entries"][0]["published"] == "2026-07-10T12:00:00Z"
        assert result["entries"][0]["summary"] == "A post about widgets."

    def test_limit_enforced(self, monkeypatch):
        monkeypatch.setattr(
            rss_fetch_tool.urllib.request, "urlopen", lambda *a, **kw: _FakeResponse(RSS2_SAMPLE)
        )

        result = rss_fetch_tool.fetch_feed("https://example.com/feed.xml", limit=1)

        assert result["ok"] is True
        assert len(result["entries"]) == 1
        assert result["entries"][0]["title"] == "50% off widgets"


class TestFetchFeedGuards:
    """Input validation and XXE defense run before any parsing occurs."""

    def test_rejects_disallowed_scheme(self):
        result = rss_fetch_tool.fetch_feed("file:///etc/passwd")

        assert result["ok"] is False
        assert "invalid or disallowed url" in result["error"]

    def test_rejects_ftp_scheme(self):
        result = rss_fetch_tool.fetch_feed("ftp://example.com/feed.xml")

        assert result["ok"] is False
        assert "invalid or disallowed url" in result["error"]

    def test_rejects_empty_url(self):
        result = rss_fetch_tool.fetch_feed("")

        assert result["ok"] is False
        assert "invalid or disallowed url" in result["error"]

    def test_rejects_doctype_before_parsing(self, monkeypatch):
        monkeypatch.setattr(
            rss_fetch_tool.urllib.request, "urlopen", lambda *a, **kw: _FakeResponse(DOCTYPE_SAMPLE)
        )

        result = rss_fetch_tool.fetch_feed("https://example.com/evil.xml")

        assert result["ok"] is False
        assert "disallowed XML construct" in result["error"]

    def test_rejects_doctype_smuggled_via_utf16(self, monkeypatch):
        """Regression: a UTF-16-encoded feed hides <!DOCTYPE/<!ENTITY from a
        scan of the force-decoded-as-UTF-8 string (each ASCII byte comes out
        as byte+0x00), so the old guard let this through to the parser. The
        raw-bytes NUL-stripped scan must catch it before decoding happens.
        """
        monkeypatch.setattr(
            rss_fetch_tool.urllib.request,
            "urlopen",
            lambda *a, **kw: _FakeResponse(DOCTYPE_SAMPLE, encoding="utf-16"),
        )

        result = rss_fetch_tool.fetch_feed("https://example.com/evil-utf16.xml")

        assert result["ok"] is False
        assert "disallowed XML construct" in result["error"]

    def test_parses_clean_utf16_feed(self, monkeypatch):
        """A legitimate UTF-16 feed (BOM + no DOCTYPE/ENTITY) must still
        decode and parse — the XXE guard shouldn't collaterally break valid
        non-UTF-8 feeds."""
        monkeypatch.setattr(
            rss_fetch_tool.urllib.request,
            "urlopen",
            lambda *a, **kw: _FakeResponse(RSS2_SAMPLE, encoding="utf-16"),
        )

        result = rss_fetch_tool.fetch_feed("https://example.com/feed-utf16.xml")

        assert result["ok"] is True
        assert result["feed_title"] == "Deals Feed"
        assert len(result["entries"]) == 2
        assert result["entries"][0]["title"] == "50% off widgets"


class TestFetchFeeds:
    """fetch_feeds isolates per-feed errors so one bad feed doesn't sink the batch."""

    def test_mixed_success_and_failure(self, monkeypatch):
        def fake_urlopen(req, *a, **kw):
            if "good" in req.full_url:
                return _FakeResponse(RSS2_SAMPLE)
            raise rss_fetch_tool.urllib.error.URLError("boom")

        monkeypatch.setattr(rss_fetch_tool.urllib.request, "urlopen", fake_urlopen)

        result = rss_fetch_tool.fetch_feeds(
            ["https://example.com/good.xml", "https://example.com/bad.xml"]
        )

        assert result["ok"] is True
        assert len(result["results"]) == 2
        assert result["results"][0]["ok"] is True
        assert result["results"][0]["feed_title"] == "Deals Feed"
        assert result["results"][1]["ok"] is False
        assert "could not reach feed" in result["results"][1]["error"]

    def test_rejects_non_list_urls(self):
        result = rss_fetch_tool.fetch_feeds("https://example.com/feed.xml")

        assert result["ok"] is False
        assert "must be a list" in result["error"]
