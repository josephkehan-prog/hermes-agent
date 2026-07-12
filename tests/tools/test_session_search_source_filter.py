"""session_search `source` filter (discovery shape): restrict hits by session source."""
import json

import pytest

from hermes_state import SessionDB
from tools.session_search_tool import SESSION_SEARCH_SCHEMA, session_search


@pytest.fixture
def db(tmp_path):
    return SessionDB(tmp_path / "state.db")


def _seed(db):
    """Same query term across three sources: cli, telegram, discord."""
    for sid, source in (("s_cli", "cli"), ("s_tg", "telegram"), ("s_dc", "discord")):
        db.create_session(sid, source=source)
        db.append_message(sid, role="user", content="deploy the rocket please")
        db.append_message(sid, role="assistant", content="rocket deploy acknowledged")
    db._conn.commit()


def _sources(result_json):
    data = json.loads(result_json)
    assert data["success"], data
    return {r.get("source") for r in data["results"]}


def test_no_source_returns_all(db):
    _seed(db)
    assert _sources(session_search(query="rocket", limit=10, db=db)) == {
        "cli",
        "telegram",
        "discord",
    }


def test_single_source_filters(db):
    _seed(db)
    assert _sources(session_search(query="rocket", source="telegram", limit=10, db=db)) == {
        "telegram"
    }


def test_multiple_sources_comma_separated(db):
    _seed(db)
    got = _sources(session_search(query="rocket", source="telegram,discord", limit=10, db=db))
    assert got == {"telegram", "discord"}


def test_unknown_source_yields_no_results(db):
    _seed(db)
    data = json.loads(session_search(query="rocket", source="nonexistent", limit=10, db=db))
    assert data["success"] is True
    assert data["count"] == 0


def test_blank_source_is_ignored(db):
    _seed(db)
    assert _sources(session_search(query="rocket", source="   ", limit=10, db=db)) == {
        "cli",
        "telegram",
        "discord",
    }


def test_schema_documents_source():
    props = SESSION_SEARCH_SCHEMA["parameters"]["properties"]
    assert "source" in props
    assert props["source"]["type"] == "string"


class TestHandlerThreadsDiscoveryParams:
    """Regression: the registered tool handler must forward source/after/before
    to session_search (they were previously documented but dropped)."""

    def _handler(self):
        from tools.registry import registry

        entry = registry.get_entry("session_search")
        assert entry is not None
        return entry.handler

    def test_handler_forwards_source(self, db):
        _seed(db)
        result = self._handler()({"query": "rocket", "source": "telegram", "limit": 10}, db=db)
        assert _sources(result) == {"telegram"}

    def test_handler_forwards_before(self, db):
        import time

        _seed(db)
        # Push every seeded message far into the past, then filter to before now.
        old = time.time() - 10 * 86400
        db._conn.execute("UPDATE messages SET timestamp = ?", (old,))
        db._conn.commit()
        from datetime import datetime, timedelta

        cutoff = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        # before the cutoff → all three old sessions present
        data = json.loads(self._handler()({"query": "rocket", "before": cutoff, "limit": 10}, db=db))
        assert data["success"] is True
        assert data["count"] == 3
        # after the cutoff → none (all messages are 10 days old)
        data2 = json.loads(self._handler()({"query": "rocket", "after": cutoff, "limit": 10}, db=db))
        assert data2["count"] == 0
