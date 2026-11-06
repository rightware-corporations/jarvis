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
import re
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

from jarvis.language.intent import NO_REQUEST, IntentKind, IntentVerdict
from jarvis.language.prompts import SAY_MODEL_UNAVAILABLE, clarification_text

LOGGER = logging.getLogger(__name__)

# Fixed failure codes (never provider text). See ``classify_provider_failure``.
FAILURE_NOT_CONFIGURED = "PROVIDER_NOT_CONFIGURED"
FAILURE_TIMEOUT = "PROVIDER_TIMEOUT"
FAILURE_UNREACHABLE = "PROVIDER_UNREACHABLE"
FAILURE_INVALID_RESPONSE = "PROVIDER_INVALID_RESPONSE"
FAILURE_ERROR = "PROVIDER_ERROR"
FAILURE_DESTINATION_DENIED = "PROVIDER_DESTINATION_DENIED"
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
    from jarvis.brain.local_transport import LoopbackDestinationError, OversizedResponseError

    chain = _causes(error)
    if any(isinstance(item, LoopbackDestinationError) for item in chain):
        return FAILURE_DESTINATION_DENIED
    if any(isinstance(item, OversizedResponseError) for item in chain):
        return FAILURE_INVALID_RESPONSE
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
    # Ollama split (JAR-COG-01-R02): model load, prompt processing, generation.
    load_ms: float = 0.0
    prompt_tokens: int = 0
    prompt_ms: float = 0.0
    generation_ms: float = 0.0

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
        for key, value in (
            ("llm_load_ms", self.load_ms - before.load_ms),
            ("llm_prompt_tokens", float(self.prompt_tokens - before.prompt_tokens)),
            ("llm_prompt_ms", self.prompt_ms - before.prompt_ms),
            ("llm_generation_ms", self.generation_ms - before.generation_ms),
        ):
            if value > 0:
                metrics[key] = round(value, 1)
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
                "load_ms": state.load_ms + changes.pop("load_ms", 0.0),
                "prompt_tokens": state.prompt_tokens + changes.pop("prompt_tokens", 0),
                "prompt_ms": state.prompt_ms + changes.pop("prompt_ms", 0.0),
                "generation_ms": state.generation_ms + changes.pop("generation_ms", 0.0),
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
            load_ms=_bounded(metadata.get("load_duration"), _MAX_DURATION_NS) / 1_000_000,
            prompt_tokens=int(_bounded(metadata.get("prompt_eval_count"), _MAX_EVAL_COUNT)),
            prompt_ms=_bounded(metadata.get("prompt_eval_duration"), _MAX_DURATION_NS) / 1_000_000,
            generation_ms=_bounded(metadata.get("eval_duration"), _MAX_DURATION_NS) / 1_000_000,
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


# Tools whose execution has an effect on the computer (JAR-COG-01). Read-only tools
# (time, system status) are not gated; they never authorise an effectful call.
EFFECTFUL_TOOLS: frozenset[str] = frozenset({"open_allowed_application"})
# Read-only tools and the information need that makes each relevant (JAR-COG-01-R02).
READ_ONLY_NEEDS: dict[str, str] = {"get_local_time": "time", "get_system_status": "system"}
KNOWN_TOOLS: frozenset[str] = EFFECTFUL_TOOLS | frozenset(READ_ONLY_NEEDS)
_SAFE_TOOL_NAME = re.compile(r"^[a-z][a-z0-9_]{0,47}$")


# Tool names the Wyzer system prompt mentions to the model (not registered in the slice).
# Only these and the registered tools are logged by name: an invented name could carry
# user content ("guardar_relatorio_projecto_orion"), so it is logged as "<unknown>".
WYZER_ADVERTISED_TOOLS: frozenset[str] = frozenset(
    {"activate_file_tools", "activate_visual_target", "browser_inspect_page", "browser_stop",
     "coding_agent_cancel", "coding_agent_message", "coding_agent_start", "coding_agent_status",
     "control_media", "control_named_window", "copy_selected_text", "get_current_media",
     "get_monitor_layout", "inspect_screen", "list_installed_games", "list_open_windows",
     "open_file", "open_indexed_folder", "paste_clipboard", "read_clipboard", "task_plan_create",
     "task_step_update", "open_application", "is_process_running", "get_foreground_window",
     "browser_start", "move_named_window_to_monitor"}
)


def safe_tool_name(name: object) -> str:
    """A model-generated tool name for audit: known names only, never invented ones."""
    if not isinstance(name, str) or not _SAFE_TOOL_NAME.match(name):
        return "<invalid>"
    return name if name in KNOWN_TOOLS or name in WYZER_ADVERTISED_TOOLS else "<unknown>"
SAY_NO_ACTION_REPLY = "Não abri nenhuma aplicação, porque não mo pediste. Em que posso ajudar?"
# Fallback when only read-only or unknown tools were dropped: no talk of applications.
SAY_RETRY_REPLY = "Desculpa, não consegui responder a isso agora. Podes dizer-me de outra forma?"
_NO_TOOL_NOTE = (
    "VEXEL_POLICY: responde apenas em texto, em português, à última mensagem do utilizador, "
    "usando o contexto da conversa. Não inventes horas, datas nem estados do computador: se "
    "te pedirem e não tiveres essa informação, diz que não a tens."
)
_ACTION_TEXT = re.compile(
    r"(?i)\b(?:abr[aeio]\w*|calculadora|bloco de notas|sim ou n|diz sim|confirm\w*|inici\w*|"
    r"lan[cç]\w*|program\w*|execut\w*|aplica[cç]\w*)"
)


def _looks_like_action_text(text: str) -> bool:
    return bool(_ACTION_TEXT.search(text))
_TEXT_ONLY_NOTE = (
    "VEXEL_POLICY: a chamada de ferramenta proposta não foi autorizada pelo pedido do "
    "utilizador e não foi executada. Não abras aplicações. Responde apenas em texto, em "
    "português, à última mensagem do utilizador, usando o contexto da conversa."
)


class EffectGate:
    """Post-model policy boundary for effectful tool calls (JAR-COG-01, Package A).

    ``authorization`` is the ``IntentVerdict`` of the *user's own* request that the
    current turn serves, set by ``VoiceSession`` (never derived from model text or tool
    results). Without one, every effectful call is blocked (fail closed).
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._authorization: IntentVerdict = NO_REQUEST
        self.blocked = 0
        self.allowed = 0
        self.unknown_blocked = 0
        self.irrelevant_blocked = 0
        self.simulated = True  # launcher mode, for honest clarification wording
        self.rejected_names: list[str] = []  # audit: sanitised names of dropped calls

    @property
    def authorization(self) -> IntentVerdict:
        with self._lock:
            return self._authorization

    def authorize(self, verdict: IntentVerdict | None) -> None:
        with self._lock:
            self._authorization = verdict or NO_REQUEST

    def counts(self) -> tuple[int, int]:
        with self._lock:
            return self.blocked, self.allowed

    def audit(self) -> tuple[int, int, int, list[str]]:
        """``(effectful_blocked, unknown_blocked, irrelevant_blocked, names)`` so far."""
        with self._lock:
            return self.blocked, self.unknown_blocked, self.irrelevant_blocked, list(
                self.rejected_names
            )

    def split(self, calls: list[Any]) -> tuple[list[Any], list[Any]]:
        """``(kept, blocked)``.

        Without an explicit execution request, every effectful call is blocked, whatever
        its form. With one, the requested applications pass; a call for another known
        application is blocked (no switching); a malformed or non-configured call goes
        on to Wyzer, whose validation or the tool itself refuses it (honest DENIED).
        """
        verdict = self.authorization
        kept: list[Any] = []
        blocked: list[Any] = []
        unknown: list[Any] = []
        irrelevant: list[Any] = []
        for call in calls:
            name = call.function.name
            arguments = call.function.arguments
            if name not in KNOWN_TOOLS:
                # Not a registered tool: it can never run. Without an explicit request it
                # is dropped here (no DENIED replacing a conversational answer). With one,
                # Wyzer refuses it (honest refusal) — unless the same reply also carries an
                # authorised opening, which an unknown call must not sabotage.
                if verdict.kind is IntentKind.EXECUTE_REQUEST and not self._has_authorised(
                    calls, verdict
                ):
                    kept.append(call)
                else:
                    unknown.append(call)
                continue
            if name in READ_ONLY_NEEDS:
                # Read-only, but only when its information was asked for ("Será?" never
                # needs the clock; "Que horas são?" does).
                if READ_ONLY_NEEDS[name] in verdict.needs:
                    kept.append(call)
                else:
                    irrelevant.append(call)
                continue
            app = arguments.get("app") if isinstance(arguments, dict) else None
            shaped = isinstance(arguments, dict) and set(arguments) == {"app"}
            if verdict.kind is not IntentKind.EXECUTE_REQUEST:
                blocked.append(call)  # nothing was requested: no confirmation, ever
            elif shaped and isinstance(app, str) and verdict.authorises(app):
                kept.append(call)  # if not configured, the tool itself denies it (DENIED)
            elif shaped and app in ("calculator", "notepad"):
                blocked.append(call)  # a different application than the one requested
            else:
                kept.append(call)  # malformed: Wyzer validation denies it (DENIED)
        with self._lock:
            self.blocked += len(blocked)
            self.unknown_blocked += len(unknown)
            self.irrelevant_blocked += len(irrelevant)
            self.allowed += sum(1 for c in kept if c.function.name in EFFECTFUL_TOOLS)
            for call in (*blocked, *unknown, *irrelevant):
                self.rejected_names.append(safe_tool_name(call.function.name))
            del self.rejected_names[:-64]
        return kept, [*blocked, *unknown, *irrelevant]

    @staticmethod
    def _has_authorised(calls: list[Any], verdict: IntentVerdict) -> bool:
        for call in calls:
            arguments = call.function.arguments
            if call.function.name in EFFECTFUL_TOOLS and isinstance(arguments, dict):
                app = arguments.get("app")
                if set(arguments) == {"app"} and isinstance(app, str) and verdict.authorises(app):
                    return True
        return False

    @staticmethod
    def any_effectful(calls: list[Any]) -> bool:
        return any(call.function.name in EFFECTFUL_TOOLS for call in calls)


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
        self.gate = EffectGate()
        self.last_message_count = 0

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
        self.last_message_count = len(messages)
        response = await self._measured_chat(messages, tools, settings)
        return await self._enforce(response, messages, settings)

    async def _enforce(
        self,
        response: ProviderChatResponse,
        messages: list[ChatMessage],
        settings: ChatRequestSettings | None,
    ) -> ProviderChatResponse:
        """Drop effectful calls the user did not ask for, before Wyzer sees them."""
        message = response.message
        if not message.tool_calls:
            return response
        try:
            kept, blocked = self.gate.split(list(message.tool_calls))
        except Exception as error:  # fail closed: no tool call survives a gate error
            LOGGER.warning("effect gate failed: %s", type(error).__name__)
            kept, blocked = [], list(message.tool_calls)
        if not blocked:
            return response
        LOGGER.info("dropped %d tool call(s) outside the request", len(blocked))
        metadata = {**dict(response.metadata or {}), "vexel_blocked_calls": len(blocked)}
        if kept:
            return ProviderChatResponse(
                message=message.model_copy(update={"tool_calls": kept}), metadata=metadata
            )
        verdict = self.gate.authorization
        effectful = EffectGate.any_effectful(blocked)
        plain = (message.content or "").strip()
        if verdict.kind is IntentKind.AMBIGUOUS and effectful:
            text = clarification_text(verdict.hinted_applications, simulated=self.gate.simulated)
        elif (
            not effectful
            and plain
            and not any(call.function.name in READ_ONLY_NEEDS for call in blocked)
            and not _looks_like_action_text(plain)
        ):
            # Only unknown calls were dropped and the model also answered in plain text:
            # use it, without a second model round (latency). After a dropped read-only
            # call the text may carry an invented time/state, so ask again instead.
            text = plain
        else:
            # Text sent together with a blocked call is discarded ("Vou abrir …", a fake
            # confirmation question): ask again without tools instead.
            text = await self._text_only_answer(messages, settings, effectful=effectful)
        return ProviderChatResponse(
            message=ChatMessage(role="assistant", content=text), metadata=metadata
        )

    async def _text_only_answer(
        self,
        messages: list[ChatMessage],
        settings: ChatRequestSettings | None,
        *,
        effectful: bool = True,
    ) -> str:
        """Ask once more without any tool, so the user still gets an answer."""
        note = ChatMessage(role="system", content=_TEXT_ONLY_NOTE if effectful else _NO_TOOL_NOTE)
        retry = await self._measured_chat([*messages, note], [], settings)
        text = (retry.message.content or "").strip()
        if retry.message.tool_calls or not text:
            return SAY_NO_ACTION_REPLY if effectful else SAY_RETRY_REPLY
        return text

    async def _measured_chat(
        self,
        messages: list[ChatMessage],
        tools: list[NativeToolDefinition],
        settings: ChatRequestSettings | None,
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
        try:
            timings = getattr(getattr(self.inner, "_transport", None), "last_timings", None)
            metadata = {**dict(timings or {}), **dict(response.metadata or {})}
        except Exception as error:  # measurement never breaks a turn
            LOGGER.warning("provider timings ignored: %s", type(error).__name__)
            metadata = dict(response.metadata or {})
        self._safe_record(self.meter.record_success, elapsed(), metadata)
        return response

    @staticmethod
    def _safe_record(method: Callable[..., None], *args: Any) -> None:
        """Measurement must never change the turn: a meter error is logged by type only."""
        try:
            method(*args)
        except Exception as error:
            LOGGER.warning("provider meter failed: %s", type(error).__name__)


def create_direct_chat_provider(llm: Any) -> ChatProvider:
    """Wyzer's own provider for ``llm.provider``, with the loopback transport injected.

    Mirrors ``wyzer.brain.factory.create_chat_provider`` (same arguments and defaults)
    and only adds ``transport=LoopbackJsonTransport(endpoint)``: requests can then only
    go, without any proxy, to the configured loopback origin (JAR-NET-01) — and forces
    ``auto_start=False`` (no subprocess, even for settings that bypassed the slice
    config). Makes no network call. Raises ``LoopbackDestinationError`` for a
    non-loopback endpoint.
    """
    from wyzer.brain.factory import _default_endpoint
    from wyzer.brain.provider import FakeChatProvider
    from wyzer.brain.providers import (
        LlamaCppChatProvider,
        OllamaChatProvider,
        OpenAICompatibleChatProvider,
    )

    from jarvis.brain.local_transport import LoopbackJsonTransport

    if llm.provider == "none":
        return FakeChatProvider(available=False)
    endpoint = str(llm.endpoint).rstrip("/") if llm.endpoint else _default_endpoint(llm.provider)
    common: dict[str, Any] = {
        "temperature": llm.temperature,
        "think": llm.think,
        "max_output_tokens": llm.max_output_tokens,
        "timeout_seconds": llm.request_timeout_seconds,
        "transport": LoopbackJsonTransport(endpoint),
    }
    if llm.provider == "ollama":
        return OllamaChatProvider(
            endpoint,
            llm.model,
            **common,
            context_length=llm.context_length,
            auto_start=False,  # never ``ollama serve`` from VEXEL, whatever the settings say
            startup_timeout_seconds=llm.startup_timeout_seconds,
            keep_alive=llm.keep_alive,
        )
    # The slice config refuses any api_key, so none is ever sent.
    if llm.provider == "llama_cpp":
        return LlamaCppChatProvider(endpoint, llm.model, **common, api_key=None)
    if llm.provider == "openai_compatible":
        return OpenAICompatibleChatProvider(endpoint, llm.model, **common, api_key=None)
    raise ValueError(f"unsupported LLM provider: {llm.provider}")


def create_local_provider(settings: WyzerSettings) -> PortugueseProvider:
    """Build the configured local provider (Ollama by default). Makes no network call.

    The transport is ``LoopbackJsonTransport``: never a proxy, only the configured
    loopback origin (JAR-NET-01)."""
    return PortugueseProvider(create_direct_chat_provider(settings.llm))
