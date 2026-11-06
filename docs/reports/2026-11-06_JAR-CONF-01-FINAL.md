# JAR-CONF-01 — repetição da confirmação e invocação duplicada de ferramenta

- **Data:** 06/11/2026
- **Modo:** TARGETED_FUNCTIONAL_SECURITY_FIX
- **Estado final:** `CONFIRMATION_REPLAY_FIXED` + `READY_FOR_REAL_LLM_RETEST`
- **Evidência:** testes com providers controlados (simulados) e um teste em loopback HTTP com o cliente Ollama real do Wyzer. A correcção ainda **não** foi validada com o `qwen3.5:2b` real: ver a secção 8.

## 1. Causa

**Confirmada por reprodução** (antes da correcção, com um provider controlado):

```
"Abre a calculadora" → CONFIRMATION_REQUESTED
"sim"                → CONFIRMATION_REQUESTED   (action_status=None)
estados: … awaiting_confirmation → listening → thinking → tool_running → awaiting_confirmation
lançamentos simulados: ['calculator']   (já executado uma vez)
um segundo "sim" executaria a mesma acção outra vez
```

**Sequência real**, lida em `wyzer/app/orchestrator.py`, que não foi alterado:
1. CONFIRMATION
2. YES → `_resume_confirmation`
3. `_execute_calls` executa a chamada aprovada **uma vez** (`SIMULATED`)
4. `_tool_loop` faz **uma nova chamada ao LLM**
5. o modelo pede **a mesma** `open_allowed_application`
6. como a ferramenta é `ConfirmationMode.ALWAYS`, o Orchestrator emite **uma segunda confirmação**

No `VoiceSession._respond`, havendo confirmação pendente, a resposta passava a ser a nova pergunta e o resultado `SIMULATED` já registado era ignorado. Isto bate com o que se observou na B5:
- `confirmation_requested → confirmation_requested`;
- um `tool_running` no segundo turno;
- nenhum `action_status=SIMULATED`.

O `tool_running` corresponde à primeira e única execução, e não prova sozinho que a acção terminou.

**Hipótese aberta (não verificada):** o `qwen3.5:2b` repete a chamada porque o resultado da ferramenta diz `opened=false` / «SIMULATED: no process was started» e o modelo lê isso como falha. Não se alterou o prompt (requisito 7). A correcção não depende do comportamento do modelo.

## 2. Fluxo antes e depois

| Passo | Antes | Depois |
|---|---|---|
| «sim» → execução aprovada | 1× `SIMULATED` | 1× `SIMULATED` |
| o modelo repete a mesma chamada (mesmo digest e mesma acção do Orchestrator, também mais tarde, por exemplo Calculadora → Bloco de Notas → Calculadora, ou numa continuação em lote) | 2.ª confirmação; o estado perde-se; um 2.º «sim» executaria outra vez | a repetição pendente é **descartada** com o «no» do próprio Wyzer: nunca é aprovada e a acção fica fechada. Fala-se o resultado registado: «Modo de simulação: não abri a Calculadora…»; `CONFIRMED` com `action_status=SIMULATED` e `metrics.repeat_call_dropped=1` |
| «sim» seguinte | executaria a repetição | `NOTHING_TO_CONFIRM` (nada a executar) |
| o modelo pede **outra** aplicação | 2.ª confirmação sem o resultado da 1.ª | confirmação própria, que nunca é aprovada automaticamente. A pergunta começa pelo resultado real da 1.ª: «Modo de simulação: não abri a Calculadora… Queres que eu abra o Bloco de Notas?»; `action_status=SIMULATED` |
| o modelo altera argumentos | — | a validação recusa a chamada (`DENIED`); é reportado o resultado da chamada confirmada, também no prefixo de uma pergunta seguinte |
| a repetição vem com chamadas de continuação | — | fail-closed: a repetição e a continuação são descartadas; nada é aprovado automaticamente |

## 3. Modificações

Só `jarvis/core/voice_loop.py` (+76/−4) e um ficheiro de testes novo.

- **`_Turn.confirmed`**: a `PendingConfirmation` aprovada neste turno (acção, step, ferramenta, argumentos).
- **`VoiceSession._executed`**: um registo pequeno, das últimas 16 acções do Orchestrator, com `action_id → {digests de chamadas confirmadas que correram}`.
- **`_record_executed`**: quando há um resultado com o `step_id` da chamada confirmada (a execução aconteceu de facto), regista `ConfirmationPolicy.digest(ferramenta, argumentos)` e devolve esse resultado.
- **`_already_executed(pending)`**: verdadeiro quando o digest da chamada pendente já correu na **mesma** acção.
- **Em `_respond`:**
  - numa repetição: `orchestrator.handle("no")` (o Wyzer limpa a confirmação e a continuação e fecha a acção; o «no» fica só localmente e não vai para o modelo), depois o caminho normal de resultado;
  - noutra chamada: `_present_confirmation(..., prior=resultado confirmado)`;
  - num turno confirmado: reporta-se sempre o resultado da chamada confirmada.
- **Inalterado:** o Wyzer (182/182), os prompts, a allowlist, o TTL, o digest, o anti-replay, o fail-closed e o lançador simulado.

## 4. Prova de execução única e de autorização correcta

| Teste | Prova |
|---|---|
| `test_b5_exact_repeat_after_execution_is_dropped_not_reconfirmed` | 1 lançamento; 1 `AWAITING_CONFIRMATION`; falado `[pergunta, resultado SIMULATED]`; o «sim» seguinte não faz nada |
| `test_b5_calculator_approve_over_http_with_wyzer_ollama_client` | o mesmo, por HTTP em loopback com o `OllamaChatProvider` real: 2 pedidos `/api/chat`, 1 lançamento |
| `test_repeated_twice_in_one_reply_still_runs_once` | duas chamadas iguais na mesma resposta → 1 lançamento |
| `test_repeat_after_failed_launch_does_not_loop` | a repetição depois de `FAILED` → 1 tentativa, `FAILED` reportado |
| `test_model_asks_for_another_application_needs_its_own_confirmation` | o Bloco de Notas não é aprovado automaticamente; precisa de «sim» próprio |
| `test_two_legitimate_requests_in_independent_turns_each_need_confirmation` | um pedido novo do utilizador nunca herda a autorização |
| `test_ping_pong_between_applications_never_runs_one_twice` | Calculadora → Bloco de Notas → Calculadora: 2 lançamentos, a 3.ª chamada é descartada |
| `test_batched_continuation_repeat_is_dropped` | `[Bloco de Notas, Calculadora]` em lote depois da Calculadora → a Calculadora não corre outra vez |
| `test_prefix_reports_the_confirmed_result_not_a_later_refusal` | o prefixo diz `SIMULATED`, não `DENIED` |
| `test_drop_closes_the_orchestrator_action` | sem acção activa nem confirmação; o pedido seguinte funciona; «yes»/«no» nunca chegam ao modelo |

**Mutações:**

| Mutação | Efeito nos testes |
|---|---|
| desligar o registo de execuções | 8 falham (incluindo o B5 por HTTP e o ping-pong) |
| desligar a escolha do resultado confirmado | 2 falham |

## 5. Testes novos e regressão

`tests_vexel/test_conf01_repeat_confirmation.py` tem 20 testes. Cobrem:
- aprovação única;
- repetição exacta;
- repetição dupla na mesma resposta;
- repetição depois de falha;
- outra aplicação, aprovada e recusada;
- argumentos alterados;
- negação e resposta ambígua;
- confirmação expirada;
- cancelamento;
- ausência de resultados;
- ferramenta só de leitura a seguir;
- dois pedidos independentes;
- ping-pong, continuação em lote e continuação descartada;
- prefixo honesto;
- estado do Orchestrator depois do descarte;
- B5 por HTTP.

| Gate | Resultado (Linux, Python 3.11, venv) |
|---|---|
| Integridade Wyzer | 182/182 |
| Compilação | 209 ficheiros, 0 erros |
| `tests_vexel` + `tests_lab` | **581 passed** (dois runs; 561 + 20) |
| `tests_desktop` (offscreen) | 87 passed |
| `--check-config` | `CONFIG_OK` |
| Regressão de segurança e HTTP (confirmação, TTS fail-closed, `ActionStatus`, sem Windows real, cancelamento, NET-01, ENGINE-01) | 277 passed |

## 5b. Revisão independente

Feita por um subagente, só de leitura, sobre o diff. **0 P0 e 0 P1.**

**Corrigidos:**
- **P2, ping-pong entre aplicações e continuação em lote:** a mesma chamada podia correr duas vezes na mesma acção. Agora há um registo por acção.
- **P2, prefixo `DENIED` quando a chamada confirmada tinha dado `SIMULATED`:** o resultado passa a ser escolhido pelo `step_id` confirmado.
- **P2/P3, estado do Orchestrator depois do descarte:** passou a usar o «no» do Wyzer, que fecha a acção.
- **P3:** o caso da execução ligada ao `step_id`, a nome da aplicação no prefixo e o estilo dos testes.

**Ficam documentados (P3, fail-closed):**
- a continuação descartada junto com a repetição;
- se a pergunta seguinte não for apresentada (TTS falha), o resultado da 1.ª chamada fica em `action_status` mas não é falado.

## 6. Integridade Wyzer

182/182. Nenhum ficheiro do manifesto foi tocado.

## 7. SHA e CI

| SHA | Conteúdo | CI |
|---|---|---|
| `a75e3a599e270b5964771adcbcd50dabcc4e6fc1` | correcção e 20 testes | **12/12 success**: push [42200013256](https://github.com/rightware-corporations/jarvis/actions/runs/42200013256), PR [42200012038](https://github.com/rightware-corporations/jarvis/actions/runs/42200012038). No `windows-latest`, `tests_vexel` 565 passed e `tests_lab` 16 passed |
| seguinte | este relatório, `01_CURRENT`, `03_BACKLOG`, índice | mesmo workflow |

Base: `d0b3fa5` (= `origin/develop`, árvore limpa, 182/182). O push foi normal, em fast-forward. O PR #2 continua em Draft e não foi tocado.

## 8. Reteste só do cenário CALCULATOR_APPROVE com o `qwen3.5:2b` real (Kaggle)

O Kaggle corre Linux. Este reteste prova o comportamento do modelo e do backend, não o Windows nem a latência do PC de QA.

1. **Código:**
   - `git clone` do repositório e `git checkout <SHA da JAR-CONF-01>`;
   - venv com Python 3.11 e `pip install 'pydantic>=2.8,<3' 'psutil>=6,<8'`.
2. **Ollama:** já a correr no notebook (`ollama serve`) com `qwen3.5:2b` presente. Registar:
   - `ollama --version`;
   - `ollama list` (digest do `qwen3.5:2b`).
3. **Configuração local** (não versionada): copiar `configs/jarvis_slice.toml` para `/kaggle/working/jarvis_2b.toml` e mudar só `model = "qwen3.5:2b"`. O endpoint tem de ser `http://127.0.0.1:11434`, porque `localhost` é recusado desde a JAR-NET-01.
4. **Verificar:** `python -m jarvis --check-config --config /kaggle/working/jarvis_2b.toml` deve dar `CONFIG_OK`.
5. **Executar só o cenário:**

   ```bash
   printf 'Jarvis, abre a calculadora\nsim\nsim\nsair\n' | WYZER_HOME=/kaggle/working/run_conf01 python -m jarvis --text --config /kaggle/working/jarvis_2b.toml
   ```

   Durante o turno, noutra célula: `ollama ps` (modelo carregado).

   O 3.º «sim» é intencional: tem de dar `nothing_to_confirm`.
6. **Evidência:**
   - `/kaggle/working/run_conf01/vexel/logs/text-turns.jsonl` e `text-ui-events.jsonl` (sem texto por omissão);
   - a saída `[resultado=…]` da consola;
   - `ollama ps`, `ollama list` e `ollama --version`.
7. **PASS** (todos):
   - turno 1: `confirmation_requested`;
   - turno 2: `confirmed` com `action_status=SIMULATED`, e `metrics.repeat_call_dropped=1` se o modelo voltou a repetir a chamada (o campo falta se não repetiu; ambos são PASS);
   - turno 3: `nothing_to_confirm`;
   - em `text-ui-events.jsonl`, exactamente **1** estado `awaiting_confirmation` e no máximo 1 `tool_running` no turno 2;
   - nenhum `detail=PROVIDER_*`.
8. **FAIL:**
   - um segundo `confirmation_requested` para a Calculadora;
   - turno 2 sem `action_status`;
   - qualquer execução no turno 3.

   Em caso de FAIL, arquivar os dois `jsonl` e reportar sem repetir.

## 9. Observações abertas (não bloqueantes)

- A repetição descartada fica no histórico da conversa do Orchestrator como uma tool call do assistente sem resultado. Não executa nada (o Wyzer não pode ser alterado), mas é preciso observar no reteste se o modelo reage a isso no turno seguinte.
- Um pedido legítimo de «abrir a mesma aplicação duas vezes» **no mesmo pedido** só corre uma vez (fail-closed). Um novo pedido do utilizador é uma acção nova e funciona.
