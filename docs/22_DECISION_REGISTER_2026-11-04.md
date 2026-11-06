# VEXEL Jarvis — Registo de decisões, hipóteses e pendências (04-11-2026)

**Natureza:** registo de continuidade; distinguir confirmação do utilizador de proposta da equipa. **Não é uma autorização geral de implementação**. Data/timezone: 2026-11-04, Africa/Maputo.
**Precedência:** decisão explícita mais recente da RIGHTWARE > documentação aprovada > estado verificado do GitHub > rascunhos e recomendações. O `CLAUDE.md` anexo continua **DRAFT**, não vinculativo até aprovação e commit.

## A. Direcções confirmadas pela RIGHTWARE na conversa

| ID | Direcção confirmada | Limite exacto |
| --- | --- | --- |
| D-001 | Produto **VEXEL Jarvis — Issa Edition**, destinado a Issa Maulid, desenvolvido pela RIGHTWARE. | A organização é RIGHTWARE, não confundir com identidade do operador. |
| D-002 | Reutilizar **Wyzer AI v0.3.1** como motor; **não** reiniciar de zero nem trocar por OpenClaw/portal genérico. | Código importado no repo próprio; melhorias mediante arquitectura controlada. |
| D-003 | Repositório canónico: [`rightware-corporations/jarvis`](https://github.com/rightware-corporations/jarvis). | **Não** migrar para o repositório VEXEL/website. |
| D-004 | Manter apenas `main` (estável) e `develop` (engenharia). | Não criar outras branches, worktrees nem merge para main sem pedido. |
| D-005 | Python é base principal de backend/voz e integração, com Ollama ou modelo local como via preferencial de IA. | Não congelar modelo específico antes de QA. |
| D-006 | Jarvis activa por nome («Jarvis»/«Hey Jarvis»), conversa em português, mantém contexto, responde por voz e executa tarefas **autorizadas**. | Ainda não comprovado nem instalado no PC de Issa. |
| D-007 | Claude/ChatGPT podem ser ferramentas de desenvolvimento, **nunca dependências pagas obrigatórias do runtime**. | Infraestrutura própria pode ter custos; local/servidor/híbrido por decidir. |
| D-008 | Deseja-se **interface HUD própria**, holográfica, flutuante e móvel no desktop; rejeita UI de chat/dashboard convencional. | Visual final ainda requer avaliação real e aprovação. |
| D-009 | Priorizar **reaproveitamento de frontend** já existente para reduzir tempo, em vez de redesenhar reactor/partículas do zero. | Não aprova copiar backend de IA, voz cloud, marca/arte ou licenças de terceiros automaticamente. |
| D-010 | Modelo de colaboração: RIGHTWARE aprova; ChatGPT especifica/revê; Claude implementa; Manus pode avaliar visualmente no Chromium. | Cada ferramenta deve produzir evidências PASS/FAIL e obedecer ao mesmo estado GitHub. |
| D-011 | Preparar e instalar skills Claude especializados antes da engenharia. | O plugin `rightware-jarvis-dev` v0.1.0 com 9 skills **aparece instalado e activo nas capturas**; revisão v0.1.1 pendente. |
| D-012 | Pedida preservação de um **handoff completo no próprio repositório**, para continuar mesmo que o chat falhe. | Implementar nesta ronda só documentação de continuidade. |

## B. Propostas aceites como orientação, mas **não convertidas em decisão final de implementação**

| ID | Proposta | Estado/gate de escolha |
| --- | --- | --- |
| P-001 | Três modos: Floating (principal), Expanded HUD (contextual), Intelligence Graph (opcional). | Estudo UX; gráficos apenas com dados reais autorizados. |
| P-002 | Começar pela extracção visual de [`adewaskar/jarvis`](https://github.com/adewaskar/jarvis) (revisão `1c4016afdf86f7043efc6882ceffef84ad0d8783`). | **Candidato prioritário de frontend, não frontend final aprovado**. Preview real e auditoria de licenças pendentes. |
| P-003 | Reaproveitar `src/scene/{Core,Scene,Particles,Orbits}.tsx` e partes `src/ui/`. | Confirmar imports/contraintes, direitos, build visual e minimização das dependências; excluir `bridge/server.mjs`, `brain.ts` cloud etc. |
| P-004 | Shell desktop PySide6 + QWebEngine + QWebChannel para UI React/Three.js. | **Hipótese arquitectural** sujeita à POC Windows M0 e medições; fallback QPainter/Qt Quick. |
| P-005 | Adaptador de estados e eventos entre Python/Wyzer e HUD, evitando o browser controlar ferramentas. | Definir schemas/políticas de mensagens antes de integrar. |
| P-006 | Uso eventual de VoiceStudio **como serviço local de voz separado e opcional**. | Estudo de licenças AGPL/pesos, recursos e comparação com Faster-Whisper/Kokoro; nenhum código integrado. |
| P-007 | Skills internas `jarvis-wyzer-integrator`, `jarvis-ollama-runtime`, `jarvis-llm-eval`, `jarvis-voice-pt` e `jarvis-hud-desktop`. | Criar apenas após contratos e plugin v0.1.1; não dependem de API paga. |
| P-008 | Elaborar e aprovar `CLAUDE.md` na raiz. | Draft original e V2 arquivados em `docs/reference/`; **ainda não aprovado/instalado na raiz**. |
| P-009 | Plugin `rightware-jarvis-dev` v0.1.1 com `pyside6-desktop` `allowed-tools` limitado a Read/Grep/Glob. | O Claude detectou Read/Edit/Write/Bash/Grep/Glob na v0.1.0, aguardando novo pacote/upload/verificação. |
| P-010 | Executar preview **front-only** com Chromium/Playwright por Manus. | Apenas Vite em ambiente isolado, sem bridge Claude, mic, camera, ElevenLabs, serviços pagos e ferramentas OS; aguardar provas reais. |

## C. Factos técnicos **verificados por código e CI**, não equivalentes a aceitação funcional

- `XtraWyze/Wyzer-Ai` `v0.3.1`, commit `db83c085feca32d3c091361165cb9ac7ecadafe0`; **182/182 ficheiros textuais** importados e hash-verificados; **44 binários excluídos** (42 PNG, 2 ONNX); código MIT, outros direitos pendentes.
- Branches `main` e `develop`; PR [#2](https://github.com/rightware-corporations/jarvis/pull/2) Draft e aberto no momento da verificação.
- `jarvis_lab/` inclui `Orchestrator` headless/registry vazio, FastAPI e Web Lab HTML/CSS/JS; 16 testes de contratos mock previamente PASS; **não** prova Ollama ou voz real. CI anterior: [run 41827440760](https://github.com/rightware-corporations/jarvis/actions/runs/41827440760).
- Py 3.11 em `pyproject.toml` e `installer/constraints-windows-py311.txt`.
- `wyzer/speech/whisper.py` fixa `language="en"`; config `small.en` e voz desactivada; modelos wake ONNX excluídos; confirmação/interruptions em inglês; Kokoro tem roteamento de vozes `pf`/`pm` sem qualidade PT-MZ testada.
- `adewaskar/jarvis`: MIT no arquivo `LICENSE`; `Particles.tsx` define `COUNT = 4000`; `Scene.tsx` usa React Three Fiber; `brain.ts` importa Anthropic. Nunca afirmar que a UI funciona independentemente do Claude **sem um harness visível comprovado**.
- `VoiceStudio`: codebase AGPL-3.0-only, API STT/TTS local e variantes PT-BR/PT-PT; pesos/modelos têm direitos distintos (OmniVoice default marcado como não comercial no inventário estudado). Não incorporar por omissão.

## D. O que **NÃO** foi aprovado nem concluído

- Não existe aprovação de design final, modelo/voz/wake word, framework de render definitivo, distribuição local/servidor, acesso ao PC de Issa, publicação Internet ou data de lançamento.
- Não foi importado o frontend `adewaskar`. Não há screenshots Chromium reais confirmados nesta conversa. A captura `localhost:4719` é referência de outra interface no browser, não prova de overlay.
- Não foram testados Ollama real, wake word «Jarvis», TTS/STT português com voz de Issa, Windows tools, render WebGL transparente em PySide6 ou QA completo no Windows.
- O orçamento/estimativa de **18,5–28 pessoa-dias de integração + 3–5 dias de POC** foi fornecido por Claude **como estimativa**, nunca aprovado como prazo, nem medido.
- Os resultados de Claude para `JAR-HUD-01` foram comunicados por resumo e link de artefacto; **o relatório completo não foi recebido como anexo materializado nesta conversa**. Não representar a transcrição como auditoria independente integral.
- Claude pode estar a trabalhar na v0.1.1 e na especificação M0; **nenhum output posterior deve ser presumido**.
- Manus recebeu uma tarefa prevista de preview; **nenhum resultado nem screenshot seu foi apresentado/validado** até ao fecho deste handoff.

## E. Hierarquia de documentos

1. [Handoff completo actualizado](21_MASTER_HANDOFF_2026-11-04.md): narrativo, inventário e referências.
2. [Playbook/checklist de execução](23_EXECUTION_PLAYBOOK_2026-11-04.md): tarefas, gates e aceitação.
3. [`01_CURRENT.md`](01_CURRENT.md): estado histórico incremental; **consultar adenda mais recente**.
4. [`19_CLAUDE_SKILLS_TOOLCHAIN_PLAN.md`](19_CLAUDE_SKILLS_TOOLCHAIN_PLAN.md): plano original de skills; rever com [auditoria Claude](reference/CLAUDE_SKILLS_AUDIT_2026-11-04.md).
5. [DRAFT CLAUDE V2](reference/CLAUDE_REVIEW_V2_DRAFT_2026-11-04.md): **não em vigor**.
6. [Handoff pré-Wyzer](archive/PRE_WYZER_HANDOFF_2026-11-04.md): histórico de cinco finalistas, **superado pela selecção Wyzer**.

**Operação:** não usar este registo para autorizar automaticamente alterações no repo ou execução de scripts/skills. Cada gate exige decisão explícita e evidências actuais.
