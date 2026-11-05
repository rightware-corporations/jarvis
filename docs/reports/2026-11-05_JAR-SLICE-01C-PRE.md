# JAR-SLICE-01C-PRE — Preparação para IA e voz reais no Windows

**Estado final: `PREP_READY`.** Não equivale a funcionamento real do Jarvis.
**Base:** `develop@372c21905ca2478c8b545e6b67af528a587e51b0` (= `origin/develop`, `REMOTE_CI_PASS`)
**HEAD local:** `4ac65269d0964eb7c47adb29052bae0fc79b1c5d` · 3 commits locais · árvore limpa · **sem push**

---

## 1. Fase 1 — Reconciliação do núcleo

| Gate | Resultado |
|---|---|
| G1 HEAD, árvore, integridade | PASS: HEAD = `origin/develop` = `372c219`, árvore limpa, 182/182 |
| G2 interfaces revistas | `__main__` (só `--check-config` e `--text`), `assistant.build_voice_session`, `stt_pt` (subclasse PT, sem captura ligada), `tts` (fábrica sem selecção de voz PT), `activation` (manual), `pt_provider` (Ollama via Wyzer), `jarvis_slice.toml` |
| G3 o que faltava para a voz real | modo de voz explícito; ligação da captura ao Whisper; selecção de uma voz PT **instalada**; detecção de microfone, voz, Ollama e modelo; tratamento de falhas de captura e STT (antes eram tratadas como silêncio); cancelamento e encerramento dos adapters; registo de tempos por turno |
| G4 `--text` | preservado; `_text_mode` não foi alterado |
| G5 sem duplicar o Wyzer | reutilizados: `WindowsSpeechRecognizer.capture_utterance`, `PowerShellSpeechRunner`, `OllamaChatProvider.diagnose()` (`/api/tags`), `install_check._whisper_present`, `WindowsSpeechSynthesizer`, `runtime_paths.data_home`. Única duplicação mínima: o comando de download do Whisper no plano de QA, porque o `wyzer.install_check` lê o `wyzer.toml` (`small.en`) |

## 2. Fase 2 — Runtime de voz (o que foi implementado)

| # | Requisito | Implementação |
|---|---|---|
| 1 | Modo de voz explícito | `python -m jarvis --voice` (`jarvis/runtime/voice_mode.py`); `--diagnose [--json]` para o relatório |
| 2 | Captura substituível | `AudioCapture` → `WyzerMicrophoneCapture` (Wyzer), envolvida em `CancellableCapture` |
| 3 | Whisper PT no ciclo | `create_voice_input()`: captura → `PortugueseWhisperRecognizer` (`language="pt"`, hotwords da configuração, `local_files_only`) |
| 4 | Voz SAPI PT instalada | `jarvis/voice/sapi.py`: inventário via `PowerShellSpeechRunner`. Usa a voz configurada se for PT e estiver activa; senão pt-PT, depois pt-BR. Nunca escolhe uma voz não portuguesa |
| 5 | Ausência de microfone | `probe_microphone()` (lista de dispositivos, sem abrir stream): `MIC_MISSING`, `MIC_NO_DEFAULT`, `AUDIO_QUERY_FAILED`, `AUDIO_DEPENDENCY_MISSING` |
| 6 | Ausência de voz PT | `PT_VOICE_MISSING` (indica as culturas instaladas); `PT_VOICE_FALLBACK` = WARN |
| 7 | Ollama indisponível ou modelo em falta | `OLLAMA_UNREACHABLE`, `MODEL_NOT_INSTALLED`; o Jarvis nunca arranca o Ollama (`auto_start=false`) |
| 8 | Cancelamento e encerramento | `cancel()` chega à captura (o áudio capturado através de um cancelamento é descartado); `shutdown()` fecha a captura e o TTS; consola em thread daemon (nunca impede a saída) |
| 9 | Tempos por componente | `stt_ms`, `think_ms`, `tts_ms` por turno em `voice-turns.jsonl`; estados em `ui-events.jsonl` |
| 10 | Diagnóstico privado | logs sem texto por omissão; nada é gravado; directório por omissão `.wyzer/vexel/logs` (git-ignored) |

Falhas de captura e STT são agora `STT_FAILED`, com estado `ERROR` → frase PT → `IDLE`. Cancelam qualquer confirmação pendente: um `sim` posterior não executa nada.

Correcção encontrada durante os testes: o preflight usava `platform.platform()`, que em Linux lança `uname -p`. A guarda de processos da suite detectou-o, e foi substituído por chamadas que não arrancam processos.

## 3. Fase 3 — Preflight Windows (para revisão; não executado)

`qa/windows/Invoke-JarvisPreflight.ps1` (PowerShell 5.1, só ASCII):

- **Recolhe:** Windows, CPU, RAM, GPU/VRAM (registo, porque o WMI limita a 4 GB), disco, Python 3.11 (`py -0p`), Ollama (versão e porta 127.0.0.1 com `/api/version` e `/api/tags`), vozes SAPI e OneCore, reconhecedores, endpoints de áudio (registo MMDevices).
- **Saída:** `report.txt`, `report.json` e `transcript.txt` higienizados em `evidence\` (git-ignored); `-CopySummary` é opt-in.
- **Privacidade:**
  - remove utilizador, computador, domínio e caminhos de perfil;
  - remove nomes possessivos em dispositivos («Ana's AirPods»), MAC e IP;
  - não usa `Start-Transcript`, porque o cabeçalho desse transcript regista o utilizador e a máquina.
- **Validação:** 21 testes estáticos. Proíbem instalação, download, `ollama pull/serve`, escrita no registo, remoção ou movimentação de ficheiros, serviços e processos, políticas, elevação, `Invoke-Expression`, gravação e fala, segredos e identificadores. Exigem rede só em loopback, escrita só nos próprios relatórios, clipboard opt-in, sintaxe compatível com 5.1, chavetas equilibradas e comandos nativos que não abortam com stderr.
- **Limitação:** não havia PowerShell neste ambiente, por isso o script **não foi executado nem analisado pelo parser oficial**. A primeira execução no G1 é também a primeira validação real.

## 4. Fase 4 — Matriz PASS/FAIL (testes com fakes)

| # | Item da ordem | Testes | Resultado |
|---|---|---|---|
| 1 | Inicialização do modo de voz | arranque, turno e shutdown; preflight READY; fábricas por omissão sem carregar modelos | PASS |
| 2 | Ausência de microfone | 3 casos do probe + falha de query + modo de voz bloqueado | PASS |
| 3 | Ausência de voz PT | bloqueio; 7 casos de selecção; WARN para voz não PT configurada; parsing; sem sonda fora do Windows | PASS |
| 4 | Ollama indisponível ou modelo em falta | `OllamaChatProvider` real do Wyzer com transporte falso (4 casos, 1 GET a `/api/tags`); modo de voz bloqueado; modelo que desaparece → frase PT | PASS |
| 5 | Falha de captura de áudio | `CaptureError` → `STT_FAILED` (capture); adapter Whisper real propaga `CaptureError` sem carregar o modelo | PASS |
| 6 | Falha do STT | Whisper e erro inesperado → `STT_FAILED` (stt); confirmação pendente cancelada | PASS |
| 7 | Falha do TTS | no runtime: `tts_failed` e recuperação no turno seguinte (+21 casos da R01) | PASS |
| 8 | Cancelamento durante o reconhecimento | descarta a frase, o adapter é cancelado, nada é enviado ao modelo; `CancellableCapture` descarta o áudio e recusa após `close` | PASS |
| 9 | Resposta tardia após cancelamento | turno de voz com provider que ignora o cancelamento: descartado, sem confirmação pendente | PASS |
| 10 | Confirmações não apresentadas | TTS falha no pedido: `confirmation_not_presented`, o `sim` em fila nunca é consumido | PASS |
| 11 | Ferramentas Windows desactivadas | o runtime usa sempre o `SimulatedLauncher`; `allow_real_windows_actions=true` bloqueia o arranque; guarda de processos activa | PASS |
| 12 | Regressão dos 321 anteriores | 321/321 dentro dos 399 | PASS |
| — | Script PowerShell (estático) | 21 casos | PASS |

**Totais:** 399 passed, 0 failed, 0 skipped (305→383 em `tests_vexel`, mais 16 em `tests_lab`). São 78 novos: 47 do runtime, 21 do script e 10 verificações estáticas dos módulos novos. Estável em 10 execuções consecutivas. Reprodução do CI num venv novo (pydantic 2.14.3, psutil 7.2.2): 383 + 16 PASS.

## 5. Verificações obrigatórias (HEAD `4ac6526`)

| Comando | Resultado |
|---|---|
| `python scripts/verify_import.py` | 182/182, rc=0 |
| `python -m compileall -q wyzer jarvis tests_vexel tests_lab` | rc=0 |
| `pytest tests_vexel tests_lab` | 399 passed, rc=0 |
| `python -m jarvis --check-config` | `CONFIG_OK`, rc=0 |
| `python -m jarvis --diagnose` (cloud Linux) | `PREFLIGHT BLOCKED`, rc=3 (esperado: não é Windows, sem pacotes, sem modelo, sem Ollama) |
| `python -m jarvis --voice` (cloud Linux) | recusa arrancar, rc=3 |
| `python -m jarvis --text` | arranca e termina com EOF, rc=0 |
| Por commit | `e21495c` 378 PASS · `bfdefb7` 399 PASS · `4ac6526` 399 PASS; 182/182 em todos |
| Manifesto | 0 caminhos tocados; blob SHA 182/182 |
| Workflow | não alterado |
| Imports novos de terceiros no runtime | nenhum (stdlib, `jarvis` e `wyzer`; `numpy`, `sounddevice` e `faster_whisper` são importados de forma tardia, via Wyzer) |
| Binários, modelos, áudio, segredos, dados pessoais | nenhum |

## 6. Commits locais

| SHA | Mensagem |
|---|---|
| `e21495cc29e247fdf72aa946f3e7787369918fa0` | feat(slice-01c-pre): voice runtime, read-only preflight and fail-closed STT handling |
| `bfdefb74b44fd3723aa10c060045c2eac25b8af7` | feat(qa): read-only Windows QA preflight script for JAR-SLICE-01C |
| `4ac65269d0964eb7c47adb29052bae0fc79b1c5d` | docs(slice-01c-pre): Windows QA plan G1-G10, licences, corpus and status |

**Ficheiros (18; +2172/−8):**

- **Novos:**
  - `jarvis/runtime/__init__.py`, `jarvis/runtime/preflight.py`, `jarvis/runtime/voice_mode.py`
  - `jarvis/voice/capture.py`, `jarvis/voice/sapi.py`
  - `qa/windows/Invoke-JarvisPreflight.ps1`, `qa/windows/README.md`
  - `tests_vexel/test_01c_pre_voice_runtime.py`, `tests_vexel/test_01c_pre_windows_preflight_static.py`
  - `docs/25_JAR-SLICE-01C_WINDOWS_QA_PLAN.md`
- **Alterados:**
  - `jarvis/__main__.py`, `jarvis/config.py`, `jarvis/core/voice_loop.py`
  - `jarvis/voice/contracts.py`, `jarvis/voice/stt_pt.py`
  - `configs/jarvis_slice.toml`
  - `docs/01_CURRENT.md`, `docs/03_BACKLOG.md`

**Repositório:** local `develop` em `4ac6526`, 3 commits à frente; remoto `origin/develop` = `372c219`, inalterado. Só existem `main` e `develop`; sem worktrees nem tags novas.

## 7. Fase 5 — Plano de execução Windows

Em `docs/25_JAR-SLICE-01C_WINDOWS_QA_PLAN.md`: G1–G10, com comandos exactos, critérios PASS, condições de STOP e evidência por gate. Inclui o corpus PT-MZ de 20 frases, a tabela de comparação `qwen3.5:4b` vs `qwen3.5:2b` (o modelo por omissão nunca é alterado automaticamente) e o rollback validado por um novo preflight.

## 8. Dependências e licenças (para a 01C)

**Instalação no venv do PC de QA**, fixada pelas constraints do Wyzer:

| Pacote | Versão |
|---|---|
| pydantic | 2.12.3 |
| psutil | 7.1.3 |
| numpy | 1.26.4 |
| sounddevice | 0.5.3 |
| faster-whisper | 1.2.1 |
| ctranslate2 | 4.6.2 |
| av | 16.0.1 |
| onnxruntime | 1.23.2 |
| huggingface-hub | 0.36.2 |

Não instalar nesta fase: kokoro, torch, openwakeword, PySide6.

**Licenças** (tabela completa no plano): MIT para faster-whisper, CTranslate2, o modelo Whisper, onnxruntime, sounddevice e Ollama; BSD-3 para numpy e PyAV; Apache-2.0 para huggingface-hub.

**Bloqueadores de licença:**
- **Qwen3.5:** Apache-2.0 apenas segundo fontes secundárias ([The AI Bench](https://theaibench-site.pages.dev/models/qwen-3-5-4b/)); tem de ser confirmado com `ollama show --license` no G3. Uma fonte encontrada ([DEV Community](https://dev.to/preecha/how-to-use-qwen-35-with-ollama-20a0)) contradiz-se nos tamanhos e na RAM, por isso os números são medidos no G9.
- **FFmpeg nas wheels do PyAV:** LGPL, a rever antes de qualquer distribuição.
- **Wake word:** `WAKE_WORD_BLOCKED` mantém-se.
- **Kokoro/espeak-ng:** GPL, fora desta fase.

## 9. Riscos residuais

1. **O script PowerShell nunca correu.** Só tem validação estática e revisão manual; pode haver erros de runtime só visíveis no Windows (por exemplo, propriedades do registo diferentes por versão).
2. **Vozes OneCore** podem não ser visíveis ao System.Speech. Nesse caso o preflight dá WARN, mas o Jarvis não as consegue usar sem trabalho adicional.
3. **A captura do Wyzer não é interrompível a meio de uma frase.** Pode bloquear até ao timeout (8 s) ou ao limite de 15 s; o áudio é descartado, mas a thread fica ocupada até lá.
4. **Limiar de energia fixo do Wyzer (250 RMS):** em ambientes ruidosos ou com microfones fracos pode cortar ou não detectar a fala. Medir no G5.
5. **Comportamento do modelo real** (tool calling em PT com 4B) é desconhecido: o maior risco funcional do G4/G8.
6. **Latência em CPU** do Whisper `small` + 4B + SAPI pode exceder a referência de p95 ≤ 8 s.
7. **Fuso horário:** o Windows não tem tzdata por omissão; o relógio cai para a hora local do sistema (já tratado na 01B, a confirmar no G4).
8. **Mantêm-se os riscos da R01:** filtro de afirmações por padrões, `InProcessExecutor` sem cancelamento a meio de uma ferramenta, evidência de `SUCCEEDED` real por definir (01D).

## 10. Estado final

**`PREP_READY`.**
- O código de integração está preparado e passa nos testes remotos com fakes.
- Os 182 ficheiros estão intactos.
- O diagnóstico Windows está pronto para revisão.
- Os bloqueadores de ambiente e de licença estão identificados.
- O plano de QA tem gates, procedimentos e rollback.
- A execução real continua desactivada (o voice runtime recusa arrancar fora de um preflight READY, e as aplicações são sempre simuladas).

Próximo passo, que depende de autorização: rever o script e o plano, publicar estes 3 commits e correr o CI remoto, e depois executar G1–G10 no PC de QA.
