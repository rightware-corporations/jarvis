# JAR-NET-01 — segurança do transporte do LLM local e gate de inferência

- **Data:** 05/11/2026
- **Modo:** TARGETED_SECURITY_ENGINEERING (fail-closed)
- **Estado final:** `NET_SECURITY_PASS` + `REAL_INFERENCE_PENDING` (ver secção 13 e a nota sobre Windows na secção 6)
- **Evidência:** `HTTP_CONTRACT_PASS` com servidores sintéticos em loopback. Nenhum modelo foi executado.

## 1. HEAD

| Momento | SHA |
|---|---|
| Inicial | `4e259bea9b0633a1591c13267d63f74246128ab7` (= `origin/develop`, árvore limpa, 182/182, CI anterior 12/12) |
| Código | `f31e688274ec5d25b80f7fd23eccf092e0410243` |
| Final | commit deste relatório (só documentação), a seguir a `f31e688` |

## 2. Causa do risco

`wyzer/brain/http.py` (`UrllibJsonTransport`, upstream e imutável) chama `urllib.request.urlopen`. Isto tem três consequências:

- **O opener por omissão inclui um `ProxyHandler()`.** Esse handler lê `HTTP_PROXY`, `HTTPS_PROXY` e `ALL_PROXY` e, em Windows sem variáveis de ambiente, o proxy do registo (`getproxies_registry`).
- **A excepção `<local>` do registo não cobre `127.0.0.1`.** O urllib só a aplica a nomes sem pontos, por isso um pedido a `127.0.0.1:11434` pode ir para o proxy do sistema, levando o prompt, os resultados das ferramentas e as respostas.
- **O opener global fica em cache desde o primeiro uso,** e segue redireccionamentos 301/302/303.

O teste de controlo `test_control_upstream_transport_is_captured_by_the_proxy` mostra o risco: com `HTTP_PROXY` apontado para um proxy hostil, o transporte upstream entrega-lhe o pedido.

## 3. Alteração exacta

| Ficheiro | Alteração |
|---|---|
| `jarvis/brain/local_transport.py` (novo) | `LoopbackJsonTransport`, que implementa o contrato `JsonTransport` do Wyzer (ver lista abaixo) |
| `jarvis/brain/pt_provider.py` | `create_direct_chat_provider(llm)` espelha o `create_chat_provider` do Wyzer com os mesmos argumentos, injecta `transport=LoopbackJsonTransport(endpoint)` e força `auto_start=False`. `create_local_provider` usa-o. Novo código de falha `PROVIDER_DESTINATION_DENIED`; uma resposta demasiado grande dá `PROVIDER_INVALID_RESPONSE` |
| `jarvis/runtime/preflight.py` | o diagnóstico do LLM usa o mesmo transporte |
| `jarvis/config.py` | `llm.endpoint` tem de cumprir a mesma regra de origem. **Mudança de comportamento:** `localhost` deixa de ser aceite (a configuração do repositório já usa `127.0.0.1`) |
| `.claude/rules/testing.md` | D01: servidores sintéticos só em `127.0.0.1`/`::1`, em portas efémeras |
| `.claude/rules/security.md` | D02: o contrato do transporte |
| `tests_vexel/ollama_loopback.py` | `RecordingProxy` (proxy hostil que regista bytes); `Reply.headers`; GETs por script |
| `tests_vexel/test_net01_loopback_transport.py` (novo) | testes adversariais |

O `LoopbackJsonTransport` comporta-se assim:
- usa um opener próprio, `build_opener(ProxyHandler({}), _NoRedirect())`, que não consulta nenhum proxy (ambiente, registo ou sistema) e recusa redireccionamentos;
- só aceita `http` para a origem configurada (esquema, IP de loopback literal, porta). Recusa nomes (`localhost` incluído), credenciais no URL, zone ids, IPv4-mapped e porta 0, **antes** de abrir um socket;
- limita o corpo da resposta a 4 MiB;
- mantém os timeouts, as verificações de JSON e as mensagens de erro do Wyzer (reutiliza `HttpTransportError` e `_safe_http_error`).

O que não muda:
- os 182 ficheiros do Wyzer;
- o protocolo Ollama (`OllamaChatProvider`, o parsing e a repetição do Qwen continuam upstream);
- as variáveis globais do processo;
- o modelo por omissão.

Não se criou outro cliente Ollama: o transporte é a peça que se injecta por `transport=`.

## 4. Testes adversariais

Em todos os testes o proxy hostil corre em `127.0.0.1`. Apaga-se qualquer variável `*_proxy` e define-se a variável em teste.

| ID | Teste | Resultado |
|---|---|---|
| controlo | transporte upstream com `HTTP_PROXY` | **capturado** pelo proxy (o risco existe) |
| T1 | `HTTP_PROXY` (e `http_proxy`) | ligação directa; 0 ligações ao proxy |
| T2 | `HTTPS_PROXY` | idem |
| T3 | `ALL_PROXY` | idem |
| T4 | `NO_PROXY` ausente e todas as variáveis definidas | idem |
| T5 | proxy do sistema: em Windows, leitor do registo simulado e `proxy_bypass_registry=False`; noutros SO, `getproxies()` simulado | controlo capturado; transporte VEXEL com 0 ligações a mais |
| T6/T8 | endpoint autorizado e resposta válida, num turno completo (hora de Maputo, 2 chamadas) | `ANSWERED`, 2 pedidos ao Ollama sintético |
| T7 | destinos recusados (`10.0.0.5`, `example.com`, `localhost`, `https`, outra porta, `127.0.0.2`, credenciais, `file:`, `ftp:`) | `LoopbackDestinationError`, **sem nenhum socket** (`socket.create_connection` falha se for chamado) |
| T7 | config e transporte recusam `192.168.1.20`, `localhost`, `https`, `ollama.local`, `[::1%eth0]`, `[::ffff:127.0.0.1]`, `:0`, `user@`, `0.0.0.0` | `SliceConfigError` e `LoopbackDestinationError` |
| T9 | timeout de 0,3 s | `PROVIDER_TIMEOUT` em < 2,5 s; proxy com 0 ligações |
| T10 | cancelamento com pedido em curso | `CancelledError` propagado; proxy com 0 ligações |
| T11 | não JSON, array, não UTF-8, > 4 MiB, HTTP 404 | as mesmas mensagens sanitizadas do Wyzer |
| T12 | bytes recebidos pelo proxy em todo o turno | `b""` |
| extra | redireccionamentos 301/302/303/307/308, em POST e em GET | não seguidos; o `Location` nunca é pedido |
| extra | paridade com a factory upstream (ollama, llama_cpp, openai_compatible) | atributos iguais, excepto o transporte e `auto_start` |
| extra | `LLMSettings` do Wyzer cru (`auto_start=True` por omissão) | o provider VEXEL fica com `auto_start=False` |
| extra | preflight com proxy hostil | diagnóstico directo, proxy com 0 ligações |

**Mutações** (feitas localmente e revertidas):

| Mutação | Efeito nos testes |
|---|---|
| retirar `ProxyHandler({})` | 9 testes falham |
| seguir redireccionamentos | 8 testes falham |

## 5. Evidência de ausência de tráfego para o proxy

- **Contagem:** o `RecordingProxy` conta as ligações TCP e guarda os bytes recebidos. Em todos os testes do transporte VEXEL ficou com `connections == 0` e `received() == b""`.
- **Controlo:** o mesmo proxy, com as mesmas variáveis, recebe o pedido do transporte upstream. A evidência não é vazia.

## 6. Resultados Linux e Windows

| Ambiente | Resultado |
|---|---|
| Linux cloud, Python 3.11, venv (`f31e688` antes do push) | `tests_vexel` + `tests_lab` com **561 passed** (dois runs); `tests_desktop` 87; os 45 contratos JAR-ENGINE-01 continuam verdes e passam agora pelo novo transporte |
| `windows-latest` (CI, `f31e688`) | `tests_vexel` **545 passed**, `tests_lab` 16 passed; `desktop-orb` em Windows com success |

**Windows: o que fica provado e o que não fica.**

Fica provado no runner `windows-latest`:
- o caminho real do urllib em Windows (`getproxies` → `getproxies_registry`), com o leitor do registo simulado;
- o comportamento com variáveis de ambiente.

Não fica provado:
- **o registo real de um PC com proxy configurado.** As definições de proxy da máquina não foram alteradas, como a ordem exige;
- WinHTTP/WPAD/PAC: o Python não os usa.

Este último ponto tem de ser confirmado no PC de QA (matriz, linha «Proxy»).

## 7. Revisão independente

Feita por um subagente, só de leitura, sobre o diff. **0 P0 e 0 P1.**

**Corrigidos:**
- **P2:** `auto_start` é agora forçado a `False`.
- **P3:**
  - config e transporte usam a mesma regra (credenciais, porta 0, zone id, IPv4-mapped);
  - porta 0 deixou de ser tratada como a porta 80;
  - resposta grande demais → `PROVIDER_INVALID_RESPONSE`;
  - redireccionamentos em GET testados;
  - limpeza de todas as variáveis `*_proxy`, para estabilidade em Windows;
  - teste de paridade com a factory upstream;
  - um erro ao ler o corpo de um HTTPError não escapa ao tipo de erro do transporte.

**Abertos:**
- **P2, fora do âmbito:** `apps/weblab/api.py` constrói o `OllamaChatProvider` com o transporte por omissão e aceita `JARVIS_OLLAMA_URL` sem validação. O laboratório não é o produto e não está implantado. A correcção fica como **JAR-NET-02**.
- **P3:** o timeout é por operação de socket (um servidor que envia aos poucos pode exceder o total), e a thread de um pedido cancelado mantém o socket até ao timeout. Ambos são comportamento upstream.

## 8. Integridade Wyzer

`scripts/verify_import.py` dá 182/182. A intersecção do diff com o manifesto está vazia (Q6).

## 9. Commits e CI

| SHA | Conteúdo | CI |
|---|---|---|
| `f31e688` | transporte, factory, config, preflight, regras D01/D02, testes | **12/12 success** no SHA exacto: push [42094026210](https://github.com/rightware-corporations/jarvis/actions/runs/42094026210), PR [42094037918](https://github.com/rightware-corporations/jarvis/actions/runs/42094037918). O `windows-python` mostra `tests_vexel` 545 passed (com os 51 testes JAR-NET-01, incluindo o caminho do registo Windows) e `tests_lab` 16 passed |
| seguinte | este relatório, `01_CURRENT`, `03_BACKLOG`, índice | mesmo workflow |

## 10. PR #2

Mantém-se `open`, `draft: true` e `merged: false`. Não foi tocado.

## 11. Matriz operacional para a primeira inferência real (JAR-INFER-01)

Execução só no PC de QA autorizado, por uma pessoa, segundo o plano 25 (G3, G4, G9, G10). Nada no PC do utilizador final.

| Item | Requisito | Verificação |
|---|---|---|
| Máquina | Windows 10 **22H2** ou Windows 11 (requisito oficial do Ollama) | `winver` |
| CPU | x86-64 com AVX2 | inventário G1 |
| RAM | 4b: ≥ 8 GB livres; 2b: ≥ 5 GB; 0.8b: ≥ 3 GB (indicativo, a medir) | Gestor de Tarefas durante o G9 |
| Disco | ≥ 10 GB livres; SSD de preferência | G1 |
| Ollama | instalado manualmente (G3); `auto_start=false`, o VEXEL nunca o inicia | `ollama --version` |
| Modelo e digest | `qwen3.5:0.8b`, `:2b`, `:4b`; registar o ID/digest exacto | `ollama list` e `ollama show <tag>` |
| Licença | confirmar a de cada tag (anunciada Apache-2.0 para o Qwen3.5) | `ollama show <tag> --license` |
| Endpoint | `http://127.0.0.1:11434` (só IP de loopback; `localhost` é recusado) | `python -m jarvis --check-config` |
| Proxy | garantido pelo transporte. Confirmar no PC: o proxy registado em Definições → Rede → Proxy **não** recebe tráfego do Jarvis | registar se há proxy configurado (sim/não); com proxy, repetir o caso A e confirmar que funciona |
| Diagnóstico | linha do LLM OK | `python -m jarvis --diagnose` |
| Corpus | `qa/corpus/pt_mz_v1.txt` (20 frases) | — |
| Ferramentas e confirmações | B/C com a ferramenta certa; D/E pedem «sim/não» e dão `SIMULATED`; F cancela | saída `[resultado=… acção=…]` |
| Latência | `llm_ms`, `llm_eval_count`, `llm_model_ms`, `think_ms`; primeira chamada a frio à parte | `python qa/benchmarks/latency_summary.py <logs>/text-turns.jsonl` |
| Rollback | G10 sem apagar; R1 (`ollama rm`, desinstalar) só com autorização | plano 25 |

**Testes progressivos:**
- Ordem: 1) `qwen3.5:0.8b` → 2) `qwen3.5:2b` → 3) `qwen3.5:4b`.
- Cada um usa uma cópia local da configuração (`--config`, fora do git), com o mesmo corpus e o mesmo procedimento.
- Pára-se num modelo quando dá FAIL de recursos (RAM a esgotar ou swap contínuo).
- A escolha definitiva sai das medições e fica registada num ADR (JAR-MODEL-ADR). `configs/` não muda sem decisão RIGHTWARE.

**Critério de `REAL_INFERENCE_PASS`** (por modelo, todos obrigatórios):
1. **Evidência independente de execução real:**
   - durante o turno, `ollama ps` mostra a tag carregada (com tamanho e processador);
   - `ollama list` dá o digest do modelo;
   - a versão do Ollama fica registada.
   - Um `llm_eval_count > 0` sozinho **não** basta: um servidor sintético também o produz.
2. **Prova de geração:** um nonce aleatório escolhido pelo operador no momento (por exemplo «Repete a palavra-código X»), que nenhum script prévio conhece, aparece na resposta.
3. Respostas em PT nas 20 frases.
4. B/C com a ferramenta correcta em pelo menos 19 de 20 tentativas; D/E com confirmação e `SIMULATED`; 0 afirmações falsas; 0 `PROVIDER_*` inesperados.
5. Latência registada. O G9 de voz é medido depois, em `--voice`.

**Evidência a arquivar** (sanitizada):
- os `jsonl` sem texto;
- a saída de `ollama ps`, `ollama list` e `ollama --version`;
- o resumo de latência.

Sem transcrições nem identificadores da máquina.

## 12. Bloqueadores restantes

1. Não há PC de QA autorizado com Windows 10 22H2 ou posterior e Ollama.
2. Licença e digest do modelo por registar (G3).
3. Comportamento com o proxy real do registo por confirmar no PC de QA.
4. JAR-NET-02: o Web Lab ainda usa o transporte por omissão (fora do produto).
5. Prompt de sistema do Wyzer com cerca de 10 000 caracteres: é um custo de latência, e reduzi-lo depende da JAR-ARCH-02.

## 13. Estado final

**`NET_SECURITY_PASS` + `REAL_INFERENCE_PENDING`**, com estas condições:
- o tráfego do LLM local não passa por proxies;
- os destinos não autorizados são recusados antes de abrir um socket;
- os testes adversariais e as regressões passam em Linux e no runner `windows-latest` (secção 9);
- a integridade está em 182/182;
- não há P0 nem P1 abertos.

O proxy configurado no registo de um PC Windows real não foi testado (secção 6). Por isso esse comportamento fica declarado como provado por construção (`ProxyHandler({})`) e pelo caminho de código no runner, e não por um PC real.
