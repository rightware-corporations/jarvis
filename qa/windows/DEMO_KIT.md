# Kit da primeira demonstração (PC Windows de QA)

Sequência curta para o operador. O procedimento completo, os critérios PASS/STOP, as licenças e as regras de privacidade estão no [plano 25](../../docs/25_JAR-SLICE-01C_WINDOWS_QA_PLAN.md); este kit só os põe por ordem de execução. **Cada passo exige a autorização da RIGHTWARE indicada.** Aplicações sempre simuladas; wake word bloqueada.

| # | Passo | Comando | Evidência | Autorização |
|---|---|---|---|---|
| 1 | Inventário read-only (G1) | `powershell -NoProfile -ExecutionPolicy Bypass -File .\qa\windows\Invoke-JarvisPreflight.ps1` | `evidence\jarvis-preflight-*\report.txt` (rever à mão) | PC de QA |
| 2 | venv e dependências (G2) | ver plano 25 §G2 (inclui `tzdata==2025.2`) | `evidence\g2-freeze.txt`, 182/182, `CONFIG_OK` | instalação no venv |
| 3 | Ollama + modelo (G3) | `ollama pull qwen3.5:4b`; `ollama show qwen3.5:4b --license` | licença e `ollama list` | instalar Ollama e descarregar pesos |
| 4 | Conversa em texto (G4) | `.\.venv\Scripts\python -m jarvis --text` (6 comandos) | respostas por comando | — |
| 5 | Modelo STT + microfone (G5) | download `Systran/faster-whisper-small`; `--diagnose` | `STT_MODEL_OK`, `MIC_OK` | download do Whisper |
| 6 | Voz PT (G6) | `--diagnose` | `PT_VOICE_SELECTED` | instalar voz, se faltar |
| 7 | **Pré-condição** | `.\.venv\Scripts\python -m jarvis --diagnose` | **`PREFLIGHT READY`**; se não, parar | — |
| 8 | Primeiro ciclo de voz (G7/G8) | `.\.venv\Scripts\python -m jarvis --voice --config evidence\qa.toml` (Enter = falar) | corpus [`qa/corpus/pt_mz_v1.txt`](../corpus/pt_mz_v1.txt); 6 comandos | registo de transcrições, se pretendido |
| 9 | Orb em simultâneo (opcional) | `python -m apps.desktop --demo` num venv com `PySide6-Essentials==6.6.1` | o orb percorre os 9 estados | — |
| 10 | Latências (G9) | `.\.venv\Scripts\python qa\benchmarks\latency_summary.py .wyzer\vexel\logs\voice-turns.jsonl` | p50/p95 por fase e veredicto | — |
| 11 | Privacidade (fim) | `Get-ChildItem $env:TEMP -Filter 'wyzer-whisper-*.wav'` | contagem = 0 | remoção só com autorização |
| 12 | Rollback validado (G10) | plano 25 §G10 (sem apagar nada) | `evidence\g10-manifest.txt` | — |

**Notas:**
- O orb no passo 9 ainda mostra estados simulados. A ligação ao ciclo de voz real é o passo seguinte, depois de os gates G7/G8 passarem.
- Antes de partilhar, rever cada evidência segundo o §2.4 do plano 25. Nunca enviar áudio nem transcrições para o GitHub.
