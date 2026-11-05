# 25 — JAR-SLICE-01C: Plano de execução no PC Windows de QA

**Estado:** preparado em JAR-SLICE-01C-PRE; **não executado**. Cada gate exige autorização explícita da RIGHTWARE antes de começar.
**Base de código:** `develop` no SHA aprovado para a 01C (registar o SHA exacto em cada relatório).
**Âmbito:** activação manual → microfone → Whisper PT → Wyzer → Ollama local → voz SAPI PT. Aplicações **sempre simuladas**; wake word **bloqueada** (`WAKE_WORD_BLOCKED`).

## 0. Regras de execução

- PC Windows de QA autorizado; nunca o PC pessoal do Issa sem autorização separada.
- Utilizador Windows normal (sem administrador). Pedir elevação só onde estiver escrito, e só com autorização.
- Tudo dentro de uma pasta de trabalho, `C:\VEXEL-QA\jarvis`, e de um venv local `.venv` (git-ignored). Não fazer `pip install` global.
- **Privacidade:**
  - gravações e transcrições ficam apenas no PC de QA, em `evidence\` ou `.wyzer\` (ambas git-ignored);
  - nunca enviar áudio para o repositório público;
  - `log_transcript_text = true` só numa cópia local da configuração (`evidence\qa.toml`), nunca em commit.
- Qualquer gate FAIL → STOP, relatório, nenhum passo seguinte.
- Evidência mínima por gate: comando executado, saída relevante, PASS/FAIL, data/hora, SHA do código.

## 1. Gates

### G1 — Inventário de hardware aprovado
1. Copiar o repositório (zip do SHA aprovado ou `git clone`) para `C:\VEXEL-QA\jarvis`.
2. `powershell -NoProfile -ExecutionPolicy Bypass -File .\qa\windows\Invoke-JarvisPreflight.ps1`. Opcional: `-CopySummary` para colar o resumo no relatório. O `Bypass` aplica-se apenas a este processo.
3. Anexar `evidence\jarvis-preflight-*\report.txt` e `report.json` (higienizados), depois de revistos à mão.

**PASS:**
- Windows 10/11 x64.
- RAM ≥ 16 GB (8–16 GB → WARN e plano com `qwen3.5:2b`; < 8 GB → FAIL).
- Disco livre ≥ 15 GB.
- ≥ 1 entrada de áudio activa.
- Indicação de pelo menos uma voz PT.

**STOP:** sem microfone activo, ou RAM < 8 GB.

### G2 — Instalação isolada e reversível de dependências
```powershell
cd C:\VEXEL-QA\jarvis
py -3.11 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -c installer\constraints-windows-py311.txt `
    pydantic psutil numpy sounddevice faster-whisper huggingface-hub
.\.venv\Scripts\python -m pip freeze > evidence\g2-freeze.txt
.\.venv\Scripts\python scripts\verify_import.py
.\.venv\Scripts\python -m jarvis --check-config
```
As versões são fixadas pelas constraints do próprio Wyzer: `pydantic==2.12.3`, `psutil==7.1.3`, `numpy==1.26.4`, `sounddevice==0.5.3`, `faster-whisper==1.2.1`, `ctranslate2==4.6.2`, `av==16.0.1`, `onnxruntime==1.23.2`, `huggingface-hub==0.36.2`. Não instalar `kokoro`, `torch`, `openwakeword` nem `PySide6` nesta fase.

**PASS:** integridade 182/182, `CONFIG_OK`, freeze anexado com as versões acima.

### G3 — Ollama e modelo autorizados
Requer autorização explícita para (a) instalar o Ollama e (b) descarregar os pesos.
1. Instalar o Ollama oficial (instalador por utilizador, sem administrador). Registar a versão: `ollama --version`.
2. `ollama pull qwen3.5:4b`.
3. `ollama show qwen3.5:4b --license > evidence\g3-license.txt`: confirmar a licença **antes** de qualquer uso. Fontes secundárias indicam Apache-2.0; não foi verificado numa fonte primária.
4. `ollama list > evidence\g3-models.txt`.
5. `.\.venv\Scripts\python -m jarvis --diagnose`: `llm` tem de dar `LLM_MODEL_OK`.

**PASS:** licença registada e compatível, modelo listado, `LLM_MODEL_OK`.
**Nota:** o Jarvis nunca arranca o Ollama (`auto_start = false`); a aplicação do Ollama tem de estar a correr.

### G4 — Conversação real em modo texto
`.\.venv\Scripts\python -m jarvis --text`. Escrever os seis comandos:

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

Registar respostas incorrectas do modelo (são o principal risco desta fase).

### G5 — Faster-Whisper com microfone
1. Descarregar o modelo `small` (multilingue, MIT) para a cache local, com autorização:
   `.\.venv\Scripts\python -c "from huggingface_hub import snapshot_download; snapshot_download('Systran/faster-whisper-small', cache_dir='.wyzer/models')"`
   (Não se usa `wyzer.install_check --download-model` porque esse comando lê o `wyzer.toml`, que aponta para `small.en`.)
2. `--diagnose` → `stt_model` = `STT_MODEL_OK`, `microphone` = `MIC_OK`.
3. Criar `evidence\qa.toml` (cópia local de `configs\jarvis_slice.toml` com `log_transcript_text = true`).
4. `python -m jarvis --voice --config evidence\qa.toml`. Ler 20 frases do corpus PT-MZ (secção 3), uma por activação.

**PASS:**
- ≥ 18/20 transcrições com o sentido correcto;
- 0 falhas de captura não reportadas;
- comandos de controlo (`sim`, `não`, `cancela`) 100% correctos.

### G6 — TTS português instalado e testado
1. `--diagnose` → `tts_voice` = `PT_VOICE_SELECTED` ou `PT_VOICE_CONFIGURED` (ordem de preferência: pt-PT, depois pt-BR).
2. Se `PT_VOICE_MISSING`: instalar uma voz PT em Definições → Hora e idioma → Voz, **com autorização** (pode exigir administrador). Repetir o diagnóstico. Se a voz aparecer só como OneCore (o preflight dá WARN), registar como bloqueador técnico de SAPI.
3. No modo de voz, ouvir 5 respostas.

**PASS:** voz PT audível e inteligível, sem cortes; `cancela` durante a fala pára o áudio.

### G7 — Ciclo completo com activação manual
`python -m jarvis --voice`. Enter → falar → resposta falada.

**PASS:**
- 10 ciclos sem erro;
- a sequência de estados em `ui-events.jsonl` é válida;
- `c` cancela durante a escuta, o pensamento e a fala;
- `q` termina sem deixar processos (verificar no Gestor de Tarefas).

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

### G10 — Rollback validado
```powershell
ollama rm qwen3.5:4b            # e qwen3.5:2b, se tiver sido instalado
# Desinstalar o Ollama em Definições → Aplicações (se a RIGHTWARE pedir remoção total)
Remove-Item -Recurse C:\VEXEL-QA\jarvis\.venv
Remove-Item -Recurse C:\VEXEL-QA\jarvis\.wyzer
# Guardar e depois apagar evidence\ conforme a política de retenção acordada
powershell -NoProfile -ExecutionPolicy Bypass -File .\qa\windows\Invoke-JarvisPreflight.ps1
```
**PASS:** o novo preflight mostra o modelo ausente e/ou o Ollama não instalado; não fica nenhuma alteração fora de `C:\VEXEL-QA` (excepto a desinstalação explícita do Ollama e de vozes, que são decisões separadas).

## 2. Licenças a confirmar no G2/G3

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

## 3. Corpus PT-MZ mínimo (G5/G8)

Ler cada frase com a voz natural do operador. Não gravar ficheiros, porque o Jarvis só transcreve. Registar a transcrição obtida.

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

## 4. O que esta preparação não prova

Os testes da 01C-PRE usam fakes para o microfone, o Whisper, as vozes, o Ollama e o lançador de aplicações. Provam o comportamento do código perante falhas e cancelamentos. Não provam a qualidade do reconhecimento, a voz, a latência nem o comportamento do modelo real: isso é o objectivo dos gates G4–G9.
