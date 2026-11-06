"""TTS selection behind the ``TextToSpeech`` contract.

* ``windows_system``: System.Speech via Wyzer. Which Portuguese voices exist (Maria,
  Helia, ...) is verified on the QA PC in 01C; nothing here assumes one is installed.
* ``kokoro``: optional alternative, Brazilian Portuguese voices only (pf_dora, pm_alex,
  pm_santa). Its G2P path pulls espeak-ng (GPL-3.0-or-later) — licence review pending.
* ``text``: prints instead of speaking (text mode, CI).

Construction imports no audio or model library; that happens on ``warm_up``/``speak``.
"""

from __future__ import annotations

import sys
import threading
from typing import Any, TextIO

from jarvis.voice.contracts import TextToSpeech

KOKORO_PT_VOICES = frozenset({"pf_dora", "pm_alex", "pm_santa"})


class UnsupportedTtsError(ValueError):
    pass


class TextOnlySpeech:
    """Writes what would be spoken. Used for text mode; never touches audio."""

    def __init__(self, stream: TextIO | None = None, prefix: str = "Jarvis: ") -> None:
        self._stream = stream or sys.stdout
        self._prefix = prefix
        self._lock = threading.Lock()

    def warm_up(self) -> None:
        return None

    def speak(self, text: str) -> None:
        with self._lock:
            self._stream.write(f"{self._prefix}{text}\n")
            self._stream.flush()

    def stop(self) -> None:
        return None


def create_text_to_speech(speech: Any, *, adapter: str | None = None) -> TextToSpeech:
    name = (adapter or speech.tts_adapter).strip().casefold().replace("-", "_")
    if name == "text":
        return TextOnlySpeech()
    if name in {"windows", "windows_system", "system_speech"}:
        from wyzer.speech.windows import WindowsSpeechSynthesizer

        return WindowsSpeechSynthesizer(voice=speech.voice, rate=speech.rate, volume=speech.volume)
    if name in {"kokoro", "kokoro_tts"}:
        voice = (speech.voice or "pf_dora").strip()
        if voice not in KOKORO_PT_VOICES:
            raise UnsupportedTtsError(
                f"Kokoro voice {voice!r} is not Portuguese; use one of {sorted(KOKORO_PT_VOICES)}"
            )
        from wyzer.speech.kokoro import KokoroSpeechSynthesizer

        return KokoroSpeechSynthesizer(
            voice=voice,
            speed=speech.tts_speed,
            volume=speech.volume,
            device=speech.tts_device,
            language_code="p",
        )
    raise UnsupportedTtsError(f"unsupported TTS adapter {name!r}")
