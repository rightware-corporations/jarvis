# 09 — VEXEL Jarvis Web Lab (código inicial)

**Estado:** backend e frontend adicionados à branch `develop`; CI dos testes API em verificação. **Sem URL publicada, modelo configurado ou voz real**.

## Visual / fonte
O website VEXEL em `rightware-corporations/vexel` usa `Inter` como família `sans`. Este laboratório adopta a mesma família na variável CSS `--font-interface`; sem terceiros nem fontes binárias embutidas. Se Inter não estiver instalado no navegador, aplica-se o fallback system-ui; a entrega de um ficheiro Inter auto-hospedado poderá ser analisada separadamente. A tipografia original do operador não foi identificada por nome e poderá substituir o token. Sem copiar o layout do website, o Jarvis mantém cor de fundo escura, prata e azul/íris.

## Código implementado
- `jarvis_lab/api.py`: API FastAPI, health sem estado sensível, sessões de curta duração, autenticação obrigatória pelo header `X-Jarvis-Lab-Token`, rate limit básico por host, resposta de erro quando Ollama indisponível, restrições de cache/frame/JS.
- `jarvis_lab/web/index.html`, `lab.css`, `lab.js`: interface conversacional e diagnósticos; sem acesso ao desktop, sem microfone funcional; o token é mantido somente na memória JS e expurgado ao terminar a sessão.
- `tests_lab/test_api.py`: contratos HTTP com provider de teste explicitamente simulado. **Não** atestam resposta de modelo real.

## Configuração do servidor de testes — apenas ambiente remoto
Os seguintes nomes são configurações para um operador de servidor autorizado; o utilizador **não precisa de executar nada no seu computador**.

- `JARVIS_LAB_TOKEN`: segredo forte com pelo menos 16 caracteres, somente no ambiente privado do servidor.
- `JARVIS_OLLAMA_MODEL`: nome de um modelo auto-hospedado instalado no servidor ou endpoint autorizado, e.g. `qwen3.5:4b` sujeito a disponibilidade/recursos.
- `JARVIS_OLLAMA_URL`: endereço privado do serviço Ollama, default `http://127.0.0.1:11434`.
- Entrypoint da aplicação (quando uma infraestrutura de deploy segura estiver preparada): `jarvis_lab.api:app` por um processo ASGI.

Sem segredo ou modelo, o chat recusa novas sessões e mostra `MODEL_UNAVAILABLE`. Nunca se faz fallback silencioso para Claude/ChatGPT, modelos pagos ou respostas simuladas na API de produção.

## Limitações e gate
- Apenas um operador/segredo, sessão em memória. Não usar em ambiente público sem TLS, proxy de autenticação e controlo de rede adicional.
- Rate limiting local ao processo, não distribuído; não há base de dados de sessões multiworker, SSO, persistência de conversas ou logs auditáveis.
- Servidor não executa PowerShell, ações do Windows, coding agent, browser control ou ferramentas OS.
- Identidade da pessoa, voz, modelo local PT, wake word e integração em máquinas reais são trabalho separado.
- Não usar `uvicorn --reload` como modo de produção.

## Testes exigidos
1. CI headless PASS com dependências FastAPI/httpx e os novos testes `tests_lab/test_api.py`.
2. Verificar status 401 sem autenticação, 503 sem modelo, 404 sessão desconhecida, CSP, frontend, rate limit e TTL.
3. Executar manual QA do layout, acessibilidade e mobile numa preview segura.
4. Só depois configurar Ollama real num host isolado e capturar os resultados de sessão.
