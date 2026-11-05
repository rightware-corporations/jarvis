# Relatórios de fase

Relatórios técnicos entregues no fim de cada ordem RIGHTWARE. Cada relatório regista os SHAs, os gates, os resultados dos testes e do CI, os riscos e o estado final. Não contêm áudio, transcrições nem dados pessoais. Os ficheiros de evidência completos (logs e diffs) continuam a ser entregues em zip com cada relatório.

| Data | Ordem | Estado final | Relatório |
|---|---|---|---|
| 2026-11-05 | JAR-SLICE-01B-R01 — correcções e regressão | `CANDIDATE_PASS` | [2026-11-05_JAR-SLICE-01B-R01.md](2026-11-05_JAR-SLICE-01B-R01.md) |
| 2026-11-05 | JAR-SLICE-01B-PUB — publicação e CI | `REMOTE_CI_PASS` | [2026-11-05_JAR-SLICE-01B-PUB.md](2026-11-05_JAR-SLICE-01B-PUB.md) |
| 2026-11-05 | JAR-SLICE-01C-PRE — preparação de voz real | `PREP_READY` | [2026-11-05_JAR-SLICE-01C-PRE.md](2026-11-05_JAR-SLICE-01C-PRE.md) |
| 2026-11-05 | JAR-SLICE-01C-PUB — correcções do plano, CI Windows, publicação | `REMOTE_CI_PASS` | [2026-11-05_JAR-SLICE-01C-PUB.md](2026-11-05_JAR-SLICE-01C-PUB.md) |
| 2026-11-05 | JAR-MISSION-02-CONT — CI Windows com Python, preflight no runner, Orb Desktop MVP, kit QA, revisão independente | `MISSION_PASS` | [2026-11-05_JAR-MISSION-02-CONT.md](2026-11-05_JAR-MISSION-02-CONT.md) |
| 2026-11-05 | JAR-MIGRATION-00 — passagem para Claude Code Cloud (`CLAUDE.md`, rules, skills, handoff) | `HANDOFF_READY` | [2026-11-05_JAR-MIGRATION-00.md](2026-11-05_JAR-MIGRATION-00.md) |
| 2026-11-05 | JAR-ENGINE-01 — integração funcional do backend por HTTP, métricas LLM, `--text` simulado | `ENGINE_INTEGRATION_PASS` + `REAL_INFERENCE_PENDING` | [2026-11-05_JAR-ENGINE-01-FINAL.md](2026-11-05_JAR-ENGINE-01-FINAL.md) |

O relatório da JAR-SLICE-01B (implementação inicial) foi entregue apenas na conversa; o seu conteúdo está resumido em `docs/01_CURRENT.md` e no relatório R01.

Nomes: `AAAA-MM-DD_JAR-<ordem>.md`. Os relatórios descrevem o estado no momento em que foram escritos e não se reescrevem.
