# ADR-0001 — Estrutura do repositório: backend, frontend, dados e laboratório

- **Estado:** Aceite pelo operador RIGHTWARE em 05/11/2026 (opção «estrutura completa e publicar»); revisão pelo ChatGPT pendente.
- **Data:** 2026-11-05
- **Substitui / refina:** a árvore-alvo do [11 §5](../11_ARCHITECTURE_REVIEW_AND_EVOLUTION.md), que era uma proposta e não reflectia o código.
- **Relacionado:** D-002, D-005, D-008 e D-010 no [registo de decisões](../22_DECISION_REGISTER_2026-11-04.md).

## Contexto

O repositório tem o Wyzer v0.3.1 importado (182 ficheiros verificados por caminho e hash), o núcleo VEXEL (`jarvis/`), um laboratório web (antes `jarvis_lab/`, agora `apps/weblab/`), testes, configuração, QA Windows e documentação numerada. Faltava uma regra escrita sobre onde vive cada camada, o que é o "frontend", o "backend" e a "base de dados", e o que nunca entra no git.

Restrição dura: os 182 ficheiros do manifesto (`wyzer/`, `tests/`, `installer/`, `wyzer.toml`, `pyproject.toml`, …) **não mudam de caminho**. A verificação de integridade compara-os pelo caminho exacto.

## Decisão

### 1. O que é o produto

O VEXEL Jarvis é uma **aplicação de desktop Windows local**, não uma aplicação web nem um serviço na cloud.

| Camada | O que é | Onde vive | Estado |
|---|---|---|---|
| **Motor (upstream)** | Wyzer v0.3.1: orquestrador, políticas, adapters de voz, ferramentas | `wyzer/` (imutável) | importado, 182/182 |
| **Backend (núcleo VEXEL)** | processo Python local: ciclo de voz, PT, ferramentas autorizadas, política de confirmação, preflight | `jarvis/` | implementado e testado (01B–01C-PRE) |
| **IA** | modelo local servido pelo Ollama em `127.0.0.1` | fora do repositório (instalado no PC) | por validar no G3 |
| **Frontend (produto)** | interface de desktop: orb (01E) e depois HUD | `apps/desktop/` (pasta criada com README; código só na 01E) | por iniciar |
| **Contratos do frontend** | estados, eventos e fila para a UI, sem Qt | `jarvis/ui/` | implementado |
| **Laboratório web** | FastAPI + HTML para testes e demonstrações remotas; **não é o produto** | `apps/weblab/` (movido de `jarvis_lab/`; entrypoint `apps.weblab.api:app`) | existe |
| **Base de dados** | **ainda não existe** no produto. Quando houver memória (JAR-MEM-01): SQLite local por utilizador | dados em `%LOCALAPPDATA%` (nunca no repositório); esquema e migrações em `jarvis/memory/` | futuro |
| **Configuração** | perfis TOML sem segredos | `configs/` | `jarvis_slice.toml` |
| **QA** | inventário Windows, corpus de frases, benchmarks | `qa/windows/`, `qa/corpus/` (corpus PT-MZ v1), `qa/benchmarks/` | windows e corpus com conteúdo; benchmarks por escrever |
| **Testes** | RIGHTWARE: `tests_vexel/`, `tests_lab/`; upstream: `tests/` (imutável) | idem | 399 no CI |
| **Documentação** | ver §3 | `docs/` | — |

### 2. Regras de dependência

1. `jarvis/` **nunca importa** Qt, frameworks web nem `apps/`. A UI consome apenas `jarvis.ui` (eventos, `QueueSink`).
2. `apps/desktop/` pode importar `jarvis/`; o contrário é proibido.
3. `apps/weblab/` não importa os adapters Windows nem as ferramentas reais.
4. A tecnologia do frontend (Qt nativo/QML ou QWebEngine com web) é decidida pelo POC M0 e registada num ADR próprio. Só nesse ADR, e se for QWebEngine, nasce `apps/desktop/web/`.
5. O `wyzer/` só é alterado através de uma política de patches aprovada (JAR-ARCH-02), nunca editando os ficheiros do manifesto directamente.

### 3. Documentação

- `docs/00`–`25_*.md`: **ficam como estão** (histórico; mover partia os links). Não se acrescentam novos documentos numerados para decisões ou relatórios.
- `docs/adr/`: uma decisão de arquitectura por ficheiro (`NNNN-titulo.md`), com estado, contexto, decisão e consequências.
- `docs/reports/`: relatórios de fase (`AAAA-MM-DD_JAR-…md`). Antes iam só por zip; passam a ficar no repositório. Contêm apenas informação técnica, sem dados pessoais.
- `docs/plans/`: planos de fase novos (`AAAA-MM-DD_JAR-…md`); o índice aponta também para o plano 25, que mantém o nome.

### 4. Dados que nunca entram no git

Áudio, transcrições, logs de voz, bases de dados de memória, modelos (Whisper, LLM, wake word), venvs e relatórios de QA não revistos. Os caminhos por omissão já estão ignorados pelo `.gitignore` upstream: `.wyzer/*`, `evidence/`, `logs/`, `.venv/`. Não se cria uma pasta `data/` no repositório: os dados de teste vivem nos próprios testes, como fakes e fixtures sintéticos.

## Alternativas consideradas

| Alternativa | Porque não agora |
|---|---|
| Manter `jarvis_lab/` na raiz | Escolhido inicialmente para não mexer em imports e CI; o operador preferiu a estrutura completa, e a mudança foi feita com `git mv` (histórico preservado), imports, CI e documentos de instruções corrigidos e testes verdes. |
| Pasta `data/` no repositório | Rejeitada: uma base de dados não é uma pasta do repositório; os dados de teste vivem nos testes. |
| Pastas vazias | O git não guarda pastas vazias; cada pasta nova tem um README que diz o que lá vai e quando. |
| Reorganizar os documentos numerados em subpastas | Quebra dezenas de links internos e nos relatórios; valor baixo face ao risco. |
| Mover o código upstream para `vendor/wyzer/` | Impossível sem uma nova política de integridade (os caminhos estão no manifesto). |
| Backend em servidor/cloud | Contraria D-005/D-007 (local, sem dependência paga); só se a RIGHTWARE escolher alojar a inferência. |

## Consequências

- **Positivas:** fronteiras claras entre motor, núcleo, UI, laboratório e dados; o frontend pode mudar de tecnologia sem tocar no núcleo; nada de dados pessoais no repositório público; os relatórios ficam versionados.
- **Negativas e custos:** coexistem a numeração antiga e as pastas novas em `docs/`; os documentos históricos e os relatórios mencionam `jarvis_lab/` (descrevem o estado da altura); quem corria o laboratório tem de usar `apps.weblab.api:app`.
- **Seguimento:**
  - ADR-0002 para o renderer do frontend (depois do M0);
  - ADR para o modelo local (depois do G9);
  - ADR para a voz TTS (depois do G7);
  - ADR para a política de patches do Wyzer (JAR-ARCH-02).
