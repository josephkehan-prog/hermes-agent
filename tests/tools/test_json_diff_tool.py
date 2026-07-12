"""Tests for tools/json_diff_tool.py — structured JSON diffing."""

import json

from tools import json_diff_tool


class TestJsonDiff:
    """json_diff compares two already-parsed JSON-compatible values."""

    def test_detects_added_and_modified_keys(self):
        # Arrange
        old = {"a": 1, "b": 2}
        new = {"a": 1, "b": 3, "c": 4}

        # Act
        result = json_diff_tool.json_diff(old, new)

        # Assert
        assert result["ok"] is True
        assert result["changed"] is True
        assert result["added"] == {"c": 4}
        assert result["removed"] == {}
        assert result["modified"] == {"b": {"old": 2, "new": 3}}

    def test_detects_removed_key(self):
        # Arrange
        old = {"a": 1, "b": 2}
        new = {"a": 1}

        # Act
        result = json_diff_tool.json_diff(old, new)

        # Assert
        assert result["changed"] is True
        assert result["removed"] == {"b": 2}
        assert result["added"] == {}
        assert result["modified"] == {}

    def test_identical_inputs_report_no_changes(self):
        # Arrange
        old = {"a": 1, "b": {"c": [1, 2, 3]}}
        new = {"a": 1, "b": {"c": [1, 2, 3]}}

        # Act
        result = json_diff_tool.json_diff(old, new)

        # Assert
        assert result["ok"] is True
        assert result["changed"] is False
        assert result["added"] == {} and result["removed"] == {} and result["modified"] == {}
        assert result["summary"] == "no changes"

    def test_nested_dict_change_reports_dotted_path(self):
        # Arrange
        old = {"a": {"b": {"c": 1}}}
        new = {"a": {"b": {"c": 2}}}

        # Act
        result = json_diff_tool.json_diff(old, new)

        # Assert
        assert result["modified"] == {"a.b.c": {"old": 1, "new": 2}}

    def test_list_index_change_reports_dotted_path(self):
        # Arrange
        old = {"a": {"b": [{"c": 1}]}}
        new = {"a": {"b": [{"c": 2}]}}

        # Act
        result = json_diff_tool.json_diff(old, new)

        # Assert
        assert result["modified"] == {"a.b.0.c": {"old": 1, "new": 2}}

    def test_list_grow_reports_added_by_index(self):
        # Arrange
        old = {"items": [1, 2]}
        new = {"items": [1, 2, 3]}

        # Act
        result = json_diff_tool.json_diff(old, new)

        # Assert
        assert result["added"] == {"items.2": 3}

    def test_list_shrink_reports_removed_by_index(self):
        # Arrange
        old = {"items": [1, 2, 3]}
        new = {"items": [1, 2]}

        # Act
        result = json_diff_tool.json_diff(old, new)

        # Assert
        assert result["removed"] == {"items.2": 3}

    def test_type_change_is_reported_as_modified(self):
        # Arrange
        old = {"a": {"nested": True}}
        new = {"a": "now-a-string"}

        # Act
        result = json_diff_tool.json_diff(old, new)

        # Assert
        assert result["modified"] == {"a": {"old": {"nested": True}, "new": "now-a-string"}}

    def test_deep_nesting_is_walked_fully(self):
        # Arrange
        old = {"a": {"b": {"c": {"d": [{"e": 1}]}}}}
        new = {"a": {"b": {"c": {"d": [{"e": 2}]}}}}

        # Act
        result = json_diff_tool.json_diff(old, new)

        # Assert
        assert result["modified"] == {"a.b.c.d.0.e": {"old": 1, "new": 2}}

    def test_does_not_mutate_inputs(self):
        # Arrange
        old = {"a": 1}
        new = {"a": 1, "b": 2}
        old_copy, new_copy = dict(old), dict(new)

        # Act
        json_diff_tool.json_diff(old, new)

        # Assert
        assert old == old_copy
        assert new == new_copy


class TestJsonDiffText:
    """json_diff_text parses two raw JSON strings, then delegates to json_diff."""

    def test_parses_and_diffs_valid_json_strings(self):
        # Arrange
        old_json_str = json.dumps({"a": 1, "b": 2})
        new_json_str = json.dumps({"a": 1, "b": 3, "c": 4})

        # Act
        result = json_diff_tool.json_diff_text(old_json_str, new_json_str)

        # Assert
        assert result["ok"] is True
        assert result["added"] == {"c": 4}
        assert result["modified"] == {"b": {"old": 2, "new": 3}}

    def test_invalid_json_in_old_returns_error_dict(self):
        # Arrange
        old_json_str = "{not valid json"
        new_json_str = json.dumps({"a": 1})

        # Act
        result = json_diff_tool.json_diff_text(old_json_str, new_json_str)

        # Assert
        assert result["ok"] is False
        assert "old_json_str" in result["error"]

    def test_invalid_json_in_new_returns_error_dict(self):
        # Arrange
        old_json_str = json.dumps({"a": 1})
        new_json_str = "{not valid json"

        # Act
        result = json_diff_tool.json_diff_text(old_json_str, new_json_str)

        # Assert
        assert result["ok"] is False
        assert "new_json_str" in result["error"]

    def test_oversized_input_is_rejected(self, monkeypatch):
        # Arrange
        monkeypatch.setattr(json_diff_tool, "_MAX_INPUT_CHARS", 10)
        old_json_str = json.dumps({"a": "way too long for the cap"})
        new_json_str = json.dumps({"a": 1})

        # Act
        result = json_diff_tool.json_diff_text(old_json_str, new_json_str)

        # Assert
        assert result["ok"] is False
        assert "limit" in result["error"]


class TestIgnorePaths:
    """ignore_paths drops changes at volatile dotted paths (e.g. timestamps)."""

    def test_ignores_exact_modified_path(self):
        old = {"data": 1, "meta": {"ts": 100}}
        new = {"data": 2, "meta": {"ts": 200}}

        result = json_diff_tool.json_diff(old, new, ignore_paths=["meta.ts"])

        assert result["changed"] is True
        assert result["modified"] == {"data": {"old": 1, "new": 2}}
        assert "meta.ts" not in result["modified"]

    def test_ignoring_only_change_yields_no_changes(self):
        old = {"meta": {"ts": 100}}
        new = {"meta": {"ts": 200}}

        result = json_diff_tool.json_diff(old, new, ignore_paths=["meta.ts"])

        assert result["changed"] is False
        assert result["summary"] == "no changes"

    def test_ignore_path_prefix_covers_subtree(self):
        old = {"meta": {"a": 1, "b": 2}, "keep": 1}
        new = {"meta": {"a": 9, "b": 9}, "keep": 2}

        result = json_diff_tool.json_diff(old, new, ignore_paths=["meta"])

        assert result["modified"] == {"keep": {"old": 1, "new": 2}}

    def test_ignore_prefix_does_not_match_sibling_by_string(self):
        # "meta" must not accidentally ignore "metadata"
        old = {"metadata": 1}
        new = {"metadata": 2}

        result = json_diff_tool.json_diff(old, new, ignore_paths=["meta"])

        assert result["modified"] == {"metadata": {"old": 1, "new": 2}}

    def test_ignores_added_and_removed_paths(self):
        old = {"keep": 1, "vol": {"x": 1}}
        new = {"keep": 1, "vol2": {"y": 2}}

        result = json_diff_tool.json_diff(old, new, ignore_paths=["vol", "vol2"])

        assert result["changed"] is False

    def test_ignore_paths_via_text_entrypoint(self):
        old = json.dumps({"n": 1, "t": 100})
        new = json.dumps({"n": 2, "t": 200})

        result = json_diff_tool.json_diff_text(old, new, ignore_paths=["t"])

        assert result["modified"] == {"n": {"old": 1, "new": 2}}

    def test_none_ignore_paths_is_full_diff(self):
        old = {"a": 1}
        new = {"a": 2}

        result = json_diff_tool.json_diff(old, new, ignore_paths=None)

        assert result["modified"] == {"a": {"old": 1, "new": 2}}
