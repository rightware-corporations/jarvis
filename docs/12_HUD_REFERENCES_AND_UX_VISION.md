# JAR-UX-REF-01 — Pesquisa de HUD, janela flutuante e referências de interface

**Data:** 2026-11-04 (Africa/Maputo)  
**Estado:** ESTUDO / PROPOSTAS. **Não constitui aprovação de UI, integração, licença ou implementação.**  
**Âmbito:** Interface Jarvis para Issa Maulid; o motor de IA continua Wyzer/Python. Claude e ChatGPT são ferramentas de desenvolvimento, **não dependências do assistente em utilização**.

## 1. Requisitos expressos e observações dos materiais enviados

- Um Jarvis **voice-first** e verdadeiramente flutuante no Windows, não uma app de chat convencional, nem dashboard empresarial.
- Um núcleo/reactor animado, móvel, que pode ficar sobre outras janelas, com acesso simples a silenciar/ocultar/expandir.
- **Expanded HUD**: centro de comando com painéis que surgem quando o contexto o exige (briefings, agenda, resultados, tarefas, diagnósticos).
- **Intelligence Graph**: grafo de relações entre informações, ficheiros, tarefas, projectos e aplicações **somente quando existem dados reais autorizados**.
- Modo minimizado não deve monopolizar GPU/RAM/CPU, microfone ou foco de teclado. A interface nunca deve apresentar uma execução fictícia.

### Referência A — vídeo `jarvis.mp4` disponibilizado na conversa
Foi observado um reactor/esfera luminosa azul com estados de fala, painéis de contexto e transições; não há implementação/código identificados de forma verificável a partir do vídeo. A referência é **experiência e arte**, não prova de capacidades de IA, licenças, velocidade ou origem do software. O vídeo não foi copiado para o repo.

### Referência B — captura de ecrã enviada na conversa
Mostra uma **aplicação aberta em browser localhost:4719**, com grande grafo de nós interligados, filtros laterais, um reactor J.A.R.V.I.S. à direita e comandos inferiores. Um browser em localhost **não comprova overlay nativo**; o comportamento flutuante terá de vir de uma shell desktop. A captura não foi copiada para o repo.

### Referência C — Google Drive, `Como instalar o seu Jarvis? Passo a Passo`
[Documento fornecido](https://drive.google.com/file/d/1qweMY0y0x4IBuWKQY_UkMoYJrAX1J1X6/view). Trata-se de **material comercial** para um assistente instalável via browser/PWA com toque, fala, listas, lembretes, timers, clima e cotações. Não há fonte de código independente identificada pelo documento. Não prova wake word permanente, IA local, ausência de custos nem controlo real do computador. Útil apenas para fluxos e UX.

### Referência D — guia Avello de Jarvis com Claude Code
[Documento enviado](https://docs.google.com/document/d/1LQDzVkhHrPYyGVdMtHzaPBlSIipDsa4TN6skBBGsRuE/view) aponta para [`adewaskar/jarvis`](https://github.com/adewaskar/jarvis), não para Wyzer. A implementação importa `@anthropic-ai/claude-agent-sdk` em `bridge/server.mjs`, por omissão `claude-opus-5`; a alternativa `src/lib/brain.ts` também usa Anthropic directamente. A via de voz do browser em `src/lib/voice.ts` fixa `en-GB` sem ElevenLabs. **Não adoptá-lo como runtime** pois exige Claude/Anthropic. A UI é modular e sob licença MIT: `src/scene/Core.tsx`, `Scene.tsx`, `Orbits.tsx`, `src/ui/Panels.tsx`.
- Riscos documentados no upstream, não reaproveitar a bridge: [issue #37](https://github.com/adewaskar/jarvis/issues/37) sobre `server.listen(PORT)` exposto em LAN, [PR #42](https://github.com/adewaskar/jarvis/pull/42) para não carregar conectores claude.ai, [PR #29](https://github.com/adewaskar/jarvis/pull/29) sobre gravação de transcrições. Em 2026-11-04, PRs consultados estavam abertos/não integrados.

## 2. Catálogo de candidatos a referências visuais

| Projecto | Código útil identificado | Licença vista | Utilização admissível nesta fase |
| --- | --- | --- | --- |
| [`adewaskar/jarvis`](https://github.com/adewaskar/jarvis) | `src/scene/{Core,Scene,Orbits}.tsx`, `src/ui/{Hud,Panels}.tsx`; React, R3F, GLSL | MIT no `LICENSE` | Referência/reuso eventual do frontend, **desacoplado do Claude** e com atribuição |
| [`harsh-raj00/my-jarvis`](https://github.com/harsh-raj00/my-jarvis) | `frontend/src/components/3D/{JarvisScene,HolographicCore,RotatingRings,ParticleField,VoiceIndicator}.jsx` | MIT confirmado | Reactor 3D, partículas, efeitos visuais; benchmark de fluidez pendente |
| [`desertcache/samantha-ui`](https://github.com/desertcache/samantha-ui) | `src/components/SoulOrb/{SoulOrb.jsx,fragmentShader.glsl,vertexShader.glsl}` | MIT confirmado | Transições orgânicas ao amplitude/estado; não é assistente completo |
| [`Angga-29/jarvis-ai-assistant`](https://github.com/Angga-29/jarvis-ai-assistant) | `jarvis-hud/electron/main.js`: janela 130×130, frameless, transparente, always-on-top | MIT confirmado | Comportamento de floating overlay **como referência**, sem exigir Electron |
| [`hasibjaan/jarvis`](https://github.com/hasibjaan/jarvis) | `ui/orb.py` e `ui/hud.py`, PySide6/QPainter, amostragem reduzida por frame | Licença não confirmada no repo consultado | **Inspecção/ inspiração apenas**; não copiar antes de permissão/licença |
| [`ScuderiaFerrariSimp/Jarvis-Desktop-Assistant`](https://github.com/ScuderiaFerrariSimp/Jarvis-Desktop-Assistant) | `main.py` usa PySide6 + `QWebEngineView` em janela sem moldura | Não confirmada | Arquitectura de referência. `ui/orb.html` não estava no tree consultado; não adoptar sem fonte |
| [`vasturiano/react-force-graph`](https://github.com/vasturiano/react-force-graph) | Componentes de force-directed graph 2D/3D/VR para representação das relações | Licença a verificar na versão seleccionada | POC de grafo, se justificada pelos dados; não integrar sem licença/benchmarks |

**Nota de propriedade intelectual:** licença de código, assets, vídeos, modelos, fontes e branding não são automaticamente iguais. Não incorporar ficheiros visuais de terceiros no `jarvis/` sem licença/atribuições e revisão de dependências.

## 3. Modelo de experiência recomendado

### Modo Floating (produto principal)
- Janela nativa PySide6: sem moldura, deslocável, opcional always-on-top, minimizável/ocultável, menu de privacidade e encerramento.
- Núcleo responde a sinais verdadeiros: `OFFLINE`, `IDLE`, `WAKE_DETECTED`, `LISTENING`, `THINKING`, `TOOL_RUNNING`, `SPEAKING`, `AWAITING_CONFIRMATION`, `ERROR`, `MUTED`.
- Indicadores evidentes de microfone, processamento e confirmação; modo discreto com animações reduzidas.

### Modo Expanded HUD
- Núcleo persistente e anéis; abrir painéis exclusivamente sob eventos reais: agenda, ficheiros, tarefas, resumo, ferramentas, logs.
- Sem menu de cartões permanente, sem widgets falsos e sem autorizações escondidas em animações.

### Modo Intelligence Graph
- Grafo opcional para relações confirmadas e indexadas. Visualização separada de recuperação/autorizações; sem inspecção de ficheiros sem consentimento.
- Culling/clustering/Limits, sem manter milhares de nós com GPU activa quando minimizado.
- A captura recebida é referência visual, **não especificação de base de dados**.

## 4. Alternativas tecnológicas ainda não escolhidas

1. **Python/PySide6 + QPainter/Qt Quick/QML:** permite shell desktop nativa, estado, baixa sobrecarga potencial; avaliar capacidade de 3D e partículas sem JS.
2. **Python/PySide6 + QWebEngine + frontend React/TypeScript/Three.js:** reutilização modular dos efeitos de HUD; custo de memory/GPU/WebEngine, bridge Qt-JS e empacotamento devem ser medidos.
3. **Electron como shell:** outros projectos demonstram overlay, mas acrescenta runtime próprio sem necessidade comprovada. Não é escolha por omissão.
4. **Grafos:** componente visual separado e carregado apenas sob pedido; não juntar uma engine de grafos à esfera 24/7.

**A base de inteligência do projecto permanece Python+Wyzer; nenhuma dessas escolhas exige Claude, Anthropic nem ElevenLabs em produção.**

## 5. Contrato de estados / separação de responsabilidades

```text
Voice capture -> recognizer -> VEXEL session/Wyzer orchestrator
                          |             |
                          v             v
                    state/events      tools/results
                          |             |
                          +-------> UI event adapter
                                      |
                    +-----------------+--------------------+
                    |                 |                    |
                Floating           Expanded              Graph
              PySide6 shell        HUD overlay       Dados autorizados
```

- UI não decide autorização nem executa comandos: apenas envia intenções e mostra o estado.
- As confirmações são executadas no núcleo/policy engine e preservadas mesmo com UI fechada ou minimizada.
- A UI de laboratório web existente em `jarvis_lab/web/` permanece instrumento de teste, não produto final.
- Usar `request_id`, `session_id`, `event_id`, timestamps, status/erro reais; mensagens de áudio e tarefas nunca devem ser simuladas ao utilizador.
- Avaliar perfis de consumo: idle, listening, speaking, grafo 500/2000 nós e expansão; medição em hardware real.

## 6. Ordem de estudo / gates

- [ ] JAR-UX-02: especificar fluxos de interface/estados e design tokens VEXEL; validar wireframes dos três modos.
- [ ] JAR-UX-03: POC **visual isolada**, sem executar/instalar automações nem ligar ferramentas Windows, comparando QPainter/QML vs QWebEngine/WebGL.
- [ ] JAR-UX-04: validar dependências e licenças de componentes escolhidos; manter notices e código upstream imutável.
- [ ] JAR-UX-05: medir CPU, RAM, GPU, frames por segundo, bateria e latência de input nos PCs alvo.
- [ ] JAR-UX-06: ligar eventos reais de voz, contexto e ferramentas **após gates de segurança e voz**; QA de acessibilidade, foco, alt-tab, DPI, vários monitores.

**Estado final:** pesquisa e proposta documentadas; nenhuma interface implementada ou aprovada, nenhum pacote externo importado, nenhuma execução realizada.
