"""Tests for skills/research/deal-hunting/scripts/deals.py — no network, no external services."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "skills" / "research" / "deal-hunting" / "scripts" / "deals.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("deal_hunting_deals_test_module", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


deals = _load_script_module()


RSS_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
{items}
</channel></rss>"""


def _rss_item(title, link, pub_date="Mon, 01 Jan 2024 00:00:00 +0000"):
    return f"<item><title>{title}</title><link>{link}</link><pubDate>{pub_date}</pubDate></item>"


ATOM_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
{entries}
</feed>"""


def _atom_entry(title, href, updated="2024-01-01T00:00:00+00:00"):
    return f'<entry><title>{title}</title><link href="{href}"/><updated>{updated}</updated></entry>'


class TestExtractPrice:
    def test_finds_simple_dollar_price(self):
        assert deals.extract_price("RTX 4070 Ti Super $749.99 Shipped") == "$749.99"

    def test_finds_price_with_thousands_separator(self):
        assert deals.extract_price("$1,299.00 Dell XPS 15 Laptop") == "$1,299.00"

    def test_returns_first_price_when_multiple_present(self):
        text = "Bundle for $9.99 each (3 for $25)"
        assert deals.extract_price(text) == "$9.99"

    def test_returns_empty_string_when_no_price_present(self):
        assert deals.extract_price("Free eBook - No Price Here") == ""

    def test_finds_whole_dollar_price_without_cents(self):
        assert deals.extract_price("Samsung 990 PRO 2TB NVMe SSD - $130 Shipped") == "$130"


class TestParseRss:
    def test_parses_slickdeals_style_items_into_deal_dicts(self):
        xml_text = RSS_TEMPLATE.format(
            items=_rss_item(
                "Samsung 990 PRO 2TB NVMe SSD - $129.99 + Free Shipping",
                "https://slickdeals.net/f/12345-samsung-990-pro",
            )
        )

        result = deals.parse_rss(xml_text, "slickdeals")

        assert len(result) == 1
        deal = result[0]
        assert deal["source"] == "slickdeals"
        assert deal["title"] == "Samsung 990 PRO 2TB NVMe SSD - $129.99 + Free Shipping"
        assert deal["price"] == "$129.99"
        assert deal["link"] == "https://slickdeals.net/f/12345-samsung-990-pro"
        assert deal["date"] == "Mon, 01 Jan 2024 00:00:00 +0000"

    def test_parses_multiple_items_in_order(self):
        xml_text = RSS_TEMPLATE.format(
            items=(
                _rss_item("GPU Deal $499.99", "https://example.com/1")
                + _rss_item("SSD Deal $89.99", "https://example.com/2")
            )
        )

        result = deals.parse_rss(xml_text, "ozbargain")

        assert [d["title"] for d in result] == ["GPU Deal $499.99", "SSD Deal $89.99"]
        assert [d["price"] for d in result] == ["$499.99", "$89.99"]

    def test_query_filter_excludes_non_matching_titles_case_insensitively(self):
        xml_text = RSS_TEMPLATE.format(
            items=(
                _rss_item("Gaming GPU $499.99", "https://example.com/1")
                + _rss_item("Kitchen Blender $29.99", "https://example.com/2")
            )
        )

        result = deals.parse_rss(xml_text, "ozbargain", query_filter="gpu")

        assert len(result) == 1
        assert result[0]["title"] == "Gaming GPU $499.99"

    def test_missing_optional_fields_default_to_empty_strings(self):
        xml_text = RSS_TEMPLATE.format(items="<item><title>No link or date</title></item>")

        result = deals.parse_rss(xml_text, "slickdeals")

        assert result[0]["link"] == ""
        assert result[0]["date"] == ""


class TestParseAtom:
    def test_parses_reddit_style_entries_into_deal_dicts(self):
        xml_text = ATOM_TEMPLATE.format(
            entries=_atom_entry("[Newegg] SSD $79.99", "https://old.reddit.com/r/buildapcsales/1")
        )

        result = deals.parse_atom(xml_text, "reddit-bapcs")

        assert len(result) == 1
        deal = result[0]
        assert deal["source"] == "reddit-bapcs"
        assert deal["title"] == "[Newegg] SSD $79.99"
        assert deal["price"] == "$79.99"
        assert deal["link"] == "https://old.reddit.com/r/buildapcsales/1"
        assert deal["date"] == "2024-01-01T00:00:00+00:00"


class TestRejectDangerousXml:
    def test_doctype_declaration_is_rejected(self):
        xml_text = '<?xml version="1.0"?><!DOCTYPE foo><rss><channel/></rss>'

        with pytest.raises(deals.DealFetchError, match="disallowed XML construct"):
            deals.reject_dangerous_xml(xml_text)

    def test_entity_declaration_is_rejected(self):
        xml_text = (
            '<?xml version="1.0"?>'
            '<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
            "<rss><channel><item><title>&xxe;</title></item></channel></rss>"
        )

        with pytest.raises(deals.DealFetchError, match="disallowed XML construct"):
            deals.reject_dangerous_xml(xml_text)

    def test_rejection_is_case_insensitive(self):
        xml_text = '<?xml version="1.0"?><!DoCtYpE foo><rss><channel/></rss>'

        with pytest.raises(deals.DealFetchError):
            deals.reject_dangerous_xml(xml_text)

    def test_benign_feed_without_doctype_passes(self):
        xml_text = RSS_TEMPLATE.format(items=_rss_item("Clean feed $1.00", "https://example.com/1"))

        deals.reject_dangerous_xml(xml_text)  # must not raise

    def test_parse_rss_propagates_rejection_for_malicious_feed(self):
        xml_text = '<?xml version="1.0"?><!DOCTYPE foo><rss><channel/></rss>'

        with pytest.raises(deals.DealFetchError):
            deals.parse_rss(xml_text, "slickdeals")

    def test_parse_atom_propagates_rejection_for_malicious_feed(self):
        xml_text = '<?xml version="1.0"?><!DOCTYPE foo><feed xmlns="http://www.w3.org/2005/Atom"/>'

        with pytest.raises(deals.DealFetchError):
            deals.parse_atom(xml_text, "reddit-bapcs")


class TestWatchlistDedupe:
    def _canned_deals(self):
        return [
            {"source": "slickdeals", "title": "SSD $99.99", "price": "$99.99", "link": "https://slickdeals.net/1", "date": "d1"},
            {"source": "slickdeals", "title": "GPU $499.99", "price": "$499.99", "link": "https://slickdeals.net/2", "date": "d2"},
        ]

    def test_first_run_adds_all_deals_with_hash(self, monkeypatch, tmp_path):
        monkeypatch.setattr(deals, "search_deals", lambda query, source, limit: self._canned_deals())
        out_path = tmp_path / "watchlist.json"

        deals.watch_deals("ssd", "all", str(out_path), 15)

        saved = json.loads(out_path.read_text())
        assert len(saved) == 2
        assert saved[0]["hash"] == deals.link_hash("https://slickdeals.net/1")
        assert saved[1]["hash"] == deals.link_hash("https://slickdeals.net/2")

    def test_second_run_with_same_links_adds_no_duplicates(self, monkeypatch, tmp_path):
        monkeypatch.setattr(deals, "search_deals", lambda query, source, limit: self._canned_deals())
        out_path = tmp_path / "watchlist.json"
        deals.watch_deals("ssd", "all", str(out_path), 15)

        deals.watch_deals("ssd", "all", str(out_path), 15)

        saved = json.loads(out_path.read_text())
        assert len(saved) == 2

    def test_second_run_with_one_new_link_adds_only_that_one(self, monkeypatch, tmp_path):
        monkeypatch.setattr(deals, "search_deals", lambda query, source, limit: self._canned_deals())
        out_path = tmp_path / "watchlist.json"
        deals.watch_deals("ssd", "all", str(out_path), 15)

        new_deals = self._canned_deals() + [
            {"source": "slickdeals", "title": "RAM $59.99", "price": "$59.99", "link": "https://slickdeals.net/3", "date": "d3"}
        ]
        monkeypatch.setattr(deals, "search_deals", lambda query, source, limit: new_deals)
        deals.watch_deals("ssd", "all", str(out_path), 15)

        saved = json.loads(out_path.read_text())
        assert len(saved) == 3
        assert saved[2]["link"] == "https://slickdeals.net/3"

    def test_link_hash_is_stable_and_distinct_per_link(self):
        assert deals.link_hash("https://a.example/1") == deals.link_hash("https://a.example/1")
        assert deals.link_hash("https://a.example/1") != deals.link_hash("https://a.example/2")

    def test_load_watchlist_returns_empty_list_for_missing_file(self, tmp_path):
        missing = tmp_path / "does-not-exist.json"
        assert deals.load_watchlist(str(missing)) == []

    def test_load_watchlist_rejects_invalid_json(self, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{not valid json")

        with pytest.raises(deals.DealFetchError, match="not valid JSON"):
            deals.load_watchlist(str(bad_file))


class TestValidateQuery:
    def test_strips_surrounding_whitespace(self):
        assert deals.validate_query("  gpu deals  ") == "gpu deals"

    def test_empty_query_is_rejected(self):
        with pytest.raises(ValueError, match="must not be empty"):
            deals.validate_query("")

    def test_whitespace_only_query_is_rejected(self):
        with pytest.raises(ValueError, match="must not be empty"):
            deals.validate_query("   ")

    def test_query_at_max_length_is_accepted(self):
        query = "x" * deals.MAX_QUERY_CHARS
        assert deals.validate_query(query) == query

    def test_query_over_max_length_is_rejected(self):
        query = "x" * (deals.MAX_QUERY_CHARS + 1)
        with pytest.raises(ValueError, match="too long"):
            deals.validate_query(query)
