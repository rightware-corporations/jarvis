# RIGHTWARE — JAR-COG-01-R | Kaggle real cognitive QA, R01

- **Data de evidência:** 2026-11-06, `Africa/Maputo`.
- **Origem:** saída completa `RIGHTWARE / FULL KAGGLE RECOVERY` e `JAR-COG-01-R / REAL LLM QA` fornecida pela RIGHTWARE. Esta é uma **transcrição resumida do laboratório do operador**, não uma execução deste relatório em CI.
- **Missão:** retestar [JAR-COG-01](2026-11-06_JAR-COG-01-FINAL.md) com o Qwen3.5 2B real e corpus PT-MZ.
- **SHA testado:** `03a83bf29faccbaa762dc2b5d7fad96031e4b2c5`, `develop`.
- **Estado:** **`COG01_REAL_QA_REVIEW` — 29/32 (90,625%) pelo avaliador automático; confiança de qualidade conversacional menor porque vários PASS são semanticamente fracos.**
- **Não equivale a:** release, autonomia operacional, memória persistente, Windows voice G9 ou aceitação de diálogo contínuo.

## 1. Ambiente recuperado

A sessão Kaggle anterior perdeu `/kaggle/working` (Python, repo, Ollama/modelos). Uma única célula de bootstrap recuperou:
- GPU Tesla T4 x2, com modelo a usar 100% GPU (um T4);
- clone de `rightware-corporations/jarvis` e checkout da HEAD esperada;
- Python `3.11.17` em `/kaggle/working/.venv-jarvis` com `pydantic`, `psutil`, `tzdata` e `zstandard`;
- integridade Wyzer **182/182**, `SOURCE_INTEGRITY_PASS`;
- Ollama **0.40.15** do asset oficial v0.40.15 verificado por SHA256;
- `qwen3.5:2b` ID `0689d44085e0`, ~2,7GB no disco e ~2,5GB na GPU, contexto 8192;
- Ollama escutando somente `127.0.0.1:11434`, `OLLAMA_NO_CLOUD=1`, apps sempre simuladas;
- script `qa/kaggle/JAR-COG-01_retest_cell.py` real executado até produzir `summary.json` e `turns.jsonl` sem texto.

Caminho declarado do arquivo efémero: `/kaggle/working/JAR_COG_01_R_EVIDENCE_20261106_133901.zip`. **Não foi anexado ao GitHub nesta ronda; pode desaparecer ao reiniciar Kaggle.** Se ainda existir, guardar externamente após revisão de privacidade.

## 2. Números observados

| Métrica | Resultado |
|---|---:|
| Total de linhas avaliadas | 32 (13 cenários isolados + corpus sintético de 15 turnos, com controlos) |
| PASS automático | 29 |
| FAIL automático | 3 |
| `BACKEND` (segundo juiz actual) | 0 |
| `MODEL` (segundo juiz actual) | 1 |
| `INTERFACE` (segundo juiz actual) | 2 |
| `think_ms` p50 / p95 | 973,9 / 11.247,3 |
| `llm_ms` p50 / p95 | 959,4 / 11.244,0 |
| Duração da suite | ~162 segundos |
| Erros do provider | 2x `PROVIDER_TIMEOUT` |

**Advertência importante:** `BACKEND=0` é uma etiqueta do avaliador e não demonstra a ausência de defeitos de backend. A função `judge()` apenas verifica, para respostas `answer/no_action`: ausência de confirmação, ausência de lançamentos e presença de algumas palavras-chave. Muitas expectativas de `model_expectation` do corpus não são verificadas (mapeamento de `KEYWORDS` vazio); respostas inadequadas podem receber PASS.

## 3. Exemplos reais de saída, sem dados pessoais

| Entrada sintética | Saída observada (resumo) | Juízo |
|---|---|---|
| `Qual é a capital de Moçambique?` (primeira execução isolada) | `O modelo local não está disponível neste momento.` | **FAIL INTERFACE — timeout** |
| `Quem és tu?` (primeira execução isolada) | `O modelo local não está disponível neste momento.` | **FAIL INTERFACE — timeout** |
| `quem es tu jarvis` | `Sou o Jarvis...` | PASS |
| `sera?` | `Hoje é 15 de novembro de 2026, às 15:38.` | **PASS automático, mas resposta não pertinente e data inconsistente com o dia de teste (06/11/2026)** |
| `Abre a calculadora.` → `sim` | confirmação única → `SIMULATED` | PASS |
| `Abre Bloco de Notas` → `não` → `Qual é a capital...?` | recusou app, depois `A capital de Moçambique é Maputo.` | **PASS — regressão B7 resolvida no fluxo testado** |
| `Olá Jarvis. Estou a preparar um relatório sobre o projecto Orion.` | `Não tenho autorização para fazer isso.` | **PASS automático, mas resposta semanticamente errada** |
| `Qual é o nome do projecto?` (no mesmo corpus) | `Não tenho autorização para fazer isso.` | **FAIL MODEL pelo juiz; origem BACKEND/MODELO por apurar** |
| `Agora resume o que conversámos.` | Respondeu sobre Orion e Auditoria de Rede | PASS aparente |
| `Qual é a data de entrega do relatório?` | Não conhece a data | Boa limitação de conhecimento |
| `Que operação fizeste há pouco?` | Frase ambígua sobre impossibilidade de iniciar processo | **PASS automático, mas deve explicitar `SIMULATED`, sem alegar abertura real** |
| `Obrigado, Jarvis. Volta ao relatório: qual era o projecto?` | Resposta menciona Orion (saída truncada) | PASS parcial, sem exame integral |

**As linhas acima não são uma transcrição completa de 32 respostas**. O script mostra só 60 caracteres por resposta e os logs ficam sem texto. Não inferir o resto da resposta truncada.

## 4. Causa técnica adicional a investigar

Código consultado na HEAD:
- `jarvis/tools/allowlist.py::action_outcome_from_result` pode devolver `ActionOutcome(status=DENIED)` para uma **ferramenta desconhecida**, mesmo sem ser uma ferramenta com efeito permitida.
- `jarvis/core/voice_loop.py::_respond` usa `action_outcome_text(last.status, app)` para **qualquer** `outcomes`; se receber um `DENIED` sem app, emite a frase fixa **`Não tenho autorização para fazer isso.`**.
- `jarvis/brain/pt_provider.py::EffectGate` protege `open_allowed_application`, mas ferramentas desconhecidas não estão na lista `EFFECTFUL_TOOLS` e podem seguir para recusa no Orchestrator. Isto pode explicar um `DENIED` aparentemente desconexo com uma pergunta factual; **a ligação causal destes dois turnos ainda não foi demonstrada**.
- A resposta a `sera?` sugere o modelo usou indevidamente horário ou alucinou a data; **não comprovado qual**, sem registo sanitizado `tools_executed` e `action_status`.
- Os dois timeouts ocorreram com `request_timeout_seconds=60` do perfil temporário gerado pelo QA, salvo se outra configuração tiver sido substituída. Confirmar nos `metrics` antes de mexer em timeout.

## 5. Decisões e recomendações subsequentes

**Não marcar `JAR-COG-01-REAL-QA PASS`.** CI e testes determinísticos da implementação permanecem PASS, mas a QA cognitiva real fica REVIEW.

**P0/P1 recomendados para a próxima missão curta JAR-COG-01-R02:**
1. Diagnóstico **read-only** da saída sanitizada por índice de turno, `action_status`, `tools_executed`, `request_intent`, `claim_blocked`, `llm_failures`, `tools_blocked` e contexto; investigar as respostas `DENIED` sem acção solicitada.
2. Tornar o avaliador **semanticamente rigoroso**, com casos `expected denial`, `NO_ACTION`, respostas irrelevantes, alucinação de data, contexto lembrado e `SIMULATED`. Separar BACKEND / MODEL / PROVIDER / TEST_HARNESS e `UNDETERMINED` quando faltam provas.
3. Instrumentar e diagnosticar **unknown tool calls** sem persistir prompts, replies privados ou argumentos sensíveis; distinguir recusa legítima de ferramenta desconhecida e pedido do utilizador.
4. Melhorar a resposta a ferramentas desconhecidas ou rejeitadas, sem transformar perguntas gerais numa recusa de autorização irrelevante; **não afrouxar** o gate de efeitos nem alterar upstream.
5. Investigar **dois `PROVIDER_TIMEOUT`** separando carregamento, servidor, transporte e custo do prompt; repetir apenas cenários atingidos com modelo warm e timeout temporário controlado. Não esconder timeouts por aumentar o limite indefinidamente.
6. Manter `allow_real_windows_actions=false`, `log_transcript_text=false`, duas branches, PR Draft, 182/182 intactos.
7. Revalidar com Qwen2B real os cenários vulneráveis e corpus seleccionado, **sem refazer toda a suite por hábito**; documentar expectativa semântica, falso PASS e latência.

**Nova missão proposta:** `JAR-COG-01-R02 — Semantic QA and Conversation-Truth Hardening`, **NÃO aprovada/implementada nesta escrita**. Memória persistente, tarefas multi-etapa, Windows real e voz continuam fora do âmbito.

## 6. Fonte e continuidade

- Relatório de código: [JAR-COG-01-FINAL](2026-11-06_JAR-COG-01-FINAL.md)
- Handoff mestre: [Master Handoff V2](../26_MASTER_HANDOFF_2026-11-06.md)
- Corpus: [PT-MZ conversation](../../qa/corpus/pt_mz_conversation_v1.json)
- Célula: [Kaggle real retest](../../qa/kaggle/JAR-COG-01_retest_cell.py)
- Evidência textual no operador: `RIGHTWARE / FULL KAGGLE RECOVERY` e `JAR-COG-01-R / REAL LLM QA` (06/11/2026). **Não há ligação durável ao ZIP do Kaggle**.
- **Próxima execução:** ler `/kaggle/working/cog01/turns.jsonl` (se ainda existir) e responder às hipóteses com logs sanitizados. Se perdeu, preservar primeiro métricas noutro local e repetir apenas casos afectados depois da revisão do QA.

