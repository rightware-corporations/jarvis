# VEXEL JARVIS — ISSA EDITION | HANDOFF MESTRE, 04/11/2026

> **Handoff de continuidade e recuperação**, escrito para que RIGHTWARE, Claude, Manus e ChatGPT possam retomar o projecto sem a conversa anterior. **Este documento não autoriza instalar/deployar/executar código.** Toda a evidência tem de ser reconfirmada no GitHub antes de qualquer implementação.
>
> **Começar por:** [20_RECOVERY_START_HERE_2026-11-04.md](20_RECOVERY_START_HERE_2026-11-04.md) → [22_DECISION_REGISTER_2026-11-04.md](22_DECISION_REGISTER_2026-11-04.md) → [23_EXECUTION_PLAYBOOK_2026-11-04.md](23_EXECUTION_PLAYBOOK_2026-11-04.md).
>
> **Data:** quarta-feira, 4 de Novembro de 2026, Africa/Maputo. **Estado do runtime:** NÃO PRONTO. **Estado do repositório no início desta preservação:** `develop@da3d4a61b7dd07f209826962b7f268caa5a12b4b`; as alterações seguintes nesta operação são apenas documentos. **Não inferir HEAD novo deste valor fixo**; consultar GitHub.

## 1. Identidade, escopo e experiência pretendida

**RIGHTWARE** desenvolve o **VEXEL Jarvis — Issa Edition** para **Issa Maulid**, como assistente pessoal Windows, controlado prioritariamente por voz, com capacidade de contextualizar e executar tarefas autorizadas. É um projecto **distinto** do site/produto de marketing VEXEL, e o código canónico pertence exclusivamente a [`rightware-corporations/jarvis`](https://github.com/rightware-corporations/jarvis).

**Experiência-alvo — requisitos confirmados pelo utilizador:**
1. Activar através de «Jarvis» / «Hey Jarvis», idealmente sem clique, com wake word verdadeiramente implementada, e não mera mudança de texto.
2. Perceber **português** natural utilizado por Issa (avaliar sotaque/expressões de Moçambique), ouvir, manter a continuidade de conversa e responder oralmente.
3. Usar **modelos auto-hospedados** (Ollama preferencial) para dispensar **APIs pagas/subscrições obrigatórias de IA** em execução. Claude/ChatGPT são **ferramentas de engenharia**, não cérebro pago do Jarvis final.
4. Executar funções no Windows *quando autorizadas*: aplicações, ficheiros, browser, tarefas, lembretes, informação; sem contornar confirmações ou permissões.
5. Existir visualmente no desktop como um **núcleo holográfico flutuante, movível, vivo e reactivo**, podendo expandir-se para um HUD; um modo grafo de inteligência é **opcional**, não um dashboard sempre aberto.
6. Funcionar de forma razoável com minimização, sem roubar o foco; mostrar quando ouve, processa, fala, falha ou aguarda consentimento.
7. A decisão de execução **local, num servidor ou híbrida** continua aberta até medir hardware, rede, privacidade, latência e custos; não prometer alojamento sem custo de infraestrutura.

**Não fazer:** reabrir competição entre 5 Jarvis, construir assistente de raiz, substituir Wyzer por OpenClaw/portal genérico, obrigar Claude/Anthropic em runtime, tratar um protótipo visual como assistente funcional.

## 2. Cronologia de investigação e decisões durante 04/11/2026

| Sequência | Acontecimento verificado/referido | Resultado / nível de evidência |
| --- | --- | --- |
| Pesquisa inicial | Handoff antigo exigia comparar **5 finalistas**: `ndunl075/Jarvis`, `Theycallmeinsane/jarvis`, `Axx33284/jarvis`, `RustamovAkrom/JARVIS` e `SpandanNagale/ARIA`. Nenhum aprovado nessa altura. | **HISTÓRICO, substituído** pela selecção posterior. Ver [arquivo completo](archive/PRE_WYZER_HANDOFF_2026-11-04.md). |
| Selecção posterior | RIGHTWARE escolheu **Wyzer AI v0.3.1** como base reutilizável. | **DECISÃO DE PRODUTO**, não prova de que o assistente já funcione. |
| Migração | Código original Wyzer importado para `develop` do repo Jarvis, com manifesto SHA, direitos e PR #2 Draft. | **IMPLEMENTADO / CI** para importação de texto, não binários nem runtime. |
| Laboratório | `jarvis_lab` (headless, API e frontend web restrito), contratos de isolamento e erros; 16 testes simulados PASS em CI anterior. | **IMPLEMENTADO / TESTADO EM CI COM FAKES**, não voz/IA reais. |
| Auditoria voz | STT de Wyzer inglês fixo; Kokoro tem mapeamento PT, openWakeWord precisa de ONNX legal; comandos/confirmations localizados. | **INSPECCIONADO**; português real não testado. |
| Auditoria arquitectura | Mapas `wyzer/`, API, desktop, memória, tools, políticas; proposta de organização em `apps/` e `jarvis/`. | **DOCUMENTADO**, ainda não houve refactor. |
| Inspiração de interface | Vídeo fornecido: esfera/reacção azul com estados de fala e painéis contextuais; imagem de browser `localhost:4719` com grafo de nós, reactor J.A.R.V.I.S. e HUD. | **REFERÊNCIA VISUAL**. Não prova de overlay nativo ou código correspondente. |
| Exploração visual | Estudados `adewaskar/jarvis`, `harsh-raj00/my-jarvis`, `desertcache/samantha-ui`, `hasibjaan/jarvis`, `Angga-29/jarvis-ai-assistant`, `ScuderiaFerrariSimp/Jarvis-Desktop-Assistant`, `vasturiano/react-force-graph`. | **INSPECCIONADO** em graus diversos; candidato principal é o frontend `adewaskar`, não o seu backend. |
| Referência Google Drive PWA | Guia «Como instalar o seu Jarvis? Passo a Passo», via browser, toque e tarefas. | **DOCUMENTO COMERCIAL**, não fonte verificável de runtime. |
| Guia Claude | Documento [Avello](https://docs.google.com/document/d/1LQDzVkhHrPYyGVdMtHzaPBlSIipDsa4TN6skBBGsRuE/view) remete a `adewaskar/jarvis`. | **INSPECCIONADO**: cérebro Claude Agent SDK/Anthropic, logo **não adoptar backend**. |
| Voz alternativa | [`debpalash/VoiceStudio`](https://github.com/debpalash/VoiceStudio) inspeccionado. | API local STT/TTS, mas app AGPL e licenças de pesos específicas; **não integrado**. |
| Colaboração | RIGHTWARE concordou com ChatGPT arquitecto/revisor, Claude engenheiro, GitHub canónico e Manus para preview visual. | **DIRECÇÃO DE PROCESSO**; nenhuma ferramenta aprova release sozinha. |
| Pesquisa skills | Repo skill index e auditoria Claude `JAR-DEV-SKILLS-02`. Identificaram sete skills pré-existentes e nove relevantes a acrescentar. | **AUDITORIA**, source SHA e licenças documentados. |
| Instalação skills | Plugin `Rightware jarvis dev` v0.1.0 foi carregado em **Customize → Plugins**. Duas capturas mostram «installed and ready» e 9 skills. | **INSTALAÇÃO VISUAL CONFIRMADA**. QA profunda do funcionamento de cada skill não efectuada. |
| Correcção de permissões | Claude encontrou em `pyside6-desktop/SKILL.md` `allowed-tools: Read, Edit, Write, Bash, Grep, Glob` (a auditoria anterior dissera apenas Read). | **RISCO CONFIRMADO NO FICHEIRO ORIGINAL**; proposta v0.1.1 com apenas Read/Grep/Glob, não entregue/verificada neste ponto. |
| Documento de governação | Claude produziu draft `CLAUDE.md`; ChatGPT apresentou revisão V2. | Ambos **DRAFT** arquivados, ainda não aprovados e sem `CLAUDE.md` na raiz. |
| Auditoria do frontend | Claude elaborou `JAR-HUD-01` e referiu cerca de 46% de linhas puramente visuais, reactor GLSL, 4.000 partículas, cards/HUD; recomendou Qt+WebEngine+QWebChannel. | **RESUMO DO CLAUDE**; relatório integral permaneceu em artefacto Claude sem ficheiro recebido para GitHub; parte do código reinspeccionada por ChatGPT. |
| Preparação para visualização | RIGHTWARE quis **ver o código da UI no Chromium antes de integrar**. ChatGPT não conseguiu obter screenshot real nesta sessão. | **NÃO TESTADO**. Foi elaborado prompt para Manus fazer preview Vite **sem bridge/Claude**. |
| Tarefa activa de Manus | Utilizador decidiu encaminhar o prompt de preview ao Manus, enquanto Claude conclui outros trabalhos. | **ATRIBUÍDA/PLANEADA**. Nada entregue ainda. |
| Preservação | Solicitação presente: guardar todas estas decisões, fontes, outputs e plano no repo, para sobreviver a falhas de chat. | Este handoff e os arquivos versionados são a resposta, só documentação. |

## 3. Estado canónico do GitHub e proveniência do código

**Repositório:** [RIGHTWARE Jarvis](https://github.com/rightware-corporations/jarvis) — **público**. **Branches:** `main` (estável) e `develop` (engenharia); nenhuma branch adicional permitida. **PR:** [#2 Draft / WIP Importação Wyzer v0.3.1](https://github.com/rightware-corporations/jarvis/pull/2), **aberto e não merged** na última consulta.

**Baseline Wyzer:** [`XtraWyze/Wyzer-Ai`](https://github.com/XtraWyze/Wyzer-Ai) tag `v0.3.1`, commit `db83c085feca32d3c091361165cb9ac7ecadafe0`. Manifesto [`upstream-v0.3.1-manifest.json`](../upstream-v0.3.1-manifest.json), [`UPSTREAM_PROVENANCE.md`](../UPSTREAM_PROVENANCE.md), `LICENSE` MIT, `NOTICE.md`.
- 226 blobs upstream no snapshot, **182 ficheiros textuais/de código importados SHA iguais**, **44 binários omitidos** (42 PNG + 2 ONNX) até prova de licenças. **Não** alegar «todos os ficheiros Wyzer importados».
- `wyzer/` (89 ficheiros Python), `tests/` (49 ficheiros upstream), `installer/`, `docs/upstream/`, `examples/`, `evals/`, `wyzer.toml` e `pyproject.toml` integram fonte preservada.
- O manifesto protege baseline contra drift; alterar `pyproject.toml`, `wyzer.toml` ou código upstream sem política JAR-ARCH-02 dá falha CI. **Não alterar manifesto para fazer passar hashes depois de refactor não aprovado.**
- `main` estava em `10aa4648b61b6e2d2c2b91b3ff3edd3fb68bfe9b`, `develop` em `da3d4a61b7dd07f209826962b7f268caa5a12b4b` **antes** das adições deste handoff. Consultar HEAD/CI actual, porque os commits documentais mudaram `develop`.

**CI confirmado anteriormente:** [41813747553](https://github.com/rightware-corporations/jarvis/actions/runs/41813747553) primeira validação (182/182 e 5 testes headless), [41815677923](https://github.com/rightware-corporations/jarvis/actions/runs/41815677923) 16 testes headless/API, [41827440760](https://github.com/rightware-corporations/jarvis/actions/runs/41827440760) success em `da3d4a6`. **O CI dos novos commits de documentação deste handoff deverá ser verificado à parte.**

## 4. O que já existe tecnicamente (e o que ainda não prova)

| Área | Código concreto | Estado verdadeiro |
| --- | --- | --- |
| Orquestração | `wyzer/app/orchestrator.py` | Motor Wyzer, dependências injectáveis; proveniente do código upstream, não validado como Jarvis final. |
| Provider local | `wyzer/brain/{providers,factory}.py`; `wyzer.toml` com Ollama `127.0.0.1:11434` | Integração **INSPECCIONADA**; nenhuma resposta real Ollama testada no ambiente RIGHTWARE. |
| Registry/tools | `wyzer/tools/{registry,builtin_packs}.py` | Packs Windows presentes upstream; **não registados** no laboratório web; execução OS real não testada. |
| Segurança/confirm | `wyzer/policy/confirmations.py` e `wyzer/app/orchestrator.py` | Digest/TTL e regex em inglês. Necessita metadados-first, PT, testes adversariais, falha fechada. |
| Memória | `wyzer/memory/store.py` SQLite e `wyzer/conversation/manager.py` RAM | Fact store ≠ memória longa validada; lab sem persistência quando storage_dir nenhum. |
| Desktop original | `wyzer/ui/{desktop,chat_window,character}.py`, PySide6 | Já fornece base de janela Qt e sinais de estado; interface holográfica nova ainda **não integrada**. |
| Voz | `wyzer/speech/{openwakeword,whisper,kokoro}.py` | Existência de adaptadores; sem wake ONNX «Jarvis», sem PT implementado/testado. |
| Lab headless | `jarvis_lab/headless.py` | `Orchestrator` com registry vazio/`SafeLabProvider`; sem acções Windows; provider fake nos testes. |
| Lab API | `jarvis_lab/api.py` | FastAPI, token de laboratório, sessões e rate limit **por processo**, sem revogação e sem lock específico por sessão no tratamento; não pronto para Internet. |
| Web Lab | `jarvis_lab/web/{index.html,lab.css,lab.js}` | Demo de chat/diagnósticos sem voz, sem frontend holográfico. Não é entrega para Issa. |
| Tests | `tests_lab/` + workflow `.github/workflows/source-integrity.yml` | **16 testes mock/API PASS anteriores**; não equivale a executar os 49 testes originais nem ao E2E real. |
| Plataforma | `pyproject.toml` `>=3.11,<3.12`; `installer/constraints-windows-py311.txt` | Python **3.11** fixado. Sem migração automática para Python 3.12/uv ou remoção de constraints. |

**Riscos de API estudados:** `X-Jarvis-Lab-Token` partilhado, sessões in-memory, ownership não vinculado a identidade separada, quota/limite in-process, concorrência de `assistant.handle()` fora do `state_lock`, sem logout/revogação backend. Estes são **riscos por leitura estática**, não incidentes explorados ou reparados.

## 5. Fluxo funcional que o produto precisa ter

```text
  Issa diz "Hey Jarvis"
          |
  Detector wake word local (modelo ONNX com direitos verificados)
          |
  Captura microfone/VAD/ASR multilingue PT (cancelamento)
          |
  Normalização e entendimento de comando + contexto de sessão
          |
  Orchestrator Wyzer + provider Ollama local / privado
          |
  ConfirmationPolicy tipada / consentimento humano / auditoria
          |
  [resposta sem ferramenta] OU [broker Windows com ferramenta autorizada]
          |
  Resposta escrita + TTS PT + sinais de estado reais
          |
  HUD Floating (normal) / Expanded (tarefas) / Graph (opcional)
```

**Estados UI propostos:** `OFFLINE`, `IDLE`, `WAKE_DETECTED`, `LISTENING`, `THINKING`, `TOOL_RUNNING`, `AWAITING_CONFIRMATION`, `SPEAKING`, `PAUSED`, `MUTED`, `ERROR`. **Não é contrato implementado**, é candidato ao schema de eventos e a testes. A UI não decide autorizações, nem recebe tokens do LLM ou acesso directo a PowerShell.

## 6. Voz — pesquisa realizada e pendências

**Wyzer:**
- Em `wyzer/speech/whisper.py`, `model.transcribe(...,language="en")` com prompt/hotwords em inglês; `wyzer.toml`: `speech.enabled=false`, `wake_phrase="hey wyzer"`, `wake_model="hey_Wyzer.onnx"` e `whisper_model="small.en"`. **Trocar apenas `wake_phrase` não produz detector Jarvis funcional.**
- `wyzer/speech/openwakeword.py` usa `openwakeword.model.Model` e requer modelo ONNX válido, um dos binários não distribuídos.
- `wyzer/speech/kokoro.py` identifica prefixos `pf`/`pm` para vozes PT-BR; preset de saída ainda inglês; qualidade pt-PT/pt-MZ não testada.
- `wyzer/app/cli.py`, `orchestrator.py` e `policy/confirmations.py` reconhecem essencialmente comandos/afirmações inglesas, risco de execução ou de confirmação inadequada em PT.

**VoiceStudio** [fonte](https://github.com/debpalash/VoiceStudio), `main@fd66407f9447b2348e1dab74901328d3b8bd2e47`:
- TTS e STT locais com API FastAPI; `POST /v1/audio/speech`, `POST /v1/audio/transcriptions`, WS `/v1/audio/transcriptions/stream` e `/ws/tts`; motores Faster-Whisper, WhisperX e opções em catálogo.
- `backend/core/language_variants.py` reconhece `pt-BR` e `pt-PT`, mas **não comprova sotaque moçambicano**; desempenho/memória variam muito por engine.
- Aplicação `AGPL-3.0-only`; licença de pesos **não herda** licença do SDK. Inventário consultado marcou OmniVoice default com restrições não comerciais e termos de tokenizer. Revisão legal antes de distribuição.
- **Orientação:** priorizar reparação do STT Wyzer + comparação controlada de Kokoro PT versus alternativa local legal; VoiceStudio opcional como processo serviço separado não isenta automaticamente obrigações AGPL.

Referências: [auditoria da voz PT](10_VOICE_PT_AUDIT.md), [VoiceStudio em profundidade](13_VOICESTUDIO_STATIC_ASSESSMENT.md). **Nenhum modelo/voz/microfone de Issa foi instalado/testado.**

## 7. Frontend/holograma — o que foi visto e o que queremos

### 7.1 Referências directas entregues pelo utilizador

1. **Vídeo `jarvis.mp4`** (cerca de 82s, entregue nesta conversa; **não publicado no repo público**): esfera/reactor azul com partículas/óbitas, estado de fala, painéis de meteorologia/agenda/comunicações, estrutura sensível ao contexto. É **referência visual**, não código validado.
2. **Screenshot `localhost:4719`**: interface no Chromium com grafo de centenas de nós azuis/verdes/amarelos interligados; filtros e workspaces à esquerda, reactor circular J.A.R.V.I.S. à direita, comandos inferiores. **Não demonstra** ser overlay nativo do Windows, nem é prova de origem `adewaskar`.
3. **Google Drive comercial:** [guia de instalação via browser](https://drive.google.com/file/d/1qweMY0y0x4IBuWKQY_UkMoYJrAX1J1X6/view?usp=drive_link), descreve PWA e funcionalidades assistente; não expõe implementação.
4. **Google Docs Avello:** [«Seu próprio Jarvis com Claude Code»](https://docs.google.com/document/d/1LQDzVkhHrPYyGVdMtHzaPBlSIipDsa4TN6skBBGsRuE/view). Remete a [`adewaskar/jarvis`](https://github.com/adewaskar/jarvis); instalação Claude/Anthropic é dependência do **backend dessa referência**, não deverá ser importada.
5. Mais fontes anotadas: [`harsh-raj00/my-jarvis`](https://github.com/harsh-raj00/my-jarvis) (reactor R3F MIT), [`desertcache/samantha-ui`](https://github.com/desertcache/samantha-ui) (SoulOrb/GLSL MIT), [`Angga-29/jarvis-ai-assistant`](https://github.com/Angga-29/jarvis-ai-assistant) (overlay Electron MIT), [`hasibjaan/jarvis`](https://github.com/hasibjaan/jarvis) (PySide6/orb/hud, licença não confirmada), [`ScuderiaFerrariSimp/Jarvis-Desktop-Assistant`](https://github.com/ScuderiaFerrariSimp/Jarvis-Desktop-Assistant) (Qt WebEngine, licença não confirmada), [`vasturiano/react-force-graph`](https://github.com/vasturiano/react-force-graph) (grafos, licença da versão exacta a confirmar).

### 7.2 Candidato prioritário: frontend `adewaskar/jarvis`

**Rev. inspeccionada:** [`1c4016afdf86f7043efc6882ceffef84ad0d8783`](https://github.com/adewaskar/jarvis/tree/1c4016afdf86f7043efc6882ceffef84ad0d8783). **Licença do código:** MIT (`LICENSE`; © 2026 Aditya Dewaskar). **Componentes considerados para extracção com notices:**
- `src/scene/Core.tsx` (reactor/shader), `Scene.tsx` (cena e estados), `Particles.tsx` (`const COUNT = 4000`), `Orbits.tsx`.
- `src/ui/Hud.tsx`, `Panels.tsx`, `Blades.tsx`, `Effects.tsx`, `Pointer.tsx` e, sujeito a branding/direitos, efeitos de arranque.
- `src/ui/sanitise.ts` para sanitização de conteúdos, mas manter sanitização própria e CSP do projecto.

**Excluir/desacoplar:** `bridge/server.mjs` (Claude Agent SDK), `src/lib/{brain,anthropic,bridge}.ts` na forma original; browser speech em inglês com privacidade/serviços externos, ElevenLabs, camera/gestos e permissões cloud; música e branding *Iron Man/J.A.R.V.I.S.* sem revisão jurídica. **A UI visual pode usar React/Three.js sem Claude como cérebro**, mas ainda precisa de build e eventos falsos/actuais.

**Posição da equipa:** primeiro testar visual real no Chromium sem backend Claude; depois medir composição `PySide6 + QWebEngine + QWebChannel` em Windows e comparar fallback `QPainter/Qt Quick`. **O frontend não foi copiado para RIGHTWARE**.

**Claude JAR-HUD-01 (relatório resumido pelo utilizador):** diz que o núcleo/shader, partículas, HUD e cards formam ~46% das linhas de `src/` e não importam Claude; aproveitamento visual pode ser considerável; apontou estimativa de **18,5–28 pessoa-dias** após POC **3–5 dias**. **Estimativa não verificada/compromisso não assumido.** O artefacto completo [JAR-HUD-01](https://claude.ai/artifact/VEVVzCMeXw5As159GVA4XK) não foi materializado aqui.

### 7.3 Modos visuais e POC

- **Floating — prioridade:** pequena janela sem moldura/móvel sobre desktop, always-on-top opcional, mute/indicador de microfone, ocultar/expandir, sem roubar o foco, perfil de consumo baixo.
- **Expanded HUD — quando útil:** reactor central, painéis surgem por acção real (agenda, resultados, ficheiros, diagnósticos); informação contextual e legível, sem cartões fixos genéricos.
- **Intelligence Graph — fase posterior/opcional:** grafo relações reais autorizadas, clustering e carregamento sob pedido, sem indexar ficheiros pessoais silenciosamente.
- **JAR-UX-03 M0:** WebGL transparente no Qt Windows, ensaio real de focus, Alt-Tab, DPI, multi-monitor, CPU/RAM/GPU/FPS, resize, transparência, brilho, cleanup. Se insatisfatório, estudar reactor 2D/Qt nativo. **Não executado.**
- O aspecto final NÃO foi aprovado. Screenshot Chromium real do `adewaskar` é requisito imediato de decisão.

Fontes: [HUD e UX](12_HUD_REFERENCES_AND_UX_VISION.md); [arquitectura proposta](11_ARCHITECTURE_REVIEW_AND_EVOLUTION.md).

## 8. Claude — competências, instalação, riscos e outputs

**Colaboração definida:** RIGHTWARE especifica/autoriza, ChatGPT arquitecta e revê, Claude implementa e testa, Manus faz exploração visual, GitHub concentra a verdade dos commits.

### Auditoria e competências
- O Claude examinou seis repositórios de skills: `anthropics/claude-plugins-official`, `anthropics/skills`, `wshobson/agents`, `obra/superpowers`, `trailofbits/skills`, `NerdBase-by-Stark/claude-code-skills`.
- O ambiente já tinha plugins RIGHTWARE engineering/security/frontend/design/marketing, GitHub, algumas skills de Superpowers, `frontend-design` e `supply-chain-risk-auditor`.
- Recomendação JAR-DEV-SKILLS-02: nove skills adicionais **sem duplicar** — `async-python-patterns`, `python-type-safety`, `python-error-handling`, `python-resilience`, `python-resource-management`, `python-performance-optimization`, `python-packaging`, `pyside6-desktop`, `property-based-testing`.
- `pyright-lsp` reservado para **Claude Code local**, não essencial em Claude Desktop cloud; `superpowers` plugin completo, `security-guidance`, `modern-python`, `llm-application-dev` completo **não recomendados** por hooks/subagentes, conflito de Python 3.11 ou SDK Anthropic em exemplos.
- O Claude produziu o pacote `rightware-jarvis-dev.zip` (v0.1.0) **99 600 bytes**, SHA256 declarado `9f9ce6dec3a30d6d937bb4b47dcc0b58fd6352bc88d3cab9d62b0263b646aee6`, 40 ficheiros; fonte e hashes em [relatório de validação](reference/CLAUDE_PLUGIN_VALIDATION_V010_2026-11-04.md). **O ZIP original não foi enviado aqui**, portanto hash não recalculado por ChatGPT.
- Upload em `Settings → Customize → Skills → Upload a skill` FALHOU porque o ZIP é **plugin com 9 skills** (aquela rota requer **uma** skill, um `SKILL.md`, sem plugin manifest). Instalação correta: `Customize → Plugins → Upload plugin`.
- Capturas fornecidas mostram **Rightware jarvis dev** v0.1.0 **instalado e activo**, separador `Skills · 9` e toast «installed and ready to use».
- **Correcção posterior:** Claude verificou que `pyside6-desktop/SKILL.md` permite `Read, Edit, Write, Bash, Grep, Glob`. A sugestão anterior de apenas Read era falsa. Foi solicitada **v0.1.1** limitando a `Read, Grep, Glob`, subjecta a novo pacote/validação/upload e revisão de permissões globais. Não inventar que a v0.1.1 já foi instalada.

### `CLAUDE.md` e governação
- [Draft original](reference/CLAUDE_ORIGINAL_DRAFT_2026-11-04.md) preparado pelo Claude. [Revisão V2](reference/CLAUDE_REVIEW_V2_DRAFT_2026-11-04.md) produzida por ChatGPT. **Nenhuma aprovada ou commitada na raiz**.
- Cobrem as regras: duas branches, commit apenas quando autorizado, preservação Wyzer 182/182, Python 3.11, pip e constraints, licença, segurança, proibição de IA paga como requisito, QA PASS/FAIL, trabalhos por SHA.
- A V2 recomenda distinção de protocolos “OpenAI-compatible” usados localmente versus **API paga**, revisão de `QWebChannel` e permissões de QA Windows.
- Claude foi orientado a: preparar pacote v0.1.1, comparar original→V2, especificar POC M0 **sem executar/alterar repo**. **Output final dessa nova ronda não recebido**.

**Arquivos:** [auditoria skills Claude](reference/CLAUDE_SKILLS_AUDIT_2026-11-04.md), [plano oficial da conversa 19](19_CLAUDE_SKILLS_TOOLCHAIN_PLAN.md), [relatório do ZIP](reference/CLAUDE_PLUGIN_VALIDATION_V010_2026-11-04.md).

## 9. Manus — tarefa actual de pré-visualização

**O utilizador decidiu enviar o trabalho ao Manus, uma vez que Claude estava ocupado.** Responsabilidade: preview do frontend `adewaskar/jarvis` no **Chromium real**, sem qualquer IA paga ou bridge.

**Prompt de execução já preparado e enviado para o utilizador encaminhar:**
- clone temporário do commit `1c4016a` fora do repositório RIGHTWARE;
- revisar `package.json`/`package-lock.json` e scripts; apenas dependências visuais necessárias, sem scripts perigosos;
- iniciar **somente Vite** bind em `127.0.0.1` (não `npm start`, não `npm run bridge`, não `bridge/server.mjs`);
- sem Claude Agent SDK, Anthropic/ElevenLabs, modelo remoto, mic/camera, MCP, ferramentas OS ou dados privados;
- Chromium/Playwright com PNG de arranque, idle, listening, thinking, speaking, expanded/painéis e janela compacta. Se precisar mock de estado, anotar `MOCK` e alterar apenas harness temporário;
- entrega: **capturas reais, galeria HTML, consola, limitações, lista MANTER/ADAPTAR/REMOVER, PASS/FAIL**;
- nenhum commit/merge/deploy, nenhuma integração final. **Nada recebido ainda**.

**Cuidado essencial:** a imagem `localhost:4719` enviada anteriormente é **referência de outro ecrã**, não screenshot provado do `adewaskar`. A galeria solicitada ao Manus irá colmatar essa lacuna.

## 10. Modelo de trabalho e arquitectura-alvo

```text
 RIGHTWARE (produto, orçamento, aprovações e release)
       |
       +-- ChatGPT: arquitectura, tarefas, auditorias e aceitação técnica
       +-- Claude: implementação controlada/QA em develop (depois da autorização)
       +-- Manus: preview visual Chromium e relatório (sem acesso à IA runtime)
       |
 GitHub rightware-corporations/jarvis
       |
   main (estável)  <-- PR #2 Draft / revisão RIGHTWARE
       |
   develop (engenharia, CI, docs e código)
       |
 ┌───────────────────────────────────────────────────────┐
 │   PySide6 shell / HUD visual reutilizado (PROP.)      │
 │   Floating | Expanded | Graph opcional                │
 └──────────────────────────┬────────────────────────────┘
                            │ estados tipados/QWebChannel (PROP.)
 ┌──────────────────────────v────────────────────────────┐
 │ Python 3.11 / adaptações RIGHTWARE / Wyzer Orchestrator│
 └─────────────┬────────────┬──────────────┬─────────────┘
          Ollama local    Memória         Policies + broker
                                             |
                                    Windows tools autorizadas
```

**Árvore modular proposta, não materializada:** `apps/{desktop,web,api,agent-windows}/`, `jarvis/{core,voice,providers,memory,policy,tools,schemas,observability}/`, `tests_vexel/`, `configs/`. **A árvore real contém `wyzer/`, `jarvis_lab/`, `tests/`, `tests_lab/`, `docs/` e `installer/`**. Refactor só incremental, com imports, licenças e testes.

## 11. Principais bloqueadores / riscos e sua resolução

| Risco | Impacto | Medida / gate |
| --- | --- | --- |
| Falha de chat anterior | Perda de contexto, decisões contraditórias | Documentos GitHub 20–23, snapshots e prompt de recuperação |
| Upstream 182/182 imutável | Refactor involuntário invalida CI e proveniência | JAR-ARCH-02 primeiro, patch policy rastreável |
| Português STT fixo inglês | Não reconhece comandos de Issa | JAR-VOICE-01: multilingue e avaliação PT real |
| Modelo wake Jarvis ausente | Não activa por nome | ONNX legal, avaliação falsos positivos/negativos |
| TTS e licenças | Voz inadequada/restrição de distribuição | Comparar Kokoro vs alternativa licenciada; corpus pt-MZ consentido |
| No real Ollama | Não há experiência de IA provada | JAR-MODEL-01 real num host autorizado com logs de latência |
| Segredos e sessões Web Lab | IDOR/concorrência/abuso em acesso remoto | JAR-SEC-01/02; evitar deploy Internet |
| React/Three em Qt transparente | Frame drops, RAM/GPU/bugs de foco | JAR-UX-03 M0 com métricas Windows e fallback Qt |
| Dependência Claude no frontend upstream | Violação do princípio sem API paga | Copiar apenas componentes visuais, remover bridge/Anthropic |
| Personagens/música Marvel, assets de terceiros | Propriedade intelectual/trademark | Revisão de licenças e branding original RIGHTWARE |
| Plugin v0.1.0 PySide6 com Bash/Edit/Write | Permissões permissivas na engenharia | Corrigir para v0.1.1 e rever configuração global |
| Dados pessoais e voz do Issa | Privacidade e consentimento | Não publicar amostras; testar apenas com autorização |
| Duplicação de prompts/skills | Mudanças de arquitectura inconsistentes | `CLAUDE.md` aprovado, docs canonizados e tarefas com ID |

## 12. Próximas decisões e roteiro

**Imediato (sem implementação):** fechar preservação docs/CI; **aguardar** Claude v0.1.1 e diff `CLAUDE.md`; **aguardar** Manus screenshots Chromium. Rever screenshot em conjunto e escolher componentes MANTER/ADAPTAR/REMOVER. Só depois decidir se autorizar M0 Windows.

**Depois:** 
1. JAR-ARCH-02: aprovar `CLAUDE.md` e política de patches que preserve upstream.
2. JAR-HUD-00: analisar os screenshots reais; não comprar trabalho de UI sem ver o resultado.
3. JAR-UX-03 M0: POC PySide6/QWebEngine com WebGL/transparência; medir; fallback nativo.
4. JAR-SEC-01/02 e JAR-CORE-01: sessões, autorização e contrato de estados.
5. JAR-MODEL-01: teste real Ollama, memória, tempo de resposta, streaming e ferramentas simuladas.
6. JAR-VOICE-01/02: PT multilingue, wake Jarvis, TTS em PT, barge-in e confirmação.
7. JAR-HUD-02: separar e integrar componentes visuais licenciados a contrato Python.
8. JAR-AGENT-01: abrir as primeiras ferramentas Windows autorizadas em sandbox.
9. JAR-RELEASE-01: QA Windows real, instalador e aceitação do Issa (gates A–D).

**Custo/prazo:** não há baseline de hardware de Issa nem benchmarking, logo nenhuma promessa de tempo ou custo. Estimativa Claude (3–5 dias M0 + 18,5–28 pessoa-dias integração) é apenas referência de planeamento.

## 13. Inventário documental no GitHub

**Primários:**
- [00_START_HERE](00_START_HERE.md) — índice prévio, com adenda deste handoff.
- [01_CURRENT](01_CURRENT.md) — histórico de estado, riscos e gates.
- [02_ARCHITECTURE](02_ARCHITECTURE.md), [03_BACKLOG](03_BACKLOG.md), [04_ACCEPTANCE](04_ACCEPTANCE.md).
- [05_SOURCE_AUDIT_P0](05_SOURCE_AUDIT_P0.md), [06_REMOTE_QA](06_REMOTE_QA.md), [08_HEADLESS_ADAPTER](08_HEADLESS_ADAPTER.md), [09_WEB_LAB](09_WEB_LAB.md).
- [10_VOICE_PT_AUDIT](10_VOICE_PT_AUDIT.md), [11_ARCHITECTURE_REVIEW_AND_EVOLUTION](11_ARCHITECTURE_REVIEW_AND_EVOLUTION.md).
- [12_HUD_REFERENCES_AND_UX_VISION](12_HUD_REFERENCES_AND_UX_VISION.md), [13_VOICESTUDIO_STATIC_ASSESSMENT](13_VOICESTUDIO_STATIC_ASSESSMENT.md).
- [19_CLAUDE_SKILLS_TOOLCHAIN_PLAN](19_CLAUDE_SKILLS_TOOLCHAIN_PLAN.md).
- [20_RECOVERY_START_HERE](20_RECOVERY_START_HERE_2026-11-04.md), **este 21**, [22_DECISION_REGISTER](22_DECISION_REGISTER_2026-11-04.md), [23_EXECUTION_PLAYBOOK](23_EXECUTION_PLAYBOOK_2026-11-04.md).

**Referências históricas arquivadas:**
- [Pré-Wyzer handoff integral](archive/PRE_WYZER_HANDOFF_2026-11-04.md): 5 finalistas antigos, hipóteses e relatório Perplexity. **SUPERADO**.
- [JAR-DEV-SKILLS-02 integral](reference/CLAUDE_SKILLS_AUDIT_2026-11-04.md).
- [Rightware plugin v0.1.0 validation](reference/CLAUDE_PLUGIN_VALIDATION_V010_2026-11-04.md).
- [`CLAUDE.md` original DRAFT](reference/CLAUDE_ORIGINAL_DRAFT_2026-11-04.md).
- [`CLAUDE.md` V2 DRAFT](reference/CLAUDE_REVIEW_V2_DRAFT_2026-11-04.md).

**Fontes externas complementares:** [Wyzer origin](https://github.com/XtraWyze/Wyzer-Ai), [frontend candidato](https://github.com/adewaskar/jarvis/tree/1c4016afdf86f7043efc6882ceffef84ad0d8783), [VoiceStudio](https://github.com/debpalash/VoiceStudio), [Manus](https://manus.im), [Claude artifact HUD audit](https://claude.ai/artifact/VEVVzCMeXw5As159GVA4XK), [guia Avello](https://docs.google.com/document/d/1LQDzVkhHrPYyGVdMtHzaPBlSIipDsa4TN6skBBGsRuE/view) e [guia PWA](https://drive.google.com/file/d/1qweMY0y0x4IBuWKQY_UkMoYJrAX1J1X6/view).

**Ficheiros multimédia NÃO enviados ao GitHub público:** vídeo `jarvis.mp4`, capturas de screenshots/consultas e galeria de quadros gerada; não reutilizar sem avaliar direitos, privacidade e consentimento. Este handoff descreve-os e remete às fontes recebidas.

## 14. Protocolo de recuperação após falha do chat

1. Abrir [GitHub `develop/docs/20_RECOVERY_START_HERE_2026-11-04.md`](https://github.com/rightware-corporations/jarvis/blob/develop/docs/20_RECOVERY_START_HERE_2026-11-04.md).
2. Ler este Master, Decision Register, Execution Playbook e `01_CURRENT`. Confirmar **HEAD actual**, branches, PR#2, CI e diferenciar os commits documentais de implementação.
3. Consultar saídas **novas** do Claude e Manus apenas se efectivamente entregues; não inferir conclusão pelo facto de terem recebido um prompt.
4. Preservar source Wyzer; se for preciso escrever em upstream, exigir JAR-ARCH-02 antes.
5. A próxima resposta ao operador deve identificar **TASK ID, estado actual e acção única concreta**, não recomeçar o projecto nem pedir história repetida.
6. Se o chat tiver falhado, copiar o prompt completo de recuperação do [playbook 23 `7](23_EXECUTION_PLAYBOOK_2026-11-04.md#7-prompt-de-recuperação-colar-num-chat-novo-com-acesso-ao-github).

## 15. Declaração de veracidade final

**O que está comprovado:** código-fonte principal Wyzer importado/preservado; laboratório limitado com testes CI de contrato anteriores; documentação de arquitectura/voz/skills/HUD; plugin Claude v0.1.0 visualmente instalado; decisões de produto e prompt Manus preparados.

**O que NÃO está comprovado:** Jarvis com «Hey Jarvis» a ouvir Issa, português natural de Issa, inferência Ollama real, execução segura de tarefas Windows, UX holográfica integrada, previews Chromium reais do `adewaskar`, hardware/benchmarks e entrega pronta.

**A recuperação deve continuar a partir deste estado, não do handoff pré-Wyzer.**

## ADENDA APÓS PUBLICAÇÃO — nova entrega Claude recebida, 04/11/2026

O estado das secções originais representa o instante anterior à nova entrega. **Não reescrever o histórico; usar esta adenda como informação posterior.**

- O Claude entregou `rightware-jarvis-dev-0.1.1.zip`, `rightware-jarvis-dev-0.1.1-VALIDATION.md`, `CLAUDE_V3_PROPOSTA.md` e `CLAUDE_V2_para_V3.diff`. Integridade interna do ZIP e permissão limitada do `pyside6-desktop` confirmadas por análise independente, **mas sem instalação da v0.1.1 na conta confirmada**.
- [Revisão 24](24_CLAUDE_V011_V3_REVIEW_AND_M0_GATE_2026-11-04.md) regista SHA256 do ZIP, avisos e quatro ajustes propostos ao V3.
- V3 e diff foram preservados em [reference/CLAUDE_V3_PROPOSTA_2026-11-04.md](reference/CLAUDE_V3_PROPOSTA_2026-11-04.md) e [reference/CLAUDE_V2_PARA_V3_2026-11-04.diff](reference/CLAUDE_V2_PARA_V3_2026-11-04.diff); **V3 continua DRAFT, sem `CLAUDE.md` oficial na raiz**.
- Claude relatou plano M0 de 31 testes/8 áreas para comparar PySide6/Qt; **o plano e limiares completos não foram recebidos como ficheiro**. Recomendação: primeiro galeria Chromium do Manus, depois smoke Windows com baseline 6.6.1, só então matriz completa após autorização.
- O pacote ZIP de skills não foi publicado no repo público; apenas metadados/validação e referências. Não confundir um ZIP recebido no chat com plugin já instalado.
