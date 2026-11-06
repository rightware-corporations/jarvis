"""``python -m jarvis --voice``: manual activation → microphone → Whisper PT → Wyzer →
local Ollama → Portuguese SAPI voice.

Fail-closed start: the preflight must be READY, otherwise the runtime does not start
and the exit code is ``EXIT_PREFLIGHT_BLOCKED``. Application launches are always the
``SimulatedLauncher`` in 01C, whatever the configuration says.

Console controls (manual activation, no wake word):

* Enter         → listen once (and once more if a confirmation is requested)
* ``c``         → cancel whatever is running
* ``q``/``sair`` → cancel and exit
* end of input  → finish the current turn, then exit

Logs (no text unless ``vexel.log_transcript_text = true``): ``voice-turns.jsonl`` with
outcome and per-stage timings, ``ui-events.jsonl`` with state transitions. Default
location is Wyzer's data home (``.wyzer/vexel/logs``, git-ignored).
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from jarvis.config import SliceConfig
from jarvis.runtime.preflight import PreflightDeps, PreflightReport, run_preflight
from jarvis.tools.allowlist import SimulatedLauncher
from jarvis.ui.events import FanOutSink, JsonlEventLog, UiEventSink
from jarvis.voice.activation import ManualActivation
from jarvis.voice.capture import AudioCapture, CancellableCapture, WyzerMicrophoneCapture
from jarvis.voice.contracts import SpeechToText, TextToSpeech

LOGGER = logging.getLogger(__name__)

EXIT_OK = 0
EXIT_CONFIG_INVALID = 2
EXIT_PREFLIGHT_BLOCKED = 3
EXIT_RUNTIME_ERROR = 4

_QUIT = {"q", "quit", "sair", "exit"}
_CANCEL = {"c", "cancela", "cancel"}


class Console(Protocol):
    def read_line(self) -> str | None:
        """Blocking read of one command line; ``None`` at end of input."""
        ...

    def write(self, text: str) -> None: ...


class StdConsole:
    def read_line(self) -> str | None:
        try:
            return input()
        except EOFError:
            return None

    def write(self, text: str) -> None:
        print(text, flush=True)


def _default_capture() -> AudioCapture:
    return WyzerMicrophoneCapture()


def _default_stt(config: SliceConfig, capture: AudioCapture) -> SpeechToText:
    from jarvis.voice.stt_pt import create_voice_input

    return create_voice_input(
        config.wyzer.speech, capture, hotwords=config.vexel.stt_hotwords
    )


def _default_tts(config: SliceConfig, voice_name: str) -> TextToSpeech:
    from jarvis.voice.tts import create_text_to_speech

    speech = config.wyzer.speech.model_copy(update={"voice": voice_name})
    return create_text_to_speech(speech, adapter="windows_system")


def _default_provider(config: SliceConfig) -> Any:
    from jarvis.brain.pt_provider import create_local_provider

    return create_local_provider(config.wyzer)


def default_log_directory(config: SliceConfig) -> Path:
    if config.vexel.log_directory:
        return Path(config.vexel.log_directory).expanduser()
    from wyzer.runtime_paths import data_home

    return data_home() / "vexel" / "logs"


@dataclass
class VoiceRuntimeDeps:
    preflight: PreflightDeps = field(default_factory=PreflightDeps)
    capture_factory: Callable[[], AudioCapture] = _default_capture
    stt_factory: Callable[[SliceConfig, AudioCapture], SpeechToText] = _default_stt
    tts_factory: Callable[[SliceConfig, str], TextToSpeech] = _default_tts
    provider_factory: Callable[[SliceConfig], Any] = _default_provider
    console: Console = field(default_factory=StdConsole)
    log_directory: Path | None = None
    extra_sink: UiEventSink | None = None


class TurnLog:
    """Sanitised per-turn evidence: outcome, policy decision and timings."""

    def __init__(self, path: Path, *, include_text: bool = False) -> None:
        self.path = path
        self.include_text = include_text
        self._lock = threading.Lock()
        self.records: list[dict[str, Any]] = []

    def write(self, record: dict[str, Any]) -> None:
        stamped = {"ts": datetime.now(UTC).isoformat(), **record}
        with self._lock:
            self.records.append(stamped)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(stamped, ensure_ascii=False) + "\n")


@dataclass
class VoiceRuntimeResult:
    exit_code: int
    report: PreflightReport
    turns: list[dict[str, Any]] = field(default_factory=list)
    launcher: SimulatedLauncher | None = None


async def run_voice_mode(
    config: SliceConfig, deps: VoiceRuntimeDeps | None = None
) -> VoiceRuntimeResult:
    deps = deps or VoiceRuntimeDeps()
    console = deps.console
    report = await run_preflight(config, deps.preflight)
    console.write(report.render())
    if not report.ready or report.voice is None:
        console.write("Modo de voz não iniciado: corrige os itens FAIL acima.")
        return VoiceRuntimeResult(EXIT_PREFLIGHT_BLOCKED, report)

    from jarvis.core.assistant import build_voice_session

    log_directory = deps.log_directory or default_log_directory(config)
    turn_log = TurnLog(
        log_directory / "voice-turns.jsonl", include_text=config.vexel.log_transcript_text
    )
    sinks: list[UiEventSink] = [
        JsonlEventLog(
            log_directory / "ui-events.jsonl", include_text=config.vexel.log_transcript_text
        )
    ]
    if deps.extra_sink is not None:
        sinks.append(deps.extra_sink)

    launcher = SimulatedLauncher()  # 01C: never a real launcher
    capture = CancellableCapture(deps.capture_factory())
    stt = deps.stt_factory(config, capture)
    tts = deps.tts_factory(config, report.voice.name)
    activation = ManualActivation()
    session, _parts = build_voice_session(
        config,
        deps.provider_factory(config),
        stt=stt,
        tts=tts,
        activation=activation,
        sink=FanOutSink(sinks),
        launcher=launcher,
    )
    session_log = TurnLog(log_directory / "voice-sessions.jsonl", include_text=False)
    session_log.write(
        {"event": "session_start", "session_id": session.session_id, "reason": "process_start"}
    )
    result = VoiceRuntimeResult(EXIT_OK, report, launcher=launcher)
    commands: asyncio.Queue[str | None] = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def read_console() -> None:
        # Daemon thread: a blocked input() can never keep the process alive on exit.
        while True:
            line = console.read_line()
            command = None if line is None else line.strip().casefold()
            try:
                loop.call_soon_threadsafe(commands.put_nowait, command)
            except RuntimeError:  # loop already closed
                return
            if command is None or command in _QUIT:
                return

    console.write("Jarvis em modo de voz. Enter para falar, 'c' para cancelar, 'q' para sair.")
    session.start()
    threading.Thread(target=read_console, name="jarvis-console", daemon=True).start()
    turn: asyncio.Task[Any] | None = None
    try:
        while True:
            command = await commands.get()
            if command is None:  # end of input: let the current turn finish
                if turn is not None:
                    await turn
                break
            if command in _QUIT:
                session.cancel(reason="quit")
                if turn is not None:
                    await turn
                break
            if command in _CANCEL:
                session.cancel(reason="console")
                continue
            if turn is not None and not turn.done():
                console.write("Ainda estou a tratar do pedido anterior.")
                continue
            turn = asyncio.create_task(_one_turn(session, turn_log, result))
    except Exception as error:
        LOGGER.exception("voice runtime failed: %s", type(error).__name__)
        result.exit_code = EXIT_RUNTIME_ERROR
    finally:
        session.shutdown()
        reason = "error" if result.exit_code != EXIT_OK else "user_quit_or_end"
        session_log.write({"event": "session_end", "session_id": session.session_id, "reason": reason})
    return result


async def _one_turn(session: Any, turn_log: TurnLog, result: VoiceRuntimeResult) -> None:
    for turn_result in await session.voice_turn():
        record = turn_result.as_record(include_text=turn_log.include_text)
        turn_log.write(record)
        result.turns.append(record)
