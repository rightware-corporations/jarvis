# 01 — CURRENT

**Data:** 2026-11-04 | **Repositório:** `rightware-corporations/jarvis` (público)

## Estado
- **BASE ESCOLHIDA:** Wyzer `v0.3.1` / upstream commit `db83c085feca32d3c091361165cb9ac7ecadafe0`.
- **IMPORTAÇÃO:** 182/182 ficheiros textuais/ código copiados, comparados por hash SHA Git; ZERO diferença. Excluídos 42 PNG + 2 ONNX.
- **LICENÇA DO CÓDIGO:** MIT, com NOTICE original. Licenças de assets/modelos/vozes por rever antes da distribuição.
- **BRANCHES:** somente `main` e `develop` verificadas via GitHub API. A antiga `feat/wyzer-v031-core-import` foi eliminada por workflow temporário PASS (run 41814286015); workflow privilegiado removido.
- **CÓDIGO DO UPSTREAM:** `wyzer/` (89 ficheiros), `tests/` (49), configs/scripts/installer/docs em `develop`.
- **INTEGRIDADE:** validada estaticamente por comparação Git de árvores. Workflow remoto criado.
- **CI REMOTO:** [run 41813747553](https://github.com/rightware-corporations/jarvis/actions/runs/41813747553) **PASS nos jobs `source-integrity` e `headless-contract`**. Integridade SHA 182/182 e compilação sintática PASS; 5 testes headless PASS. Foram corrigidas falhas iniciais de dependência `psutil`.
- **HEADLESS:** `jarvis_lab/headless.py` usa `Orchestrator` original com registry vazio, e `tests_lab/` contém testes de contrato; **5 PASS em Ubuntu/Python 3.11 remoto**.
- **INFERÊNCIA REAL:** Ollama previsto; endpoint/hosting e modelo em produção por decidir.
- **PORTUGUÊS:** ainda sem implementação/validação.
- **WEB LAB:** API FastAPI e interface HTML/CSS/JS em `jarvis_lab/` publicadas na `develop`, com autenticação por token, TTL/rate limit em memória e interface com fonte Inter (configurável). CI API validado: 16 testes headless/API PASS no run 41815677923. O adaptador sanitiza falhas do provider para não expor mensagens internas. **Não há deploy nem IA real configurada.**
- **PC ISSA:** não utilizado; requisitos de hardware desconhecidos.
- **ENTREGA:** não pronta.

## Verificações efectuadas
- GitHub upstream `v0.3.1`: 226 blobs, 182 importados, 44 assets binários excluídos.
- Hash original de todos os 182 importados verificado com GitHub git trees (nenhum mismatch).
- `Orchestrator(registry, executor, provider,...)` suporta injecção; `jarvis_lab` separa-se dos tool packs Win32.
- `MemoryStore` original não recebe `user_id`; a composição lab cria uma DB SQLite por identificador de utilizador.
- Configuração upstream: `small.en`, UI/voz inglesa, `coding_agent.enabled=true`. Lab **não** activa coding agent nem ferramentas do Windows.
- Confirmação e controlo determinístico upstream reconhecem expressões inglesas; PT requer localização cuidadosa.

## Gates seguintes
1. **Gate QA remoto (parcial PASS):** integridade, compilação e cinco contratos headless confirmados no run 41813747553; testes de integração mais profundos pendentes.
2. **Gate headless Linux (parcial PASS):** instância do `Orchestrator` com Pydantic e psutil no GitHub Ubuntu; mapear restantes dependências e plataforma.
3. **Gate segurança:** testar negação, confirmação, cancelamento e separação por utilizador; nenhuma ferramenta real no lab.
4. **Gate IA real:** a API já permite construir `OllamaChatProvider` com configuração em servidor, mas endpoint e modelo reais não foram fornecidos/testados; escolher hosting, validar tool calling e latência.
5. **Gate web:** UI e API implementadas com 16 testes de contrato PASS; deploy seguro, QA visual/browser e inferência real ainda pendentes.
6. **Gate PT:** STT, TTS, wake word, confirmações e comandos em português.
7. **Gate entrega:** direitos de modelos/assets, instalador, hardware e QA no equipamento Issa autorizado.

## Próxima execução
Passou o primeiro workflow remoto. Próximo: testes de confirmação/cancelamento, isolamento de serviços e iniciação de API headless autenticada / model runner. **A presença de novos testes não equivale a PASS até existir execução e logs correspondentes.**

## Avanço recente — laboratório web
- [GitHub Actions 41815677923](https://github.com/rightware-corporations/jarvis/actions/runs/41815677923) — PASS em `source-integrity` e `headless-contract` (16 testes).
- `jarvis_lab/api.py`: API FastAPI que exige token e falha com `503` sem modelo. Modelo real ainda não testado.
- `jarvis_lab/web/`: frontend inicial com Inter como fallback da tipografia usada no website VEXEL, CSS configurável.
- Uma regressão detectada em CI demonstrou exposição possível de texto de erro do provider pelo Orchestrator upstream. Adicionado `SafeLabProvider` para devolver falha genérica sem dados internos; teste passou.


## Revisão arquitectural — 2026-11-04 (JAR-ARCH-01)

- **Auditoria estática concluída e publicada:** [11_ARCHITECTURE_REVIEW_AND_EVOLUTION.md](11_ARCHITECTURE_REVIEW_AND_EVOLUTION.md). Mapas do frontend web, backend FastAPI, UI PySide6, orquestrador Wyzer, ferramentas, voz, memória, políticas, dependências e proposta de árvore futura.
- **Riscos P0 identificados por leitura, sem prova de exploração:** sessão do Web Lab com token partilhado e estado em memória; ausência de serialização por sessão de `assistant.handle()`; falta de revogação de sessão no backend; comandos e heurísticas de risco inglesas. Antes de preview externo com executor, exigir testes e segurança.
- **Não foi executada refactorização:** `wyzer/`, `jarvis_lab/`, `tests/` e manifesto de integridade continuam no lugar; `apps/` e `jarvis/` são apenas estrutura recomendada no documento.
- **README reconciliado:** já reflecte a existência da API/GUI de laboratório, ao contrário do texto anterior.
- **Próxima execução recomendada:** JAR-ARCH-02 (política de patches/snapshot da origem) e JAR-SEC-01 (isolamento, concorrência e sessões revogáveis) com contract tests; em paralelo preparar STT PT/JAR-VOICE-01. Não disponibilizar ao Issa até testes reais de LLM, voz e ferramentas.
- **QA desta revisão:** alterações documentais; GitHub Actions da respectiva HEAD só conta como PASS após conclusão explícita do workflow. O laboratório permanece sem modelo Ollama real e sem voz funcional.

## Pesquisa visual e de voz — 2026-11-04 (JAR-UX-REF-01 / JAR-VOICE-REF-01)

- **Pesquisa de interface documentada:** [12_HUD_REFERENCES_AND_UX_VISION.md](12_HUD_REFERENCES_AND_UX_VISION.md). Ideia de UI `Floating` (núcleo móvel), `Expanded HUD` (painéis contextuais) e `Intelligence Graph` (grafo apenas com dados reais autorizados). **Ainda é proposta, sem implementação nem decisão de renderização.**
- **Fontes estudadas:** `adewaskar/jarvis` (frontend MIT, **runtime depende Claude**, não adoptar bridge), `harsh-raj00/my-jarvis` (MIT), `desertcache/samantha-ui` (MIT), `Angga-29/jarvis-ai-assistant` (MIT), `hasibjaan/jarvis` (licença não confirmada), `ScuderiaFerrariSimp/Jarvis-Desktop-Assistant` (licença não confirmada), `vasturiano/react-force-graph` (licença da versão a verificar).
- **VoiceStudio estudado directamente:** [13_VOICESTUDIO_STATIC_ASSESSMENT.md](13_VOICESTUDIO_STATIC_ASSESSMENT.md), fonte `debpalash/VoiceStudio@fd66407f9447b2348e1dab74901328d3b8bd2e47`. API FastAPI local com TTS/STT, PT-BR/PT-PT identificados, sem Claude obrigatório; **AGPL-3.0-only para app, pesos default OmniVoice CC-BY-NC com termos adicionais**. NÃO copiar nem escolher modelo para uso comercial sem revisão jurídica.
- **Estado sem mudanças operacionais:** nem VoiceStudio nem as UI de terceiros foram instalados ou importados; Wyzer continua motor. A `main` e o PR Draft continuam sujeitos aos gates prévios.
- **Próxima fase recomendada:** definir decisões de renderer/UI e matriz de licenças/modelos; fazer avaliação PT e benchmarking de ASR/TTS; preservar o projecto de voz existente do Wyzer antes de adicionar serviços externos.


## HANDOFF INTEGRAL E SITUACÃO DE CONTINUIDADE — 04/11/2026

**Documentação-mestre:** [20_RECOVERY_START_HERE_2026-11-04.md](20_RECOVERY_START_HERE_2026-11-04.md) · [21_MASTER_HANDOFF_2026-11-04.md](21_MASTER_HANDOFF_2026-11-04.md) · [22_DECISION_REGISTER_2026-11-04.md](22_DECISION_REGISTER_2026-11-04.md) · [23_EXECUTION_PLAYBOOK_2026-11-04.md](23_EXECUTION_PLAYBOOK_2026-11-04.md).

- **Baseline antes de preservação:** `develop@da3d4a61b7dd07f209826962b7f268caa5a12b4b`; CI [41827440760](https://github.com/rightware-corporations/jarvis/actions/runs/41827440760) PASS. Os commits subsequentes nesta ronda documentam o histórico e devem ter CI verificado separadamente.
- **Referências arquivadas integralmente:** [handoff anterior à selecção Wyzer](archive/PRE_WYZER_HANDOFF_2026-11-04.md) (**obsoleto**), [JAR-DEV-SKILLS-02 Claude](reference/CLAUDE_SKILLS_AUDIT_2026-11-04.md), [validação v0.1.0](reference/CLAUDE_PLUGIN_VALIDATION_V010_2026-11-04.md), [draft CLAUDE.md original](reference/CLAUDE_ORIGINAL_DRAFT_2026-11-04.md) e [V2](reference/CLAUDE_REVIEW_V2_DRAFT_2026-11-04.md). Drafts NÃO estão em vigor.
- **Claude:** plugin `rightware-jarvis-dev` v0.1.0 com nove skills **confirmado visualmente instalado** pelo operador; auditoria revelou `pyside6-desktop` com permissões `Read/Edit/Write/Bash/Grep/Glob`; v0.1.1 restringida e revisão do `CLAUDE.md` são tarefas pendentes. Não afirmar que foram concluídas sem novo output.
- **Frontend:** `adewaskar/jarvis@1c4016a...` é o **candidato visual**; `bridge/server.mjs` / Anthropic devem ficar de fora. A hipótese Qt/QWebEngine/QWebChannel NÃO foi testada. O utilizador exige primeiro ver screenshots **reais** no Chromium.
- **Manus:** recebeu/receberá o prompt de preview do frontend exclusivamente Vite, sem bridge/IA externa, para entregar PNGs, galeria e consola com mocks marcados. **Nenhuma captura real foi recebida ou validada neste handoff**.
- **Próxima avaliação RIGHTWARE:** rever resultados Manus e Claude; aprovar a política de patches, o `CLAUDE.md` e só então autorizar POC M0. **Sem instalação/deploy/mudança de código nesta preservação.**

