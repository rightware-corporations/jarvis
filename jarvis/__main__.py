"""Command line entry point for the slice.

    python -m jarvis --check-config [--config configs/jarvis_slice.toml]
    python -m jarvis --text          # type instead of speaking; local provider only
    python -m jarvis --diagnose [--json]  # read-only readiness report (exit 3 if blocked)
    python -m jarvis --voice         # manual activation → mic → Whisper PT → Ollama → SAPI PT

Voice mode refuses to start unless the preflight is READY. Application launches stay
simulated in voice mode (JAR-SLICE-01C). Real launches remain off in text mode unless
the config enables them *and* the process runs on Windows (JAR-SLICE-01D).
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


async def _diagnose(path: Path, as_json: bool) -> int:
    from jarvis.runtime.preflight import run_preflight
    from jarvis.runtime.voice_mode import EXIT_PREFLIGHT_BLOCKED

    config = load_slice_config(path)
    report = await run_preflight(config)
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2) if as_json else report.render())
    return 0 if report.ready else EXIT_PREFLIGHT_BLOCKED


async def _voice_mode(path: Path) -> int:
    from jarvis.runtime.voice_mode import run_voice_mode

    result = await run_voice_mode(load_slice_config(path))
    return result.exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jarvis")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-config", action="store_true")
    mode.add_argument("--text", action="store_true")
    mode.add_argument("--diagnose", action="store_true")
    mode.add_argument("--voice", action="store_true")
    parser.add_argument("--json", action="store_true", help="with --diagnose: JSON output")
    args = parser.parse_args(argv)
    if args.check_config:
        return _check(args.config)
    try:
        if args.diagnose:
            return asyncio.run(_diagnose(args.config, args.json))
        if args.voice:
            return asyncio.run(_voice_mode(args.config))
    except (OSError, SliceConfigError) as error:
        print(f"CONFIG_INVALID: {error}", file=sys.stderr)
        return 2
    return asyncio.run(_text_mode(args.config))


if __name__ == "__main__":
    raise SystemExit(main())
