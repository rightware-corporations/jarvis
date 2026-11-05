"""Portuguese instruction and failure sanitising around any Wyzer ``ChatProvider``.

The wrapper never changes tool definitions or tool calls; it only appends a fixed
Portuguese instruction to the system message the Orchestrator already built, and
replaces provider exceptions with a fixed Portuguese sentence (no internal details).

JAR-ENGINE-01: every call is also measured by a ``ProviderMeter`` (wall time, Ollama
``eval_count``/``total_duration``, truncation, and a fixed failure code such as
``PROVIDER_TIMEOUT`` or ``PROVIDER_HTTP_404``). The codes are derived from exception
types and HTTP status only: no provider text, prompt or reply is ever recorded.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.error import URLError

from wyzer.brain.provider import ChatProvider
from wyzer.config import WyzerSettings
from wyzer.models import (
    ChatMessage,
    ChatRequestSettings,
    NativeToolDefinition,
    ProviderChatResponse,
)

from jarvis.language.prompts import SAY_MODEL_UNAVAILABLE

LOGGER = logging.getLogger(__name__)

# Fixed failure codes (never provider text). See ``classify_provider_failure``.
FAILURE_NOT_CONFIGURED = "PROVIDER_NOT_CONFIGURED"
FAILURE_TIMEOUT = "PROVIDER_TIMEOUT"
FAILURE_UNREACHABLE = "PROVIDER_UNREACHABLE"
FAILURE_INVALID_RESPONSE = "PROVIDER_INVALID_RESPONSE"
FAILURE_ERROR = "PROVIDER_ERROR"
FAILURE_HTTP_PREFIX = "PROVIDER_HTTP_"


def _causes(error: BaseException) -> list[BaseException]:
    chain: list[BaseException] = []
    current: BaseException | None = error
    while current is not None and current not in chain and len(chain) < 8:
        chain.append(current)
        current = current.__cause__ or current.__context__
    return chain


def classify_provider_failure(error: BaseException) -> str:
    """Map a provider exception to a fixed code, from types and HTTP status only."""
    chain = _causes(error)
    for item in chain:
        code = getattr(item, "code", None)
        if code == "PROVIDER_NOT_CONFIGURED":
            return FAILURE_NOT_CONFIGURED
        if code == "INVALID_PROVIDER_RESPONSE":
            return FAILURE_INVALID_RESPONSE
    for item in chain:
        status = getattr(item, "status", None)
        if isinstance(status, int) and 100 <= status <= 599:
            return f"{FAILURE_HTTP_PREFIX}{status}"
    for item in chain:
        if isinstance(item, TimeoutError):
            return FAILURE_TIMEOUT
        if isinstance(item, URLError) and isinstance(item.reason, TimeoutError):
            return FAILURE_TIMEOUT
    for item in chain:
        if isinstance(item, (json.JSONDecodeError, UnicodeDecodeError)):
            return FAILURE_INVALID_RESPONSE
    for item in chain:
        if isinstance(item, (URLError, ConnectionError)):
            return FAILURE_UNREACHABLE
    if "non-object JSON" in str(error):  # Wyzer transport: valid JSON, not an object
        return FAILURE_INVALID_RESPONSE
    for item in chain:
        if isinstance(item, OSError):
            return FAILURE_UNREACHABLE
    return FAILURE_ERROR


_MAX_EVAL_COUNT = 10_000_000
_MAX_DURATION_NS = 86_400 * 1_000_000_000  # one day


def _bounded(value: Any, limit: float, *, integer: bool = False) -> float:
    """``value`` if it is a plain finite number in (0, limit], else 0."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0.0
    if integer and not isinstance(value, int):
        return 0.0
    if not 0 < value <= limit:  # also rejects NaN
        return 0.0
    number = float(value)
    return number if math.isfinite(number) else 0.0


@dataclass(frozen=True, slots=True)
class MeterSnapshot:
    calls: int = 0
    failures: int = 0
    cancelled: int = 0
    truncated: int = 0
    total_ms: float = 0.0
    eval_count: int = 0
    model_duration_ms: float = 0.0
    last_failure: str | None = None

    def since(self, before: MeterSnapshot) -> dict[str, float]:
        """Per-turn metrics (only keys with activity), for ``TurnResult.metrics``."""
        calls = self.calls - before.calls
        if calls <= 0:
            return {}
        metrics = {
            "llm_calls": float(calls),
            "llm_ms": round(self.total_ms - before.total_ms, 1),
        }
        for key, value in (
            ("llm_failures", self.failures - before.failures),
            ("llm_cancelled", self.cancelled - before.cancelled),
            ("llm_truncated", self.truncated - before.truncated),
            ("llm_eval_count", self.eval_count - before.eval_count),
        ):
            if value:
                metrics[key] = float(value)
        model_ms = round(self.model_duration_ms - before.model_duration_ms, 1)
        if model_ms > 0:
            metrics["llm_model_ms"] = model_ms
        return metrics


class ProviderMeter:
    """Thread-safe counters for the calls made through one ``PortugueseProvider``."""

    def __init__(self, timer: Callable[[], float] = time.perf_counter) -> None:
        self.timer = timer
        self._lock = threading.Lock()
        self._state = MeterSnapshot()

    def snapshot(self) -> MeterSnapshot:
        with self._lock:
            return self._state

    def _update(self, elapsed_ms: float, **changes: Any) -> None:
        with self._lock:
            state = self._state
            values = {
                "calls": state.calls + 1,
                "failures": state.failures + changes.pop("failures", 0),
                "cancelled": state.cancelled + changes.pop("cancelled", 0),
                "truncated": state.truncated + changes.pop("truncated", 0),
                "total_ms": state.total_ms + elapsed_ms,
                "eval_count": state.eval_count + changes.pop("eval_count", 0),
                "model_duration_ms": state.model_duration_ms
                + changes.pop("model_duration_ms", 0.0),
                "last_failure": changes.pop("last_failure", state.last_failure),
            }
            self._state = MeterSnapshot(**values)

    def record_success(self, elapsed_ms: float, metadata: dict[str, Any]) -> None:
        # Provider metadata is untrusted: only plain, finite, bounded numbers are kept.
        eval_count = _bounded(metadata.get("eval_count"), _MAX_EVAL_COUNT, integer=True)
        duration = _bounded(metadata.get("total_duration"), _MAX_DURATION_NS)  # nanoseconds
        self._update(
            elapsed_ms,
            eval_count=int(eval_count),
            model_duration_ms=duration / 1_000_000,
            truncated=1 if metadata.get("done_reason") == "length" else 0,
        )

    def record_failure(self, elapsed_ms: float, code: str) -> None:
        self._update(elapsed_ms, failures=1, last_failure=code)

    def record_cancelled(self, elapsed_ms: float) -> None:
        self._update(elapsed_ms, cancelled=1)

PORTUGUESE_INSTRUCTION = (
    "VEXEL_LANGUAGE_POLICY: Responde sempre em português, de forma natural e curta, "
    "porque a resposta vai ser lida em voz alta. Não uses markdown, listas, títulos, "
    "emojis nem código. Usa frases completas e números por extenso quando forem curtos. "
    "Nunca digas que uma acção foi feita sem um resultado de ferramenta que o confirme. "
    "Para saber a hora usa get_local_time; para o estado do computador usa "
    "get_system_status; para abrir aplicações usa apenas open_allowed_application."
)


class PortugueseProvider:
    def __init__(
        self,
        inner: ChatProvider,
        *,
        instruction: str = PORTUGUESE_INSTRUCTION,
        meter: ProviderMeter | None = None,
    ) -> None:
        self.inner = inner
        self.instruction = instruction
        self.meter = meter or ProviderMeter()

    @property
    def available(self) -> bool:
        return self.inner.available

    def _with_instruction(self, messages: list[ChatMessage]) -> list[ChatMessage]:
        if messages and messages[0].role == "system":
            first = messages[0]
            merged = f"{first.content or ''}\n\n{self.instruction}".strip()
            return [first.model_copy(update={"content": merged}), *messages[1:]]
        return [ChatMessage(role="system", content=self.instruction), *messages]

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[NativeToolDefinition],
        settings: ChatRequestSettings | None = None,
    ) -> ProviderChatResponse:
        started = self.meter.timer()

        def elapsed() -> float:
            return round((self.meter.timer() - started) * 1000, 1)

        try:
            response = await self.inner.chat(self._with_instruction(messages), tools, settings)
        except asyncio.CancelledError:
            self._safe_record(self.meter.record_cancelled, elapsed())
            raise
        except Exception as error:  # sanitise: never expose provider internals
            code = classify_provider_failure(error)
            self._safe_record(self.meter.record_failure, elapsed(), code)
            LOGGER.warning("local provider failed: %s (%s)", code, type(error).__name__)
            return ProviderChatResponse(
                message=ChatMessage(role="assistant", content=SAY_MODEL_UNAVAILABLE),
                metadata={
                    "vexel_provider_failure": type(error).__name__,
                    "vexel_failure_code": code,
                },
            )
        self._safe_record(self.meter.record_success, elapsed(), dict(response.metadata or {}))
        return response

    @staticmethod
    def _safe_record(method: Callable[..., None], *args: Any) -> None:
        """Measurement must never change the turn: a meter error is logged by type only."""
        try:
            method(*args)
        except Exception as error:
            LOGGER.warning("provider meter failed: %s", type(error).__name__)


def create_local_provider(settings: WyzerSettings) -> PortugueseProvider:
    """Build the configured local provider (Ollama by default). Makes no network call."""
    from wyzer.brain import create_chat_provider

    return PortugueseProvider(create_chat_provider(settings.llm, settings.personality))
