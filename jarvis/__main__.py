"""Command line entry point for the slice.

    python -m jarvis --check-config [--config configs/jarvis_slice.toml]
    python -m jarvis --text          # type instead of speaking; local provider only

Voice mode (microphone, Whisper, Windows voices) is wired in 01C on the QA PC.
Real Windows application launches stay off unless the config enables them *and* the
process runs on Windows (JAR-SLICE-01D).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from jarvis.config import SliceConfigError, load_slice_config

DEFAULT_CONFIG = Path("configs/jarvis_slice.toml")


def _check(path: Path) -> int:
    try:
        config = load_slice_config(path)
    except (OSError, SliceConfigError) as error:
        print(f"CONFIG_INVALID: {error}", file=sys.stderr)
        return 2
    summary = {
        "config": str(path),
        "llm_provider": config.wyzer.llm.provider,
        "llm_model": config.wyzer.llm.model,
        "llm_endpoint": str(config.wyzer.llm.endpoint),
        "whisper_model": config.wyzer.speech.whisper_model,
        "tts_adapter": config.wyzer.speech.tts_adapter,
        "activation": config.vexel.activation,
        "allowed_applications": list(config.vexel.allowed_applications),
        "allow_real_windows_actions": config.vexel.allow_real_windows_actions,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("CONFIG_OK")
    return 0


async def _text_mode(path: Path) -> int:
    from jarvis.brain.pt_provider import create_local_provider
    from jarvis.core.assistant import build_voice_session
    from jarvis.tools.allowlist import SimulatedLauncher, WindowsApplicationLauncher
    from jarvis.ui.events import RecordingSink
    from jarvis.voice.activation import ManualActivation
    from jarvis.voice.tts import TextOnlySpeech

    config = load_slice_config(path)
    launcher = (
        WindowsApplicationLauncher(allow_real_windows_actions=True)
        if config.vexel.allow_real_windows_actions and sys.platform == "win32"
        else SimulatedLauncher()
    )

    class _NoStt:
        def listen(self, timeout_seconds: float) -> None:
            return None

    session, _ = build_voice_session(
        config,
        create_local_provider(config.wyzer),
        stt=_NoStt(),
        tts=TextOnlySpeech(),
        activation=ManualActivation(),
        sink=RecordingSink(),
        launcher=launcher,
    )
    session.start()
    print("Modo texto. Escreve 'sair' para terminar.")
    while True:
        try:
            line = await asyncio.to_thread(input, "Tu: ")
        except (EOFError, KeyboardInterrupt):
            break
        if line.strip().casefold() in {"sair", "exit", "quit"}:
            break
        await session.handle_text(line)
    session.shutdown()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jarvis")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-config", action="store_true")
    mode.add_argument("--text", action="store_true")
    args = parser.parse_args(argv)
    if args.check_config:
        return _check(args.config)
    return asyncio.run(_text_mode(args.config))


if __name__ == "__main__":
    raise SystemExit(main())
