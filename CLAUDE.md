# CLAUDE.md — RIGHTWARE · VEXEL Jarvis (Issa Edition)

Contexto permanente para sessões Claude Code neste repositório. É contexto, não configuração imposta: as permissões efectivas vêm das definições do Claude Code e do GitHub. Em caso de dúvida, prevalece a fonte oficial ligada aqui. Documentação em português; identificadores de código em inglês.

**Antes de qualquer alteração:** ler [`docs/plans/JAR-CLAUDE-CODE-HANDOFF.md`](docs/plans/JAR-CLAUDE-CODE-HANDOFF.md), reconciliar o estado (secção «Recuperação de sessão») e apresentar um plano à RIGHTWARE.

## 1. Identidade e papéis

- **RIGHTWARE** é a autoridade de produto: define prioridades, aprova decisões e autoriza execução, push, merge e entregas.
- **VEXEL Jarvis — Issa Edition** é o produto. É um assistente de voz em português, local, para Windows, entregue a um utilizador final (Issa).
- **ChatGPT** é arquitecto e revisor. Não aprova em nome da RIGHTWARE.
- **Claude** é o engenheiro de implementação. Implementa ordens identificadas (`JAR-…`), testa e documenta com evidência.
- **Manus** serve apenas para preview Chromium e capturas de ecrã.
- O frontend `adewaskar/jarvis` continua a ser apenas um candidato visual até a RIGHTWARE o avaliar.

## 2. Arquitectura (aprovada: ADR-0001, `ARCH_APPROVED`)

Fonte: [`docs/adr/0001-estrutura-do-repositorio.md`](docs/adr/0001-estrutura-do-repositorio.md). É uma aplicação de desktop Windows local, não um serviço web.

| Pasta | Papel |
|---|---|
| `wyzer/` | motor upstream Wyzer v0.3.1, **imutável** |
| `jarvis/` | núcleo VEXEL (backend local):<br>• `core/voice_loop.py` (sessão de voz);<br>• `language/` (PT);<br>• `tools/allowlist.py`;<br>• `voice/`;<br>• `runtime/` (`--voice`, `--diagnose`, `--text`, `--check-config`);<br>• `ui/events.py` (contratos de UI sem Qt) |
| `apps/desktop/` | frontend do produto: Orb PySide6 (MVP; demo simulada) |
| `apps/weblab/` | laboratório web FastAPI. **Não é o produto** e nunca tem ferramentas Windows reais |
| `configs/` | `jarvis_slice.toml`, sem segredos |
| `qa/` | `windows/` (preflight PowerShell read-only, kit de demo), `corpus/`, `benchmarks/` |
| `tests/` · `tests_vexel/` · `tests_lab/` · `tests_desktop/` | upstream (imutável) · núcleo · laboratório · Orb |
| `docs/` | `00`–`25` são históricos; decisões novas vão para `adr/`, planos para `plans/` e relatórios para `reports/` |

Regras de dependência:
- `jarvis/` nunca importa `apps/`, Qt ou frameworks web.
- `apps/desktop` consome apenas os contratos de `jarvis.ui`.
- A UI não duplica o orquestrador.
- Não se reorganiza a árvore, não se volta a mover `apps/weblab/` e não se criam `tests_rw/` nem `data/`.

Detalhe em [`.claude/rules/architecture.md`](.claude/rules/architecture.md).

## 3. Ambiente e comandos

**Ambiente:**
- Python **3.11** (o mesmo do CI).
- Não há `requirements.txt`. As dependências mínimas de teste são as do workflow: `'pydantic>=2.8,<3' 'pytest>=8,<9' 'psutil>=6,<8' 'fastapi>=0.115,<1' 'httpx>=0.27,<1' 'uvicorn>=0.30,<1'`.
- Para o Orb: mais `PySide6-Essentials==6.6.1`.
- Num venv próprio. Não se instalam modelos.

**Comandos de verificação** (devem dar PASS antes de qualquer commit):

```
python scripts/verify_import.py                     # integridade Wyzer 182/182
python -m compileall -q wyzer tests scripts jarvis apps tests_vexel tests_lab
python -m pytest tests_vexel tests_lab              # 443 + 16 (sem -q extra: o pyproject já tem addopts=-q)
QT_QPA_PLATFORM=offscreen python -m pytest tests_desktop   # 87, só com PySide6
python -m jarvis --check-config
```

**CI:** `.github/workflows/source-integrity.yml`, com 6 jobs:
- `source-integrity`;
- `headless-contract`;
- `windows-preflight-parse`;
- `windows-python`;
- `desktop-orb` (ubuntu e windows).

Procedimento completo: skill `jarvis-quality-gates` e [`.claude/rules/testing.md`](.claude/rules/testing.md).

## 4. Wyzer 182/182

Os 182 ficheiros listados em [`upstream-v0.3.1-manifest.json`](upstream-v0.3.1-manifest.json) são upstream protegido. O critério é a **inclusão no manifesto**, não um padrão de pastas: inclui, por exemplo, `.gitignore`, `pyproject.toml`, `wyzer.toml` e `installer/`.

- Nunca se editam, movem ou reformatam.
- A verificação compara o blob SHA dos bytes, por isso em Windows é preciso `core.autocrlf false`.
- Qualquer evolução do Wyzer exige uma política de patches aprovada (JAR-ARCH-02).

Proveniência: [`UPSTREAM_PROVENANCE.md`](UPSTREAM_PROVENANCE.md).

## 5. Contratos de segurança (resumo — fonte: [`.claude/rules/security.md`](.claude/rules/security.md))

- `allow_real_windows_actions = false`. O lançador real (01D) está desligado.
- Não se acrescentam ferramentas fora da allowlist de 3.
- Confirmação obrigatória, com digest, TTL e anti-replay. Nunca é contornável pelo LLM.
- O estado das acções é `SIMULATED`, `SUCCEEDED`, `FAILED` ou `DENIED`. Nunca se afirma sucesso sem evidência.
- Não há shell arbitrária nem subprocessos no runtime.
- O guard de processos dos testes (`tests_vexel/conftest.py`) não se enfraquece.
- Não há APIs pagas nem SDKs comerciais obrigatórios. LLM local (Ollama em `127.0.0.1`), `auto_start = false`.
- Wake word: `WAKE_WORD_BLOCKED`. A activação é manual e os modelos `hey_jarvis` não se usam.
- Não há Hypothesis enquanto a dependência não for aprovada.

## 6. Git e publicação (fonte: [`.claude/rules/git-policy.md`](.claude/rules/git-policy.md))

**Branches:**
- Só existem `main` e `develop`. Trabalha-se em `develop`.
- `main` só muda por decisão da RIGHTWARE.
- O PR #2 (`develop`→`main`) fica em **Draft**: não se fecha nem se funde.

**Proibido sem autorização:**
- criar branches ou worktrees;
- force push;
- reescrever histórico publicado.

**Publicação:**
- Push apenas quando a ordem o autoriza.
- Depois do push, acompanhar o CI até terminar e registar os URLs dos runs.
- Commits pequenos, cada um verde. Sem segredos.

**Restrição da cloud:** se o ambiente cloud só permitir push para branches temporários (por exemplo `claude/*`), **parar e apresentar alternativas** à RIGHTWARE. Não se contorna a restrição com comandos perigosos.

## 7. Estado real vs simulado (rótulos)

Rótulos de estado (sem promover sem evidência):

| Rótulo | Evidência mínima |
|---|---|
| ANUNCIADO | fonte citada |
| INSPECCIONADO | caminho e linha ou commit |
| TESTADO | ambiente, SHA, comando, resultado e logs |
| APROVADO | decisão RIGHTWARE registada |
| IMPLEMENTADO | commit em `develop` + CI PASS dos testes relevantes |

Testes com fakes **não** provam áudio, Ollama, GPU nem Windows reais.

| Área | Estado |
|---|---|
| Núcleo de voz, PT, confirmação, allowlist, eventos de UI | IMPLEMENTADO (fakes) |
| CI Windows (Python 3.11, preflight PowerShell no runner) | TESTADO no runner `windows-latest` |
| Orb Desktop MVP (9 estados, demo, snapshots) | IMPLEMENTADO; demo simulada, **não ligado** ao `VoiceSession` real |
| Ollama + `qwen3.5:4b`, Whisper `small` com microfone, voz SAPI PT, latência | **não testado** (JAR-SLICE-01C, PC de QA) |
| Abrir Calculadora/Bloco de Notas reais | **desligado** (01D) |
| Wake word, memória/SQLite, HUD | não existe |

## 8. Privacidade (repositório público)

Nunca entram no repositório:
- credenciais, tokens ou variáveis de ambiente (também nunca impressos em logs);
- áudio, transcrições ou `voice-turns.jsonl` real;
- modelos;
- identificadores de máquinas ou utilizadores;
- dados do PC do Issa.

Regras associadas:
- `log_transcript_text = false` por omissão.
- Os relatórios só contêm informação técnica revista.
- Configuração privada fica fora do git.
- A futura memória SQLite ficará em `%LOCALAPPDATA%\VEXEL\Jarvis\`. É direcção futura (D05): **não se implementa**.

## 9. Documentação e ADR

- Não se criam novos documentos numerados.
- Uma decisão de arquitectura por ADR em `docs/adr/`. Um ADR aceite não se reescreve: substitui-se.
- Planos ficam em `docs/plans/` e relatórios de fase em `docs/reports/` (`AAAA-MM-DD_JAR-….md`). Os relatórios não se reescrevem.
- Actualizar `docs/01_CURRENT.md` e `docs/03_BACKLOG.md` quando o estado muda, com rótulo e evidência.
- Ligar à fonte; não duplicar.

**Precedência de fontes:**
1. última decisão RIGHTWARE;
2. ADR aprovado;
3. código publicado;
4. testes e CI;
5. documentação actual;
6. propostas históricas (por exemplo `docs/reference/`, `docs/archive/`).

Contradição sem evidência: marcar `REVIEW_REQUIRED` e perguntar.

## 10. Referências

- Handoff: [`docs/plans/JAR-CLAUDE-CODE-HANDOFF.md`](docs/plans/JAR-CLAUDE-CODE-HANDOFF.md).
- Estado e backlog:
  - [`docs/01_CURRENT.md`](docs/01_CURRENT.md);
  - [`docs/03_BACKLOG.md`](docs/03_BACKLOG.md);
  - [`docs/04_ACCEPTANCE.md`](docs/04_ACCEPTANCE.md).
- Decisões:
  - [`docs/22_DECISION_REGISTER_2026-11-04.md`](docs/22_DECISION_REGISTER_2026-11-04.md);
  - [`docs/adr/`](docs/adr/README.md).
- QA Windows:
  - [`docs/25_JAR-SLICE-01C_WINDOWS_QA_PLAN.md`](docs/25_JAR-SLICE-01C_WINDOWS_QA_PLAN.md);
  - [`qa/windows/DEMO_KIT.md`](qa/windows/DEMO_KIT.md).
- Relatórios: [`docs/reports/`](docs/reports/README.md).

## 11. Recuperação de sessão (sempre, antes de alterar)

1. `git status -sb`, `git rev-parse HEAD`, `git fetch origin` e `git log --oneline origin/develop -5`. A árvore deve estar limpa e HEAD deve ser igual a `origin/develop`.
2. `git branch -a`: só `main` e `develop`. Confirmar o estado do PR #2 (Draft).
3. `python scripts/verify_import.py` → 182/182.
4. Ver o último run de CI da HEAD.
5. Ler o relatório mais recente em `docs/reports/` e o handoff.
6. Se houver divergência, parar e reportar. Não "corrigir" o histórico.

## 12. Skills do projecto (`.claude/skills/`)

| Skill | Quando |
|---|---|
| `jarvis-repository` | orientação, mapa do repositório e recuperação |
| `jarvis-quality-gates` | antes de cada commit ou push, e ao acompanhar o CI |
| `jarvis-windows-voice` | trabalho no ciclo de voz, no preflight, no QA Windows ou no Orb |

Skills e plugins de terceiros:
- `allowed-tools` pré-aprova ferramentas no turno da skill. **Não restringe** permissões.
- O plugin `rightware-jarvis-dev@0.1.1`, se estiver instalado, declara Read/Grep/Glob na skill `pyside6-desktop`.
- Não se copiam skills ou plugins de terceiros sem validar a origem e a licença.
- PySide6 6.6.1 é LGPL-3.0/GPL. É permitido, mas com obrigações de conformidade: ligação dinâmica, sem modificações, com atribuição.
