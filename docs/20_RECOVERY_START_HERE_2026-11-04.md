# COMEÇAR AQUI — recuperação do VEXEL Jarvis após falha de conversa

**Data do handoff:** 2026-11-04 (Africa/Maputo). **Produto:** VEXEL Jarvis — Issa Edition, RIGHTWARE. **Repositório:** [rightware-corporations/jarvis](https://github.com/rightware-corporations/jarvis), branch **develop**. **Não reiniciar discussão nem selecção.**

## Em 60 segundos

- **Motor escolhido:** Wyzer AI `v0.3.1`, Python 3.11; código já importado (`182/182` ficheiros de código/texto; 44 binários omitidos) para `develop`, com proveniência e verificações; `main` não deve ser modificada sem aprovação.
- **Objectivo:** «Hey Jarvis» por voz em português, resposta falada, memória/contexto, tarefas autorizadas e HUD holográfico flutuante para Issa Maulid, **sem APIs de IA pagas obrigatórias**.
- **Implementação existente:** `jarvis_lab/` com FastAPI, interface web técnica e testes com providers falsos (16 PASS anteriormente). **Não** há Ollama real validado, wake word Jarvis/PT, ferramentas Windows reais, nem HUD final.
- **Frontend:** prioritário reutilizar a *camada visual* MIT de [`adewaskar/jarvis`](https://github.com/adewaskar/jarvis/tree/1c4016afdf86f7043efc6882ceffef84ad0d8783). O **backend deste candidato depende do Claude**, portanto não o integrar. PySide6+QWebEngine+QWebChannel é **hipótese de POC**, não escolha já validada.
- **Claude:** plugin pessoal `rightware-jarvis-dev` **v0.1.0 instalado visualmente**, com nove skills; correcção v0.1.1 de permissões de `pyside6-desktop` **pendente**. `CLAUDE.md` original e revisão V2 **DRAFT, ainda não aprovadas**.
- **Manus:** encarregado/solicitado para screenshots **reais** do frontend original no Chromium, só Vite e sem bridge Claude. **Nenhum screenshot ou relatório entregue/validado até este handoff**.
- **Processo:** RIGHTWARE decide; ChatGPT arquitectura/revisão; Claude implementa/testa; Manus preview visual. GitHub é fonte dos commits.
- **Branches:** só `main` e `develop`, PR [#2](https://github.com/rightware-corporations/jarvis/pull/2) Draft. Não executar, instalar, fazer deploy, publicar ou criar branches sem tarefa autorizada.
- **CI antes da preservação:** [run 41827440760](https://github.com/rightware-corporations/jarvis/actions/runs/41827440760) PASS no `develop@da3d4a6`; **verificar o CI do HEAD depois dos commits documentais do handoff**.

## Ler na ordem

1. **[21 — Handoff mestre de tudo o que já foi visto](21_MASTER_HANDOFF_2026-11-04.md)** — história, repo, código, áudio, HUD, skills, Claude/Manus e riscos.
2. **[22 — Decisões e propostas](22_DECISION_REGISTER_2026-11-04.md)** — o que foi confirmado pela RIGHTWARE versus hipóteses/ideias/implementação.
3. **[23 — Execução e checklist](23_EXECUTION_PLAYBOOK_2026-11-04.md)** — próximas tarefas, critérios PASS/FAIL, donos de trabalho e prompt para novo chat.
4. **[01 — CURRENT](01_CURRENT.md)** — estado técnico e adenda de continuidade.
5. **[03 — BACKLOG](03_BACKLOG.md)** e [04 — ACCEPTANCE](04_ACCEPTANCE.md) — gates do produto.

## Outputs preservados que não podem perder-se

- [Handoff de **pré-selecção** anterior ao Wyzer — histórico superado](archive/PRE_WYZER_HANDOFF_2026-11-04.md).
- [Auditoria de skills JAR-DEV-SKILLS-02 integral](reference/CLAUDE_SKILLS_AUDIT_2026-11-04.md).
- [Relatório de validação do plugin RIGHTWARE v0.1.0](reference/CLAUDE_PLUGIN_VALIDATION_V010_2026-11-04.md).
- [Draft original `CLAUDE.md`](reference/CLAUDE_ORIGINAL_DRAFT_2026-11-04.md) e [revisão V2, não aprovada](reference/CLAUDE_REVIEW_V2_DRAFT_2026-11-04.md).
- [12 — Referências HUD](12_HUD_REFERENCES_AND_UX_VISION.md), [13 — VoiceStudio](13_VOICESTUDIO_STATIC_ASSESSMENT.md), [19 — Skills plano inicial](19_CLAUDE_SKILLS_TOOLCHAIN_PLAN.md).

**Não arquivado integralmente:** artefacto Claude [JAR-HUD-01](https://claude.ai/artifact/VEVVzCMeXw5As159GVA4XK) apenas referido/resumido; capturas e vídeo fornecidos no chat não foram enviados para o repo público; preview Manus ainda sem output.

## Exactamente o que fazer a seguir

1. **Conferir repo remoto**: HEAD `develop`, duas branches, PR#2 e CI actual. Ler documentação; **não mexer em código sem autorização**.
2. **Aguardar saída Claude**: plugin v0.1.1, diff original/V2 do `CLAUDE.md` e especificação M0; rever e aprovar **antes de commit na raiz**.
3. **Aguardar saída Manus**: PNG reais/galeria Chromium, consola e estados UI, com simulados marcados como `MOCK`. Avaliar visualmente com RIGHTWARE.
4. Só após a avaliação autorizar, se apropriado, **JAR-UX-03 M0**: teste Windows PySide6+WebGL+QWebChannel sem integração funcional, com medição CPU/RAM/GPU/foco/transparência.
5. Em paralelo de engenharia devidamente aprovada: `JAR-ARCH-02` upstream patch policy e `JAR-SEC-01` isolamentos da API. Voz PT/Ollama real só em hosts controlados e depois dos gates.

## Prompt de arranque rápido para outra conversa

> Retoma **VEXEL Jarvis — Issa Edition** da RIGHTWARE. Abre o repo **https://github.com/rightware-corporations/jarvis** na branch **develop** e lê integralmente **docs/20_RECOVERY_START_HERE_2026-11-04.md**, **docs/21_MASTER_HANDOFF_2026-11-04.md**, **docs/22_DECISION_REGISTER_2026-11-04.md** e **docs/23_EXECUTION_PLAYBOOK_2026-11-04.md**. Confirma HEAD, PR#2, branches e CI antes de afirmar estado. Wyzer já foi escolhido/importado: não recomeçar comparação, não construir outro assistente, não substituir motor por Claude/OpenClaw. Python/Ollama local-first, voz PT e HUD flutuante são requisitos; frontend `adewaskar` apenas visual, ainda não integrado. Claude trabalha na correcção de skills/CLAUDE.md; Manus foi encarregado do preview real Chromium mas não entregou ainda. Respeita apenas main/develop, upstream intocado, direitos, segurança e decisões RIGHTWARE. Indica estado exacto, tarefas, blockers e próxima acção, **sem instalar/deployar ou modificar código sem pedido**.

**Veracidade:** se um resultado posterior chegar (Claude, Manus, novo commit), registar aqui ou em `01_CURRENT` com prova e data; **não apagar o histórico nem reescrever estados antigos como se fossem aprovados**.

## ADENDA — nova entrega Claude recebida (04-11-2026, posterior ao handoff mestre)

**Ler agora também:** [24_CLAUDE_V011_V3_REVIEW_AND_M0_GATE_2026-11-04.md](24_CLAUDE_V011_V3_REVIEW_AND_M0_GATE_2026-11-04.md). A primeira versão do handoff descrevia a v0.1.1 como **aguardada**; depois recebemos o ZIP 0.1.1, relatório, draft V3 e diff V2→V3.

- **Plugin 0.1.1:** ZIP enviado e verificado por SHA-256 `919e1e3acd589f95f749d056b59baabf292cfb2cbe8eb10882612c300ec577f4`; 40 ficheiros, 9 skills, 34 hashes internos verificados; `pyside6-desktop` limita a pré-aprovação a Read/Grep/Glob. **Ainda não há prova de upload da v0.1.1 à conta**; a v0.1.0 era a última visualmente instalada.
- **CLAUDE.md V3:** [draft](reference/CLAUDE_V3_PROPOSTA_2026-11-04.md) e [diff](reference/CLAUDE_V2_PARA_V3_2026-11-04.diff) arquivados. Recomendado com quatro ajustes em 24; **NÃO aprovado/commitado na raiz**.
- **M0:** Claude relatou plano de 31 testes/8 áreas, mas o plano integral/limiares **não foi anexado**. Primeiro receber preview Manus/Chromium, depois smoke Windows isolado e só então matriz expandida sob autorização.
- **Instalador Wyzer:** `PySide6==6.6.1` em `installer/constraints-windows-py311.txt`, venv/pip, sem PyInstaller. Não fazer upgrade upstream sem política JAR-ARCH-02.
