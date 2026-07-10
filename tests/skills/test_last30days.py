"""Tests for skills/research/last30days/scripts/last30days.py — no network, no external services."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "skills" / "research" / "last30days" / "scripts" / "last30days.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("last30days_test_module", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


last30days = _load_script_module()


class TestValidateQuery:
    def test_strips_surrounding_whitespace(self):
        assert last30days.validate_query("  bitcoin  ") == "bitcoin"

    def test_empty_query_is_rejected(self):
        with pytest.raises(ValueError, match="must not be empty"):
            last30days.validate_query("")

    def test_whitespace_only_query_is_rejected(self):
        with pytest.raises(ValueError, match="must not be empty"):
            last30days.validate_query("   ")

    def test_query_at_max_length_is_accepted(self):
        query = "x" * last30days.MAX_QUERY_CHARS
        assert last30days.validate_query(query) == query

    def test_query_over_max_length_is_rejected(self):
        query = "x" * (last30days.MAX_QUERY_CHARS + 1)
        with pytest.raises(ValueError, match="too long"):
            last30days.validate_query(query)

    def test_control_character_is_rejected(self):
        with pytest.raises(ValueError, match="control characters"):
            last30days.validate_query("bitcoin\x00drop")

    def test_newline_is_rejected(self):
        with pytest.raises(ValueError, match="control characters"):
            last30days.validate_query("bitcoin\nX-Injected: 1")

    def test_del_character_is_rejected(self):
        with pytest.raises(ValueError, match="control characters"):
            last30days.validate_query("bitcoin\x7f")

    def test_ordinary_punctuation_is_accepted(self):
        assert last30days.validate_query("rust async/await?!") == "rust async/await?!"


class TestParseSources:
    def test_all_expands_to_full_source_list(self):
        assert last30days.parse_sources("all") == last30days.SOURCES

    def test_comma_separated_list_is_split_and_stripped(self):
        assert last30days.parse_sources("reddit, hn") == ["reddit", "hn"]

    def test_unknown_source_is_rejected(self):
        with pytest.raises(ValueError, match="unknown source"):
            last30days.parse_sources("reddit,twitter")


class TestComputeCutoff:
    def test_cutoff_is_30_days_before_reference_time(self):
        reference = 1_700_000_000  # fixed reference instant, not wall-clock time
        cutoff_epoch, cutoff_date = last30days.compute_cutoff(now=reference)

        assert cutoff_epoch == reference - last30days.THIRTY_DAYS_SECONDS
        assert cutoff_date == "2023-10-15"

    def test_cutoff_uses_time_time_when_now_is_not_passed(self, monkeypatch):
        monkeypatch.setattr(last30days.time, "time", lambda: 1_700_000_000)

        cutoff_epoch, _cutoff_date = last30days.compute_cutoff()

        assert cutoff_epoch == 1_700_000_000 - last30days.THIRTY_DAYS_SECONDS

    def test_cutoff_is_computed_fresh_each_call_not_at_import(self, monkeypatch):
        monkeypatch.setattr(last30days.time, "time", lambda: 1_000_000_000)
        first_epoch, _ = last30days.compute_cutoff()

        monkeypatch.setattr(last30days.time, "time", lambda: 2_000_000_000)
        second_epoch, _ = last30days.compute_cutoff()

        assert second_epoch - first_epoch == 1_000_000_000


class TestParseRedditJson:
    def test_parses_listing_children_into_entries(self):
        payload = {
            "data": {
                "children": [
                    {
                        "data": {
                            "title": "Bitcoin hits new high",
                            "subreddit": "CryptoCurrency",
                            "score": 421,
                            "created_utc": 1_700_000_000,
                            "permalink": "/r/CryptoCurrency/comments/abc123/bitcoin_hits_new_high/",
                        }
                    }
                ]
            }
        }

        result = last30days.parse_reddit_json(payload, limit=15)

        assert len(result) == 1
        entry = result[0]
        assert entry["source"] == "reddit"
        assert entry["title"] == "Bitcoin hits new high"
        assert entry["link"] == "https://www.reddit.com/r/CryptoCurrency/comments/abc123/bitcoin_hits_new_high/"
        assert "score 421" in entry["metric"]
        assert entry["date"] == "2023-11-14T22:13:20Z"

    def test_respects_limit(self):
        payload = {"data": {"children": [{"data": {"title": f"post {i}"}} for i in range(5)]}}

        result = last30days.parse_reddit_json(payload, limit=2)

        assert len(result) == 2

    def test_missing_data_key_yields_empty_list(self):
        assert last30days.parse_reddit_json({}, limit=15) == []


class TestParseHnJson:
    def test_parses_hits_into_entries(self):
        payload = {
            "hits": [
                {
                    "title": "Show HN: my keyless research tool",
                    "url": "https://example.com/tool",
                    "points": 88,
                    "num_comments": 12,
                    "created_at": "2024-01-05T10:00:00.000Z",
                    "objectID": "39000000",
                }
            ]
        }

        result = last30days.parse_hn_json(payload, limit=15)

        assert len(result) == 1
        entry = result[0]
        assert entry["source"] == "hn"
        assert entry["title"] == "Show HN: my keyless research tool"
        assert entry["link"] == "https://example.com/tool"
        assert "88 pts" in entry["metric"]

    def test_falls_back_to_hn_item_link_when_url_missing(self):
        payload = {"hits": [{"title": "Ask HN: x", "url": None, "objectID": "123"}]}

        result = last30days.parse_hn_json(payload, limit=15)

        assert result[0]["link"] == "https://news.ycombinator.com/item?id=123"

    def test_respects_limit(self):
        payload = {"hits": [{"title": f"story {i}", "objectID": str(i)} for i in range(5)]}

        result = last30days.parse_hn_json(payload, limit=3)

        assert len(result) == 3


class TestParsePolymarketJson:
    def test_filters_markets_by_query_case_insensitively(self):
        payload = [
            {"question": "Will Bitcoin hit $100k in 2026?", "volume": "45231", "slug": "btc-100k-2026", "startDate": "2026-01-01"},
            {"question": "Will it rain in Paris tomorrow?", "volume": "500", "slug": "paris-rain", "startDate": "2026-01-01"},
        ]

        result = last30days.parse_polymarket_json(payload, "bitcoin", limit=15)

        assert len(result) == 1
        entry = result[0]
        assert entry["source"] == "polymarket"
        assert "Bitcoin" in entry["title"]
        assert entry["link"] == "https://polymarket.com/event/btc-100k-2026"
        assert "45231" in entry["metric"]

    def test_no_match_yields_empty_list(self):
        payload = [{"question": "Unrelated market", "volume": "1", "slug": "x"}]

        result = last30days.parse_polymarket_json(payload, "bitcoin", limit=15)

        assert result == []

    def test_respects_limit(self):
        payload = [{"question": f"bitcoin market {i}", "volume": "1", "slug": str(i)} for i in range(5)]

        result = last30days.parse_polymarket_json(payload, "bitcoin", limit=2)

        assert len(result) == 2


class TestParseGithubJson:
    def test_parses_items_into_entries(self):
        payload = {
            "items": [
                {
                    "full_name": "nous-research/hermes-agent",
                    "html_url": "https://github.com/nous-research/hermes-agent",
                    "stargazers_count": 42,
                    "pushed_at": "2026-07-01T00:00:00Z",
                }
            ]
        }

        result = last30days.parse_github_json(payload, limit=15)

        assert len(result) == 1
        entry = result[0]
        assert entry["source"] == "github"
        assert entry["title"] == "nous-research/hermes-agent"
        assert entry["link"] == "https://github.com/nous-research/hermes-agent"
        assert "42" in entry["metric"]

    def test_respects_limit(self):
        payload = {"items": [{"full_name": f"org/repo{i}"} for i in range(5)]}

        result = last30days.parse_github_json(payload, limit=1)

        assert len(result) == 1


class TestSearchAllErrorIsolation:
    def test_one_source_failing_does_not_drop_the_others(self, monkeypatch):
        monkeypatch.setattr(last30days, "fetch_reddit", lambda query, limit: (_ for _ in ()).throw(last30days.SourceFetchError("boom")))
        monkeypatch.setattr(last30days, "fetch_hn", lambda query, limit, cutoff_epoch: [{"source": "hn", "title": "ok", "date": "", "link": "", "metric": ""}])
        monkeypatch.setattr(last30days, "fetch_polymarket", lambda query, limit: [])
        monkeypatch.setattr(last30days, "fetch_github", lambda query, limit, cutoff_date: [])

        entries, errors = last30days.search_all("bitcoin", ["reddit", "hn", "polymarket", "github"], 15)

        assert len(entries) == 1
        assert entries[0]["source"] == "hn"
        assert "reddit" in errors
        assert "hn" not in errors

    def test_all_sources_succeeding_yields_no_errors(self, monkeypatch):
        monkeypatch.setattr(last30days, "fetch_reddit", lambda query, limit: [])
        monkeypatch.setattr(last30days, "fetch_hn", lambda query, limit, cutoff_epoch: [])
        monkeypatch.setattr(last30days, "fetch_polymarket", lambda query, limit: [])
        monkeypatch.setattr(last30days, "fetch_github", lambda query, limit, cutoff_date: [])

        entries, errors = last30days.search_all("bitcoin", last30days.SOURCES, 15)

        assert entries == []
        assert errors == {}

    def test_all_sources_failing_reports_error_per_source(self, monkeypatch):
        def _boom(*_args, **_kwargs):
            raise last30days.SourceFetchError("down")

        monkeypatch.setattr(last30days, "fetch_reddit", _boom)
        monkeypatch.setattr(last30days, "fetch_hn", _boom)
        monkeypatch.setattr(last30days, "fetch_polymarket", _boom)
        monkeypatch.setattr(last30days, "fetch_github", _boom)

        entries, errors = last30days.search_all("bitcoin", last30days.SOURCES, 15)

        assert entries == []
        assert set(errors) == set(last30days.SOURCES)


class TestMergedOutputStructure:
    def test_json_output_contains_entries_counts_and_errors(self, capsys):
        entries = [
            {"source": "reddit", "title": "a", "date": "", "link": "", "metric": ""},
            {"source": "hn", "title": "b", "date": "", "link": "", "metric": ""},
        ]

        last30days.print_json(entries, {"github": "boom"}, ["reddit", "hn", "github"])

        out = capsys.readouterr().out
        import json as _json
        payload = _json.loads(out)
        assert payload["counts"] == {"reddit": 1, "hn": 1, "github": 0}
        assert payload["errors"] == {"github": "boom"}
        assert len(payload["entries"]) == 2

    def test_table_output_prints_counts_line(self, capsys):
        entries = [{"source": "reddit", "title": "a", "date": "2024-01-01", "link": "https://x", "metric": "score 1"}]

        last30days.print_table(entries, {}, ["reddit"])

        out = capsys.readouterr().out
        assert "reddit=1" in out
        assert "https://x" in out
