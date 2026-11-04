# 04 — Critérios de aceitação e evidências

## Regras de evidência
Cada teste executado deve indicar: ambiente, OS, Python, SHA upstream/derivado, comando exacto, resultado PASS/FAIL, logs e data. Análise documental e existência de testes **não** contam como PASS.

## Gate A — Núcleo e permissões
- [ ] Orchestrator com provider stub e registry simulado inicializa sem Windows.
- [ ] Qualquer tool desconhecida é negada, sem importações dinâmicas.
- [ ] Acções perigosas requerem confirmação exacta e expiram.
- [ ] Cancelamento impede execução posterior de ferramentas.
- [ ] Memória é persistente e isolada por utilizador; apagar funciona.
- [ ] Falha do modelo resulta em erro explícito, não confirmação de tarefa fictícia.
- [ ] Limite de chamadas de ferramentas evita ciclos infinitos.

## Gate B — Web Lab
- [ ] API HTTPS privada com autenticação/sessão e sem segredos no browser.
- [ ] Chat usa modelo real auto-hospedado ou responde claramente indisponível.
- [ ] Uma tarefa simulada expõe chamada de ferramenta e resultado auditável.
- [ ] Tentativas de execução OS reais no web lab são recusadas.
- [ ] Teste automatizado para cross-user session leakage e rate limiting.
- [ ] Logs são privativos e não incluem áudio/screen shots por omissão.

## Gate C — Português/voz
- [ ] `Olá, Jarvis`/activação escolhida reconhecida em equipamentos reais.
- [ ] `Abre o navegador`, `O que tenho aberto?`, `Cancela`, `Sim`, `Não` reconhecidos.
- [ ] STT e TTS produzem e percebem português inteligível.
- [ ] Perguntas de seguimento preservam contexto sem repetir wake word na janela prevista.
- [ ] Falsos positivos com áudio em colunas avaliados.
- [ ] Modelos de voz/wake possuem autorização de utilização e redistribuição.

## Gate D — Entrega
- [ ] Pacote Windows assinado ou checksum de release verificável.
- [ ] Sem credenciais embutidas no binário/repo.
- [ ] Instalação limpa, arranque e desinstalação/reversão testados.
- [ ] Recursos CPU/RAM medidos no equipamento Issa.
- [ ] Manual e limites de privacidade/segurança claros.
- [ ] Aceitação expressa do utilizador após demonstração.

**Estado global (2026-11-04):** gates A, B, C e D PENDENTES. Não declarar produto pronto.
