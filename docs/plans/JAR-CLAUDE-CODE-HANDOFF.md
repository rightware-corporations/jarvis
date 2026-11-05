# JAR-CLAUDE-CODE-HANDOFF — passagem para Claude Code Cloud

- **Ordem:** JAR-MIGRATION-00 (RIGHTWARE, 05/11/2026)
- **Base verificada:** `develop@1104ac49a1223f549c761c81e8aa889c23a663d3`
  - CI 6/6 success: runs [42068389183](https://github.com/rightware-corporations/jarvis/actions/runs/42068389183) e [42068400340](https://github.com/rightware-corporations/jarvis/actions/runs/42068400340).
  - Os commits desta migração são posteriores e só documentais; ver a secção 16 e o relatório final.
- **Leitura obrigatória antes:** [`CLAUDE.md`](../../CLAUDE.md)
- **Legenda:**
  - **[F]** facto verificado (com fonte);
  - **[D]** decisão RIGHTWARE;
  - **[R]** recomendação;
  - **[P]** pendente.

---

## 01. Identidade do projecto
[F] VEXEL Jarvis — Issa Edition: assistente de voz em português para Windows, desenvolvido pela RIGHTWARE para um utilizador final (Issa). É construído sobre o Wyzer AI v0.3.1. O repositório canónico é `rightware-corporations/jarvis` e é **público**. Fonte: [D-001..D-003](../22_DECISION_REGISTER_2026-11-04.md).

## 02. Objectivo de negócio e de produto
[D] O assistente deve:
- ser activado pelo nome;
- conversar em português (PT-MZ);
- manter o contexto;
- responder por voz;
- executar **apenas** tarefas autorizadas;
- correr localmente, sem dependências pagas obrigatórias (D-005..D-007);
- ter uma interface própria flutuante (orb/HUD), não um chat convencional (D-008).

[F] Ainda não foi entregue nem instalado no PC do Issa. Os gates de produto A–D estão em [`04_ACCEPTANCE.md`](../04_ACCEPTANCE.md).

## 03. Arquitectura actual
[F] Fluxo:
1. activação manual;
2. captura de áudio;
3. STT Whisper PT;
4. `VoiceSession` (`jarvis/core/voice_loop.py`) sobre o orquestrador Wyzer;
5. LLM local (Ollama);
6. allowlist de 3 ferramentas com confirmação PT;
7. TTS SAPI PT.

O estado é publicado como `UiEvent` (`jarvis/ui/events.py`) para um `QueueSink`, que o Orb (`apps/desktop/`) consome na thread da GUI.

## 04. Decisões ADR
[D] [ADR-0001](../adr/0001-estrutura-do-repositorio.md) = `ARCH_APPROVED` (JAR-MIGRATION-00, D01 e D07). Decisões da migração:

| ID | Decisão |
|---|---|
| D01 | A árvore `wyzer/`, `jarvis/`, `apps/desktop`, `apps/weblab`, `configs`, `qa`, `tests*`, `docs` é final:<br>• `jarvis/` não depende de `apps/`;<br>• o weblab sem ferramentas Windows reais;<br>• a UI não duplica o orquestrador;<br>• não se reorganiza mais. |
| D02 | `docs/00`–`25` ficam como histórico; o que é novo vai para `adr/`, `plans/` e `reports/`. |
| D03 | Mantêm-se `tests/`, `tests_vexel/`, `tests_lab/` (e `tests_desktop/`); não há `tests_rw`. |
| D04 | `configs/jarvis_slice.toml`; sem configuração privada, credenciais, transcrições ou modelos no repositório. |
| D05 | SQLite em `%LOCALAPPDATA%\VEXEL\Jarvis\`, com código em `jarvis/memory/`: **só direcção futura**, não se implementa. |
| D06 | Manutenção de CI (Node 20 → 24, visibilidade do pytest) permitida no futuro, como ordem própria. |
| D07 | Estado do ADR-0001 actualizado, com histórico preservado. |

[P] ADRs seguintes previstos no ADR-0001:
- renderer do frontend (M0);
- modelo local (G9);
- TTS (G7);
- política de patches do Wyzer (JAR-ARCH-02).

## 05. Estrutura do repositório
Ver [`CLAUDE.md` §2](../../CLAUDE.md) e a skill `jarvis-repository` §3. [F] Os documentos de instruções para sessões Claude Code são:
- `CLAUDE.md`;
- `.claude/rules/` (architecture, git-policy, security, testing);
- `.claude/skills/` (jarvis-repository, jarvis-quality-gates, jarvis-windows-voice).

## 06. Proveniência e integridade do Wyzer
[F] Origem: `XtraWyze/Wyzer-Ai`, tag `v0.3.1`, commit `db83c085feca32d3c091361165cb9ac7ecadafe0`. Licença MIT ([`NOTICE.md`](../../NOTICE.md), [`UPSTREAM_PROVENANCE.md`](../../UPSTREAM_PROVENANCE.md)).
- Foram importados 182 ficheiros e excluídos 44 binários.
- `scripts/verify_import.py` compara o blob SHA por caminho → 182/182 em `1104ac4` (local e nos jobs `source-integrity` e `windows-python`).
- Os ficheiros protegidos são os do manifesto (inclui `.gitignore`, `pyproject.toml`, `wyzer.toml`, `installer/`, `tests/`).

## 07. Capacidades implementadas (código + testes com fakes; CI verde)
[F] Todas com rótulo IMPLEMENTADO, provadas com fakes:
- **Sessão de voz:** turnos com geração e lock, interrupção e cancelamento seguro.
- **PT:** normalização, vocativo, `sim/não/cancela`.
- **Confirmação:** digest, TTL, anti-replay, fail-closed se a pergunta não for falada.
- **Estado de acção:** `ActionStatus` com filtragem de afirmações falsas.
- **Allowlist** de 3 ferramentas.
- **Máquina de estados de UI:** 9 estados, ordenada e thread-safe.
- **Runtime:** `--text`, `--voice`, `--diagnose [--json]`, `--check-config`; preflight sem processos.
- **Preflight PowerShell** read-only.
- **Orb Desktop MVP:** 9 estados vectoriais, demo, snapshots, high-DPI, encerramento verificado.
- **Kit QA:** `DEMO_KIT.md`, `latency_summary.py`, corpus PT-MZ v1 com 20 frases.

Fonte: [relatório MISSION-02-CONT](../reports/2026-11-05_JAR-MISSION-02-CONT.md).

## 08. Capacidades simuladas (não provadas em hardware)
[F] Continuam simulados ou não testados:
- LLM real (Ollama + `qwen3.5:4b`);
- STT Whisper `small` com microfone;
- voz SAPI PT;
- latência real;
- abertura real de Calculadora/Bloco de Notas (lançador simulado; 01D desligado);
- Orb ligado a uma sessão real (hoje só a `DemoDriver`).

Nenhuma destas capacidades pode ser declarada real com base em testes.

## 09. Runtime Windows
[F] O job `windows-python` (runner `windows-latest`, Python 3.11, cp1252, LF) corre a integridade, os testes, `--check-config`, `--diagnose` (exit 3 com as ausências esperadas, validadas por `qa/windows/ci_expect_diagnose.py`) e o preflight PowerShell 5.1 no runner, com verificações de efeitos colaterais e identificadores.

[F] Defeito real encontrado e corrigido: `platform.*` lançava `cmd /c ver` (commit `e031f60`).

[P] O PC de QA físico ainda não foi usado.

## 10. Estado do Ollama
[F] Configurado (`configs/jarvis_slice.toml`):
- `provider = "ollama"`, `model = "qwen3.5:4b"`, endpoint `127.0.0.1:11434`;
- `auto_start = false`.

Nunca foi instalado nem testado. No CI é a ausência esperada `OLLAMA_UNREACHABLE`. [P] G3/G4 da 01C.

## 11. Estado do STT/TTS
[F] Configuração:
- STT: `faster_whisper`, modelo `small` multilingue, CPU int8, `download_root = .wyzer/models` (nunca descarregado; `STT_MODEL_MISSING` no CI).
- TTS: `windows_system` (SAPI), preferências `pt-PT` e `pt-BR`. A disponibilidade de voz PT não está verificada (`PT_VOICE_MISSING` no runner).
- Wake word: `WAKE_WORD_BLOCKED`, activação manual.

[P] Pendentes:
- G5, G6 e G7;
- VOICE-WAKE-01;
- VOICE-TTS-LIC-01 (Kokoro/espeak-ng GPL).

## 12. Estado do Orb
[F] MVP em `apps/desktop/orb/` (PySide6-Essentials 6.6.1). O job `desktop-orb` corre em Ubuntu e Windows, com 87 testes, snapshot de cada estado, demo de 3 s e artefacto de imagens.

[F] Não está ligado ao `VoiceSession` real. A direcção visual definitiva ainda depende de revisão de design e do M0 (ADR-0002).

## 13. Estado do Web Lab
[F] `apps/weblab/` (FastAPI, `apps.weblab.api:app`) é laboratório, não produto. Tem token, sessões, limites e 16 testes, e não tem ferramentas Windows reais.

[P] Por fazer: endurecimento para preview público (JAR-P1-05B). Não há deploy.

## 14. Fronteiras de segurança
Fonte: [`.claude/rules/security.md`](../../.claude/rules/security.md). Os pontos essenciais:
- acções reais desligadas;
- confirmação obrigatória;
- sem shell nem subprocessos;
- local e gratuito;
- wake word bloqueada;
- sem dados pessoais no repositório público.

## 15. QA e CI
- [F] Workflow `.github/workflows/source-integrity.yml`, com 6 jobs (lista em [`CLAUDE.md` §3](../../CLAUDE.md)). Todos usam `persist-credentials: false`.
- [F] Contagens em `1104ac4`: `tests_vexel` 443, `tests_lab` 16, `tests_desktop` 87.
- [F] Os avisos de Node 20 nas actions são conhecidos (JAR-CI-NODE24).
- [R] A visibilidade do resumo do pytest (por causa do `addopts=-q`) pode ser melhorada numa ordem D06.

## 16. Últimos commits verificados

| SHA | Conteúdo | CI |
|---|---|---|
| `fb9f1ef` | MISSION-02: última alteração de código | 6/6 ([42067632566](https://github.com/rightware-corporations/jarvis/actions/runs/42067632566), [42067646847](https://github.com/rightware-corporations/jarvis/actions/runs/42067646847)) |
| `1104ac4` | Relatório final da MISSION-02 | 6/6 ([42068389183](https://github.com/rightware-corporations/jarvis/actions/runs/42068389183), [42068400340](https://github.com/rightware-corporations/jarvis/actions/runs/42068400340)) |
| *(JAR-MIGRATION-00)* | `CLAUDE.md`, `.claude/`, este handoff, estado do ADR-0001 | ver [relatório final](../reports/README.md) |

## 17. PR #2
[F] `develop` → `main`, **aberto e em Draft**.
- Base: `main@10aa464`.
- Head: segue `develop`.

[D] Não se fecha nem se funde sem decisão RIGHTWARE. Cada push para `develop` gera também um run de `pull_request`.

## 18. Dependências e licenças

| Componente | Versão / estado | Licença | Nota |
|---|---|---|---|
| Wyzer AI | v0.3.1 importado | MIT | imutável |
| Python | 3.11 | PSF | — |
| pydantic, psutil, fastapi, httpx, uvicorn, pytest | intervalos do workflow | MIT/BSD | só os do CI |
| PySide6-Essentials | 6.6.1 (constraint do Wyzer) | LGPL-3.0 / GPL | ligação dinâmica, sem modificações, atribuição |
| tzdata, sounddevice | 2025.2, 0.5.3 (só no CI Windows) | Apache-2.0, MIT | — |
| Ollama + `qwen3.5:4b` | não instalados | MIT / Apache-2.0 (por confirmar no G3) | instalação manual no PC de QA |
| faster-whisper `small` | não descarregado | MIT (por confirmar no G2) | — |
| Kokoro (TTS alternativo) | não usado | — | espeak-ng GPL-3.0-or-later: VOICE-TTS-LIC-01 |
| Wake word `hey_jarvis` | **bloqueada** | sem licença comercial aprovada | VOICE-WAKE-01 |

## 19. Bloqueadores actuais
1. [P] Não há PC de QA Windows com acesso nesta fase. Tudo o que é real (G1–G10) espera por uma pessoa autorizada.
2. [P] Não há wake word licenciada (activação manual).
3. [P] A voz PT SAPI no PC de QA não está confirmada.
4. [P] Licença do Kokoro/espeak-ng por rever.
5. [P] As actions do CI usam Node 20 (aviso, não falha).
6. [P] Permissões de push da sessão Cloud por verificar (secção 21).

## 20. Roadmap (ordem recomendada [R]; nada iniciado)
1. JAR-SLICE-01C (QA real G1–G10, por uma pessoa, no PC de QA).
2. JAR-SLICE-01E-WIRE (Orb ↔ `VoiceSession`).
3. JAR-SLICE-01D-EVID e depois 01D (lançador real).
4. JAR-CI-NODE24 (manutenção D06).
5. M0 / ADR-0002 (renderer do HUD).
6. JAR-ARCH-02 (patches do Wyzer).
7. JAR-MEM-01 (SQLite, D05).
8. JAR-RELEASE-01.

O backlog completo está em [`03_BACKLOG.md`](../03_BACKLOG.md).

## 21. Política operacional Claude Code Cloud
[D] Papéis dos ambientes:
- **GitHub** é a fonte de verdade.
- **Claude Code Cloud** é o ambiente principal de engenharia.
- **GitHub Actions** valida.
- O **PC Windows** serve só para testes físicos.
- O **chat normal** fica para a estratégia.

[D] Primeira acção de cada sessão Cloud: verificar as opções e permissões **reais** do ambiente.
- Ramo de trabalho atribuído.
- Se o push para `develop` é aceite.
- Se o ambiente cria branches temporários ou PRs automáticos.
- Acesso do `gh`.
- Rede disponível.

[F] Esta sessão de migração conseguiu fazer push para `develop` com acesso concedido pela RIGHTWARE. Não está garantido que uma sessão nova tenha o mesmo acesso.

[F] Limitações observadas nesta sessão:
- `gh` com GraphQL bloqueada (`gh pr view` → HTTP 403); a REST (`gh api repos/…`) e `gh run …` funcionam.
- O `curl`/`wget` da shell só alcança a allowlist da rede.

[F/ANUNCIADO] Relatos públicos indicam que sessões Claude Code na web podem limitar o push a branches `claude/*`. Não foi verificado em documentação oficial nesta sessão.

[D] A política de dois ramos mantém-se. Se o ambiente não permitir respeitá-la:
- não se contorna (sem remotes reescritos, tokens manuais ou force);
- a sessão pára e apresenta alternativas à RIGHTWARE: ver [`git-policy.md`](../../.claude/rules/git-policy.md).

## 22. Skills e rules

| Ficheiro | Carregamento |
|---|---|
| `CLAUDE.md` | sempre |
| `.claude/rules/git-policy.md`, `security.md` | sempre (sem `paths`) |
| `.claude/rules/architecture.md`, `testing.md` | quando se lêem ou editam ficheiros nos `paths` |
| `.claude/skills/*/SKILL.md` | só a descrição até a skill ser invocada |

[F] Formato confirmado na documentação oficial do Claude Code:
- skills com frontmatter `name`, `description` e `when_to_use`;
- rules com `paths` opcional.

As skills não declaram `allowed-tools` (que pré-aprova, não restringe) nem executam comandos destrutivos. Não foram copiados skills ou plugins de terceiros.

[F] O plugin `rightware-jarvis-dev` é da RIGHTWARE. A instalação da v0.1.1 ficou pendente em JAR-CLAUDE-01B.

## 23. Recuperação de sessão
Seguir [`CLAUDE.md` §11](../../CLAUDE.md) e a skill `jarvis-repository`.

Estado esperado:
- só `main` e `develop`;
- PR #2 Draft;
- 182/182;
- CI verde da HEAD.

Se uma missão foi interrompida:
- o trabalho local não publicado só conta depois de passar pelos gates;
- o publicado nunca se reescreve;
- o último relatório em `docs/reports/` é o ponto de retoma.

## 24. Próxima missão recomendada (identificada, **não executada**)
[R] **JAR-SLICE-01C — passo 1 do `DEMO_KIT` (G1, inventário read-only)** no PC Windows de QA autorizado, executado por uma pessoa.

O Claude prepara as instruções e revê a evidência sanitizada.

Alternativa sem hardware: **JAR-CI-NODE24** (D06), uma ordem de manutenção pequena.

A 01E-WIRE só depois de G7/G8. A escolha cabe à RIGHTWARE.

## 25. Acções que exigem aprovação explícita da RIGHTWARE

**Git e repositório:**
- push para `develop` fora de uma ordem que o autorize;
- qualquer alteração a `main`, merge ou fecho do PR #2, ou a sua saída de Draft;
- criar branches, worktrees ou PRs; force push; reescrever histórico; apagar refs.

**Código protegido e arquitectura:**
- alterar ficheiros do manifesto Wyzer;
- nova política de patches;
- reorganizar a árvore, novo ADR, mudança de arquitectura.

**Ferramentas, runtime e dados:**
- activar `allow_real_windows_actions`, o lançador real ou ferramentas novas;
- ferramentas reais no Web Lab;
- instalar modelos, Ollama ou dependências pesadas; microfone, GPU ou áudio reais;
- wake word;
- implementar a memória/SQLite.

**Externos e privacidade:**
- APIs pagas e SDKs comerciais;
- copiar código, assets, skills ou plugins de terceiros;
- qualquer acção no PC do Issa;
- publicar evidência de QA, áudio ou transcrições;
- deploy público.

**Missões:** iniciar qualquer missão nova, incluindo a da secção 24.
