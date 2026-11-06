"""Fakes for the VEXEL slice tests. All simulated: no audio, no network, no processes."""

from __future__ import annotations

import asyncio
import threading
from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from wyzer.models import (
    ChatMessage,
    ChatRequestSettings,
    NativeFunctionCall,
    NativeToolCall,
    NativeToolDefinition,
    ProviderChatResponse,
)

from jarvis.config import SliceConfig, load_slice_config
from jarvis.tools.allowlist import SystemStatusResult
from jarvis.voice.contracts import Transcript

REPO_ROOT = Path(__file__).resolve().parents[1]
SLICE_CONFIG = REPO_ROOT / "configs" / "jarvis_slice.toml"
FIXED_NOW = datetime(2026, 11, 4, 12, 30, tzinfo=UTC)  # 14:30 in Africa/Maputo


def slice_config() -> SliceConfig:
    return load_slice_config(SLICE_CONFIG)


def say(text: str) -> ProviderChatResponse:
    return ProviderChatResponse(message=ChatMessage(role="assistant", content=text))


def call(name: str, arguments: dict[str, Any] | None = None, call_id: str = "c1") -> ProviderChatResponse:
    return ProviderChatResponse(
        message=ChatMessage(
            role="assistant",
            content=None,
            tool_calls=[
                NativeToolCall(
                    id=call_id,
                    function=NativeFunctionCall(name=name, arguments=arguments or {}),
                )
            ],
        )
    )


class ScriptedProvider:
    """Scripted local-LLM stand-in that records every request (messages, tools)."""

    def __init__(self, responses: Iterable[ProviderChatResponse] = (), *, delay: float = 0.0) -> None:
        self._responses = deque(responses)
        self.delay = delay
        self.requests: list[tuple[list[ChatMessage], list[NativeToolDefinition]]] = []
        self.started = asyncio.Event()

    @property
    def available(self) -> bool:
        return True

    def push(self, *responses: ProviderChatResponse) -> None:
        self._responses.extend(responses)

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[NativeToolDefinition],
        settings: ChatRequestSettings | None = None,
    ) -> ProviderChatResponse:
        del settings
        self.requests.append((list(messages), list(tools)))
        self.started.set()
        if self.delay:
            await asyncio.sleep(self.delay)
        if not self._responses:
            raise RuntimeError("scripted provider exhausted")
        return self._responses.popleft()

    def tool_names_seen(self) -> set[str]:
        return {tool.function.name for _, tools in self.requests for tool in tools}


class ExplodingProvider:
    available = True

    async def chat(self, messages: Any, tools: Any, settings: Any = None) -> ProviderChatResponse:
        raise ConnectionError("connection refused to 127.0.0.1:11434")


class ScriptedStt:
    """Returns queued utterances; ``None`` simulates silence or timeout."""

    def __init__(self, utterances: Iterable[str | None] = ()) -> None:
        self._queue: deque[str | None] = deque(utterances)
        self.timeouts: list[float] = []

    def push(self, *utterances: str | None) -> None:
        self._queue.extend(utterances)

    def listen(self, timeout_seconds: float) -> Transcript | None:
        self.timeouts.append(timeout_seconds)
        text = self._queue.popleft() if self._queue else None
        return None if text is None else Transcript(text=text, confidence=0.9)


@dataclass
class RecordingTts:
    spoken: list[str] = field(default_factory=list)
    stops: int = 0
    warmed: bool = False
    block: threading.Event | None = None

    def warm_up(self) -> None:
        self.warmed = True

    def speak(self, text: str) -> None:
        self.spoken.append(text)
        if self.block is not None:
            self.block.wait(5)

    def stop(self) -> None:
        self.stops += 1
        if self.block is not None:
            self.block.set()


class FixedProbe:
    def __init__(self) -> None:
        self.reads = 0

    def read(self) -> SystemStatusResult:
        self.reads += 1
        return SystemStatusResult(
            cpu_percent=12.5,
            memory_percent=41.0,
            memory_used_gb=6.5,
            memory_total_gb=16.0,
            uptime_minutes=95,
            battery_percent=80.0,
            on_ac_power=True,
        )


class ImmediateActivation:
    def __init__(self, fires: int = 1) -> None:
        self.fires = fires
        self.closed = False

    def wait(self, timeout_seconds: float) -> bool:
        if self.closed or self.fires <= 0:
            return False
        self.fires -= 1
        return True

    def close(self) -> None:
        self.closed = True


# ----------------------------------------------------------------- R01 fakes


class FailingTts:
    """TTS that fails at a chosen stage on chosen calls (1-based); other calls succeed."""

    def __init__(self, error: BaseException, *, fail_calls: set[int] | None = None) -> None:
        self.error = error
        self.fail_calls = fail_calls  # None = always fail
        self.calls = 0
        self.spoken: list[str] = []
        self.volume = 100

    def warm_up(self) -> None:
        return None

    def speak(self, text: str) -> None:
        self.calls += 1
        if self.fail_calls is None or self.calls in self.fail_calls:
            raise self.error
        self.spoken.append(text)

    def stop(self) -> None:
        return None


class SilentTts:
    """Mimics Wyzer Kokoro at volume 0: returns normally without producing audio."""

    volume = 0

    def __init__(self) -> None:
        self.calls = 0

    def warm_up(self) -> None:
        return None

    def speak(self, text: str) -> None:
        self.calls += 1

    def stop(self) -> None:
        return None


class FailingLauncher:
    simulated = True

    def __init__(self, error: BaseException | None = None) -> None:
        self.error = error or OSError("launcher unavailable")
        self.requested: list[str] = []

    def launch(self, app: str):
        self.requested.append(app)
        raise self.error


class StatusLauncher:
    """Returns a fixed status (e.g. FAILED, or a forged SUCCEEDED for a test)."""

    simulated = False

    def __init__(self, status: str) -> None:
        self.status = status
        self.requested: list[str] = []

    def launch(self, app: str):
        from jarvis.tools.allowlist import ActionStatus, LaunchResult

        self.requested.append(app)
        status = ActionStatus(self.status)
        return LaunchResult(
            app=app,
            status=status,
            opened=status is ActionStatus.SUCCEEDED,
            simulated=status is ActionStatus.SIMULATED,
            launch_id="fixed",
        )


class StubbornProvider(ScriptedProvider):
    """Ignores cancellation once and still returns its scripted response (late reply)."""

    async def chat(self, messages, tools, settings=None):
        self.requests.append((list(messages), list(tools)))
        self.started.set()
        try:
            await asyncio.sleep(self.delay)
        except asyncio.CancelledError:
            await asyncio.sleep(0)
        return self._responses.popleft()


class ExplodingSink:
    def __init__(self) -> None:
        self.calls = 0

    def publish(self, event) -> None:
        self.calls += 1
        raise RuntimeError("display crashed")
