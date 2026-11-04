# 03 — Backlog priorizado

Legenda: `TODO`, `IN_PROGRESS`, `DONE`, `BLOCKED`. `DONE` só com evidência.

## P0 — Fundação e confiança (primeiro ciclo)
- [x] `JAR-P0-01` Escolher upstream e fixar versão SHA.
- [x] `JAR-P0-02` Inicializar repositório exclusivo `rightware-corporations/jarvis`, sem alterar a `main` do website VEXEL.
- [x] `JAR-P0-03` Registar arquitectura, backlog e aceitação.
- [x] `JAR-P0-04` Confirmar repositório exclusivo para o produto Jarvis. **Nota:** é público; direitos e informações confidenciais devem ser revistos antes de qualquer importação.
- [ ] `JAR-P0-05` Importar upstream `v0.3.1` com licença, proveniência e digest.
- [ ] `JAR-P0-06` Mapear imports e dependências Windows vs multiplataforma; identificar seams do `Orchestrator`.
- [ ] `JAR-P0-07` Desactivar por defeito coding agent e quaisquer ferramentas perigosas no lab.
- [ ] `JAR-P0-08` Escrever testes de contratos: ferramentas simuladas, confirmação obrigatória, negação, cancelamento, memória isolada.

## P1 — Demonstração web remota
- [ ] `JAR-P1-01` Implementar backend headless que reutilize o núcleo Wyzer.
- [ ] `JAR-P1-02` Implementar adapters simulados seguros para desktop e navegador.
- [ ] `JAR-P1-03` Integrar provider Ollama **real** ou modo claramente indisponível; sem falsos sucessos.
- [ ] `JAR-P1-04` Criar UI web premium com chat, streaming/estados, debug e logs de ferramentas.
- [ ] `JAR-P1-05` Proteger API: autenticação, isolamento de sessão, limites, sem segredos no frontend.
- [ ] `JAR-P1-06` Executar QA em ambiente remoto e disponibilizar preview privado.

## P2 — Voz, português, UX
- [ ] `JAR-P2-01` STT multilíngue pt e medição com amostras reais/autorizadas.
- [ ] `JAR-P2-02` TTS português com voz e licença verificadas.
- [ ] `JAR-P2-03` Wake word Jarvis legal e funcional; teste de falsos positivos/negativos.
- [ ] `JAR-P2-04` Interrupção, continuação de conversa e confirmação em português.
- [ ] `JAR-P2-05` Identidade e personalização de Jarvis para Issa, sem introduzir dados privados de teste.

## P3 — Distribuição, Windows e entrega
- [ ] `JAR-P3-01` Escolher local/híbrido/servidor após hardware conhecido.
- [ ] `JAR-P3-02` Agente Windows local e autenticação, mínimo privilégio e logs.
- [ ] `JAR-P3-03` QA com PC Issa: microfone, colunas, Ollama, arranque, memória, bateria/CPU.
- [ ] `JAR-P3-04` Direitos de redistribuição: bibliotecas, wake model, vozes, modelos LLM.
- [ ] `JAR-P3-05` Release, instalador, reversão e guia de suporte.

## Critério de prioridade
Não iniciar decoração/UI avançada, deploy público ou distribuição antes de uma prova de núcleo headless, políticas de segurança e provider real. A interface web é um laboratório, não substitui o agente Windows.
