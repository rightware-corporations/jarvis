# VEXEL Jarvis — Issa Edition

Base de engenharia para o assistente de voz Jarvis desenvolvido pela RIGHTWARE a partir de [Wyzer AI](https://github.com/XtraWyze/Wyzer-Ai).

> Estado: fundação e auditoria estática. O código upstream ainda não foi importado, não há testes de runtime aprovados nem deploy de demonstração.

## Fonte escolhida

- Repositório upstream: `XtraWyze/Wyzer-Ai`
- Tag: `v0.3.1`
- Commit fixado: [`db83c085feca32d3c091361165cb9ac7ecadafe0`](https://github.com/XtraWyze/Wyzer-Ai/commit/db83c085feca32d3c091361165cb9ac7ecadafe0)
- Licença do código upstream: MIT; modelos, vozes e outros assets exigem verificação específica.

## Direcção

Desenvolvimento e testes remotos, sem instalação no computador de desenvolvimento do operador. Um laboratório web deve usar ferramentas simuladas; o controlo real do Windows depende de um executor local autorizado. O modelo de inferência deve ser local ou auto-hospedado, sem APIs pagas obrigatórias. Português será a língua prioritária.

## Documentação

Começar por [`docs/00_START_HERE.md`](docs/00_START_HERE.md), seguido de `01_CURRENT.md`, `02_ARCHITECTURE.md`, `03_BACKLOG.md`, `04_ACCEPTANCE.md` e `05_SOURCE_AUDIT_P0.md`.

**Nota:** este repositório é público. Não incluir credenciais, dados pessoais do destinatário ou gravações reais de voz nos testes.
