"""A loopback stand-in for the Ollama HTTP API used by JAR-ENGINE-01 contract tests.

It implements only the endpoints Wyzer's ``OllamaChatProvider`` really calls
(``GET /api/tags``, ``POST /api/chat``, ``POST /api/generate``) and answers from a
script. It binds ``127.0.0.1`` on an ephemeral port, never forwards anything, runs
no model and starts no process (threads only, so the process guard is untouched).

Evidence produced with it is ``HTTP_CONTRACT_PASS`` (wire format, parsing, failure
handling). It is never evidence of inference: the replies are scripted.
"""

from __future__ import annotations

import json
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

DEFAULT_MODEL = "qwen3.5:4b"


@dataclass
class Reply:
    """One scripted HTTP answer.

    ``body`` is a dict (sent as JSON) or raw bytes. ``delay`` sleeps before the status
    line (to provoke client timeouts); ``hold`` blocks until the server is released;
    ``drop`` closes the socket without any response (network error).
    """

    body: dict[str, Any] | bytes | list[Any] = field(default_factory=dict)
    status: int = 200
    delay: float = 0.0
    hold: bool = False
    drop: bool = False


def chat_text(text: Any, **extra: Any) -> Reply:
    body = {
        "model": DEFAULT_MODEL,
        "created_at": "2026-11-05T00:00:00Z",
        "message": {"role": "assistant", "content": text},
        "done": True,
        "done_reason": "stop",
        "total_duration": 1_500_000_000,
        "eval_count": 12,
    }
    body.update(extra)
    return Reply(body)


def chat_tool(name: str, arguments: Any = None, **extra: Any) -> Reply:
    body = {
        "model": DEFAULT_MODEL,
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [{"function": {"name": name, "arguments": arguments or {}}}],
        },
        "done": True,
        "done_reason": "stop",
        "total_duration": 900_000_000,
        "eval_count": 8,
    }
    body.update(extra)
    return Reply(body)


@dataclass
class Received:
    method: str
    path: str
    headers: dict[str, str]
    body: Any


class FakeOllama:
    def __init__(self, models: tuple[str, ...] = (DEFAULT_MODEL,)) -> None:
        self.models = list(models)
        self.chat_script: deque[Reply] = deque()
        self.received: list[Received] = []
        self.chat_arrived = threading.Event()
        self.release = threading.Event()
        self._lock = threading.Lock()
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------- lifecycle
    def start(self) -> FakeOllama:
        fake = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, format: str, *args: Any) -> None:  # silence stderr
                return None

            def _read_body(self) -> Any:
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length) if length else b""
                if not raw:
                    return None
                return json.loads(raw.decode("utf-8"))

            def _send(self, reply: Reply) -> None:
                if reply.hold:
                    fake.release.wait(10)
                if reply.delay:
                    deadline = time.monotonic() + reply.delay
                    while time.monotonic() < deadline and not fake.release.is_set():
                        time.sleep(0.01)
                if reply.drop:
                    self.close_connection = True
                    self.connection.close()
                    return
                if isinstance(reply.body, (bytes, bytearray)):
                    data = bytes(reply.body)
                else:
                    data = json.dumps(reply.body, ensure_ascii=False).encode("utf-8")
                try:
                    self.send_response(reply.status)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                except OSError:  # client gave up (timeout/cancel)
                    pass

            def _record(self, body: Any) -> None:
                with fake._lock:
                    fake.received.append(
                        Received(self.command, self.path, dict(self.headers.items()), body)
                    )

            def do_GET(self) -> None:  # noqa: N802 - http.server API
                self._record(None)
                if self.path == "/api/tags":
                    models = [{"name": name, "model": name} for name in fake.models]
                    self._send(Reply({"models": models}))
                else:
                    self._send(Reply({"error": "not found"}, status=404))

            def do_POST(self) -> None:  # noqa: N802 - http.server API
                body = self._read_body()
                self._record(body)
                if self.path == "/api/chat":
                    with fake._lock:
                        reply = fake.chat_script.popleft() if fake.chat_script else None
                    fake.chat_arrived.set()
                    self._send(reply or Reply({"error": "script exhausted"}, status=500))
                elif self.path == "/api/generate":
                    self._send(Reply({"model": body.get("model"), "response": "", "done": True}))
                else:
                    self._send(Reply({"error": "not found"}, status=404))

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.daemon_threads = True
        self._server = server
        self._thread = threading.Thread(
            target=server.serve_forever, kwargs={"poll_interval": 0.05}, name="fake-ollama", daemon=True
        )
        self._thread.start()
        return self

    def stop(self) -> None:
        self.release.set()
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self._thread is not None:
            self._thread.join(5)

    # ----------------------------------------------------------------- helpers
    @property
    def host(self) -> str:
        assert self._server is not None
        return str(self._server.server_address[0])

    @property
    def url(self) -> str:
        assert self._server is not None
        return f"http://127.0.0.1:{self._server.server_address[1]}"

    def script(self, *replies: Reply) -> None:
        with self._lock:
            self.chat_script.extend(replies)

    def chats(self) -> list[Received]:
        with self._lock:
            return [item for item in self.received if item.path == "/api/chat"]
