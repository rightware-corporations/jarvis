"""Read-only readiness checks before the voice runtime starts.

Every check is injectable so the whole report is testable without Windows, audio,
models or a network. Nothing here installs, downloads, records, speaks or starts a
process: the Ollama check is one HTTP GET to the configured loopback endpoint
(``/api/tags`` through Wyzer's own ``diagnose``), the voice check lists installed
SAPI voices (Windows only), the microphone check lists devices without opening a
stream, the model check looks at the local cache folder (Wyzer's install check).

The report contains no transcript, no audio and no user data: device and voice names
are product names; the endpoint is loopback by configuration.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

from jarvis.config import WAKE_WORD_BLOCKED, SliceConfig
from jarvis.voice.capture import MicrophoneStatus, probe_microphone
from jarvis.voice.sapi import (
    VoiceInfo,
    VoiceSelection,
    list_sapi_voices,
    select_portuguese_voice,
)

VOICE_DEPENDENCIES = ("numpy", "sounddevice", "faster_whisper", "ctranslate2")


class CheckStatus(StrEnum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIP = "SKIP"


@dataclass(frozen=True, slots=True)
class Check:
    name: str
    status: CheckStatus
    code: str
    detail: str = ""
    blocking: bool = True

    @property
    def blocks(self) -> bool:
        return self.blocking and self.status is CheckStatus.FAIL


@dataclass
class PreflightReport:
    checks: list[Check] = field(default_factory=list)
    voice: VoiceInfo | None = None

    @property
    def ready(self) -> bool:
        return not any(check.blocks for check in self.checks)

    @property
    def blocking_codes(self) -> list[str]:
        return [check.code for check in self.checks if check.blocks]

    def get(self, name: str) -> Check:
        return next(check for check in self.checks if check.name == name)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "blocking": self.blocking_codes,
            "selected_voice": asdict(self.voice) if self.voice else None,
            "checks": [{**asdict(check), "status": check.status.value} for check in self.checks],
        }

    def render(self) -> str:
        lines = [f"PREFLIGHT {'READY' if self.ready else 'BLOCKED'}"]
        for check in self.checks:
            info = "" if check.blocking else " (info)"
            detail = f" — {check.detail}" if check.detail else ""
            lines.append(f"  [{check.status.value:4}] {check.name:16} {check.code}{info}{detail}")
        return "\n".join(lines)


def _default_whisper_present(settings: Any) -> bool:
    from wyzer.install_check import _whisper_present

    return _whisper_present(settings)


async def _default_llm_diagnose(config: SliceConfig) -> Any:
    from wyzer.brain import create_chat_provider
    from wyzer.brain.factory import diagnostic_provider

    provider = diagnostic_provider(create_chat_provider(config.wyzer.llm))
    if provider is None:
        return None
    return await provider.diagnose()


@dataclass
class PreflightDeps:
    """Probes; the defaults are the real read-only implementations."""

    platform: str = sys.platform
    python_version: tuple[int, int] = (sys.version_info[0], sys.version_info[1])
    find_spec: Callable[[str], Any] = importlib.util.find_spec
    whisper_present: Callable[[Any], bool] = _default_whisper_present
    microphone: Callable[[], MicrophoneStatus] = probe_microphone
    voices: Callable[[], Sequence[VoiceInfo]] = list_sapi_voices
    llm_diagnose: Callable[[SliceConfig], Awaitable[Any]] = _default_llm_diagnose


async def run_preflight(config: SliceConfig, deps: PreflightDeps | None = None) -> PreflightReport:
    deps = deps or PreflightDeps()
    report = PreflightReport()
    windows = deps.platform == "win32"
    report.checks.append(_check_platform(deps))
    report.checks.append(_check_python(deps))
    report.checks.append(_check_dependencies(deps))
    report.checks.append(_check_stt_model(config, deps))
    report.checks.append(_check_microphone(deps))
    report.checks.append(_check_voice(config, deps, report) if windows else
                         Check("tts_voice", CheckStatus.SKIP, "NOT_WINDOWS", "SAPI is Windows-only"))
    report.checks.append(await _check_llm(config, deps))
    report.checks.append(_check_windows_actions(config))
    report.checks.append(Check("activation", CheckStatus.PASS, "MANUAL", WAKE_WORD_BLOCKED, blocking=False))
    return report


def os_description() -> str:
    """Host OS summary without spawning a process.

    The ``platform`` module is avoided on purpose: on Windows ``platform.system()`` and
    ``platform.release()`` run ``cmd /c ver``, and on Linux ``platform.platform()`` runs
    ``uname -p`` (both found by the test suite's process guard).
    """
    if sys.platform == "win32":
        version = sys.getwindowsversion()  # type: ignore[attr-defined]
        machine = os.environ.get("PROCESSOR_ARCHITECTURE", "")
        return f"Windows {version.major}.{version.minor}.{version.build} {machine}".strip()
    uname = os.uname()
    return f"{uname.sysname} {uname.release} {uname.machine}"


def _check_platform(deps: PreflightDeps) -> Check:
    if deps.platform == "win32":
        return Check("platform", CheckStatus.PASS, "WINDOWS", os_description())
    return Check("platform", CheckStatus.FAIL, "NOT_WINDOWS", f"platform={deps.platform}")


def _check_python(deps: PreflightDeps) -> Check:
    major, minor = deps.python_version
    if (major, minor) == (3, 11):
        return Check("python", CheckStatus.PASS, "PY311", f"{major}.{minor}")
    return Check("python", CheckStatus.FAIL, "PYTHON_NOT_311", f"{major}.{minor}")


def _check_dependencies(deps: PreflightDeps) -> Check:
    missing = [name for name in VOICE_DEPENDENCIES if deps.find_spec(name) is None]
    if missing:
        return Check("dependencies", CheckStatus.FAIL, "DEPENDENCY_MISSING", ", ".join(missing))
    return Check("dependencies", CheckStatus.PASS, "DEPENDENCIES_OK", ", ".join(VOICE_DEPENDENCIES))


def _check_stt_model(config: SliceConfig, deps: PreflightDeps) -> Check:
    speech = config.wyzer.speech
    try:
        present = bool(deps.whisper_present(config.wyzer))
        detail = f"{speech.whisper_model} in {speech.whisper_download_root}"
    except Exception as error:
        present, detail = False, type(error).__name__
    if present:
        return Check("stt_model", CheckStatus.PASS, "STT_MODEL_OK", detail)
    return Check("stt_model", CheckStatus.FAIL, "STT_MODEL_MISSING", detail)


def _check_microphone(deps: PreflightDeps) -> Check:
    try:
        mic = deps.microphone()
    except Exception as error:
        return Check("microphone", CheckStatus.FAIL, "AUDIO_QUERY_FAILED", type(error).__name__)
    detail = f"inputs={mic.input_devices} default={'yes' if mic.default_input else 'no'}"
    if mic.available:
        return Check("microphone", CheckStatus.PASS, mic.code, detail)
    return Check("microphone", CheckStatus.FAIL, mic.code, f"{detail} {mic.detail}".strip())


def _check_voice(config: SliceConfig, deps: PreflightDeps, report: PreflightReport) -> Check:
    try:
        voices = list(deps.voices())
    except Exception as error:
        return Check("tts_voice", CheckStatus.FAIL, "VOICE_INVENTORY_FAILED", type(error).__name__)
    selection: VoiceSelection = select_portuguese_voice(
        voices,
        configured=config.wyzer.speech.voice,
        preferred_cultures=config.vexel.voice_cultures,
    )
    report.voice = selection.voice
    if selection.voice is None:
        cultures = sorted({voice.culture for voice in voices if voice.culture})
        return Check("tts_voice", CheckStatus.FAIL, "PT_VOICE_MISSING",
                     f"installed cultures: {', '.join(cultures) or 'none'}")
    detail = f"{selection.voice.name} ({selection.voice.culture})"
    if selection.detail:
        detail += f"; {selection.detail}"
    if selection.code == "PT_VOICE_FALLBACK":
        return Check("tts_voice", CheckStatus.WARN, selection.code, detail, blocking=False)
    return Check("tts_voice", CheckStatus.PASS, selection.code, detail)


async def _check_llm(config: SliceConfig, deps: PreflightDeps) -> Check:
    llm = config.wyzer.llm
    try:
        result = await deps.llm_diagnose(config)
    except Exception as error:
        return Check("llm", CheckStatus.FAIL, "OLLAMA_UNREACHABLE", type(error).__name__)
    if result is None:
        return Check("llm", CheckStatus.FAIL, "LLM_PROVIDER_UNSUPPORTED", llm.provider)
    details = getattr(result, "details", {}) or {}
    endpoint = getattr(result, "endpoint", "") or ""
    if getattr(result, "available", False):
        return Check("llm", CheckStatus.PASS, "LLM_MODEL_OK", f"{llm.model} at {endpoint}")
    if details.get("configured_model_found") is False:
        return Check("llm", CheckStatus.FAIL, "MODEL_NOT_INSTALLED",
                     f"{llm.model} not listed by {endpoint} ({details.get('model_count', 0)} models)")
    return Check("llm", CheckStatus.FAIL, "OLLAMA_UNREACHABLE", endpoint)


def _check_windows_actions(config: SliceConfig) -> Check:
    if config.vexel.allow_real_windows_actions:
        return Check("windows_actions", CheckStatus.FAIL, "REAL_ACTIONS_NOT_ALLOWED",
                     "01C requires the simulated launcher")
    return Check("windows_actions", CheckStatus.PASS, "SIMULATED_LAUNCHER",
                 "allow_real_windows_actions=false")
