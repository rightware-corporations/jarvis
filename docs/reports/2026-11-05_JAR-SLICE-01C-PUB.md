# JAR-SLICE-01C-PUB — Correcção de gates, publicação e CI Windows

**Estado final: `REMOTE_CI_PASS`**
**Repositório:** `rightware-corporations/jarvis` · **Branch:** `develop` · **Push:** 2026-11-05T14:42:50Z

## 1. SHAs

| | SHA |
|---|---|
| `origin/develop` antes | `372c21905ca2478c8b545e6b67af528a587e51b0` |
| `origin/develop` depois (`git ls-remote`) | `8cf751c266d61bd87f818f010e4b3a0faad8d0a3` |
| HEAD local | `8cf751c266d61bd87f818f010e4b3a0faad8d0a3` |
| `origin/main` (inalterada) | `10aa4648b61b6e2d2c2b91b3ff3edd3fb68bfe9b` |

Comando: `git push origin develop`, sem força. Saída: `372c219..8cf751c  develop -> develop`, rc=0 (fast-forward).

## 2. Commits publicados

| SHA | Mensagem | Autor | Data |
|---|---|---|---|
| `e21495cc29e247fdf72aa946f3e7787369918fa0` | feat(slice-01c-pre): voice runtime, read-only preflight and fail-closed STT handling | Claude | 2026-11-05T16:03:01+02:00 |
| `bfdefb74b44fd3723aa10c060045c2eac25b8af7` | feat(qa): read-only Windows QA preflight script for JAR-SLICE-01C | Claude | 2026-11-05T16:03:01+02:00 |
| `4ac65269d0964eb7c47adb29052bae0fc79b1c5d` | docs(slice-01c-pre): Windows QA plan G1-G10, licences, corpus and status | Claude | 2026-11-05T16:03:01+02:00 |
| `02e697cfdffb6d3bd19183332172cf1539f657f8` | docs(slice-01c-pub): fix QA gate dependencies, rollback and audio privacy | Claude | 2026-11-05T16:42:43+02:00 |
| `8cf751c266d61bd87f818f010e4b3a0faad8d0a3` | ci(slice-01c-pub): parse the Windows QA preflight with the PowerShell 5.1 parser | Claude | 2026-11-05T16:42:43+02:00 |

Os três commits da 01C-PRE foram publicados sem alteração. As correcções são dois commits novos.

## 3. Matriz de gates

| Fase | Gate | Resultado |
|---|---|---|
| 1 | G1 `origin/develop` = `372c219` | PASS (`fetch` e `ls-remote`) |
| 1 | G2 branch `develop` e 3 commits documentados | PASS (SHAs idênticos, `is-ancestor` verdadeiro) |
| 1 | G3 integridade Wyzer | PASS 182/182 |
| 1 | G4 árvore limpa | PASS (0 entradas). Os dois ficheiros de teste assinalados como alterados pelo ambiente tinham o blob igual a HEAD |
| 1 | G5 mecanismos de segurança | PASS: `allow_real_windows_actions=false` por omissão e na configuração; runtime de voz força o `SimulatedLauncher`; `auto_start` recusado; wake word `manual`; nenhum spawn em `jarvis/`; confirmações fail-closed |
| 2 | FIX-01 dependências dos gates | Corrigido (ver 4) |
| 2 | FIX-02 rollback | Corrigido (ver 4) |
| 2 | FIX-03 privacidade de áudio | Corrigido (ver 4) |
| 2 | Estado da 01B-PUB na documentação | Actualizado em `docs/01_CURRENT.md` e `docs/03_BACKLOG.md` |
| 3 | Job Windows de parsing | Adicionado (`windows-preflight-parse`) |
| 4 | Integridade, compilação, testes, configuração, âmbito, artefactos, YAML | PASS local: 182/182; compile rc=0; `tests_vexel` 383 + `tests_lab` 16 = 399 (venv local e venv equivalente ao CI); `CONFIG_OK`; 0 ficheiros do manifesto; 0 binários ou segredos; YAML com 3 jobs |
| 5 | Push fast-forward e HEAD remota = local | PASS |
| 6 | CI remoto no SHA exacto | PASS, 6/6 jobs |

## 4. Correcções no plano (`docs/25_JAR-SLICE-01C_WINDOWS_QA_PLAN.md`)

- **FIX-01.** Antes, o G1 exigia uma voz PT que só o G6 instalava, e o G5 usava `--voice`, que exige o preflight completo, voz PT incluída. Agora:
  - O **G1** é um inventário. A falta de microfone ou de voz PT dá **BLOCKER_VOICE**, que não pára o inventário nem os gates G2–G4. Os STOP ficam para Windows, RAM < 8 GB, disco < 10 GB e Python.
  - O **G5** só instala e verifica o modelo STT e o microfone (`STT_MODEL_OK`, `MIC_OK`).
  - O **G6** só garante a voz PT.
  - O **G7** é o primeiro ciclo real (reconhecimento, voz, cancelamento) e exige `--diagnose` = `PREFLIGHT READY`, ou seja G3, G5 e G6 PASS.
  - Há um diagrama de dependências e STOP explícitos por gate.
- **FIX-02.** O **G10** valida o rollback sem apagar nada. Arquiva as evidências com SHA-256, faz o inventário só de leitura do que seria removido e escreve o procedimento R1 com os caminhos reais. A remoção (**R1**) é opcional, linha a linha, e exige autorização escrita específica, depois de G10 PASS e das evidências arquivadas. O ambiente fica pronto para repetir a demonstração.
- **FIX-03.** Nova secção 2 sobre privacidade:
  - o WAV temporário do Wyzer: `wyzer-whisper-*.wav` em `%TEMP%`, criado depois da captura e apagado no `finally` (confirmado no código: `tempfile.mkstemp` e `path.unlink(missing_ok=True)`), só pode ficar se o processo for terminado à força; há verificação no fim de G7–G9;
  - captura só em memória; a voz SAPI recebe o texto pelo stdin, sem ficheiros;
  - tabela dos logs locais com e sem `log_transcript_text`;
  - proibição de publicar áudio, transcrições ou identificadores no GitHub;
  - lista de higienização antes de partilhar evidências.

Diff incremental: `JAR-SLICE-01C-PUB-fixes.diff` (4 ficheiros, +190/−57).

## 5. Alteração do workflow

Um job novo; os jobs Linux não mudaram.

- `windows-preflight-parse` corre em `windows-latest` com `shell: powershell` (Windows PowerShell 5.1).
- Confirma Desktop 5.x e usa `System.Management.Automation.Language.Parser::ParseFile` sobre `qa/windows/Invoke-JarvisPreflight.ps1`.
- Emite cada erro como `::error file=…,line=…,col=…::mensagem` e termina com `exit 1` se houver algum.
- Lista as funções e o `#Requires`.
- Não executa o script e não instala nada; `permissions: contents: read` mantém-se.

Diff: `JAR-SLICE-01C-PUB-ci-workflow.diff`.

## 6. GitHub Actions

| Run | Evento | headSha | Conclusão | Duração |
|---|---|---|---|---|
| [42047670896](https://github.com/rightware-corporations/jarvis/actions/runs/42047670896) | push | `8cf751c266d61bd87f818f010e4b3a0faad8d0a3` | **success** | 14:42:54Z → 14:43:16Z |
| [42047684355](https://github.com/rightware-corporations/jarvis/actions/runs/42047684355) | pull_request (#2) | `8cf751c266d61bd87f818f010e4b3a0faad8d0a3` | **success** | 14:42:59Z → 14:43:22Z |

| Run | Job | Runner / Python | Resultado |
|---|---|---|---|
| push | [windows-preflight-parse](https://github.com/rightware-corporations/jarvis/actions/runs/42047670896/job/127314968392) | windows-2025-vs2026 · Windows PowerShell 5.1.26100.33648 (Desktop) | success |
| push | [source-integrity](https://github.com/rightware-corporations/jarvis/actions/runs/42047670896/job/127314969588) | ubuntu-26.04 · CPython 3.11.18 | success |
| push | [headless-contract](https://github.com/rightware-corporations/jarvis/actions/runs/42047670896/job/127314969120) | ubuntu-26.04 · CPython 3.11.17 | success |
| PR | [windows-preflight-parse](https://github.com/rightware-corporations/jarvis/actions/runs/42047684355/job/127315016790) | windows-2025-vs2026 · Windows PowerShell 5.1.26100.33648 (Desktop) | success |
| PR | [source-integrity](https://github.com/rightware-corporations/jarvis/actions/runs/42047684355/job/127315017215) | ubuntu-26.04 · CPython 3.11.17 | success |
| PR | [headless-contract](https://github.com/rightware-corporations/jarvis/actions/runs/42047684355/job/127315017473) | ubuntu-26.04 · CPython 3.11.18 | success |

**Evidência por item (igual nos dois runs):**

1. **Integridade Wyzer:** `Source integrity: 182/182` · `Binary assets intentionally excluded: 44` · `SOURCE_INTEGRITY_PASS`.
2. **Compilação:** `compileall -q wyzer tests scripts jarvis tests_vexel tests_lab`, sem qualquer saída; passo success.
3. **`tests_lab`:** 16 passed, 0 failed, 0 error, 0 skipped.
4. **`tests_vexel`:** 383 passed, 0 failed, 0 error, 0 skipped. Total 399, igual ao local.
5. **`--check-config`:** `CONFIG_OK`, `allow_real_windows_actions: false`, passo success.
6. **Parsing PowerShell:** `Windows PowerShell 5.1.26100.33648 (Desktop), CLR 4.0.30319.42000` · `Parsed qa/windows/Invoke-JarvisPreflight.ps1: 2971 tokens, 0 parse error(s)` · funções `Protect-Text, Write-Step, Get-Prop, Invoke-Probe, Get-Value, Add-Gate` · `#Requires -Version: 5.1` · `PARSE_PASS (script parsed, not executed)`.
7. **SHA testado:** o `headSha` dos dois runs é igual ao SHA publicado.

**Avisos e anotações:** não há anotações de erro nem passos falhados.
- `warning`: Node.js 20 obsoleto (`actions/checkout@v4`, `actions/setup-python@v5`, forçados a correr em Node 24), em todos os jobs.
- `notice`: migração do `ubuntu-latest` para Ubuntu 26.
- `StarletteDeprecationWarning` no `tests_lab`, já existente.

As linhas `::error` visíveis nos logs do job Windows são o código do passo ecoado pelo runner (a cinzento) e não anotações emitidas; a API dos check-runs confirma 0 erros.

**Dependências no CI:** pydantic 2.14.3, pydantic-core 2.50.4, psutil 7.2.2, pytest 8.4.2. São diferentes das constraints Windows do plano de QA (pydantic 2.12.3, psutil 7.1.3); os testes passam nas duas combinações. O Python variou entre 3.11.17 e 3.11.18 conforme a imagem.

Contagens de testes: o `-q` do workflow soma-se ao `-q` do `pyproject`, por isso a linha «N passed» não aparece. As contagens foram tiradas, por script, das linhas de progresso (um carácter por teste).

## 7. Integridade Wyzer

| Momento | Resultado |
|---|---|
| Antes (G3) | 182/182 em HEAD `4ac6526` |
| Antes do push | 182/182; 0 caminhos do manifesto nos commits novos |
| CI (2 runs) | 182/182 |
| Depois do push | `git archive origin/develop` + `verify_import.py`: 182/182 |

## 8. PR #2 (apenas lido)

Aberto, **draft**, não merged. `develop` → `main` (`10aa464`). Head `8cf751c…` (reflecte a nova HEAD). 86 commits, 266 ficheiros. `mergeable_state: clean`. Checks no SHA: 6/6 success. Não alterei, não comentei e não fiz merge.

## 9. Riscos e limitações pendentes

1. **O parsing não equivale a execução.** O CI prova que o script é sintacticamente válido para o PowerShell 5.1. As sondas (WMI, registo, System.Speech, MMDevices) só são exercitadas no G1 real.
2. **Avisos de Node 20 nas actions.** Recomendo uma tarefa própria para actualizar `checkout` e `setup-python` antes de o GitHub deixar de aceitar o Node 20. Não alterei nada.
3. **Versões não fixadas no CI Linux** (intervalos): diferem das constraints do Windows QA.
4. **Resumo do pytest suprimido** pelo `-q` duplicado (proposta anterior: `pytest -ra`).
5. Mantêm-se os riscos da 01C-PRE: vozes OneCore, captura não interrompível a meio de uma frase, limiar de energia fixo, comportamento e latência do modelo real, licença do Qwen3.5 por confirmar no G3.

## 10. Próxima execução no PC de QA (identificada; nada instalado nem executado)

**G1 — Inventário read-only.** Com autorização da RIGHTWARE e no PC de QA autorizado:
1. copiar `develop@8cf751c` para `C:\VEXEL-QA\jarvis`;
2. correr `powershell -NoProfile -ExecutionPolicy Bypass -File .\qa\windows\Invoke-JarvisPreflight.ps1`;
3. rever à mão o `report.txt` e o `report.json` (secção 2.4 do plano) e enviar o resumo.

Com esse resultado decide-se o G2 e o G3: as dependências, o Ollama e o `qwen3.5:4b`, ou o `qwen3.5:2b` se a RAM ficar entre 8 e 16 GB. O G7, o primeiro ciclo de voz real, só começa depois de um `--diagnose` READY.
