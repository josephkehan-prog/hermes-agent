"""Tests for skills/research/open-databases/scripts/dbquery.py — no network, no external services."""

from __future__ import annotations

import argparse
import importlib.util
import sqlite3
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "skills" / "research" / "open-databases" / "scripts" / "dbquery.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("open_databases_dbquery_test_module", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dbquery = _load_script_module()


class _RecordingFetchJson:
    """Stand-in for dbquery.fetch_json — records the URL it was called with, no network."""

    def __init__(self, payload):
        self._payload = payload
        self.calls = []

    def __call__(self, url, headers=None):
        self.calls.append((url, headers))
        return self._payload


class TestTableNameValidation:
    def test_rejects_sql_injection_attempt_with_exit_code_2(self, tmp_path):
        db_path = tmp_path / "test.db"

        with pytest.raises(SystemExit) as exc_info:
            dbquery.dump_sqlite(str(db_path), "results; DROP TABLE results;--", [], ["a"])

        assert exc_info.value.code == 2

    def test_rejects_table_name_with_space(self, tmp_path):
        db_path = tmp_path / "test.db"

        with pytest.raises(SystemExit) as exc_info:
            dbquery.dump_sqlite(str(db_path), "my table", [], ["a"])

        assert exc_info.value.code == 2

    def test_rejects_table_name_starting_with_digit(self, tmp_path):
        db_path = tmp_path / "test.db"

        with pytest.raises(SystemExit) as exc_info:
            dbquery.dump_sqlite(str(db_path), "1results", [], ["a"])

        assert exc_info.value.code == 2

    def test_accepts_plain_identifier(self):
        assert dbquery.TABLE_NAME_RE.match("openalex_results")

    def test_accepts_identifier_with_underscore_and_digits(self):
        assert dbquery.TABLE_NAME_RE.match("_results_2024")


class TestDumpSqliteRoundTrip:
    def test_inserted_rows_are_readable_back_via_parameterized_insert(self, tmp_path):
        db_path = tmp_path / "results.db"
        columns = ["id", "title"]
        rows = [
            {"id": "1", "title": "Foo"},
            {"id": "2", "title": "Bar; DROP TABLE results_table;--"},
        ]

        dbquery.dump_sqlite(str(db_path), "results_table", rows, columns)

        connection = sqlite3.connect(str(db_path))
        try:
            stored = connection.execute('SELECT id, title FROM "results_table"').fetchall()
        finally:
            connection.close()
        assert stored == [("1", "Foo"), ("2", "Bar; DROP TABLE results_table;--")]

    def test_missing_column_values_default_to_empty_string(self, tmp_path):
        db_path = tmp_path / "results.db"
        columns = ["id", "title"]
        rows = [{"id": "1"}]  # "title" is absent

        dbquery.dump_sqlite(str(db_path), "results_table", rows, columns)

        connection = sqlite3.connect(str(db_path))
        try:
            stored = connection.execute('SELECT id, title FROM "results_table"').fetchall()
        finally:
            connection.close()
        assert stored == [("1", "")]

    def test_calling_twice_appends_rather_than_overwrites(self, tmp_path):
        db_path = tmp_path / "results.db"
        columns = ["id"]

        dbquery.dump_sqlite(str(db_path), "results_table", [{"id": "1"}], columns)
        dbquery.dump_sqlite(str(db_path), "results_table", [{"id": "2"}], columns)

        connection = sqlite3.connect(str(db_path))
        try:
            stored = connection.execute('SELECT id FROM "results_table"').fetchall()
        finally:
            connection.close()
        assert stored == [("1",), ("2",)]


class TestReadQueryFile:
    def test_bad_extension_exits_with_code_2(self, tmp_path):
        bad_file = tmp_path / "query.txt"
        bad_file.write_text("SELECT * WHERE { ?s ?p ?o }")

        with pytest.raises(SystemExit) as exc_info:
            dbquery.read_query_file(str(bad_file))

        assert exc_info.value.code == 2

    def test_rq_extension_is_read_successfully(self, tmp_path):
        query_file = tmp_path / "query.rq"
        query_file.write_text("SELECT * WHERE { ?s ?p ?o }")

        assert dbquery.read_query_file(str(query_file)) == "SELECT * WHERE { ?s ?p ?o }"

    def test_sparql_extension_is_read_successfully(self, tmp_path):
        query_file = tmp_path / "query.sparql"
        query_file.write_text("SELECT * WHERE { ?s ?p ?o }")

        assert dbquery.read_query_file(str(query_file)) == "SELECT * WHERE { ?s ?p ?o }"


class TestUrlBuildersUseQuote:
    def test_openalex_url_percent_encodes_spaces_not_plus(self, monkeypatch):
        recorder = _RecordingFetchJson({"results": []})
        monkeypatch.setattr(dbquery, "fetch_json", recorder)
        args = argparse.Namespace(query="deep learning & AI", type="works", limit=5)

        dbquery.cmd_openalex(args)

        url = recorder.calls[0][0]
        assert "deep%20learning" in url
        assert "deep+learning" not in url
        assert " " not in url

    def test_crossref_url_percent_encodes_query(self, monkeypatch):
        recorder = _RecordingFetchJson({"message": {"items": []}})
        monkeypatch.setattr(dbquery, "fetch_json", recorder)
        args = argparse.Namespace(query="climate change", limit=5)

        dbquery.cmd_crossref(args)

        url = recorder.calls[0][0]
        assert "climate%20change" in url
        assert "climate+change" not in url

    def test_wikidata_url_percent_encodes_sparql_query(self, monkeypatch):
        recorder = _RecordingFetchJson({"head": {"vars": []}, "results": {"bindings": []}})
        monkeypatch.setattr(dbquery, "fetch_json", recorder)
        args = argparse.Namespace(query="SELECT ?s WHERE { ?s ?p ?o }", query_file=None)

        dbquery.cmd_wikidata(args)

        url = recorder.calls[0][0]
        assert "SELECT%20%3Fs" in url
        assert "SELECT ?s" not in url

    def test_edgar_url_percent_encodes_query_and_includes_forms(self, monkeypatch):
        recorder = _RecordingFetchJson({"hits": {"hits": []}})
        monkeypatch.setattr(dbquery, "fetch_json", recorder)
        args = argparse.Namespace(query="Acme Corp", forms="10-K,10-Q", limit=10)

        dbquery.cmd_edgar(args)

        url = recorder.calls[0][0]
        assert "Acme%20Corp" in url
        assert "Acme+Corp" not in url
        assert "forms=10-K%2C10-Q" in url

    def test_wayback_url_percent_encodes_target_url(self, monkeypatch):
        recorder = _RecordingFetchJson([])
        monkeypatch.setattr(dbquery, "fetch_json", recorder)
        args = argparse.Namespace(url="https://example.com/a b?x=1&y=2", limit=20)

        dbquery.cmd_wayback(args)

        url = recorder.calls[0][0]
        assert "example.com%2Fa%20b%3Fx%3D1%26y%3D2" in url


class TestResponseShapeCrashRegressions:
    """Regression tests: each cmd_* must exit(2) on an unexpected top-level response
    shape rather than raising an uncaught AttributeError from .get()/indexing."""

    def test_openalex_non_dict_response_exits_with_code_2(self, monkeypatch):
        monkeypatch.setattr(dbquery, "fetch_json", _RecordingFetchJson([1, 2, 3]))
        args = argparse.Namespace(query="q", type="works", limit=5)

        with pytest.raises(SystemExit) as exc_info:
            dbquery.cmd_openalex(args)

        assert exc_info.value.code == 2

    def test_openalex_none_response_exits_with_code_2(self, monkeypatch):
        monkeypatch.setattr(dbquery, "fetch_json", _RecordingFetchJson(None))
        args = argparse.Namespace(query="q", type="works", limit=5)

        with pytest.raises(SystemExit) as exc_info:
            dbquery.cmd_openalex(args)

        assert exc_info.value.code == 2

    def test_crossref_non_dict_response_exits_with_code_2(self, monkeypatch):
        monkeypatch.setattr(dbquery, "fetch_json", _RecordingFetchJson([1, 2, 3]))
        args = argparse.Namespace(query="q", limit=5)

        with pytest.raises(SystemExit) as exc_info:
            dbquery.cmd_crossref(args)

        assert exc_info.value.code == 2

    def test_crossref_none_response_exits_with_code_2(self, monkeypatch):
        monkeypatch.setattr(dbquery, "fetch_json", _RecordingFetchJson(None))
        args = argparse.Namespace(query="q", limit=5)

        with pytest.raises(SystemExit) as exc_info:
            dbquery.cmd_crossref(args)

        assert exc_info.value.code == 2

    def test_wikidata_non_dict_response_exits_with_code_2(self, monkeypatch):
        monkeypatch.setattr(dbquery, "fetch_json", _RecordingFetchJson([1, 2, 3]))
        args = argparse.Namespace(query="SELECT ?s WHERE { ?s ?p ?o }", query_file=None)

        with pytest.raises(SystemExit) as exc_info:
            dbquery.cmd_wikidata(args)

        assert exc_info.value.code == 2

    def test_wikidata_none_response_exits_with_code_2(self, monkeypatch):
        monkeypatch.setattr(dbquery, "fetch_json", _RecordingFetchJson(None))
        args = argparse.Namespace(query="SELECT ?s WHERE { ?s ?p ?o }", query_file=None)

        with pytest.raises(SystemExit) as exc_info:
            dbquery.cmd_wikidata(args)

        assert exc_info.value.code == 2

    def test_edgar_non_dict_response_exits_with_code_2(self, monkeypatch):
        monkeypatch.setattr(dbquery, "fetch_json", _RecordingFetchJson([1, 2, 3]))
        args = argparse.Namespace(query="q", forms=None, limit=10)

        with pytest.raises(SystemExit) as exc_info:
            dbquery.cmd_edgar(args)

        assert exc_info.value.code == 2

    def test_edgar_none_response_exits_with_code_2(self, monkeypatch):
        monkeypatch.setattr(dbquery, "fetch_json", _RecordingFetchJson(None))
        args = argparse.Namespace(query="q", forms=None, limit=10)

        with pytest.raises(SystemExit) as exc_info:
            dbquery.cmd_edgar(args)

        assert exc_info.value.code == 2

    def test_wayback_non_list_dict_response_exits_with_code_2(self, monkeypatch):
        # A dict is truthy so it skips the `if not data` early return, and previously
        # fell into `header, *records = data`, silently unpacking dict keys as garbage.
        monkeypatch.setattr(dbquery, "fetch_json", _RecordingFetchJson({"unexpected": "shape"}))
        args = argparse.Namespace(url="https://example.com", limit=20)

        with pytest.raises(SystemExit) as exc_info:
            dbquery.cmd_wayback(args)

        assert exc_info.value.code == 2
