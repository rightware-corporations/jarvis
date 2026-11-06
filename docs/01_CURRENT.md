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

## Estado posterior — revisão da entrega Claude v0.1.1 / V3 / M0, 04/11/2026

- [24_CLAUDE_V011_V3_REVIEW_AND_M0_GATE_2026-11-04.md](24_CLAUDE_V011_V3_REVIEW_AND_M0_GATE_2026-11-04.md) é a revisão actual dos ficheiros recebidos.
- **VALIDADO neste chat:** ZIP `rightware-jarvis-dev-0.1.1.zip` 100834 bytes, SHA-256 `919e1e3acd589f95f749d056b59baabf292cfb2cbe8eb10882612c300ec577f4`; 34/34 hashes conforme manifesto, 9 skills, PySide6 pré-aprova só Read/Grep/Glob; não instalado aqui.
- **V3:** [draft arquivado](reference/CLAUDE_V3_PROPOSTA_2026-11-04.md), [diff V2→V3](reference/CLAUDE_V2_PARA_V3_2026-11-04.diff), [validação do plugin](reference/CLAUDE_PLUGIN_VALIDATION_V011_2026-11-04.md). Quatro correcções recomendadas, nenhuma aprovação de `CLAUDE.md` na raiz.
- **M0:** 31 testes/8 áreas declarados pelo Claude, plano integral e limiares não recebidos. Não há Windows aprovado ou POC executada; preview visual Chromium do Manus ainda sem evidência entregue.
- **Próximo passo real:** RIGHTWARE instalar v0.1.1 em Customize→Plugins e confirmar skills; aguardar PNG/galeria do Manus; Claude rever V3 e enviar M0 completo. Preservar os 182 ficheiros upstream.

## JAR-SLICE-01B — núcleo funcional testável (simulado), 04/11/2026

**Base:** `develop@f3e145698483f8fb67c8f12b8752a5efd29a3e9a`. Commits **apenas locais**, sem push nem merge.

- **Novo código (só ficheiros novos):** `jarvis/` (config, linguagem PT, provider PT, voz, ferramentas allowlist, estados, núcleo), `configs/jarvis_slice.toml`, `tests_vexel/`. Os 182 ficheiros do manifesto Wyzer, `pyproject.toml`, `wyzer.toml` e o instalador **não foram alterados** (verificação 182/182 PASS).
- **Composição:** `Orchestrator` Wyzer original com registry fechado de 3 ferramentas (`get_local_time`, `get_system_status`, `open_allowed_application` com enum `calculator|notepad` e `ConfirmationMode.ALWAYS`); provider injectável embrulhado por `PortugueseProvider` (instrução PT, falhas sanitizadas). STT PT por subclasse de `FasterWhisperRecognizer` (sem tocar em `whisper.py`). TTS por contrato substituível (`windows_system`, `kokoro` só vozes pt-BR, `text`).
- **Política PT determinística:** `sim`/`não`/`cancela` e variantes aprovadas por correspondência exacta; silêncio, timeout e frases ambíguas cancelam; confirmação ligada a `action_id` + digest SHA-256 + TTL; `sim` repetido não reexecuta; resposta tardia após cancelamento é descartada.
- **Estados para o orb 01E:** `OFFLINE, IDLE, LISTENING, THINKING, TOOL_RUNNING, AWAITING_CONFIRMATION, SPEAKING, MUTED, ERROR` com tabela de transições e log JSONL sem texto transcrito por defeito. HUD **não** implementado.
- **Testes:** 236 PASS em `tests_vexel` + 16 PASS em `tests_lab`, venv isolado Python 3.11.18 (pydantic 2.12.3, psutil 7.1.3, pytest 8.4.2), Linux cloud. **Tudo com fakes** (LLM, STT, TTS, lançador de aplicações, relógio, sonda do sistema).
- **WAKE_WORD_BLOCKED:** modelos openWakeWord `hey_jarvis` (CC BY-NC-SA 4.0) não usados nem descarregados; activação manual.
- **Ainda não testado com componentes reais (01C, PC QA Windows):** Ollama + `qwen3.5:4b` e tool calling real, Faster-Whisper `small` com microfone e áudio PT-MZ, vozes PT Windows disponíveis (Maria/Helia/outra), latências reais, abertura real de Calculadora/Bloco de Notas (01D, `allow_real_windows_actions` continua `false`).

## JAR-SLICE-01B-R01 — correcções e regressão, 05/11/2026

**Estado:** `CANDIDATE_PASS` local (não equivale a CI remoto PASS nem a publicação aprovada). Commits **apenas locais**; `origin/develop` continua em `f3e1456`.

- **P0 — TTS fail-closed:** `GuardedSpeech` transforma cada fala num resultado explícito (`SPOKEN`, `INTERRUPTED`, `FAILED` com fase `synthesis/playback/adapter/unknown`, `NOT_PRESENTED`). Falha de TTS → estado `ERROR` → `IDLE`, nunca «falado». Uma confirmação só fica armada depois de o pedido ter sido efectivamente apresentado; se a fala falhar, for interrompida ou não for apresentada (volume 0), a operação pendente é cancelada e um `sim` posterior não executa nada. Volume 0 passou a ser recusado na configuração. Não existe canal visual de confirmação na 01B.
- **P1 — simulação ≠ execução:** `LaunchResult` tem `status` (`SIMULATED`, `SUCCEEDED`, `FAILED`, `DENIED`) e valida que `opened=True` só existe com `SUCCEEDED`. O resultado falado de acções vem do resultado registado da ferramenta, não do texto do modelo; o modelo não consegue anunciar «Abri…» sem um `SUCCEEDED` (substituído por «Não abri nenhuma aplicação.»). Argumentos fora do esquema, aplicações fora da allowlist e ferramentas não registadas → `DENIED`.
- **P1 — eventos e concorrência:** eventos publicados em ordem estrita sob o mesmo lock; callbacks de ferramentas chegam ao event loop via `call_soon_threadsafe` (nunca à UI a partir de threads de trabalho); `QueueSink` para a futura UI Qt; eventos com `generation` e callbacks antigos descartados; resposta tardia após cancelamento não arma confirmações; falhas de sink isoladas e contadas, sem efeito nas políticas.
- **Limitação documentada:** o `InProcessExecutor` do Wyzer não interrompe uma ferramenta já em execução; cancelar depois de um efeito não o reverte. Para `open_allowed_application` o efeito só ocorre depois de um `sim` válido.
- **CI preparado (não publicado):** `.github/workflows/source-integrity.yml` passa a compilar `jarvis/`, `tests_vexel/`, `tests_lab/` e a correr `pytest -q tests_vexel` e `python -m jarvis --check-config`, sem novas dependências. Reprodução local num venv novo com a linha `pip` do workflow: todos os passos rc=0; falha injectada → rc=1.
- **Testes:** 321 PASS (305 `tests_vexel` + 16 `tests_lab`), 15 execuções consecutivas sem falhas. Continua tudo simulado: LLM, STT, TTS, lançador, relógio e sonda.

## JAR-SLICE-01C-PRE — preparação para IA e voz reais no Windows, 05/11/2026

**Estado:** `PREP_READY` local; **não equivale a funcionamento real**. Commits apenas locais sobre `develop@372c219`; nada publicado.

- **Novo modo `python -m jarvis --voice`:** activação manual pela consola (Enter / `c` / `q`) → microfone → Faster-Whisper `small` em português → Wyzer → Ollama local → voz SAPI portuguesa. Só arranca se o preflight estiver `READY`. As aplicações ficam **sempre** com o `SimulatedLauncher`; com `allow_real_windows_actions=true` o arranque é bloqueado.
- **`python -m jarvis --diagnose [--json]`:** preflight read-only. Verifica plataforma, Python 3.11, pacotes, modelo Whisper na cache (via `wyzer.install_check`), microfone (lista de dispositivos, sem abrir stream), voz PT (inventário SAPI; pt-PT antes de pt-BR), Ollama e modelo (`/api/tags` via `diagnose()` do Wyzer), política de aplicações e activação manual.
- **Reutilização do Wyzer:** captura (`WindowsSpeechRecognizer.capture_utterance`), `PowerShellSpeechRunner`, `OllamaChatProvider.diagnose()`, `install_check._whisper_present`, `WindowsSpeechSynthesizer`. Nenhum ficheiro upstream foi alterado (182/182).
- **Falhas tratadas:** falha de captura ou STT ≠ silêncio (`STT_FAILED`, estado `ERROR`, confirmação pendente cancelada); falha de TTS (R01); cancelamento durante o reconhecimento descarta o áudio e avisa o adapter; shutdown fecha os adapters; tempos por fase em `voice-turns.jsonl` (sem texto por omissão).
- **Preflight Windows para QA:** `qa/windows/Invoke-JarvisPreflight.ps1`, read-only, para revisão; **não executado**.
- **Plano de QA:** [25_JAR-SLICE-01C_WINDOWS_QA_PLAN.md](25_JAR-SLICE-01C_WINDOWS_QA_PLAN.md), com gates G1–G10, licenças, corpus PT-MZ e rollback.
- **Testes:** 399 PASS (`tests_vexel` + `tests_lab`), com fakes.

## JAR-SLICE-01B-PUB e JAR-SLICE-01C-PUB — publicação, 05/11/2026

- **01B-PUB concluída (`REMOTE_CI_PASS`):** `origin/develop` avançou de `f3e1456` para `372c219` por fast-forward. Os runs [42007778632](https://github.com/rightware-corporations/jarvis/actions/runs/42007778632) (push) e [42007788982](https://github.com/rightware-corporations/jarvis/actions/runs/42007788982) (PR #2) passaram no SHA exacto: 182/182, compilação, `tests_lab` 16/16, `tests_vexel` 305/305 e `--check-config`. As secções R01 e 01C-PRE acima, que dizem «commits apenas locais», descrevem o estado no momento em que foram escritas.
- **01C-PUB (em curso):** o plano de QA ([25](25_JAR-SLICE-01C_WINDOWS_QA_PLAN.md)) foi corrigido:
  - FIX-01: o G1 é um inventário que regista a falta de voz e de microfone como bloqueador da fase de voz; G5 e G6 só instalam e verificam; o primeiro reconhecimento real é no G7, depois de um `--diagnose` READY;
  - FIX-02: o G10 valida o rollback sem apagar nada, e a remoção (R1) exige autorização específica;
  - FIX-03: nova secção sobre o WAV temporário do Wyzer, os logs com texto e a higienização das evidências.
- **CI:** novo job `windows-preflight-parse` (Windows PowerShell 5.1, parser oficial, sem executar o script). O resultado só conta depois do run remoto.

## Organização do repositório — ADR-0001, 05/11/2026

- [ADR-0001](adr/0001-estrutura-do-repositorio.md) define as camadas:
  - backend local em `jarvis/`;
  - frontend de desktop em `apps/desktop/`, a criar só com a 01E;
  - contratos de UI em `jarvis/ui/`;
  - base de dados futura como SQLite local fora do repositório;
  - laboratório web em `apps/weblab/` (não é o produto).
- Novas pastas: `docs/adr/` (decisões), `docs/plans/` (planos) e `docs/reports/` (relatórios de fase R01, 01B-PUB, 01C-PRE e 01C-PUB).
- **Estrutura completa aplicada** (opção escolhida pelo operador):
  - `apps/desktop/` (README; código só na 01E);
  - `apps/weblab/` (o laboratório, movido de `jarvis_lab/` com `git mv`; imports, `tests_lab`, CI e documentos de instruções actualizados; entrypoint `apps.weblab.api:app`);
  - `qa/corpus/` (corpus PT-MZ v1);
  - `qa/benchmarks/` (README).
- Não se cria `data/`. As referências a `jarvis_lab/` nos documentos históricos e nos relatórios descrevem o estado de então.

## JAR-MISSION-02-CONT — 05/11/2026 (`MISSION_PASS`, com componentes simulados)

- **CI Windows real** (`windows-python`): Python 3.11 num venv; 182/182; `tests_lab` e `tests_vexel`; `--check-config`; `--diagnose` com as ausências esperadas documentadas; execução do preflight PowerShell no runner, com verificação de efeitos colaterais e de identificadores. Foi encontrado e corrigido um defeito real: o preflight lançava `cmd /c ver`.
- **Orb Desktop MVP** (`apps/desktop/`): 9 estados vectoriais com legendas PT, eventos thread-safe, demo simulada, high-DPI, encerramento verificado; job `desktop-orb` em Ubuntu e Windows. Ainda não está ligado ao ciclo de voz real.
- **Kit QA:** `qa/windows/DEMO_KIT.md`, `qa/benchmarks/latency_summary.py`; `tzdata` acrescentado ao G2 do plano 25.
- **Revisão independente:** 0 P0; o P1 e os 5 P2 foram corrigidos.
- **Testes:** 443 + 16 + 87 PASS em Linux e Windows. Relatório: [docs/reports/2026-11-05_JAR-MISSION-02-CONT.md](reports/2026-11-05_JAR-MISSION-02-CONT.md).

## JAR-MIGRATION-00 — passagem para Claude Code Cloud, 05/11/2026

- O [ADR-0001](adr/0001-estrutura-do-repositorio.md) passa a `ARCH_APPROVED` (D01/D07).
- Contexto persistente para sessões Claude Code:
  - [`CLAUDE.md`](../CLAUDE.md);
  - `.claude/rules/` (architecture, git-policy, security, testing);
  - `.claude/skills/` (jarvis-repository, jarvis-quality-gates, jarvis-windows-voice);
  - o handoff [`plans/JAR-CLAUDE-CODE-HANDOFF.md`](plans/JAR-CLAUDE-CODE-HANDOFF.md).
- Só documentação: sem alterações de runtime, testes ou Wyzer.
- Próxima missão identificada, não iniciada (handoff §24).

## JAR-ENGINE-01 — integração funcional do backend, 05/11/2026 (`ENGINE_INTEGRATION_PASS` + `REAL_INFERENCE_PENDING`)

- **Percurso por HTTP real** com o `OllamaChatProvider`/`UrllibJsonTransport` do Wyzer, sem alterações, contra um servidor Ollama falso em `127.0.0.1` (`tests_vexel/ollama_loopback.py`).
  - Cobre os 12 cenários (disponível, indisponível, modelo em falta, válido, malformado, timeout, rede, cancelamento, PT, tool call válido e não autorizado, dados inesperados) e os casos A–F.
  - Evidência `HTTP_CONTRACT_PASS`. **Nenhum modelo foi executado.**
- **Métricas:** `ProviderMeter` regista por turno `llm_ms`, `llm_calls`, `llm_eval_count`, `llm_model_ms`, `llm_failures`, `llm_cancelled` e `llm_truncated`. As falhas ficam com códigos fixos (`PROVIDER_TIMEOUT`, `PROVIDER_HTTP_404`, …), sem texto do provider.
- **`--text`** (`jarvis/runtime/text_mode.py`):
  - usa sempre o `SimulatedLauncher`;
  - faz um diagnóstico read-only do LLM;
  - escreve `text-turns.jsonl` sanitizado. É a entrada para a primeira inferência real (procedimento no relatório, §16).
- **Testes:** `tests_vexel` 491, `tests_lab` 16, `tests_desktop` 87. CI 12/12 em `eea5bac` (runs [42088773796](https://github.com/rightware-corporations/jarvis/actions/runs/42088773796), [42088782805](https://github.com/rightware-corporations/jarvis/actions/runs/42088782805)).
- **Revisão independente:** 0 P0/P1; os P2 foram corrigidos.
- **Push para `develop` a partir do Claude Code Cloud:** verificado (fast-forward).
- **Continua não testado:** Ollama real, modelo, latência real, microfone, Whisper e SAPI. Requisito do Ollama: Windows 10 22H2 ou posterior.
- Relatório: [docs/reports/2026-11-05_JAR-ENGINE-01-FINAL.md](reports/2026-11-05_JAR-ENGINE-01-FINAL.md).

## JAR-NET-01 — transporte do LLM local sem proxy, 05/11/2026 (`NET_SECURITY_PASS` + `REAL_INFERENCE_PENDING`)

- **Risco fechado:** o `UrllibJsonTransport` do Wyzer usa o opener global do urllib, que respeita os proxies do ambiente e o proxy do registo Windows (a excepção `<local>` não cobre `127.0.0.1`).
- **Correcção:** `jarvis/brain/local_transport.py` (`LoopbackJsonTransport`) é injectado em todos os providers do VEXEL (runtime e preflight).
  - Usa `ProxyHandler({})` e não segue redireccionamentos.
  - Só aceita `http` para a origem configurada, que tem de ser um IP de loopback.
  - Força `auto_start=False`.
  - O Wyzer continua 182/182.
- **Mudança de configuração:** `llm.endpoint` só aceita IPs de loopback (`127.0.0.1`/`::1`). `localhost` é recusado.
- **Evidência:**
  - um proxy hostil em loopback recebe 0 bytes do transporte VEXEL, e o transporte upstream é capturado (controlo);
  - CI 12/12 em `f31e688`; `tests_vexel` 545 no `windows-latest`, com o leitor do registo simulado.
  - **Não testado:** o proxy real do registo num PC.
- **D01:** servidores HTTP sintéticos em loopback autorizados nos testes (`.claude/rules/testing.md`).
- **Contagens:** `tests_vexel` 545, `tests_lab` 16, `tests_desktop` 87.
- Relatório, com a matriz da primeira inferência real: [docs/reports/2026-11-05_JAR-NET-01-FINAL.md](reports/2026-11-05_JAR-NET-01-FINAL.md).

## JAR-CONF-01 — confirmação repetida e invocação duplicada, 06/11/2026 (`CONFIRMATION_REPLAY_FIXED` + `READY_FOR_REAL_LLM_RETEST`)

- **Causa** (confirmada por reprodução): depois do «sim», o Wyzer executa a chamada aprovada (`SIMULATED`) e volta a chamar o LLM. O `qwen3.5:2b` repetiu a mesma `open_allowed_application`, e foi apresentada uma 2.ª confirmação. O estado `SIMULATED` perdia-se, e um 2.º «sim» executaria a acção duas vezes.
- **Correcção** (`jarvis/core/voice_loop.py`):
  - um registo, por acção do Orchestrator, dos digests já executados;
  - uma repetição (mesma acção e mesmo digest) é descartada com o «no» do Wyzer e fala-se o resultado registado;
  - outra chamada continua a precisar de confirmação própria;
  - um pedido novo do utilizador nunca herda autorizações.
  - Sem mudanças de prompt; Wyzer 182/182.
- **Testes:** 20 novos (providers controlados e o B5 por HTTP em loopback). `tests_vexel` 565, `tests_lab` 16, `tests_desktop` 87. CI 12/12 em `a75e3a5`.
- **Revisão independente:** 0 P0/P1; os P2 foram corrigidos.
- **Falta** o reteste real do CALCULATOR_APPROVE com o `qwen3.5:2b` (instruções no relatório, §8).
- Relatório: [docs/reports/2026-11-06_JAR-CONF-01-FINAL.md](reports/2026-11-06_JAR-CONF-01-FINAL.md).

## JAR-COG-01 — segurança de intenção e continuidade da conversa, 06/11/2026 (`JAR_COG_01_COMPLETE`, simulado)

- **Causas** (tabela no relatório):
  - a autorização para abrir dependia só da tool call do modelo;
  - **demonstrado:** tool calls recusadas ficavam por responder no histórico enviado ao LLM, e o modelo voltava a pedi-las («capital de Moçambique» → Bloco de Notas);
  - o guard de afirmações substituía a resposta inteira («quem es tu» → «Não abri nenhuma aplicação.»);
  - os logs não tinham identidade de sessão.
- **Correcções** (sem tocar no Wyzer, 182/182):
  - `IntentVerdict` a partir do pedido do utilizador e gate pós-modelo (`EffectGate`): sem pedido explícito não há confirmação nem execução;
  - `VexelConversation` (chamadas fechadas `NOT_EXECUTED`, sem órfãos, orçamento);
  - `session_id`/`turn_index`, `nova conversa`, telemetria sem texto.
- **Testes:** `tests_vexel` 685, `tests_lab` 16, `tests_desktop` 87; CI 12/12 em `3cd85f7`. Revisão independente: P0/P1 = 0.
- **NÃO VERIFICADO:** compreensão real do contexto pelo `qwen3.5:2b`. Reteste com `qa/kaggle/JAR-COG-01_retest_cell.py`.
- Relatório: [docs/reports/2026-11-06_JAR-COG-01-FINAL.md](reports/2026-11-06_JAR-COG-01-FINAL.md).
