# Remote QA — import baseline (2026-11-04)

## Initial pipeline
The workflow `.github/workflows/source-integrity.yml` runs on `develop` and pull requests to `develop`/`main`. It:
1. Verifies all **182** imported text/source files against the immutable upstream Git blob SHA-1 identifiers from `upstream-v0.3.1-manifest.json`.
2. Runs `python -m compileall -q wyzer tests scripts` on GitHub-hosted Ubuntu/Python 3.11.

**What it DOES NOT prove:** dependency installation, imports under Linux, unit-test results, voice/wake-word quality, Ollama replies, tool execution, browser access or Windows readiness.

## Branch policy
- `main`: stable, documented work; no directly developed experimental features.
- `develop`: integration and engineering.
- The pre-existing temporary `feat/wyzer-v031-core-import` must be **deleted** from GitHub to satisfy the request of exactly two branch refs. No changes should be made on that branch. GitHub integration does not currently expose deletion of branch refs; user/admin can remove it via GitHub UI.

## Baseline policy
The manifest protects the initial pristine import. Once an upstream file is intentionally modified, update this strategy: preserve a frozen upstream snapshot in a dedicated prefix or annotate and audit deliberately changed files. **Do not silently update the manifest SHA to conceal drift.** Until the change policy is implemented, any modified imported file will fail the integrity job.

## Next gates
- Execute source-integrity workflow and record actual run ID and conclusion.
- Audit imports to separate headless (Linux) from Windows-only packages.
- Implement provider and tool fake contract tests; refuse OS writes in web lab.
- Add PT language to confirmation/cancel controls and voice paths.
- Prove Ollama or self-hosted inference using a remote controlled runner before a web preview.
