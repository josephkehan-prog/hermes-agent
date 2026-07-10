"""Tests for skills/research/social-footprint/scripts/footprint.py — no network by default."""

from __future__ import annotations

import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "skills" / "research" / "social-footprint" / "scripts" / "footprint.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("social_footprint_test_module", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


footprint = _load_script_module()


class TestEmailPermutations:
    def test_generates_expected_candidate_addresses_no_network(self):
        candidates = footprint.email_permutations("John", "Doe", "example.com")

        assert "john.doe@example.com" in candidates
        assert "johndoe@example.com" in candidates
        assert "john@example.com" in candidates
        assert "doe@example.com" in candidates
        assert "j.doe@example.com" in candidates
        assert "jdoe@example.com" in candidates
        assert "doe.john@example.com" in candidates
        assert all(addr.endswith("@example.com") for addr in candidates)

    def test_lowercases_mixed_case_names(self):
        candidates = footprint.email_permutations("JoHn", "DOE", "example.com")

        assert "john.doe@example.com" in candidates

    def test_no_duplicate_candidates(self):
        candidates = footprint.email_permutations("A", "B", "example.com")

        assert len(candidates) == len(set(candidates))

    def test_cli_email_permute_prints_candidates(self):
        args = footprint.build_parser().parse_args(["email-permute", "John", "Doe", "example.com"])
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = args.func(args)

        assert code == 0
        assert "john.doe@example.com" in buf.getvalue()

    def test_cli_email_permute_json_output(self):
        args = footprint.build_parser().parse_args(["email-permute", "John", "Doe", "example.com", "--json"])
        buf = io.StringIO()
        with redirect_stdout(buf):
            args.func(args)

        payload = json.loads(buf.getvalue())
        assert "john.doe@example.com" in payload["candidates"]


class TestGravatarHash:
    def test_known_md5_matches_gravatar_spec_example(self):
        # Gravatar's own docs use this example: MD5 of the lowercased,
        # trimmed address "MyEmailAddress@example.com" (Gravatar API docs).
        digest = footprint.gravatar_hash("MyEmailAddress@example.com")

        assert digest == "0bc83cb571cd1c50ba6f3e8a78ef1346"

    def test_hash_is_case_and_whitespace_insensitive(self):
        a = footprint.gravatar_hash("  Test@Example.com  ")
        b = footprint.gravatar_hash("test@example.com")

        assert a == b

    def test_hash_is_32_char_hex(self):
        digest = footprint.gravatar_hash("someone@example.com")

        assert len(digest) == 32
        int(digest, 16)  # raises ValueError if not valid hex


class TestUsernameValidation:
    def test_accepts_normal_username(self):
        assert footprint.validate_username("octocat") == "octocat"

    def test_accepts_dots_hyphens_underscores(self):
        assert footprint.validate_username("a.b-c_d") == "a.b-c_d"

    @pytest.mark.parametrize(
        "bad",
        [
            "",
            "a" * 40,
            "user name",  # space
            "user/name",  # path injection
            "user?x=1",  # query injection
            "../etc/passwd",
            "user;rm -rf",
            "user\nname",
        ],
    )
    def test_rejects_invalid_or_injection_usernames(self, bad):
        with pytest.raises(footprint.FootprintError):
            footprint.validate_username(bad)


class TestEmailValidation:
    def test_accepts_valid_email(self):
        assert footprint.validate_email("test@example.com") == "test@example.com"

    @pytest.mark.parametrize(
        "bad",
        ["", "no-at-sign", "@example.com", "user@", "user @example.com", "user@bad domain"],
    )
    def test_rejects_invalid_email(self, bad):
        with pytest.raises(footprint.FootprintError):
            footprint.validate_email(bad)


class TestDomainValidation:
    def test_accepts_bare_domain(self):
        assert footprint.validate_domain("example.com") == "example.com"

    @pytest.mark.parametrize("bad", ["", "example", "has space.com", "user@example.com"])
    def test_rejects_invalid_domain(self, bad):
        with pytest.raises(footprint.FootprintError):
            footprint.validate_domain(bad)


class TestClassifyPresenceLogic:
    def test_reliable_site_404_control_and_404_target_is_absent(self):
        status = footprint._classify(404, 404, b"", b"")
        assert status == "absent"

    def test_reliable_site_404_control_and_200_target_is_present(self):
        status = footprint._classify(404, 200, b"", b"body")
        assert status == "present"

    def test_soft_404_site_similar_bodies_is_absent(self):
        status = footprint._classify(200, 200, b"not found page" * 10, b"not found page" * 10)
        assert status == "absent"

    def test_soft_404_site_differing_bodies_is_manual(self):
        status = footprint._classify(200, 200, b"x" * 10, b"y" * 5000)
        assert status == "manual"

    def test_no_target_status_is_error(self):
        status = footprint._classify(404, None, b"", b"")
        assert status == "error"


class TestHibpStub:
    def test_hibp_stub_prints_needs_review_flag_and_does_not_hit_network(self, monkeypatch):
        def _fail_if_called(*_args, **_kwargs):
            raise AssertionError("hibp stub must not make network calls")

        monkeypatch.setattr(footprint, "fetch_status", _fail_if_called)
        args = footprint.build_parser().parse_args(["hibp", "test@example.com"])
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = args.func(args)

        assert code == 0
        assert "NEEDS-REVIEW" in buf.getvalue()
        assert "PAID API key" in buf.getvalue()

    def test_hibp_stub_rejects_invalid_email(self):
        args = footprint.build_parser().parse_args(["hibp", "not-an-email"])
        with pytest.raises(footprint.FootprintError):
            args.func(args)


class TestRequireHttpScheme:
    def test_rejects_file_scheme(self):
        with pytest.raises(footprint.FootprintError):
            footprint._require_http_scheme("file:///etc/passwd")

    def test_allows_https(self):
        footprint._require_http_scheme("https://example.com")


@pytest.mark.skip(reason="live network test — run manually, not in CI")
class TestLiveUsernameCheck:
    def test_live_username_lookup_against_own_throwaway_handle(self):
        args = footprint.build_parser().parse_args(["username", "octocat", "--json"])
        buf = io.StringIO()
        with redirect_stdout(buf):
            args.func(args)

        payload = json.loads(buf.getvalue())
        assert payload["username"] == "octocat"
        assert len(payload["results"]) == len(footprint.PLATFORMS)
