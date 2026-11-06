"""JAR-COG-01-R02 — focused Kaggle retest of the R01 failures (run as one cell).

Prerequisites, as in R01 (nothing is installed or downloaded here): repository checked
out at the SHA published by JAR-COG-01-R02, working directory = repository root, Python
3.11 venv with pydantic/psutil, Ollama already serving 127.0.0.1:11434 with qwen3.5:2b.

What it does:
1. Verifies the SHA (fails early).
2. Measures the model **cold load** separately with Wyzer's own ``warm_up()`` (empty
   generation, ``keep_alive``), so the scenarios below run with the model **loaded**.
3. Runs only the affected scenarios: ORION intro/title/recall (one session), ``sera?``,
   time and system questions, the report greeting, the two R01 timeout questions
   (capital, identity; three warm repetitions each), the simulated Calculator and the
   follow-up "Que operação fizeste há pouco?", and an honest refusal ("Abre o Paint.").
4. Judges each turn with ``qa/kaggle/semantic_judge.py`` and prints, per turn: result,
   layer, evidence, llm calls, load / prompt / generation ms, prompt tokens, tools
   executed and dropped. The configured timeout is printed, never changed.
5. Writes metrics only (no conversation text) to ``/kaggle/working/cog01_r02``.
Applications stay simulated (``allow_real_windows_actions`` forced to ``false``).
"""

import asyncio
import importlib.util
import json
import subprocess
import sys
import time
import tomllib
from pathlib import Path

EXPECTED_SHA = ""  # paste the SHA published by JAR-COG-01-R02 before running
MODEL = "qwen3.5:2b"
OUT = Path("/kaggle/working/cog01_r02")

head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
if not EXPECTED_SHA or head != EXPECTED_SHA:
    raise SystemExit(f"SHA mismatch: HEAD={head!r} expected={EXPECTED_SHA!r} — stop.")
sys.path.insert(0, str(Path.cwd()))

from jarvis.brain.pt_provider import create_local_provider  # noqa: E402
from jarvis.config import parse_slice_config  # noqa: E402
from jarvis.core.assistant import build_voice_session  # noqa: E402
from jarvis.tools.allowlist import SimulatedLauncher  # noqa: E402
from jarvis.ui.events import RecordingSink  # noqa: E402

_spec = importlib.util.spec_from_file_location("semantic_judge", Path("qa/kaggle/semantic_judge.py"))
sj = importlib.util.module_from_spec(_spec)
sys.modules["semantic_judge"] = sj
_spec.loader.exec_module(sj)

data = tomllib.loads(Path("configs/jarvis_slice.toml").read_text(encoding="utf-8"))
data["llm"]["model"] = MODEL
data["llm"]["endpoint"] = "http://127.0.0.1:11434"
data["vexel"]["allow_real_windows_actions"] = False
CONFIG = parse_slice_config(data)
assert CONFIG.vexel.allow_real_windows_actions is False
print(f"configured request_timeout_seconds={CONFIG.wyzer.llm.request_timeout_seconds} (unchanged)")


class Speech:
    def speak(self, text):
        return None

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
    provider = create_local_provider(CONFIG.wyzer)
    session, _parts = build_voice_session(
        CONFIG, provider, stt=NoStt(), tts=Speech(), activation=Activation(),
        sink=RecordingSink(), launcher=launcher,
    )
    session.start()
    return session, launcher, provider


A = sj.EXPECTATIONS
SIMULATED = sj.Expectation("simulated", app="calculator")
SCENARIOS = [
    ("ORION", [("Olá Jarvis. Estou a preparar um relatório sobre o projecto Orion.", None),
               ("O título do relatório é Auditoria de Rede.", None),
               ("Qual é o nome do projecto?", None),
               ("E qual é o título do relatório?", None)]),
    ("SERA_DATE", [("sera?", None)]),
    ("TIME", [("Que horas são em Maputo?", None)]),
    ("SYSTEM", [("Como está o computador?", None)]),
    ("REPORT_GREETING", [("Olá Jarvis, estou a preparar um relatório.", None)]),
    *[(f"TIMEOUT_CAPITAL_{i}", [("Qual é a capital de Moçambique?", None)]) for i in range(3)],
    *[(f"TIMEOUT_IDENTITY_{i}", [("Quem és tu?", None)]) for i in range(3)],
    ("ACTION_MEMORY", [("Abre a calculadora.", None), ("sim", SIMULATED),
                       ("Que operação fizeste há pouco?", None)]),
    ("HONEST_REFUSAL", [("Abre o Paint.", None)]),
]
LATENCY_KEYS = ("llm_calls", "llm_ms", "llm_load_ms", "llm_prompt_tokens", "llm_prompt_ms",
                "llm_generation_ms", "think_ms")


async def warm_up():
    _session, _launcher, provider = new_session()
    started = time.monotonic()
    try:
        await provider.inner.warm_up()
        status = "OK"
    except Exception as error:  # report, never hide
        status = f"FAILED:{type(error).__name__}"
    load_s = time.monotonic() - started
    timings = getattr(provider.inner._transport, "last_timings", {})
    return status, load_s, timings


async def run_all():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    with (OUT / "turns.jsonl").open("w", encoding="utf-8") as metrics:
        for name, turns in SCENARIOS:
            session, launcher, _provider = new_session()
            for text, expectation in turns:
                before = len(launcher.requested)
                result = await session.handle_text(text)
                record = result.as_record(include_text=False)
                verdict = sj.judge(text, result.reply, record, expectation or A.get(text),
                                   launched=launcher.requested[before:])
                rows.append((name, text, result.reply or "", verdict, record))
                metrics.write(json.dumps({**record, "scenario": name, **verdict.as_dict()},
                                         ensure_ascii=False) + "\n")
            session.shutdown()
    return rows


status, load_s, timings = asyncio.run(warm_up())
print(f"WARM-UP (cold load, separate from scenarios): {status} wall={load_s:.1f}s "
      f"load_duration_ms={timings.get('load_duration', 0) / 1e6:.0f}")
rows = asyncio.run(run_all())
for name, text, reply, verdict, record in rows:
    m = record.get("metrics") or {}
    lat = " ".join(f"{k}={m[k]:.0f}" for k in LATENCY_KEYS if k in m)
    print(f"\n[{verdict.result}/{verdict.layer}] {name} | {text}")
    print(f"  OUTPUT: {reply[:120]}")
    print(f"  {lat} tools={record.get('tools_executed')} dropped={record.get('tools_rejected')}")
    print(f"  evidence: {verdict.evidence}")
passed = sum(1 for r in rows if r[3].result == "PASS")
by_layer = {layer: sum(1 for r in rows if r[3].layer == layer) for layer in sj.LAYERS}
timeouts = sum(1 for r in rows if str(r[4].get("detail")) == "PROVIDER_TIMEOUT")
print(f"\nPASS {passed}/{len(rows)}  failures by layer: {by_layer}  timeouts(warm)={timeouts}")
for command in (["ollama", "--version"], ["ollama", "ps"], ["ollama", "list"],
                ["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.used", "--format=csv"]):
    out = subprocess.run(command, capture_output=True, text=True)
    print("$", " ".join(command), "\n", out.stdout.strip() or out.stderr.strip())
(OUT / "summary.json").write_text(json.dumps({
    "sha": head, "model": MODEL, "warm_up": status, "warm_up_wall_s": load_s,
    "pass": passed, "total": len(rows), "by_layer": by_layer, "warm_timeouts": timeouts,
    "timeout_s": CONFIG.wyzer.llm.request_timeout_seconds,
}, indent=2), encoding="utf-8")
print(f"metrics (no text): {OUT}/turns.jsonl, {OUT}/summary.json")
