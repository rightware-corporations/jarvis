# 02 — Arquitetura-alvo (proposta; ainda não implementada)

```text
Browser HTTPS (microfone opcional)
  | auth, texto, voz -> Web Lab API
  v
VEXEL Jarvis API/headless adapter
  | sessão, memória, planeamento, políticas, logs
  +--> Wyzer Orchestrator (derivado v0.3.1)
  |      +--> LLM adapter -> Ollama auto-hospedado (modelo com tool-calling)
  |      +--> Tool registry -> simulação/fixtures auditáveis [WEB LAB]
  |
  +--> STT/TTS multilingue (alternativa local/servidor; licenças verificadas)

FUTURO (apenas se aprovado):
  autenticação + canal autenticado + consentimento explícito
  -> agente Windows local, executando ferramentas sob permissões mínimas
```

## Limites de confiança
1. **Browser:** não possui credenciais Ollama nem acesso ao SO do utilizador; acções perigosas nunca disponíveis.
2. **API headless:** tokens/sessões autenticados, rate limit, CORS, auditoria e tratamento de erros. Não expor Ollama directamente à Internet.
3. **Orchestrator:** preservar registry tipado, validação, limites de rondas, confirmações e cancelamento do Wyzer. Adaptar, não reescrever o núcleo.
4. **Executor web:** simulado, nunca executar shell/PowerShell, abrir apps, apagar ficheiros ou mexer em ambiente real.
5. **Executor Windows futuro:** serviço local explicitamente instalado e autorizado, firewall/localhost, controlo de comandos e consentimento para riscos elevados.
6. **Memória:** separação por utilizador e sessão, política de retenção, apagar dados a pedido; não usar perfis reais no protótipo.

## Estratégia de portabilidade
- Isolar imports e inicialização Windows específicos; não fingir que pywinauto/WinRT funcionam no Linux.
- Provar que `Orchestrator`, `ChatProvider`, políticas e memória se instanciam com ferramentas simuladas sem dependências Win32.
- Fazer os primeiros testes de contrato do núcleo/agent, depois um endpoint remoto headless.
- Manter o modo Windows do upstream funcional; mudanças de portabilidade devem ficar atrás de adapters.
- No lab, se não houver modelo Ollama disponível, reportar `MODEL_UNAVAILABLE`, não gerar respostas falsas como se fossem do modelo.

## Contratos iniciais (proposta)
- `POST /api/v1/sessions` -> sessão de testes autenticada.
- `POST /api/v1/chat` -> texto, sessão, resposta, referências de ferramentas, estados de confirmação.
- `POST /api/v1/confirmations/{id}` -> aprovar/rejeitar chamadas simuladas permitidas.
- `GET /api/v1/capabilities` -> lista de ferramentas em modo simulado e os respectivos riscos.
- `GET /api/v1/health` -> estado verificável dos componentes, incluindo Ollama.
- `POST /api/v1/voice/transcribe` e `POST /api/v1/voice/synthesize` quando serviços multilingues estiverem disponíveis.
Estes são **contratos propostos**, não endpoints já disponíveis.

## Português e personalização
- Trocar Whisper `small.en` por modelo multilingue; `language=pt` após avaliação de qualidade.
- Piper `pt_PT` ou `pt_BR` como candidatos iniciais; avaliar qualidade, licença e inteligibilidade em português de Moçambique.
- Adaptar wake word/modelo acústico: nome `Jarvis` na interface não garante que `Hey Jarvis` seja detectado.
- Traduzir comandos, confirmações, cancelamentos, respostas e prompts de sistema, sem remover controlos de segurança.
- Utilizar perfis de voz e identidade próprios, sem imitar uma pessoa real não autorizada.

## Distribuição: decisão adiada
- **Local:** modelo e executor no PC Issa; privacidade forte, exige hardware adequado.
- **Híbrido:** voz/UI e executor local, inferência em máquina/servidor da RIGHTWARE; rede e custos.
- **Servidor:** acesso web para tarefas e conhecimento, mas NÃO controle arbitrário do computador do Issa sem agente local.
Critérios: capacidade do PC, latência, privacidade, custo total, disponibilidade e segurança.
