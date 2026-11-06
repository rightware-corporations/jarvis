---
paths:
  - "jarvis/**/*"
  - "apps/**/*"
  - "configs/**/*"
  - "tests_vexel/**/*"
  - "tests_lab/**/*"
  - "tests_desktop/**/*"
  - "qa/**/*"
---

# Regras de arquitectura

Fonte única: [ADR-0001](../../docs/adr/0001-estrutura-do-repositorio.md) (`ARCH_APPROVED`). Este ficheiro só resume o que se verifica ao editar código.

- **Fronteiras:**
  - `jarvis/` não importa `apps/`, PySide6/Qt, FastAPI nem outros frameworks web.
  - `apps/desktop/` importa apenas `jarvis.ui` (há um teste que o verifica).
  - `apps/weblab/` não importa adapters Windows nem ferramentas reais.
- **A UI não orquestra:**
  - o Orb só reflecte `UiEvent` (via `QueueSink` + `QTimer` na thread da GUI);
  - não cria orquestrador, modelo, microfone nem ferramentas.
- **Ferramentas:**
  - a allowlist em `jarvis/tools/allowlist.py` tem 3 nomes (`get_local_time`, `get_system_status`, `open_allowed_application`);
  - há um teste contra deriva;
  - acrescentar uma ferramenta é uma decisão RIGHTWARE, não uma refactorização.
- **Estados da UI:**
  - os 9 `VoiceState` e `ALLOWED_TRANSITIONS` em `jarvis/ui/events.py` são contrato;
  - mudar exige actualizar `tests_vexel` e `tests_desktop` em conjunto.
- **Configuração:**
  - só `configs/jarvis_slice.toml`, sem segredos;
  - `wyzer.toml` e `pyproject.toml` são upstream protegido.
- **Árvore congelada:**
  - não mover pastas;
  - não criar `data/`, `tests_rw/` nem novos documentos numerados;
  - a memória SQLite (`jarvis/memory/`, dados em `%LOCALAPPDATA%\VEXEL\Jarvis\`) é direcção futura e não se implementa sem ordem.
- **Mudança de arquitectura:** novo ADR proposto à RIGHTWARE. Nunca uma reorganização implícita num commit de funcionalidade.
