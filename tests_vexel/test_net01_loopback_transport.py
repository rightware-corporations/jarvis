"""JAR-NET-01 — the local LLM transport never goes through a proxy (decisions D01–D03).

Adversarial set-up: every proxy variable points at ``RecordingProxy``, a hostile
listener on loopback that records any byte it receives, and ``NO_PROXY`` is absent.
A control test shows that Wyzer's upstream ``UrllibJsonTransport`` *does* send the
request to that proxy under the same conditions, so the other assertions are not
vacuous. ``LoopbackJsonTransport`` (injected by ``create_local_provider``) must reach
the synthetic Ollama directly and leave the proxy with zero connections.

Windows: on ``win32`` the system proxy comes from ``urllib.request.getproxies_registry``;
the registry reader is stubbed (the machine's proxy settings are never changed), so
the real Windows ``getproxies`` code path runs on the ``windows-latest`` runner. On
other platforms the same test stubs ``getproxies``. Evidence class:
``HTTP_CONTRACT_PASS``; no model runs.
"""

from __future__ import annotations

import asyncio
import socket
import sys
import time
import urllib.request

import pytest

from wyzer.brain.http import HttpTransportError, UrllibJsonTransport

from jarvis.brain.local_transport import (
    LoopbackDestinationError,
    LoopbackJsonTransport,
    build_direct_opener,
)
from jarvis.brain.pt_provider import create_direct_chat_provider, create_local_provider
from jarvis.config import SliceConfigError, parse_slice_config
from jarvis.core.voice_loop import TurnOutcome
from jarvis.language.prompts import SAY_MODEL_UNAVAILABLE
from tests_vexel.fakes import SLICE_CONFIG
from tests_vexel.ollama_loopback import FakeOllama, RecordingProxy, Reply, chat_text, chat_tool
from tests_vexel.test_engine01_ollama_http_contract import ask, config_for, http_rig

PROXY_VARIABLES = ("http_proxy", "HTTP_PROXY", "https_proxy", "HTTPS_PROXY", "all_proxy", "ALL_PROXY")
NO_PROXY_VARIABLES = ("no_proxy", "NO_PROXY")


@pytest.fixture
def ollama():
    server = FakeOllama().start()
    try:
        yield server
    finally:
        server.stop()


@pytest.fixture
def proxy():
    server = RecordingProxy().start()
    try:
        yield server
    finally:
        server.stop()


def _clear_proxy_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove every ``*_proxy`` variable (any case): urllib's getproxies_environment
    matches all of them, and on Windows any one disables the registry lookup."""
    import os

    for name in list(os.environ):
        if name.casefold().endswith("_proxy"):
            monkeypatch.delenv(name, raising=False)


@pytest.fixture
def hostile_env(monkeypatch: pytest.MonkeyPatch, proxy: RecordingProxy) -> RecordingProxy:
    """T1–T4: every proxy variable set to the hostile proxy, NO_PROXY absent."""
    _clear_proxy_env(monkeypatch)
    for name in PROXY_VARIABLES:
        monkeypatch.setenv(name, proxy.url)
    return proxy


def tags(transport, base: str):
    return asyncio.run(transport.request("GET", f"{base}/api/tags", timeout_seconds=3))


# ===================================================== control (non-vacuous)


def test_control_upstream_transport_is_captured_by_the_proxy(
    hostile_env: RecordingProxy, ollama: FakeOllama
) -> None:
    """The risk is real: Wyzer's default transport sends loopback traffic to the proxy."""
    with pytest.raises(HttpTransportError):
        tags(UrllibJsonTransport(), ollama.url)  # the proxy answers 502
    assert hostile_env.connections >= 1
    assert f"{ollama.url}/api/tags".encode() in hostile_env.received()
    assert ollama.received == []


# ============================================================ T1–T4, T6, T8


@pytest.mark.parametrize("variable", ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy"])
def test_t1_t4_each_proxy_variable_alone_is_ignored(
    monkeypatch: pytest.MonkeyPatch, proxy: RecordingProxy, ollama: FakeOllama, variable: str
) -> None:
    _clear_proxy_env(monkeypatch)
    monkeypatch.setenv(variable, proxy.url)
    response = tags(LoopbackJsonTransport(ollama.url), ollama.url)
    assert response.status == 200 and response.data["models"][0]["name"] == "qwen3.5:4b"
    assert proxy.connections == 0
    assert [(r.method, r.path) for r in ollama.received] == [("GET", "/api/tags")]


def test_t5_t6_t8_t12_full_turn_never_reaches_the_hostile_proxy(
    hostile_env: RecordingProxy, ollama: FakeOllama
) -> None:
    ollama.script(chat_tool("get_local_time"), chat_text("São catorze e trinta em Maputo."))
    rig = http_rig(ollama.url)
    assert isinstance(rig.parts.provider.inner._transport, LoopbackJsonTransport)
    result = ask(rig, "Jarvis, que horas são em Maputo?")
    assert result.outcome is TurnOutcome.ANSWERED
    assert rig.tts.spoken == ["São catorze e trinta em Maputo."]
    assert len(ollama.chats()) == 2  # both calls went directly to the local endpoint
    assert hostile_env.connections == 0 and hostile_env.received() == b""  # T12


def test_t5_system_proxy_path_is_ignored(
    monkeypatch: pytest.MonkeyPatch, proxy: RecordingProxy, ollama: FakeOllama
) -> None:
    """Windows registry proxy (stubbed reader) or, elsewhere, the system getproxies()."""
    _clear_proxy_env(monkeypatch)
    system = {"http": proxy.url, "https": proxy.url}
    # urlopen() caches a global opener built from the proxies seen at first use.
    monkeypatch.setattr(urllib.request, "_opener", None)
    if sys.platform == "win32":
        monkeypatch.setattr(urllib.request, "getproxies_registry", lambda: dict(system))
        # The real Windows bypass reads ProxyOverride; "<local>" does not cover 127.0.0.1.
        monkeypatch.setattr(urllib.request, "proxy_bypass_registry", lambda host: False)
    else:
        monkeypatch.setattr(urllib.request, "getproxies", lambda: dict(system))
    with pytest.raises(HttpTransportError):
        tags(UrllibJsonTransport(), ollama.url)  # control: the system proxy captures it
    captured = proxy.connections
    assert captured >= 1

    response = tags(LoopbackJsonTransport(ollama.url), ollama.url)
    assert response.status == 200
    assert proxy.connections == captured  # nothing more reached the proxy


def test_opener_has_no_proxy_handler_and_no_redirects(hostile_env: RecordingProxy) -> None:
    def proxy_handlers(opener):
        return [h for h in opener.handlers if isinstance(h, urllib.request.ProxyHandler)]

    # Control: a default opener built now would route through the hostile proxy.
    assert proxy_handlers(urllib.request.build_opener())[0].proxies["http"] == hostile_env.url
    # ProxyHandler({}) replaces the default and, having no *_open method, adds nothing.
    opener = build_direct_opener()
    assert proxy_handlers(opener) == []
    redirects = [h for h in opener.handlers if isinstance(h, urllib.request.HTTPRedirectHandler)]
    assert len(redirects) == 1 and type(redirects[0]).__name__ == "_NoRedirect"


# ===================================================================== T7


@pytest.mark.parametrize(
    "url",
    [
        "http://10.0.0.5:11434/api/chat",
        "http://example.com/api/chat",
        "http://localhost:{port}/api/chat",  # names resolve through the OS: refused
        "https://127.0.0.1:{port}/api/chat",
        "http://127.0.0.1:1/api/chat",  # loopback, but not the configured port
        "http://127.0.0.2:{port}/api/chat",  # loopback range, but not the configured host
        "http://user:pw@127.0.0.1:{port}/api/chat",
        "file:///etc/passwd",
        "ftp://127.0.0.1:{port}/x",
    ],
)
def test_t7_unauthorised_destination_is_refused_before_any_socket(
    monkeypatch: pytest.MonkeyPatch, ollama: FakeOllama, url: str
) -> None:
    transport = LoopbackJsonTransport(ollama.url)
    port = ollama.url.rsplit(":", 1)[1]

    def no_socket(*args, **kwargs):
        raise AssertionError("a socket was opened for a refused destination")

    monkeypatch.setattr(socket, "create_connection", no_socket)
    with pytest.raises(LoopbackDestinationError):
        asyncio.run(transport.request("POST", url.format(port=port), payload={"x": 1}))
    assert ollama.received == []


@pytest.mark.parametrize(
    "endpoint",
    ["http://192.168.1.20:11434", "http://localhost:11434", "https://127.0.0.1:11434", "http://ollama.local:11434"],
)
def test_t7_non_loopback_endpoint_is_refused_by_config_and_transport(endpoint: str) -> None:
    import tomllib

    data = tomllib.loads(SLICE_CONFIG.read_text(encoding="utf-8"))
    data["llm"]["endpoint"] = endpoint
    with pytest.raises(SliceConfigError):
        parse_slice_config(data)
    with pytest.raises(LoopbackDestinationError):
        LoopbackJsonTransport(endpoint)


def test_ipv6_loopback_origin_is_accepted() -> None:
    transport = LoopbackJsonTransport("http://[::1]:11434")
    assert transport.allows("http://[::1]:11434/api/chat")
    assert not transport.allows("http://127.0.0.1:11434/api/chat")


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_redirect_is_not_followed(hostile_env: RecordingProxy, ollama: FakeOllama, status: int) -> None:
    # urllib would follow 301/302/303 for POST (as a GET to the new host); never here.
    ollama.script(Reply({"error": "moved"}, status=status, headers={"Location": f"{hostile_env.url}/steal"}))
    transport = LoopbackJsonTransport(ollama.url)
    with pytest.raises(HttpTransportError) as raised:
        asyncio.run(transport.request("POST", f"{ollama.url}/api/chat", payload={"secret": "prompt"}))
    assert raised.value.status == status
    assert hostile_env.connections == 0


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_redirect_is_not_followed_for_get(ollama: FakeOllama, status: int) -> None:
    # For GET, stock urllib follows every 3xx: this exercises _NoRedirect for 307/308 too.
    ollama.script(Reply({"error": "moved"}, status=status, headers={"Location": f"{ollama.url}/api/tags"}))
    transport = LoopbackJsonTransport(ollama.url)
    with pytest.raises(HttpTransportError) as raised:
        asyncio.run(transport.request("GET", f"{ollama.url}/api/moved", timeout_seconds=3))
    assert raised.value.status == status
    assert [r.path for r in ollama.received] == ["/api/moved"]  # Location never requested


def test_provider_failure_codes_for_transport_errors() -> None:
    from jarvis.brain.local_transport import OversizedResponseError
    from jarvis.brain.pt_provider import classify_provider_failure

    assert classify_provider_failure(LoopbackDestinationError("x")) == "PROVIDER_DESTINATION_DENIED"
    assert classify_provider_failure(OversizedResponseError("x")) == "PROVIDER_INVALID_RESPONSE"


@pytest.mark.parametrize(
    "url",
    [
        "http://[::1%25eth0]:11434",
        "http://[::ffff:127.0.0.1]:11434",
        "http://127.0.0.1:0",
        "http://user@127.0.0.1:11434",
        "http://@127.0.0.1:11434",
        "http://0.0.0.0:11434",
    ],
)
def test_ambiguous_loopback_forms_are_refused_by_transport_and_config(url: str) -> None:
    import tomllib

    with pytest.raises(LoopbackDestinationError):
        LoopbackJsonTransport(url)
    data = tomllib.loads(SLICE_CONFIG.read_text(encoding="utf-8"))
    data["llm"]["endpoint"] = url
    try:
        config = parse_slice_config(data)
    except SliceConfigError:
        return
    # Accepted only if pydantic normalised it to a clean origin the transport takes.
    endpoint = str(config.wyzer.llm.endpoint)
    assert "@" not in endpoint and LoopbackJsonTransport(endpoint).origin[1] == "127.0.0.1"


def test_default_port_is_not_confused_with_port_zero() -> None:
    transport = LoopbackJsonTransport("http://127.0.0.1")
    assert transport.allows("http://127.0.0.1:80/api/tags")
    assert not transport.allows("http://127.0.0.1:0/api/tags")


# ======================================================== T9, T10, T11


def test_t9_timeout_is_preserved(hostile_env: RecordingProxy, ollama: FakeOllama) -> None:
    ollama.script(Reply(delay=3.0, body={"message": {"role": "assistant", "content": "tarde"}}))
    rig = http_rig(ollama.url, timeout=0.3)
    started = time.monotonic()
    result = ask(rig, "Que horas são?")
    assert time.monotonic() - started < 2.5
    assert result.detail == "PROVIDER_TIMEOUT" and rig.tts.spoken == [SAY_MODEL_UNAVAILABLE]
    assert hostile_env.connections == 0


def test_t10_cancellation_is_preserved(hostile_env: RecordingProxy, ollama: FakeOllama) -> None:
    ollama.script(Reply(hold=True, body=chat_text("tarde").body))
    transport = LoopbackJsonTransport(ollama.url)

    async def scenario() -> None:
        task = asyncio.create_task(
            transport.request("POST", f"{ollama.url}/api/chat", payload={"m": 1}, timeout_seconds=5)
        )
        deadline = time.monotonic() + 5
        while not ollama.chat_arrived.is_set():
            assert time.monotonic() < deadline, "request never reached the loopback server"
            await asyncio.sleep(0.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        ollama.release.set()  # let the abandoned worker thread finish
        await asyncio.sleep(0.1)

    asyncio.run(scenario())
    assert hostile_env.connections == 0


@pytest.mark.parametrize(
    ("reply", "message"),
    [
        (Reply(b"not json"), "invalid JSON"),
        (Reply(b"[1, 2]"), "non-object JSON"),
        (Reply(b"\xff\xfe\x00"), "invalid JSON"),
        (Reply(b'{"a": "' + b"x" * (4 * 1024 * 1024 + 10) + b'"}'), "oversized"),
    ],
    ids=["not_json", "array", "not_utf8", "oversized"],
)
def test_t11_malformed_response_keeps_the_sanitised_errors(
    ollama: FakeOllama, reply: Reply, message: str
) -> None:
    ollama.script(reply)
    transport = LoopbackJsonTransport(ollama.url)
    with pytest.raises(HttpTransportError) as raised:
        asyncio.run(transport.request("POST", f"{ollama.url}/api/chat", payload={}))
    assert message in str(raised.value) and raised.value.status is None


def test_http_error_message_is_the_upstream_sanitised_one(ollama: FakeOllama) -> None:
    ollama.script(Reply({"error": "model not found"}, status=404))
    transport = LoopbackJsonTransport(ollama.url)
    with pytest.raises(HttpTransportError) as raised:
        asyncio.run(transport.request("POST", f"{ollama.url}/api/chat", payload={}))
    assert raised.value.status == 404
    assert str(raised.value) == "Local model endpoint returned HTTP 404: model not found"


# ========================================================= wiring checks


def test_factory_mirror_matches_upstream_except_transport_and_auto_start(ollama: FakeOllama) -> None:
    from wyzer.brain import create_chat_provider

    config = config_for(ollama.url)
    for provider in ("ollama", "llama_cpp", "openai_compatible"):
        llm = config.wyzer.llm.model_copy(update={"provider": provider})
        upstream, mirror = create_chat_provider(llm), create_direct_chat_provider(llm)
        assert type(upstream) is type(mirror)
        ignored = {"_transport", "_startup_lock", "auto_start"}
        assert {k: v for k, v in vars(upstream).items() if k not in ignored} == {
            k: v for k, v in vars(mirror).items() if k not in ignored
        }, provider


def test_auto_start_is_forced_off_even_for_raw_wyzer_settings() -> None:
    from wyzer.config import LLMSettings

    raw = LLMSettings(provider="ollama", model="qwen3.5:4b", endpoint="http://127.0.0.1:11434")
    assert raw.auto_start is True  # upstream default: would start "ollama serve"
    assert create_direct_chat_provider(raw).auto_start is False


def test_every_jarvis_provider_entry_point_uses_the_loopback_transport(ollama: FakeOllama) -> None:
    config = config_for(ollama.url)
    assert isinstance(create_local_provider(config.wyzer).inner._transport, LoopbackJsonTransport)
    for provider in ("ollama", "llama_cpp", "openai_compatible"):
        llm = config.wyzer.llm.model_copy(update={"provider": provider})
        assert isinstance(create_direct_chat_provider(llm)._transport, LoopbackJsonTransport)


def test_preflight_diagnosis_goes_direct(hostile_env: RecordingProxy, ollama: FakeOllama) -> None:
    from jarvis.runtime.preflight import _default_llm_diagnose

    result = asyncio.run(_default_llm_diagnose(config_for(ollama.url)))
    assert result.available and result.details["configured_model_found"] is True
    assert hostile_env.connections == 0
