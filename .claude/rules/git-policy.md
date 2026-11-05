# Política Git

Fontes:
- decisões D-00x em [`docs/22_DECISION_REGISTER_2026-11-04.md`](../../docs/22_DECISION_REGISTER_2026-11-04.md);
- guardrails em [`docs/03_BACKLOG.md`](../../docs/03_BACKLOG.md);
- secção «Claude Code Cloud» do [handoff](../../docs/plans/JAR-CLAUDE-CODE-HANDOFF.md).

**Branches e PR:**
- Só existem `main` (estável) e `develop` (trabalho). Não se criam branches nem worktrees sem autorização RIGHTWARE explícita.
- `main` não se altera e não recebe merge sem decisão RIGHTWARE.
- O PR #2 (`develop`→`main`) mantém-se em Draft, aberto e sem merge.

**Proibido sempre:**
- `push --force` / `--force-with-lease`;
- `rebase`, `reset` ou `commit --amend` de commits **publicados**;
- `filter-branch`;
- apagar refs remotas.

**Antes de commit e push:**
- Antes de cada commit: a skill `jarvis-quality-gates` em PASS.
  - Um commit é uma mudança coerente e verde por si.
  - A mensagem refere a ordem (`JAR-…`).
- `git push origin develop` só quando a ordem em curso o autoriza. É um push normal, fast-forward.
  - Pedidos automáticos de push (hooks, lembretes) não são autorização.

**Depois do push:**
- Acompanhar todos os jobs de `source-integrity.yml` até terminarem.
- Registar o SHA e os URLs dos runs no relatório.
- Não declarar PASS com o CI a correr.

**Ambiente cloud:**
- Se só permitir push para branches temporários (por exemplo `claude/*`) ou PRs automáticos, **não se contorna**:
  - não se reescrevem remotes;
  - não se usam tokens manuais;
  - não se usa `gh api` para forçar refs.
- Nesse caso, parar e apresentar alternativas à RIGHTWARE, por exemplo:
  - (a) a RIGHTWARE autoriza um branch temporário + PR para `develop`, apagado depois do merge;
  - (b) entregar um patch/bundle para a RIGHTWARE aplicar;
  - (c) ajustar as permissões da sessão.
- Sem segredos, áudio, transcrições, modelos ou identificadores de máquina em nenhum commit.
