"""QA kit (JAR-MISSION-02 C): latency summary and the PT-MZ corpus."""

from __future__ import annotations

import asyncio
import json
import math
import sys
from pathlib import Path

import pytest

from jarvis.language.pt import ControlIntent, classify_control, normalize, strip_vocative
from tests_vexel.fakes import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "qa" / "benchmarks"))
import latency_summary as ls  # noqa: E402


@pytest.mark.parametrize(
    ("values", "q", "expected"),
    [([1, 2, 3, 4], 50, 2), ([1, 2, 3, 4], 95, 4), ([5], 95, 5), (list(range(1, 101)), 95, 95)],
)
def test_percentile_nearest_rank(values, q, expected) -> None:
    assert ls.percentile([float(v) for v in values], q) == expected


def test_percentile_of_nothing_is_nan() -> None:
    assert math.isnan(ls.percentile([], 50))


def _write(path: Path, records: list[dict]) -> Path:
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records), encoding="utf-8")
    return path


def test_summary_never_reads_transcript_text(tmp_path: Path, capsys) -> None:
    secret = "o meu número é 84 000 0000"
    records = [
        {"outcome": "answered", "intended": "answered", "heard": secret, "reply": secret,
         "metrics": {"stt_ms": 900.0, "think_ms": 1500.0 + i * 10, "tts_ms": 700.0}}
        for i in range(20)
    ]
    path = _write(tmp_path / "voice-turns.jsonl", records)
    code = ls.main([str(path)])
    out = capsys.readouterr().out
    assert secret not in out and "heard" not in out
    assert code == 0 and "PASS" in out
    assert all(set(turn) <= set(ls.SAFE_FIELDS) for turn in ls.load_turns(path))


def test_slow_replies_fail_acceptance(tmp_path: Path) -> None:
    records = [{"outcome": "answered", "metrics": {"think_ms": 7000.0, "tts_ms": 2500.0}} for _ in range(20)]
    summary = ls.summarise(ls.load_turns(_write(tmp_path / "v.jsonl", records)))
    assert summary["acceptance"]["pass"] is False
    assert summary["response_ms"]["p95"] == 9500.0


def test_summary_from_a_real_simulated_voice_session(tmp_path: Path) -> None:
    """End to end with the real TurnLog format produced by the voice runtime."""
    from jarvis.runtime.voice_mode import TurnLog
    from tests_vexel.conftest import make_rig
    from tests_vexel.fakes import call, say

    rig = make_rig()
    log = TurnLog(tmp_path / "voice-turns.jsonl")
    rig.provider.push(call("open_allowed_application", {"app": "calculator"}), say("Abri."))
    for text in ("abre a calculadora", "sim"):
        log.write(asyncio.run(rig.session.handle_text(text)).as_record())
    summary = ls.summarise(ls.load_turns(log.path))
    assert summary["turns"] == 2
    assert summary["outcomes"] == {"confirmation_requested": 1, "confirmed": 1}
    assert summary["action_status"] == {"SIMULATED": 1}
    assert summary["acceptance"]["enough_samples"] is False


CORPUS = REPO_ROOT / "qa" / "corpus" / "pt_mz_v1.txt"


def _corpus() -> list[str]:
    return [line for line in CORPUS.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")]


def test_corpus_has_twenty_text_only_phrases() -> None:
    phrases = _corpus()
    assert len(phrases) == 20 and len(set(phrases)) == 20
    assert not any(c.isdigit() for c in "".join(phrases))  # no numbers / identifiers


@pytest.mark.parametrize(
    ("phrase", "intent"),
    [("Sim.", ControlIntent.CONFIRM), ("Sim, confirmo.", ControlIntent.CONFIRM),
     ("Pode avançar.", ControlIntent.CONFIRM), ("Não.", ControlIntent.REJECT),
     ("Não, obrigado.", ControlIntent.REJECT), ("Esquece.", ControlIntent.REJECT),
     ("Cancela essa operação.", ControlIntent.CANCEL), ("Pára.", ControlIntent.CANCEL)],
)
def test_corpus_control_phrases_classify_as_expected(phrase: str, intent: ControlIntent) -> None:
    assert phrase in _corpus()
    assert classify_control(strip_vocative(normalize(phrase))) is intent


def test_corpus_requests_are_never_control_words() -> None:
    controls = {"Sim.", "Sim, confirmo.", "Pode avançar.", "Não.", "Não, obrigado.", "Esquece.",
                "Cancela essa operação.", "Pára."}
    for phrase in set(_corpus()) - controls:
        assert classify_control(strip_vocative(normalize(phrase))) is ControlIntent.NONE, phrase


def test_fewer_than_twenty_timed_turns_never_pass(tmp_path: Path) -> None:
    # Review finding P1: one fast turn used to print PASS and exit 0.
    path = _write(tmp_path / "v.jsonl", [{"outcome": "answered", "metrics": {"think_ms": 100.0, "tts_ms": 50.0}}])
    assert ls.main([str(path)]) == 1
    summary = ls.summarise(ls.load_turns(path))
    assert summary["acceptance"]["pass"] is False and summary["acceptance"]["enough_samples"] is False


def test_interrupted_or_incomplete_turns_are_not_timed(tmp_path: Path) -> None:
    records = [{"outcome": "answered", "metrics": {"think_ms": 3000.0, "tts_ms": 1000.0}} for _ in range(20)]
    records += [
        {"outcome": "discarded", "metrics": {"think_ms": 10.0, "tts_ms": 1.0}},
        {"outcome": "answered", "metrics": {"think_ms": 10.0}},
        {"outcome": "tts_failed", "metrics": {"think_ms": 10.0, "tts_ms": 1.0}},
    ]
    summary = ls.summarise(ls.load_turns(_write(tmp_path / "v.jsonl", records)))
    assert summary["response_ms"]["count"] == 20
    assert summary["response_ms"]["p50"] == 4000.0
    assert summary["outcomes"]["discarded"] == 1


def test_json_output_is_strict_json(tmp_path: Path, capsys) -> None:
    path = _write(tmp_path / "v.jsonl", [{"outcome": "not_heard", "metrics": {"stt_ms": 8000.0}}])
    ls.main([str(path), "--json"])
    out = capsys.readouterr().out
    assert "NaN" not in out
    json.loads(out)  # strict parser


# ----------------------------------------------------------- CI diagnose checker

sys.path.insert(0, str(REPO_ROOT / "qa" / "windows"))
import ci_expect_diagnose as ced  # noqa: E402


def _report(*, ready=False, missing="faster_whisper, ctranslate2, numpy", platform_ok=True, extra=()):
    checks = [
        {"name": "platform", "status": "PASS" if platform_ok else "FAIL", "code": "WINDOWS" if platform_ok else "NOT_WINDOWS", "detail": ""},
        {"name": "python", "status": "PASS", "code": "PY311", "detail": ""},
        {"name": "dependencies", "status": "FAIL", "code": "DEPENDENCY_MISSING", "detail": missing},
        {"name": "stt_model", "status": "FAIL", "code": "STT_MODEL_MISSING", "detail": ""},
        {"name": "llm", "status": "FAIL", "code": "OLLAMA_UNREACHABLE", "detail": ""},
        {"name": "windows_actions", "status": "PASS", "code": "SIMULATED_LAUNCHER", "detail": ""},
        {"name": "activation", "status": "PASS", "code": "MANUAL", "detail": ""},
    ]
    blocking = [c["code"] for c in checks if c["status"] == "FAIL"] + list(extra)
    return {"ready": ready, "blocking": blocking, "checks": checks}


@pytest.mark.parametrize(
    ("report", "expected"),
    [
        (_report(), 0),
        (_report(missing="faster_whisper, ctranslate2, numpy, pydantic"), 1),  # real packaging gap
        (_report(platform_ok=False), 1),
        (_report(ready=True), 1),
        (_report(extra=("REAL_ACTIONS_NOT_ALLOWED",)), 1),
    ],
    ids=["expected_absences", "unexpected_package", "not_windows", "ready_without_models", "unexpected_blocker"],
)
def test_ci_diagnose_checker(tmp_path: Path, report: dict, expected: int) -> None:
    path = tmp_path / "diag.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    assert ced.main(str(path)) == expected
