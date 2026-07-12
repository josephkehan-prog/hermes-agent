"""Tests for session_search after/before date filters (discovery shape)."""
import json
import time
from datetime import datetime, timedelta

import pytest

from hermes_state import SessionDB
from tools.session_search_tool import SESSION_SEARCH_SCHEMA, session_search


@pytest.fixture
def db(tmp_path):
    return SessionDB(tmp_path / "state.db")


def _seed(db):
    """Two sessions about rockets: one ~10 days old, one ~1 hour old."""
    now = time.time()
    old_ts = now - 10 * 86400
    new_ts = now - 3600

    db.create_session("s_old", source="cli")
    db.append_message("s_old", role="user", content="rocket telemetry looks wrong")
    db.append_message("s_old", role="assistant", content="Fixed the rocket telemetry parser.")

    db.create_session("s_new", source="cli")
    db.append_message("s_new", role="user", content="rocket launch checklist please")
    db.append_message("s_new", role="assistant", content="Here is the rocket launch checklist.")

    db._conn.execute("UPDATE messages SET timestamp = ? WHERE session_id = ?", (old_ts, "s_old"))
    db._conn.execute("UPDATE messages SET timestamp = ? WHERE session_id = ?", (new_ts, "s_new"))
    db._conn.execute("UPDATE sessions SET started_at = ? WHERE id = ?", (old_ts, "s_old"))
    db._conn.execute("UPDATE sessions SET started_at = ? WHERE id = ?", (new_ts, "s_new"))
    db._conn.commit()
    return old_ts, new_ts


def _session_ids(result_json):
    data = json.loads(result_json)
    assert data["success"], data
    return {r["session_id"] for r in data["results"]}


def test_after_excludes_older_sessions(db):
    _seed(db)
    cutoff = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    ids = _session_ids(session_search(query="rocket", after=cutoff, db=db))
    assert ids == {"s_new"}


def test_before_excludes_newer_sessions(db):
    _seed(db)
    cutoff = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    ids = _session_ids(session_search(query="rocket", before=cutoff, db=db))
    assert ids == {"s_old"}


def test_after_and_before_window(db):
    old_ts, _ = _seed(db)
    start = datetime.fromtimestamp(old_ts - 86400).strftime("%Y-%m-%d")
    end = datetime.fromtimestamp(old_ts + 86400).strftime("%Y-%m-%d")
    ids = _session_ids(session_search(query="rocket", after=start, before=end, db=db))
    assert ids == {"s_old"}


def test_before_date_only_is_inclusive_end_of_day(db):
    _, new_ts = _seed(db)
    same_day = datetime.fromtimestamp(new_ts).strftime("%Y-%m-%d")
    ids = _session_ids(session_search(query="rocket", before=same_day, db=db))
    assert "s_new" in ids


def test_no_filters_returns_both(db):
    _seed(db)
    ids = _session_ids(session_search(query="rocket", db=db))
    assert ids == {"s_old", "s_new"}


def test_invalid_date_is_clear_error(db):
    _seed(db)
    data = json.loads(session_search(query="rocket", after="not-a-date", db=db))
    assert data["success"] is False
    assert "after" in data["error"].lower() or "date" in data["error"].lower()


def test_schema_documents_date_filters():
    props = SESSION_SEARCH_SCHEMA["parameters"]["properties"]
    assert "after" in props and "before" in props
    assert props["after"]["type"] == "string"
    assert props["before"]["type"] == "string"
