"""Latency summary for G9 (JAR-SLICE-01C) from ``voice-turns.jsonl``.

Reads **metrics only** (``outcome``, ``intended``, ``action_status``, ``metrics``); the
``heard``/``reply`` text fields are never read or printed, even if text logging was
enabled. Prints p50/p95/max per stage and the acceptance check (p50 ≤ 4 s, p95 ≤ 8 s
for think + tts, i.e. end of speech → end of reply).

    python qa/benchmarks/latency_summary.py .wyzer/vexel/logs/voice-turns.jsonl [--json]
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

STAGES = ("stt_ms", "think_ms", "tts_ms")
SAFE_FIELDS = ("outcome", "intended", "action_status", "metrics")
P50_LIMIT_MS = 4000.0
P95_LIMIT_MS = 8000.0


def percentile(values: list[float], q: float) -> float:
    """Nearest-rank percentile (no interpolation), q in [0, 100]."""
    if not values:
        return math.nan
    ordered = sorted(values)
    rank = max(1, math.ceil(q / 100.0 * len(ordered)))
    return ordered[rank - 1]


def load_turns(path: Path) -> list[dict[str, Any]]:
    turns = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        turns.append({key: record.get(key) for key in SAFE_FIELDS})
    return turns


def summarise(turns: list[dict[str, Any]]) -> dict[str, Any]:
    stages: dict[str, dict[str, float]] = {}
    for stage in STAGES:
        values = [float(t["metrics"][stage]) for t in turns if stage in (t.get("metrics") or {})]
        stages[stage] = {
            "count": len(values),
            "p50": percentile(values, 50),
            "p95": percentile(values, 95),
            "max": max(values) if values else math.nan,
        }
    responses = [
        float(t["metrics"].get("think_ms", 0.0)) + float(t["metrics"].get("tts_ms", 0.0))
        for t in turns
        if (t.get("metrics") or {}).get("think_ms") is not None
    ]
    p50, p95 = percentile(responses, 50), percentile(responses, 95)
    return {
        "turns": len(turns),
        "outcomes": dict(Counter(t.get("outcome") for t in turns)),
        "action_status": dict(Counter(t.get("action_status") for t in turns if t.get("action_status"))),
        "stages": stages,
        "response_ms": {"count": len(responses), "p50": p50, "p95": p95},
        "acceptance": {
            "p50_limit_ms": P50_LIMIT_MS,
            "p95_limit_ms": P95_LIMIT_MS,
            "enough_samples": len(responses) >= 20,
            "pass": bool(responses) and p50 <= P50_LIMIT_MS and p95 <= P95_LIMIT_MS,
        },
    }


def render(summary: dict[str, Any]) -> str:
    def ms(value: float) -> str:
        return "n/a" if math.isnan(value) else f"{value:,.0f} ms"

    lines = [f"Turns: {summary['turns']}  outcomes: {summary['outcomes']}"]
    if summary["action_status"]:
        lines.append(f"Action status: {summary['action_status']}")
    for stage, data in summary["stages"].items():
        lines.append(f"  {stage:9} n={data['count']:3}  p50={ms(data['p50']):>10}  p95={ms(data['p95']):>10}  max={ms(data['max']):>10}")
    response = summary["response_ms"]
    acceptance = summary["acceptance"]
    verdict = "PASS" if acceptance["pass"] else "FAIL"
    lines.append(
        f"Response (think+tts) n={response['count']}  p50={ms(response['p50'])}  p95={ms(response['p95'])}"
        f"  -> {verdict} (p50 <= {acceptance['p50_limit_ms']:.0f} ms, p95 <= {acceptance['p95_limit_ms']:.0f} ms)"
    )
    if not acceptance["enough_samples"]:
        lines.append("  note: fewer than 20 turns; G9 needs at least 20")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    summary = summarise(load_turns(args.path))
    print(json.dumps(summary, indent=2, default=str) if args.json else render(summary))
    return 0 if summary["acceptance"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
