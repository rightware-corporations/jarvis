# JAR-DEV-SKILLS-02 — Auditoria de skills Claude para o Jarvis

Nov 4, 2026 · @RIGHTWARE

## Resumo executivo

**O ambiente já cobre cerca de metade do plano JAR-DEV-SKILLS-01: só faltam 4 instalações novas na primeira vaga.** Sete das skills que o documento 19 propunha instalar já estão activas e são byte-a-byte idênticas à revisão actual dos repositórios de origem (verificado com `diff -r`).

**Estado desta tarefa:** INSPECCIONADO. Nada foi instalado, executado ou alterado no repositório Jarvis. Os seis repositórios foram clonados em modo superficial para uma pasta isolada (`/home/claude/audit`) e lidos sem correr scripts nem hooks.

**Conjunto mínimo recomendado (aguarda autorização):**

| # | Skill / plugin | Fonte | Porquê agora |
| --- | --- | --- | --- |
| 1 | `pyright-lsp` | anthropics/claude-plugins-official | Verificação de tipos e navegação no `wyzer/` (mypy strict já configurado) |
| 2 | Selecção de `python-development` (7 skills) | wshobson/agents | asyncio, tipagem, erros, resiliência, recursos, desempenho, packaging |
| 3 | `pyside6-desktop` | NerdBase-by-Stark/claude-code-skills | Única skill encontrada para Qt/PySide6, QThread e PyInstaller Windows |
| 4 | `property-based-testing` | trailofbits/skills | Hypothesis para a política de confirmação, parsers PT e máquina de estados |

**Não recomendado instalar:** o plugin completo `superpowers` (hook SessionStart e skills de worktree/branch contrárias à regra de 2 branches; as 5 skills úteis já estão activas), `security-guidance` (revisão LLM em hooks), `modern-python` (shims de PATH), `llm-application-dev` completo (LLM-as-judge com SDK Anthropic) e `claude-api`.

**Correcções ao documento 19:** `frontend-design` e `supply-chain-risk-auditor` já estão instalados; `insecure-defaults` passou a ser um pipeline multi-agente (Sonnet/Opus), não uma skill leve; Superpowers está também no marketplace oficial; `python-development` assume Python 3.12+ e o Jarvis está fixado em 3.11.

**Decisão pendente antes de instalar:** em que ambiente a instalação deve ficar activa (ver secção 4). Instalar via CLI nesta sessão cloud não persiste entre sessões.

## 1. Skills já existentes no ambiente

**A conta claude.ai tem 5 plugins RIGHTWARE carregados por upload ("My Uploads", 2026-11-04) que já incluem 23 skills relevantes ao Jarvis.** Fontes: `ListPlugins`, `ListSkills`, `/mnt/skills/plugin-files/*/README.md` e `licenses/`.

| Plugin instalado | Skills relevantes para o Jarvis | Origem declarada | Igual ao upstream actual? |
| --- | --- | --- | --- |
| `rightware-engineering` | test-driven-development, systematic-debugging, verification-before-completion, brainstorming, writing-plans | obra/superpowers (MIT) | Sim, as 5 idênticas a `22f0b46` |
| `rightware-engineering` | python-testing-patterns, architecture-patterns, api-design-principles | wshobson/agents (MIT) | python-testing-patterns idêntica a `7e2fb55` |
| `rightware-security` | supply-chain-risk-auditor, semgrep, codeql, sarif-parsing, sharp-edges, differential-review, semgrep-rule-creator | trailofbits/skills (CC-BY-SA-4.0) | supply-chain-risk-auditor idêntica a `711af09` |
| `rightware-frontend` | typescript-advanced-types, vercel-react-best-practices, vercel-composition-patterns | wshobson/agents, vercel-labs | Não comparado (fora do núcleo Python) |
| `rightware-design` | impeccable, interaction-design, design-system-patterns, visual-design-foundations, web-design-guidelines | pbakaus/impeccable, wshobson, vercel-labs | Não comparado |
| skill base (`~/.claude/skills/frontend-design`) | frontend-design | anthropics (Apache-2.0) | Sim, idêntica a `plugins/frontend-design` em `fa4eb54` |
| plugin GitHub MCP | operações de repositório | GitHub (Anthropic directory) | n/d |

**Também presente nesta sessão cloud:** `pyright` e `pyright-langserver` em `/root/.local/bin`, `uv`, Node 22, Claude Code 2.1.318. O único marketplace configurado na CLI é `anthropic-plugin-directory`; `~/.claude/settings.json` está vazio (`{}`), sem hooks de terceiros.

**Sem relevância técnica para o Jarvis:** rightware-marketing, skills de redes sociais, anúncios, marca, Remotion, PSD, docx/pptx/xlsx/pdf.

**Lacunas confirmadas (nenhum dos 6 repositórios cobre):** Ollama/modelos locais, Three.js/React Three Fiber, voz PT (STT/TTS/wake word), avaliação de LLM sem API paga, regras de 2 branches.

## 2. Skills seleccionadas e justificação técnica

**Critério:** cobrir uma lacuna real do stack documentado (Python 3.11, asyncio, FastAPI, pytest, PySide6), não duplicar o que existe, sem hooks automáticos nem dependência de API paga.

| Decisão | Skill / plugin | Justificação no contexto Jarvis |
| --- | --- | --- |
| **Instalar (vaga 1)** | `pyright-lsp` | Dá diagnóstico de tipos após cada edição e navegação de símbolos no `wyzer/` (89 ficheiros) e `jarvis_lab/`. Só declara um servidor LSP; sem hooks, agentes ou comandos. |
| **Instalar (vaga 1)** | `async-python-patterns` | Risco P0 de concorrência em `jarvis_lab/api.py` (`assistant.handle()` sem lock por sessão) e loop de voz com cancelamento. |
| **Instalar (vaga 1)** | `python-type-safety` | `pyproject.toml` usa `mypy strict` com plugin Pydantic. |
| **Instalar (vaga 1)** | `python-error-handling`, `python-resilience` | Timeouts, retry e falha controlada do provider Ollama e do `SafeLabProvider`. |
| **Instalar (vaga 1)** | `python-resource-management` | Microfone, streams de áudio, modelos ONNX/Whisper e threads devem ser libertados. |
| **Instalar (vaga 1)** | `python-performance-optimization` | Medir CPU/RAM no idle, listening e HUD (JAR-UX-05). |
| **Instalar (vaga 1)** | `python-packaging` | Separar extras Windows/voz/headless (problema P1 no doc 11). |
| **Instalar (vaga 1)** | `pyside6-desktop` | QThread, QSS e PyInstaller são o núcleo do modo Floating; nenhum outro repo tem skill Qt. |
| **Instalar (vaga 1)** | `property-based-testing` | Hypothesis para `wyzer/policy/confirmations.py` (digest/TTL, sim/não/cancelar), normalização PT e invariantes de sessão. |
| Vaga 2 | `fastapi-templates` | Padrões de DI e lifespan úteis para JAR-API-01; o scaffold de raiz não é para usar. |
| Vaga 2 | `insecure-defaults` | Fail-open, segredos de fallback e permissões no Web Lab; pipeline pesado, correr só com autorização por execução. |
| Vaga 2 (opcional) | `feature-dev` | 3 agentes só de leitura (explorer, architect, reviewer); sobrepõe-se a brainstorming/writing-plans. |
| Vaga 3 | `webapp-testing` | QA browser do Web Lab/QWebEngine quando houver ambiente aprovado; o script usa `shell=True`. |
| Não instalar | `superpowers` (plugin completo) | Hook SessionStart injecta `using-superpowers`; inclui `using-git-worktrees`, `finishing-a-development-branch` e `subagent-driven-development` com scripts de workspace. As 5 skills úteis já estão activas. |
| Não instalar | `python-development` completo | O agente `python-pro` impõe "Python 3.12+" e uv; o comando `python-scaffold` cria projectos novos. |
| Não instalar | `llm-application-dev` completo | `llm-evaluation/references/details.md` usa `from anthropic import Anthropic` para LLM-as-judge. Base para uma skill interna adaptada a Ollama. |
| Não instalar | `security-guidance` | Hooks em edição/Stop/commit com revisão LLM e `ensure_agent_sdk.py`; envia diffs e consome quota. |
| Não instalar | `modern-python` | Hook SessionStart altera PATH com shims de `python`/`pip`; conflita com o instalador pip + `constraints-windows-py311.txt`. |
| Não instalar | `claude-api`, `code-review`, `commit-commands` | SDK Anthropic; comandos `gh pr` / commit-push que contornam a revisão RIGHTWARE. |

## 3. Fonte, licença e revisão

**Todas as candidatas são texto (Markdown/JSON) sem scripts executáveis, excepto as assinaladas.** Revisões = HEAD da branch por omissão em 2026-11-04, clonadas nesta auditoria; fixar estas SHAs na instalação.

| Skill | Caminho na fonte | Revisão (SHA) | Licença | Ficheiros executáveis |
| --- | --- | --- | --- | --- |
| `pyright-lsp` | [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official/tree/fa4eb54397ee2faccb6940512a19c017cb1337f3/plugins/pyright-lsp) `plugins/pyright-lsp` | `fa4eb54397ee2faccb6940512a19c017cb1337f3` (2026-11-03) | Apache-2.0 | Nenhum; a entrada do marketplace invoca `pyright-langserver --stdio` |
| 7 skills `python-development` | [wshobson/agents](https://github.com/wshobson/agents/tree/7e2fb559cf4b824b27f1fec49fe88f7511066d26/plugins/python-development/skills) `plugins/python-development/skills/<nome>` | `7e2fb559cf4b824b27f1fec49fe88f7511066d26` (2026-10-30) | MIT (plugin v1.2.4) | Nenhum (2–3 `.md` por skill) |
| `fastapi-templates` | [wshobson/agents](https://github.com/wshobson/agents/tree/7e2fb559cf4b824b27f1fec49fe88f7511066d26/plugins/api-scaffolding/skills/fastapi-templates) | `7e2fb55…` | MIT | Nenhum |
| `pyside6-desktop` | [NerdBase-by-Stark/claude-code-skills](https://github.com/NerdBase-by-Stark/claude-code-skills/tree/ae59623b0bb6e5ff5e2d6beb7878cb0640f93886/pyside6-desktop) `pyside6-desktop/` | `ae59623b0bb6e5ff5e2d6beb7878cb0640f93886` (2026-04-16) | MIT (2026) | Nenhum na pasta; `install.sh` na raiz copia para `~/.claude/skills` e não é necessário |
| `property-based-testing` | [trailofbits/skills](https://github.com/trailofbits/skills/tree/711af095215ad4ecde5b90cd1d0124b3f1c4ca9e/plugins/property-based-testing) | `711af095215ad4ecde5b90cd1d0124b3f1c4ca9e` (2026-11-02) | CC-BY-SA-4.0 (repo) | Nenhum na skill; `evals-extra/run.sh` não é carregado pela skill |
| `insecure-defaults` | [trailofbits/skills](https://github.com/trailofbits/skills/tree/711af095215ad4ecde5b90cd1d0124b3f1c4ca9e/plugins/insecure-defaults) | `711af09…` (plugin v2.0.3) | CC-BY-SA-4.0 | `workflows/audit.js` (pipeline Recon→Discover→Verify→Report) |
| `feature-dev` | [claude-plugins-official](https://github.com/anthropics/claude-plugins-official/tree/fa4eb54397ee2faccb6940512a19c017cb1337f3/plugins/feature-dev) | `fa4eb54…` (v1.0.1) | Apache-2.0 | Nenhum; agentes sem Bash/Edit |
| `webapp-testing` | [anthropics/skills](https://github.com/anthropics/skills/tree/ca45fc496a3436251f191354091d557da31c15b5/skills/webapp-testing) | `ca45fc496a3436251f191354091d557da31c15b5` (2026-10-28) | Apache-2.0 | `scripts/with_server.py` (`subprocess.Popen(shell=True)`) |
| `superpowers` (referência) | [obra/superpowers](https://github.com/obra/superpowers/tree/22f0b463e7a5e579904dd6211a520321035526f7) | HEAD `22f0b46…` v7.0.2; marketplace oficial fixa `bb92a777…` | MIT | `hooks/session-start`, `skills/subagent-driven-development/scripts/*` |

**Obrigações de licença:** MIT e Apache-2.0 exigem manter o aviso de copyright (Apache também o `NOTICE`, quando existe). CC-BY-SA-4.0 exige atribuição e que adaptações sejam partilhadas com a mesma licença: não derivar skills internas do Jarvis a partir de texto Trail of Bits, e nunca copiar esse texto para `docs/` ou código do produto. Nenhuma destas licenças cobre o runtime do Jarvis, porque as skills não entram na distribuição.

## 4. Métodos de instalação e compatibilidade

**O destino da instalação decide o método: há três destinos e só dois são duradouros.** Os plugins `rightware-*` existentes foram instalados pelo destino A, que é o que serve as sessões da app Claude onde esta auditoria corre.

| Destino | Persiste? | Quem executa | Método |
| --- | --- | --- | --- |
| **A. Conta claude.ai (Customize → Plugins → upload)** | Sim, em todas as sessões Claude (web, Desktop, cloud) da conta | Eu preparo e valido o pacote; o upload é feito por si na interface | Plugin `rightware-jarvis-dev` (.zip) com as skills fixadas por SHA, `licenses/` e `README.md` de proveniência, igual ao padrão `rightware-*` |
| **B. Claude Code local (CLI ou separador Code do Desktop)** | Sim, no `~/.claude` dessa máquina | Quem usa essa máquina | Comandos `/plugin` abaixo |
| C. Projecto (`.claude/skills/` no repo) | Sim, para todos os clones | Commit em `develop` | Fica para as skills internas (secção 6), após autorização para alterar ficheiros |
| — Esta sessão cloud via CLI | **Não**: o contentor é descartável | — | Não conta como instalação |

**Comandos para o destino B (verificados nas fontes):**

```text
# Oficial Anthropic (marketplace claude-plugins-official)
/plugin install pyright-lsp@claude-plugins-official

# Trail of Bits: adicionar marketplace e escolher só o necessário
/plugin marketplace add trailofbits/skills
/plugin install property-based-testing@trailofbits

# wshobson: NÃO instalar o plugin completo python-development;
# copiar só as 7 pastas de skills fixadas (ver procedimento abaixo)
```

**Instalação selectiva por cópia (skills sem plugin), revisão fixa:**

```bash
T=$(mktemp -d)
git clone --filter=blob:none --no-checkout https://github.com/wshobson/agents "$T/w"
git -C "$T/w" checkout 7e2fb559cf4b824b27f1fec49fe88f7511066d26 -- plugins/python-development/skills
for s in async-python-patterns python-type-safety python-error-handling python-resilience \
         python-resource-management python-performance-optimization python-packaging; do
  cp -r "$T/w/plugins/python-development/skills/$s" ~/.claude/skills/$s
done
git clone --no-checkout https://github.com/NerdBase-by-Stark/claude-code-skills "$T/n"
git -C "$T/n" checkout ae59623b0bb6e5ff5e2d6beb7878cb0640f93886 -- pyside6-desktop LICENSE
cp -r "$T/n/pyside6-desktop" ~/.claude/skills/pyside6-desktop
```

Não usar `install.sh` nem `npx skills add`: a cópia directa faz o mesmo sem executar código de terceiros.

**Compatibilidade:**

- Skills (`SKILL.md` + `references/`) funcionam em Claude Code CLI, Desktop e sessões claude.ai com plugins.
- `pyright-lsp` só tem efeito no Claude Code com LSP e `pyright-langserver` no PATH; na app claude.ai não traz benefício. Nesta sessão cloud o binário já existe.
- `pyside6-desktop` usa a chave não-padrão `filePattern` no frontmatter; é ignorada sem erro, a activação depende da `description`.
- `insecure-defaults` (vaga 2) depende do suporte a workflows/subagentes do Claude Code; não corre como skill simples.
- Superpowers, se um dia for necessário: `/plugin install superpowers@claude-plugins-official` fixa `bb92a777…`; o doc 19 indicava apenas o marketplace `obra/superpowers-marketplace`.

## 5. Dependências adicionais e riscos de segurança

**A vaga 1 não acrescenta nenhuma dependência ao Jarvis nem ao runtime; só `pyright-lsp` precisa de um binário na máquina de desenvolvimento.**

| Skill | Dependência na máquina de dev | Dependência no projecto | Risco principal | Mitigação |
| --- | --- | --- | --- | --- |
| `pyright-lsp` | `pyright-langserver` no PATH (`npm i -g pyright`) | Nenhuma | O pacote PyPI `pyright` descarrega Node na primeira execução | Instalar via npm com versão fixada; nunca adicionar ao `pyproject.toml` |
| 7 skills `python-development` | Nenhuma | Nenhuma | Texto sugere Python 3.12+, uv e reestruturação | Regra no CLAUDE.md: Python 3.11, pip + constraints, sem reestruturar por sugestão de skill |
| `pyside6-desktop` | Nenhuma | PySide6 já é extra `ui` | `references/architecture.md` traz regras de outra app (descoberta de dispositivos de rede, scan de sub-redes) | Ignorar regras de rede; considerar remover esse ficheiro na cópia (MIT permite) |
| `property-based-testing` | Nenhuma | `hypothesis` como extra `dev` quando for usada | Adicionar dependência sem tarefa aprovada | Só entra com JAR-SEC-02 e revisão |
| `insecure-defaults` (vaga 2) | Claude Code com workflows | Nenhuma | Lança vários subagentes (Sonnet + Opus) sobre o código: consumo de quota | Correr apenas sob pedido explícito, com âmbito limitado |
| `webapp-testing` (vaga 3) | Playwright + browsers | Playwright já é dependência Wyzer | `with_server.py` executa comandos com `shell=True` | Só em ambiente aprovado, comandos escritos por nós |

**Riscos transversais observados nas fontes:**

- **Branches e worktrees:** `writing-plans` (já instalada) menciona `using-git-worktrees` e revisão "whole-branch". Sem regra explícita, o Claude pode propor worktree ou branch. Mitigação: CLAUDE.md do projecto com a proibição (secção 6).
- **Hooks:** nenhuma instalação recomendada traz hooks. `superpowers`, `modern-python` e `security-guidance` trazem hooks SessionStart/Stop e ficam fora.
- **Dependência de IA no runtime:** `llm-evaluation` e `claude-api` usam o SDK Anthropic nos exemplos. Não instaladas; a skill interna de avaliação usa Ollama ou métricas determinísticas.
- **Actualizações silenciosas:** instalar por marketplace segue a HEAD. Fixar SHAs na cópia e registar no README do pacote.
- **Prompt injection via skill:** a pesquisa por padrões (curl/wget, pipes para shell, "ignore previous", alteração de settings ou permissões) nas pastas candidatas não encontrou instruções desse tipo. Só há exemplos ilustrativos de `pip install` (line-profiler, py-spy, build/twine). `python-packaging` inclui publicação no PyPI com twine: fica proibido no CLAUDE.md, o Jarvis não publica pacotes.

## 6. Skills a desenvolver internamente para o Jarvis

**Seis peças internas cobrem as lacunas que nenhum repositório externo resolve; a primeira é um CLAUDE.md, não uma skill, porque tem de vigorar em todas as sessões.** Destino: `.claude/` e `CLAUDE.md` no repo (destino C), versionados em `develop`, só depois de autorizada a alteração de ficheiros. Criar com `skill-creator` (já instalado), sem copiar texto CC-BY-SA.

| Ordem | Peça | Conteúdo obrigatório | Depende de |
| --- | --- | --- | --- |
| 0 | `CLAUDE.md` do projecto | Só `main`/`develop`; sem worktree, branch, force-push, merge ou release; sem Anthropic/OpenAI no runtime; Python 3.11 + pip/constraints; rótulos ANUNCIADO/INSPECCIONADO/TESTADO/APROVADO/IMPLEMENTADO; não publicar no PyPI; prevalece sobre qualquer skill externa | Autorização para alterar `develop` |
| 1 | `jarvis-wyzer-integrator` | Integridade 182/182 contra `upstream-v0.3.1-manifest.json`; patch policy (JAR-ARCH-02); fronteiras `wyzer/` vs `jarvis/`; testes de regressão | JAR-ARCH-02 |
| 2 | `jarvis-ollama-runtime` | Provider Ollama de `wyzer/brain/providers.py`, streaming, tool calling, timeouts, fail-closed, sem credenciais no browser | JAR-MODEL-01 (host e modelo definidos) |
| 3 | `jarvis-llm-eval` | Corpus PT de comandos, métricas determinísticas (acerto de tool call, schema válido, latência), juiz opcional via Ollama local; nunca SDK pago | Skill 2 + corpus consentido |
| 4 | `jarvis-voice-pt` | faster-whisper multilingue com `language` configurável, Kokoro PT, openWakeWord «Jarvis», VAD, barge-in, matriz de licenças, consentimento de gravação | VOICE-LIC-01, VOICE-STT-01 |
| 5 | `jarvis-hud-desktop` | PySide6 Floating/Expanded/Graph, estados reais do doc 12, overlay sem roubar foco, QWebEngine + React/Three.js só se a POC o justificar, medições CPU/GPU/fps | JAR-UX-02/03; cobre a lacuna Three.js |

**Fora de âmbito:** nenhuma destas skills instala dependências, descarrega modelos ou executa ferramentas Windows; descrevem contratos e testes. A ordem 0 deve preceder qualquer tarefa de implementação com Claude.

## 7. Plano de instalação por fases

**Cada fase só começa depois do gate anterior; nenhuma fase altera código do Jarvis.**

&#91;embedded content: plano de instalação · 4 fases, 3 gates\]

Até o CLAUDE.md da F2 existir, as regras de 2 branches e de runtime sem Claude vigoram pelas instruções desta tarefa. Em cada fase, a instalação é seguida da verificação da secção 8 antes de declarar a skill activa.

## 8. Verificação e reversão

**Cada instalação tem uma prova de presença, uma prova de integridade e um comando de reversão; nenhuma é declarada activa sem os três registados.**

**Antes de instalar (registo de base):**

```bash
claude plugin list > /tmp/antes-plugins.txt
ls -1 ~/.claude/skills > /tmp/antes-skills.txt
cat ~/.claude/settings.json > /tmp/antes-settings.json
```

**Integridade das skills copiadas (deve dar zero diferenças face à SHA fixada):**

```bash
diff -r "$T/w/plugins/python-development/skills/async-python-patterns" ~/.claude/skills/async-python-patterns
diff -r "$T/n/pyside6-desktop" ~/.claude/skills/pyside6-desktop
sha256sum ~/.claude/skills/*/SKILL.md   # comparar com o manifesto do pacote
```

**Presença e activação:**

| Destino | Verificar | Reverter |
| --- | --- | --- |
| A. Upload claude.ai | `ListSkills`/`ListPlugins` mostra `rightware-jarvis-dev` activo; numa sessão nova, pedir "usa a skill pyside6-desktop" e confirmar que carrega | Customize → Plugins → desactivar ou remover `rightware-jarvis-dev` |
| B. Plugin marketplace | `claude plugin list`; `claude plugin details pyright-lsp@claude-plugins-official`; `/plugin` → Installed | `claude plugin uninstall pyright-lsp@claude-plugins-official`; `claude plugin uninstall property-based-testing@trailofbits`; `claude plugin marketplace remove trailofbits` |
| B. Skills copiadas | `ls ~/.claude/skills`; `/skills` numa sessão nova | `rm -r ~/.claude/skills/<nome>` para cada uma das 8 pastas instaladas |
| LSP | `pyright-langserver --version`; editar um `.py` com erro de tipo e ver o diagnóstico | Desinstalar o plugin; o binário fica, ou `npm rm -g pyright` |

**Prova de não-regressão:** `diff /tmp/antes-settings.json ~/.claude/settings.json` deve continuar sem hooks novos; `git -C <checkout jarvis> status` deve mostrar a árvore limpa e `git branch -a` apenas `main` e `develop`.