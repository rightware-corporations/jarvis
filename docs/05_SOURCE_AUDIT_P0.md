# 05 — Auditoria estática P0 do upstream Wyzer v0.3.1

**Referência fixa:** `XtraWyze/Wyzer-Ai@db83c085feca32d3c091361165cb9ac7ecadafe0` (`v0.3.1`). **Natureza da prova:** leitura de código GitHub; nenhum teste funcional executado.

## Inventário
Git tree do tag: 226 blobs, incluindo 140 `.py`, 49 ficheiros sob `tests/`, 42 `.png`, 2 `.onnx`. Existem licenças e artefactos binários de modelos/assets que exigem verificação de direitos antes da distribuição.

## Seams reaproveitáveis
| Ficheiro | Facto inspeccionado | Decisão de adaptação |
| --- | --- | --- |
| `wyzer/app/orchestrator.py` | `Orchestrator(registry, executor, provider, *, conversation, memory, tasks, confirmation_policy, ...)`; aceita injecção de dependências | **Ponto principal para execução headless** e testes com provider/executor simulados |
| `wyzer/brain/providers.py` | `NativeChatProvider` parametrizado por endpoint/model; erros explícitos | Preservar adapter Ollama; injectar transporte em testes |
| `wyzer/tools/registry.py` | Registo tipado/capabilities por `ToolRegistry` | No Web Lab criar registry específico **sem** packs Windows, browser real ou shell |
| `wyzer/policy/confirmations.py` | `ConfirmationPolicy` com aprovação vinculada a digest/TTL; detecção condicional usa regex inglesas | Localizar detecção de risco e prompts, preferir metadados tipados em vez de traduções frágeis |
| `wyzer/memory/store.py` | `MemoryStore(database_path)` com SQLite e `remember/list/forget`; instância sem argumento user_id | **Não partilhar a mesma DB** entre sessões/contas web; criar escopo por utilizador e testes de isolamento |
| `wyzer/app/cli.py` | `build_assistant` cria packs Windows e serviços locais por defeito | Não reutilizar `build_assistant` directamente no servidor; compor `Orchestrator` com adapters headless |
| `wyzer/speech/__init__.py` | Importa adaptadores de áudio Windows | Definir voice service opcional e lazy imports no servidor |

## Riscos prioritários confirmados por inspeção
1. **Português não é apenas TTS/STT:** `orchestrator.py` usa regex `_YES`, `_NO`, `_STOP`, `_HELP`, `_TASK_STATUS`, `_PAUSE`, `_RESUME` em inglês. `confirmations.py` usa padrões ingleses como `send`, `purchase`, `restart`. Sem localização, `sim`, `não` ou `cancela` podem falhar no fluxo determinístico.
2. **Memória multiutilizador:** o tipo `MemoryStore` não recebe `user_id`. Isto é suficiente para o aplicativo local de um utilizador, mas requer separação explícita por utilizador e sessão no servidor.
3. **Windows vs servidor:** `wyzer/app/cli.py` compõe ferramentas de desktop e imports de fala Windows; hosting Linux pode requerer dependências opcionais e guards. A presença de `Orchestrator` desacoplado não prova que todos os imports funcionam fora de Windows.
4. **Código agente:** `wyzer.toml` define `coding_agent.enabled=true`. Em laboratório web, manter **off** até sandbox, limites de workspace e segurança aprovados.
5. **Modelos e voz:** o `small.en` não cobre português; o openWakeWord e modelos de voz têm termos próprios. MIT do núcleo não resolve a licença dos assets.

## Sequência técnica de correcção
- **T01:** snapshot/import upstream com proveniência e LICENSE intactos.
- **T02:** testes isolados de importação do `Orchestrator` em runtime remoto sem ambiente Windows.
- **T03:** `create_headless_assistant` com `ToolRegistry` de simulação e `ToolExecutor` de testes; sem acções reais.
- **T04:** isolamento de `MemoryStore` por utilizador (ou instância/db individual) e testes de cross-user leakage.
- **T05:** confirmação metadados-first + localização PT de `sim/não/cancelar`; teste de não-escalação.
- **T06:** provider auto-hospedado real, autenticação de API e observabilidade.
- **T07:** serviços de voz multilingue opcionais, benchmark de latência e UX.

**Conclusão:** a escolha Wyzer continua forte; a arquitectura já oferece injecção `provider/executor/registry` e permite preservar o motor principal. Contudo, o `Web Lab` ainda requer uma composição própria, isolamento multiutilizador e localização de segurança. Sem estes gates, não expor serviços à Internet.
