# JAR-ENGINE-01 — integração funcional do backend e preparação para inferência real

- **Data:** 05/11/2026
- **Modo:** AUTONOMOUS_ENGINEERING_MISSION (gated, fail-closed)
- **Estado final:** `ENGINE_INTEGRATION_PASS` + `REAL_INFERENCE_PENDING`
- **Classe de evidência:** `HTTP_CONTRACT_PASS`. Nenhum modelo foi executado: nada aqui é `REAL_INFERENCE_PASS`.

## 1. HEAD

| Momento | SHA |
|---|---|
| Inicial | `eff28c1ccf8b4083e736a544b594b4533dd27d38` (= `origin/develop`, árvore limpa, 182/182) |
| Código | `eea5bac9624e5985f35b5d6f73ab55bfdc2f3d12` |
| Final | commit deste relatório (só documentação), a seguir a `eea5bac` |

## 2. Arquitectura usada (ADR-0001, sem mudanças)

```
texto (--text) ─► normalização PT (jarvis/language/pt.py)
              ─► VoiceSession (jarvis/core/voice_loop.py)
              ─► Orchestrator Wyzer (wyzer/app/orchestrator.py, intacto)
              ─► PortugueseProvider + ProviderMeter (jarvis/brain/pt_provider.py)
              ─► OllamaChatProvider + UrllibJsonTransport (wyzer/brain/*, intactos)
              ─► HTTP 127.0.0.1 /api/chat · /api/tags
              ─► validação da resposta (Wyzer) + códigos fixos de falha (VEXEL)
              ─► allowlist de 3 + confirmação PT (digest, TTL, anti-replay)
              ─► ActionStatus + texto PT construído pelo VEXEL ─► TTS / consola
```

Não se criou outro cliente HTTP nem outro orquestrador. Os 182 ficheiros Wyzer não foram tocados (Q6 vazio).

## 3. Matriz de componentes

| Componente | Entrypoint | Entrada | Saída | Contrato de erro | Evidência |
|---|---|---|---|---|---|
| Entrada de texto | `python -m jarvis --text` → `jarvis.runtime.text_mode.run_text_mode` | linha da consola | `TurnResult` + `text-turns.jsonl` | IO → `TEXT_MODE_IO_ERROR` (exit 4); config → exit 2 | `test_text_mode_end_to_end_over_http…` |
| Normalização PT | `jarvis.language.pt.normalize/classify_control` | texto | `ControlIntent` | ambíguo → `NONE`; durante confirmação → cancela | `test_02`, `test_07_09`, casos F |
| Sessão | `VoiceSession.handle_text/voice_turn` | texto / transcrição | `TurnResult`, `UiEvent` | erro → `ERROR`→`IDLE`, confirmação limpa | 443 testes existentes + casos A–F |
| Orquestração | `Orchestrator.handle` (Wyzer) | texto ou `yes/no/stop` | `AssistantResponse` | excepção do provider → texto fixo PT | casos A–F por HTTP |
| Provider | `PortugueseProvider.chat` → `OllamaChatProvider._chat` | mensagens + 3 ferramentas | `ProviderChatResponse` | código fixo, frase «O modelo local não está disponível…» | cenários 2, 3, 5–7, 12 |
| HTTP | `UrllibJsonTransport.request` | JSON | `JsonResponse` | `HttpTransportError(status)` | servidor loopback |
| Autorização | `build_allowlist_registry` + `action_outcome_from_result` | tool call | `ActionStatus` | fora da allowlist ou argumentos inválidos → `DENIED` | cenário 11 |
| Confirmação | `_present_confirmation` / `_handle_while_pending` | `sim/não/cancela` | `CONFIRMED/REJECTED/…` | não apresentada ou ambígua → cancela | casos D, E, F |
| Eventos | `StateMachine` → `UiEventSink` | transições | `UiEvent` ordenados | sink falhado isolado | ordem verificada em B, D, E |
| Métricas | `ProviderMeter` + `TurnResult.metrics` | chamadas ao provider | `think_ms`, `llm_ms`, `llm_calls`, `llm_eval_count`, `llm_model_ms`, `llm_failures`, `llm_cancelled`, `llm_truncated`, `tts_ms` | metadados hostis ignorados; nunca quebra o turno | cenário 12 (hostil) |
| Cancelamento | `VoiceSession.cancel` → `Orchestrator.interrupt` | — | `DISCARDED` | resposta tardia descartada, sem confirmação armada | cenário 8 |

**Lacunas encontradas (e fechadas nesta ordem):**
1. Nenhum teste passava pelo provider HTTP real do Wyzer. Passou a haver um servidor loopback com 45 testes de contrato.
2. A falha do provider era indistinguível de uma resposta normal no registo. Passou a ter um código fixo em `detail`.
3. Não havia latência do LLM separada de `think_ms`. Passou a haver `llm_ms` e os contadores do Ollama.
4. O `--text` podia usar o lançador real (com a configuração activa, em Windows) e não registava turnos. Passou a ser sempre `SimulatedLauncher`, com `text-turns.jsonl` sanitizado.

## 4. Evidência HTTP (`HTTP_CONTRACT_PASS`)

**Servidor:** `tests_vexel/ollama_loopback.py`.
- `ThreadingHTTPServer` em `127.0.0.1:0`, só com threads (o guard de processos fica intacto).
- Respostas por script, só para os endpoints que o provider usa: `GET /api/tags`, `POST /api/chat` e `POST /api/generate`.
- As variáveis de proxy são removidas nos testes, e `NO_PROXY` é definido para loopback.

**Contrato observado no fio** (`test_04_09`):
- `POST /api/chat` com `model=qwen3.5:4b`, `stream=false` e `think=false`;
- `options={temperature:0.1, num_predict:256, num_ctx:8192}` e `keep_alive=30m`;
- exactamente 3 ferramentas (`get_local_time`, `get_system_status`, `open_allowed_application`);
- a mensagem de sistema inclui `VEXEL_LANGUAGE_POLICY`;
- UTF-8 intacto («Moçambique») e sem cabeçalho `Authorization`.

**Tamanho do pedido** (INSPECCIONADO, medido no servidor de teste):
- cerca de 11 300 caracteres por chamada, dos quais cerca de 10 000 são o prompt de sistema do Wyzer e cerca de 900 o JSON das ferramentas;
- um turno com ferramenta faz 2 chamadas;
- o prefixo do prompt de sistema mantém-se estável entre chamadas (cerca de 9 500 de 10 000 caracteres em comum), o que permite reutilizar a cache do Ollama.

| # | Cenário | Resultado esperado e verificado |
|---|---|---|
| 1 | Provider disponível | `diagnose()` → `available`, modelo encontrado; `LLM_READY` |
| 2 | Provider indisponível (porta fechada) | `LLM_UNREACHABLE`; frase fixa; `detail=PROVIDER_UNREACHABLE`; sem IP no texto |
| 3 | Modelo não encontrado | `LLM_MODEL_MISSING`; HTTP 404 → `PROVIDER_HTTP_404`; o «try pulling» do servidor nunca chega ao utilizador |
| 4 | Resposta válida | texto falado igual; `llm_calls=1`, `llm_eval_count=12`, `llm_model_ms=1500`, `llm_ms ≤ think_ms` |
| 5 | Malformada (não JSON, array, sem `message`, `tool_calls` não lista, JSON truncado) | `PROVIDER_INVALID_RESPONSE`; nada executado; sem confirmação |
| 6 | Timeout (0,3 s) | `PROVIDER_TIMEOUT` em < 2,5 s; a resposta tardia não é falada |
| 7 | Erro de rede (ligação cortada) | `PROVIDER_UNREACHABLE` |
| 8 | Cancelamento com pedido em curso | `DISCARDED`; a tool call tardia (abrir Calculadora) não arma confirmação; `llm_cancelled=1`; o turno seguinte funciona |
| 9 | Resposta em português | UTF-8 nos dois sentidos |
| 10 | Tool call válido | resultado da ferramenta devolvido ao modelo por HTTP (`role=tool`, `14:30`, `Africa/Maputo`) |
| 11 | Tool call não autorizado (ferramenta desconhecida, app `cmd`, argumento extra, JSON inválido) | `DENIED`; «Não tenho autorização para fazer isso.»; nada lançado |
| 12 | Informação inesperada | conteúdo não-string → texto; campos desconhecidos ignorados; tool calls lixo ignoradas; afirmação falsa «abri» → bloqueada; `done_reason=length` → `llm_truncated`; metadados hostis (números enormes, `Infinity`, booleanos, negativos) ignorados; 500 de parsing Qwen → uma única repetição conservadora; 500 repetido → falha fixa |

## 5. Casos end-to-end (tudo simulado)

| Caso | Pedido | Resultado |
|---|---|---|
| A | «Jarvis, qual é a capital de Moçambique?» | `ANSWERED`, resposta PT falada |
| B | «Jarvis, que horas são em Maputo?» | `get_local_time` → 2.ª chamada com o resultado → resposta. Estados `LISTENING→THINKING→TOOL_RUNNING→SPEAKING→IDLE` |
| C | «Como está o computador?» | `get_system_status` com sonda de teste (CPU 12,5 %) |
| D | «Abre a calculadora» → «sim» | pergunta PT falada; nada antes do «sim»; `SIMULATED`; texto «Modo de simulação: não abri a Calculadora…»; a afirmação falsa do modelo «Abri…» não é repetida; um segundo «sim» não faz nada nem chama o modelo |
| E | «Abre o bloco de notas» → «sim» | idem, com o Bloco de Notas |
| F | «não», «cancela», «talvez amanhã»; «sim» sem nada pendente | `REJECTED`/`CANCELLED_UNCLEAR`/`NOTHING_TO_CONFIRM`; nada lançado; a recusa nunca é enviada ao modelo |

**Latências por componente:**
- os testes medem `think_ms`, `llm_ms` e `tts_ms` em cada turno;
- em loopback com respostas por script, são da ordem dos milissegundos. **Não** são latência de inferência e não servem de base para dimensionar o hardware.

## 6. Resultados Python e CI

| Gate | Ambiente | Resultado |
|---|---|---|
| Q1 integridade | Linux cloud, Python 3.11 (venv) | 182/182 |
| Q2 compilação | idem | 206 ficheiros, 0 erros |
| Q3 `tests_vexel` + `tests_lab` | idem; pydantic 2.14.3, pytest 8.4.2, psutil 7.2.2, fastapi 0.162.0, httpx 0.28.1, uvicorn 0.54.0 | **507 passed** (baseline 459; 45 contratos novos e 3 parametrizações automáticas do novo módulo) |
| Q4 `tests_desktop` | idem + PySide6-Essentials 6.6.1, offscreen | 87 passed |
| Q5 `--check-config` | idem | `CONFIG_OK` |
| Q6 manifesto | `git diff origin/develop` | intersecção vazia |
| Q7 segredos | idem | sem ocorrências |
| Q8 branches | — | só `main` e `develop` |
| Mutação | `_bounded` desactivado | o teste dos metadados hostis falha (2), como esperado |

Incompatibilidade cloud: o container não tinha `libEGL`. Foram instaladas as mesmas bibliotecas de sistema que o job `desktop-orb` instala (`libegl1`, `libgl1`, `libxkbcommon0`, `libfontconfig1`, `libdbus-1-3`).

CI de `eea5bac`: ver a secção 13.

## 7. Problemas encontrados e corrigidos

| Sev. | Problema | Correcção |
|---|---|---|
| P2 | Metadados do provider (números enormes ou `Infinity`) podiam rebentar a medição fora do bloco sanitizado: o utilizador ouvia texto interno em inglês ou o turno terminava com uma excepção | `_bounded()` aceita só números finitos e limitados; `_safe_record` e um `_record_llm` que nunca lança; a confirmação é limpa antes das métricas; testes de regressão |
| P2 | `latency_summary` podia dar PASS do G9 com registos do modo texto | registos com `mode=text` → `NOT_APPLICABLE`, nunca PASS |
| P3 | O teste de cancelamento podia ficar pendurado para sempre | prazo de 5 s com mensagem |
| P3 | Recusa lenta da ligação em Windows | timeout de 10 s no teste 2 |
| P3 | Faltava o prompt «Tu: »; erro de IO no `--text` dava traceback | `PromptConsole`; `TEXT_MODE_IO_ERROR` (exit 4) |
| P3 | Defesa em profundidade | «The local model could not respond…» do Orchestrator traduzido para a frase fixa PT |

## 8. Revisão independente

Feita por um subagente, só de leitura, sobre o diff, nas áreas pedidas. **0 P0 e 0 P1.** Os 2 P2 e 4 P3 da secção 7 foram corrigidos.

Ficam abertos:
- **P3 (proxy do sistema):** o `urllib` do Wyzer respeita `HTTP(S)_PROXY` e, em Windows, o proxy do registo. Esse proxy não exclui `127.0.0.1`, por isso os prompts podiam passar por um proxy configurado no PC.
  - Mitigação no procedimento (secção 16): confirmar que não há proxy, ou definir `NO_PROXY=127.0.0.1,localhost`.
  - Uma correcção no runtime fica para decisão RIGHTWARE.
- **P3 (thread HTTP após cancelamento):** a thread do pedido abandonado continua até ao timeout, e o Ollama continua a gerar. O `llm_ms` do turno seguinte pode incluir essa espera.
- **P3 (01D):** a 01D precisará de um entrypoint próprio para o lançador real, e o teste `test_text_mode_module_has_no_real_launcher` mudará nessa ordem.
- **`REVIEW_REQUIRED`:** os testes usam um servidor HTTP em loopback. Não há rede externa, mas é um socket real; `testing.md` diz «sem rede». É preciso que a RIGHTWARE confirme que loopback é aceitável.

## 9. Análise de hardware

O resumo sanitizado do PC do utilizador final foi analisado e entregue **apenas no chat** à RIGHTWARE (`CLAUDE.md` §8: dados do PC do Issa não entram no repositório). Aqui ficam só os requisitos genéricos.

## 10. Matriz de compatibilidade de modelos (requisitos genéricos)

Os tamanhos são **ANUNCIADOS** (biblioteca Ollama, via fontes secundárias; não verificados). O desempenho é uma **hipótese** até ao G9.

| Modelo | Download | RAM indicativa (modelo + KV 8k) | Papel | Risco principal |
|---|---|---|---|---|
| `qwen3.5:4b` (oficial em `configs/`) | ~3,4 GB | ~5–6 GB | qualidade de tool calling e PT | latência em CPUs de 2 núcleos |
| `qwen3.5:2b` (q8_0 por omissão; `2b-q4_K_M` ~1,9 GB) | ~2,7 GB | ~3,5–4,5 GB | compromisso | qualidade de tool calling por medir |
| `qwen3.5:0.8b` | ~1,0 GB | ~2 GB | mínimo | erros de ferramenta e de PT; obriga a mais validação |

**Requisitos mínimos propostos (a confirmar com G3/G9):**

| Item | Requisito |
|---|---|
| Sistema operativo | **Windows 10 22H2 ou posterior** (requisito oficial do Ollama para Windows) |
| CPU | x86-64 com AVX2; 4 núcleos físicos recomendados |
| RAM | ≥ 8 GB livres para o 4b com Whisper `small`; 12–16 GB no total |
| Disco | ≥ 10 GB livres; SSD recomendado (carregamento a frio a partir de HDD é lento; `keep_alive=30m` mitiga) |

**Limites a medir no G9:**
- `think_ms + tts_ms`: p50 ≤ 4 s e p95 ≤ 8 s, com pelo menos 20 turnos (já em `latency_summary`);
- novos: `llm_ms` por chamada e `llm_eval_count`/`llm_model_ms`, para tokens por segundo;
- primeira chamada a frio, à parte;
- qualidade: tool call correcto nos casos B–E em pelo menos 19 de 20 frases do corpus, com 0 afirmações falsas e PT correcto.

**Alternativa de arquitectura (sem decisão):** inferência privada noutro computador autorizado da rede local.
- Exige mudar a regra «endpoint loopback» de `jarvis/config.py` e um novo ADR.
- Tem implicações de privacidade (os prompts saem do PC) e de disponibilidade.

## 11. Dependências e licenças

Não há dependências novas no runtime. Os testes usam só a stdlib (`http.server`, `threading`). O venv local seguiu as gamas do workflow (secção 6). Ollama e Qwen não foram instalados.

## 12. Limitações reais da cloud

| Item | Estado |
|---|---|
| Push para `develop` | **Verificado**: fast-forward aceite (`eff28c1..eea5bac`) |
| Branches temporários | não exigidos; sessão configurada com `develop` |
| `gh` | REST e `gh run` funcionam; GraphQL dá 403 |
| Rede da shell | só allowlist (`pypi.org` acessível; `registry.ollama.ai` e `huggingface.co` não) |
| Modelos, áudio, Windows | indisponíveis por política e por ambiente |
| Bibliotecas Qt | `libEGL` em falta; instaladas como no CI |

## 13. Commits e GitHub Actions

| SHA | Conteúdo | CI |
|---|---|---|
| `eea5bac` | código e testes JAR-ENGINE-01 | push [42088773796](https://github.com/rightware-corporations/jarvis/actions/runs/42088773796) · PR [42088782805](https://github.com/rightware-corporations/jarvis/actions/runs/42088782805) — **12/12 success** no SHA exacto `eea5bac`. O `windows-python` mostra `tests_vexel` 491 passed e `tests_lab` 16 passed no `windows-latest`; no `headless-contract` a contagem fica escondida pelo `-q` duplo (D06) |
| seguinte | este relatório, `01_CURRENT`, `03_BACKLOG`, índice | segue no mesmo workflow |

## 14. PR #2

Mantém-se `open`, `draft: true` e `merged: false`, com head = `develop`. Não foi tocado.

## 15. Bloqueadores da inferência real

1. Não há PC de QA autorizado com Ollama. A instalação é manual, feita por uma pessoa (G3).
2. Requisito do Ollama: Windows 10 22H2 ou posterior. É preciso confirmar a versão do PC de QA e do PC-alvo.
3. Modelo oficial `qwen3.5:4b` por validar quanto a latência em CPUs de 2 núcleos. A mudança de modelo é uma decisão RIGHTWARE e exige um ADR (G9).
4. Licença do modelo por confirmar no G3.
5. Proxy do sistema (secção 8).

## 16. Procedimento recomendado para a primeira inferência real (não executado)

Só no PC de QA autorizado, por uma pessoa, segundo o plano 25. Nada no PC do Issa.

1. **Base:**
   - Windows 10 22H2 ou posterior; Python 3.11; `git checkout` de `develop` no SHA indicado;
   - venv com as dependências do workflow.
2. **Configuração:**
   - `python -m jarvis --check-config` → `CONFIG_OK` e `allow_real_windows_actions=false`.
3. **Ollama (G3, com autorização):**
   - instalar manualmente;
   - `ollama pull <modelo escolhido pela RIGHTWARE>`;
   - registar a versão do Ollama e o digest do modelo (`ollama list`).
4. **Proxy:**
   - confirmar que não há proxy de sistema;
   - ou, na consola, `set NO_PROXY=127.0.0.1,localhost`.
5. **Diagnóstico:** `python -m jarvis --diagnose`. A linha do LLM deve estar OK; microfone e voz podem faltar nesta fase.
6. **Inferência por texto:** `python -m jarvis --text`.
   - A primeira linha deve ser `LLM ollama <modelo>: LLM_READY`.
   - Escrever os casos A–F, com as frases do corpus `qa/corpus/pt_mz_v1.txt`.
   - Cada turno imprime `[resultado=… llm_ms=… llm_calls=… llm_eval_count=…]`.
7. **Métricas:** `python qa/benchmarks/latency_summary.py .wyzer/vexel/logs/text-turns.jsonl`.
   - Mostra `llm_ms` e `think_ms`.
   - O G9 dá `NOT_APPLICABLE`: é medido depois, em `--voice`.
8. **Critério de `REAL_INFERENCE_PASS`:**
   - em pelo menos 1 turno, `llm_eval_count > 0` produzido pelo modelo real;
   - respostas em PT;
   - B/C com a ferramenta certa e D/E com pedido de confirmação e `SIMULATED`;
   - 0 `PROVIDER_*` inesperados e 0 afirmações falsas.
   - A evidência é sanitizada: os `jsonl` sem texto e um resumo técnico. Sem transcrições nem identificadores.
9. **Rollback:** conforme o G10 do plano 25 (sem remoção automática; R1 exige autorização).

## 17. Estado final

**`ENGINE_INTEGRATION_PASS` + `REAL_INFERENCE_PENDING`.**

O percurso funcional foi demonstrado com o provider HTTP real do Wyzer contra o servidor loopback. As políticas de ferramentas e de confirmação mantêm-se e o tratamento de falhas foi comprovado. O código está publicado em `develop`, com integridade 182/182.

Isto **não** é demonstração de IA real. O estado do CI está na secção 13.
