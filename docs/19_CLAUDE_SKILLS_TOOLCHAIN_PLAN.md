# JAR-DEV-SKILLS-01 — Stack de skills para Claude (proposta de instalação)

**Data:** 2026-11-04 (Africa/Maputo)  
**Classificação:** ESTUDO E RECOMENDAÇÃO; não há skills instaladas por esta tarefa.  
**Objectivo:** configurar Claude **como engenheiro de implementação**, com ChatGPT como arquitecto/revisor e RIGHTWARE como autoridade de produto. **Claude e ChatGPT não são dependências do runtime do Jarvis.**

## 1. Referências verificadas

| Prioridade | Fonte (repositório/caminho) | Utilização no Jarvis | Observação |
| --- | --- | --- | --- |
| A | [`anthropics/claude-plugins-official`](https://github.com/anthropics/claude-plugins-official) → [`frontend-design`](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/frontend-design) | HUD intencional, componentes e animações visuais | É **skill de implementação visual**, não aprova visual final nem faz benchmarks de Qt. |
| A | [`wshobson/agents`](https://github.com/wshobson/agents) → [`python-development`](https://github.com/wshobson/agents/tree/main/plugins/python-development) | Python, async, testes, packaging, typing, desempenho | Abrange múltiplos padrões. **Não reestruturar ou actualizar o projecto só por instalação**. |
| A | [`obra/superpowers`](https://github.com/obra/superpowers) → [marketplace](https://github.com/obra/superpowers-marketplace) | Test-first, debugging, verificação e revisão | Algumas rotinas recomendam branches/worktrees/parallel coding; **incompatível sem restrições com 2 branches-only**. Proibir branches adicionais. |
| A | [`NerdBase-by-Stark/claude-code-skills`](https://github.com/NerdBase-by-Stark/claude-code-skills/tree/main/pyside6-desktop) → `pyside6-desktop/SKILL.md` | PySide6 widgets/QThread/packaging Windows | Licença MIT verificada; skill comunitária, examinar script e referências antes de instalar. |
| A | [`anthropics/claude-plugins-official`](https://github.com/anthropics/claude-plugins-official) → [`pyright-lsp`](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/pyright-lsp) | Navegação e verificação estática Python | LSP necessita `pyright-langserver` instalado e disponível no PATH. |
| B | [`anthropics/claude-plugins-official`](https://github.com/anthropics/claude-plugins-official) → [`feature-dev`](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/feature-dev) | Planeamento e implementação com gates | Adaptar para não substituir especificação e decisões RIGHTWARE. |
| B | [`wshobson/agents`](https://github.com/wshobson/agents) → [`llm-evaluation`](https://github.com/wshobson/agents/tree/main/plugins/llm-application-dev/skills/llm-evaluation) | Evals de modelos locais, ferramentas, prompt/contexto | Pode usar métricas automáticas; não obrigar "LLM as judge" pago. |
| B | [`wshobson/agents`](https://github.com/wshobson/agents) → [`fastapi-templates`](https://github.com/wshobson/agents/tree/main/plugins/api-scaffolding/skills/fastapi-templates) | DI, asyncio, contratos FastAPI | Focado em scaffolding novo; utilizar padrões selectivos, **não construir nova API de raiz**. |
| B | [`trailofbits/skills`](https://github.com/trailofbits/skills) → [`insecure-defaults`](https://github.com/trailofbits/skills/tree/main/plugins/insecure-defaults) | Detectar fail-open, permissões, tokens, serviços de rede | Auditoria, não substitui testes exploratórios. |
| B | [`trailofbits/skills`](https://github.com/trailofbits/skills) → [`supply-chain-risk-auditor`](https://github.com/trailofbits/skills/tree/main/plugins/supply-chain-risk-auditor) | Auditoria de dependências PyPI/npm e scripts de instalação | Especialmente relevante para DLLs, plugins, ASR/TTS e assets. |
| C | [`anthropics/skills`](https://github.com/anthropics/skills) → [`webapp-testing`](https://github.com/anthropics/skills/tree/main/skills/webapp-testing) | QA da UI Web/Qt WebEngine com browser | Só quando ambiente de teste estiver aprovado; não executar actualmente. |

## 2. Achados negativos / adiamentos

- [`gschoep/build-with-local-llm-ollama`](https://github.com/gschoep/build-with-local-llm-ollama) tem skill explícita de Ollama, mas contém `C:\Users\Precision\.claude\skills\ollama\config.json` hardcoded no corpo; **não instalar sem reparar portabilidade**.
- [`hadeelsharaf/claude-ollama-skills`](https://github.com/hadeelsharaf/claude-ollama-skills) serve sobretudo para delegar pequenas tarefas de **Claude Code** a modelos Ollama. Não constitui automaticamente biblioteca para o runtime do VEXEL Jarvis; não é prioridade.
- [`anthropics/skills/claude-api`](https://github.com/anthropics/skills/tree/main/skills/claude-api) orienta para SDK Anthropic, **não** Ollama. Não usar para arquitectura do runtime; Claude Code pode usá-la apenas se o trabalho for realmente Anthropic SDK.
- Não instalar todos os 94 plugins do `wshobson/agents`; não copiar 185 skills indiscriminadamente.
- `security-guidance` oficial da Anthropic inclui hooks e revisões LLM do diff/commits. Precisa de consentimento explícito para leitura e envio de código e pode acrescentar consumo de quota Claude durante **desenvolvimento**. Em Jarvis, optar por auditoria estática inicialmente.
- `Superpowers` usa fluxos que podem encorajar branches, worktrees e paralelismo. Restringir esses fluxos pelo contrato específico do projecto.

## 3. Comandos de instalação encontrados nas fontes, para **execução futura depois de revisão**

### Plugins oficiais Anthropic (marketplace normalmente disponível por omissão)
```text
/plugin install frontend-design@claude-plugins-official
/plugin install pyright-lsp@claude-plugins-official
/plugin install feature-dev@claude-plugins-official
```

### Superpowers
```text
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

### wshobson/agents
```text
/plugin marketplace add wshobson/agents
/plugin install python-development@claude-code-workflows
```

Skills individuais de `wshobson/agents` podem ser seleccionadas com `npx skills add wshobson/agents --skill llm-evaluation -a claude-code`, **depois de analisar o SKILL.md**.

### Trail of Bits
```text
/plugin marketplace add trailofbits/skills
```
Escolher apenas `insecure-defaults` e `supply-chain-risk-auditor` após conferir a instalação `/plugin`.

### PySide6 comunitária
Recomendar instalação **selectiva** da pasta `pyside6-desktop/`, com `SKILL.md` e `references/` juntas. Não executar `curl | bash` nem script `install.sh` sem revisão de conteúdo, SHA e alterações pretendidas.

**Claude Desktop Chat:** a interface suporta skills/plugins por Customize → Skills/Plugins; executar comandos de instalação local e trabalhar no checkout requer Claude Code ou Cowork com permissões adequadas. Não confundir colar URL com instalar.

## 4. Skills RIGHTWARE propostas (a criar depois de fixar contratos)

Criar skills **project-local** em `.claude/skills/`, mantidas em Git, só quando o contrato estiver definido:

- `jarvis-wyzer-integrator`: upstream 182/182 hashes, patches rastreáveis, fronteiras de módulos, regressões; preservar apenas `main` e `develop`.
- `jarvis-voice-pt`: wake Jarvis, faster-whisper PT, Kokoro TTS, avaliação de alternativos, VAD, estados, interrupção, licenças/vozes e consentimento. Proibir assumir pt-MZ validado sem corpus de voz e testes.
- `jarvis-hud-desktop`: UI Qt PySide6, QWebEngine/QML POC, Floating/Expanded/Graph, estados verdadeiros, acessibilidade, CPU/RAM/GPU/fps, overlay sem roubar foco, privacidade.
- **Opcional futuro:** `jarvis-ollama-runtime`: protocolos Ollama, ferramentas, streaming, recursos e avaliações; não instalar outro agent runtime como dependência.

## 5. Política de segurança e execução para Claude

1. **Somente duas branches:** `main` estável, `develop` de engenharia. **Sem branch/worktree adicional**, push forçado, merge e release sem autorização específica.
2. **Antes de instalar:** mostrar lista proposta, URL/revisão exacta, licença, conteúdo de `SKILL.md`, scripts/hook executáveis, permissões, destino global vs projecto, dependências, scripts de inicialização e risco de rede; preparar rollback.
3. **Não executar** código do Wyzer, VoiceStudio, skills de terceiros, instalações, scripts remotos, deploys, downloads de modelos ou auditorias que alterem o host sem autorização.
4. **Não incorporar** código licenciado AGPL (VoiceStudio) sem revisão jurídica, ou assets/modelos de licença desconhecida. Skills não concedem direitos adicionais.
5. **Distinguir** ANUNCIADO, INSPECCIONADO NO CÓDIGO, TESTADO, APROVADO, IMPLEMENTADO.
6. **Não recolher/compartilhar** chaves, `.env`, tokens, gravações de voz, dados do Issa ou credenciais de conectores.
7. Quando houver implementação: obter tarefa e SHA base, diffs, testes unitários/integrados, evidências PASS/FAIL, revisão ChatGPT e decisão final RIGHTWARE.

## 6. Passo seguinte recomendado (ainda sem execução)

Claude deve fazer **auditoria read-only da configuração de skills**, detectando conflitos de instalações existentes; apresentar no máximo 6 instalações para a primeira vaga:
`python-development`, `superpowers`, `pyside6-desktop`, `frontend-design`, `pyright-lsp` e uma skill de auditoria estática à escolha. Skills da voz/Ollama serão project-local, com especificação RIGHTWARE, não dependência automática de ferramentas externas.

**Estado:** documento de selecção; nenhuma skill efectivamente instalada, nem branch/modificação de código de produto criada.
