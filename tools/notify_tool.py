"""Keyless push notifications via ntfy.sh (monitoring/alerting support).

``notify`` POSTs a message to a public or self-hosted ntfy server
(https://ntfy.sh by default) — free, no API key, no account. Any device
subscribed to the topic (phone app, desktop, browser) receives a push. This
module only shells out to urllib against the ntfy HTTP API; no code from the
ntfy project is vendored here. Credit: ntfy
(https://github.com/binwiederhier/ntfy, Apache License 2.0 — Copyright (c)
Philipp Heckel).

ntfy topics are public by default — anyone who knows (or guesses) the topic
name can subscribe and read messages, or publish to it. Callers should use
long, unguessable topic names for anything sensitive; this module does not
enforce that, it only validates the topic against ntfy's own charset rules
(``^[a-zA-Z0-9_-]{1,64}$``) to reject path-traversal/injection attempts
before it ever reaches the URL.

SSRF note: only ``http``/``https`` server URLs are accepted (``file://``,
``ftp://``, etc. are rejected), and the resolved host is checked against
private/reserved/loopback/link-local ranges (including cloud metadata
endpoints) via ``tools._net_guard``. ``server`` defaults to the public
ntfy.sh instance but a self-hosted server URL may be passed instead.
"""

import json
import re
import urllib.error
import urllib.request
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from tools import _net_guard
from tools.registry import registry

_USER_AGENT = "Hermes-Agent (https://github.com/NousResearch/hermes-agent)"
_TIMEOUT_S = _net_guard.DEFAULT_TIMEOUT_SECONDS
_ALLOWED_SCHEMES = _net_guard.ALLOWED_SCHEMES
_DEFAULT_SERVER = "https://ntfy.sh"
_TOPIC_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
_MIN_PRIORITY = 1
_MAX_PRIORITY = 5
_MAX_MESSAGE_LEN = 4096
_MAX_RESPONSE_BYTES = _net_guard.MAX_RESPONSE_BYTES


def _validate_topic(topic: Any) -> Optional[str]:
    """Return topic if it matches ntfy's charset rules, else None."""
    if not isinstance(topic, str):
        return None
    topic = topic.strip()
    if not _TOPIC_RE.match(topic):
        return None
    return topic


def _validate_server(server: Any) -> Optional[str]:
    """Return server stripped of a trailing slash if it's a well-formed
    http(s) URL, else None."""
    if not isinstance(server, str) or not server.strip():
        return None
    candidate = server.strip().rstrip("/")
    parsed = urlparse(candidate)
    if parsed.scheme.lower() not in _ALLOWED_SCHEMES or not parsed.netloc:
        return None
    return candidate


def _validate_message(message: Any) -> Optional[str]:
    """Return message if it's a non-empty string within the length cap, else None."""
    if not isinstance(message, str) or not message.strip():
        return None
    if len(message) > _MAX_MESSAGE_LEN:
        return None
    return message


def _validate_priority(priority: Any) -> Optional[int]:
    """Return priority as an int in [1, 5] if valid, None if unset,
    or raise ValueError if present but out of range/non-numeric."""
    if priority is None:
        return None
    try:
        priority_int = int(priority)
    except (TypeError, ValueError):
        raise ValueError(f"priority must be an integer {_MIN_PRIORITY}-{_MAX_PRIORITY}, got {priority!r}")
    if not (_MIN_PRIORITY <= priority_int <= _MAX_PRIORITY):
        raise ValueError(f"priority must be between {_MIN_PRIORITY} and {_MAX_PRIORITY}, got {priority_int}")
    return priority_int


def notify(
    message: Any,
    topic: Any,
    title: Any = None,
    priority: Any = None,
    tags: Any = None,
    server: Any = _DEFAULT_SERVER,
) -> Dict[str, Any]:
    """Send a push notification to an ntfy topic.

    Any device subscribed to ``topic`` on ``server`` receives the message as
    a push notification. Returns {ok, topic} on success, {ok: False, error}
    on invalid input or request failure.
    """
    valid_topic = _validate_topic(topic)
    if valid_topic is None:
        return {"ok": False, "error": f"invalid topic: {topic!r} (must match ^[a-zA-Z0-9_-]{{1,64}}$)"}

    valid_server = _validate_server(server)
    if valid_server is None:
        return {"ok": False, "error": f"invalid or disallowed server url: {server!r} (http/https only)"}

    valid_message = _validate_message(message)
    if valid_message is None:
        return {"ok": False, "error": f"message must be a non-empty string of at most {_MAX_MESSAGE_LEN} chars"}

    try:
        valid_priority = _validate_priority(priority)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    headers = {"User-Agent": _USER_AGENT}
    if title:
        headers["X-Title"] = str(title)
    if valid_priority is not None:
        headers["X-Priority"] = str(valid_priority)
    if tags:
        tag_list = tags if isinstance(tags, (list, tuple)) else [tags]
        headers["X-Tags"] = ",".join(str(tag) for tag in tag_list)

    url = f"{valid_server}/{valid_topic}"
    try:
        _net_guard.reject_private_target(url)
    except _net_guard.NetGuardError as exc:
        return {"ok": False, "error": str(exc)}

    req = urllib.request.Request(url, data=valid_message.encode("utf-8"), headers=headers, method="POST")
    opener = _net_guard.build_safe_opener()
    try:
        with opener.open(req, timeout=_TIMEOUT_S) as resp:
            _net_guard.read_capped(resp)
    except _net_guard.NetGuardError as exc:
        return {"ok": False, "error": str(exc)}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error": f"http error {exc.code}: {exc.reason}"}
    except urllib.error.URLError as exc:
        return {"ok": False, "error": f"could not reach ntfy server: {exc.reason}"}
    except (TimeoutError, OSError) as exc:
        return {"ok": False, "error": str(exc)}

    return {"ok": True, "topic": valid_topic}


registry.register(
    name="notify",
    toolset="monitoring",
    schema={
        "name": "notify",
        "description": (
            "Send a push notification to a phone/desktop via ntfy.sh (free, "
            "keyless, no account). Anyone subscribed to `topic` gets an "
            "instant push. Use a long, unguessable topic name for anything "
            "sensitive since ntfy topics are public by default. Good as an "
            "alert backend for monitoring/watch tasks."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": f"Notification body (max {_MAX_MESSAGE_LEN} chars)."},
                "topic": {
                    "type": "string",
                    "description": "ntfy topic name to publish to (^[a-zA-Z0-9_-]{1,64}$). Devices subscribe to this exact name.",
                },
                "title": {"type": "string", "description": "Optional notification title."},
                "priority": {
                    "type": "integer",
                    "description": f"Optional priority {_MIN_PRIORITY} (min) to {_MAX_PRIORITY} (max/urgent).",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional emoji-shortcode tags (e.g. 'warning', 'rotating_light'), rendered as icons.",
                },
                "server": {
                    "type": "string",
                    "description": f"ntfy server base URL (http/https). Defaults to the public {_DEFAULT_SERVER}.",
                },
            },
            "required": ["message", "topic"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        notify(
            message=args.get("message", ""),
            topic=args.get("topic", ""),
            title=args.get("title"),
            priority=args.get("priority"),
            tags=args.get("tags"),
            server=args.get("server", _DEFAULT_SERVER),
        ),
        ensure_ascii=False,
    ),
    emoji="🔔",
)
