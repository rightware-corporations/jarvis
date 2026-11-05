# 25 — JAR-SLICE-01C: Plano de execução no PC Windows de QA

**Estado:** preparado em JAR-SLICE-01C-PRE e corrigido em JAR-SLICE-01C-PUB (FIX-01 a FIX-03); **não executado**. Cada gate exige autorização explícita da RIGHTWARE antes de começar.
**Base de código:** `develop` no SHA aprovado para a 01C (registar o SHA exacto em cada relatório).
**Âmbito:** activação manual → microfone → Whisper PT → Wyzer → Ollama local → voz SAPI PT. Aplicações **sempre simuladas**; wake word **bloqueada** (`WAKE_WORD_BLOCKED`).

### Alterações na JAR-SLICE-01C-PUB

- **FIX-01, dependências dos gates.** A versão anterior tinha duas dependências circulares:
  - o G1 exigia uma voz PT, que só o G6 instalava;
  - o G5 corria `--voice`, que só arranca com o preflight completo (voz PT incluída), verificado apenas no G6.

  Agora o G1 é um inventário que nunca é bloqueado pela falta de voz ou de microfone, e regista-as como *bloqueadores da fase de voz*. O G5 apenas instala e verifica o modelo STT e o microfone. O G6 apenas garante a voz PT. O primeiro teste de reconhecimento real acontece no G7, depois de um `--diagnose` READY.
- **FIX-02, rollback.** O G10 passou a validar o plano de rollback sem apagar nada. Qualquer remoção (modelos, venv, Ollama, vozes, evidências) é um passo separado, o R1, que exige autorização específica da RIGHTWARE e só acontece depois de as evidências estarem arquivadas.
- **FIX-03, privacidade de áudio.** Nova secção 2: o WAV temporário do Wyzer, os logs locais de transcrições e as regras de higienização antes de partilhar evidências.

## 0. Regras de execução

- PC Windows de QA autorizado; nunca o PC pessoal do Issa sem autorização separada.
- Utilizador Windows normal (sem administrador). Pedir elevação só onde estiver escrito, e só com autorização.
- Tudo dentro de uma pasta de trabalho, `C:\VEXEL-QA\jarvis`, e de um venv local `.venv` (git-ignored). Não fazer `pip install` global.
- Privacidade: ver a secção 2. **Nunca publicar áudio, transcrições ou identificadores pessoais no GitHub.**
- Nada é apagado durante ou depois dos testes sem autorização específica (secção 1, R1).
- Gate com FAIL → STOP e relatório; os gates que dependem dele não começam. Excepção explícita: no G1, a falta de voz PT ou de microfone é registada como bloqueador da fase de voz (BLOCKER_VOICE) e não pára o inventário nem os gates G2–G4.
- Evidência mínima por gate: comando executado, saída relevante, PASS/FAIL/BLOCKER, data/hora, SHA do código.

### Dependências

```
G1 inventário ──► G2 dependências ──► G3 Ollama+modelo ──► G4 modo texto
                        │
                        ├──► G5 modelo STT + microfone ─┐
                        └──► G6 voz PT ─────────────────┤
                                       G3 ──────────────┤
                                                        ▼
                                  G7 ciclo de voz real (exige --diagnose READY)
                                                        ▼
                                  G8 seis comandos por voz ──► G9 benchmark
                                                        ▼
                         G10 validação do plano de rollback (sem apagar nada)
                                                        ▼
                         R1 remoção — só com autorização específica
```

G4 depende apenas de G2 e G3 e pode correr sem microfone nem voz. G5 e G6 são independentes entre si. G7 é o primeiro gate que usa microfone e voz em conjunto, e só começa se G3, G5 e G6 estiverem PASS e `--diagnose` der `PREFLIGHT READY`.

## 1. Gates

### G1 — Inventário de hardware (read-only)
1. Copiar o repositório (zip do SHA aprovado ou `git clone`) para `C:\VEXEL-QA\jarvis`.
2. `powershell -NoProfile -ExecutionPolicy Bypass -File .\qa\windows\Invoke-JarvisPreflight.ps1`. Opcional: `-CopySummary`. O `Bypass` aplica-se apenas a este processo.
3. Rever à mão `evidence\jarvis-preflight-*\report.txt` e `report.json` (secção 2.4) antes de os anexar.

**Classificação:**

| Item | PASS | BLOCKER_VOICE (continua para G2–G4) | STOP (pára tudo) |
|---|---|---|---|
| Windows | 10/11 x64 | — | outra arquitectura ou versão |
| RAM | ≥ 16 GB (8–16 GB = WARN → plano `qwen3.5:2b`) | — | < 8 GB |
| Disco livre | ≥ 15 GB | — | < 10 GB |
| Python 3.11 | registado no `py` | — | ausente e sem autorização para instalar |
| Microfone | ≥ 1 entrada activa | nenhuma entrada activa | — |
| Voz PT | SAPI PT activa | ausente, ou só OneCore (WARN) | — |

O G1 nunca exige voz PT nem microfone. Regista-os para que o G5 e o G6 os resolvam.

### G2 — Instalação isolada e reversível de dependências
```powershell
cd C:\VEXEL-QA\jarvis
py -3.11 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -c installer\constraints-windows-py311.txt `
    pydantic psutil numpy sounddevice faster-whisper huggingface-hub
.\.venv\Scripts\python -m pip install tzdata==2025.2   # IANA timezones: Windows Python has none
.\.venv\Scripts\python -m pip freeze > evidence\g2-freeze.txt
.\.venv\Scripts\python scripts\verify_import.py
.\.venv\Scripts\python -m jarvis --check-config
```
As versões são fixadas pelas constraints do próprio Wyzer: `pydantic==2.12.3`, `psutil==7.1.3`, `numpy==1.26.4`, `sounddevice==0.5.3`, `faster-whisper==1.2.1`, `ctranslate2==4.6.2`, `av==16.0.1`, `onnxruntime==1.23.2`, `huggingface-hub==0.36.2`. Mais `tzdata==2025.2` (Apache-2.0): sem ele, o Python no Windows não conhece `Africa/Maputo` e a ferramenta de hora usa o relógio do sistema (`timezone_source = "system"`). Não instalar `kokoro`, `torch`, `openwakeword` nem `PySide6` nesta fase (o Orb Desktop tem instalação própria, ver `apps/desktop/README.md`).

**PASS:** integridade 182/182, `CONFIG_OK`, freeze anexado com as versões acima. **STOP:** um pacote não instala com estas versões.

### G3 — Ollama e modelo autorizados
Requer autorização explícita para (a) instalar o Ollama e (b) descarregar os pesos.
1. Instalar o Ollama oficial (instalador por utilizador, sem administrador). Registar a versão: `ollama --version`.
2. `ollama pull qwen3.5:4b`.
3. `ollama show qwen3.5:4b --license > evidence\g3-license.txt`: confirmar a licença **antes** de qualquer uso. Fontes secundárias indicam Apache-2.0; não foi verificado numa fonte primária.
4. `ollama list > evidence\g3-models.txt`.
5. `.\.venv\Scripts\python -m jarvis --diagnose`: o item `llm` tem de dar `LLM_MODEL_OK`. Os outros itens podem continuar em FAIL nesta fase.

**PASS:** licença registada e compatível, modelo listado, `LLM_MODEL_OK`. **STOP:** licença incompatível, ou modelo não carrega.
**Nota:** o Jarvis nunca arranca o Ollama (`auto_start = false`); a aplicação do Ollama tem de estar a correr.

### G4 — Conversação real em modo texto (depende de G2, G3)
`.\.venv\Scripts\python -m jarvis --text`. Não usa microfone nem voz. Escrever os seis comandos:

| # | Comando | Esperado |
|---|---|---|
| 1 | que horas são | hora local correcta (Africa/Maputo) em PT |
| 2 | abre a calculadora | pedido de confirmação → `sim` → «Modo de simulação: não abri a Calculadora…» |
| 3 | abre o Bloco de Notas | confirmação → `não` → «Cancelei.» |
| 4 | estado do computador | CPU/RAM/uptime plausíveis em PT |
| 5 | explica novamente a última resposta | reformula a resposta anterior em PT |
| 6 | cancela essa operação | «Não há nada em curso para cancelar.» ou interrompe |

**PASS:**
- 6/6 com chamada de ferramenta correcta onde aplicável;
- nenhuma afirmação de abertura real;
- nenhuma resposta em inglês.

**STOP:** qualquer execução sem `sim`, ou resposta que afirme ter aberto uma aplicação.

### G5 — Modelo STT e microfone: instalação e verificação (sem reconhecimento)
1. Com autorização, descarregar o modelo `small` (multilingue, MIT) para a cache local:
   `.\.venv\Scripts\python -c "from huggingface_hub import snapshot_download; snapshot_download('Systran/faster-whisper-small', cache_dir='.wyzer/models')"`
   (Não se usa `wyzer.install_check --download-model` porque esse comando lê o `wyzer.toml`, que aponta para `small.en`.)
2. Registar o tamanho da pasta e a origem do modelo (`evidence\g5-model.txt`).
3. Se o G1 deu BLOCKER_VOICE no microfone: ligar ou activar um microfone (Definições → Privacidade → Microfone, para aplicações de ambiente de trabalho) e repetir o G1.
4. `--diagnose` → `stt_model` = `STT_MODEL_OK` e `microphone` = `MIC_OK`.

**PASS:** `STT_MODEL_OK` e `MIC_OK`. Não há testes de reconhecimento neste gate: passam para o G7.

### G6 — Voz portuguesa disponível (sem ciclo de voz)
1. `--diagnose` → `tts_voice` = `PT_VOICE_SELECTED` ou `PT_VOICE_CONFIGURED` (preferência pt-PT, depois pt-BR).
2. Se `PT_VOICE_MISSING`: instalar uma voz PT em Definições → Hora e idioma → Voz, **com autorização** (pode exigir administrador). Repetir o G1 e o `--diagnose`.
3. Se a voz aparecer só como OneCore (WARN no G1, `PT_VOICE_MISSING` no `--diagnose`): STOP da fase de voz e registo como bloqueador técnico de SAPI para decisão da RIGHTWARE.

**PASS:** `tts_voice` em PASS. A qualidade audível é avaliada no G7.

### G7 — Primeiro ciclo de voz real (depende de G3, G5 e G6)
**Pré-condição obrigatória:** `.\.venv\Scripts\python -m jarvis --diagnose` → `PREFLIGHT READY`. Se não estiver READY, não começar.
1. Criar `evidence\qa.toml` (cópia local de `configs\jarvis_slice.toml`). Só se a RIGHTWARE autorizar o registo de transcrições para avaliação: `log_transcript_text = true` (secção 2.2).
2. `.\.venv\Scripts\python -m jarvis --voice --config evidence\qa.toml`.
3. **Reconhecimento:** ler as 20 frases do corpus PT-MZ (secção 4), uma por activação (Enter).
4. **Voz:** ouvir pelo menos 5 respostas.
5. **Controlo:** `c` durante a escuta, o pensamento e a fala; `q` para terminar.

**PASS:**
- ≥ 18/20 frases com o sentido correcto;
- `sim`, `não` e `cancela` 100% correctos;
- voz PT audível e inteligível, sem cortes;
- `c` interrompe nas três fases;
- sequência de estados válida em `ui-events.jsonl`;
- `q` termina sem deixar processos (Gestor de Tarefas);
- nenhum `wyzer-whisper-*.wav` em `%TEMP%` no fim (secção 2.1).

**STOP:** qualquer execução sem `sim` válido, ou falha de captura não reportada.

### G8 — Seis comandos demonstrados por voz, aplicações simuladas
Os mesmos seis comandos do G4, por voz. Incluir:
- confirmação com `sim`, `não` e silêncio (timeout);
- uma frase ambígua durante a confirmação.

**PASS:**
- 6/6;
- nenhuma execução sem `sim` válido;
- `action_status = SIMULATED` em `voice-turns.jsonl`;
- 0 processos de Calculadora ou Bloco de Notas abertos.

### G9 — Benchmark de latência, CPU, RAM e GPU
- **Latências por fase:** `stt_ms`, `think_ms` e `tts_ms` de `voice-turns.jsonl`, com p50 e p95 sobre ≥ 20 turnos.
- **Recursos:** `ollama ps` (CPU/GPU e memória do modelo) e o pico de RAM do processo Python e do Ollama no Gestor de Tarefas.
- **Referência de aceitação para demonstração:** tempo de resposta (fim da fala → início da resposta) com p50 ≤ 4 s e p95 ≤ 8 s.
- **Modelo alternativo:** se a RAM for < 16 GB, ou se o p95 passar de 8 s, repetir G4/G8/G9 com `qwen3.5:2b`, numa cópia local da configuração. **Nunca** mudar o modelo por omissão no repositório sem decisão da RIGHTWARE.

| Critério | qwen3.5:4b | qwen3.5:2b |
|---|---|---|
| Comandos correctos (G4/G8) | medir | medir |
| Qualidade PT (1–5, avaliador humano) | medir | medir |
| Chamadas de ferramenta correctas | medir | medir |
| think_ms p50 / p95 | medir | medir |
| Memória do modelo (`ollama ps`) | medir | medir |

### G10 — Validação do plano de rollback (não apaga nada)
Objectivo: provar que o ambiente pode ser revertido, **sem** o reverter. O ambiente fica pronto para repetir a demonstração.
1. Arquivar as evidências: copiar `evidence\` para o local de arquivo acordado com a RIGHTWARE e registar o SHA-256 de cada ficheiro (`Get-FileHash`) em `evidence\g10-manifest.txt`.
2. Inventário do que uma reversão removeria, só com leitura:
   - `ollama list` (modelos);
   - tamanho de `.venv`, `.wyzer\models` e `.wyzer\vexel\logs`;
   - versão do Ollama instalada;
   - vozes instaladas durante o G6, se as houver.
3. Confirmar que tudo o que foi instalado está dentro de `C:\VEXEL-QA`, excepto o Ollama, os seus modelos em `%USERPROFILE%\.ollama` e eventuais vozes do Windows. Estas excepções ficam listadas explicitamente.
4. Escrever o procedimento R1 com os caminhos exactos encontrados neste PC.

**PASS:** evidências arquivadas com hash, inventário completo, R1 escrito com caminhos reais, nada removido.

### R1 — Remoção (opcional; só com autorização específica)
Executar **apenas** depois de: G10 PASS, evidências arquivadas, e uma autorização escrita da RIGHTWARE que diga *o quê* remover. Cada linha é independente; remover apenas o que for autorizado.
```powershell
ollama rm qwen3.5:4b                         # e/ou qwen3.5:2b
Remove-Item -Recurse C:\VEXEL-QA\jarvis\.venv
Remove-Item -Recurse C:\VEXEL-QA\jarvis\.wyzer\models
Remove-Item -Recurse C:\VEXEL-QA\jarvis\.wyzer\vexel\logs   # só depois de arquivar
# Desinstalação do Ollama / vozes: Definições → Aplicações / Voz (decisões separadas)
powershell -NoProfile -ExecutionPolicy Bypass -File .\qa\windows\Invoke-JarvisPreflight.ps1
```
**PASS:** o novo preflight confirma a remoção autorizada, e só essa.

## 2. Privacidade de áudio e de transcrições

### 2.1 WAV temporário do reconhecedor Wyzer
- **Quem cria:** `FasterWhisperRecognizer.listen()` (`wyzer/speech/whisper.py`), usado pelo Jarvis através do `PortugueseWhisperRecognizer`.
- **O quê:** um ficheiro `wyzer-whisper-<aleatório>.wav` (16 kHz, mono, 16 bits) com **a fala de uma activação**.
- **Onde:** a pasta temporária do utilizador (`%TEMP%`, via `tempfile.mkstemp`).
- **Ciclo de vida:**
  1. criado depois de a captura terminar;
  2. lido pelo Faster-Whisper;
  3. apagado num bloco `finally` (`path.unlink(missing_ok=True)`), mesmo que a transcrição falhe.

  Em funcionamento normal existe apenas durante a transcrição, normalmente menos de alguns segundos.
- **Pode ficar no disco se:** o processo for terminado à força (Gestor de Tarefas, falha de energia, crash do interpretador) durante a transcrição.
- **Verificação no fim do G7, G8 e G9:** `Get-ChildItem $env:TEMP -Filter 'wyzer-whisper-*.wav'` tem de estar vazio. Se houver ficheiros, registar a contagem (nunca o conteúdo) e pedir autorização para os remover.
- **Outros pontos:** a captura do Jarvis (`CancellableCapture`) mantém o áudio só em memória. A voz SAPI recebe o texto pelo stdin do PowerShell e não escreve ficheiros. Não existe gravação contínua: o microfone só é lido depois de Enter.

### 2.2 Registos locais
| Ficheiro | Conteúdo por omissão | Com `log_transcript_text = true` |
|---|---|---|
| `.wyzer\vexel\logs\voice-turns.jsonl` | resultado, decisão, estado da acção, tempos, nº de caracteres | **mais** o texto ouvido e a resposta |
| `.wyzer\vexel\logs\ui-events.jsonl` | estados, tempos, nº de caracteres | **mais** o texto associado aos eventos |
| `evidence\jarvis-preflight-*\` | inventário higienizado | — |

- `log_transcript_text = true` só numa cópia local (`evidence\qa.toml`), só com autorização, e nunca em commit.
- `.wyzer\` e `evidence\` estão no `.gitignore` do repositório; mesmo assim, não copiar estas pastas para outro local versionado.

### 2.3 Proibições
- Não publicar no GitHub (commits, issues, PRs, comentários, artefactos de CI) nenhum áudio, transcrição, excerto de `voice-turns.jsonl` com texto, nome de pessoa, nome de máquina, nome de utilizador ou identificador de dispositivo.
- Não gravar áudio com outras ferramentas durante os testes.

### 2.4 Antes de partilhar qualquer evidência
1. Rever o ficheiro à mão.
2. Confirmar que não contém texto de transcrição (excepto se a partilha da transcrição foi autorizada), nem nomes de pessoas, de utilizador ou de máquina, caminhos com o nome do utilizador, números de série, MAC ou IP.
3. Para logs com texto: partilhar só as métricas (`outcome`, `intended`, `metrics`), removendo `heard` e `reply`.
4. Registar quem reviu e quando.

## 3. Licenças a confirmar no G2/G3

| Componente | Licença (fonte) | Estado |
|---|---|---|
| Wyzer v0.3.1 | MIT (repositório, NOTICE) | confirmado |
| faster-whisper 1.2.1 | MIT | confirmar com `pip show` no G2 |
| CTranslate2 4.6.2 | MIT | confirmar no G2 |
| Modelo Whisper `small` (Systran/faster-whisper-small) | MIT (OpenAI Whisper) | confirmar no cartão do modelo no G5 |
| PyAV 16.0.1 (inclui FFmpeg) | BSD-3 (PyAV); FFmpeg LGPL nas wheels | confirmar no G2 antes de distribuir |
| onnxruntime 1.23.2 (VAD Silero) | MIT | confirmar no G2 |
| sounddevice 0.5.3 / PortAudio | MIT | confirmar no G2 |
| numpy 1.26.4 | BSD-3 | confirmado |
| huggingface-hub 0.36.2 | Apache-2.0 | confirmar no G2 |
| Ollama | MIT | confirmar no G3 |
| qwen3.5:4b / 2b | Apache-2.0 segundo fontes secundárias | **confirmar com `ollama show --license` no G3** |
| Vozes SAPI (Helia, Maria…) | parte do Windows; sem redistribuição | uso local apenas |
| openWakeWord `hey_jarvis` | CC BY-NC-SA 4.0 | **não usar** (`WAKE_WORD_BLOCKED`) |
| Kokoro + espeak-ng | Apache-2.0 + GPL-3.0-or-later | **não instalar na 01C** |

## 4. Corpus PT-MZ mínimo (G7/G8)

Ler cada frase com a voz natural do operador. Não gravar ficheiros; o Jarvis só transcreve (secção 2.1). Registar a transcrição obtida apenas se autorizado.

1. Que horas são?
2. Jarvis, que horas são agora?
3. Abre a calculadora.
4. Abre o Bloco de Notas, por favor.
5. Qual é o estado do computador?
6. Como está a memória do computador?
7. Explica novamente a última resposta.
8. Podes repetir isso de outra forma?
9. Cancela essa operação.
10. Pára.
11. Sim.
12. Sim, confirmo.
13. Não.
14. Não, obrigado.
15. Esquece.
16. Pode avançar.
17. Quanto tempo o computador está ligado?
18. Jarvis, abre a calculadora.
19. Olá Jarvis.
20. Obrigado, Jarvis.

## 5. O que esta preparação não prova

Os testes da 01C-PRE usam fakes para o microfone, o Whisper, as vozes, o Ollama e o lançador de aplicações. Provam o comportamento do código perante falhas e cancelamentos. Não provam a qualidade do reconhecimento, a voz, a latência nem o comportamento do modelo real: isso é o objectivo dos gates G4 e G7–G9. A validação sintáctica do script PowerShell no CI Windows (JAR-SLICE-01C-PUB) prova que o script é analisável pelo parser oficial, não que as sondas funcionam em todos os PCs.
