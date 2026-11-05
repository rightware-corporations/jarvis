"""``python -m apps.desktop`` — VEXEL Jarvis Orb Desktop (MVP, JAR-SLICE-01E).

    python -m apps.desktop --demo                 # simulated states, loops; Esc closes
    python -m apps.desktop --demo --duration 20   # close after 20 s
    python -m apps.desktop --snapshot out/        # write one PNG per state (offscreen ok)

The demo uses no model, microphone, voice or tool. Wiring the orb to a live
``VoiceSession`` (its ``QueueSink``) is the next step, after the 01C hardware gates.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m apps.desktop")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--demo", action="store_true", help="run the orb with simulated states")
    mode.add_argument("--snapshot", type=Path, metavar="DIR", help="write PNG snapshots and exit")
    parser.add_argument("--once", action="store_true", help="demo: play the script once")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--duration", type=float, default=None, help="demo: close after N s")
    parser.add_argument("--scale", type=float, default=2.0, help="snapshot device pixel ratio")
    args = parser.parse_args(argv)

    from apps.desktop.orb.app import ensure_application, run, save_snapshots

    if args.snapshot is not None:
        ensure_application()
        for path in save_snapshots(args.snapshot, scale=args.scale):
            print(path)
        return 0
    return run(demo=True, loop=not args.once, speed=args.speed, duration=args.duration)


if __name__ == "__main__":
    raise SystemExit(main())
