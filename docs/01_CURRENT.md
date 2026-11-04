# 01 — CURRENT

**Data:** 2026-11-04 | **Repositório:** `rightware-corporations/jarvis` (público)

## Estado
- **BASE ESCOLHIDA:** Wyzer `v0.3.1` / upstream commit `db83c085feca32d3c091361165cb9ac7ecadafe0`.
- **IMPORTAÇÃO:** 182/182 ficheiros textuais/ código copiados, comparados por hash SHA Git; ZERO diferença. Excluídos 42 PNG + 2 ONNX.
- **LICENÇA DO CÓDIGO:** MIT, com NOTICE original. Licenças de assets/modelos/vozes por rever antes da distribuição.
- **BRANCHES:** `main` e `develop` criadas; `feat/wyzer-v031-core-import` ainda existe e deve ser removida.
- **CÓDIGO DO UPSTREAM:** `wyzer/` (89 ficheiros), `tests/` (49), configs/scripts/installer/docs em `develop`.
- **INTEGRIDADE:** validada estaticamente por comparação Git de árvores. Workflow remoto criado.
- **CI REMOTO:** NENHUMA execução confirmada; NÃO declarar PASS.
- **HEADLESS:** `jarvis_lab/headless.py` usa `Orchestrator` original com registry vazio, e `tests_lab/` contém testes de contrato; execução pendente.
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
1. **Gate QA remoto:** observar execução real do workflow; capturar run ID, falhas e logs.
2. **Gate headless Linux:** assegurar que imports do `Orchestrator` funcionam com dependências mínimas.
3. **Gate segurança:** testar negação, confirmação, cancelamento e separação por utilizador; nenhuma ferramenta real no lab.
4. **Gate IA real:** escolher e testar endpoint Ollama remoto, tool calling e latência.
5. **Gate web:** API autenticada, ambiente isolado e UI de demonstração, sem exposição pública insegura.
6. **Gate PT:** STT, TTS, wake word, confirmações e comandos em português.
7. **Gate entrega:** direitos de modelos/assets, instalador, hardware e QA no equipamento Issa autorizado.

## Próxima execução
Obter PASS/FAIL reais do workflow no GitHub e corrigir as falhas, depois iniciar API headless e model runner. **A presença dos testes não equivale a PASS.**
