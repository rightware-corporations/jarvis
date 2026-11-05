# apps/desktop/ — frontend de desktop (JAR-SLICE-01E)

Lugar reservado para a interface do produto: o orb mínimo da 01E e, depois, o HUD.

- Consome **apenas** os contratos de `jarvis.ui` (`VoiceState`, `UiEvent`, `QueueSink`). Os eventos são drenados na thread da UI; nunca se actualiza a UI a partir de threads de trabalho.
- A tecnologia (Qt nativo/QML ou QWebEngine com frontend web) é decidida pelo POC M0 e registada num ADR. Só se a decisão for QWebEngine nasce `web/` aqui dentro.
- Sem código até a 01E ser autorizada.
