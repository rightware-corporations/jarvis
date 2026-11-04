# VEXEL Jarvis — Playbook de execução, handoffs e critérios PASS/FAIL

**Data-base:** 2026-11-04 (Africa/Maputo). **Finalidade:** trabalho organizado entre RIGHTWARE, ChatGPT, Claude e Manus, sem perder a continuidade quando uma conversa falhar.
**Leitura obrigatória:** [21 — Master handoff](21_MASTER_HANDOFF_2026-11-04.md), [22 — Decisions](22_DECISION_REGISTER_2026-11-04.md), [01_CURRENT](01_CURRENT.md), [04_ACCEPTANCE](04_ACCEPTANCE.md).

## 0. Regras imutáveis do fluxo de trabalho

- **RIGHTWARE é a autoridade final do produto.** Claude não transforma hipótese em decisão; ChatGPT não assume aprovação em nome da RIGHTWARE. Manus só faz inspeção visual dentro do âmbito recebido.
- **Apenas `main` e `develop`.** Sem branch extra, worktree/fork experimental, force push, alteração de histórico, merge/release sem aprovação.
- **`wyzer/` e demais 182 ficheiros do manifesto são imutáveis até JAR-ARCH-02.** Nada de actualizar hashes para disfarçar uma alteração.
- Backend do produto continua **Python 3.11 + Wyzer + Ollama/local-first**; sem dependência de Claude/ChatGPT/ElevenLabs/Anthropic API em produção. Uma API com formato “OpenAI-compatible” **não implica** consumir OpenAI paga.
- **Sem acções OS reais no Web Lab.** Ferramentas desktop requerem broker e política de autorização; servidor HTTP não tem licença para controlar Windows só por estar no browser.
- Não correr código de outros projectos, instalar dependências, transferir modelos, fazer deploy ou QA em PC pessoal/Issa sem o âmbito específico da tarefa aprovado.
- Testes simulados ≠ IA real; vídeo/README ≠ execução de código; POC ≠ produto aprovado.
- Public repo: não publicar segredos, gravações de voz, perfis pessoais, imagens de utilizadores, binários de modelo sem licença nem artefactos de sessão privada.
- Cada tarefa produz **SHA de base, diffs, testes e logs exactos, estados INSPECCIONADO/TESTADO/IMPLEMENTADO/REVIEW/APROVADO, limites e próxima dependência**.

## 1. Ponto de situação e quem está encarregado

| Workstream | Proprietário funcional | Resultado já existente | Próxima acção |
| --- | --- | --- | --- |
| Produto/decisões | RIGHTWARE | Objectivo, repo, Py/Wyzer, 2 branches e independência de IA paga definidos | Aprovar revisão de `CLAUDE.md`, plugin v0.1.1, e autorização M0 |
| Arquitectura/auditoria | ChatGPT | Docs 10–13, 19, 20–23; comparações estáticas/risco | Rever relatório Manus e alterações Claude; verificar GitHub antes de dizer PASS |
| Engenharia Claude | Claude (Claude Desktop + plugin RIGHTWARE) | Auditoria skills JAR-DEV-SKILLS-02; `CLAUDE.md` original; resumo JAR-HUD-01; 9 skills v0.1.0 instaladas | Preparar v0.1.1 com `allowed-tools` reduzidos; conciliar V2 e definir M0. **Aguardar resultado, não presumir** |
| Preview visual | Manus | Recebeu prompt para examinar `adewaskar/jarvis` front-only | Produzir screenshots **reais** do Chromium, evidência de Vite, consola, limitações e mocks claramente identificados |
| Build/QA runtime | Pendente | CI headless mocks PASS no passado; sem QA Windows ou voz real | Só após gate M0 e arquitectura de segurança |

## 2. Fase imediata — sem refactor ou implantação

### JAR-HANDOFF-00 — Continuidade (esta ronda)
- [x] Preservar o handoff pré-Wyzer como **arquivo obsoleto**.
- [x] Preservar auditoria de skills, relatório de validação e dois drafts `CLAUDE.md` como **referências**, não políticas aprovadas.
- [x] Criar registo de decisões e playbook.
- [ ] Confirmar publicação de todos os docs em `develop`, actualizar índice e `CURRENT`, verificar CI e informar SHA final.
**PASS:** links GitHub acessíveis, apenas documentos alterados, `main` e os 182 hashes intocados, workflows pós-commit concluídos com êxito.

### JAR-CLAUDE-01 — Plugin RIGHTWARE v0.1.1
- [x] Instalação **visual** v0.1.0 do plugin `rightware-jarvis-dev` com **9 skills** confirmada nas capturas de ecrã; não é QA profundo de cada skill.
- [ ] Claude preparar v0.1.1 do pacote com revisão de `pyside6-desktop/SKILL.md`: permitir **Read, Grep e Glob** apenas; eliminar pré-autorização de Edit/Write/Bash em `allowed-tools`.
- [ ] Conferir que nenhum outro plugin activo concede permissões excessivas em hooks/servidores; confirmar limites de permissões globais do Claude.
- [ ] Claude entregar ZIP + hash + manifest + teste de formato + lista de alterações + rollback; **não** instalar pelo utilizador sem rever.
- [ ] RIGHTWARE efectuar upload em **Customize → Plugins** (NÃO Upload a skill; esse aceita um único SKILL.md); reiniciar sessão e confirmar as 9 skills.
**PASS:** v0.1.1 visível na conta, sem duplicação, skills activáveis, sem hooks, permissões inspectáveis. **Nota:** skills não eliminam por si só o risco de comandos quando o agente tem outras ferramentas/permissões.
**Material:** [Auditoria JAR-DEV-SKILLS-02](reference/CLAUDE_SKILLS_AUDIT_2026-11-04.md) · [Validação v0.1.0](reference/CLAUDE_PLUGIN_VALIDATION_V010_2026-11-04.md) · [Plano 19](19_CLAUDE_SKILLS_TOOLCHAIN_PLAN.md).

### JAR-ARCH-02 — Politica de integração Wyzer e `CLAUDE.md`
- [x] Draft original [arquivado](reference/CLAUDE_ORIGINAL_DRAFT_2026-11-04.md) e [V2](reference/CLAUDE_REVIEW_V2_DRAFT_2026-11-04.md) preparados (nenhum publicado em `/CLAUDE.md`).
- [ ] Claude apresentar diff textual original → V2 e identificar regras incompatíveis.
- [ ] ChatGPT revisar Python 3.11, `pip` + constraints, gestão de alterações a `pyproject.toml`/`wyzer.toml`, fronteiras de QWebChannel, licenças e segurança.
- [ ] RIGHTWARE aprovar texto final.
- [ ] Só após aprovação: criar `CLAUDE.md` na raiz da `develop` com commit identificado e CI PASS.
- [ ] Definir `JAR-ARCH-02`: política de upstream/patcheamento verificável sem adulterar manifesto; se a estratégia for patch set, rastrear hashes originais e diffs; se snapshot, manter baseline imutável.
**PASS:** regra clara e verificável para permitir alterar a evolução sem modificar/manipular os hashes 182/182; autoridade RIGHTWARE explícita.

### JAR-HUD-00 — Preview real com Manus (prioridade visível)
- [ ] Manus confirmar SHA exacto da fonte `adewaskar/jarvis@1c4016afdf86f7043efc6882ceffef84ad0d8783`.
- [ ] Auditar scripts `package.json`/lockfile e dependências antes de executar, incluindo scripts automáticos de instalação.
- [ ] Clonar somente no ambiente de QA isolado; **não** dentro de `rightware-corporations/jarvis`.
- [ ] Se autorizado para esta tarefa, instalar apenas dependências estritamente necessárias e iniciar **frontend Vite** em `127.0.0.1`. **Não** iniciar `npm start`, `npm run bridge`, `bridge/server.mjs`, Claude Agent SDK, plugins MCP ou outros serviços externos.
- [ ] Capturar no **Chromium real** screenshots PNG: boot/inicialização, idle/reactor, listening, thinking, speaking, painel/expanded, viewport compacta. Identificar claramente o que é interface real, o que é estado simulado e o que não foi possível mostrar.
- [ ] Recolher evidência do Chromium/Playwright, consola, WebGL, tempos de carregamento, responsividade, fonte/ícones, ausência de permissões de mic/camera e estado da porta localhost.
- [ ] Entregar **galeria HTML**, imagens individuais e relatório PASS/FAIL. Não substituir imagens reais por geradas em IA.
- [ ] RIGHTWARE + ChatGPT fazer revisão visual e marcar **MANTER / ADAPTAR / REMOVER** por componente.
**PASS:** imagens verificáveis do código original, sem Claude/ElevenLabs/voz cloud, com falhas e limitações explícitas. Se o ecrã não aparecer, reportar FAIL com consola e **não inventar preview**.

## 3. JAR-HUD-01 / JAR-UX-03 M0 — POC desktop após preview

**Status:** plano técnico autorizado para especificação; **execução M0 exige aprovação RIGHTWARE e máquina Windows de QA**.
- [ ] Receber relatório **integral** JAR-HUD-01 Claude (o artefacto [JAR-HUD-01](https://claude.ai/artifact/VEVVzCMeXw5As159GVA4XK) não está arquivado no repo neste handoff; só resumo foi transcrito).
- [ ] Matriz de ficheiros: `src/scene/Core.tsx`, `Scene.tsx`, `Particles.tsx`, `Orbits.tsx`; `src/ui/{Hud,Panels,Blades,Effects,...}.tsx`; `src/lib/brain.ts`, `anthropic.ts` e bridge **excluídos**.
- [ ] Revisão de direitos de terceiros: MIT do app, dependências, fontes, efeitos, áudio, nomes/marcas Iron Man/J.A.R.V.I.S., distribuição e notices. Não copiar assets do Marvel.
- [ ] Prototipar sem ferramentas Windows reais: PySide6 sem moldura/arrastável/always-on-top **opcional**, QWebEngine com WebGL e transparência, React/Three.js como recurso visual, QWebChannel com esquema de eventos limitado.
- [ ] Testes Windows: transparência com DWM, DPI, vários monitores, Alt-Tab/foco, click-through opcional, minimização/retoma, abertura/fecho sem fuga de recursos, comportamento com GPU fraca e fallback nativo.
- [ ] Medir FPS, CPU, RAM, GPU, consumo idle, stutter, crash, carregamento, estado de áudio simulado e responsividade; RIGHTWARE fixa limites de aceitação antes da avaliação final.
- [ ] Comparar **QPainter / Qt Quick** como alternativa ao WebEngine caso latência/consumo sejam inaceitáveis.
- [ ] Apenas após aprovação, extrair componentes e introduzir adaptador Python/Wyzer, preservando licenças.
**PASS:** POC demonstrável com evidências de ambiente/commit/recursos/erros, separação frontend vs Claude garantida. Não confundir demonstração visual com Jarvis funcional.

## 4. Backend, IA local, memória e segurança (blocos seguintes)

| ID | Prioridade | Entrega / Gate | Evidência mínima |
| --- | --- | --- | --- |
| JAR-SEC-01 | P0 | Bind de sessões à identidade, concorrência serializada por sessão, logout/revogação, TTL, quotas multiworker | testes de race, 401/403, replay, cross-user e recuperação |
| JAR-SEC-02 | P0 | Autorização por ferramenta e confirmação ligada a digest+TTL; PT `sim/não/cancela` | nenhum efeito sem confirmação; cancelamento/falha fechado |
| JAR-CORE-01 | P0 | Contrato de eventos e estado entre Wyzer e frontend | schema versionado, typecheck, fakes determinísticos |
| JAR-MODEL-01 | P0 | Ollama real em host aprovado; tool calling, chat, context, streaming, timeout | logs/versões de modelo, sem fallback pago, latências medidas |
| JAR-MEM-01 | P1 | Persistência da sessão e factos/consentimento; corrigir esquecer/retenção | testes entre reinícios, isolamento e delete, protecção de dados |
| JAR-VOICE-01 | P0 | Faster-Whisper **multilingue** `pt`/auto (actual força `en` + `small.en`) | teste com áudio PT autorizado e mocks CI |
| JAR-VOICE-02 | P0 | Wake model legal «Jarvis», Kokoro PT ou TTS local licenciado, turn-taking, barge-in | falso positivo/negativo e latência com microfone real |
| JAR-AGENT-01 | P2 | Ferramentas Windows sob allowlists, aprovação e auditoria | execução mínima no Windows sandbox; rollback |
| JAR-RELEASE-01 | P3 | Instalador, operação offline/servidor medido, segurança, documentação e entrega ao Issa | gates A–D de `04_ACCEPTANCE.md`, aceitação expressa |

**VoiceStudio:** `AGPL-3.0-only`, pesos OmniVoice predefinidos restritos; **somente candidato a serviço local opcional**. Primeiro adaptar o Faster-Whisper/Kokoro já presentes, comparando qualidade, termos e custos. Sem pt-MZ comprovado.

## 5. Critérios de segurança visual e técnicos (transversais)

- Frontend é **presentation-only**: não manipula prompts de ferramenta arbitrários, não tem credenciais do modelo, não escolhe policy, não faz OS calls pelo browser.
- Mensagens UI ↔ Python: `session_id`, `request_id`, `event_id`, tipo, estado, timestamp, payload limitado; sanitização e allowlist; nenhuma chamada livre a métodos Python de `QWebChannel`.
- Estados recomendados: `OFFLINE, IDLE, WAKE_DETECTED, LISTENING, THINKING, TOOL_RUNNING, AWAITING_CONFIRMATION, SPEAKING, PAUSED, MUTED, ERROR`. Só mostrar `TOOL_RUNNING` se houver execução real autorizada.
- Offline ≠ gratuito em infra: custos de hardware/energia/hosting podem existir. Sem subscrições de IA **obrigatórias**.
- O grafo 3D **não** é MVP crítico: abrir só quando houver dados reais e perfis de autorização, sem indexar ficheiros privados automaticamente.
- Validação editorial: português, legibilidade, indicadores de escuta/privacidade; evitar layout dashboard genérico. O visual responde ao estado real do agente.
- Qualquer recurso de terceiros exige licença e notices; o código MIT do frontend não autoriza copiar personagens/músicas/trademarks.

## 6. Formato mínimo de entrega por tarefa

```text
TASK ID / ROLE / OWNER / STATUS
Base: branch develop @ <commit_sha> | upstream deps/tag
Files changed: ... | protected files changed: none
Work completed: ...
Evidence: exact command, environment, run id, log, PASS/FAIL
Architecture/security/licenses: ...
Known issues, regressions, open gates: ...
Next task ID / blocker / decisions requested:
```

**Nunca:** “está pronto”, “testado” ou “CI verde” sem a prova correspondente a esse commit.

## 7. Prompt de recuperação (colar num chat novo com acesso ao GitHub)

> Continuamos **VEXEL Jarvis — Issa Edition** da RIGHTWARE, no repo **https://github.com/rightware-corporations/jarvis**, apenas branches **main/develop**. **Não reiniciar selecção** e não substituir Wyzer/Python. Começa por ler, na branch **develop**, **docs/20_RECOVERY_START_HERE_2026-11-04.md**, **docs/21_MASTER_HANDOFF_2026-11-04.md**, **docs/22_DECISION_REGISTER_2026-11-04.md**, **docs/23_EXECUTION_PLAYBOOK_2026-11-04.md** e **docs/01_CURRENT.md**, depois confirma HEAD/PR#2/CI. Prioridade activa: Claude concluir plugin v0.1.1 e revisão `CLAUDE.md`; Manus executar preview visual real do frontend `adewaskar/jarvis` em Chromium **sem Claude bridge**, com PNGs reais; ChatGPT rever arquitectura e a visualização. Ainda não há screenshot real aceite nem HUD integrado. **Não instalar, executar, fazer deploy, migrar código, aprovar ou criar branches sem mandato concreto.** Distingue verificado em código, CI mock, proposta e funcionalidade final real. Informa divergências entre docs e HEAD antes de continuar.

## 8. Notas de continuidade e referências

- [20 Recovery index](20_RECOVERY_START_HERE_2026-11-04.md) · [21 Master](21_MASTER_HANDOFF_2026-11-04.md) · [22 Decisions](22_DECISION_REGISTER_2026-11-04.md).
- [Wyzer provenance](../UPSTREAM_PROVENANCE.md) · [API/Headless](09_WEB_LAB.md) · [Voz PT](10_VOICE_PT_AUDIT.md) · [Arquitectura](11_ARCHITECTURE_REVIEW_AND_EVOLUTION.md).
- [Visual HUD](12_HUD_REFERENCES_AND_UX_VISION.md) · [VoiceStudio](13_VOICESTUDIO_STATIC_ASSESSMENT.md) · [Skills](19_CLAUDE_SKILLS_TOOLCHAIN_PLAN.md) · [Claude audit](reference/CLAUDE_SKILLS_AUDIT_2026-11-04.md).
- [`adewaskar/jarvis` revision](https://github.com/adewaskar/jarvis/tree/1c4016afdf86f7043efc6882ceffef84ad0d8783); [pre-selection handoff](archive/PRE_WYZER_HANDOFF_2026-11-04.md) (histórico **superado**).

**Próximo passo após handoff:** esperar outputs reais de Claude e Manus; não iniciar implementação só porque o handoff está publicado.
