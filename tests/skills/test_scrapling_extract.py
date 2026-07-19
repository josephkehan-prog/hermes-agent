"""Tests for skills/research/scrapling/scripts/extract.py — no network, no external services."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "skills" / "research" / "scrapling" / "scripts" / "extract.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("scrapling_extract_test_module", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


extract = _load_script_module()


class _FakeHeaders:
    """Minimal stand-in for http.client.HTTPMessage — only what extract.py reads."""

    def __init__(self, content_type):
        self._content_type = content_type

    def get(self, key, default=None):
        if key == "Content-Type":
            return self._content_type
        return default

    def get_content_charset(self):
        return "utf-8"


class _FakeResponse:
    """Minimal stand-in for a urllib response object — no real network involved."""

    def __init__(self, body: bytes, content_type):
        self.headers = _FakeHeaders(content_type)
        self._body = body

    def read(self, amt=None):
        return self._body if amt is None else self._body[:amt]


class TestHandleUrllibResponse:
    def test_json_content_type_is_pretty_printed_with_json_method(self):
        body = b'{"a":1,"b":2}'
        response = _FakeResponse(body, "application/json; charset=utf-8")

        result = extract._handle_urllib_response(response)

        assert result["method"] == "json"
        assert result["page"] == json.dumps({"a": 1, "b": 2}, indent=2, ensure_ascii=False)

    def test_html_content_is_stripped_of_script_and_style_via_extract_text(self):
        html_body = (
            b"<html><head><style>body{color:red}</style></head>"
            b"<body><script>alert(1)</script><p>Hello world</p></body></html>"
        )
        response = _FakeResponse(html_body, "text/html; charset=utf-8")

        fetched = extract._handle_urllib_response(response)
        text = extract.extract_text(fetched, css_selector=None)

        assert fetched["method"] == "urllib"
        assert "Hello world" in text
        assert "alert(1)" not in text
        assert "color:red" not in text

    def test_binary_content_type_exits_with_code_2(self):
        response = _FakeResponse(b"%PDF-1.4 fake binary body", "application/pdf")

        with pytest.raises(SystemExit) as exc_info:
            extract._handle_urllib_response(response)

        assert exc_info.value.code == 2

    def test_empty_content_type_is_treated_as_text(self):
        body = b"plain body text"
        response = _FakeResponse(body, "")

        result = extract._handle_urllib_response(response)

        assert result["method"] == "urllib"
        assert result["page"] == "plain body text"

    def test_response_over_byte_cap_exits_with_code_2(self):
        oversized_body = b"x" * (extract.MAX_RESPONSE_BYTES + 1)
        response = _FakeResponse(oversized_body, "text/plain")

        with pytest.raises(SystemExit) as exc_info:
            extract._handle_urllib_response(response)

        assert exc_info.value.code == 2


class TestRequireHttpScheme:
    def test_file_scheme_exits_with_code_2(self):
        with pytest.raises(SystemExit) as exc_info:
            extract._require_http_scheme("file:///etc/passwd")

        assert exc_info.value.code == 2

    def test_http_scheme_is_allowed(self):
        extract._require_http_scheme("http://example.com")

    def test_https_scheme_is_allowed(self):
        extract._require_http_scheme("https://example.com")


class TestPrettyJson:
    def test_invalid_json_falls_back_to_raw_text_without_crashing(self):
        raw = "  not valid json  "

        result = extract._pretty_json(raw)

        assert result == raw.strip()


class TestExtractText:
    def test_json_method_returns_page_unmodified(self):
        fetched = {"method": "json", "page": '{\n  "a": 1\n}'}

        result = extract.extract_text(fetched, css_selector=None)

        assert result == fetched["page"]


class TestStripHtml:
    def test_strip_html_drops_script_and_style_content(self):
        html_content = "<div><script>var x = 1;</script><style>.a{color:red}</style><p>Visible</p></div>"

        text = extract._strip_html(html_content)

        assert text == "Visible"
