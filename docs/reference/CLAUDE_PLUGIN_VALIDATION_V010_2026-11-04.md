# Validação — rightware-jarvis-dev.zip

**Data:** 2026-11-04 (Africa/Maputo) · **Base:** auditoria JAR-DEV-SKILLS-02 · **Resultado global: PASS (1 aviso não bloqueante)**

**Pacote:** `rightware-jarvis-dev.zip`, 99 600 bytes, SHA-256 `9f9ce6dec3a30d6d937bb4b47dcc0b58fd6352bc88d3cab9d62b0263b646aee6`, 40 ficheiros.

| # | Requisito | Verificação efectuada | Resultado |
| --- | --- | --- | --- |
| 1 | Só as 7 skills Python, `pyside6-desktop` e `property-based-testing` | `skills/` contém exactamente as 9 pastas | PASS |
| 2 | Sem duplicar skills instaladas | Nomes e SHA-256 de cada `SKILL.md` comparados com todos os plugins/skills da conta: 0 coincidências | PASS |
| 3 | Sem `pyright-lsp` | Ausente; plugin.json sem `lspServers` | PASS |
| 4 | SKILL.md, referências, licenças, copyright e SHAs preservados | 34 ficheiros de skills + 3 licenças idênticos ao blob Git dos commits fixados (`7e2fb55…`, `ae59623…`, `711af09…`); cópia verbatim | PASS |
| 5 | Manifesto de proveniência e README | `PROVENANCE.json` (caminho, SHA-1 blob, SHA-256 por ficheiro); `README.md` com instalação, validação e reversão | PASS |
| 6 | Formato carregável em Customize → Plugins | `.claude-plugin/plugin.json` na raiz, mesmo esquema dos plugins `rightware-*` já carregados; `claude plugin validate` (Claude Code 2.1.318): **Validation passed**; frontmatter `name` = pasta em todas as skills; `unzip -t` sem erros | PASS |
| 6a | Ícone do plugin | Validador avisa `ICON_MISSING`; afecta só a listagem no diretório público, os plugins `rightware-*` também não têm ícone | AVISO |
| 7a | Sem hooks automáticos | Nenhum `hooks/`, `hooks.json`, `commands/`, `agents/` de plugin, `.mcp.json` ou settings | PASS |
| 7b | Sem scripts de instalação ou executáveis | Tipos: 33 `.md`, 2 `.json`, 1 `.yaml`, 1 `.svg`, 3 licenças; 0 ficheiros executáveis, 0 shebangs; SVG sem `<script>`/handlers | PASS |
| 7c | Sem dependência de APIs pagas | 0 ocorrências de imports `anthropic`/`openai`, chaves de API ou endpoints pagos. `agents/openai.yaml` em `property-based-testing` é só metadado de interface (nome, ícone, cor) | PASS |
| 8 | Repositório Jarvis intacto, nada instalado, produto não executado | `git status` limpo (0 alterações); remoto só `main` e `develop`; nenhum `claude plugin install` corrido; nenhum código Jarvis executado | PASS |

**Notas de uso já registadas no README:** Python 3.11 e pip prevalecem sobre sugestões de 3.12/uv; exemplos de publicação PyPI não se aplicam; as regras de rede em `pyside6-desktop/references/architecture.md` pertencem a outra aplicação; `allowed-tools: Read` em `pyside6-desktop` apenas pré-aprova leitura.

**Pendente (após upload):** confirmar na conta que as 9 skills aparecem como `rightware-jarvis-dev:<nome>` numa sessão nova.