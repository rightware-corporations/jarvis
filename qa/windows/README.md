# Windows QA (JAR-SLICE-01C)

- `Invoke-JarvisPreflight.ps1`: read-only inventory for the authorised QA PC (Windows, CPU/RAM/GPU, disk, Python 3.11, Ollama and its local port, SAPI and OneCore voices, audio endpoints). Writes sanitised `report.txt`, `report.json` and `transcript.txt` under `evidence\` (git-ignored). Optional `-CopySummary` copies the summary to the clipboard.
- `ci_expect_diagnose.py`: used by the `windows-python` CI job; checks that `--diagnose` on a runner reports exactly the expected absences (no models, microphone, voice or Ollama) and that the policy checks pass.
- [`DEMO_KIT.md`](DEMO_KIT.md): ordered steps for the first demonstration on the QA PC.
- Full procedure, gates G1–G10, licences and rollback: [`docs/25_JAR-SLICE-01C_WINDOWS_QA_PLAN.md`](../../docs/25_JAR-SLICE-01C_WINDOWS_QA_PLAN.md).

Run only with RIGHTWARE authorisation:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\qa\windows\Invoke-JarvisPreflight.ps1
```

It installs nothing, downloads nothing, records nothing, needs no administrator rights and changes no setting. Review the report by hand before sharing it.
