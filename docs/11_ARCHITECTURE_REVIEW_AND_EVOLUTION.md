# JAR-ARCH-01 — Auditoria e plano de evolução arquitectural

**Projecto:** VEXEL Jarvis — Issa Edition (RIGHTWARE)  
**Data:** 2026-11-04, Africa/Maputo  
**Natureza:** auditoria estática e **proposta de arquitectura**; não equivale a implementação, benchmark ou aprovação de migração de ficheiros.  
**Referência:** `XtraWyze/Wyzer-Ai v0.3.1 @ db83c085feca32d3c091361165cb9ac7ecadafe0`, importado na branch `develop` de `rightware-corporations/jarvis`. Auditoria da voz: [10_VOICE_PT_AUDIT.md](10_VOICE_PT_AUDIT.md).

## 1. Decisões existentes versus recomendações

### Confirmado no projecto
- Produto: VEXEL Jarvis — Issa Edition para Issa Maulid; nome de activação «Jarvis»/«Hey Jarvis», conversação natural em português, contexto e tarefas autorizadas.
- Sem subscrição de IA nem API paga obrigatória no **runtime**. Claude/ChatGPT somente para desenvolvimento.
- Reutilizar a base Wyzer, sem reconstrução do zero. Local/servidor/híbrido será decidido após medição, sem assumir especificações do PC do Issa.
- Repositório próprio e público `rightware-corporations/jarvis`; só `main` (estável) e `develop` (engenharia); não alterar o website VEXEL.
- Importação de 182 blobs de código/texto com hashes preservados; 44 binários excluídos até validação dos direitos. Não reescrever arquivos upstream sem mecanismo de patches rastreáveis.

### Recomendações; NÃO aprovadas/implementadas
- Evoluir incrementalmente para arquitectura por **interfaces e componentes**, com núcleo Wyzer preservado, interface de voz prioritária, backend API independente, frontend, memória e executor local controlado por políticas.
- Separar empacotamento Windows e dependências headless; não activar coding agent, PowerShell, browser ou controlo Windows no serviço web.
- Definir a interface web como **painel secundário e de laboratório**; a experiência Jarvis por voz e a experiência desktop são o produto principal.
- Avaliar TypeScript/React e Vite para o frontend web **apenas quando houver necessidade de componentes complexos**; não migrar agora só por preferência tecnológica. Preservar PySide6 até validar necessidades de UI desktop.

## 2. Inventário estático por capacidade

| Domínio | Evidência no código | Limite conhecido | Prioridade |
| --- | --- | --- | --- |
| Orquestração | `wyzer/app/orchestrator.py`, `wyzer/app/cli.py` | API `Orchestrator` injectável; composição CLI cria packs Windows, coding agent habilitado no `wyzer.toml` | P0 |
| Modelos | `wyzer/brain/providers.py`, `wyzer/brain/factory.py` | Ollama e endpoints locais; nenhum teste end-to-end com modelo real na RIGHTWARE | P0 |
| Voz | `wyzer/speech/openwakeword.py`, `whisper.py`, `kokoro.py`, `wyzer/ui/desktop.py` | ONNX omitido, STT `language="en"`, TTS default inglês, cancelamento em inglês; ainda não há testes de microfone | P0 |
| Ferramentas desktop | `wyzer/tools/builtin_packs.py`, `wyzer/tools/registry.py`, `wyzer/tools/windows.py` | Packs: applications, audio, media, system, windows, browser, clipboard, desktop interaction, perception, files, diagnostics; presença ≠ funcionamento validado | P0/P1 |
| Política | `wyzer/policy/confirmations.py` | Digest/TTL nas confirmações; heurística `_CONSEQUENTIAL` e `_CREDENTIAL` predominantemente inglesas; risco de variações linguísticas | P0 |
| Conversação | `wyzer/conversation/manager.py` | Histórico limitado em RAM; estado não comprovado entre reinícios no Web Lab | P1 |
| Memória | `wyzer/memory/store.py` e `jarvis_lab/headless.py` | SQLite para factos, remoção por substring, categorias em inglês; memória não activada no `jarvis_lab/api.py` | P1 |
| API | `jarvis_lab/api.py` | FastAPI, token partilhado, TTL/rate limit **por processo**, sessões em memória, `assistant.handle()` não serializado por sessão; sem endpoint de revogação; sem produção HTTPS | P0 |
| Frontend web | `jarvis_lab/web/{index.html,lab.css,lab.js}` | Interface textual e diagnósticos; HTML/CSS/JS monolíticos, sem áudio nem automação; ficheiros servidos pela API | P1 |
| Desktop | `wyzer/ui/{desktop.py,chat_window.py,character.py}` | PySide6 é camada de apresentação, acoplada a voz Windows; UX real, acessibilidade e idioma não testados | P1 |
| Empacotamento | `pyproject.toml`, `installer/` | Python 3.11 obrigatório e dependências WinRT/pywinauto no conjunto principal; CI headless instala apenas dependências mínimas | P1 |
| QA | `tests/`, `tests_lab/`, `.github/workflows/source-integrity.yml` | 49 ficheiros de testes upstream importados, mas NÃO executados integralmente no runner RIGHTWARE; 16 contratos lab PASS em execução anterior | P0 |

## 3. Diagnósticos prioritários e evidência

1. **P0 — Concurrency/ownership.** `jarvis_lab/api.py` guarda `sessions: dict` e usa `state_lock` apenas para o lookup/TTL. Invoca `await assistant.handle(...)` fora desse lock e sem lock exclusivo da sessão. Pedidos simultâneos à mesma sessão podem intercalar estado de conversa/confirmação. **É risco de arquitectura por inspecção, não falha explorada ou reproduzida.**
2. **P0 — Autenticação e sessão.** `X-Jarvis-Lab-Token` partilhado autentica todos os clientes; `session_id` não está vinculado a uma identidade individual. Não declarar multi-tenant ou seguro para múltiplas pessoas. Quando o browser «termina sessão», o JavaScript limpa apenas o identificador local; o servidor retém a sessão até TTL.
3. **P0 — Confirmação de acções.** `ConfirmationMode.ALWAYS/NEVER` tem precedência sobre heurísticas; riscos de escrita, envio e operações destrutivas exigem metadados explícitos de risco/owner por tool e confirmação vinculada ao digest+TTL. Não confiar exclusivamente em regex, português ou julgamento do LLM.
4. **P0 — Voz.** `wyzer.toml` contém `speech.enabled=false`, `hey_Wyzer.onnx`, `small.en`; `whisper.py` força `language="en"`; o fluxo de interrupção e `orchestrator.py` estão em inglês. Detectar «Jarvis» exige modelo acústico válido, não apenas trocar strings.
5. **P1 — Memória.** `MemoryStore` guarda factos autorizados; o Web Lab cria instâncias com `storage_dir=None`, portanto sem memória persistente. Retenção e eliminação de conversas têm de ser um contrato de produto; não apresentar fact store como «memória semântica completa».
6. **P1 — Dependências/plataforma.** `pyproject.toml` distribui dependências Windows e de voz como obrigatórias; separar extras e builds sem quebrar o instalador original. O CI não confirma uma instalação completa no Windows.
7. **P1 — Documentação desactualizada.** `README.md` ainda afirma que não existe aplicação web, enquanto `jarvis_lab/web/` e `docs/09_WEB_LAB.md` mostram o protótipo e seus testes. Reconciliar README e CURRENT com **provas efectivas**, sem dizer que está pronto.
8. **P1 — Frontend.** A UI do laboratório actual é um protótipo visual, não a experiência final voice-first; há mistura de inglês e português. Organizar tokens, estados, acessibilidade, gestão de sessão e distinção entre laboratório e edição Issa.

## 4. Arquitectura lógica recomendada (destino)

```text
                  VEXEL JARVIS — ISSA EDITION
   Windows Desktop UI (voice-first)    Web UI (lab/remote, restricted)
              |                                  |
      Device voice loop                     HTTPS API
     wake -> VAD -> STT -> PT            auth -> session -> quota
              |                                  |
              +----------------+-----------------+
                               v
                     JARVIS APPLICATION CORE
               session | dialogue | state | memory
                               |
                        WYZER ORCHESTRATOR
                               |
              +----------------+-----------------+
              |                |                 |
       LLM providers       policy engine     tool registry
       Ollama primary   user/role/intent/TTL  typed capabilities
              |                |                 |
       local/private host     approvals      execution broker
                                                |
                    +---------------------------+-----------+
                    |                                       |
           Web Lab simulated tools                 Windows local agent
           NO Windows/shell access                OS tools, allowlists,
                                                  audit and explicit consent
```

**Fronteiras obrigatórias:** browser nunca recebe credenciais do Ollama, tool registry web vazio ou simulado, servidor não controla PC só por haver browser, ferramenta real necessita policy/consentimento e auditoria. Um proxy de IA em servidor não equivale a controlo local do Windows.

## 5. Árvore-alvo proposta (NÃO reflecte a árvore actual)

```text
jarvis/
├── apps/
│   ├── desktop/                 # UI local voice-first; wrapper PySide6 inicial
│   ├── web/                     # interface web remota / laboratório
│   ├── api/                     # FastAPI e contratos HTTP autenticados
│   └── agent-windows/           # futuro executor Windows, apenas sob política
├── jarvis/                       # composição/adaptação própria RIGHTWARE
│   ├── core/                     # facade, orquestração de sessão e adapters Wyzer
│   ├── voice/                    # wake, VAD, STT PT, TTS, turn-taking, barge-in
│   ├── providers/                # Ollama/local; configuração fail-closed
│   ├── memory/                   # identidade/consentimento/retention/contexto
│   ├── policy/                   # riscos, permissões, aprovações e auditoria
│   ├── tools/                    # packs tipados e mediador de execução
│   ├── schemas/                  # contratos Pydantic/OpenAPI versionados
│   └── observability/            # métricas e logs redigidos
├── wyzer/                        # código original ainda intacto, referência v0.3.1
├── jarvis_lab/                   # lab existente, manter enquanto migramos
├── tests/                        # testes originais Wyzer sem adulteração
├── tests_lab/                    # contratos CI existentes
├── tests_vexel/                  # novos contratos e integração RIGHTWARE
├── configs/                      # perfis Issa/local/web, sem segredos
├── infra/                        # hosting e packaging somente após decisão
├── installer/                    # upstream existente, preservado
├── docs/                         # auditoria, CURRENT, ADRs e critérios de aceitação
├── UPSTREAM_PROVENANCE.md
├── upstream-v0.3.1-manifest.json
├── LICENSE
└── NOTICE.md
```

**Migração incremental, não Big Bang:** primeiro adicionar módulos novos sem mover `wyzer/`, `jarvis_lab/` ou `tests/`. A árvore só se materializa por fatias acompanhadas de contract tests e paths estáveis. Antes da primeira modificação upstream, implementar patch policy/versioning: snapshot imutável separado **ou** patches auditáveis aplicados sobre tag fixa; CI prova integridade da base e alterações intencionais.

## 6. Frontend: experiência e responsabilidades

- **Desktop é produto principal:** wake/listening/thinking/speaking/awaiting-confirmation/paused/error, estado compreensível, transcript opcional, aprovações explícitas, mute/privacidade, definições de microfone, histórico, configurações.
- **Web Lab é suporte de engenharia:** sessão autenticada, mensagens, eventos de ferramenta simulada, diagnósticos, latência, logs higienizados, identidade separada.
- **Design:** linguagem VEXEL própria, hierarquia editorial, tipografia/cores em tokens; não replicar automaticamente website institucional. `Inter` já é fallback no laboratório; design system definitivo ainda por validar.
- **Não adicionar por aparência:** página de cards, analytics genéricos, marketplace ou portal não são requisitos Jarvis.
- **Frontend React/TS:** apenas recomendação sujeita a decisão posterior; primeiro definir estados, fluxos, interfaces e contratos.

## 7. Backlog priorizado com critérios de saída

| ID | Ordem | Entrega | Critério para PASS |
| --- | --- | --- | --- |
| JAR-ARCH-01 | P0 | Auditoria e mapa de módulos/risco | Documento ligado a caminhos exactos, sem declarar tarefas não testadas |
| JAR-ARCH-02 | P0 | Política de fork/patch e boundaries | CI conserva 182 hashes originais e rastreia diferenças permitidas |
| JAR-SEC-01 | P0 | Sessões/identidade, cancelamento real, lock por sessão e limites | Testes concorrentes, 401/403, revoke/expiry, cross-user; modelo simulado, zero tools OS |
| JAR-SEC-02 | P0 | Confirmation policy por risco/tipo de ferramenta | Testes para `sim/não/cancelar`, expiração, replay, deny-by-default; sem bypass |
| JAR-CORE-01 | P0 | Contratos de agent/LLM/erro/estado | Unit e integração em CI com provider fake e sem dependências Windows |
| JAR-VOICE-01 | P0 | STT Whisper multilingue + PT configurável | Testes de adaptação de parâmetros e qualidade em amostras consentidas |
| JAR-VOICE-02 | P0 | Wake word Jarvis + TTS português + turn-taking | Licenças registadas e QA com fala real; testes de falsos positivos e barge-in |
| JAR-MODEL-01 | P0 | Ollama real em host controlado | Logs de chamadas reais, streaming/function calling, timeout, recursos medidos |
| JAR-MEM-01 | P1 | Memória de sessão + factos + retenção/apagamento | Persistência, isolamento, correcção e delete comprovados |
| JAR-API-01 | P1 | Contratos API e decomposição FastAPI | HTTP versionado + esquema OpenAPI + erros padronizados; sem regressão |
| JAR-UX-01 | P1 | Fluxo desktop e wireframes reais | Estados e interacções aceites antes de refactor visual |
| JAR-WEB-01 | P1 | Modularização UI e design tokens | QA browser e acessibilidade; decidir framework por necessidade |
| JAR-AGENT-01 | P2 | Windows agent local, permissão e sandbox | Ferramentas permitidas por escopo, logs, prompts de aprovação e rollback |
| JAR-RELEASE-01 | P3 | QA no PC Issa e release | Instalação limpa, medição de hardware, áudio/PT, segurança, desinstalação |

**Dependências:** ARCH-02 antes de mexer em arquivos upstream; SEC-01/SEC-02 antes de previews remotos com ferramentas; MODEL-01 antes de declarar chat de IA real; VOICE-01/02 antes de prometer «Jarvis» falado; Windows agent nunca activado no lab.

## 8. Plano de execução recomendado

**Fase A — consolidar:** manter `main`, conservar importação íntegra e CI; actualizar documentação desfasada e adoptar patch policy; abrir testes de regressão para confirmação/sessão.  
**Fase B — tornar o Jarvis confiável:** ciclo PT de voz e confirmação, provider Ollama real, memória e states estáveis; não adicionar ferramentas de risco.  
**Fase C — experiência:** fluxos de UI desktop e protótipo web, separação gradual apps/API e design system; QA browser; não confundir estático com pronto.  
**Fase D — execução autorizada:** agente Windows local, packs mínimos, confirmação, observabilidade, testes com ambiente descartável.  
**Fase E — distribuição:** decidir local/híbrido/servidor a partir do hardware, rede, privacidade e custo observado.

## 9. Evidências e limites desta auditoria

Arquivos examinados no GitHub: `docs/02_ARCHITECTURE.md`, `docs/03_BACKLOG.md`, `docs/04_ACCEPTANCE.md`, `docs/10_VOICE_PT_AUDIT.md`, `pyproject.toml`, `README.md`, `wyzer/config.py`, `wyzer/app/{cli.py,orchestrator.py}`, `wyzer/brain/factory.py`, `wyzer/brain/providers.py`, `wyzer/conversation/manager.py`, `wyzer/memory/store.py`, `wyzer/policy/confirmations.py`, `wyzer/tools/{registry.py,builtin_packs.py}`, `wyzer/ui/desktop.py`, `wyzer/speech/{whisper.py,kokoro.py,openwakeword.py}`, `jarvis_lab/{api.py,headless.py}`, `jarvis_lab/web/{index.html,lab.css,lab.js}`.

Não foram instalados pacotes, executadas ferramentas do Jarvis nem feitos deploys nesta auditoria. Resultados CI existentes provam somente os jobs/contratos que efectivamente foram executados. As prioridades e a árvore são recomendações técnicas, não decisões aprovadas por Issa ou pela RIGHTWARE.
