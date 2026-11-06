---
name: jarvis-quality-gates
description: Gates de qualidade do VEXEL Jarvis antes de commit e push — integridade Wyzer 182/182, compilação, tests_vexel, tests_lab, tests_desktop (offscreen), check-config, varrimento de segredos e acompanhamento dos 6 jobs de CI.
when_to_use: Antes de cada commit, antes de um push autorizado para develop, e ao verificar o CI de uma HEAD nova.
---

# jarvis-quality-gates

Os comandos só lêem e testam; nenhum apaga ficheiros ou altera Git.

**Commit e push:**
- O commit é feito por quem executa, depois de todos os gates passarem.
- O push só se faz com autorização explícita da ordem em curso.

## 1. Ambiente

Python 3.11, num venv próprio. Dependências (as mesmas do CI, `.github/workflows/source-integrity.yml`):

```
python -m pip install 'pydantic>=2.8,<3' 'pytest>=8,<9' 'psutil>=6,<8' 'fastapi>=0.115,<1' 'httpx>=0.27,<1' 'uvicorn>=0.30,<1'
python -m pip install 'PySide6-Essentials==6.6.1'     # só para tests_desktop
```

Não se instalam modelos, Ollama, faster-whisper nem sounddevice reais fora do plano de QA.

## 2. Gates locais (todos PASS)

| # | Comando | Esperado |
|---|---|---|
| Q1 | `python scripts/verify_import.py` | 182/182 |
| Q2 | `python -m compileall -q wyzer tests scripts jarvis apps tests_vexel tests_lab` | sem saída |
| Q3 | `python -m pytest tests_vexel tests_lab` | sem falhas; ≥ 443 + 16 |
| Q4 | `QT_QPA_PLATFORM=offscreen python -m pytest tests_desktop` | sem falhas; ≥ 87 |
| Q5 | `python -m jarvis --check-config` | OK |
| Q6 | `git diff --name-only origin/develop` comparado com os `destination` do manifesto | intersecção vazia |
| Q7 | `git diff origin/develop \| grep -inE 'token\|secret\|password\|api[_-]?key\|BEGIN .*PRIVATE'` | só falsos positivos explicados |
| Q8 | `git branch -a` | só `main` e `develop` |

Notas:
- Não acrescentar `-q` ao pytest: o resumo desaparece.
- Q6 em Python:

  ```
  python - <<'EOF'
  import json,subprocess
  m={e["destination"] for e in json.load(open("upstream-v0.3.1-manifest.json"))["imported"]}
  d=set(subprocess.run(["git","diff","--name-only","origin/develop"],capture_output=True,text=True).stdout.split())
  print(sorted(m & d) or "Q6 PASS")
  EOF
  ```

  Para validar commits locais ainda não publicados, usar `origin/develop`; para um commit já publicado, usar `HEAD~N`.

## 3. CI depois de um push autorizado

```
gh run list --branch develop --limit 4
gh run watch <id> --exit-status
```

Os 6 jobs:
- `source-integrity`;
- `headless-contract`;
- `windows-preflight-parse`;
- `windows-python`;
- `desktop-orb (ubuntu-latest)`;
- `desktop-orb (windows-latest)`.

Há um run de `push` e, enquanto o PR #2 estiver aberto, um de `pull_request`.

**Regras do CI:**
- Registar o SHA, os IDs e os URLs.
- Com jobs a correr, o estado é `REMOTE_CI_PENDING`, nunca PASS.
- Se um job falhar:
  - ler o log (`gh run view <id> --log-failed`);
  - corrigir num commit novo;
  - nunca reescrever o commit publicado.

## 4. Rótulos no relatório

- `TESTADO` só com o comando, o resultado, o SHA e o ambiente.
- Testes com fakes provam contratos; escrever «simulado» para áudio, LLM e Windows.
