# RIGHTWARE — JAR-COG-01-R02 | Reteste com Qwen3.5 2B real

**Data de execução:** 2026-11-06 (Kaggle); **evidência:** output integral fornecido pelo operador.
**SHA testado:** §f595704393de65e679c33a29e7b57a8f8850ebb6§, §develop§.
**Ambiente:** Kaggle T4×2 (um T4 usado), Python 3.11.17, Ollama 0.40.15, §qwen3.5:2b§, CUDA, loopback, ferramentas de abertura simuladas, integridade Wyzer 182/182.
**Estado de engenharia R02:** CORRECÇÕES + CI PASS; **estado do modelo real: REVIEW, não aprovado**.
**Resultado do juiz:** §12/18 PASS§ (66,7%); §MODEL 4§, §PROVIDER 2§, §BACKEND 0§, §TEST_HARNESS 0§, §UNDETERMINED 0§. Este score é **não comparável** ao 29/32 do R01 (cenários e avaliador diferentes).

## 1. Observações do laboratório real

| Cenário | Observação | Leitura correcta |
|---|---|---|
| WARM-UP | §FAILED:LLMProviderError§ após 60.1s; §load_duration_ms=0§ | Falhou o aquecimento separado; não se conhece ainda a causa. O zero é ausência de medida válida, **não prova carga instantânea**. |
| ORION primeira apresentação | resposta fixa «O modelo local não está disponível neste momento»; §PROVIDER_TIMEOUT§ ~60.0s | FAIL provider; a apresentação não foi registada como conteúdo normal. |
| ORION título | PASS, mas §llm_ms=27459§, §llm_prompt_ms=22643§, §llm_prompt_tokens=4404§ e §control_named_window:DROPPED_BY_GATE§ | Gargalo inicial no processamento do prompt (neste turno); ferramenta indevida bloqueada. Resposta tem informação técnica lateral não solicitada. |
| ORION nome do projecto | resposta «O modelo local não está disponível neste momento»; ~331ms; camada PROVIDER pelo template | **Não concluir que houve timeout neste turno:** o juiz reconheceu o template, mas o output abreviado não inclui §detail§ nem causa técnica. Histórico não demonstra retenção de Orion, porque a apresentação inicial falhou. |
| ORION título do relatório | «Auditoria de Rede» correcto; PASS | Recuperação do título demonstrada. |
| SERA_DATE | não consultou hora; §get_local_time:DROPPED_BY_GATE§; respondeu «sou o Wyzer» | Segurança melhorou; **resposta pouco pertinente** a uma pergunta ambígua. PASS heurístico não é qualidade conversacional. |
| TIME | resposta §São 19h46 em Maputo.§; §get_local_time§ executada; juiz MODEL FAIL por §missing concepts=['hora']§ | **Falso FAIL do avaliador**: formato legítimo PT §19h46§ não coincide com alternativas §hora/horas/:§. Corrigir juiz; não mudar resposta do modelo por isso. |
| SYSTEM | §get_system_status§ executada; PASS | Dados da máquina **Kaggle**, não do futuro Windows de Issa. |
| REPORT_GREETING | saudação e oferta de ajuda; §get_local_time§ bloqueado; PASS | Melhoria concreta. |
| CAPITAL ×3 | 3x «Maputo»; ferramentas indevidas bloqueadas; PASS | Regressão B7 não reapareceu nos três turnos testados. |
| IDENTITY ×3 | §Sou Wyzer§/§Sou o Wyzer§; 3x MODEL FAIL | **Conflito de instrução no backend**: §wyzer/brain/prompt.py§ começa §You are Wyzer...§; §configs/jarvis_slice.toml§ especifica §assistant_name="Jarvis"§ e §PORTUGUESE_INSTRUCTION§ não corrige explicitamente a identidade. Não atribuir à capacidade do 2B isoladamente. |
| ACTION_MEMORY | pedido Calculadora → confirmação → SIMULATED → relato coerente da simulação; 3 PASS | Mecanismo de confirmação e verdade de operação comprovado com modelo real no cenário. |
| HONEST_REFUSAL | Paint recusado, com exemplos permitidos; PASS | Nenhuma abertura não autorizada. |

**Nota:** §BACKEND=0§ é apenas etiqueta do avaliador, **não valida** automaticamente o backend. Identidade Wyzer/Jarvis é uma falha de configuração/prompt VEXEL, embora tenha sido classificada MODEL pelo juiz.

## 2. Identidade — código confirmado

- §wyzer/brain/prompt.py§ contém §"You are Wyzer, a concise Windows assistant..."§ no sistema original; protegido, não editar §wyzer/**§.
- §configs/jarvis_slice.toml§ define §[personality] assistant_name = "Jarvis"§.
- §jarvis/brain/pt_provider.py::PORTUGUESE_INSTRUCTION§ exige português e uso de ferramentas, mas não impõe nome/identidade Jarvis nem desautoriza apresentar-se como Wyzer.
- Corrigir pela composição de instruções/identidade do **VEXEL**, preservando integridade Wyzer 182/182; provar com teste real §Quem és tu?§ e testes de regressão ao prefixo do prompt original.
- Em paralelo, considerar proposta prévia JAR-ARCH-02 para prompt simplificado: o upstream anuncia ferramentas não presentes no slice e inflaciona contextos. Essa refactorização tem âmbito distinto; evitar mistura indiscriminada.

## 3. Avaliador — falso FAIL

Em §qa/kaggle/semantic_judge.py§ a expectativa para §Que horas são em Maputo?§ requer uma das alternativas §"hora", "horas", "meia noite", "meio dia", ":"§. §São 19h46 em Maputo.§ é português válido, mas não tem essas cadeias; o juiz marcou §FAIL/MODEL§. Acrescentar regex de hora §\b\d{1,2}h\d{2}\b§ (e equivalentes justificados), com testes anti-falso positivo. Avaliar grounding com resultado de relógio: a ferramenta ter sido usada não prova exactidão temporal.

## 4. Startup / timeouts — leitura conservadora

- §warm_up()§ falhou ao fim do timeout de 60s. A primeira apresentação Orion também falhou ao fim de 60s.
- Primeira resposta completa posterior demorou ~27.5s; ~22.6s foram processamento de prompt de ~4404 tokens, não geração.
- Turnos subsequentes apresentam latências menores, tipicamente abaixo de 2s no log.
- Evidência **compatível com custo de cold start/cache/prompt inicial**, mas sem prova exclusiva de causa. Investigar o estado de Ollama, warm-up, §num_ctx§, custos de system prompt, GPU e timeout com logs sanitizados; não aumentar timeout indiscriminadamente.
- Retorno de §model_unavailable_template§ no turno de Orion em ~331ms é distinto do timeout de ~60s; usar §turns.jsonl§ para ler §detail§, §llm_failures§ e §tools_rejected§ antes de atribuir a causa.

## 5. Próxima missão (RECOMENDAÇÃO, ainda não executada)

**JAR-COG-01-R03 — Identity/Cold Start/Judge calibration**, escopo limitado:
1. Corrigir identidade Jarvis no wrapper VEXEL (sem tocar upstream), validar português e evitar «Wyzer».
2. Corrigir expectativa temporal PT com prova red→green no juiz e negativas.
3. Investigar warm-up duplo timeout, latência da avaliação do prompt, falso fallback rápido no ORION_RECALL; separar PROVIDER, MODEL e BACKEND com telemetria (sem texto privado).
4. Melhorar reteste Orion: warm-up bem sucedido antes da conversa, depois confirmar que apresentação + título são realmente registados na mesma sessão e recuperados; se warm-up falhar, classificar corrida como INVALID/WARMUP_FAILURE, não comparar qualidade cognitiva.
5. Alinhar teste de §sera?§ com resposta de clarificação, sem relógio, identidade enganadora ou inventar tempo.
6. Reteste **focalizado**, sem repetir os 18 cenários ou os 777 testes integrais desnecessariamente; após gates locais, CI no SHA final, Kaggle com modelo real.
7. Manter Wyzer 182/182, PR #2 Draft, §allow_real_windows_actions=false§, registos sem transcrições reais; não criar memória persistente nem Task Engine.

**Evidência temporária:** §/kaggle/working/JAR_COG_01_R02_EVIDENCE_20261106_174641.zip§ — não copiada para GitHub; preservar externamente antes de novo reset Kaggle. Os conteúdos reportados nos logs são métricas, mas rever antes de publicar.
