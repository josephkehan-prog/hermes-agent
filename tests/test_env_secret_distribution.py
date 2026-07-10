"""Tests for the secret-distribution writer in hermes_cli.env_loader.

Covers upsert-in-place, append, routed extra destinations, and — since this
path handles secret values — that no VALUE ever appears in the returned
summary. Fully offline: everything lives under pytest's tmp_path, nothing
touches a real HERMES_HOME.
"""

import os

import pytest

from hermes_cli.env_loader import distribute_secrets, upsert_env_var


def test_upsert_env_var_replaces_existing_key_in_place(tmp_path):
    dest = tmp_path / ".env"
    dest.write_text("FOO=old\nBAR=keep-me\n", encoding="utf-8")

    action = upsert_env_var(dest, "FOO", "new-value")

    assert action == "updated"
    content = dest.read_text(encoding="utf-8")
    assert "FOO=new-value" in content
    assert "BAR=keep-me" in content
    # Order and sibling lines are preserved verbatim.
    assert content.splitlines() == ["FOO=new-value", "BAR=keep-me"]


def test_upsert_env_var_appends_when_key_absent(tmp_path):
    dest = tmp_path / ".env"
    dest.write_text("BAR=keep-me\n", encoding="utf-8")

    action = upsert_env_var(dest, "NEW_KEY", "shiny")

    assert action == "added"
    lines = dest.read_text(encoding="utf-8").splitlines()
    assert lines == ["BAR=keep-me", "NEW_KEY=shiny"]


def test_upsert_env_var_creates_missing_dest_with_chmod_600(tmp_path):
    dest = tmp_path / ".env"
    assert not dest.exists()

    action = upsert_env_var(dest, "FRESH", "value")

    assert action == "added"
    assert dest.read_text(encoding="utf-8") == "FRESH=value\n"
    mode = os.stat(dest).st_mode & 0o777
    assert mode == 0o600


def test_distribute_secrets_upsert_append_and_routes(tmp_path):
    home = tmp_path / "hermes_home"
    home.mkdir()
    canonical = home / ".env"
    canonical.write_text("EXISTING_KEY=stay-put\nFOO=old-canonical\n", encoding="utf-8")

    routed_dest = tmp_path / "other_service" / ".env"
    routed_dest.parent.mkdir()
    routed_dest.write_text("SIBLING=untouched\n", encoding="utf-8")

    inbox = tmp_path / "tokens.inbox"
    inbox.write_text(
        "\n".join(
            [
                "# a comment line, ignored",
                "",
                "FOO=super-secret-value",
                "NEW_TOKEN=another-secret",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    routes = {"FOO": [str(routed_dest)]}

    import hermes_cli.env_loader as env_loader

    monkeypatch_target = env_loader.get_env_path
    env_loader.get_env_path = lambda: canonical
    try:
        summary = distribute_secrets(inbox, routes=routes)
    finally:
        env_loader.get_env_path = monkeypatch_target

    # FOO -> canonical (updated, preserving EXISTING_KEY) + routed_dest (added).
    # NEW_TOKEN -> canonical only (added).
    assert len(summary) == 3

    canonical_content = canonical.read_text(encoding="utf-8")
    assert "EXISTING_KEY=stay-put" in canonical_content  # sibling key preserved
    assert "FOO=super-secret-value" in canonical_content
    assert "NEW_TOKEN=another-secret" in canonical_content

    routed_content = routed_dest.read_text(encoding="utf-8")
    assert "SIBLING=untouched" in routed_content  # sibling key preserved
    assert "FOO=super-secret-value" in routed_content

    # Actions reported correctly.
    by_dest_key = {(entry["key"], entry["dest"]): entry["action"] for entry in summary}
    assert by_dest_key[("FOO", str(canonical))] == "updated"
    assert by_dest_key[("FOO", str(routed_dest))] == "added"
    assert by_dest_key[("NEW_TOKEN", str(canonical))] == "added"

    # --- No secret VALUE anywhere in the returned summary. ---
    secret_values = {"super-secret-value", "another-secret", "stay-put", "untouched"}
    summary_text = repr(summary)
    for value in secret_values:
        # "super-secret-value" and "another-secret" are the actual planted
        # secrets; only those must never leak. (stay-put/untouched are
        # sibling-file content, checked for completeness.)
        if value in ("super-secret-value", "another-secret"):
            assert value not in summary_text
    for entry in summary:
        assert set(entry.keys()) == {"key", "action", "dest"}
        assert entry["action"] in ("added", "updated")


def test_distribute_secrets_rejects_malformed_key_naming_only_the_key(tmp_path):
    home = tmp_path / "hermes_home"
    home.mkdir()
    canonical = home / ".env"

    inbox = tmp_path / "tokens.inbox"
    inbox.write_text("BAD-KEY=some-secret-value\n", encoding="utf-8")

    import hermes_cli.env_loader as env_loader

    monkeypatch_target = env_loader.get_env_path
    env_loader.get_env_path = lambda: canonical
    try:
        with pytest.raises(ValueError) as excinfo:
            distribute_secrets(inbox)
    finally:
        env_loader.get_env_path = monkeypatch_target

    message = str(excinfo.value)
    assert "BAD-KEY" in message
    assert "some-secret-value" not in message


def test_distribute_secrets_rejects_empty_value(tmp_path):
    home = tmp_path / "hermes_home"
    home.mkdir()
    canonical = home / ".env"

    inbox = tmp_path / "tokens.inbox"
    inbox.write_text("EMPTY_KEY=\n", encoding="utf-8")

    import hermes_cli.env_loader as env_loader

    monkeypatch_target = env_loader.get_env_path
    env_loader.get_env_path = lambda: canonical
    try:
        with pytest.raises(ValueError, match="EMPTY_KEY"):
            distribute_secrets(inbox)
    finally:
        env_loader.get_env_path = monkeypatch_target
