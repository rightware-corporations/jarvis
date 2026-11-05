# apps/ — aplicações sobre o núcleo VEXEL

| Pasta | O que é | Estado |
|---|---|---|
| [`desktop/`](desktop/README.md) | **Frontend do produto**: aplicação de desktop Windows (orb 01E, depois HUD) | Orb MVP com demo simulada (JAR-MISSION-02); ainda não ligado ao ciclo de voz real |
| [`weblab/`](weblab/) | Laboratório web (FastAPI + HTML) para testes e demonstrações remotas. **Não é o produto** e não tem ferramentas Windows reais | existente (antigo `jarvis_lab/`) |

Regra ([ADR-0001](../docs/adr/0001-estrutura-do-repositorio.md)): as aplicações podem importar `jarvis/`; `jarvis/` nunca importa `apps/`.
