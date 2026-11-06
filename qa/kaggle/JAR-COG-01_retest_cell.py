"""JAR-COG-01 — single Kaggle retest cell with the real qwen3.5:2b (run as one cell).

Prerequisites (already present from JAR-INFER-01/B7, nothing is installed here):
* the repository checked out at the SHA published by JAR-COG-01, working directory =
  repository root, Python 3.11 venv with pydantic/psutil;
* Ollama already serving on 127.0.0.1:11434 with ``qwen3.5:2b`` already present (never downloaded here).

What it does: verifies the SHA, reuses Ollama and the model, runs the critical B7
scenarios (each in its own session) and the PT-MZ conversation corpus (one session),
prints ``INPUT | OUTPUT | EXPECTED | RESULT`` per turn, classifies failures with the
semantic judge (MODEL, BACKEND, PROVIDER, TEST_HARNESS, UNDETERMINED, with evidence;
JAR-COG-01-R02), and writes metrics only (no text) to ``/kaggle/working/cog01``.
Applications stay simulated: ``allow_real_windows_actions`` is forced to ``false``.
"""

import asyncio
import json
import statistics
import subprocess
import sys
import time
import tomllib
from pathlib import Path

EXPECTED_SHA = ""  # paste the SHA published by JAR-COG-01 before running
MODEL = "qwen3.5:2b"
OUT = Path("/kaggle/working/cog01")

head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
if not EXPECTED_SHA or head != EXPECTED_SHA:
    raise SystemExit(f"SHA mismatch: HEAD={head!r} expected={EXPECTED_SHA!r} — stop.")
sys.path.insert(0, str(Path.cwd()))

from jarvis.brain.pt_provider import create_local_provider  # noqa: E402
from jarvis.config import parse_slice_config  # noqa: E402
from jarvis.core.assistant import build_voice_session  # noqa: E402
from jarvis.tools.allowlist import SimulatedLauncher  # noqa: E402
from jarvis.ui.events import RecordingSink  # noqa: E402

data = tomllib.loads(Path("configs/jarvis_slice.toml").read_text(encoding="utf-8"))
data["llm"]["model"] = MODEL
data["llm"]["endpoint"] = "http://127.0.0.1:11434"
data["vexel"]["allow_real_windows_actions"] = False
CONFIG = parse_slice_config(data)
assert CONFIG.vexel.allow_real_windows_actions is False


class Speech:
    def __init__(self):
        self.spoken = []

    def speak(self, text):
        self.spoken.append(text)

    def stop(self):
        return None


class NoStt:
    def listen(self, timeout_seconds):
        return None


class Activation:
    def wait(self, timeout_seconds):
        return False

    def close(self):
        return None


def new_session():
    launcher = SimulatedLauncher()
    session, parts = build_voice_session(
        CONFIG, create_local_provider(CONFIG.wyzer), stt=NoStt(), tts=Speech(),
        activation=Activation(), sink=RecordingSink(), launcher=launcher,
    )
    session.start()
    return session, launcher


# expected: "answer" (no tool, no confirmation), "confirm:<app>", "simulated:<app>", "no_action"
CRITICAL = [
    [("Qual é a capital de Moçambique?", "answer", ["maputo"])],
    [("Quem és tu?", "answer", ["jarvis"])],
    [("quem es tu jarvis", "answer", ["jarvis"])],
    [("sera?", "answer", [])],
    [("Explica-me o que faz uma calculadora.", "answer", [])],
    [("Não abras a calculadora.", "answer", [])],
    [("Ontem pedi para abrir a calculadora.", "answer", [])],
    [("Qual é a diferença entre a Calculadora e o Bloco de Notas?", "answer", [])],
    [('Ele disse: "abre a calculadora"', "answer", [])],
    [("preciso de fazer contas", "answer", [])],
    [("Abre a calculadora.", "confirm:calculator", []), ("sim", "simulated:calculator", [])],
    [("Jarvis, podes abrir o Bloco de Notas?", "confirm:notepad", []), ("não", "no_action", [])],
    [("Abre o bloco de notas", "confirm:notepad", []), ("não", "no_action", []),
     ("Qual é a capital de Moçambique?", "answer", ["maputo"])],
]
corpus = json.loads(Path("qa/corpus/pt_mz_conversation_v1.json").read_text(encoding="utf-8"))
KEYWORDS = {"mentions Orion": ["orion"], "mentions Auditoria de Rede": ["auditoria"],
            "mentions Maputo": ["maputo"], "mentions Orion and Auditoria de Rede": ["orion", "auditoria"],
            "mentions Auditoria de Rede and Orion": ["orion", "auditoria"]}
CORPUS = [[(t["input"],
            "confirm:calculator" if t["tool"].startswith("confirm") else
            "simulated:calculator" if t["tool"].startswith("simulated") else "answer",
            KEYWORDS.get(t["model_expectation"], []))
           for t in corpus["turns"]]]


# JAR-COG-01-R02: the permissive keyword judge was replaced by qa/kaggle/semantic_judge.py
# (telemetry-first layers: MODEL, BACKEND, PROVIDER, TEST_HARNESS, UNDETERMINED).
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("semantic_judge", Path("qa/kaggle/semantic_judge.py"))
semantic_judge = importlib.util.module_from_spec(_spec)
sys.modules["semantic_judge"] = semantic_judge
_spec.loader.exec_module(semantic_judge)


def judge(result, launcher_before, launcher, expected, keywords, text=""):
    """Return (RESULT, layer, evidence) from the semantic judge."""
    launched = launcher.requested[launcher_before:]
    if expected.startswith("confirm:"):
        expectation = semantic_judge.Expectation("confirm", app=expected.split(":")[1])
    elif expected.startswith("simulated:"):
        expectation = semantic_judge.Expectation("simulated", app=expected.split(":")[1])
    elif expected == "no_action":
        expectation = semantic_judge.Expectation("answer", relevance=False)
    else:
        expectation = semantic_judge.EXPECTATIONS.get(text) or semantic_judge.Expectation(
            "answer", require=tuple((k,) for k in keywords)
        )
    verdict = semantic_judge.judge(
        text, result.reply, result.as_record(include_text=False), expectation, launched=launched
    )
    return verdict.result, verdict.layer, verdict.evidence


async def run_all():
    OUT.mkdir(parents=True, exist_ok=True)
    metrics = (OUT / "turns.jsonl").open("w", encoding="utf-8")
    rows, think, llm = [], [], []
    for group_name, groups in (("critical", CRITICAL), ("corpus", CORPUS)):
        for scenario in groups:
            session, launcher = new_session()  # each scenario isolated; turns share it
            for text, expected, keywords in scenario:
                before = len(launcher.requested)
                result = await session.handle_text(text)
                verdict, layer, evidence = judge(result, before, launcher, expected, keywords, text)
                rows.append((group_name, text, (result.reply or "")[:90], expected, verdict, layer))
                record = result.as_record(include_text=False)
                record.update(
                    group=group_name, expected=expected, verdict=verdict, layer=layer, evidence=evidence
                )
                metrics.write(json.dumps(record, ensure_ascii=False) + "\n")
                if "think_ms" in result.metrics:
                    think.append(result.metrics["think_ms"])
                if "llm_ms" in result.metrics:
                    llm.append(result.metrics["llm_ms"])
            session.shutdown()
    metrics.close()
    return rows, think, llm


started = time.monotonic()
rows, think, llm = asyncio.run(run_all())
print(f"{'GROUP':8} | {'INPUT':45} | {'OUTPUT':60} | {'EXPECTED':20} | RESULT | LAYER")
for group, text, output, expected, verdict, layer in rows:
    print(f"{group:8} | {text[:45]:45} | {output[:60]:60} | {expected:20} | {verdict:6} | {layer}")


def pct(values, q):
    if not values:
        return float("nan")
    ordered = sorted(values)
    return ordered[max(0, min(len(ordered) - 1, round(q / 100 * len(ordered)) - 1))]


passed = sum(1 for r in rows if r[4] == "PASS")
by_layer = {layer: sum(1 for r in rows if r[5] == layer) for layer in semantic_judge.LAYERS}
print(f"\nPASS {passed}/{len(rows)}  failures by layer: {by_layer}")
print(f"think_ms p50={pct(think, 50):.0f} p95={pct(think, 95):.0f}  llm_ms p50={pct(llm, 50):.0f} p95={pct(llm, 95):.0f}")
print(f"mean think_ms={statistics.mean(think) if think else float('nan'):.0f}  wall={time.monotonic() - started:.0f}s")
for command in (["ollama", "--version"], ["ollama", "ps"], ["ollama", "list"],
                ["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.used", "--format=csv"]):
    out = subprocess.run(command, capture_output=True, text=True)
    print("$", " ".join(command), "\n", out.stdout.strip() or out.stderr.strip())
(OUT / "summary.json").write_text(json.dumps({
    "sha": head, "model": MODEL, "pass": passed, "total": len(rows), "by_layer": by_layer,
    "think_ms_p50": pct(think, 50), "think_ms_p95": pct(think, 95),
    "llm_ms_p50": pct(llm, 50), "llm_ms_p95": pct(llm, 95),
}, indent=2), encoding="utf-8")
print(f"metrics (no text): {OUT}/turns.jsonl, {OUT}/summary.json")
