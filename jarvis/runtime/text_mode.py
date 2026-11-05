"""``python -m jarvis --text``: typed input → Portuguese normalisation → ``VoiceSession``
→ Wyzer Orchestrator → local Ollama provider → allowlist / confirmation → text reply.

This is the entry point for the first real-inference check (JAR-ENGINE-01 procedure):
no microphone, no SAPI voice, no Whisper model is needed, only the local Ollama.

* Application launches are **always** the ``SimulatedLauncher`` here, whatever the
  configuration says (real launches are JAR-SLICE-01D and are not wired to text mode).
* At start it asks the provider for a read-only diagnosis (``GET /api/tags``); the
  result is printed as a fixed code. It does not pull, load or start a model.
* Each turn is written to ``text-turns.jsonl`` with the same sanitised record as voice
  mode (outcome, action status, per-stage timings including ``llm_ms``; no text unless
  ``vexel.log_transcript_text = true``), and a one-line timing summary is printed.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jarvis.config import SliceConfig
from jarvis.runtime.voice_mode import Console, StdConsole, TurnLog, default_log_directory
from jarvis.tools.allowlist import SimulatedLauncher
from jarvis.ui.events import JsonlEventLog, UiEventSink
from jarvis.voice.activation import ManualActivation
from jarvis.voice.contracts import TextToSpeech, Transcript

LOGGER = logging.getLogger(__name__)

EXIT_OK = 0
_QUIT = {"sair", "exit", "quit"}

LLM_READY = "LLM_READY"
LLM_MODEL_MISSING = "LLM_MODEL_MISSING"
LLM_UNREACHABLE = "LLM_UNREACHABLE"
LLM_NOT_DIAGNOSABLE = "LLM_NOT_DIAGNOSABLE"


class _NoStt:
    """Text mode never listens."""

    def listen(self, timeout_seconds: float) -> Transcript | None:
        return None


class _ConsoleSpeech:
    """``TextToSpeech`` that writes the reply to the console (never audio)."""

    def __init__(self, console: Console) -> None:
        self._console = console

    def speak(self, text: str) -> None:
        self._console.write(f"Jarvis: {text}")

    def stop(self) -> None:
        return None


class PromptConsole(StdConsole):
    """Standard console with the "Tu: " prompt of the original text mode."""

    def read_line(self) -> str | None:
        try:
            return input("Tu: ")
        except EOFError:
            return None


def _default_provider(config: SliceConfig) -> Any:
    from jarvis.brain.pt_provider import create_local_provider

    return create_local_provider(config.wyzer)


@dataclass
class TextRuntimeDeps:
    provider_factory: Callable[[SliceConfig], Any] = _default_provider
    console: Console = field(default_factory=PromptConsole)
    log_directory: Path | None = None
    extra_sink: UiEventSink | None = None
    tts_factory: Callable[[Console], TextToSpeech] | None = None


@dataclass
class TextRuntimeResult:
    exit_code: int
    llm_status: str
    turns: list[dict[str, Any]] = field(default_factory=list)
    launcher: SimulatedLauncher | None = None


async def diagnose_provider(provider: Any) -> str:
    """Read-only reachability check through the provider's own ``diagnose()``."""
    inner = getattr(provider, "inner", provider)
    diagnose = getattr(inner, "diagnose", None)
    if not callable(diagnose):
        return LLM_NOT_DIAGNOSABLE
    try:
        result = await diagnose()
    except Exception as error:  # never let a diagnosis failure leak details
        LOGGER.warning("provider diagnosis failed: %s", type(error).__name__)
        return LLM_UNREACHABLE
    if result.available:
        return LLM_READY
    details = result.details or {}
    if details.get("configured_model_found") is False:
        return LLM_MODEL_MISSING
    return LLM_UNREACHABLE


def summary_line(record: dict[str, Any]) -> str:
    metrics = record.get("metrics") or {}
    parts = [f"resultado={record.get('outcome')}"]
    if record.get("action_status"):
        parts.append(f"acção={record['action_status']}")
    for key in ("think_ms", "llm_ms", "llm_calls", "llm_eval_count", "tts_ms"):
        if key in metrics:
            value = metrics[key]
            parts.append(f"{key}={value:.0f}" if isinstance(value, float) else f"{key}={value}")
    if record.get("detail"):
        parts.append(f"detalhe={record['detail']}")
    return "[" + " ".join(parts) + "]"


async def run_text_mode(
    config: SliceConfig, deps: TextRuntimeDeps | None = None
) -> TextRuntimeResult:
    from jarvis.core.assistant import build_voice_session
    from jarvis.ui.events import FanOutSink

    deps = deps or TextRuntimeDeps()
    console = deps.console
    provider = deps.provider_factory(config)
    llm_status = await diagnose_provider(provider)
    console.write(
        f"LLM {config.wyzer.llm.provider} {config.wyzer.llm.model}: {llm_status}"
        " (diagnóstico read-only; nenhum modelo é descarregado ou iniciado)"
    )

    log_directory = deps.log_directory or default_log_directory(config)
    include_text = config.vexel.log_transcript_text
    turn_log = TurnLog(log_directory / "text-turns.jsonl", include_text=include_text)
    sinks: list[UiEventSink] = [
        JsonlEventLog(log_directory / "text-ui-events.jsonl", include_text=include_text)
    ]
    if deps.extra_sink is not None:
        sinks.append(deps.extra_sink)

    launcher = SimulatedLauncher()  # text mode: never a real launcher
    tts = deps.tts_factory(console) if deps.tts_factory else _ConsoleSpeech(console)
    session, _parts = build_voice_session(
        config,
        provider,
        stt=_NoStt(),
        tts=tts,
        activation=ManualActivation(),
        sink=FanOutSink(sinks),
        launcher=launcher,
    )
    result = TextRuntimeResult(EXIT_OK, llm_status, launcher=launcher)
    session.start()
    console.write("Modo texto. Escreve 'sair' para terminar. As aplicações são sempre simuladas.")
    try:
        while True:
            line = await asyncio.to_thread(console.read_line)
            if line is None or line.strip().casefold() in _QUIT:
                break
            turn = await session.handle_text(line)
            record = {**turn.as_record(include_text=include_text), "mode": "text"}
            turn_log.write(record)
            result.turns.append(record)
            console.write(summary_line(record))
    finally:
        session.shutdown()
    return result
