# JAR-SLICE-01B-PUB — Publicação controlada e validação CI remota

**Estado final: `REMOTE_CI_PASS`**
**Repositório:** `rightware-corporations/jarvis` · **Branch:** `develop` · **Data:** 2026-11-05 (push às 10:05:25Z)

---

## 1. HEAD anterior e posterior

| | SHA |
|---|---|
| `origin/develop` antes (HEAD_ANTES) | `f3e145698483f8fb67c8f12b8752a5efd29a3e9a` |
| HEAD local (HEAD_LOCAL) | `372c21905ca2478c8b545e6b67af528a587e51b0` |
| `origin/develop` depois (`git ls-remote`, HEAD_DEPOIS) | `372c21905ca2478c8b545e6b67af528a587e51b0` |
| `origin/main` (inalterada) | `10aa4648b61b6e2d2c2b91b3ff3edd3fb68bfe9b` |

Comando: `git push origin develop`, sem flags de força. Saída: `f3e1456..372c219  develop -> develop`, rc=0 (fast-forward).

## 2. Commits publicados

| SHA | Mensagem | Autor | Data |
|---|---|---|---|
| `f0734da7aefc3ed7eb2540f2cc16e65407e24dd6` | feat(slice-01b): PT voice core composed over Wyzer with closed tool allowlist | Claude &lt;noreply@anthropic.com&gt; | 2026-11-04T18:59:35+02:00 |
| `587713874784278e4cb3aa41b6ac4e5c6c649b1e` | test(slice-01b): contract and full-cycle tests with fakes (236 cases) | Claude | 2026-11-04T18:59:35+02:00 |
| `be920911c40acb8f7bd96a7bf7e8afe8196a7269` | docs(slice-01b): record simulated results and 01C/01D pending work | Claude | 2026-11-04T18:59:35+02:00 |
| `53e295d04f1503b378908b95eb498677f103348e` | fix(slice-01b-r01): fail-closed speech, explicit action status, ordered events | Claude | 2026-11-05T11:21:52+02:00 |
| `d8aff32a3d3840f6825c5885922069138763f43a` | ci(slice-01b-r01): compile jarvis/tests and run tests_vexel and config check | Claude | 2026-11-05T11:21:52+02:00 |
| `372c21905ca2478c8b545e6b67af528a587e51b0` | docs(slice-01b-r01): record corrections, limitations and CANDIDATE_PASS status | Claude | 2026-11-05T11:21:52+02:00 |

Todos os commits têm o trailer `Co-Authored-By: Claude Opus 5.5` e `Claude-Session`.

## 3. Gates G1–G7

| Gate | Verificação | Resultado |
|---|---|---|
| G1 | `git fetch origin`; `origin/develop` == `f3e1456…` | **PASS**: `f3e145698483f8fb67c8f12b8752a5efd29a3e9a`; reconfirmado imediatamente antes do push |
| G2 | `git rev-parse --abbrev-ref HEAD` | **PASS**: `develop` |
| G3 | `git status --porcelain --untracked-files=all` | **PASS**: vazio; sem stash. Nota: o ambiente assinalou uma alteração a `jarvis/tools/allowlist.py`; a verificação mostrou o blob no disco = blob em HEAD (`1f867a1…`), sem diferença de conteúdo |
| G4 | 6 commits, iguais ao R01; ancestralidade | **PASS**: 6/6 SHAs e mensagens conferem com o relatório R01 (S em todos); `merge-base --is-ancestor origin/develop HEAD` = verdadeiro; 0 merges |
| G5 | Âmbito do diff `f3e1456..HEAD` | **PASS**: 40 ficheiros, todos em `jarvis/`, `configs/`, `tests_vexel/`, `docs/01_CURRENT.md`, `docs/03_BACKLOG.md`, `.github/workflows/source-integrity.yml`; intersecção com os 182 destinos do manifesto = **nenhuma**; blob SHA em HEAD = manifesto 182/182 (inclui `pyproject.toml`, `wyzer.toml`, `installer/install.ps1`); `jarvis_lab/` e `tests_lab/` inalterados |
| G6 | Workflow | **PASS**: `.github/workflows/source-integrity.yml`: trigger `push: branches: [develop]` (l.3–4) e `pull_request` para `develop`/`main` (l.5–6); integridade `python scripts/verify_import.py` (l.23–24); compilação `compileall … jarvis tests_vexel tests_lab` (l.25–26); `pytest -q tests_lab` (l.41–42); `pytest -q tests_vexel` (l.43–44); `python -m jarvis --check-config` (l.45–46). É o único workflow do repositório |
| G7 | Artefactos | **PASS**: `+4287/−1`; 0 ficheiros binários no `numstat`; nenhum `.exe/.dll/.ps1/.bat/.cmd/.msi/.onnx/.tflite/.bin/.pt/.gguf/.safetensors/.wav/.mp3/.zip/.whl`; todos os ficheiros novos com modo `100644` (nenhum executável); 0 padrões de segredo; 0 dados pessoais nas linhas adicionadas |

## 4. PR #2

| Campo | Valor |
|---|---|
| Estado | aberto, **draft**, não merged |
| Título | WIP: importar Wyzer v0.3.1 e preparar núcleo headless/QA remoto |
| Base → head | `main` (`10aa464…`) ← `develop` |
| Head SHA | `372c21905ca2478c8b545e6b67af528a587e51b0` (reflecte a nova HEAD) |
| Commits / ficheiros | 81 / 256 |
| `mergeable_state` | `clean` |
| Checks no SHA | `source-integrity` e `headless-contract` = success, nos dois runs (push e pull_request) |

O PR foi apenas lido: não o alterei, não o comentei e não fiz merge. O push para `develop` actualizou a head do PR, como é normal num PR aberto a partir de `develop`, e isso disparou o run `pull_request` automaticamente.

## 5. GitHub Actions

Workflow: **Jarvis Source Integrity**. Runner `ubuntu-latest` → imagem `ubuntu-26.04`. Dois runs para o SHA publicado, ambos na tentativa 1:

| Run | Evento | headSha | Conclusão | Duração |
|---|---|---|---|---|
| [42007778632](https://github.com/rightware-corporations/jarvis/actions/runs/42007778632) | push | `372c21905ca2478c8b545e6b67af528a587e51b0` | **success** | 10:05:29Z → 10:05:44Z (15 s) |
| [42007788982](https://github.com/rightware-corporations/jarvis/actions/runs/42007788982) | pull_request (#2) | `372c21905ca2478c8b545e6b67af528a587e51b0` | **success** | 10:05:33Z → 10:05:49Z (16 s) |

### Jobs

| Run | Job | Python | Conclusão | Passos |
|---|---|---|---|---|
| push | [source-integrity](https://github.com/rightware-corporations/jarvis/actions/runs/42007778632/job/127178795780) | CPython 3.11.17 | success | todos success |
| push | [headless-contract](https://github.com/rightware-corporations/jarvis/actions/runs/42007778632/job/127178795804) | CPython 3.11.17 | success | todos success |
| pull_request | [source-integrity](https://github.com/rightware-corporations/jarvis/actions/runs/42007788982/job/127178828799) | CPython 3.11.18 | success | todos success |
| pull_request | [headless-contract](https://github.com/rightware-corporations/jarvis/actions/runs/42007788982/job/127178829011) | CPython 3.11.18 | success | todos success |

### Evidência por item (igual nos dois runs)

1. **Integridade Wyzer:** `Wyzer upstream: XtraWyze/Wyzer-Ai@db83c085…` · `Source integrity: 182/182` · `Binary assets intentionally excluded: 44` · `SOURCE_INTEGRITY_PASS`.
2. **Compilação Python:** `python -m compileall -q wyzer tests scripts jarvis tests_vexel tests_lab`, sem qualquer saída; passo success (`bash -e`).
3. **`tests_lab`:** 16 testes; 16 passed, 0 failed, 0 error, 0 skipped, 0 xfail. Um aviso: `StarletteDeprecationWarning` (httpx com `starlette.testclient`), já existente.
4. **`tests_vexel`:** 305 testes; 305 passed, 0 failed, 0 error, 0 skipped, 0 xfail.
5. **`python -m jarvis --check-config`:** saída JSON (`llm_provider: ollama`, `llm_model: qwen3.5:4b`, `llm_endpoint: http://127.0.0.1:11434/`, `whisper_model: small`, `tts_adapter: windows_system`, `activation: manual`, `allowed_applications: [calculator, notepad]`, `allow_real_windows_actions: false`) e `CONFIG_OK`; passo success (exit 0).
6. **Resultado final e SHA:** os 4 jobs estão em success, e o `headSha` dos dois runs é igual a HEAD_DEPOIS. Não há `##[error]` nos logs.

**Como as contagens foram obtidas.** O workflow chama `pytest -q`, e o `pyproject.toml` já define `addopts = "-q"`. Com `-qq`, o pytest não imprime a linha «N passed». As contagens foram por isso extraídas, por script, das linhas de progresso do log (um carácter por teste, `.`/`F`/`E`/`s`/`x`). O `tests_vexel` mostra 72+72+72+72+17 = 305 pontos e nenhum outro carácter, o que coincide com as 305 execuções locais.

**Avisos encontrados (nenhum bloqueante):**
- `##[warning] Node.js 20 is deprecated…`: `actions/checkout@v4` e `actions/setup-python@v5` foram forçados a correr em Node 24.
- `DeprecationWarning: punycode` emitido pelo Node.
- `StarletteDeprecationWarning` no `tests_lab`.
- Uma dica do `git` sobre o nome da branch por omissão no checkout.

**Dependências resolvidas pelo `pip` no CI:** pydantic 2.14.3, pydantic-core 2.50.4, psutil 7.2.2, pytest 8.4.2, fastapi 0.162.0, httpx 0.28.1, starlette 1.10.0, uvicorn 0.54.0. Localmente o venv tinha pydantic 2.12.3 e psutil 7.1.3; os testes passam nas duas combinações.

Ficheiro de excertos: `JAR-SLICE-01B-PUB-ci-evidence.txt`. Os tokens aparecem como `***` nos logs do GitHub e não foram reproduzidos.

## 6. Integridade upstream Wyzer

| Momento | Fonte | Resultado |
|---|---|---|
| Antes (R01) | HEAD local, `verify_import.py` | 182/182 |
| Antes do push (G5) | blob SHA em HEAD vs manifesto | 182/182, 0 ficheiros do manifesto no diff |
| CI (2 runs) | `verify_import.py` no runner | 182/182 |
| Depois do push | `git archive origin/develop` + `verify_import.py`; blob SHA em `origin/develop` vs manifesto | 182/182 e 182/182 |

## 7. Validation checklist

- [x] origin/develop era `f3e1456…` antes do push
- [x] branch develop, árvore limpa
- [x] 6 commits exactamente iguais ao R01
- [x] sem ficheiros protegidos/upstream alterados
- [x] workflow contém tests_vexel e check-config
- [x] push normal, sem força
- [x] HEAD remota == HEAD local
- [x] Wyzer 182/182 no CI
- [x] compilação Python OK
- [x] tests_lab OK (16/16)
- [x] tests_vexel OK (305/305)
- [x] --check-config OK
- [x] SHA testado == SHA publicado
- [x] integridade upstream verificada após push
- [x] nenhum merge para main, nenhuma branch/worktree/tag nova (remoto: só `refs/heads/develop` e `refs/heads/main`; 0 tags)

## 8. Limitações e riscos residuais

1. **Validação apenas simulada.** O CI prova contratos com fakes. Não prova Ollama, Whisper, vozes, microfone, latência nem abertura real de aplicações.
2. **Resumo do pytest suprimido** (`-q` duplicado). As contagens são fiáveis mas indirectas. *Proposta, não aplicada:* trocar no workflow `pytest -q` por `pytest -rA` ou `pytest -ra`, para que o log mostre a linha final e os eventuais skips.
3. **Versões não fixadas no CI** (intervalos `>=,<`). Uma release nova de pydantic ou psutil pode alterar o comportamento entre runs. Já aconteceu aqui sem impacto (pydantic 2.14.3 no CI contra 2.12.3 local).
4. **Python do runner variável:** 3.11.17 num run e 3.11.18 no outro, conforme a cache da imagem.
5. **Avisos de deprecação** das actions em Node 20. Devem ser actualizadas (`checkout@v5`, `setup-python@v6`) numa tarefa própria antes de o GitHub deixar de as aceitar. Não alterei nada.
6. Mantêm-se os riscos documentados na R01: filtro de afirmações baseado em padrões, `InProcessExecutor` sem cancelamento de ferramentas em curso, evidência de `SUCCEEDED` real por definir (01D), wake word bloqueada, licença do espeak-ng pendente.
7. **Processo.** Foi preciso anexar o repositório à sessão com acesso `push` para usar a API do GitHub. O registo do clone gerido falhou porque o caminho difere do esperado, mas não teve impacto: o push e as leituras usaram o clone de trabalho existente.

## 9. Estado final

**`REMOTE_CI_PASS`.** Todos os gates passaram, o push foi fast-forward, os 4 jobs estão verdes nos dois runs do SHA exacto publicado `372c21905ca2478c8b545e6b67af528a587e51b0`, e os seis itens de evidência têm URL.

---

## 10. Próxima tarefa — JAR-SLICE-01C (identificação apenas; não iniciada)

**Objectivo.** Provar os seis comandos da fatia com componentes reais num PC Windows de QA autorizado: Ollama com `qwen3.5:4b` e tool calling, Faster-Whisper `small` em português com microfone, TTS SAPI com uma voz PT instalada, ainda com o lançador **simulado** (a abertura real fica para a 01D).

**Âmbito.**
- Inventário do PC: CPU/GPU/RAM, Windows, Python 3.11, vozes SAPI disponíveis (Maria, Helia, outra?), dispositivo de áudio.
- Instalação manual e documentada de Ollama e do modelo, e do modelo Whisper (`small`, MIT).
- Execução do modo texto e depois do modo voz com activação manual.
- Medição de latências por fase (STT, LLM, TTS).
- Confirmação real de `sim`/`não`/`cancela`, incluindo falha de TTS e timeout.
- Corpus de frases PT-MZ, com gravações **guardadas apenas localmente**.
- Relatório PASS/FAIL por comando.

**Dependências.**
- PC de QA Windows autorizado pela RIGHTWARE e respectivo operador.
- Autorização explícita para instalar Ollama e descarregar os pesos do `qwen3.5:4b` e do `faster-whisper-small`.
- Decisão sobre a voz TTS: SAPI disponível, ou Kokoro depois da revisão da licença do espeak-ng.
- Política para as gravações de voz (repositório público: nunca as publicar).

**Riscos.**
- Desempenho do modelo de 4B no hardware disponível (latência e qualidade do tool calling em português).
- Exactidão do STT com sotaque e vocabulário PT-MZ.
- Ausência de voz PT instalada no Windows.
- Diferenças Linux/Windows (tzdata para `Africa/Maputo`, caminhos, áudio).
- O modelo real pode produzir chamadas ou textos que os fakes não cobriram; o filtro de afirmações e a política de confirmação têm de ser re-verificados com o modelo real.
- Risco de privacidade das gravações.
- Licenças dos pesos e das vozes, a confirmar antes de qualquer distribuição.
