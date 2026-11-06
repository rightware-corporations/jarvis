# VEXEL Jarvis — Revisão da entrega Claude v0.1.1 / CLAUDE V3 / M0

**Data:** 2026-11-04 (Africa/Maputo). **Natureza:** revisão técnico-documental independente, não decisão de lançamento nem autorização da POC.  
**Base:** ficheiros enviados pela RIGHTWARE: `rightware-jarvis-dev-0.1.1.zip`, `rightware-jarvis-dev-0.1.1-VALIDATION.md`, `CLAUDE_V3_PROPOSTA.md`, `CLAUDE_V2_para_V3.diff`; resumo e link [artefacto Claude JAR-ARCH-02 / JAR-UX-03](https://claude.ai/artifact/CiMZbBPCVcPjg3iVDSMCpF). O plano da POC com todos os **31 testes/8 áreas e limiares exactos não veio em ficheiro materializado**: foi conhecido apenas por resumo do Claude. Aprová-lo à distância sem ler esses parâmetros seria precipitado.

## 1. Plugin RIGHTWARE v0.1.1 — análise e recomendação

- **Ficheiro examinado em sandbox:** `rightware-jarvis-dev-0.1.1.zip`; **100834 bytes**, **SHA-256 `919e1e3acd589f95f749d056b59baabf292cfb2cbe8eb10882612c300ec577f4`**. Digest corresponde ao relatório do Claude.
- ZIP: **40 ficheiros**, **23 pastas**, **9 skills**, sem caminhos absolutos/`../`, sem symlinks e sem bits executáveis nos ficheiros; CRC `ZipFile.testzip()=None`.
- `PROVENANCE.json` lido: 34 ficheiros de skills, **34/34 SHA-256 coincidem com o conteúdo no ZIP**. 33 entradas marcadas upstream-identical, 1 patch declarado `RW-JDEV-0001` em `skills/pyside6-desktop/SKILL.md`. Isto verifica integridade **interna do manifesto**, não comparação independente de todos os 33 contra o GitHub original.
- `.claude-plugin/plugin.json` declara `name=rightware-jarvis-dev`, `version=0.1.1`.
- Frontmatter `pyside6-desktop/SKILL.md` verificado: `allowed-tools` contém **apenas `Read`, `Grep`, `Glob`**. É pré-aprovação para o turno de invocação da skill, **não bloqueio global de Edit/Write/Bash**. Outras regras de permissão ainda aplicam.
- **Não instalámos nem executámos o plugin neste chat.** O `claude plugin validate` é **PASS reportado pelo Claude**, não reexecutado nesta revisão. O ZIP não foi publicado no repositório público; foi arquivado aqui apenas o relatório/manifesto para proveniência.
- **Recomendação:** RIGHTWARE pode substituir a versão v0.1.0 pela v0.1.1 por `Customize → Plugins`, **não** `Upload a skill`; verificar numa sessão nova o nome/versão, 9 skills e cópia instalada das permissões. Guardar v0.1.0 para rollback. **Estado da v0.1.1 na conta: NÃO CONFIRMADO até capturas/verificação pós-upload.**

[Relatório Claude v0.1.1](reference/CLAUDE_PLUGIN_VALIDATION_V011_2026-11-04.md) · [Auditoria de skills](reference/CLAUDE_SKILLS_AUDIT_2026-11-04.md).

## 2. CLAUDE.md V3 — conteúdo revisto e pontos a ajustar

**Aprovação técnica condicionada**. A versão V3 é melhor que V2: especifica providers locais (`OpenAICompatibleChatProvider`, `LlamaCppChatProvider` verificados em `wyzer/brain/providers.py`), defende assets reprodutíveis, separa Web Lab HTTP do QWebChannel desktop, remove estados transitórios do texto de governação e delimita módulos visuais do frontend.

**Quatro correcções antes de aprovar `/CLAUDE.md` no `develop`:**

1. **§4 Inventário de código VEXEL:** não limitar a `docs/0*–docs/1*`: existem `docs/20*`, `21*`, `22*`, `23*`, `24*`, `docs/reference/` e `docs/archive/`. Descrever a regra **por ficheiro incluído/excluído do manifesto upstream**, não por glob enganoso. `CLAUDE.md` só passará a "VEXEL actual" depois do commit.
2. **§14 `allowed-tools`:** trocar a frase geral "Skills e plugins de terceiros usados neste projecto declaram allowed-tools mínimo (por omissão só leitura)" por afirmação específica: `rightware-jarvis-dev@0.1.1` tem `Read/Grep/Glob` **na skill pyside6-desktop**, se instalado e validado. Outros plugins/skills e permissões globais exigem auditoria própria. `allowed-tools` **pré-aprova**, não restringe ferramentas disponíveis.
3. **§4/5 Licenças Qt:** `PySide6==6.6.1` consta já do `installer/constraints-windows-py311.txt` preservado. O PySide6 Community é disponibilizado sob opções **LGPL-3.0/GPL**; integração, distribuição e componentes QtWebEngine exigem avaliação de cumprimento (avisos, relinking/substituição de bibliotecas quando aplicável, documentação) e licença da componente exacta. Não tratar toda utilização LGPL como automaticamente proibida nem supor que uma app fechada fica livre de obrigações só por usar PySide6.
4. **§13/14 coordenação visual e QA:** adicionar Manus como responsável **somente por preview Chromium, screenshots reais e relatório visual**. Declarar explicitamente que `adewaskar/jarvis` permanece **candidato visual até avaliação pela RIGHTWARE**, sem quaisquer efeitos visuais que aleguem execução real.

**Melhorias opcionais:** indicar que comandos `ruff/mypy` requerem dependências instaladas por tarefa; preferir gate actual de CI e QA a impor novas instalações; esclarecer direitos de outputs de modelos; acrescentar política de privacidade para microfone sempre à escuta.

O draft V3 **não deve ser commitado como regra oficial** antes de validar estas correcções e obter aceitação RIGHTWARE.  
[Draft V3 preservado](reference/CLAUDE_V3_PROPOSTA_2026-11-04.md) · [Diff V2→V3](reference/CLAUDE_V2_PARA_V3_2026-11-04.diff) · [V2 arquivado](reference/CLAUDE_REVIEW_V2_DRAFT_2026-11-04.md).

## 3. M0 Windows/Qt — decisão recomendada por etapas

**Gate 0: ver o frontend real.** Primeira prioridade é receber **Manus/Chromium**: boot, idle, listening, thinking, speaking, painel, compact, evidência de estados simulados marcada `MOCK`, galeria e erros. Até lá, **NÃO APPROVED** iniciar a POC definitiva sem decisão específica.

**Gate 1: M0 smoke isolado.** Depois do preview e autorização expressa, testar numa pasta temporária e venv descartável do Windows:
- Python 3.11, baseline `PySide6==6.6.1` (`installer/constraints-windows-py311.txt` da origem), **sem editar `pyproject.toml` nem constraints originais**.
- Janela PySide6 sem moldura, transparente, móvel, com assets locais React/WebGL e `QWebChannel` mínimo apenas de estados falsos/sem ferramentas.
- Medir transparência, foco, arrasto, resize, CPU/RAM/GPU, FPS, crashes e isolamento de rede; se falhar, fallback QPainter/Qt Quick.
- **Após smoke**, executar a matriz mais ampla dos 31 testes referidos pelo Claude, condicionada à revisão do plano real e dos limiares.

**Gate 2: comparação de versões e hardware.** Comparar 6.6.1 com **6.11.3** numa **segunda venv separada** se necessário; a versão 6.11.3 foi publicada 26/10/2026 e suporta Python 3.11, mas há também **6.12.0** no PyPI (número de versão superior, publicada 08/10/2026). Não confundir 6.11.3 com última versão absoluta, nem fazer upgrade do instalador upstream por iniciativa da POC. Comparar primeiro em **um** Windows autorizado; usar segundo PC (GPU dedicada/integrada) para confirmação de compatibilidade, não como bloqueador para o smoke inicial.

**Gate 3: produto.** Só integrar visual ao Wyzer depois de resultados, licença, plano de patches e contrato de eventos/políticas validados.

**A POC M0 não foi executada.** Os 31 testes e limiares precisariam ser anexados para aprovação formal; valores num resumo não são prova nem critério acordado. Nenhum equipamento Windows foi designado nesta revisão.

## 4. Fontes verificáveis

- [Wyzer constraints](https://github.com/rightware-corporations/jarvis/blob/develop/installer/constraints-windows-py311.txt): PySide6 6.6.1.
- [Wyzer install](https://github.com/rightware-corporations/jarvis/blob/develop/installer/install.ps1): venv e pip, não PyInstaller.
- [Wyzer providers](https://github.com/rightware-corporations/jarvis/blob/develop/wyzer/brain/providers.py): `OpenAICompatibleChatProvider` e `LlamaCppChatProvider`.
- [PyPI PySide6 6.11.3](https://pypi.org/project/PySide6/6.11.3/), [PyPI PySide6 6.12.0](https://pypi.org/project/PySide6/6.12.0/), [Qt for Python commercial/open source licensing](https://doc.qt.io/qtforpython-6/commercial/index.html).
- [adewaskar/jarvis@1c4016a](https://github.com/adewaskar/jarvis/tree/1c4016afdf86f7043efc6882ceffef84ad0d8783) árvore UI: `src/scene/`, `src/ui/` e dependências Claude separadas.

## 5. Critérios para retomar

- RIGHTWARE: fazer upload v0.1.1 com verificação; aceitar ou ajustar pontos do CLAUDE V3; definir se/qual Windows pode receber M0 depois do preview; rever benchmarks propostos.
- Claude: entregar V3 corrigida como V4 (não commit sem autorização); preservar plano integral M0 e lista exacta de testes/limiares; **não mexer no upstream**.
- Manus: entregar evidência visual Chromium do frontend original; não ligar a bridge Claude.
- ChatGPT: rever entregas e preparar tarefa de implementação com SHA e gates.

**Estado:** AUDITORIA DE FICHEIROS REALIZADA; RECOMENDAÇÃO FAVORÁVEL À V0.1.1; `CLAUDE.md` V3 EM REVISÃO; M0 AINDA NÃO AUTORIZADA.
