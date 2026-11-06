"""Direct loopback transport for the local LLM (JAR-NET-01, decisions D02/D03).

Wyzer's ``UrllibJsonTransport`` calls ``urllib.request.urlopen``, whose default opener
honours ``HTTP(S)_PROXY``/``ALL_PROXY`` and, on Windows, the proxy configured in the
registry. Python's registry bypass for ``<local>`` only matches dot-less host names,
so a request to ``127.0.0.1`` can be sent to a system proxy: the prompts, the tool
results and the replies would leave the computer.

``LoopbackJsonTransport`` implements the same ``JsonTransport`` contract and is
injected into Wyzer's providers (``transport=``), so the Ollama protocol, its parsing
and its retries stay upstream and unmodified. It differs from the upstream transport
only where the privacy boundary needs it:

* its own opener with ``ProxyHandler({})``: no environment, registry or system proxy
  is ever consulted (no process-global variable is changed);
* only ``http`` to the one configured origin (scheme, loopback IP literal, port);
  any other URL is refused *before* a socket is opened;
* redirects are never followed (a 3xx is an HTTP error);
* the response body is bounded.

Timeouts, the JSON checks and the sanitised error messages are those of Wyzer: the
same ``HttpTransportError`` and ``_safe_http_error`` are reused.
"""

from __future__ import annotations

import asyncio
import ipaddress
import json
import math
from typing import Any, cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import (
    HTTPRedirectHandler,
    OpenerDirector,
    ProxyHandler,
    Request,
    build_opener,
)

from wyzer.brain.http import HttpTransportError, JsonResponse, _safe_http_error

MAX_RESPONSE_BYTES = 4 * 1024 * 1024  # an Ollama /api/chat reply is a few KB
# Ollama timing fields (nanoseconds, counts). Copied as numbers only, for latency analysis.
_TIMING_FIELDS = (
    "load_duration", "prompt_eval_count", "prompt_eval_duration", "eval_count", "eval_duration",
)


def _safe_timings(data: dict[str, Any]) -> dict[str, float]:
    """Plain, finite, non-negative numbers below one day in ns / 10M tokens; never raises."""
    timings: dict[str, float] = {}
    for key in _TIMING_FIELDS:
        value = data.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        if not 0 <= value <= 86_400 * 1_000_000_000:  # also rejects NaN and huge ints
            continue
        try:
            number = float(value)
        except (OverflowError, ValueError):
            continue
        if math.isfinite(number):
            timings[key] = number
    return timings


class LoopbackDestinationError(HttpTransportError):
    """The URL is not the configured loopback origin; nothing was sent."""


class OversizedResponseError(HttpTransportError):
    """The local endpoint sent more than ``max_response_bytes``."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        return None  # urllib then raises HTTPError with the 3xx status


def _loopback_ip(host: str | None) -> bool:
    """127.0.0.0/8 or ::1 as an IP literal; no names, zone ids or IPv4-mapped forms."""
    if not host or "%" in host:
        return False
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False  # names (even "localhost") are resolved by the OS: not trusted
    if isinstance(address, ipaddress.IPv6Address) and (
        address.ipv4_mapped is not None or address.scope_id
    ):
        return False
    return address.is_loopback


def loopback_origin(url: str) -> tuple[str, str, int] | None:
    """``(scheme, host, port)`` when ``url`` is plain http on a loopback IP, else None."""
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        return None
    host = parts.hostname
    if parts.scheme != "http" or not _loopback_ip(host):
        return None
    if parts.username is not None or parts.password is not None or "@" in parts.netloc:
        return None
    if port == 0:
        return None
    assert host is not None
    return parts.scheme, ipaddress.ip_address(host).compressed, 80 if port is None else port


_origin = loopback_origin


def build_direct_opener() -> OpenerDirector:
    """An opener that never uses a proxy and never follows redirects."""
    return build_opener(ProxyHandler({}), _NoRedirect())


class LoopbackJsonTransport:
    """``JsonTransport`` bound to one loopback origin, without any proxy."""

    def __init__(self, endpoint: str, *, max_response_bytes: int = MAX_RESPONSE_BYTES) -> None:
        origin = _origin(endpoint)
        if origin is None:
            raise LoopbackDestinationError(
                "Local model endpoint must be http on a loopback IP address."
            )
        self.origin = origin
        self.max_response_bytes = max_response_bytes
        self._opener = build_direct_opener()
        # Numeric Ollama timing fields of the last response (JAR-COG-01-R02). Never text.
        self.last_timings: dict[str, float] = {}

    def allows(self, url: str) -> bool:
        return _origin(url) == self.origin

    async def request(
        self,
        method: str,
        url: str,
        *,
        payload: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout_seconds: float = 60,
    ) -> JsonResponse:
        if not self.allows(url):
            raise LoopbackDestinationError("Destination is not the configured local model endpoint.")
        return await asyncio.to_thread(
            self._request_sync, method, url, payload, headers or {}, timeout_seconds
        )

    def _request_sync(
        self,
        method: str,
        url: str,
        payload: dict[str, Any] | None,
        headers: dict[str, str],
        timeout_seconds: float,
    ) -> JsonResponse:
        # Same request shape and error mapping as wyzer.brain.http.UrllibJsonTransport.
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request_headers = {"Accept": "application/json", **headers}
        if body is not None:
            request_headers["Content-Type"] = "application/json"
        request = Request(url, data=body, headers=request_headers, method=method)
        try:
            with self._opener.open(request, timeout=timeout_seconds) as response:
                raw_bytes = response.read(self.max_response_bytes + 1)
                status = response.status
        except HTTPError as error:
            try:
                raw_error = error.read(64 * 1024).decode("utf-8", errors="replace")
            except (OSError, TimeoutError):  # the error body itself failed to arrive
                raw_error = ""
            raise HttpTransportError(
                _safe_http_error(raw_error, error.code), status=error.code
            ) from error
        except (URLError, TimeoutError, OSError) as error:
            raise HttpTransportError(
                f"Could not reach the local model endpoint: {error}"
            ) from error
        if len(raw_bytes) > self.max_response_bytes:
            raise OversizedResponseError("Local model endpoint returned an oversized response.")
        try:
            decoded = json.loads(raw_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise HttpTransportError("Local model endpoint returned invalid JSON.") from error
        if not isinstance(decoded, dict):
            raise HttpTransportError("Local model endpoint returned a non-object JSON response.")
        self.last_timings = _safe_timings(decoded)
        return JsonResponse(status=status, data=cast(dict[str, Any], decoded))
