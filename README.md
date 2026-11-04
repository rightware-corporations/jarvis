# VEXEL Jarvis — Issa Edition

Assistente de voz da RIGHTWARE, derivado de [Wyzer AI](https://github.com/XtraWyze/Wyzer-Ai).

> **Estado (4 nov 2026):** código-fonte original importado em `develop`, integridade verificada; adaptador headless e contratos de teste criados. Os **cinco testes headless** e a integridade das fontes passaram no GitHub Actions; não existe ainda aplicação web funcional nem release para o utilizador.

## Branches
- **`main`:** documentação e base estável; não desenvolver directamente aqui.
- **`develop`:** única branch de engenharia activa. Contém upstream + adaptador headless.
- **`feat/wyzer-v031-core-import`:** branch temporária antiga, sem uso, a eliminar para ficar estritamente com duas branches.

## Proveniência
- Upstream: `XtraWyze/Wyzer-Ai`
- Tag: `v0.3.1`
- Commit: [`db83c085feca32d3c091361165cb9ac7ecadafe0`](https://github.com/XtraWyze/Wyzer-Ai/commit/db83c085feca32d3c091361165cb9ac7ecadafe0)
- **182/182** ficheiros de código/texto verificados contra os hashes Git originais; 44 binários (imagens/ONNX) excluídos até revisão jurídica.
- `LICENSE` e `NOTICE.md`: licença MIT do código; licenças de vozes/modelos/assets verificadas separadamente.
- `UPSTREAM_README.md` e `docs/upstream/`: documentação de origem preservada.
- `UPSTREAM_PROVENANCE.md` / `upstream-v0.3.1-manifest.json`: rasto auditável.

## QA remoto
Workflow: [Source Integrity](.github/workflows/source-integrity.yml).
- `python scripts/verify_import.py`: verifica a integridade dos ficheiros originais.
- `python -m compileall -q wyzer tests scripts`: compila sintaticamente.
- `python -m pytest -q tests_lab`: testa o laboratório headless com Pydantic e provider **simulado**.

**Executado em GitHub Actions:** execução [41813747553](https://github.com/rightware-corporations/jarvis/actions/runs/41813747553) com ambos os jobs PASS: integridade 182/182, sintaxe e cinco contratos headless. Isto não valida voz, Ollama ou ferramentas Windows.

## Desenvolvimento
- `jarvis_lab/headless.py`: constrói o `Orchestrator` original com registry vazio, sem acesso ao Windows.
- `tests_lab/`: testes de negação de ferramentas e memória isolada.
- Não existe ainda servidor web, login, provider Ollama validado ou STT/TTS português aprovado.
- A distribuição local, servidor ou híbrida continua pendente de validação.

## Documentação
Começar em [`docs/00_START_HERE.md`](docs/00_START_HERE.md), depois `01_CURRENT.md`, `02_ARCHITECTURE.md`, `03_BACKLOG.md`, `04_ACCEPTANCE.md`, `05_SOURCE_AUDIT_P0.md`, `06_REMOTE_QA.md` e `08_HEADLESS_ADAPTER.md`.

**Segurança:** repositório público. Não publicar segredos, dados pessoais, gravações reais, credenciais ou modelos sem direitos verificados. O operador não precisa de instalar nada no seu computador.
