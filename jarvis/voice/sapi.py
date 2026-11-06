"""Portuguese SAPI voice inventory and selection (read-only).

The inventory query runs through Wyzer's ``PowerShellSpeechRunner`` (no new process
code in VEXEL). It only lists installed System.Speech voices: name, culture, gender
and whether the voice is enabled. It never speaks.

Selection order: the configured voice if it is Portuguese and enabled; otherwise the
first enabled voice whose culture is in ``preferred_cultures`` (default pt-PT, then
pt-BR). No Portuguese voice → ``None`` (``PT_VOICE_MISSING``). A non-Portuguese voice
is never chosen for Portuguese replies.

Note: System.Speech sees SAPI 5 "Desktop" voices. OneCore-only voices installed via
Windows Settings may not be listed; the QA preflight reports both views.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol

VOICE_INVENTORY_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
  $list = @($speaker.GetInstalledVoices() | ForEach-Object {
    [ordered]@{ name = $_.VoiceInfo.Name; culture = $_.VoiceInfo.Culture.Name;
                gender = [string]$_.VoiceInfo.Gender; enabled = [bool]$_.Enabled } })
  ConvertTo-Json -Compress -InputObject $list
} finally { $speaker.Dispose() }
"""

DEFAULT_CULTURES = ("pt-PT", "pt-BR")


class ScriptRunner(Protocol):
    def run(self, script: str, *, payload: dict[str, Any] | None = None, timeout: float = 15) -> str: ...


@dataclass(frozen=True, slots=True)
class VoiceInfo:
    name: str
    culture: str
    gender: str = ""
    enabled: bool = True

    @property
    def portuguese(self) -> bool:
        return self.culture.casefold().startswith("pt")


class VoiceInventoryError(RuntimeError):
    pass


def parse_inventory(raw: str) -> list[VoiceInfo]:
    try:
        data = json.loads(raw.strip() or "[]")
    except json.JSONDecodeError as error:
        raise VoiceInventoryError("voice inventory is not valid JSON") from error
    items = data if isinstance(data, list) else [data]
    voices = []
    for item in items:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        voices.append(
            VoiceInfo(
                name=str(item["name"]),
                culture=str(item.get("culture") or ""),
                gender=str(item.get("gender") or ""),
                enabled=bool(item.get("enabled", True)),
            )
        )
    return voices


def list_sapi_voices(runner: ScriptRunner | None = None) -> list[VoiceInfo]:
    if runner is None:
        from wyzer.speech.windows import PowerShellSpeechRunner

        runner = PowerShellSpeechRunner()
    try:
        raw = runner.run(VOICE_INVENTORY_SCRIPT, timeout=15)
    except Exception as error:
        raise VoiceInventoryError(type(error).__name__) from error
    return parse_inventory(raw)


@dataclass(frozen=True, slots=True)
class VoiceSelection:
    voice: VoiceInfo | None
    code: str
    detail: str = ""


def select_portuguese_voice(
    voices: Sequence[VoiceInfo],
    *,
    configured: str | None = None,
    preferred_cultures: Sequence[str] = DEFAULT_CULTURES,
) -> VoiceSelection:
    usable = [v for v in voices if v.enabled and v.portuguese]
    if configured:
        match = next((v for v in voices if v.name == configured), None)
        if match is not None and match in usable:
            return VoiceSelection(match, "PT_VOICE_CONFIGURED")
        reason = (
            "configured voice not installed"
            if match is None
            else ("configured voice is disabled" if not match.enabled else "configured voice is not Portuguese")
        )
    else:
        reason = ""
    for culture in preferred_cultures:
        for voice in usable:
            if voice.culture.casefold() == culture.casefold():
                code = "PT_VOICE_FALLBACK" if configured else "PT_VOICE_SELECTED"
                return VoiceSelection(voice, code, reason)
    if usable:
        code = "PT_VOICE_FALLBACK" if configured else "PT_VOICE_SELECTED"
        return VoiceSelection(usable[0], code, reason or "culture outside preference list")
    return VoiceSelection(None, "PT_VOICE_MISSING", reason or "no enabled Portuguese SAPI voice")
