# apps/desktop/ — Orb Desktop (MVP)

Frontend do produto: um orb flutuante que mostra o estado do assistente. É o MVP da JAR-SLICE-01E; a direcção visual definitiva continua sujeita a revisão de design.

```
python -m apps.desktop --demo                 # estados simulados, em ciclo; Esc ou duplo clique fecha
python -m apps.desktop --demo --duration 20   # fecha após 20 s
python -m apps.desktop --snapshot saida/      # um PNG por estado (funciona sem ecrã)
```

**Instalação** (venv próprio, separado do runtime de voz): `pip install PySide6-Essentials==6.6.1 pydantic psutil`. O 6.6.1 é a versão fixada pelas constraints do Wyzer. PySide6 é LGPL-3.0, com ligação dinâmica, sem modificações.

## Arquitectura

| Ficheiro | Função | Qt? |
|---|---|---|
| `orb/visuals.py` | estado → cor, legenda PT, movimento; `frame(state, t)` determinístico | não |
| `orb/model.py` | aplica `UiEvent` por ordem; ignora eventos antigos (`generation`, `sequence`) | não |
| `orb/render.py` | desenho vectorial com QPainter (gradientes, anéis, arcos, barras); snapshots offscreen | sim |
| `orb/pump.py` | `QTimer` na thread da GUI drena o `jarvis.ui.QueueSink`; nenhuma chamada Qt a partir de threads de trabalho | sim |
| `orb/widget.py` | janela sem moldura, translúcida, sempre visível, arrastável, tamanho mínimo (high-DPI) | sim |
| `orb/demo.py` | simulador: `StateMachine` real numa thread de fundo, percorre os 9 estados | não |
| `orb/app.py` | composição, política high-DPI `PassThrough`, encerramento seguro | sim |

**Estados:** OFFLINE «Desligado» (parado) · IDLE «Pronto» (respira) · LISTENING «A ouvir» (anéis para fora) · THINKING «A pensar» (arcos em órbita) · TOOL_RUNNING «A executar» (anel segmentado) · AWAITING_CONFIRMATION «Confirma: sim ou não?» (pulso âmbar) · SPEAKING «A falar» (barras de onda) · MUTED «Silenciado» (cinzento riscado) · ERROR «Erro» (vermelho intermitente).

**Regras:**
- importa apenas `jarvis.ui` (verificado por teste);
- não cria orquestrador, não usa modelo, microfone, voz nem ferramentas.

A ligação a um `VoiceSession` real (passar o mesmo `QueueSink` como sink da sessão) fica para depois dos gates de hardware da 01C.

**Encerramento:** fechar a janela pára o simulador (join), a bomba de eventos e a animação, e só então termina o ciclo Qt. As janelas `Qt::Tool` não contam para `quitOnLastWindowClosed`, por isso o fecho chama `quit()` explicitamente.

Testes: `tests_desktop/` (offscreen), no job CI `desktop-orb` em Ubuntu e Windows.
