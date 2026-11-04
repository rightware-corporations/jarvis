# Remote QA — import baseline (2026-11-04)

## Initial pipeline — primeiras execuções verificadas
The workflow `.github/workflows/source-integrity.yml` runs on `develop` and pull requests to `develop`/`main`. It:
1. Verifies all **182** imported text/source files against the immutable upstream Git blob SHA-1 identifiers from `upstream-v0.3.1-manifest.json`.
2. Runs `python -m compileall -q wyzer tests scripts` on GitHub-hosted Ubuntu/Python 3.11.

**First confirmed PASS:** [run 41813747553](https://github.com/rightware-corporations/jarvis/actions/runs/41813747553) — both jobs succeeded. `source-integrity` verified 182/182 Git blobs and Python compilation. `headless-contract` ran five tests successfully on Ubuntu/Python 3.11 after installing `psutil` in addition to Pydantic/pytest. Prior failed runs were caused by missing `psutil` during module import and are retained as historical failure evidence.

**What it DOES NOT prove:** installation of the full original Windows dependency set, execution of the original 49-file upstream test suite, voice/wake-word quality, real Ollama replies, real desktop tool execution, browser automation, API authentication, or Windows readiness.

## Branch policy
- `main`: stable, documented work; no directly developed experimental features.
- `develop`: integration and engineering.
- **Verified:** the obsolete `feat/wyzer-v031-core-import` branch was deleted via guarded, one-time GitHub Actions [run 41814286015](https://github.com/rightware-corporations/jarvis/actions/runs/41814286015). Branch listing now contains only `main` and `develop`. The privileged cleanup workflow was subsequently deleted.

## Baseline policy
The manifest protects the initial pristine import. Once an upstream file is intentionally modified, update this strategy: preserve a frozen upstream snapshot in a dedicated prefix or annotate and audit deliberately changed files. **Do not silently update the manifest SHA to conceal drift.** Until the change policy is implemented, any modified imported file will fail the integrity job.

## Next gates
- [x] Run ID 41813747553 checked: both jobs PASS; five headless contract tests PASS.
- Audit imports to separate headless (Linux) from Windows-only packages.
- Implement provider and tool fake contract tests; refuse OS writes in web lab.
- Add PT language to confirmation/cancel controls and voice paths.
- Prove Ollama or self-hosted inference using a remote controlled runner before a web preview.
