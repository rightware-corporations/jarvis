# JAR-MIGRATION-00 — relatório final

- **Data:** 05/11/2026
- **Modo:** FINAL_HANDOFF_AND_CODE_ONBOARDING (não destrutivo)
- **Estado final:** `HANDOFF_READY`, sobre o CI 12/12 de `9ba8098`. O commit deste relatório e da correcção da skill segue o mesmo CI; ver «Commits».

## HEAD

| Momento | SHA |
|---|---|
| Antes | `1104ac49a1223f549c761c81e8aa889c23a663d3` (= `origin/develop`, árvore limpa) |
| Depois do onboarding | `9ba8098b4f3fb047bd30031a32a52c69e8d5ce0a` |
| Depois deste relatório | commit seguinte em `develop` (só documentação) |

## Ficheiros

**Criados:**
- `CLAUDE.md` (199 linhas);
- `.claude/rules/architecture.md`, `git-policy.md`, `security.md`, `testing.md`;
- `.claude/skills/jarvis-repository/SKILL.md`, `jarvis-quality-gates/SKILL.md`, `jarvis-windows-voice/SKILL.md`;
- `docs/plans/JAR-CLAUDE-CODE-HANDOFF.md` (secções 01–25);
- este relatório.

**Modificados:**
- `docs/adr/0001-estrutura-do-repositorio.md`: estado `ARCH_APPROVED`, histórico preservado;
- `docs/adr/README.md`, `docs/plans/README.md`, `docs/reports/README.md`;
- `docs/01_CURRENT.md`, `docs/03_BACKLOG.md`;
- `apps/README.md` (estado do Orb desactualizado).

Não foi alterado nenhum ficheiro `.py`, de teste, de configuração, de CI nem do manifesto Wyzer.

## Reconciliação (fase 2)

O conteúdo foi tirado de fontes por esta ordem de precedência:
1. a ordem JAR-MIGRATION-00 (D01–D07);
2. o ADR-0001;
3. o código (`configs/jarvis_slice.toml`, `jarvis/__main__.py`, `jarvis/tools/allowlist.py`, workflow);
4. o CI;
5. os documentos 01/03/25 e os relatórios.

Da proposta histórica `docs/reference/CLAUDE_V3_PROPOSTA_2026-11-04.md` só se reaproveitaram os rótulos de estado, os critérios de recusa e os papéis. Estava desactualizada: dizia que `jarvis/` não existia e mencionava `jarvis_lab`.

As quatro correcções do documento 24 foram aplicadas no `CLAUDE.md`:
- protecção definida pelo manifesto;
- semântica de `allowed-tools`;
- licença LGPL do PySide6;
- papel do Manus e de `adewaskar/jarvis`.

Nenhum ponto ficou `REVIEW_REQUIRED`.

**Formato:** confirmado na documentação oficial do Claude Code (páginas *skills* e *memory*):
- skills em `.claude/skills/<nome>/SKILL.md` com `name`, `description` e `when_to_use`;
- rules em `.claude/rules/*.md` com `paths` opcional;
- `CLAUDE.md` com menos de 200 linhas.

## Gates

| Gate | Resultado |
|---|---|
| G1 HEAD = `origin/develop`, árvore limpa | PASS (`1104ac4`) |
| G2 apenas `main` e `develop` (local e remoto) | PASS |
| G3 PR #2 aberto, Draft, base `main@10aa464` | PASS (via REST) |
| G4 integridade Wyzer | PASS 182/182 (`SOURCE_INTEGRITY_PASS`) |
| G5 compilação | PASS |
| G6 `tests_vexel` + `tests_lab` | PASS 459 (443 + 16), Python 3.11.18 |
| G7 `tests_desktop` (offscreen, PySide6 6.6.1) | PASS 87 |
| G8 `--check-config` | PASS `CONFIG_OK` |
| G9 alterações ∩ manifesto | vazio |
| G10 varrimento de segredos | PASS; único acerto é o próprio regex documentado na skill |
| G11 links relativos dos ficheiros novos e alterados | PASS, 0 partidos |
| G12 frontmatter YAML válido (3 skills, 2 rules com `paths`) | PASS |
| G13 handoff com 25 secções | PASS |
| G14 sem alterações de runtime ou testes; sem branches novos | PASS |
| G15 CI remoto da HEAD nova | PASS 12/12 em `9ba8098` |

## Commits e CI

| SHA | Conteúdo | Runs |
|---|---|---|
| `9ba8098` | onboarding + handoff + ADR | push [42079695866](https://github.com/rightware-corporations/jarvis/actions/runs/42079695866) ✓ 6/6 · PR [42079707024](https://github.com/rightware-corporations/jarvis/actions/runs/42079707024) ✓ 6/6 |
| seguinte | este relatório + correcção `gh` REST na skill `jarvis-repository` + limitação no handoff §21 | registado no relatório entregue em zip |

PR #2: `open`, `draft: true`, `merged: false`, head = `develop`. Não foi tocado.

## Limitações do Claude Code Cloud (observadas)

- **GraphQL do GitHub bloqueada:** `gh pr view` → HTTP 403. A REST (`gh api repos/…`) e `gh run list/watch/view` funcionam. A skill foi corrigida nesse sentido.
- **Push para `develop`:** funcionou nesta sessão, com acesso concedido pela RIGHTWARE. Não está garantido numa sessão nova. Há relatos públicos, não verificados em documentação oficial, de sessões web limitadas a `claude/*`. A política e as alternativas estão no handoff §21 e em `git-policy.md`.
- **Rede da shell restrita a uma allowlist:** nenhum modelo, Ollama ou hardware é alcançável. As capacidades reais continuam a depender do PC de QA.

## Próxima missão (identificada, não iniciada)

JAR-SLICE-01C, passo 1 do `DEMO_KIT` (G1, inventário read-only), no PC de QA autorizado e executado por uma pessoa. A alternativa sem hardware é JAR-CI-NODE24. Ver o handoff §24.

## Mensagem de arranque para a primeira sessão Claude Code (não enviada)

> Estás no repositório `rightware-corporations/jarvis`, ramo `develop`. Antes de alterar qualquer ficheiro:
> 1. Lê `CLAUDE.md` e `docs/plans/JAR-CLAUDE-CODE-HANDOFF.md`.
> 2. Reconcilia o estado com a skill `jarvis-repository`: HEAD = `origin/develop`, só `main` e `develop`, PR #2 em Draft (via `gh api`), integridade 182/182, CI da HEAD verde.
> 3. Verifica as permissões reais desta sessão: se podes fazer push para `develop` ou só para branches temporários, e se o `gh` funciona.
> 4. Apresenta-me o estado reconciliado, as limitações encontradas e um plano para a próxima missão (handoff §24).
>
> Não alteres código, não faças commit nem push, e não inicies nenhuma missão até eu aprovar o plano.
