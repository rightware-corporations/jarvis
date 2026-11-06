# VEXEL Jarvis — Issa Edition

> **CONTINUIDADE / ESTADO MAIS RECENTE (06/11/2026):** [Master Handoff V2 — 26_MASTER_HANDOFF_2026-11-06.md](docs/26_MASTER_HANDOFF_2026-11-06.md). Esta é a leitura prioritária para novos agentes. **Ollama/Qwen3.5 2B foram testados realmente no Kaggle**; confirmação real B6 PASS; benchmark B7 **11/12** devido a selecção indevida de ferramenta. **JAR-COG-01 já publicada em `develop` com testes simulados; reteste com Qwen2B real ainda pendente. Memória persistente, agente executivo, microfone/voz Windows e release continuam pendentes.** Os parágrafos de 04–05/11 abaixo são preservados como histórico, incluindo afirmações então válidas de que ainda não havia inferência real.



## Recuperação do projecto e continuidade (04/11/2026)

**Se a conversa anterior falhar, não recomeçar o Jarvis:** iniciar por [docs/20_RECOVERY_START_HERE_2026-11-04.md](docs/20_RECOVERY_START_HERE_2026-11-04.md), depois ler o [handoff mestre](docs/21_MASTER_HANDOFF_2026-11-04.md), [decisões](docs/22_DECISION_REGISTER_2026-11-04.md) e [checklist/playbook](docs/23_EXECUTION_PLAYBOOK_2026-11-04.md).

Wyzer permanece o motor. O frontend `adewaskar/jarvis` é apenas candidato visual; Claude trabalha em skills/governação e Manus fará preview real Chromium. **Nenhum HUD externo importado, nenhuma voz Jarvis validada e nenhum serviço Ollama real testado.** O `CLAUDE.md` existe apenas como [draft original](docs/reference/CLAUDE_ORIGINAL_DRAFT_2026-11-04.md) e [revisão V2](docs/reference/CLAUDE_REVIEW_V2_DRAFT_2026-11-04.md), ainda não aprovada.


Assistente pessoal da **VEXEL / RIGHTWARE**, derivado de [Wyzer AI v0.3.1](https://github.com/XtraWyze/Wyzer-Ai), para activação por «Jarvis», conversação por voz em português, memória e execução de tarefas autorizadas. **Meta de runtime:** sem subscrição obrigatória nem APIs pagas de IA. A escolha entre local, servidor e híbrido continua pendente de testes.

> **Estado em 2026-11-05 — EM DESENVOLVIMENTO.** O núcleo VEXEL (`jarvis/`) já tem o ciclo de voz em português, a política de confirmação `sim/não/cancela`, três ferramentas autorizadas (aplicações sempre **simuladas**), o modo `--voice` e o diagnóstico `--diagnose`. São 399 testes com componentes simulados, todos PASS no CI (Linux, e parsing PowerShell 5.1 em Windows). **Ainda não foi validado** com Ollama real, microfone, voz SAPI portuguesa nem no PC do Issa: isso é a JAR-SLICE-01C, num PC de QA autorizado. A wake word «Jarvis» está bloqueada até haver um modelo com licença comercial.

## Estrutura do repositório

Definida no [ADR-0001](docs/adr/0001-estrutura-do-repositorio.md). O VEXEL Jarvis é uma **aplicação de desktop Windows local**, não uma aplicação web.

```
wyzer/ tests/ installer/ wyzer.toml pyproject.toml   upstream Wyzer v0.3.1 — imutável (182 ficheiros)
jarvis/                 BACKEND: núcleo VEXEL em Python (voz, PT, política, ferramentas, preflight)
  core/ voice/ brain/ tools/ language/ runtime/ ui/
apps/
  desktop/              FRONTEND do produto (orb 01E, HUD) — por iniciar
  weblab/               laboratório web FastAPI + HTML (não é o produto; antigo jarvis_lab/)
configs/                perfis TOML sem segredos
qa/
  windows/              inventário read-only do PC de QA (PowerShell)
  corpus/               frases PT-MZ de teste (só texto)
  benchmarks/           scripts de medição (G9)
tests_vexel/ tests_lab/ testes RIGHTWARE (CI)
docs/
  adr/                  decisões de arquitectura
  plans/                planos de fase
  reports/              relatórios de fase
  00–25_*.md            histórico e documentos de referência
scripts/  .github/workflows/
```

- **Base de dados:** ainda não existe no produto. A memória futura será um SQLite local no PC do utilizador, nunca no repositório.
- **IA:** modelo local servido pelo Ollama em `127.0.0.1`, instalado fora do repositório. Nenhuma API paga no runtime.
- **Nunca no git:** áudio, transcrições, logs de voz, bases de dados, modelos e venvs (`.wyzer/`, `evidence/`, `logs/` e `.venv/` estão ignorados).

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

- [CI — Source Integrity](.github/workflows/source-integrity.yml): integridade 182/182, compilação, `tests_lab/`, `tests_vexel/` e `--check-config` em Ubuntu/Python 3.11, e parsing do script de QA com o PowerShell 5.1 em Windows.
- Exemplo confirmado: [run 41816985515](https://github.com/rightware-corporations/jarvis/actions/runs/41816985515) PASS no commit da auditoria anterior. Estes testes **não** exercitam voz, GPU, browser, Ollama ou Windows real.
- Laboratório: `apps/weblab/api.py` (FastAPI, entrypoint `apps.weblab.api:app`), `apps/weblab/web/` (UI). A ausência de modelo configurado provoca `MODEL_UNAVAILABLE`; um provider falso só é injectado nos testes.

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
