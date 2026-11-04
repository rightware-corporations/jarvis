# JAR-P2-00 — Auditoria estática do caminho de voz e português

**Data:** 2026-11-04 (Africa/Maputo)  
**Estado:** INSPECCIONADO NO CÓDIGO; NÃO EXECUTADO.  
**Base:** `XtraWyze/Wyzer-Ai@db83c085feca32d3c091361165cb9ac7ecadafe0` (`v0.3.1`); `rightware-corporations/jarvis@e071145fd4f4d31d81fd39763f28431e0ec75e7c` (`develop` antes desta auditoria).

## Objectivo vinculativo

VEXEL Jarvis — Issa Edition deve acordar por `Jarvis` ou `Hey Jarvis`, compreender e responder em português, manter conversa/contexto e executar **somente tarefas autorizadas**, sem APIs pagas ou subscrições de IA obrigatórias. O laboratório FastAPI sem voz é apenas infra-estrutura de ensaio; não substitui a experiência principal. Instalação final local/servidor/híbrida e hardware do Issa continuam indecisos.

## Evidência concreta — leitura estática

| Área | Ficheiro e linhas | Constatação | Estado |
| --- | --- | --- | --- |
| Wake word | [`wyzer/speech/openwakeword.py#L29-L64`](https://github.com/rightware-corporations/jarvis/blob/e071145fd4f4d31d81fd39763f28431e0ec75e7c/wyzer/speech/openwakeword.py#L29-L64) | `OpenWakeWordDetector` exige ficheiro ONNX existente e carrega `openwakeword.model.Model(..., inference_framework="onnx")`. | Código identificado; microfone/modelo não testados. |
| Modelo de activação | [`wyzer.toml#L57-L80`](https://github.com/rightware-corporations/jarvis/blob/e071145fd4f4d31d81fd39763f28431e0ec75e7c/wyzer.toml#L57-L80) | Voz desactivada; `wake_phrase="hey wyzer"`, `wake_model="hey_Wyzer.onnx"`, `whisper_model="small.en"`. Dois ONNX não foram importados por revisão de direitos. | Bloqueia voz imediata. |
| STT | [`wyzer/speech/whisper.py#L87-L99`](https://github.com/rightware-corporations/jarvis/blob/e071145fd4f4d31d81fd39763f28431e0ec75e7c/wyzer/speech/whisper.py#L87-L99) | `model.transcribe(..., language="en")` e hotwords inglesas; trocar só o nome do modelo não basta para português. | Alteração real de código/configuração necessária. |
| TTS | [`wyzer/speech/kokoro.py#L11-L35`](https://github.com/rightware-corporations/jarvis/blob/e071145fd4f4d31d81fd39763f28431e0ec75e7c/wyzer/speech/kokoro.py#L11-L35) | Mapeamento de prefixos `pf`/`pm` para português brasileiro está presente. `af_heart` continua a voz por omissão. | Suporte de encaminhamento no código; qualidade, vozes disponíveis e direitos não verificados. |
| Comandos de interrupção | [`wyzer/app/cli.py#L178-L238`](https://github.com/rightware-corporations/jarvis/blob/e071145fd4f4d31d81fd39763f28431e0ec75e7c/wyzer/app/cli.py#L178-L238) | `stop/cancel/pause` e frases derivadas de Wyzer; detecção de pause por regex inglesa. | Localizar para `parar`, `cancelar`, `pausa` etc., mantendo decisões determinísticas. |
| Confirmações | [`wyzer/app/orchestrator.py#L60-L66`](https://github.com/rightware-corporations/jarvis/blob/e071145fd4f4d31d81fd39763f28431e0ec75e7c/wyzer/app/orchestrator.py#L60-L66); [`wyzer/policy/confirmations.py#L32-L54`](https://github.com/rightware-corporations/jarvis/blob/e071145fd4f4d31d81fd39763f28431e0ec75e7c/wyzer/policy/confirmations.py#L32-L54) | `yes/no/stop/pause/resume` e heurísticas de risco não são localizadas. `ConfirmationMode.ALWAYS` e `NEVER` existem e devem preservar prioridades. | Bloqueador para comandos e acções em PT. |
| LLM | [`wyzer/brain/factory.py#L21-L59`](https://github.com/rightware-corporations/jarvis/blob/e071145fd4f4d31d81fd39763f28431e0ec75e7c/wyzer/brain/factory.py#L21-L59); `wyzer.toml` | Ollama usa endpoint configurável, por omissão `127.0.0.1:11434`; alternativas OpenAI-compatíveis são opcionais. | Caminho local identificado; inferência real não testada. |
| Lab | `jarvis_lab/headless.py`, `jarvis_lab/api.py` | Registry vazio, sem ferramentas OS; testes usam providers simulados; `speech_enabled=false` no health. | Segurança parcial verificada por CI; não é Jarvis de voz. |

## Estratégia de adaptação sem corromper o upstream

A importação original tem **182/182 blobs SHA iguais** e workflow de integridade. NÃO modificar `wyzer/` silenciosamente nem alterar o manifesto para esconder drift. Primeiro adoptar uma das opções rastreáveis: (a) snapshot congelado `upstream/` e diffs adaptados auditados; ou (b) patches versionados com verificação separada do original. Implementar adaptadores de língua/voz e testes independentes antes de activar ferramentas reais.

## Sequência técnica e gates

1. **JAR-P2-01 — STT PT:** expor linguagem `pt`/auto de forma configurável, usar modelo Whisper multilingue em vez de `*.en`; unit tests com modelo falso confirmam parâmetro correcto, ausência de downloads automáticos e falha fechada.
2. **JAR-P2-02 — TTS PT:** enumerar vozes realmente suportadas pela versão Kokoro escolhida; verificar direitos de modelos/vozes, testar inteligibilidade de português utilizado pelo Issa; `pf`/`pm` no código não provam qualidade nem variante pt-PT.
3. **JAR-P2-03 — Wake word Jarvis:** obter ou treinar ONNX com proveniência/licença comprovada; reconfigurar nome e frase; testes de detecção/falsos positivos requerem microfone real na fase de QA autorizada.
4. **JAR-P2-04 — Segurança linguística:** tratar `sim`, `não`, `cancela`, `pára`, `pausa`, `continua` sem confundir com texto livre; acções com risco elevado exigem confirmação explícita e vinculada à acção. Testes negativos para evitar execução sem confirmação.
5. **JAR-P2-05 — Conversa de voz:** verificar turnos, timeout, eco, interrupção durante TTS (barge-in) e respostas faladas. A existência de VAD ou de detector de frases não comprova barge-in completo.
6. **JAR-P1-01C — Antes de preview HTTPS:** testar concorrência de pedidos por sessão, revalidação de TTL, gestão de estado/quotas fora de um único processo, isolamento e exposição do token; nenhum controlo real do Windows no servidor.
7. **JAR-P1-03 — Inferência auto-hospedada:** integrar modelo Ollama real e testar pedidos/contexto/latência num runner/host controlado com logs; não assumir GPU ou alojamento grátis.
8. **JAR-P3 — Aceitação:** medir com áudio e pronúncia reais do Issa e só então escolher distribuição local/servidor/híbrida.

## Estado de evidência

- [x] Código e configuração do Wyzer examinados estaticamente.
- [x] O GitHub Actions confirmou integridade e os contratos actuais; [run 41815835913](https://github.com/rightware-corporations/jarvis/actions/runs/41815835913) concluiu com dois jobs PASS no commit auditado.
- [ ] Qualquer teste executado por esta auditoria (nenhum).
- [ ] STT/TTS/wake word PT implementados e testados.
- [ ] Modelo real Ollama testado.
- [ ] Ferramentas desktop autorizadas e QA de áudio do Issa.

**Próximo trabalho recomendado:** consolidar a estratégia de patch de upstream e implementar JAR-P2-01 com testes isolados, sem instalar dependências localmente e sem activar ferramentas reais.
