# VEXEL Jarvis — Issa Edition | Handoff

**Data:** 2026-11-04 | **Estado:** upstream importado em `develop`; integridade 182/182, compilação e 5 testes headless PASS em GitHub Actions.

## Decisões
- **Base:** [XtraWyze/Wyzer-Ai](https://github.com/XtraWyze/Wyzer-Ai) `v0.3.1`, SHA `db83c085feca32d3c091361165cb9ac7ecadafe0`.
- **Produto:** VEXEL Jarvis — Issa Edition, com português como língua prioritária.
- **Inferência:** auto-hospedada / Ollama como preferencial; sem subscrição de IA obrigatória. Infraestrutura pode ter custo.
- **Desenvolvimento:** remoto; nenhuma operação no computador do operador; acesso ao PC do Issa só para QA de entrega autorizado.
- **Distribuição:** local, servidor ou híbrida por decidir; browser remoto por si só não controla Windows.
- **Repositório:** `rightware-corporations/jarvis` (PÚBLICO).
- **Branches-alvo:** apenas `main` e `develop`. A antiga branch `feat/wyzer-v031-core-import` está inactiva e ainda precisa de remoção.

## Implementação actual
- 182 fontes textuais e de código do upstream importadas, **182 hashes Git iguais aos originais**; 44 assets binários deliberadamente omitidos.
- `LICENSE`, `NOTICE.md`, `UPSTREAM_PROVENANCE.md`, manifesto de SHA e `docs/upstream/` preservados.
- `jarvis_lab/headless.py` cria núcleo Wyzer com ferramentas vazias, sem acesso a OS; `tests_lab/` escritos e **cinco contratos headless PASS em runner GitHub Ubuntu**.
- Workflow `.github/workflows/source-integrity.yml` executado: [run 41813747553](https://github.com/rightware-corporations/jarvis/actions/runs/41813747553) **PASS em dois jobs**; 5 testes headless passaram.
- Nada foi instalado ou executado no PC do operador nem do Issa.

## Ordem de leitura
1. `01_CURRENT.md` — estado exacto e limitações.
2. `02_ARCHITECTURE.md` — arquitetura web/headless/Windows.
3. `03_BACKLOG.md` — tarefas por prioridade e gates.
4. `04_ACCEPTANCE.md` — provas para declarar prontidão.
5. `05_SOURCE_AUDIT_P0.md` — riscos de código identificados.
6. `06_REMOTE_QA.md` e `08_HEADLESS_ADAPTER.md` — fluxo de testes remoto.

## Regras
- Nunca confundir código publicado, prova estática, teste executado e produto validado.
- Não alterar `rightware-corporations/vexel` ou `vexel-website`.
- Não transformar ChatGPT/Claude em dependência de inferência final.
- Não publicar dados pessoais, tokens, vozes ou wake models sem direitos verificáveis.
- O lab não expõe ferramentas de Windows ou shell. Autorizações e políticas antes de qualquer execução real.
- `main` é estável; funcionalidades entram via `develop` e revisão.
