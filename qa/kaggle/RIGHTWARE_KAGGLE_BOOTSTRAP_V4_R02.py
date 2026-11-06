"""RIGHTWARE VEXEL Jarvis — Kaggle complete recovery + JAR-COG-01-R02.

Single cell, no external paid APIs: Git develop, Python 3.11, verified Ollama
v0.40.15, qwen3.5:2b, official focused R02 QA. Read-only/simulated actions.
Run from Kaggle with GPU T4 and Internet enabled. Persistent backup in GitHub.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import sysconfig
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import ProxyHandler, build_opener

ROOT = Path("/kaggle/working")
REPO = ROOT / "rightware-jarvis"
PY = ROOT / ".venv-jarvis/bin/python"
OLLAMA = ROOT / ".ollama-runtime/bin/ollama"
ARCHIVE = ROOT / "ollama-linux-amd64-v0.40.15.tar.zst"
MODEL = "qwen3.5:2b"
RELEASE = "b80cef3d90bc66f53f7de7139f149695e34a715f"
URL = "https://github.com/ollama/ollama/releases/download/v0.40.15/ollama-linux-amd64.tar.zst"
DIGEST = "628c018404a4206493efd38e46251c154ede5141b8b8dc85c659b3b027c47379"
ROOT.mkdir(exist_ok=True, parents=True)

def run(*args, **kw):
    print("[RUN]", " ".join(map(str, args)), flush=True)
    return subprocess.run([str(x) for x in args], check=True, **kw)

def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()

def ready():
    try:
        with build_opener(ProxyHandler({})).open(
            "http://127.0.0.1:11434/api/version", timeout=4
        ) as response:
            return json.load(response)
    except Exception:
        return None

print("=== RIGHTWARE / RECOVERY V4 + REAL R02 ===", flush=True)
gpu = subprocess.run(["nvidia-smi", "-L"], text=True, capture_output=True)
if gpu.returncode or not gpu.stdout.strip():
    raise RuntimeError("GPU indisponível: activar GPU T4 e Internet no Kaggle.")
print("[PASS] GPU", gpu.stdout.strip(), flush=True)

if not (REPO / ".git").is_dir():
    if REPO.exists():
        raise RuntimeError("Pasta Jarvis sem .git; não sobrescrever.")
    run("git", "clone", "--branch", "develop", "--single-branch",
        "--depth", "30", "https://github.com/rightware-corporations/jarvis.git", REPO)
else:
    if git("remote", "get-url", "origin") not in {
        "https://github.com/rightware-corporations/jarvis.git",
        "git@github.com:rightware-corporations/jarvis.git",
    }:
        raise RuntimeError("Remote Git inesperado")
    if git("branch", "--show-current") != "develop":
        raise RuntimeError("O checkout não está em develop")
    if git("status", "--porcelain"):
        raise RuntimeError("Alterações locais: preservadas; actualização interrompida")
    run("git", "pull", "--ff-only", "origin", "develop", cwd=REPO)
run("git", "fetch", "--no-tags", "--depth", "80", "origin", "develop", cwd=REPO)
head = git("rev-parse", "HEAD")
if subprocess.run(
    ["git", "merge-base", "--is-ancestor", RELEASE, head], cwd=REPO
).returncode:
    raise RuntimeError("A HEAD de develop não contém a versão de código R02.")
print("[PASS] R02 CODE PRESENT, HEAD =", head, flush=True)

uv = shutil.which("uv")
if not uv:
    run(sys.executable, "-m", "pip", "install", "-q", "uv")
    candidates = [
        Path(sysconfig.get_path("scripts")) / "uv",
        Path(sys.executable).parent / "uv",
        Path.home() / ".local/bin/uv",
    ]
    uv = next((str(x) for x in candidates if x.exists()), None) or shutil.which("uv")
if not uv:
    raise RuntimeError("uv não disponível")
if not PY.exists():
    run(uv, "python", "install", "3.11")
    run(uv, "venv", "--python", "3.11", PY.parent.parent)
run(uv, "pip", "install", "--python", PY,
    "pydantic>=2.8,<3", "psutil>=6,<8", "tzdata", "zstandard>=0.23,<1")
run(PY, "--version")
integrity = subprocess.run(
    [str(PY), "scripts/verify_import.py"], cwd=REPO,
    check=True, capture_output=True, text=True
)
if "SOURCE_INTEGRITY_PASS" not in integrity.stdout:
    raise RuntimeError("Source integrity failed: " + integrity.stdout[-500:])
print("[PASS] WY ZER / SOURCE_INTEGRITY_182_182", flush=True)

if not OLLAMA.exists():
    if shutil.disk_usage(ROOT).free < 9 * 1024**3:
        raise RuntimeError("Necessários 9 GiB livres para Ollama e modelo")
    run("curl", "-fL", "--retry", "3", "--connect-timeout", "30",
        "-o", ARCHIVE, URL)
    h = hashlib.sha256()
    with ARCHIVE.open("rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    if h.hexdigest() != DIGEST:
        raise RuntimeError("SHA256 oficial do Ollama não corresponde")
    OLLAMA.parent.parent.mkdir(parents=True, exist_ok=True)
    extract = (
        "import sys,tarfile,zstandard;"
        "f=open(sys.argv[1],'rb');"
        "reader=zstandard.ZstdDecompressor().stream_reader(f);"
        "tarfile.open(fileobj=reader,mode='r|').extractall(sys.argv[2],filter='data')"
    )
    run(PY, "-c", extract, ARCHIVE, OLLAMA.parent.parent)
    if not OLLAMA.exists():
        raise RuntimeError("Ollama não foi extraído em bin/ollama")
    ARCHIVE.unlink()
print("[PASS] OLLAMA_BINARY", flush=True)

env = os.environ.copy()
env.update(
    OLLAMA_HOST="127.0.0.1:11434",
    OLLAMA_MODELS=str(ROOT / ".ollama-models"),
    OLLAMA_NO_CLOUD="1",
    CUDA_VISIBLE_DEVICES="0",
    PYTHONUNBUFFERED="1",
    PATH=str(OLLAMA.parent) + os.pathsep + env.get("PATH", ""),
)
Path(env["OLLAMA_MODELS"]).mkdir(parents=True, exist_ok=True)
if not ready():
    log = OLLAMA.parent.parent / "server.log"
    with log.open("ab") as f:
        proc = subprocess.Popen([str(OLLAMA), "serve"], env=env,
                                stdout=f, stderr=subprocess.STDOUT)
    for _ in range(60):
        if ready():
            break
        if proc.poll() is not None:
            raise RuntimeError("Ollama server ended: " +
                               log.read_text(errors="replace")[-1000:])
        time.sleep(1)
if not ready():
    raise RuntimeError("Ollama server not reachable on loopback")
print("[PASS] OLLAMA_SERVER", ready(), flush=True)

def model_present():
    output = subprocess.check_output([str(OLLAMA), "list"], env=env, text=True)
    return any(row.split() and row.split()[0] == MODEL
               for row in output.splitlines()[1:])

if not model_present():
    print("[RESTORE] qwen3.5:2b — model download", flush=True)
    with (ROOT / "jarvis_ollama_pull.log").open("wb") as f:
        proc = subprocess.Popen([str(OLLAMA), "pull", MODEL], env=env,
                                stdout=f, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 1800
        while proc.poll() is None:
            if time.monotonic() > deadline:
                proc.kill()
                raise RuntimeError("Model download exceeded QA limit")
            try:
                proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                print("[DOWNLOAD] Qwen3.5 2B em transferência...", flush=True)
    if proc.returncode:
        raise RuntimeError("Ollama pull failed; see jarvis_ollama_pull.log")
if not model_present():
    raise RuntimeError("qwen3.5:2b ausente")
print("[PASS] QWEN3.5_2B_READY", flush=True)

# Execute unchanged official QA in a separate process; only inject HEAD SHA.
script = REPO / "qa/kaggle/JAR-COG-01-R02_focused_retest.py"
source = script.read_text(encoding="utf-8")
needle = 'EXPECTED_SHA = ""'
if source.count(needle) != 1:
    raise RuntimeError("Contrato de EXPECTED_SHA mudou")
if 'data["vexel"]["allow_real_windows_actions"] = False' not in source:
    raise RuntimeError("Política de simulação Windows ausente")
source = source.replace(needle, f'EXPECTED_SHA = "{head}"', 1)
compile(source, str(script), "exec")
print("=== JAR-COG-01-R02 / REAL MODEL QA START ===", flush=True)
subprocess.run([str(PY), "-u", "-c", source], cwd=REPO,
               env=env, check=True, timeout=1800)
path = ROOT / "cog01_r02/summary.json"
if not path.exists():
    raise RuntimeError("R02 summary.json não foi gerado")
summary = json.loads(path.read_text(encoding="utf-8"))
print("=== JAR-COG-01-R02 / RESULTADO ===")
print(json.dumps(summary, indent=2, ensure_ascii=False))
zip_path = ROOT / (
    "JAR_COG_01_R02_EVIDENCE_" +
    datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".zip"
)
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
    for path in (ROOT / "cog01_r02/summary.json",
                 ROOT / "cog01_r02/turns.jsonl"):
        if path.exists():
            archive.write(path, path.name)
print("EVIDENCE_ZIP:", zip_path)
print("=== RIGHTWARE / R02 RECOVERY AND REAL RETEST COMPLETE ===")
