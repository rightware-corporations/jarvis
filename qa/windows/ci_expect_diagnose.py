"""Check ``python -m jarvis --diagnose --json`` on a CI runner that has no models,
microphone, Portuguese voice or Ollama (JAR-MISSION-02, Windows CI).

The preflight must report BLOCKED for exactly those *expected* absences, and the
policy checks must pass. Anything else (an unexpected blocker, a failing policy
check, a crash) fails the step. Absences are printed, not hidden.

Usage:  python -m jarvis --diagnose --json > diag.json
        python qa/windows/ci_expect_diagnose.py diag.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# A clean CI runner cannot satisfy these; each is a documented, expected absence.
EXPECTED_ABSENCES = {
    "DEPENDENCY_MISSING": "faster-whisper/ctranslate2/numpy not installed in CI (no models)",
    "STT_MODEL_MISSING": "Whisper model is never downloaded in CI",
    "AUDIO_DEPENDENCY_MISSING": "sounddevice/PortAudio not installed",
    "AUDIO_QUERY_FAILED": "audio subsystem not available on the runner",
    "MIC_MISSING": "runner has no microphone",
    "MIC_NO_DEFAULT": "runner has no default input device",
    "PT_VOICE_MISSING": "runner image has no Portuguese SAPI voice",
    "VOICE_INVENTORY_FAILED": "System.Speech not usable on the runner",
    "OLLAMA_UNREACHABLE": "Ollama is never installed in CI",
    "MODEL_NOT_INSTALLED": "no LLM model in CI",
}
MUST_BE_ABSENT = {"STT_MODEL_MISSING", "OLLAMA_UNREACHABLE"}  # proves nothing was downloaded
# DEPENDENCY_MISSING is only expected for the model/audio-processing packages that CI
# deliberately does not install; anything else missing is a real packaging problem.
EXPECTED_MISSING_PACKAGES = {"faster_whisper", "ctranslate2", "numpy"}
MUST_PASS = {
    "platform": "WINDOWS",
    "python": "PY311",
    "windows_actions": "SIMULATED_LAUNCHER",
    "activation": "MANUAL",
}


def main(path: str) -> int:
    report = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    checks = {check["name"]: check for check in report["checks"]}
    problems: list[str] = []

    print("Preflight on CI runner (expected BLOCKED: no models, microphone, voice or Ollama)")
    for check in report["checks"]:
        note = EXPECTED_ABSENCES.get(check["code"], "")
        print(f"  [{check['status']:4}] {check['name']:16} {check['code']:26} {note}")

    if report["ready"]:
        problems.append("preflight READY on a runner without models: probes are not reliable")
    for name, code in MUST_PASS.items():
        check = checks.get(name)
        if check is None or check["status"] != "PASS" or check["code"] != code:
            problems.append(f"policy check {name} expected PASS/{code}, got {check}")
    unexpected = [code for code in report["blocking"] if code not in EXPECTED_ABSENCES]
    if unexpected:
        problems.append(f"unexpected blockers: {unexpected}")
    dependencies = checks.get("dependencies")
    if dependencies is not None and dependencies["code"] == "DEPENDENCY_MISSING":
        missing_packages = {name.strip() for name in dependencies["detail"].split(",") if name.strip()}
        extra = missing_packages - EXPECTED_MISSING_PACKAGES
        if extra:
            problems.append(f"unexpected missing packages: {sorted(extra)}")
    missing = MUST_BE_ABSENT - set(report["blocking"])
    if missing:
        problems.append(f"expected absences not reported: {sorted(missing)}")

    if problems:
        for problem in problems:
            print(f"::error::{problem}")
        return 1
    print(f"DIAGNOSE_AS_EXPECTED: {len(report['blocking'])} documented absence(s), policy checks PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
