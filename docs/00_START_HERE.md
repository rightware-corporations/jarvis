# VEXEL Jarvis — Issa Edition | Handoff

> **HANDOFF ACTUAL / PRIMEIRA LEITURA (06/11/2026):** [MASTER HANDOFF V2 — estado, decisões, Kaggle real, falhas cognitivas, roadmap e recuperação](26_MASTER_HANDOFF_2026-11-06.md).
> **Estado recente:** Ollama/Qwen3.5 reais testados no Kaggle; JAR-CONF-01 com CI e B6 real PASS; B7 11/12 e falha de intenção; JAR-COG-01 entretanto **publicada** no `develop` (gate de intenção + contexto, testes simulados); **JAR-COG-01-R reteste real no Kaggle pendente**. Ver **ADENDA A** do Master Handoff. `main` estável; `develop` engenharia; PR #2 Draft. As secções de 04–05/11 abaixo são **histórico**, não o estado mais recente.


> **Estrutura do repositório (05/11/2026):** [ADR-0001](adr/0001-estrutura-do-repositorio.md) — onde vivem o backend (`jarvis/`), o futuro frontend de desktop, a futura base de dados, o laboratório web e o que nunca entra no git. Decisões de arquitectura em [`docs/adr/`](adr/README.md); relatórios de fase em [`docs/reports/`](reports/README.md).


## HANDOFF MESTRE DE RECUPERAÇÃO — 04/11/2026

> **PRIMEIRO DOCUMENTO A LER:** [20_RECOVERY_START_HERE_2026-11-04.md](20_RECOVERY_START_HERE_2026-11-04.md). A situação evoluiu além do primeiro import.
>
> **Pacote completo:** [21_MASTER_HANDOFF_2026-11-04.md](21_MASTER_HANDOFF_2026-11-04.md) (história integral, Wyzer, voz, HUD, Claude, Manus); [22_DECISION_REGISTER_2026-11-04.md](22_DECISION_REGISTER_2026-11-04.md) (aprovado vs proposto); [23_EXECUTION_PLAYBOOK_2026-11-04.md](23_EXECUTION_PLAYBOOK_2026-11-04.md) (checklist e prompt de recuperação).
>
> **AGORA:** plugin Claude v0.1.0 com 9 skills instalado visualmente, v0.1.1 e CLAUDE.md definitivo pendentes; **Manus foi solicitado para screenshots reais do frontend adewaskar no Chromium**, sem resultados entregues. **Nenhuma integração HUD, modelo Ollama real, voz PT funcional ou Jarvis entregue.** Os cinco finalistas do handoff antigo são históricos e NÃO substituem a escolha Wyzer.


**Data:** 2026-11-04 | **Estado:** upstream importado em `develop`; integridade 182/182, compilação e 5 testes headless PASS em GitHub Actions.

## Decisões
- **Base:** [XtraWyze/Wyzer-Ai](https://github.com/XtraWyze/Wyzer-Ai) `v0.3.1`, SHA `db83c085feca32d3c091361165cb9ac7ecadafe0`.
- **Produto:** VEXEL Jarvis — Issa Edition, com português como língua prioritária.
- **Inferência:** auto-hospedada / Ollama como preferencial; sem subscrição de IA obrigatória. Infraestrutura pode ter custo.
- **Desenvolvimento:** remoto; nenhuma operação no computador do operador; acesso ao PC do Issa só para QA de entrega autorizado.
- **Distribuição:** local, servidor ou híbrida por decidir; browser remoto por si só não controla Windows.
- **Repositório:** `rightware-corporations/jarvis` (PÚBLICO).
- **Branches confirmadas:** apenas `main` e `develop`. A antiga `feat/wyzer-v031-core-import` foi eliminada com sucesso (Actions 41814286015), e o workflow de limpeza foi removido.

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

## Pesquisa complementar — HUD flutuante e VoiceStudio (2026-11-04)

- [12_HUD_REFERENCES_AND_UX_VISION.md](12_HUD_REFERENCES_AND_UX_VISION.md): estudo das referências visuais enviadas (vídeo do orb, captura de grafo, guia comercial, guia Claude), inventário open source, licenças e proposta de Floating/Expanded/Graph HUD. **Design não aprovado, nada importado**.
- [13_VOICESTUDIO_STATIC_ASSESSMENT.md](13_VOICESTUDIO_STATIC_ASSESSMENT.md): auditoria de `debpalash/VoiceStudio` para STT/TTS e voz PT; APIs locais, recursos, riscos AGPL e pesos OmniVoice não comerciais. **Candidato avaliado, não seleccionado nem executado**.
- Nenhuma alteração ao motor Wyzer, ao código do frontend ou aos 182 hashes de origem nesta pesquisa. Evitar confundir interfaces de referência com Jarvis operacional e documentação com QA.
