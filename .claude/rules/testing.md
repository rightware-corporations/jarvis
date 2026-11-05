---
paths:
  - "tests_vexel/**/*"
  - "tests_lab/**/*"
  - "tests_desktop/**/*"
  - "jarvis/**/*.py"
  - "apps/**/*.py"
  - "qa/**/*.py"
  - ".github/workflows/*"
---

# Regras de testes

Procedimento completo: skill `jarvis-quality-gates`. Plano de QA real: [`docs/25_JAR-SLICE-01C_WINDOWS_QA_PLAN.md`](../../docs/25_JAR-SLICE-01C_WINDOWS_QA_PLAN.md).

**Onde ficam os testes novos:**
- núcleo em `tests_vexel/`;
- laboratório em `tests_lab/`;
- Orb em `tests_desktop/`.

`tests/` é upstream protegido: não se edita.

**Como se escrevem:**
- Só fakes e fixtures sintéticos (`tests_vexel/fakes.py`): sem microfone, GPU, rede, Ollama, modelos ou ferramentas Windows reais.
- Excepção autorizada (D01, JAR-NET-01): servidores HTTP sintéticos **só em `127.0.0.1` ou `::1`, em portas efémeras** (ex.: `tests_vexel/ollama_loopback.py`), com threads e respostas por script.
  - Continuam proibidas ligações externas, modelos remotos, serviços pagos e portas expostas.
  - A evidência destes testes é `HTTP_CONTRACT_PASS`, nunca inferência real.
- Não se remove nem se enfraquece um teste, nem o guard de processos, sem justificação aprovada.
- Um teste tem de poder falhar. Por exemplo, nada de `or True`.
- Não há Hypothesis (dependência não aprovada).

**Ao correr:**
- Python 3.11.
- `pytest` sem `-q` extra (o `pyproject` já tem `addopts=-q`; um segundo `-q` esconde o resumo).
- Os testes do Orb correm com `QT_QPA_PLATFORM=offscreen`.

**Contagens de referência** em `1104ac4`:
- `tests_vexel` 443;
- `tests_lab` 16;
- `tests_desktop` 87.

Uma descida inexplicada é FAIL.

**Diferenças Windows:**
- correr sem `cmd`/`ver`;
- `core.autocrlf false`;
- encoding cp1252;
- `tzdata` para `Africa/Maputo`.

O job `windows-python` existe para apanhar estas diferenças.

**Como se reporta:**
- PASS só com o comando, o resultado e o SHA.
- Fakes provam contratos, não áudio, LLM ou Windows reais: escrever «simulado».
