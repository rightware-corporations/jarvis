---
name: jarvis-repository
description: Orientação e recuperação no repositório RIGHTWARE VEXEL Jarvis — reconciliar HEAD, branches, PR #2, integridade Wyzer 182/182 e CI antes de qualquer alteração; mapa de onde vive cada camada.
when_to_use: No início de cada sessão, depois de uma interrupção, ou quando for preciso saber onde colocar código, testes ou documentos.
---

# jarvis-repository

Só leitura. Esta skill não altera ficheiros, não faz push e não cria branches.

## 1. Reconciliar o estado (antes de alterar)

```
git status -sb                         # árvore limpa? ramo develop?
git fetch origin
git rev-parse HEAD origin/develop      # devem coincidir
git branch -a                          # só main e develop (locais e remotos)
git log --oneline -8 origin/develop
python scripts/verify_import.py        # Wyzer 182/182
gh api repos/rightware-corporations/jarvis/pulls/2 --jq '{state,draft,head:.head.sha,base:.base.ref}'   # open, draft=true
gh run list --branch develop --limit 4
```

Notas sobre o `gh`:
- Nas sessões Claude Code Cloud, a GraphQL do GitHub está bloqueada. `gh pr view` falha com HTTP 403; usar a REST (`gh api …`), como acima. `gh run list/watch/view` funcionam.
- Se o `gh` não tiver acesso, registar a limitação e não procurar outro caminho com credenciais manuais.

**Divergências** (árvore suja, HEAD ≠ origin, ramos extra, PR não-draft, 182 ≠ 182, CI vermelho):
- parar e reportar à RIGHTWARE com a evidência;
- não "arrumar" com reset, stash drop ou force.

## 2. Ler, por esta ordem

1. [`CLAUDE.md`](../../../CLAUDE.md).
2. [`docs/plans/JAR-CLAUDE-CODE-HANDOFF.md`](../../../docs/plans/JAR-CLAUDE-CODE-HANDOFF.md).
3. O relatório mais recente em [`docs/reports/`](../../../docs/reports/README.md).
4. [`docs/01_CURRENT.md`](../../../docs/01_CURRENT.md) (fim) e [`docs/03_BACKLOG.md`](../../../docs/03_BACKLOG.md) (fim).
5. A ordem RIGHTWARE em curso (`JAR-…`).

Precedência em caso de conflito:
1. decisão RIGHTWARE;
2. ADR aprovado;
3. código publicado;
4. testes e CI;
5. docs actuais;
6. propostas históricas.

Sem evidência suficiente: `REVIEW_REQUIRED`.

## 3. Onde vai cada coisa

| Quero… | Lugar |
|---|---|
| lógica do assistente, voz, PT, ferramentas, preflight | `jarvis/<módulo>/` |
| interface de desktop | `apps/desktop/` (só via `jarvis.ui`) |
| demo web | `apps/weblab/` (sem ferramentas reais) |
| teste do núcleo / lab / Orb | `tests_vexel/` / `tests_lab/` / `tests_desktop/` |
| configuração | `configs/jarvis_slice.toml` |
| script ou kit de QA | `qa/windows/`, `qa/benchmarks/`, `qa/corpus/` |
| decisão de arquitectura | novo `docs/adr/NNNN-….md` |
| plano / relatório de fase | `docs/plans/` / `docs/reports/AAAA-MM-DD_JAR-….md` |

Nunca: ficheiros do manifesto Wyzer (`upstream-v0.3.1-manifest.json`), `data/`, novos `docs/NN_…`.

## 4. Apresentar o plano

Antes de mudar código, enviar à RIGHTWARE:
- o estado reconciliado;
- a ordem entendida;
- os ficheiros a tocar;
- os testes a acrescentar;
- os riscos;
- o que fica por fazer.

Para operações que precisam de autorização, ver a secção 25 do handoff.
