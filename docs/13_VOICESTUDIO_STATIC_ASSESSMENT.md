# JAR-VOICE-REF-01 — Auditoria estática do VoiceStudio e opções de integração

**Data:** 2026-11-04 (Africa/Maputo)  
**Estado:** REPOSITÓRIO INVESTIGADO; **NÃO ESCOLHIDO, NÃO INSTALADO, NÃO EXECUTADO, NÃO INTEGRADO**.  
**Fonte:** [`debpalash/VoiceStudio`](https://github.com/debpalash/VoiceStudio) `main@fd66407f9447b2348e1dab74901328d3b8bd2e47`.  
**Destino da avaliação:** [VEXEL Jarvis — Issa Edition](https://github.com/rightware-corporations/jarvis/tree/develop), motor existente Wyzer 0.3.1 + Python. Independência de APIs pagas e subscrições de IA é requisito de **runtime**, não proíbe Claude/ChatGPT como ferramentas de desenvolvimento.

## 1. Resumo executivo

VoiceStudio é um estúdio de voz local-first, não um assistente autónomo equivalente ao Wyzer. Inclui **síntese TTS, reconhecimento STT/ASR, ditado, voice cloning, voice design, dubbing, gestão de modelos, API FastAPI, WebSocket e MCP**. O README **anuncia** 646 línguas, mas isso não comprova boa inteligibilidade para português de Moçambique nem para cada motor configurável.

**Recomendação:** inscrever VoiceStudio como **candidato a serviço local de voz acessível por API** e como catálogo de motores a pesquisar; **não copiar o repositório inteiro, não usar o modelo predefinido sem exame das licenças e não substituir o Wyzer**. O módulo `wyzer/speech/` já traz Faster-Whisper/Kokoro e precisa de uma matriz comparativa antes de adicionar outro runtime pesado.

## 2. Evidência técnica concreta — implementação inspeccionada

| Subsistema | Caminho/contrato verificado | Evidência e limitações |
| --- | --- | --- |
| Arquitectura | [`README.md`](https://github.com/debpalash/VoiceStudio/blob/fd66407f9447b2348e1dab74901328d3b8bd2e47/README.md), `backend/`, `electron/`, `mobile/`, `omnivoice/` | Aplicação desktop Electron com backend Python FastAPI e múltiplos motores; **5.298 entradas no Git tree**. Grande superfície para carregar dentro do Jarvis. |
| ASR HTTP | [`backend/api/routers/openai_compat.py#L1184`](https://github.com/debpalash/VoiceStudio/blob/fd66407f9447b2348e1dab74901328d3b8bd2e47/backend/api/routers/openai_compat.py#L1184-L1216) | `POST /v1/audio/transcriptions` em protocolo compatível com a forma de API OpenAI **mas processado localmente**, não significa chamada à API paga da OpenAI. |
| ASR em fluxo | [`backend/api/routers/capture_ws.py#L303`](https://github.com/debpalash/VoiceStudio/blob/fd66407f9447b2348e1dab74901328d3b8bd2e47/backend/api/routers/capture_ws.py#L303-L304) | WebSocket `/v1/audio/transcriptions/stream`: áudio WebM/Opus ou `pcm=1&sr=16000`, eventos partial/final/summary. [Protocolo](https://github.com/debpalash/VoiceStudio/blob/fd66407f9447b2348e1dab74901328d3b8bd2e47/docs/speech-platform.md). |
| TTS HTTP | [`backend/api/routers/openai_compat.py#L649`](https://github.com/debpalash/VoiceStudio/blob/fd66407f9447b2348e1dab74901328d3b8bd2e47/backend/api/routers/openai_compat.py#L649-L677) | `POST /v1/audio/speech` com saída áudio; alias de nomes de modelos, escolha real pelo backend instalado. |
| TTS em fluxo | [`backend/api/routers/tts_stream.py#L307`](https://github.com/debpalash/VoiceStudio/blob/fd66407f9447b2348e1dab74901328d3b8bd2e47/backend/api/routers/tts_stream.py#L307) | `/ws/tts` expõe PCM16 em chunks, eventos de formato, sample rate, conclusão/latência, engine. Comentário do código fala em meta inferior a 100 ms para primeiro áudio **não comprovada neste projecto**. |
| Descoberta de serviço | [`docs/speech-platform.md`](https://github.com/debpalash/VoiceStudio/blob/fd66407f9447b2348e1dab74901328d3b8bd2e47/docs/speech-platform.md) | `GET /.well-known/voicestudio-speech`, protocolo `voicestudio.speech.v1`; exemplo loopback `127.0.0.1:3900`. |
| Voz PT | [`backend/core/language_variants.py`](https://github.com/debpalash/VoiceStudio/blob/fd66407f9447b2348e1dab74901328d3b8bd2e47/backend/core/language_variants.py) | Configuração explícita `Portuguese (Brazil)`→`pt-BR`, `Portuguese (Portugal)`→`pt-PT`. `pt` isolado resolve por omissão para **pt-BR**. **Não comprova variante pt-MZ, sotaque moçambicano ou qualidade em hardware real.** |
| ASR engines | [`docs/engines/README.md`](https://github.com/debpalash/VoiceStudio/blob/fd66407f9447b2348e1dab74901328d3b8bd2e47/docs/engines/README.md), `backend/config/models.yaml` | WhisperX, Faster-Whisper, Whisper.cpp opcional, modelos diferentes por CPU/GPU. `whisper.cpp` requer binário/modelo local seleccionado. |
| TTS engines | Mesmo catálogo, `docs/engines/omnivoice.md`, `docs/engines/supertonic3.md`, `docs/engines/kittentts.md` | OmniVoice é default, Supertonic-3 opcional CPU PT, KittenTTS inglês apenas. Qualidade, disponibilidade e licenças variam por modelo. |
| Segurança API | [`docs/api-auth.md`](https://github.com/debpalash/VoiceStudio/blob/fd66407f9447b2348e1dab74901328d3b8bd2e47/docs/api-auth.md) | Loopback é não autenticado por omissão; para acesso remoto `OMNIVOICE_API_KEY`, PIN no HTTP de consumo e tickets WS; NÃO expor portas directamente na Internet. |
| MCP | [`docs/mcp.md`](https://github.com/debpalash/VoiceStudio/blob/fd66407f9447b2348e1dab74901328d3b8bd2e47/docs/mcp.md) | `generate_speech`, `clone_voice`, `design_voice`, transcrição. MCP não obriga Claude, mas **Jarvis não precisa de MCP para STT/TTS**; endpoint HTTP/WS é mais directo. |
| Windows/recursos | [`docs/install/windows.md`](https://github.com/debpalash/VoiceStudio/blob/fd66407f9447b2348e1dab74901328d3b8bd2e47/docs/install/windows.md), [performance](https://github.com/debpalash/VoiceStudio/blob/fd66407f9447b2348e1dab74901328d3b8bd2e47/docs/performance.md) | CPU funciona com degradação de latência. NVIDIA CUDA, opções de engines nativos e Vulkan em alguns percursos; sidecars/modelos podem ocupar vários GB. Não inferir hardware/latência do PC Issa. |

## 3. Licenças: BLOQUEADOR para cópia ingénua

**VoiceStudio aplicação: `AGPL-3.0-only`**. Comprovado em [`LICENSE`](https://github.com/debpalash/VoiceStudio/blob/fd66407f9447b2348e1dab74901328d3b8bd2e47/LICENSE), [`LICENSE-NOTICE.md`](https://github.com/debpalash/VoiceStudio/blob/fd66407f9447b2348e1dab74901328d3b8bd2e47/LICENSE-NOTICE.md), `pyproject.toml`.

- A AGPL permite uso interno e comercial do programa nas condições da licença; **não equivale a licença permissiva MIT**. Redistribuir software derivado/combinado ou disponibilizar versão modificada via rede pode gerar obrigações de oferta de código-fonte correspondente. A fronteira de processos/HTTP não deve ser tratada como isenção jurídica automática. Obter revisão jurídica antes de adoptar o código.
- O upstream anuncia uma **licença comercial separada** para incorporação em produtos proprietários sem obrigações AGPL e disponibiliza funcionalidades Pro; isso não implica que a **versão open source** exija subscrição para correr.
- **OmniVoice default: pesos CC-BY-NC** com termos adicionais para tokenizer (Higgs Audio 2 / Meta Llama); o próprio catálogo `backend/config/model_licenses.json` identifica `commercial_use:false` e `review_status:noncommercial` em `k2-fsa/OmniVoice`. **Não seleccionar este modelo para distribuição/uso comercial do Jarvis sem direitos e revisão adequados.**
- `omnivoice/` (código Python do motor) é indicado como **Apache-2.0** por upstream, **mas pesos e tokenizers não herdam automaticamente a licença Apache**.
- Outros motores também têm pesos/licenças próprias. Ex.: Supertonic-3: SDK MIT, pesos OpenRAIL-M com condições; KittenTTS é inglês apenas. Não assumir que a licença da aplicação autoriza automaticamente modelos/vozes/outputs.
- Voz do Issa ou de outra pessoa requer gravação de referência autorizada e consentimento explícito, especialmente se houver clonagem, e retenção limitada.

**Política recomendada:** não importar ficheiros de VoiceStudio para `rightware-corporations/jarvis` antes de uma matriz `software-code license / model license / weights revision / output rights / redistribution / consent`. Se for usada a aplicação como serviço local separado, documentar arquitectura, distribuição e obrigações AGPL com aconselhamento jurídico.

## 4. Comparação com o que já existe no Wyzer

| Necessidade | Wyzer 0.3.1 no `develop` | VoiceStudio avaliado | Orientação |
| --- | --- | --- | --- |
| Wake word «Hey Jarvis» | `wyzer/speech/openwakeword.py`, depende de ONNX válido | VoiceStudio não é substituto directo do wake word do Jarvis | **Continuar openWakeWord** (licença/modelo por validar). |
| STT português | `wyzer/speech/whisper.py` usa faster-whisper mas força `language="en"` e modelo `small.en` | API STT local Whisper/WhisperX e WS parcialmente contínuo | **Primeiro reparar/adaptar STT existente**, comparar latência/acerto contra VoiceStudio. |
| TTS português | `wyzer/speech/kokoro.py` mapeia vozes `pf`/`pm`, default inglês | Muitos motores; português `pt-BR`/`pt-PT`, perfil e streaming | Avaliar 1–2 motores licenciados para runtime comercial; **não adoptar OmniVoice default NC**. |
| Turn-taking e interrupção | `wyzer/ui/desktop.py` e `wyzer/app/cli.py` contêm loops e interromper em inglês | VoiceStudio fornece áudio e transcrições, não decide tarefa/política do Jarvis | Orquestração no Wyzer; interfaces de áudio devem aceitar cancelamento/timeout. |
| Memória, IA e OS tools | Wyzer + Ollama e registry/policy | VoiceStudio é plataforma de voz | **Não trocar núcleo** por VoiceStudio. |
| Deploy | Local/servidor/híbrido ainda indecisos | Possível serviço local, Docker e desktop | Medir custo e segurança; sem servidor remoto agora. |

## 5. Arquitectura de integração proposta — não implementada

```text
Microfone (Issa / Windows)
      |
  Wake word Jarvis (detector ONNX avaliado separadamente)
      |
  VoiceCaptureAdapter -> STTAdapter
      |                    ├─ Wyzer Faster-Whisper PT (baseline)
      |                    └─ VoiceStudio local HTTP/WS (candidato)
      v
  Session/context -> Wyzer Orchestrator -> Ollama (local/private)
                          |                |
                    policy + tools       resposta de texto
                                             |
                                     TTSAdapter
                                          ├─ Kokoro PT (baseline)
                                          └─ VoiceStudio local HTTP/WS (candidato)
                                             |
                                         AudioOutput
                                             |
                                          HUD state
```

**Proposta de contratos:** `SpeechToText.transcribe(audio, language, session_id, cancel_token)`; `SpeechToText.stream(...)`; `TextToSpeech.synthesize(text, voice, language, cancel_token)`; `TextToSpeech.stream(...)`. Definir estados e formatos sem impor biblioteca/dependência. No futuro, adapter `VoiceStudioClient` por HTTP/WS seria um módulo **separado/opcional**, sem copiar a implementação AGPL.

**Segurança:** usar loopback por omissão; não expor painel administrativo; autenticação para qualquer tráfego remoto; TLS/WSS se sair da máquina; protecção de logs e gravações; timeout/size limits; consentimento explícito; privilégios mínimos.

## 6. Gates propostos antes de integrar

- [ ] **VOICE-LIC-01:** matriz jurídica e de pesos/voz/outputs por revisão exacta de 2–3 modelos candidatos. Não instalar modelos cuja licença não cumpra a distribuição prevista.
- [ ] **VOICE-PT-01:** avaliar `pt-BR` vs `pt-PT` vs português de Moçambique na voz e no STT. Testar nomes de pessoas/lugares e comandos: «Jarvis», «abre o navegador», «encontra o ficheiro», «cancela», «não», «sim»; sem guardar áudio sem autorização.
- [ ] **VOICE-STT-01:** corrigir modo multilingue do Faster-Whisper já presente no Wyzer, com mocks e sem downloads; manter `language=pt` configurável.
- [ ] **VOICE-TTS-01:** comparar Kokoro PT com **um** motor opcional local de licença admissível. Não colocar VoiceStudio e modelos pesados em autostart por omissão.
- [ ] **VOICE-API-01:** estudar `/v1/audio/transcriptions`, `/v1/audio/transcriptions/stream`, `/v1/audio/speech` e `/ws/tts`; descrever erros/frames, autenticação, cold start e comportamento de cancelamento.
- [ ] **VOICE-PERF-01:** medir latência para primeira transcrição parcial, TTFA, RTF, CPU/RAM/VRAM, precisão de comandos, ecos/interrupção e falhas em hardware consentido.
- [ ] **VOICE-ARCH-01:** decidir **baseline Wyzer** versus **serviço VoiceStudio opcional**, documentando custo de memória, isolamento, upgrades e licenças.
- [ ] **VOICE-RELEASE-01:** só considerar release após testes E2E reais, instalação reversível, direitos de distribuição e avaliação com Issa.

## 7. Critério de selecção e status

**Não é critério suficiente:** 646 línguas anunciadas, grande popularidade, interface bonita, existência de modelo `pt`, fornecedor ter free tier ou app ser open source.  
**Critério essencial:** português inteligível em Moçambique, funcionamento autónomo sem API paga, licenças compatíveis com a distribuição prevista, execução segura, velocidade e recursos aceitáveis.

| Evidência | Estado |
| --- | --- |
| Código de rotas REST/WS e documentação inspeccionados | **INSPECCIONADO** |
| Código de variantes `pt-BR` e `pt-PT` inspeccionado | **INSPECCIONADO** |
| Declarações de 646 línguas e performance | **ANUNCIADO / NÃO TESTADO** |
| Voz pt-MZ, latência e sotaque de Issa | **NÃO TESTADO** |
| Modelo com licença comercial adequada seleccionado | **PENDENTE** |
| VoiceStudio instalado ou executado na RIGHTWARE | **NÃO** |
| Integração no código do Jarvis | **NÃO** |

**Documentos associados:** [JAR-VOICE-PT-00](10_VOICE_PT_AUDIT.md), [JAR-ARCH-01](11_ARCHITECTURE_REVIEW_AND_EVOLUTION.md), [HUD/UX](12_HUD_REFERENCES_AND_UX_VISION.md). A interface holográfica é um projecto separado da escolha do sintetizador.
