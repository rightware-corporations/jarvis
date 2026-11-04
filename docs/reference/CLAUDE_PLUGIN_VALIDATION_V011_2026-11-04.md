# Validação — rightware-jarvis-dev 0.1.1

**Data:** 2026-11-04 (Africa/Maputo) · **Decisão de origem:** RIGHTWARE JAR-ARCH-02, ponto 2 · **Resultado global: PASS (1 aviso não bloqueante)**

**Pacote:** `rightware-jarvis-dev-0.1.1.zip`, 100 834 bytes, SHA-256 `919e1e3acd589f95f749d056b59baabf292cfb2cbe8eb10882612c300ec577f4`, 40 ficheiros. Substitui 0.1.0 (`9f9ce6de…`).

## Alteração

| ID | Ficheiro | Antes (0.1.0) | Depois (0.1.1) |
| --- | --- | --- | --- |
| RW-JDEV-0001 | `skills/pyside6-desktop/SKILL.md` | `allowed-tools`: Read, Edit, Write, Bash, Grep, Glob | `allowed-tools`: Read, Grep, Glob |

Diferença face à cópia 0.1.0 instalada na conta: exactamente 3 linhas removidas (`- Edit`, `- Write`, `- Bash`). As listas YAML do frontmatter foram escritas sem indentação, a forma que o claude.ai guardou no upload da 0.1.0, para que o SHA-256 se mantenha depois do upload. Face ao upstream (`NerdBase-by-Stark/claude-code-skills@ae59623`): corpo byte a byte igual; após parsing YAML, só a chave `allowed-tools` difere.

## Resultados

| # | Verificação | Resultado | Evidência |
| --- | --- | --- | --- |
| 1 | Só `pyside6-desktop` declarava `allowed-tools` | PASS | `grep` em todas as 9 skills; nenhuma outra declara a chave |
| 2 | `allowed-tools` reduzido a Read, Grep, Glob | PASS | Frontmatter do ZIP extraído |
| 3 | Restantes 33 ficheiros de skills e 3 licenças idênticos ao upstream fixado | PASS | `PROVENANCE.json` regenerado: 34 ficheiros, 0 falhas; único `matches_upstream: false` é o patch declarado |
| 4 | Patch registado | PASS | `PROVENANCE.json` → `patches[RW-JDEV-0001]` com motivo, base de licença (MIT), diff e SHA-1 upstream original |
| 5 | Versão | PASS | `plugin.json` → `0.1.1` |
| 6 | Formato de plugin | PASS | `claude plugin validate` (Claude Code 2.1.318): **Validation passed**; `unzip -t` sem erros |
| 6a | Ícone | AVISO | `ICON_MISSING`, igual aos restantes plugins RIGHTWARE |
| 7 | Sem hooks, comandos, agentes, MCP, settings, instaladores | PASS | Pesquisa no ZIP extraído: nenhum |
| 8 | Sem executáveis nem shebangs | PASS | 0 ficheiros com bit de execução, 0 `#!` |
| 9 | Sem APIs pagas | PASS | 0 imports `anthropic`/`openai`, chaves ou endpoints pagos |
| 10 | Sem duplicação com outros plugins | PASS | Nenhum nome das 9 skills existe noutros plugins da conta |
| 11 | Integridade pelo comando do README | PASS | One-liner SHA-256 sobre o ZIP extraído |
| 12 | Repositório Jarvis intacto | PASS | `git status` limpo; remoto só `main` e `develop` |
| 13 | Nada instalado | PASS | Nenhum upload nem `claude plugin install` executado |

## Permissões efectivas no ambiente Claude (sessão cloud claude.ai, INSPECCIONADO)

- `~/.claude/settings.json`: `{}`. Sem definições geridas (`/etc/claude-code` inexistente), portanto `allowManagedPermissionRulesOnly` não está activo e o `allowed-tools` das skills é respeitado.
- Definições do lançador: `permissions.allow = ["Skill"]`; 10 regras `deny` que protegem ficheiros do próprio ambiente; aprovação de ferramentas feita por um classificador automático (`autoMode`) com listas `allow`/`soft_deny`.
- Efeito da 0.1.0: ao invocar `pyside6-desktop`, `Edit`, `Write` e `Bash` ficavam pré-aprovados nesse turno. Efeito da 0.1.1: só leitura é pré-aprovada; edição e terminal voltam ao fluxo normal de aprovação.
- Segundo a documentação do Claude Code, `allowed-tools` pré-aprova as ferramentas apenas durante o turno que invoca a skill, não restringe as outras ferramentas, e as regras `deny`/`ask` prevalecem.
- **Não verificado:** definições do Claude Code local da RIGHTWARE (outra máquina). Aplicar a mesma leitura lá antes de usar o plugin em projecto local.

## Pós-instalação (a executar pela RIGHTWARE após o upload)

1. Remover ou substituir 0.1.0; confirmar uma só cópia de cada skill.
2. Numa sessão nova: confirmar 9 skills `rightware-jarvis-dev:<nome>`.
3. Pedir ao Claude para verificar `PROVENANCE.json` contra a cópia instalada; esperado PASS em 34/34, incluindo `pyside6-desktop/SKILL.md`.
4. Confirmar `allowed-tools: [Read, Grep, Glob]` na cópia instalada.

**Reversão:** remover 0.1.1 e carregar o ZIP 0.1.0 guardado.