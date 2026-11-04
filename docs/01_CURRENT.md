# 01 — CURRENT

**Data:** 2026-11-04 | **Repositório:** `rightware-corporations/jarvis` (público)

## Estado
- **BASE ESCOLHIDA:** Wyzer `v0.3.1` / upstream commit `db83c085feca32d3c091361165cb9ac7ecadafe0`.
- **IMPORTAÇÃO:** 182/182 ficheiros textuais/ código copiados, comparados por hash SHA Git; ZERO diferença. Excluídos 42 PNG + 2 ONNX.
- **LICENÇA DO CÓDIGO:** MIT, com NOTICE original. Licenças de assets/modelos/vozes por rever antes da distribuição.
- **BRANCHES:** somente `main` e `develop` verificadas via GitHub API. A antiga `feat/wyzer-v031-core-import` foi eliminada por workflow temporário PASS (run 41814286015); workflow privilegiado removido.
- **CÓDIGO DO UPSTREAM:** `wyzer/` (89 ficheiros), `tests/` (49), configs/scripts/installer/docs em `develop`.
- **INTEGRIDADE:** validada estaticamente por comparação Git de árvores. Workflow remoto criado.
- **CI REMOTO:** [run 41813747553](https://github.com/rightware-corporations/jarvis/actions/runs/41813747553) **PASS nos jobs `source-integrity` e `headless-contract`**. Integridade SHA 182/182 e compilação sintática PASS; 5 testes headless PASS. Foram corrigidas falhas iniciais de dependência `psutil`.
- **HEADLESS:** `jarvis_lab/headless.py` usa `Orchestrator` original com registry vazio, e `tests_lab/` contém testes de contrato; **5 PASS em Ubuntu/Python 3.11 remoto**.
- **INFERÊNCIA REAL:** Ollama previsto; endpoint/hosting e modelo em produção por decidir.
- **PORTUGUÊS:** ainda sem implementação/validação.
- **WEB LAB:** API e UI não implementadas; não há deploy.
- **PC ISSA:** não utilizado; requisitos de hardware desconhecidos.
- **ENTREGA:** não pronta.

## Verificações efectuadas
- GitHub upstream `v0.3.1`: 226 blobs, 182 importados, 44 assets binários excluídos.
- Hash original de todos os 182 importados verificado com GitHub git trees (nenhum mismatch).
- `Orchestrator(registry, executor, provider,...)` suporta injecção; `jarvis_lab` separa-se dos tool packs Win32.
- `MemoryStore` original não recebe `user_id`; a composição lab cria uma DB SQLite por identificador de utilizador.
- Configuração upstream: `small.en`, UI/voz inglesa, `coding_agent.enabled=true`. Lab **não** activa coding agent nem ferramentas do Windows.
- Confirmação e controlo determinístico upstream reconhecem expressões inglesas; PT requer localização cuidadosa.

## Gates seguintes
1. **Gate QA remoto (parcial PASS):** integridade, compilação e cinco contratos headless confirmados no run 41813747553; testes de integração mais profundos pendentes.
2. **Gate headless Linux (parcial PASS):** instância do `Orchestrator` com Pydantic e psutil no GitHub Ubuntu; mapear restantes dependências e plataforma.
3. **Gate segurança:** testar negação, confirmação, cancelamento e separação por utilizador; nenhuma ferramenta real no lab.
4. **Gate IA real:** escolher e testar endpoint Ollama remoto, tool calling e latência.
5. **Gate web:** API autenticada, ambiente isolado e UI de demonstração, sem exposição pública insegura.
6. **Gate PT:** STT, TTS, wake word, confirmações e comandos em português.
7. **Gate entrega:** direitos de modelos/assets, instalador, hardware e QA no equipamento Issa autorizado.

## Próxima execução
Passou o primeiro workflow remoto. Próximo: testes de confirmação/cancelamento, isolamento de serviços e iniciação de API headless autenticada / model runner. **A presença de novos testes não equivale a PASS até existir execução e logs correspondentes.**
