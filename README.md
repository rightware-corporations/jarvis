# VEXEL Jarvis — Issa Edition

Assistente pessoal da **VEXEL / RIGHTWARE**, derivado de [Wyzer AI v0.3.1](https://github.com/XtraWyze/Wyzer-Ai), para activação por «Jarvis», conversação por voz em português, memória e execução de tarefas autorizadas. **Meta de runtime:** sem subscrição obrigatória nem APIs pagas de IA. A escolha entre local, servidor e híbrido continua pendente de testes.

> **Estado em 2026-11-04 — EM DESENVOLVIMENTO.** O código upstream foi importado para `develop` e preservado com hashes verificáveis. Existe uma API FastAPI headless e um protótipo web de laboratório com **16 testes de contrato anteriormente PASS**, utilizando provider simulado. Não foi validado um LLM Ollama real, wake word «Jarvis», STT/TTS em português, controlo Windows real nem uma release instalada no equipamento do Issa. **A UI web não é o produto de voz final.**

## Estrutura actual — não confundir com a árvore-alvo

| Local | Conteúdo |
| --- | --- |
| `wyzer/` | Código upstream original (núcleo, voz, providers, memória, ferramentas, desktop). Preservado. |
| `jarvis_lab/` | Composição headless, API HTTP experimental e `web/` (HTML/CSS/JS); sem ferramentas Windows reais. |
| `tests/` | Testes importados do upstream, sem declaração de execução integral nesta migração. |
| `tests_lab/` | Testes de contrato do laboratório, já executados remotamente. |
| `docs/` | Estado, arquitectura, auditorias, backlog e aceitação. |
| `installer/` | Scripts upstream importados, não validados para distribuição RIGHTWARE. |

A **arquitectura-alvo proposta**, incluindo separação entre frontend, backend, agente Windows, memória, voz e segurança, está em [docs/11_ARCHITECTURE_REVIEW_AND_EVOLUTION.md](docs/11_ARCHITECTURE_REVIEW_AND_EVOLUTION.md). **Ainda não foram movidos ficheiros para `apps/` ou `jarvis/`**. Será uma migração incremental após testes e definição de política de patches.

## Branches e integração

- `main`: base estável; não desenvolver directamente.
- `develop`: única branch de engenharia; upstream importado, laboratório e documentação.
- [PR #2](https://github.com/rightware-corporations/jarvis/pull/2): Draft, sem merge, de `develop` para `main`.

## Integridade e direitos

- Upstream: `XtraWyze/Wyzer-Ai` tag `v0.3.1`, commit `db83c085feca32d3c091361165cb9ac7ecadafe0`.
- **182/182** ficheiros textuais/código verificados por hashes Git; **44 binários** (42 PNG + 2 ONNX) omitidos até revisão de direitos.
- [UPSTREAM_PROVENANCE.md](UPSTREAM_PROVENANCE.md), [manifesto](upstream-v0.3.1-manifest.json), `LICENSE` (MIT original) e `NOTICE.md` preservados. Licenças de modelos, vozes e demais assets precisam de validação separada.
- Não modificar `wyzer/` nem adulterar o manifesto sem estratégia de patch/auditoria que preserve a base.

## Verificação remota

- [CI — Source Integrity](.github/workflows/source-integrity.yml): integridade de ficheiros, sintaxe Python e contratos do `tests_lab/` em GitHub Actions Ubuntu/Python 3.11.
- Exemplo confirmado: [run 41816985515](https://github.com/rightware-corporations/jarvis/actions/runs/41816985515) PASS no commit da auditoria anterior. Estes testes **não** exercitam voz, GPU, browser, Ollama ou Windows real.
- Lab: `jarvis_lab/api.py` (FastAPI), `jarvis_lab/web/` (UI). A ausência de modelo configurado provoca `MODEL_UNAVAILABLE`; um provider falso só é injectado nos testes.

## Próxima sequência recomendada

1. Completar política de patches e auditabilidade da base Wyzer.
2. Endurecer sessões, concorrência, autorização e confirmação de acções.
3. Preparar STT português e wake word com licenças verificadas.
4. Testar Ollama real num ambiente controlado; observar latência e contexto.
5. Evoluir UI desktop voice-first e modularização de frontend/backend de forma progressiva.
6. Validar segurança do agente Windows; testar no PC do Issa apenas com autorização.

## Documentação de continuidade

1. [00_START_HERE](docs/00_START_HERE.md) e [01_CURRENT](docs/01_CURRENT.md)
2. [03_BACKLOG](docs/03_BACKLOG.md) e [04_ACCEPTANCE](docs/04_ACCEPTANCE.md)
3. [10_VOICE_PT_AUDIT](docs/10_VOICE_PT_AUDIT.md) — português e voz
4. [11_ARCHITECTURE_REVIEW_AND_EVOLUTION](docs/11_ARCHITECTURE_REVIEW_AND_EVOLUTION.md) — inventário, riscos e estrutura futura

**Segurança:** repositório público. Não publicar credenciais, gravações, perfis pessoais ou modelos sem direitos. Não expor o laboratório na Internet sem HTTPS, autenticação e ensaios de segurança. Claude/ChatGPT são ferramentas de desenvolvimento, nunca dependências obrigatórias do Jarvis em produção.

## Referências externas em estudo (sem integração)

- **Visual/HUD:** [12 — UX, overlay e grafo](docs/12_HUD_REFERENCES_AND_UX_VISION.md). React/Three.js, PySide6 e referências de orb flutuante; propostas, não interface final.
- **Voz:** [13 — VoiceStudio](docs/13_VOICESTUDIO_STATIC_ASSESSMENT.md). Candidato de STT/TTS local com APIs HTTP/WebSocket, mas **AGPL-3.0-only** na aplicação e pesos OmniVoice default com restrição não comercial. Não está integrado nem instalado.
- O Wyzer continua como motor; tecnologias/arte visual de terceiros só após verificação de direitos e QA.
