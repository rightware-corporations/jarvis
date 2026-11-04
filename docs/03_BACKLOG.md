# 03 — Backlog de execução

Legenda: [x] documentação/implementação verificada; [ ] pendente; cada teste só conta com logs de execução.

## P0 — Fundação e controlo
- [x] `JAR-P0-01` Escolher Wyzer `v0.3.1` e fixar commit.
- [x] `JAR-P0-02` Usar `rightware-corporations/jarvis` sem alterar website VEXEL.
- [x] `JAR-P0-03` Definir arquitectura, riscos e critérios de aceitação.
- [x] `JAR-P0-04` Criar branch `develop`; manter `main` estável.
- [x] `JAR-P0-05` Importar 182 ficheiros fonte/texto upstream, MIT/NOTICE e manifesto; excluir 44 binários até revisão.
- [x] `JAR-P0-05A` Comparar hashes SHA de todos os 182 importados — 182/182 iguais.
- [x] `JAR-P0-06A` Confirmar importação/instanciação headless no GitHub Ubuntu (run 41813747553).
- [ ] `JAR-P0-06B` Mapear todas as dependências específicas de Windows e a execução do modelo real.
- [x] `JAR-P0-07` Criar composição lab sem coding agent, shell, browser ou ferramentas do Windows.
- [x] `JAR-P0-08A` Executar cinco testes de contrato headless em runner remoto — 5 PASS.
- [ ] `JAR-P0-08B` Expandir testes de confirmação, cancelamento, concorrência e protecção multiutilizador.
- [x] `JAR-P0-09` GitHub Actions: SHA 182/182, compilação e 5 testes headless PASS, run 41813747553.
- [x] `JAR-P0-10` Eliminar branch temporária `feat/wyzer-v031-core-import` por GitHub Actions run 41814286015 PASS; remover workflow privilegiado depois. Verificadas apenas `main` e `develop`.

## P1 — Laboratório remoto
- [x] `JAR-P1-00` Criar factory headless com registry vazio e memória por subject.
- [x] `JAR-P1-01A` Criar API headless autenticada em código (token em header, sessions, limite de pedidos); CI pendente.
- [x] `JAR-P1-01B` CI remoto: testes API de autenticação, sessões, limites, isolamento básico e falhas sanitizadas PASS (run 41815677923).
- [ ] `JAR-P1-01C` QA de segurança adicional com preview HTTPS, concorrência e multiworker.
- [ ] `JAR-P1-02` Simulador controlado de tarefas de computador; proibição verificável de operações reais.
- [ ] `JAR-P1-03` Integrar Ollama real auto-hospedado e testar function calling, segurança e latência.
- [x] `JAR-P1-04A` Implementar shell web próprio VEXEL Jarvis com chat, estado, diagnostics e Inter; não inclui voz activa.
- [ ] `JAR-P1-04B` Testar UI com modelo real, adicionar microfone/TTS seguro quando prontos.
- [x] `JAR-P1-05A` Autenticação simples com token, rate-limit em memória, TTL e limites de sessões (protótipo single-operator).
- [ ] `JAR-P1-05B` Fortalecer para preview cloud: identidade, HTTPS, logs, multiworker, CSRF/origem e revisão de exposição pública.
- [x] `JAR-P1-06A` Executar 16 testes headless/API + integridade e compilação remotos PASS (run 41815677923).
- [ ] `JAR-P1-06B` Publicar preview privado HTTPS com servidor de inferência auto-hospedado e QA visual/browser.

## P2 — Português e conversa por voz
- [ ] `JAR-P2-01` STT Whisper multilingue PT.
- [ ] `JAR-P2-02` TTS português e licença.
- [ ] `JAR-P2-03` Wake word `Jarvis` legal e funcional.
- [ ] `JAR-P2-04` Confirmação `sim/não`, cancelamento, barge-in e seguimento de conversa PT.
- [ ] `JAR-P2-05` Identidade/voz/UX Jarvis para Issa.

## P3 — Entrega
- [ ] `JAR-P3-01` Escolher distribuição local/servidor/híbrida e modelo de custos.
- [ ] `JAR-P3-02` Agente Windows local seguro.
- [ ] `JAR-P3-03` QA de hardware/microfone/colunas com PC Issa autorizado.
- [ ] `JAR-P3-04` Auditoria licenças de modelos, wake, TTS e assets.
- [ ] `JAR-P3-05` Release assinada ou checksum, reversão, instruções e aceitação.

## Guardrails
- Desenvolver apenas em `develop`; promoção a `main` após revisão e testes.
- Repositório é **público**. Sem credenciais, ficheiros privados, gravações reais ou modelos não licenciados.
- Não fazer deploy público nem entregar ao Issa antes dos gates de segurança, modelo real e voz.
- Não usar PC do operador para programar, executar testes ou instalar componentes.


## Nova linha de execução derivada da auditoria arquitectural (2026-11-04)

Fonte de requisitos e evidência: [11_ARCHITECTURE_REVIEW_AND_EVOLUTION.md](11_ARCHITECTURE_REVIEW_AND_EVOLUTION.md). **Estas linhas são recomendações, não funcionalidades entregues.**

- [x] `JAR-ARCH-01` Auditar o código real e definir a árvore modular alvo sem movimentar arquivos upstream.
- [ ] `JAR-ARCH-02` Aprovar e implementar política de patch/fork que preserve upstream imutável e permita evolução com diffs auditáveis.
- [ ] `JAR-SEC-01` Serialização por sessão, identidade/session ownership, logout/revogação no backend, concorrência, quotas e isolamento multiworker; testes adversariais.
- [ ] `JAR-SEC-02` Confirmação por risco explícito/metadados de ferramentas e comandos PT, TTL e digest; negação de bypass por LLM.
- [ ] `JAR-CORE-01` Contratos estáveis do núcleo/voz/ferramentas, composição por interfaces; não refactor Big Bang.
- [ ] `JAR-VOICE-01` STT multilingue português e testes sem microfone em CI.
- [ ] `JAR-VOICE-02` ONNX Jarvis legalmente utilizável, TTS português e barge-in com testes reais.
- [ ] `JAR-MODEL-01` Testes end-to-end com Ollama real, desempenho e tool calling num host controlado.
- [ ] `JAR-MEM-01` Memória persistente, isolamento, consentimento, edição, esquecimento e continuidade.
- [ ] `JAR-API-01` Separação progressiva da API e esquemas; sem quebrar testes anteriores.
- [ ] `JAR-UX-01` Fluxos e wireframes voice-first reais (desktop) antes de redesenhar a interface.
- [ ] `JAR-WEB-01` Tokens, acessibilidade, estados e modularização do frontend; escolher framework somente por necessidade comprovada.
- [ ] `JAR-AGENT-01` Agente Windows seguro e escopado, nunca integrado no Web Lab sem gate de autorização.
- [ ] `JAR-RELEASE-01` Licenças, instalação, testes no PC Issa e aceitação de entrega.

**Ordem crítica:** arquitectura de patches → segurança de sessão/políticas → STT/LLM reais → UX/desktop → agentes e distribuição. Preferir incrementos isolados com CI e evidência PASS/FAIL.

## Pesquisa de UI voice-first e motores de voz — gates pendentes (2026-11-04)

- [x] `JAR-UX-REF-01` Registar fontes visuais, fluxos, licenças identificadas, ambiguidade dos vídeos/capturas e modos Floating / Expanded / Graph ([12](12_HUD_REFERENCES_AND_UX_VISION.md)).
- [x] `JAR-VOICE-REF-01` Auditar `debpalash/VoiceStudio` **estaticamente**: STT/TTS HTTP/WS, PT, engines, API, licenças e comparação com Wyzer ([13](13_VOICESTUDIO_STATIC_ASSESSMENT.md)).
- [ ] `JAR-UX-02` Criar fluxos e wireframes da UI nativa PySide6 para os três modos, estados reais e privacidade.
- [ ] `JAR-UX-03` Avaliar por POC e medição `QPainter/Qt Quick/QML` versus `QWebEngine + Three.js`; não adoptar React/Electron sem justificação.
- [ ] `JAR-UX-04` Verificar licenças/atribuições dos componentes visuais exactos antes de qualquer cópia.
- [ ] `VOICE-LIC-01` Matriz de modelos TTS/STT por licença de software, pesos, direitos sobre outputs, redistribuição e consentimento; **OmniVoice default não autorizado para distribuição comercial** com a evidência actual.
- [ ] `VOICE-PT-01` Definir corpus e critérios PT-MZ com Issa; testar `pt-BR`/`pt-PT`, qualidade e falsos positivos.
- [ ] `VOICE-STT-01` Adaptar Faster-Whisper multilingue existente em Wyzer antes de acrescentar VoiceStudio.
- [ ] `VOICE-TTS-01` Avaliar Kokoro PT existente e **um** segundo motor local com licenças admissíveis.
- [ ] `VOICE-API-01` Desenhar adapter opcional para endpoints VoiceStudio locais, validando segurança, erro, streaming, cancelamento, CPU/RAM e licença; sem instalar serviço agora.
- [ ] `VOICE-ARCH-01` Escolher estratégia de voz com base em evidências e não no README ou no número publicitado de línguas.


## JAR-HANDOFF-00 — Recuperação integral do dia 04/11/2026

Fonte: [21_MASTER_HANDOFF_2026-11-04.md](21_MASTER_HANDOFF_2026-11-04.md), [22_DECISION_REGISTER_2026-11-04.md](22_DECISION_REGISTER_2026-11-04.md) e [23_EXECUTION_PLAYBOOK_2026-11-04.md](23_EXECUTION_PLAYBOOK_2026-11-04.md).

- [x] Arquivar o **handoff pré-Wyzer** como histórico superado e preservar auditorias/rascunhos Claude sem os declarar vigentes.
- [x] Registar decisões da RIGHTWARE versus recomendações/hipóteses/experiências não executadas.
- [x] Criar prompt de recuperação e playbook M0/Claude/Manus.
- [ ] Verificar CI da HEAD depois desta documentação e registar SHA e runs.
- [ ] **JAR-CLAUDE-01:** receber plugin `rightware-jarvis-dev` v0.1.1 sem pré-autorização de Edit/Write/Bash na skill PySide6; validar e fazer upload na conta.
- [ ] **JAR-ARCH-02:** receber diff `CLAUDE.md` original→V2; aprovar política de patches/segurança; depois autorizar commit no `develop`.
- [ ] **JAR-HUD-00 (Manus):** obter screenshots Chromium reais da UI `adewaskar/jarvis` só frontend Vite, sem Claude Agent SDK, com galeria HTML e PASS/FAIL.
- [ ] **JAR-UX-03 M0:** **após aprovação** realizar POC Windows PySide6 + QWebEngine + QWebChannel, medir transparência, performance e focus; preparar fallback Qt nativo.
- [ ] **JAR-HUD-02:** integrar só componentes visuais licenciados após M0, sem bridge/Anthropic, e com backend Wyzer/Python.
- [ ] Continuar JAR-SEC-01/02, JAR-MODEL-01, JAR-VOICE-01/02 e JAR-RELEASE-01 mediante tarefas aprovadas (ver [playbook](23_EXECUTION_PLAYBOOK_2026-11-04.md)).

## Adenda Claude v0.1.1 / CLAUDE V3 — 04/11/2026

[Revisão técnica detalhada / estado de aceite](24_CLAUDE_V011_V3_REVIEW_AND_M0_GATE_2026-11-04.md).

- [x] **JAR-CLAUDE-01A** Receber e inspeccionar ZIP `rightware-jarvis-dev-0.1.1.zip`, validação, SHA256 e manifesto — PASS quanto à integridade interna; `allowed-tools=Read,Grep,Glob`.
- [ ] **JAR-CLAUDE-01B** RIGHTWARE substituir plugin 0.1.0 por 0.1.1 em Customize→Plugins; abrir sessão nova e confirmar as 9 skills e permissão efectiva instalada.
- [x] **JAR-ARCH-02A** Receber V3 e diff V2→V3, arquivar propostas e emitir parecer técnico.
- [ ] **JAR-ARCH-02B** Rever §4 docs/2*, §14 semântica `allowed-tools`, licença PySide6/LGPL e papel Manus; aprovar documento final e **só depois** publicar `/CLAUDE.md`.
- [ ] **JAR-HUD-00** Receber preview **real** Chromium/Playwright do frontend `adewaskar/jarvis` produzido pelo Manus, com imagens, galeria, consola e mocks explícitos.
- [ ] **JAR-UX-03A** Claude entregar plano integral M0, 31 testes/8 áreas, critérios numéricos e matriz CPU/RAM/GPU. **Não afirmar plano aprovado com base em resumo.**
- [ ] **JAR-UX-03B** RIGHTWARE autorizar smoke Windows com Python 3.11 / PySide6 6.6.1 num venv isolado; se relevante comparar 6.11.3 em outro venv e segundo hardware, preservando constraints e manifesto de origem.

## JAR-SLICE-01 — primeira fatia vertical

- [x] **JAR-SLICE-01A** Plano e auditoria da fatia (sem código).
- [x] **JAR-SLICE-01B** Núcleo testável com fakes: STT PT por composição, contrato TTS, provider injectável, máquina de estados, allowlist de 3 ferramentas, política PT `sim/não/cancela`, confirmação com digest/TTL/anti-replay, cancelamento seguro e testes de ciclo completo — **236 PASS simulados**; commits locais, sem push.
- [ ] **JAR-SLICE-01C** PC QA Windows: instalar Ollama e `qwen3.5:4b` manualmente, Faster-Whisper `small` local, inventário de vozes PT SAPI, testes reais dos seis comandos, latências, gravações **não** publicadas.
- [ ] **JAR-SLICE-01D** Activar `WindowsApplicationLauncher` (só Windows + `allow_real_windows_actions=true`) e testar Calculadora/Bloco de Notas reais, incluindo nomes localizados.
- [ ] **JAR-SLICE-01E** Orb PySide6 mínimo ligado aos sinais `UiEvent`.
- [ ] **VOICE-WAKE-01** `WAKE_WORD_BLOCKED`: escolher wake word com licença comercial ou treinar modelo próprio; até lá activação manual.
- [ ] **VOICE-TTS-LIC-01** Kokoro: rever obrigações de espeak-ng (GPL-3.0-or-later) via misaki antes de distribuir.
