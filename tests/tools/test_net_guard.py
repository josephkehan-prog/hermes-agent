"""Tests for tools/_net_guard.py — shared SSRF / fetch-safety helpers."""

from unittest.mock import MagicMock, patch

import pytest

from tools import _net_guard


class TestValidateHostname:
    def test_accepts_plain_domain(self):
        assert _net_guard.validate_hostname("example.com") is True

    def test_accepts_subdomain(self):
        assert _net_guard.validate_hostname("api.example.co.uk") is True

    def test_rejects_empty(self):
        assert _net_guard.validate_hostname("") is False

    def test_rejects_non_string(self):
        assert _net_guard.validate_hostname(None) is False
        assert _net_guard.validate_hostname(12345) is False

    def test_rejects_shell_injection_attempt(self):
        assert _net_guard.validate_hostname("example.com; rm -rf /") is False

    def test_rejects_single_label(self):
        assert _net_guard.validate_hostname("localhost") is False

    def test_rejects_overlong_hostname(self):
        overlong = ("a" * 64 + ".") * 4 + "com"
        assert _net_guard.validate_hostname(overlong) is False

    def test_rejects_leading_or_trailing_hyphen_label(self):
        assert _net_guard.validate_hostname("-example.com") is False
        assert _net_guard.validate_hostname("example-.com") is False


class TestRequireHttpScheme:
    def test_accepts_http(self):
        assert _net_guard.require_http_scheme("http://example.com") == "http://example.com"

    def test_accepts_https(self):
        url = "https://example.com/path"
        assert _net_guard.require_http_scheme(url) == url

    def test_rejects_file_scheme(self):
        with pytest.raises(_net_guard.NetGuardError, match="unsupported URL scheme"):
            _net_guard.require_http_scheme("file:///etc/passwd")

    def test_rejects_ftp_scheme(self):
        with pytest.raises(_net_guard.NetGuardError, match="unsupported URL scheme"):
            _net_guard.require_http_scheme("ftp://example.com")


class TestRejectPrivateTarget:
    def test_rejects_loopback_ip_literal(self):
        with pytest.raises(_net_guard.NetGuardError, match="non-public address"):
            _net_guard.reject_private_target("http://127.0.0.1/")

    def test_rejects_ipv6_loopback_literal(self):
        with pytest.raises(_net_guard.NetGuardError, match="non-public address"):
            _net_guard.reject_private_target("http://[::1]/")

    def test_rejects_cloud_metadata_ip_literal(self):
        with pytest.raises(_net_guard.NetGuardError, match="non-public address"):
            _net_guard.reject_private_target("http://169.254.169.254/latest/meta-data/")

    def test_rejects_hostname_resolving_to_private_ip(self):
        with patch.object(_net_guard.socket, "gethostbyname", return_value="10.0.0.5"):
            with pytest.raises(_net_guard.NetGuardError, match="non-public address"):
                _net_guard.reject_private_target("http://internal.example.com/")

    def test_allows_hostname_resolving_to_public_ip(self):
        with patch.object(_net_guard.socket, "gethostbyname", return_value="93.184.216.34"):
            _net_guard.reject_private_target("http://example.com/")  # does not raise

    def test_rejects_unresolvable_hostname(self):
        import socket as socket_module

        with patch.object(
            _net_guard.socket, "gethostbyname", side_effect=socket_module.gaierror("nope")
        ):
            with pytest.raises(_net_guard.NetGuardError, match="could not resolve host"):
                _net_guard.reject_private_target("http://does-not-exist.invalid/")

    def test_rejects_url_with_no_hostname(self):
        with pytest.raises(_net_guard.NetGuardError, match="could not determine hostname"):
            _net_guard.reject_private_target("file:///etc/passwd")

    def test_rejects_leading_zero_octal_octet(self):
        """0177.0.0.1: ipaddress.ip_address() correctly refuses to guess
        whether the leading zero means octal, so this must be rejected
        outright rather than falling through to socket.gethostbyname(),
        whose octal interpretation is glibc/platform-dependent and can
        resolve this straight to 127.0.0.1 on Linux (classic SSRF bypass)."""
        with pytest.raises(_net_guard.NetGuardError, match="ambiguous numeric host"):
            _net_guard.reject_private_target("http://0177.0.0.1/")

    def test_rejects_bare_decimal_integer_host(self):
        with pytest.raises(_net_guard.NetGuardError, match="ambiguous numeric host"):
            _net_guard.reject_private_target("http://2130706433/")  # == 127.0.0.1

    def test_rejects_hex_literal_host(self):
        with pytest.raises(_net_guard.NetGuardError, match="ambiguous numeric host"):
            _net_guard.reject_private_target("http://0x7f000001/")  # == 127.0.0.1

    def test_rejects_short_dotted_form_host(self):
        with pytest.raises(_net_guard.NetGuardError, match="ambiguous numeric host"):
            _net_guard.reject_private_target("http://127.1/")  # inet_aton shorthand for 127.0.0.1

    def test_does_not_flag_ordinary_hostname_as_ambiguous(self):
        """A normal hostname (letters present) must never hit the
        ambiguous-numeric pre-filter — only resolve/private-IP checks apply."""
        with patch.object(_net_guard.socket, "gethostbyname", return_value="93.184.216.34"):
            _net_guard.reject_private_target("http://example.com/")  # does not raise


class TestSafeRedirectHandler:
    def test_refuses_redirect_to_loopback(self):
        handler = _net_guard.SafeRedirectHandler()
        req = MagicMock()

        with pytest.raises(_net_guard.NetGuardError, match="non-public address"):
            handler.redirect_request(
                req, None, 302, "Found", {}, "http://127.0.0.1/secret"
            )

    def test_refuses_redirect_to_disallowed_scheme(self):
        handler = _net_guard.SafeRedirectHandler()
        req = MagicMock()

        with pytest.raises(_net_guard.NetGuardError, match="unsupported URL scheme"):
            handler.redirect_request(req, None, 302, "Found", {}, "file:///etc/passwd")

    def test_allows_redirect_to_public_target(self):
        handler = _net_guard.SafeRedirectHandler()
        req = MagicMock()

        with patch.object(_net_guard.socket, "gethostbyname", return_value="93.184.216.34"):
            with patch.object(
                _net_guard.urllib.request.HTTPRedirectHandler,
                "redirect_request",
                return_value="sentinel-request",
            ) as mock_super:
                result = handler.redirect_request(
                    req, None, 302, "Found", {}, "https://example.com/new-path"
                )

        mock_super.assert_called_once()
        assert result == "sentinel-request"

    def test_max_redirections_matches_guard_limit(self):
        assert _net_guard.SafeRedirectHandler.max_redirections == _net_guard.MAX_REDIRECTS


class TestBuildSafeOpener:
    def test_returns_opener_with_safe_redirect_handler(self):
        opener = _net_guard.build_safe_opener()

        handler_types = [type(h) for h in opener.handlers]
        assert _net_guard.SafeRedirectHandler in handler_types


class TestReadCapped:
    def test_returns_body_under_cap(self):
        response = MagicMock()
        response.read.return_value = b"hello"

        assert _net_guard.read_capped(response) == b"hello"

    def test_rejects_body_over_cap(self):
        response = MagicMock()
        response.read.return_value = b"x" * (_net_guard.MAX_RESPONSE_BYTES + 1)

        with pytest.raises(_net_guard.NetGuardError, match="exceeds"):
            _net_guard.read_capped(response)

    def test_reads_with_cap_plus_one_bound(self):
        response = MagicMock()
        response.read.return_value = b"ok"

        _net_guard.read_capped(response)

        response.read.assert_called_once_with(_net_guard.MAX_RESPONSE_BYTES + 1)
