"""Latency summary for G9 (JAR-SLICE-01C) from ``voice-turns.jsonl``.

Reads **metrics only** (``outcome``, ``intended``, ``action_status``, ``metrics``); the
``heard``/``reply`` text fields are never read or printed, even if text logging was
enabled. Prints p50/p95/max per stage and the acceptance check (p50 ≤ 4 s, p95 ≤ 8 s
for think + tts, i.e. end of speech → end of reply). ``llm_ms`` (JAR-ENGINE-01) is the
local model's share of ``think_ms`` and is reported, not added. It also reads
``text-turns.jsonl`` from ``python -m jarvis --text`` (records with ``"mode": "text"``):
stage timings are reported, but the G9 acceptance is ``NOT_APPLICABLE`` and never PASS,
because text mode has no STT and its ``tts_ms`` is a console print, not speech.

    python qa/benchmarks/latency_summary.py .wyzer/vexel/logs/voice-turns.jsonl [--json]
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

STAGES = ("stt_ms", "think_ms", "llm_ms", "tts_ms")  # llm_ms is part of think_ms
SAFE_FIELDS = ("outcome", "intended", "action_status", "metrics", "mode")
P50_LIMIT_MS = 4000.0
P95_LIMIT_MS = 8000.0
MIN_SAMPLES = 20
TIMED_OUTCOMES = {"answered", "confirmed", "confirmation_requested"}


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
    # Response time = think + tts, only for turns that completed both stages and were
    # actually spoken; interrupted/failed turns are reported in "outcomes", not timed.
    responses = [
        float(t["metrics"]["think_ms"]) + float(t["metrics"]["tts_ms"])
        for t in turns
        if t.get("outcome") in TIMED_OUTCOMES
        and {"think_ms", "tts_ms"} <= set(t.get("metrics") or {})
    ]
    p50, p95 = percentile(responses, 50), percentile(responses, 95)
    enough = len(responses) >= MIN_SAMPLES
    text_mode = any(t.get("mode") == "text" for t in turns)
    return {
        "turns": len(turns),
        "outcomes": dict(Counter(t.get("outcome") for t in turns)),
        "action_status": dict(Counter(t.get("action_status") for t in turns if t.get("action_status"))),
        "stages": stages,
        "response_ms": {"count": len(responses), "p50": p50, "p95": p95},
        "acceptance": {
            "p50_limit_ms": P50_LIMIT_MS,
            "p95_limit_ms": P95_LIMIT_MS,
            "min_samples": MIN_SAMPLES,
            "enough_samples": enough,
            # Text-mode logs are not voice latency evidence: never a G9 PASS.
            "applicable": not text_mode,
            # Fewer than MIN_SAMPLES timed turns is never a PASS (G9 needs >= 20).
            "pass": (not text_mode) and enough and p50 <= P50_LIMIT_MS and p95 <= P95_LIMIT_MS,
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
    verdict = (
        "PASS" if acceptance["pass"] else "FAIL" if acceptance.get("applicable", True)
        else "NOT_APPLICABLE (text mode)"
    )
    lines.append(
        f"Response (think+tts) n={response['count']}  p50={ms(response['p50'])}  p95={ms(response['p95'])}"
        f"  -> {verdict} (p50 <= {acceptance['p50_limit_ms']:.0f} ms, p95 <= {acceptance['p95_limit_ms']:.0f} ms)"
    )
    if not acceptance["enough_samples"]:
        lines.append(f"  FAIL reason: only {response['count']} timed turn(s); G9 needs at least {acceptance['min_samples']}")
    return "\n".join(lines)


def _json_safe(value: Any) -> Any:
    """Strict JSON: NaN (no samples) becomes null."""
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    summary = summarise(load_turns(args.path))
    print(json.dumps(_json_safe(summary), indent=2) if args.json else render(summary))
    return 0 if summary["acceptance"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
