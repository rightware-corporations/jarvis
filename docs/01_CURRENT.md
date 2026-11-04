# 01 — CURRENT

## Estado de referência (2026-11-04)
- **Escolha upstream:** DEFINIDA — `XtraWyze/Wyzer-Ai` / `v0.3.1` / `db83c085feca32d3c091361165cb9ac7ecadafe0`.
- **Licença do código upstream:** MIT, identificada no ficheiro LICENSE; direitos de modelos/vozes/assets sujeitos a verificação separada.
- **Código upstream dentro da RIGHTWARE:** NÃO IMPORTADO.
- **Repositório definitivo Jarvis:** CRIADO — `rightware-corporations/jarvis` (público); documentos migrados para `docs/` na `main`.
- **Testes do upstream:** NÃO EXECUTADOS.
- **Laboratório web:** NÃO IMPLEMENTADO.
- **Deploy cloud:** NÃO EXECUTADO.
- **Português:** NÃO IMPLEMENTADO/VALIDADO.
- **IA local/servidor:** fornecedor Ollama identificado; modelo e hardware finais por definir.
- **PC do Issa:** NÃO ACEDIDO.
- **Entrega ao cliente:** NÃO PRONTA.

## Evidência estática do upstream
- `pyproject.toml`: Python >=3.11,<3.12, runtime orientado para Windows.
- `wyzer.toml`: `llm.provider=ollama`; `model=qwen3.5:4b`; `speech.whisper_model=small.en`; `speech.voice=af_heart`; `coding_agent.enabled=true`.
- `wyzer/app/cli.py`: `build_assistant(...)` constrói o Orchestrator, registry, executor isolado, memória e tarefas persistentes.
- `docs/ARCHITECTURE.md`: ciclo `provider -> registry -> validação -> confirmação -> worker -> resultado`; sessão, memória, ferramentas, percepção; não substitui QA real.
- `docs/SAFETY.md`: confirmações de operações consequentes, isolamento e interrupções descritos.
- `docs/MODEL_ACCEPTANCE.md`: suites de aceitação simuladas sem executar ferramentas reais.
- `docs/SPEECH.md`: wake word `Hey Wyzer`, STT local e TTS local; `--voice` opt-in.
- MIT não concede automaticamente direitos sobre modelos e vozes externos.

## Bloqueadores/gates actuais
1. Importar upstream no repositório Jarvis independente com histórico/licença ou snapshot rastreável.
2. Verificar se componentes WinRT/pywinauto/pacotes exclusivos Windows impedem importação/instalação do núcleo em Linux.
3. Desenhar/implementar modo `headless`/adapters sem Win32 e sem execução de acções de desktop no servidor.
4. Validar STT multilingue e TTS português; localização de comandos, confirmações e barge-in.
5. Validar requisitos de alojamento Ollama ou alternativa auto-hospedada; web frontend isolado não equivale a inferência.
6. Executar testes automatizados isolados; relatórios de PASS/FAIL com comandos, ambiente, SHA e logs.
7. Fazer QA Windows e voz no equipamento de destino somente após autorização.

## Próxima acção técnica
Importar o código upstream `v0.3.1` no repositório `rightware-corporations/jarvis` e efectuar a auditoria de importações e dependências por plataforma. O repositório é público: verificar direitos dos binários/modelos antes de importar. Até lá, os documentos aqui registam a fundação, não um produto executável.
