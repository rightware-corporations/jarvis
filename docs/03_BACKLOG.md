# 03 — Backlog de execução

Legenda: [x] documentação/implementação verificada; [ ] pendente; cada teste só conta com logs de execução.

## P0 — Fundação e controlo
- [x] `JAR-P0-01` Escolher Wyzer `v0.3.1` e fixar commit.
- [x] `JAR-P0-02` Usar `rightware-corporations/jarvis` sem alterar website VEXEL.
- [x] `JAR-P0-03` Definir arquitectura, riscos e critérios de aceitação.
- [x] `JAR-P0-04` Criar branch `develop`; manter `main` estável.
- [x] `JAR-P0-05` Importar 182 ficheiros fonte/texto upstream, MIT/NOTICE e manifesto; excluir 44 binários até revisão.
- [x] `JAR-P0-05A` Comparar hashes SHA de todos os 182 importados — 182/182 iguais.
- [ ] `JAR-P0-06` Confirmar imports headless em Linux com execução de CI e mapear dependências Win32.
- [x] `JAR-P0-07` Criar composição lab sem coding agent, shell, browser ou ferramentas do Windows.
- [ ] `JAR-P0-08` Executar e validar testes de contrato (código publicado, resultados pendentes).
- [x] `JAR-P0-09` Publicar workflow de GitHub Actions para integridade/compilação/headless tests.
- [ ] `JAR-P0-10` Eliminar branch temporária `feat/wyzer-v031-core-import` (ferramenta GitHub actual não fornece delete ref).

## P1 — Laboratório remoto
- [x] `JAR-P1-00` Criar factory headless com registry vazio e memória por subject.
- [ ] `JAR-P1-01` API remota autenticada que instancia a factory.
- [ ] `JAR-P1-02` Simulador controlado de tarefas de computador; proibição verificável de operações reais.
- [ ] `JAR-P1-03` Integrar Ollama real auto-hospedado e testar function calling, segurança e latência.
- [ ] `JAR-P1-04` UI web premium com chat, mic, estado e logs de tools simuladas.
- [ ] `JAR-P1-05` Sessões, autenticação, limites, logs e privacidade.
- [ ] `JAR-P1-06` Testes remotos PASS/FAIL com evidências e preview privado.

## P2 — Português e conversa por voz
- [ ] `JAR-P2-01` STT Whisper multilingue PT.
- [ ] `JAR-P2-02` TTS português e licença.
- [ ] `JAR-P2-03` Wake word `Jarvis` legal e funcional.
- [ ] `JAR-P2-04` Confirmação `sim/não`, cancelamento, barge-in e seguimento de conversa PT.
- [ ] `JAR-P2-05` Identidade/voz/UX Jarvis para Issa.

## P3 — Entrega
- [ ] `JAR-P3-01` Escolher distribuição local/servidor/híbrida e modelo de custos.
- [ ] `JAR-P3-02` Agente Windows local seguro.
- [ ] `JAR-P3-03` QA de hardware/microfone/colunas com PC Issa autorizado.
- [ ] `JAR-P3-04` Auditoria licenças de modelos, wake, TTS e assets.
- [ ] `JAR-P3-05` Release assinada ou checksum, reversão, instruções e aceitação.

## Guardrails
- Desenvolver apenas em `develop`; promoção a `main` após revisão e testes.
- Repositório é **público**. Sem credenciais, ficheiros privados, gravações reais ou modelos não licenciados.
- Não fazer deploy público nem entregar ao Issa antes dos gates de segurança, modelo real e voz.
- Não usar PC do operador para programar, executar testes ou instalar componentes.
