# VEXEL — JARVIS PARA ISSA MAULID

Handoff operacional e histórico de investigação — 04/11/2026, Africa/Maputo.

## 00. Ler primeiro — ponto exacto de continuação

Estamos na investigação e selecção de uma base existente de assistente JARVIS gratuito. O utilizador entregou um relatório Perplexity; o relatório foi lido e criticado. A próxima tarefa é auditoria documental e de código dos finalistas, sem instalar dependências, executar o código dos projectos, configurar contas ou fazer deploy.

Nenhum repositório foi escolhido, clonado, instalado ou testado nesta investigação. Nenhum PASS funcional foi obtido. Não apresentar afirmações de README como resultados comprovados. Não recomeçar com introduções genéricas, sugestões de OpenClaw ou perguntas já respondidas. Começar pela auditoria comparativa e reportar descobertas concretas.

Este ficheiro é uma síntese operacional extensa da conversa, não uma exportação literal de todas as mensagens. Preserva objectivos, correcções, histórico relevante, URLs, limitações e trabalho pendente. O apêndice contém o texto extraído do relatório entregue, preservado como fonte não validada. Não fingir acesso à conversa antiga, ao PC do Issa ou a ferramentas que não existam no novo chat.

## 01. Pessoas e contexto

- RIGHTWARE é a organização; não confundir com a identidade pessoal do utilizador.
- VEXEL é a linha/contexto de trabalho desta entrega.
- Destinatário: Issa Maulid, também escrito informalmente Issa Maulis. Parceiro da VEXEL.
- O utilizador é o operador técnico que vai preparar a solução. Tem Claude Pro e ChatGPT Plus como ferramentas de trabalho.
- O PC do Issa ainda NÃO está disponível. CPU, RAM, GPU, microfone e sistema operativo não foram confirmados. Windows é hipótese prioritária, não facto confirmado.
- Não transferir as especificações do HP EliteBook do utilizador para o computador do Issa.
- Existe uma cotação anterior para Issa; preço não é objecto da decisão técnica actual. Não assumir orçamento disponível nem subscrição futura do Issa a partir dela.

## 02. Objectivo e requisitos vinculativos

O Issa imagina um assistente pessoal presente no computador: chega, diz “Jarvis” ou “Hey Jarvis”, ele acorda, ouve e responde por voz. Quer pensar com ele, investigar, aprofundar ideias, usar aplicações e realizar trabalho com continuidade. A experiência de voz é central; painel/HUD próprio é desejável. Não basta um chat genérico nem apenas ditado para terminal.

Requisitos:
1. Ausência de APIs pagas ou subscrições obrigatórias de IA em funcionamento.
2. Claude/ChatGPT podem ajudar a instalar, programar e configurar. NÃO devem ser o cérebro obrigatório do Jarvis.
3. Activação por nome, reconhecimento de fala, modelo, resposta falada e memória devem ter uma configuração sem serviços pagos obrigatórios.
4. Aproveitar código existente. Não começar a construir um produto novo de raiz.
5. Português utilizável e compreensão da pronúncia real do Issa. pt-PT específico NÃO foi escolhido; o relatório introduziu essa preferência sem confirmação.
6. Conversa natural, continuidade, pesquisa e tarefas nas aplicações autorizadas são a visão. O conjunto exacto de apps/tarefas ainda não foi recolhido; não bloquear a auditoria por isso.
7. Processamento local é aceitável. Um servidor próprio ou alugado é opção posterior, não filtro obrigatório na pesquisa.
8. Não excluir um projecto só porque é local, só porque não tem deploy pronto ou só porque oferece também um provider pago.
9. Excluir a DEPENDÊNCIA paga obrigatória. Um modo local genuíno pode tornar elegível um projecto cujo default é cloud.
10. Sem API paga não significa electricidade/hardware/alojamento gratuitos. Não prometer hospedagem gratuita permanente.
11. Free tier, créditos promocionais e login de subscrição não são independência de serviço pago.

## 03. Comportamento esperado do próximo assistente

O utilizador pediu raciocínio e trabalho de engenharia: avaliar antes de executar, ser específico, não genérico e não atribuir falhas aos prompts dele. Já corrigiu várias vezes o desvio para Claude como runtime e para OpenClaw/portais. Não repetir esses desvios.

Não transformar recomendação em decisão aprovada. Usar estados: confirmado pelo utilizador, candidato, hipótese, anunciado pelo autor, identificado no código, testado, não confirmado. Não prometer funcionamento universal ou “faz tudo”. Não ficar a pedir autorização para cada leitura pública; a investigação está autorizada. Instalação e deploy ainda não são a fase actual.

## 04. Origem e histórico relevante

Vídeo inicial: https://www.youtube.com/watch?v=BgpRjk4Yoqk
Título encontrado: I Stopped Paying for AI APIs… and Built This Jarvis Instead, Zubair Trabzada / AI Workshop.

O utilizador tentou NotebookLM e Gemini. O resumo recebido mencionava AI Workshop Lite, um prompt pack, Ollama, qwen3.5:9b e VoiceStudio. A descrição/transcrição integral do vídeo NÃO foi obtida directamente pelo assistente. Não afirmar que foi visto ou analisado minuto a minuto.

Links relacionados:
- https://www.skool.com/aiworkshop-lite/about — página pública anunciava acesso gratuito; comunidade paga é outra oferta. Não precisamos de depender dela.
- https://github.com/debpalash/VoiceStudio — componente de voz; não é, sozinho, um Jarvis completo.
- https://ollama.com/library/qwen3.5 — modelo foi encontrado no catálogo; não foi seleccionado.
- https://docs.ollama.com/windows

Histórico resumido:
1. Foi proposto diagnóstico PowerShell do PC. Não executado; o utilizador ainda não tem esse PC.
2. Utilizador perguntou por Railway/Vercel para poupar o PC. Foi explicado que modelo pode correr num servidor, mas hospedagem tem custos e controlo de apps locais exige um componente local. Nada foi aprovado ou configurado.
3. Utilizador reforçou visão de assistente pessoal amplo.
4. Pediu investigação de repositórios existentes em vez de construir de raiz.
5. Primeira pesquisa desviou para OpenClaw/Open WebUI/AnythingLLM/LibreChat/Open Interpreter. Utilizador rejeitou esse foco: quer experiência Jarvis por voz.
6. Segunda pesquisa encontrou vários Jarvis ligados a Claude. Utilizador esclareceu novamente: Claude só para desenvolver/instalar; funcionamento deve ser free.
7. Foi definido método de pesquisa e entregue prompt Perplexity.
8. Utilizador anexou relatório com 18 candidatos; foi analisado e encontradas falhas de evidência e triagem.
9. Agora pede handoff para continuar no chat normal, sem repetir investigação introdutória.

## 05. Estado actual e checklist

- [x] Visão e restrição de custos clarificadas.
- [x] Pesquisas públicas preliminares realizadas.
- [x] Prompt de pesquisa aprofundada entregue e utilizado.
- [x] Relatório Perplexity recebido e lido.
- [x] Revisão crítica do relatório e algumas verificações públicas.
- [ ] Fixar commits/versões dos candidatos auditados.
- [ ] Ler implementação real da cadeia de voz, providers e ferramentas.
- [ ] Verificar licenças do código/modelos/vozes e dependências externas.
- [ ] Comparar os finalistas e seleccionar base para prova de conceito.
- [ ] Obter hardware e rotina do Issa na fase apropriada.
- [ ] Instalar em ambiente de teste e executar testes funcionais.
- [ ] Configurar português e palavra de activação.
- [ ] Validar tarefas reais e entregar.

## 06. Auditoria do relatório Perplexity

Fonte original: “Investigação_ assistentes “JARVIS” locais e open s.pdf”.
Library ID: libfile_283159fcafb881919184610f3bec0b02
Link: https://chatgpt.com/library?file_id=libfile_283159fcafb881919184610f3bec0b02&account_id=personal

Conclusões do relatório, NÃO decisões nossas:
- ndunl075/Jarvis seria a melhor experiência global.
- Theycallmeinsane/jarvis seria o melhor para ferramentas Windows e instalação.
- Couvbat/Jarvis seria a melhor referência de arquitectura/segurança.
- Sugeria pilotar o primeiro e aproveitar referências dos outros.

Problemas identificados:
1. Referência [1] usada repetidamente para ndunl075 aponta na bibliografia para Ambidiosidad/jarvis. ndunl075 aparece como [19]. Correcção necessária; não invalida automaticamente cada afirmação, mas elimina rastreabilidade adequada.
2. A maior parte da evidência é README/estrutura de pastas. Existência de tests/ não significa testes aprovados. Nenhum teste próprio foi executado.
3. Superlativos “melhor arquitectura” e “instalação mais simples” são hipóteses sem comparação prática.
4. Excluir projecto porque default é cloud contradiz o critério: devemos verificar modo local completo antes de excluir.
5. Português pt-PT e integrações CRM/email/VEXEL foram assumidos sem decisão do utilizador.
6. Não misturar três bases prematuramente. Primeiro escolher a melhor base completa; integrar componentes apenas onde necessário.
7. O relatório diz que hardware Axx33284 não estava declarado na evidência consultada; a pesquisa anterior desta conversa encontrou no README referência a RTX 3060 12 GB e 32 GB RAM. Revalidar na versão auditada.
8. Falha de acesso a Theycallmeinsane nesta sessão não comprova remoção/inexistência. Não usar mirrors como validação primária.

## 07. Finalistas para auditoria — nenhum aprovado

### ndunl075/Jarvis
https://github.com/ndunl075/Jarvis
https://github.com/ndunl075/Jarvis/releases
Documentação consultada anunciava Windows, openWakeWord, Silero VAD, faster-whisper, Ollama, Piper, interrupção, orb/HUD/tray, notas, controlo de apps, pesquisa DuckDuckGo e deep research. Modo Ultra com Brave/Groq/Jina é opcional segundo README.
Alertas: defaults STT base.en e voz inglesa; README continha link de release condicionado a publicação de ZIP; consulta de releases não confirmou um instalador utilizável. Não afirmar que todos os recursos funcionam. Memória rica e documentos requerem inspecção.
Forks onlyflames360/jarvis e brocode47/jarvis apareceram nas buscas: não contar como bases independentes sem diferenças verificadas.

### Theycallmeinsane/jarvis
https://github.com/Theycallmeinsane/jarvis
NOVO candidato prioritário do relatório. O relatório anuncia Windows, wake word, Whisper, Ollama default, Piper/Kokoro/SAPI, memória JSON, histórico JSONL, extensão Chrome, ferramentas e testes. Claude seria opcional.
Estado: acesso directo falhou no último turno; resultados de pesquisa incluíram um proxy. Portanto NÃO foi validado independentemente no código. Confirmar origem, acesso, licença, providers, scripts e ferramentas.

### Axx33284/jarvis
https://github.com/Axx33284/jarvis
README consultado anuncia Windows nativo via pywebview/WebView2, wake word local, Ollama/Qwen, Whisper, Kokoro, memória, ferramentas e skills. Arquitectura descrita inclui gate, audit e undo journal; sem comprovação de eficácia.
Hardware declarado no README consultado: RTX 3060 12 GB / 32 GB RAM; small.en; foco voz britânica inglesa. Documento menciona setup.ps1 que instala dependências/modelos. Nada executado.
Contradição a investigar: descrição anuncia agir sem pedir autorização; estrutura também anuncia confirmações. Verificar caminho efectivo, não inferir segurança pela pasta safety/.
Licença ainda não confirmada nesta revisão: código público não basta.

### RustamovAkrom/JARVIS
https://github.com/RustamovAkrom/JARVIS
README consultado: JARVIS/MARK LIV, Python/PyQt6, HUD, memória, ferramentas; Gemini Live default; cadeia alternativa STT/LLM/TTS documentada como capaz de funcionar localmente. Wake word opcional. ENGINE & PROVIDERS permite alternar.
Primeiro arranque documentado pede chave Gemini: questão principal é se há arranque/configuração totalmente local sem chave e sem fallback externo. Reavaliar; não descartar só por default cloud.
README observado referia Python 3.14+, instalação de Playwright. Dados temporais podem mudar; fixar versão antes de concluir.

### SpandanNagale/ARIA
https://github.com/SpandanNagale/ARIA
README consultado: Windows, openWakeWord “Hey Aria”, faster-whisper, Ollama Qwen3:14b, XTTS-v2/Piper fallback, HUD PySide6, memória ChromaDB, ferramentas de PC/web. Treino do wake word foi feito separadamente; autor reconhece detector inicial pouco afinado.
Orientado a GPU de classe 12 GB; README referia RTX 5070 e 16 GB+ RAM, com pressão de VRAM e dependências CUDA específicas. Não tratar como requisito mínimo medido.
Para virar Jarvis é preciso mudar detector/modelo de activação, não apenas o texto da UI. Verificar licenças de modelos/voz e português efectivo. Não instalar automaticamente.

## 08. Outras pistas — não perder, não priorizar sem evidência

- https://github.com/Couvbat/Jarvis — Linux, Whisper/Ollama/Piper, wake word opcional, memória/RAG/MCP e políticas documentadas. Referência técnica, não automaticamente base Windows.
- https://github.com/alexberardi/jarvis-server — Jarvis Automation, servidor e agente desktop/voz; documentação indicava pré-release/work in progress.
- https://docs.jarvisautomation.dev/ e https://docs.jarvisautomation.dev/agent/voice/
- https://github.com/lusparkl/local_ai_assistant_jarvis — my-own-jarvis, documentação/PyPI localizada, ainda não auditado.
- https://github.com/BatmanOnTop/jarvis — local macOS, ainda não auditado.
- https://github.com/MichelleBudri/my-jarvis
- https://github.com/Ambidiosidad/jarvis
- https://github.com/vigneshwaran484/Jarvis
- https://github.com/stevensaint/jarvis — possível relação/fork PersonalJarvis; origem precisa verificação.
- https://github.com/dmrr35/Open.Jarvis
- https://github.com/PiyushBorseGit/Jarvis-ai
- https://github.com/mahirhacks/Jarvis-Voice-Assistant
- https://github.com/kalaiii2618/jarvis-local-ai
- https://github.com/nick31415926/voice_assistant
- https://github.com/sosoj92/jarvis-assistant-vocal
- https://github.com/bertrandmbanwi/Jarvis — reavaliar modo local, não excluir só por default OpenAI.
- https://github.com/thefhiter/jarvis — verificar selecção local e fallbacks.
- https://github.com/isair/jarvis — pista adicional; não validada. Verificar licença comercial, não assumir liberdade de revenda.
- https://github.com/lopadova/jarvis-desktop — pista adicional de configuração local, não auditada.
- https://github.com/hamezksm/loci — pista adicional de voz local, não auditada.

Referências fora da selecção actual:
- https://github.com/adewaskar/jarvis — UI Iron Man, wake phrase, bridge Node/Claude Agent SDK, ElevenLabs opcional/browser speech. Provável referência do tutorial “dá o link ao Claude e instala”; NÃO confirmado como mesmo tutorial do utilizador. Dependência Claude torna-o inelegível para runtime actual, salvo fork local comprovado.
- https://github.com/JManuelPorras/hey-jarvis — Windows wake word/Whisper + Claude CLI + Edge TTS; depende de Claude.
- https://github.com/anymikey/jarvis — Claude e Deepgram/TTS; não gratuito independente.
- https://github.com/RizN91/jarvis — chave OpenAI; não elegível para núcleo gratuito.
- https://github.com/PersonalJarvis/PersonalJarvis redireccionou para https://github.com/Dodaios/Dodaios na consulta. Não assumir identidade estável sem verificar.
- OpenClaw, Open WebUI, AnythingLLM, LibreChat, Open Interpreter, GPT Researcher e AgenticSeek foram explorados; não são o foco escolhido. Não voltar a recomendá-los como substituição genérica da experiência Jarvis.

## 09. Próxima tarefa exacta: auditoria estática comparativa

Trabalhar com os cinco finalistas, priorizando acesso e evidência. Leitura pública e download/clone apenas para inspecção são compatíveis com investigação; NÃO executar scripts, instalar dependências, descarregar modelos ou iniciar serviços.

1. Confirmar repositório original/fork, commit/tag/data, licença e releases.
2. Ler configuração, manifesto de dependências e scripts de instalação sem os executar.
3. Mapear ficheiros reais que implementam wake word, STT, LLM, TTS, memória e ferramentas.
4. Identificar todas as chamadas externas e chaves obrigatórias, incluindo fallback. Verificar se config local evita autenticação cloud no arranque.
5. Avaliar conversa multivolta, barge-in, estados de escuta, eco e timeout. Não confundir presença de VAD com interrupção completa.
6. Avaliar português: modelos .en, idioma hardcoded, comandos por regex, língua de confirmação, voz disponível, nomes próprios e activação.
7. Verificar memória após reinício, correcção/apagamento e diferença entre notas/histórico/memória semântica.
8. Verificar pesquisa vs abrir URL, citações, leitura de páginas e dependências pagas.
9. Inspeccionar acções Windows/browser/documentos e confirmação/auditoria. Acesso a shell não prova domínio de todas as apps.
10. Examinar testes/CI e problemas conhecidos. Registar “não executado” para testes próprios.
11. Produzir matriz com evidências por caminho/linha e commit, bloqueadores, configurações necessárias e alterações de código necessárias.
12. Recomendar uma base principal e alternativa apenas se evidência suficiente; caso contrário explicitar o bloqueio e continuar pesquisa dirigida.

Não inventar notas numéricas de maturidade. Não comparar velocidade sem benchmarks reproduzidos. Não concluir custo de servidor antes de saber modelo e uso. Não misturar projectos antes de demonstrar a necessidade.

## 10. Prova de conceito futura — ainda não executada

Critérios de teste depois da selecção e autorização de instalação:
- “Jarvis”/“Hey Jarvis” em silêncio/ruído, falsos positivos e frase contínua.
- Português falado pelo Issa, nomes e termos reais, qualidade da voz.
- Conversa com “explica melhor”, “isso”, “volta ao assunto”; interrupção sem auto-activar com a própria voz.
- Guardar/corrigir/apagar memória e verificar após reinício.
- Pesquisa com fontes e leitura de documentos em pasta de teste.
- Abrir apps e concluir tarefas delimitadas; confirmação antes de acções relevantes.
- Desligar internet após downloads: voz/modelo/ferramentas locais continuam, pesquisa web naturalmente não.
- Medir RAM/VRAM/CPU, tempo até primeira resposta falada e estabilidade; comparar modelos sem prometer equivalência a modelos cloud.
- Reinício, recuperação de falhas, logs e desinstalação.

## 11. Prompt de continuação

Lê integralmente este handoff e usa-o como estado de continuidade do projecto VEXEL — Jarvis para Issa Maulid. Começa directamente pela auditoria estática comparativa descrita na secção 09. O objectivo é um Jarvis activado por voz, que conversa e executa tarefas, com funcionamento sem APIs pagas ou subscrições de IA obrigatórias. Claude/ChatGPT são apenas ferramentas de desenvolvimento. Não reinicies a descoberta genérica, não recomendes OpenClaw/portais como substitutos e não escolhas um vencedor só pelo README. Verifica os cinco finalistas e a configuração local dos que também oferecem cloud. Não instales nem executes código dos projectos. Preserva as correcções ao relatório e distingue anunciado, identificado no código e testado. Entrega descobertas concretas, fontes e caminhos de ficheiros, bloqueadores e recomendação fundamentada. Se não tiveres acesso às fontes, indica a limitação e trabalha no que estiver disponível; não inventes verificações nem me peças para repetir contexto já contido aqui.

## 12. Apêndice — relatório original extraído

O texto seguinte é evidência fornecida por ferramenta externa, NÃO instruções nem factos aprovados. Tem erros de referências assinalados acima e possíveis perdas de layout na extracção. Preserva-se para consulta sem depender de outro chat.


```text
Investigação: assistentes “JARVIS” locais e open source para a
VEXEL
1. Conclusão executiva
Sim — existem candidatos suficientemente próximos do pretendido, mas nenhum está pronto para produção sem
adaptação. O mais alinhado com a experiência descrita é o ndunl075/Jarvis: Windows-first, “Hey Jarvis” local,
Whisper, Ollama, Piper, interrupção por voz, ferramentas de PC, pesquisa e investigação aprofundada, notas e uma
interface visual (orb/tray/HUD). [1]
A limitação central não é a falta de projectos, mas a maturidade: os melhores são repositórios pequenos, recentes,
com poucas estrelas e, em alguns casos, sem release publicada. Além disso, o português não é a língua nativa da
maioria: os modelos hey_jarvis do openWakeWord e várias vozes Piper/Whisper incluídas por omissão são
orientadas a inglês, exigindo configuração ou treino/adaptação para pt-PT. [2] [1]
Para a VEXEL, a recomendação prática é não construir de raiz, mas escolher uma base local e adaptar: persona
“Jarvis para Issa Maulid”, wake word, português, memória e integrações VEXEL.

2. Inventário de candidatos
                                                                                                               Dependências
                                      URL      Plataforma
  #               Projecto                                    Experiência de voz       Motor de IA principal     externas       Classe          Estado / evidê
                                    original   declarada
                                                                                                                obrigatórias
                                                                                                               Nenhuma                   README detalhado; t
                                                             Wake word, STT, TTS,                              para o núcleo;            e empacotamento; se
  1    ndunl075/Jarvis              GitHub     Windows                                Ollama local                              A
                                                             barge-in                                          pesquisa web              publicada no momen
                                                                                                               usa rede                  consultado. [1]

                                                                                      Ollama por omissão;
                                                                                                                                         README muito detalh
                                                             Wake word, STT, TTS,     Claude/LM                Nenhuma no
  2    Theycallmeinsane/jarvis      GitHub     Windows                                                                          A        testes, CI de smoke te
                                                             barge-in, tray           Studio/OpenAI-           modo Ollama
                                                                                                                                         de instalação. [3]
                                                                                      compatível opcionais

                                                                                                                                         Arquitectura, testes, a
                                                             Wake word opcional,                               Nenhuma
  3    Couvbat/Jarvis               GitHub     Linux                                  Ollama local                              A        documentação de se
                                                             STT, TTS, barge-in                                para o núcleo
                                                                                                                                         Linux apenas. [2]

                                                                                                                                         README descreve ins
                                                             openWakeWord                                      Nenhuma
                                                                                                                                         winget, visão, áudio d
  4    Axx33284/jarvis              GitHub     Windows       “hey_jarvis”, Whisper,   Ollama + tool calling    declarada        A/B
                                                                                                                                         e biblioteca de skills;
                                                             Kokoro                                            para o núcleo
                                                                                                                                         completa pendente.

                                                             openWakeWord
                                                                                                                                         Evidência parcial via
                                               Não           hey_jarvis em            Não confirmado nesta
  5    MichelleBudri/my-jarvis      GitHub                                                                     A confirmar      E        requer inspecção do
                                               confirmado    CPU; interface           consulta
                                                                                                                                         README/código. [5]
                                                             servida localmente

                                                                                      Ollama                                             README descreve me
                                               Raspberry     Whisper, Piper, wake                              Nenhuma
  6    Ambidiosidad/jarvis          GitHub                                            (gemma3:1b,                               A        persistente, UI web e
                                               Pi / Docker   word opcional                                     declarada
                                                                                      qwen2.5:3b)                                        local. [1]

                                                             openWakeWord,
                                                                                                               Nenhuma                   README declara pipe
  7    SpandanNagale/ARIA           GitHub     Windows       faster-whisper,          Ollama Qwen3                              A
                                                                                                               declarada                 totalmente offline. [6
                                                             XTTS/Piper, HUD

                                                             “Hey Jarvis” via                                                            README declara GUI
                                               Não                                    Ollama/llama3.2, ciclo   Nenhuma
  8    vigneshwaran484/Jarvis       GitHub                   openWakeWord, TTS                                                  A        Reactor” e ferrament
                                               confirmado                             ReAct                    declarada
                                                             neural                                                                      sistema. [7]

                                                             Whisper/Nemotron,                                 Nenhuma
                                                                                      Ollama ou servidor                                 README descreve too
  9    stevensaint/jarvis           GitHub     Self-hosted   Piper/Kokoro/Qwen3-                               obrigatória se   A/B
                                                                                      OpenAI-compatível                                  modelos locais. [8]
                                                             TTS                                               Ollama

                                               Windows-                                                                                  Descrição genérica; in
  10   dmrr35/Open.Jarvis           GitHub                   A confirmar              A confirmar              A confirmar      E
                                               first                                                                                     técnica pendente. [9]


[QUEBRA DE PÁGINA]
                                                                                                                                        Dependências
                                                      URL        Plataforma
  #                     Projecto                                                    Experiência de voz          Motor de IA principal     externas            Classe          Estado / evidê
                                                    original     declarada
                                                                                                                                         obrigatórias

                                                                                                                                                                       README declara offli
                                                                Não                                            LLM local + automação
  11        PiyushBorseGit/Jarvis-ai                GitHub                        STT, VAD, voz                                         A confirmar           B/E      cadeia completa requ
                                                                confirmado                                     desktop
                                                                                                                                                                       verificação. [10]

                                                                                                               Ollama Qwen;
            mahirhacks/Jarvis-Voice-                                              Wake word + faster-          roteamento imediato                                     README declara cont
  12                                                GitHub      Windows                                                                 Ollama local          A/B
            Assistant                                                             whisper                      para comandos                                           apps, browser e siste
                                                                                                               simples

                                                                                                               Qwen via Ollama;                                        Stack declarada com
                                                                Não                                                                     Ollama, Piper,
  13        kalaiii2618/jarvis-local-ai             GitHub                        Whisper + Piper              Qdrant para                                    A/B      Qdrant adiciona com
                                                                confirmado                                                              Qdrant                         [12]
                                                                                                               memória/RAG

                                                                                                                                                                       README declara
                                                                Não               Wake word, faster-                                    Nenhuma
  14        nick31415926/voice_assistant            GitHub                                                     Ollama                                         A        hey_jarvis_v0
                                                                confirmado        whisper, XTTS                                         declarada
                                                                                                                                                                       Ollama e XTTS. [13]

                                                                                                               Ollama;                                                 README declara mod
            sosoj92/jarvis-assistant-                           Não                                                                     Nenhuma no
  15                                                GitHub                        Voz local declarada          Piper/Kokoro/Windows                           A/B      totalmente offline, se
            vocal                                               confirmado                                                              modo local
                                                                                                               TTS                                                     custos de utilização.

                                                                                                               Gemini Live por                                         Pipeline local é possí
                                                                Windows,          Wake word opcional,                                   Gemini por
  16        RustamovAkrom/JARVIS                    GitHub                                                     omissão; Ollama/LM                             D/B      não é o comportame
                                                                PyQt6             faster-whisper, HUD                                   omissão
                                                                                                               Studio/etc. opcionais                                   omissão. [15]

                                                                macOS-                                         OpenAI por omissão;      OpenAI por                     Suporta modo offline
  17        bertrandmbanwi/Jarvis                   GitHub                        Voz local declarada                                                         D/B
                                                                first                                          Ollama/MLX opcionais     omissão                        cérebro por omissão

                                                                                                               Anthropic API/Claude
                                                                Não               Wake word, voz,                                       Claude/Groq                    Ollama existe, mas nã
  18        thefhiter/jarvis                        GitHub                                                     Code por omissão;                              D/B
                                                                confirmado        painel de definições                                  por omissão                    caminho principal. [1
                                                                                                               Ollama opcional

Nota sobre os projectos sugeridos: lusparkl/local_ai_assistant_jarvis, BatmanOnTop/jarvis e
alexberardi/jarvis-server não produziram evidência suficiente nas consultas efectuadas para serem classificados
com confiança; devem ser tratados como E — informação insuficiente, não como candidatos validados. O
adewaskar/jarvis não foi confirmado nesta sessão como dependente de Claude, mas a pista prévia e os projectos
semelhantes justificam mantê-lo fora da lista principal até inspecção directa.

3. Matriz dos melhores candidatos
       Critério                 ndunl075/Jarvis                      Theycallmeinsane/jarvis                      Couvbat/Jarvis                Axx33284/jarvis

                      “Hey Jarvis”, openWakeWord,                                                        “Hey Jarvis” opcional,          hey_jarvis ONNX
                                                               “Hey Jarvis”, openWakeWord; teste
                      sensibilidade configurável.                                                        openWakeWord, sem chave         em CPU, sempre
  Wake word                                                    dedicado --wake-test.
                      IDENTIFICADO NO README.                                                            API. IDENTIFICADO NO            activo.
                      [1]                                      IDENTIFICADO NO README. [3]
                                                                                                         README. [2]                     ANUNCIADO. [4]

                      faster-whisper;                          faster-whisper; modelos                   faster-whisper; idioma
                                                                                                                                         Whisper.
  STT                 tiny/base/small; build inclui            maioritariamente .en por omissão.         configurável, incluindo
                                                               [3]                                                                       ANUNCIADO. [4]
                      base.en. [1]                                                                       auto. [2]

                                                               Ollama por omissão; Claude/LM
                      Ollama, streaming, tool calling,                                                   Ollama; múltiplos providers     Ollama + tool calling.
  LLM                                                          Studio/OpenAI-compatível opcionais.
                      histórico. [1]                           [3]                                       e fallback local/remoto. [2]     [4]


                      Piper; en_GB-alan-medium                                                           Piper; vozes descarregáveis.
  TTS                                                          Piper/Kokoro/SAPI; vozes locais. [3]                                      Kokoro. [4]
                      por omissão. [1]                                                                   [2]


                                                               Barge-in; interrupção durante a           Barge-in implementado na
  Interrupção         Barge-in por fala. [1]                                                                                             Não confirmado.
                                                               resposta. [3]                             camada de voz. [2]

                      Histórico de conversa e notas            memory.json para factos,                  Histórico em SQLite,            Biblioteca de skills
                      markdown persistentes; não há            history.jsonl para contexto               lembretes persistentes e        auto-melhorável;
  Memória
                      memória semântica completa               entre reinícios; comandos                 RAG local com embeddings        memória a confirmar.
                      declarada. [1]                           “remember/forget”. [3]                    Ollama. [2]                      [4]


                      DuckDuckGo + investigação
                      profunda local, com relatório            DuckDuckGo, Wikipedia, leitura de         Fetch de páginas; pesquisa
  Pesquisa web                                                                                                                           A confirmar.
                      markdown e citações; Ultra               páginas e Chrome. [3]                     documental local. [2]
                      opcional usa Brave/Groq/Jina. [1]

                                                               Conjunto muito extenso: apps,
                      Abrir/fechar apps, URLs, Steam,                                                    Ficheiros, web e                Controlo de Windows,
  Aplicações /                                                 janelas, media, ficheiros,
                      volume, screenshots, visão local,                                                  lançamento de apps, com         visão e áudio do
  PC                                                           Gmail/Calendar opcionais, Chrome,
                      ditação, clipboard. [1]                                                            sandbox e whitelist. [2]        sistema. [4]
                                                               PowerShell com confirmação. [3]


[QUEBRA DE PÁGINA]
     Critério              ndunl075/Jarvis                   Theycallmeinsane/jarvis                    Couvbat/Jarvis             Axx33284/jarvis

                Notas markdown; leitura/produção       Leitura de PDF, Word, texto e código;      Pesquisa em notas/ficheiros
  Documentos    de documentos genéricos não é o        criação, cópia, zip, organização de        indexados; texto apenas,      A confirmar.
                foco principal. [1]                    ficheiros. [3]                             sem PDF nativo. [2]

                                                       Extensão Chrome: tabs, leitura de
                                                                                                  MCP para extensões;
  Automação     Abrir URLs/pesquisar; não há           página, cliques, escrita, scroll, vídeo;
                                                                                                  automação browser não é       A confirmar.
  browser       automação profunda declarada. [1]      acções sensíveis pedem confirmação.
                                                       [3]                                        foco central. [2]

                Tray, orb flutuante, HUD, painéis de   Tray com estados visuais, logs,
                                                                                                  TUI Rich no terminal; sem
  Interface     notas/pesquisa/logs, paleta de         definições; menos “HUD” que o                                            A confirmar.
                                                                                                  GUI desktop declarada. [2]
                comandos. [1]                          anterior. [3]

                Sim, foco principal; build portátil    Sim, foco principal; setup.ps1.
  Windows                                                                                         Não; Linux testado. [2]       Sim. [4]
                PyInstaller. [1]                       [3]


                                                                                                  Whisper configurável para
                Não documentado; STT incluído é        Não documentado; STT .en e vozes           outros idiomas;
  Português                                                                                                                     Não confirmado.
                .en e voz Piper é inglesa. [1]         inglesas por omissão. [3]                  documentação demonstra
                                                                                                  francês, não português. [2]

                CPU mínimo 4 núcleos/8 GB;                                                        8 GB mínimo, 16 GB
  Hardware                                             Sem GPU: 8–16 GB RAM conforme                                            Não declarado na
                recomendado 6+ núcleos/16 GB;                                                     recomendado, ~10 GB de
  declarado                                            modelo; GPU acelera. [3]                                                 evidência consultada.
                GPU opcional com 8+ GB VRAM. [1]                                                  modelos; GPU opcional. [2]

                                                                                                  MIT; modelos
                                                       MIT; modelos têm licenças próprias.
  Licença       MIT. [1]                               [3]                                        descarregados                 A confirmar.
                                                                                                  separadamente. [2]


4. Análise técnica dos três melhores

4.1 ndunl075/Jarvis — melhor enquadramento global
O que já existe: o projecto declara e descreve uma cadeia completa local: openWakeWord, Silero VAD, faster-
whisper, Ollama com tool calling e Piper. Inclui barge-in, modos activo/mudo/adormecido, controlo de aplicações,
screenshots, visão local via Ollama, notas markdown, pesquisa DuckDuckGo e um modo de deep research com
planeador/worker locais, páginas completas, citações e relatório markdown. [1]
Evidência no repositório: existem tests/, pyproject.toml, requirements.lock, build.ps1, jarvis.spec,
documentação técnica (SPEC.md, BUILD.md) e estrutura de empacotamento Windows. Isso é um sinal positivo de
engenharia, mas o README indica que o download oficial depende de uma release futura com um ficheiro exacto
Jarvis-0.0.1-windows-x64.zip; na consulta, não havia release publicada. [1]

O que falta para a VEXEL:
     Validação real do wake word com a pronúncia de “Jarvis” pelo Issa Maulid.
     Português pt-PT: trocar Whisper .en por um modelo multilingue, testar compreensão e escolher/ajustar voz pt-
     PT.
     Memória persistente mais rica do que notas/histórico: preferências, pessoas, projectos VEXEL, documentos e
     correcção/apagamento controlado.
     Integrações VEXEL: e-mail, calendário, CRM, pastas de trabalho, navegador e ferramentas internas via MCP ou
     ferramentas Python.
     Teste de latência sem GPU e definição de um modelo Ollama adequado ao hardware real.
Veredicto: melhor candidato para experiência JARVIS, desde que se aceite instalar a partir do código e adaptar
português/memória.

4.2 Theycallmeinsane/jarvis — melhor execução de tarefas no Windows
O que já existe: é o candidato com o conjunto mais amplo de ferramentas práticas: abrir/fechar aplicações, janelas,
volume por aplicação, media, temporizadores, notas, ficheiros, clipboard, screenshots, definições do Windows, Wi-
Fi, brilho, processos, serviços, GitHub, Calendar/Gmail opcionais e automação Chrome através de extensão. [3]
Evidência no código/documentação: o README descreve explicitamente o fluxo openWakeWord → webrtcvad →
faster-whisper → agente → Piper/Kokoro, memória em data/memory.json, histórico em data/history.jsonl,
confirmação para acções perigosas, MCP, testes offline e um smoke test de voz em GitHub Actions. [3]
Pontos de atenção:


[QUEBRA DE PÁGINA]
    O Claude é uma opção explícita, mas não é obrigatório: o provider por omissão é Ollama e o README permite
    trocar para LM Studio ou qualquer servidor OpenAI-compatível local. [3]
    Os modelos Whisper e vozes por omissão são maioritariamente ingleses; para Issa Maulid será necessário
    configurar STT multilingue e voz em português. [3]
    A superfície de controlo é muito poderosa: PowerShell, processos, serviços e ficheiros exigem políticas de
    permissão, confirmação e auditoria antes de uso profissional. [3]
Veredicto: melhor candidato para autonomia e execução de tarefas no PC, com o maior esforço de
governança/segurança.

4.3 Couvbat/Jarvis — melhor arquitectura e disciplina de segurança
O que já existe: pipeline local com Whisper, Ollama, Piper, VAD, wake word opcional, memória SQLite, lembretes
persistentes, RAG com nomic-embed-text via Ollama, MCP, sandbox de directórios, whitelist de comandos,
confirmações e testes. [2]
Evidência no repositório: há ARCHITECTURE.md, AUDIT.md, testes com cobertura, ruff, pytest, instalação reproduzível
via pip install -e . e documentação explícita de limitações conhecidas. É o projecto mais transparente quanto ao
que está implementado e ao que ainda não está. [2]
Limitações importantes:
    É Linux, não Windows; não serve directamente como base primária se o PC do Issa for Windows.
    A interface é um TUI, não um painel desktop ou representação visual tipo JARVIS. [2]
    O RAG é apenas texto; PDF exigiria dependência e trabalho adicional. [2]
    A pesquisa web existe como fetch de páginas, mas não há um modo de investigação profunda comparável ao do
    ndunl075/Jarvis. [2]
Veredicto: excelente referência de arquitectura — especialmente para sandbox, RAG local, MCP e política de
ferramentas — mas não é a base ideal para um Windows-first JARVIS.

5. Recomendações condicionais
                Necessidade                       Recomendação condicional                                            Justificação

                                                                                         Wake word, voz bidireccional, barge-in, Ollama local, HUD/orb/tray,
  Melhor experiência JARVIS                    ndunl075/Jarvis                           pesquisa e deep research, notas e ferramentas Windows numa base
                                                                                         única. [1]

                                                                                         Ambos podem operar com openWakeWord, Whisper, Ollama e Piper
  Melhor independência de serviços             ndunl075/Jarvis ou
                                                                                         sem chave de API obrigatória; no ndunl075, os serviços extra são opt-
  pagos                                        Couvbat/Jarvis
                                                                                         in. [1] [2]

                                                                                         setup.ps1 instala dependências, detecta hardware, configura
  Instalação/adaptação mais simples
                                               Theycallmeinsane/jarvis                   modelo e voz, cria atalhos e inclui diagnóstico, teste de wake word e
  em Windows
                                                                                         modo texto. [3]

  Melhor referência técnica para                                                         Memória SQLite, RAG local, MCP, sandbox, whitelist, confirmações e
                                               Couvbat/Jarvis
  memória/RAG/segurança                                                                  testes são mais maduros conceptualmente. [2]

Não recomendo, nesta fase, nenhum projecto como “instalar e usar amanhã”. O percurso mais defensável é pilotar
o ndunl075/Jarvis como base de experiência e usar o Theycallmeinsane/jarvis como referência para ferramentas
Windows e automação Chrome; o Couvbat/Jarvis serve como referência para memória/RAG e políticas de
segurança.

6. Exclusões e ressalvas
              Solução                                                            Motivo da exclusão da lista principal
  RustamovAkrom/JARVIS                Gemini Live é o motor por omissão; o modo local existe, mas não é o comportamento principal. [15]

  bertrandmbanwi/Jarvis               OpenAI é o cérebro por omissão; Ollama/MLX são alternativas. [16]

  thefhiter/jarvis                    A cadeia preferencial é Anthropic API → Claude Code → Groq → Ollama; Ollama é apenas o último recurso. [17]

                                      Não validado nesta investigação; a pista prévia indica dependência de Claude. Manter fora até inspecção directa do
  adewaskar/jarvis
                                      código e requirements.

  Porcupine/Picovoice como            Pode exigir conta/chave/licença Picovoice; o Couvbat/Jarvis explicitamente prefere openWakeWord para evitar essa
  wake word                           dependência. [2]

  Edge TTS                            Serviço online da Microsoft; não satisfaz o requisito de voz local/offline.


[QUEBRA DE PÁGINA]
             Solução                                                      Motivo da exclusão da lista principal

  Pesquisa via Tavily, Serper ou   Podem ser opcionais, mas não devem ser o mecanismo principal se o objectivo é funcionar sem chaves pagas. O
  Brave                            ndunl075 usa DuckDuckGo no pipeline base e reserva Brave/Groq/Jina para um modo Ultra opt-in. [1]


7. Plano de prova de conceito para Issa Maulid
Fase 0 — Pré-requisitos
    Confirmar Windows, microfone/headset, permissões de microfone e política de segurança da VEXEL.
    Instalar Ollama e escolher inicialmente um modelo pequeno; não assumir GPU.
    Instalar o candidato a partir do código, registando commit, tag e data.
Fase 1 — Voz e activação
 1. Arrancar em segundo plano e confirmar que o wake word não consome recursos de forma excessiva.
 2. Testar “Jarvis” e “Hey Jarvis” em silêncio, com música, com televisão e a distâncias realistas.
 3. Testar falsos positivos com vozes semelhantes e conteúdo de fundo.
 4. Testar comando na mesma respiração: “Hey Jarvis, abre o Outlook”.
 5. Testar interrupção: começar uma resposta longa e voltar a falar.
Fase 2 — Português e conversa
 1. Configurar Whisper multilingue, se necessário; testar frases pt-PT com nomes, siglas e terminologia VEXEL.
 2. Testar resposta falada em pt-PT, escolhendo voz Piper/compatível adequada.
 3. Avaliar continuidade: “Isso”, “explica melhor”, “e em Maputo?”, “volta ao assunto anterior”.
 4. Testar correcção: “Isso está errado”, “esquece isso”, “não voltes a dizer isso”.
Fase 3 — Memória e documentos
 1. Guardar factos: “Lembra-te que o meu gestor é X”.
 2. Reiniciar o assistente e confirmar persistência.
 3. Listar, corrigir e apagar memórias.
 4. Indexar uma pasta de documentos VEXEL e perguntar por conteúdos específicos.
 5. Testar criação, leitura, resumo e exportação de documentos.
Fase 4 — Ferramentas
 1. Abrir/fechar aplicações e URLs.
 2. Criar, mover, procurar e ler ficheiros dentro de pastas autorizadas.
 3. Testar pesquisa web — exige internet — e confirmar que a conversa local continua a funcionar sem internet.
 4. Testar leitura de página e investigação com fontes.
 5. Testar automação de browser apenas em sites de teste, com confirmação para acções de escrita.
Fase 5 — Segurança e operação
 1. Confirmar que acções destrutivas pedem confirmação.
 2. Restringir directórios, comandos e ferramentas expostas ao modelo.
 3. Reiniciar o PC e o assistente; verificar recuperação de estado, logs e memória.
 4. Testar operação sem internet: wake word, STT, LLM, TTS, ficheiros locais e aplicações devem funcionar;
    pesquisa web, weather e descarregamento inicial de modelos não.

8. Questões ainda em aberto
    Hardware real: CPU, RAM, GPU/VRAM, microfone e ruído ambiente do Issa Maulid. Isto determina o modelo
    Ollama, o tamanho do Whisper e a viabilidade de Kokoro/XTTS.
    Windows confirmado: os dois melhores candidatos assumem Windows, mas a versão, permissões corporativas
    e política de instalação ainda precisam de validação.
    Português pt-PT: nenhum dos três melhores documenta explicitamente pt-PT. Será necessário testar Whisper
    multilingue, pronúncia do wake word e voz TTS.
    Releases e estabilidade: o ndunl075/Jarvis não tinha release publicada na consulta; o Theycallmeinsane/jarvis
    tem muito pouca tracção externa. São projectos promissores, mas jovens. [1] [3]


[QUEBRA DE PÁGINA]
    Integrações VEXEL: e-mail, calendário, CRM, pastas partilhadas, autenticação e ferramentas internas não
    foram avaliados.
    Segurança operacional: ferramentas de ficheiros, PowerShell, browser e contas Google exigem uma política
    VEXEL de permissões, confirmação e auditoria. [3] [2]
    Vídeo de referência: não consegui consultar a descrição ou transcrição do vídeo do YouTube nesta investigação;
    por isso, não atribuo componentes nem repositórios ao vídeo sem evidência directa.

9. Fontes principais
    ndunl075/Jarvis — README, especificação, build e modelo de privacidade: https://github.com/ndunl075/Jarvis [1]
    Theycallmeinsane/jarvis — README, arquitectura de voz, ferramentas, MCP e testes: https://github.com/Theycall
    meinsane/jarvis [3]
    Couvbat/Jarvis — README, arquitectura, RAG, segurança e testes: https://github.com/Couvbat/Jarvis [2]
    Axx33284/jarvis — descrição de Windows, openWakeWord, Whisper, Kokoro e Ollama:
    https://github.com/Axx33284/jarvis [4]
    Ambidiosidad/jarvis — assistente offline para Raspberry Pi/Docker: https://github.com/Ambidiosidad/jarvis [1]
    MichelleBudri/my-jarvis — openWakeWord hey_jarvis e interface local: https://github.com/MichelleBudri/my-jarvis
     [5]

    SpandanNagale/ARIA — pipeline offline Windows: https://github.com/SpandanNagale/ARIA [6]
    vigneshwaran484/Jarvis — assistente offline com ReAct e GUI: https://github.com/vigneshwaran484/Jarvis [7]
    stevensaint/jarvis — assistente self-hosted com Ollama e múltiplos motores de voz:
    https://github.com/stevensaint/jarvis [8]
    mahirhacks/Jarvis-Voice-Assistant — Windows, wake word, Whisper e Ollama: https://github.com/mahirhacks/Jarvi
    s-Voice-Assistant [11]
    kalaiii2618/jarvis-local-ai — Whisper, Qwen/Ollama, Piper e Qdrant: https://github.com/kalaiii2618/jarvis-local-ai [12]
    nick31415926/voice_assistant — wake word, faster-whisper, Ollama e XTTS: https://github.com/nick31415926/voice_
    assistant [13]
    sosoj92/jarvis-assistant-vocal — modo local declarado sem API: https://github.com/sosoj92/jarvis-assistant-vocal [14]
    RustamovAkrom/JARVIS — PyQt6, Gemini Live por omissão e pipeline local opcional:
    https://github.com/RustamovAkrom/JARVIS [15]
    bertrandmbanwi/Jarvis — OpenAI por omissão, Ollama/MLX opcional: https://github.com/bertrandmbanwi/Jarvis
     [16]

    thefhiter/jarvis — Anthropic/Claude Code/Groq por omissão, Ollama opcional: https://github.com/thefhiter/jarvis
     [17]

                                                                     ⁂

  1. https://github.com/Ambidiosidad/jarvis
  2. https://github.com/Couvbat/Jarvis
  3. https://github.com/Theycallmeinsane/jarvis
  4. https://github.com/Axx33284/jarvis
  5. https://github.com/MichelleBudri/my-jarvis
  6. https://github.com/SpandanNagale/ARIA
  7. https://github.com/vigneshwaran484/Jarvis
  8. https://github.com/stevensaint/jarvis
  9. https://github.com/dmrr35/Open.Jarvis
 10. https://github.com/PiyushBorseGit/Jarvis-ai
 11. https://github.com/mahirhacks/Jarvis-Voice-Assistant
 12. https://github.com/kalaiii2618/jarvis-local-ai
 13. https://github.com/nick31415926/voice_assistant
 14. https://github.com/sosoj92/jarvis-assistant-vocal/blob/main/README.en.md
 15. https://github.com/RustamovAkrom/JARVIS
 16. https://github.com/bertrandmbanwi/Jarvis
 17. https://github.com/thefhiter/jarvis/blob/main/README.md


[QUEBRA DE PÁGINA]
18. https://github.com/DO0OG/Ari-VoiceCommand
19. https://github.com/ndunl075/Jarvis
20. https://github.com/devkewalramani/Jarvis-local/blob/main/README.md
21. https://github.com/DO0OG
22. https://github.com/topics/jarvis?l=python&o=desc&s=updated
23. https://github.com/topics/faster-whisper?l=typescript&o=desc&s=stars
24. https://github.com/darshitp091/Jarvis/blob/main/doctor.py
25. https://github.com/CoderRebel/J.A.R.V.I.S/blob/main/README.md
26. https://github.com/ONEPUNCHMAN411/Jarvis
27. https://github.com/csells/awesome-jarvis


[QUEBRA DE PÁGINA]

```