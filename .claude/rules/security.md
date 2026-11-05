# Regras de segurança e privacidade

Fontes:
- [`SECURITY.md`](../../SECURITY.md);
- [`docs/25_JAR-SLICE-01C_WINDOWS_QA_PLAN.md`](../../docs/25_JAR-SLICE-01C_WINDOWS_QA_PLAN.md) §0 e §2;
- relatórios em [`docs/reports/`](../../docs/reports/README.md).

Cada item é um contrato coberto por testes. Enfraquecê-lo é motivo de recusa.

1. **Acções reais desligadas.**
   - `allow_real_windows_actions = false`.
   - O lançador real só existe para a 01D, só em Windows e só com autorização.
   - CI e cloud usam o lançador simulado (`SIMULATED_LAUNCHER`).
2. **Confirmação.**
   - Acções com efeito exigem confirmação PT («sim/não/cancela»), ligada a `action_id` + digest + ferramenta, com TTL e anti-replay.
   - Se a pergunta não foi apresentada (TTS falhou ou foi interrompido), não há confirmação válida (fail-closed).
3. **Honestidade de estado.** `ActionStatus` é `SIMULATED`, `SUCCEEDED`, `FAILED` ou `DENIED`. A resposta nunca afirma sucesso que o estado não suporta.
4. **Sem execução arbitrária.**
   - Nada de shell, subprocessos ou `eval` no runtime.
   - O preflight usa `sys.getwindowsversion()` / `os.uname()`, não o módulo `platform`, que lança processos.
   - O guard de processos de `tests_vexel/conftest.py` só permite `[sys.executable, scripts/verify_import.py]`.
5. **Local e gratuito.**
   - LLM via Ollama em `127.0.0.1`, `auto_start = false`.
   - Sem APIs pagas, chaves ou SDKs comerciais obrigatórios.
   - Em CI e cloud: sem download de modelos.
6. **Wake word bloqueada** (`WAKE_WORD_BLOCKED`): activação manual; não usar os modelos `hey_jarvis`.
7. **Privacidade.**
   - `log_transcript_text = false`.
   - Logs e modelos ficam em `.wyzer/` (git-ignored).
   - Nunca se publicam áudio, transcrições, dados do PC do Issa, nomes de máquina ou de utilizador, tokens ou variáveis de ambiente (nem em logs de CI).
8. **Web Lab.** Não é o produto: sem ferramentas Windows reais, token obrigatório, sem exposição pública sem gate.
9. **Terceiros.**
   - Validar a origem e a licença antes de copiar código, assets, skills ou plugins.
   - PySide6 6.6.1 é LGPL-3.0 (ligação dinâmica, sem modificações).
   - Kokoro/espeak-ng tem pendente a revisão GPL (VOICE-TTS-LIC-01).
10. **PC do Issa.** Nada se instala ou configura nele. QA real só no PC de QA autorizado, com plano 25.
