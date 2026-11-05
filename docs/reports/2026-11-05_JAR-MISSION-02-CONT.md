# JAR-MISSION-02-CONT — Relatório final

**Estado final: `MISSION_PASS`** · 2026-11-05 · branch `develop`
`MISSION_PASS` diz respeito ao código e ao CI com componentes simulados. **Não equivale a funcionamento real com Ollama, microfone e voz**, que é a JAR-SLICE-01C no PC de QA.

## 1. Estado recuperado

| Verificação | Resultado |
|---|---|
| `origin/develop` = HEAD local | `abae0c9cd54e091b2ac155aa607dcb5641648bab` |
| `7c10bbe` e `abae0c9` na história | sim (ancestrais) |
| Commits locais por publicar | 0 · árvore limpa · 0 stashes |
| Integridade Wyzer | 182/182 |
| Últimos runs | [42053169193](https://github.com/rightware-corporations/jarvis/actions/runs/42053169193) e [42053185299](https://github.com/rightware-corporations/jarvis/actions/runs/42053185299), success |
| PR #2 | aberto, draft, head `abae0c9` |

A ordem original da JAR-MISSION-02 não foi recebida nesta sessão. As frentes A–F e os requisitos foram tirados da ordem de continuação.

## 2. HEAD inicial e final

| | SHA |
|---|---|
| Inicial | `abae0c9cd54e091b2ac155aa607dcb5641648bab` |
| Código final (CI verde) | `fb9f1ef22102d2cae4cc9dd003dcd8ed5295743e` |
| Final | o commit de documentação que acrescenta este relatório (ver a mensagem de entrega) |
| `main` | `10aa4648b61b6e2d2c2b91b3ff3edd3fb68bfe9b` (inalterada) |

## 3. Commits

**Existentes (reconhecidos, não repetidos):** `7c10bbe` (ADR-0001) e `abae0c9` (estrutura).

**Novos, todos publicados por fast-forward:**

| SHA | Commit |
|---|---|
| `2692d8f` | test(mission-02): fronteiras ADR-0001 e comportamento de `Africa/Maputo` · ci(mission-02): job `windows-python` |
| `e031f60` | fix(preflight): descrição do SO sem lançar processos no Windows |
| `4794ede` | feat(desktop): Orb Desktop MVP |
| `48d94ae` | feat(qa): kit da primeira demonstração e resumo de latências G9 |
| `baa3434` | ci(desktop): job `desktop-orb` (Ubuntu e Windows) |
| `25cf2d0` | fix(qa): achados da revisão (G9 nunca passa com < 20 amostras; verificador CI mais estrito) |
| `4a69ee5` | fix(desktop): achados da revisão (ordenação por sessão, encerramento verificado, validação de `--speed`) |
| `fb9f1ef` | ci: `persist-credentials: false`; verificação de identificadores alargada |

O commit `2692d8f` contém dois commits locais (os testes e o job CI), publicados no mesmo push. Cada commit novo foi verificado sozinho: 182/182, mais os testes headless e do Orb.

## 4. ADR-0001 confirmado

A estrutura publicada está conforme. As fronteiras passaram a ter teste (`tests_vexel/test_mission02_boundaries_and_time.py`):
- `jarvis/` não importa Qt, web nem `apps/`;
- `apps/weblab/` não chega aos adapters Windows nem ao lançador real;
- `apps/desktop/` só importa `jarvis.ui`. Num interpretador limpo, o Orb carrega exactamente `jarvis`, `jarvis.ui` e `jarvis.ui.events`;
- a árvore não tem áudio, modelos nem bases de dados.

O ADR não foi reescrito e o laboratório não foi movido.

## 5. Árvore efectiva (novidades a negrito)

```
apps/desktop/  __init__.py  __main__.py  README.md
               orb/ visuals.py model.py render.py pump.py widget.py demo.py app.py   (novo)
apps/weblab/   api.py headless.py web/
jarvis/        brain core language runtime tools ui voice   (preflight.py corrigido)
qa/windows/    Invoke-JarvisPreflight.ps1  ci_expect_diagnose.py (novo)  DEMO_KIT.md (novo)  README.md
qa/corpus/     pt_mz_v1.txt
qa/benchmarks/ latency_summary.py (novo)  README.md
tests_vexel/   … + test_mission02_boundaries_and_time.py, test_mission02_qa_kit.py (novos)
tests_desktop/ conftest.py test_orb_logic.py test_orb_qt.py (novo)
docs/adr  docs/plans  docs/reports
```

## 6. Frontend, backend e Web Lab

- **Backend (`jarvis/`):** sem alterações funcionais, excepto a correcção do `os_description()`.
- **Frontend (`apps/desktop/`):** Orb MVP (ver 10).
- **Web Lab (`apps/weblab/`):** o entrypoint `apps.weblab.api:app` é uma aplicação FastAPI; rotas `/`, `/lab.css`, `/lab.js`, `/api/v1/health`, `/api/v1/sessions` e `/api/v1/chat`; `tests_lab` 16/16 em Linux e Windows.

## 7. Frentes da missão

| Frente | Estado | Evidência |
|---|---|---|
| A — Compatibilidade Python no CI Windows | **concluída** | job `windows-python`: 443 + 16 PASS em Windows (cp1252, LF, `tzdata`) |
| B — Preflight PowerShell no runner | **concluída** | primeira execução real: todas as sondas sem erro, 3 ficheiros, repositório intacto, sem identificadores |
| C — Kit de demonstração QA | **concluída** | `DEMO_KIT.md`, `latency_summary.py` (21 testes), verificador do diagnóstico (5 testes) |
| D — Orb Desktop MVP | **concluída (MVP)** | 87 testes offscreen em Ubuntu e Windows; snapshots dos 9 estados; demo com saída limpa |
| E — Revisão independente | **concluída** | agente revisor só de leitura: 0 P0, 1 P1, 5 P2, 9 P3 → todos tratados |
| F — Regressão, integração, publicação | **concluída** | CI 6/6 jobs em push e PR no SHA `fb9f1ef` |

## 8. Testes

| Suite | Linux | Windows |
|---|---|---|
| `tests_vexel` | 443 PASS (local e CI) | 443 PASS (CI) |
| `tests_lab` | 16 PASS | 16 PASS |
| `tests_desktop` (offscreen) | 87 PASS | 87 PASS |
| Saltados | 0 | 0 |

- Estabilidade: 5 execuções headless e 5 do Orb consecutivas, sem falhas.
- Ambiente Windows no CI: Python 3.11.9 e Windows PowerShell 5.1.26100.33648. O parsing do script deu 0 erros.

## 9. Preflight no runner Windows (resultado real, sem dados de máquina)

- **`--diagnose`:** exit 3 (BLOCKED, esperado). Políticas `platform`, `python`, `windows_actions` e `activation` em PASS. Cinco ausências documentadas: `DEPENDENCY_MISSING`, `STT_MODEL_MISSING`, `MIC_MISSING` (sonda real com o `sounddevice`), `PT_VOICE_MISSING` (inventário SAPI real) e `OLLAMA_UNREACHABLE`.
- **`Invoke-JarvisPreflight.ps1`:** Windows Server 2025, 16 GB de RAM (PASS), 28 GB livres, Python 3.11 registado. Sem voz PT, sem microfone e sem Ollama (esperado). Privilégios: WARN, porque o runner corre elevado. Sondas com erro: nenhuma.

## 10. Estado do Orb

- **Os nove estados:**
  - cores e movimentos distintos: parado, respira, anéis, órbita, segmentos, pulso âmbar, barras de onda, riscado, intermitente;
  - legendas PT: «Desligado», «Pronto», «A ouvir», «A pensar», «A executar», «Confirma: sim ou não?», «A falar», «Silenciado», «Erro».
- **Arquitectura e concorrência:**
  - desenho vectorial com QPainter;
  - modelo determinístico e ordenado por sessão;
  - `QueueSink` drenado por um `QTimer` na thread da GUI (testado: os eventos são aplicados apenas na thread da GUI).
- **Janela e ciclo de vida:**
  - high-DPI `PassThrough` com tamanhos mínimos;
  - encerramento verificado (join do simulador, timers parados, `quit()` explícito);
  - simulador sem modelo nem ferramentas.
- **Executar:** `python -m apps.desktop --demo`; `--snapshot DIR`.
- **Por fazer:** ligar o Orb a um `VoiceSession` real (depois de G7/G8). A direcção visual definitiva fica sujeita a revisão de design.

## 11. Revisão independente

Feita por um agente revisor que não escreveu o código, em modo só de leitura, sobre `abae0c9..baa3434`. Veredicto: `READY_WITH_FIXES`. Achados e tratamento:

- **P1** O resumo G9 dava PASS com uma só amostra → **corrigido** (≥ 20 amostras), com teste.
- **P2** O modelo do Orb ignorava o `session_id` (uma sessão reiniciada ficava congelada) → **corrigido**, com teste.
- **P2** `--speed 0` provocava divisão por zero → **corrigido** (argparse e driver), com testes.
- **P2** O encerramento não reportava fugas, por isso o passo de CI passava sem as detectar → **corrigido** (`shutdown()` devolve o estado e `run()` sai com código ≠ 0), com teste.
- **P2** Turnos interrompidos ou incompletos entravam no tempo de resposta → **corrigido**, com teste.
- **P2** `importorskip` podia esconder um Qt partido → **removido**.
- **P3** (9 achados): asserção inútil, unicidade de imagem dependente da legenda, lista negra de imports → lista branca, histórico sem limite, animação a 60 fps nos estados parados, `NaN` no JSON, `DEPENDENCY_MISSING` demasiado permissivo, `persist-credentials` e `USERDOMAIN`/`USERPROFILE`, encerramento depois de `deleteLater` → **todos corrigidos**.

## 12. Defeitos

**Corrigidos nesta missão:**
- **preflight:** lançava `cmd /c ver` no Windows; encontrado pelo CI Windows e pela guarda de processos;
- **fuso horário:** `Africa/Maputo` sem `tzdata` no Windows; o plano de QA instala-o e o fallback para o relógio do sistema ficou testado;
- **revisão:** os achados da secção 11.

**Pendentes:** nenhum P0 ou P1. Os riscos estão na secção 15.

## 13. Skills e ferramentas usadas

- Skill `rightware-jarvis-dev:pyside6-desktop`: regras de threading Qt, `deleteLater`, DPI e tamanhos mínimos.
- Agente revisor independente (só de leitura).
- GitHub Actions (runners Ubuntu e Windows) e a API REST do GitHub.
- Não foram instaladas ferramentas de terceiros. O PySide6 6.6.1 foi usado só em venvs isolados e no CI.

## 14. CI

- **SHA `fb9f1ef`:**
  - [push 42067632566](https://github.com/rightware-corporations/jarvis/actions/runs/42067632566) e [PR 42067646847](https://github.com/rightware-corporations/jarvis/actions/runs/42067646847): `source-integrity`, `headless-contract`, `windows-preflight-parse`, `windows-python`, `desktop-orb (ubuntu-latest)` e `desktop-orb (windows-latest)`, todos success;
  - artefactos `orb-snapshots-ubuntu-latest` e `orb-snapshots-windows-latest`.
- **Histórico desta missão:**
  - `2692d8f` → `REMOTE_CI_FAIL` no `windows-python` (19 testes; defeito real no preflight);
  - `e031f60` → PASS ([42064653918](https://github.com/rightware-corporations/jarvis/actions/runs/42064653918)), corrigido numa ronda.

## 15. Riscos residuais

1. Nada foi validado com hardware real (Ollama, Whisper, microfone, voz SAPI PT, latência): é a JAR-SLICE-01C.
2. O Orb ainda não está ligado ao ciclo de voz real; o design visual é provisório.
3. O PySide6 6.6.1 é LGPL-3.0, com ligação dinâmica; a distribuição precisa de revisão de licenças (JAR-RELEASE-01).
4. As actions usam Node 20 (aviso de obsolescência). Foram mantidas as mesmas versões; a actualização é uma tarefa à parte.
5. O CI resolve versões flutuantes no Linux (pydantic 2.14.x), diferentes das constraints do Windows QA (2.12.3); os testes passam nas duas.
6. Mantêm-se os riscos já registados: vozes OneCore, captura não interrompível a meio da frase, licença do Qwen3.5 por confirmar no G3.

## 16. Próximo passo para QA real

Com autorização da RIGHTWARE e no PC de QA: seguir `qa/windows/DEMO_KIT.md`, começando pelo passo 1 (inventário read-only), e enviar o `report.txt` revisto. O ciclo de voz (passo 8) só começa com `--diagnose` = `PREFLIGHT READY`.

## 17. Estado final

**`MISSION_PASS`**:
- estrutura ADR-0001 consolidada e testada;
- código existente preservado (182/182);
- CI Windows funcional com testes Python reais;
- preflight validado no runner, dentro do âmbito permitido;
- Orb MVP demonstrável;
- revisão independente concluída e tratada;
- CI remoto verde na HEAD de código publicada;
- nenhum P0/P1.
