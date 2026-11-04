# Headless adapter — primeira implementação

**Estado:** código publicado; execução dos testes em GitHub Actions por verificar.

## Ficheiros
- `jarvis_lab/headless.py`: constrói o **Orchestrator original** com `ToolRegistry()` vazia e `InProcessExecutor`; não publica API HTTP.
- `tests_lab/test_headless.py`: conversa com provider simulado, ausência de ferramentas reais, negação de execução desconhecida e memória separada por subject.
- `.github/workflows/source-integrity.yml`: valida SHA/compilação e executa testes de contrato em runner remoto com Python 3.11 + Pydantic + pytest.

## Propriedades pretendidas
- Nenhuma ferramenta real de Windows, shell, navegador ou coding agent registada.
- Memória SQLite desactivada sem diretório fornecido; quando activa, há um ficheiro por identificador de utilizador derivado por SHA-256.
- `FakeChatProvider` devolve respostas pré-programadas só para testes; **não é IA real e não comprova português**.
- Erro `UNKNOWN_TOOL` para qualquer ferramenta ausente.

## Não está implementado
- Autenticação, API HTTPS, isolamento entre pedidos concorrentes/instâncias ou quotas.
- Ollama remoto real, STT/TTS, wake word, streaming e interface web.
- Execução real de ferramentas Windows; será fase separada sujeita a autorização.
- Revisão de licenças dos 44 binários excluídos.

**Gate:** não expor este adaptador à Internet como serviço de produção. Primeiro obter os resultados efectivos da execução remota, acrescentar autenticação/isolamento e testar modelo real.
