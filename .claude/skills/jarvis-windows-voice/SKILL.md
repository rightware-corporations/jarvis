---
name: jarvis-windows-voice
description: Trabalho no ciclo de voz PT do VEXEL Jarvis (VoiceSession, confirmação, TTS/STT, preflight, Orb) e na preparação do QA Windows real (JAR-SLICE-01C, gates G1–G10) — o que se pode fazer na cloud/CI e o que só se faz no PC de QA com autorização.
when_to_use: Ao alterar jarvis/core, jarvis/voice, jarvis/runtime, jarvis/ui, apps/desktop ou qa/windows, ou ao preparar/analisar evidência do PC Windows de QA.
---

# jarvis-windows-voice

Esta skill não executa nada no Windows. Na cloud e no CI tudo é simulado; o hardware real só existe no PC de QA autorizado, operado por uma pessoa.

## 1. Onde está cada peça

| Peça | Ficheiro | Contrato a preservar |
|---|---|---|
| Sessão de voz | `jarvis/core/voice_loop.py` | geração por turno, lock de turno, `interrupt`; confirmação ligada a (action_id, digest, ferramenta) |
| Apresentação TTS | `jarvis/voice/presentation.py` | `SPOKEN` / `INTERRUPTED` / `FAILED(stage)` / `NOT_PRESENTED`; pergunta não falada ⇒ sem confirmação |
| PT | `jarvis/language/pt.py` | `classify_control` (sim/não/cancela); vocativo «Jarvis» removido |
| Ferramentas | `jarvis/tools/allowlist.py` | 3 nomes; `ActionStatus`; lançador simulado por omissão |
| Eventos de UI | `jarvis/ui/events.py` | 9 estados, `ALLOWED_TRANSITIONS`, publicação ordenada, `QueueSink` |
| Runtime | `jarvis/runtime/voice_mode.py`, `preflight.py` | `--diagnose` sai com 3 quando BLOCKED; não lança processos |
| Orb | `apps/desktop/orb/` | só `jarvis.ui`; Qt apenas na thread da GUI |
| QA | `qa/windows/` (`Invoke-JarvisPreflight.ps1` read-only, PS 5.1, ASCII; `DEMO_KIT.md`; `ci_expect_diagnose.py`), `qa/benchmarks/latency_summary.py`, `qa/corpus/pt_mz_v1.txt` | sem efeitos colaterais; métricas sem texto |

## 2. Na cloud ou no CI (permitido)

- Alterar código com testes fakes em `tests_vexel/` e `tests_desktop/`, e depois a skill `jarvis-quality-gates`.
- Validar o preflight PowerShell **pelo parser** e pela execução read-only **no runner** do CI. Não há outro Windows disponível.
- `python -m apps.desktop --snapshot DIR` e `--demo --duration N` (offscreen) para o Orb.

## 3. Proibido sem ordem e autorização RIGHTWARE

- Microfone, GPU ou áudio reais.
- Descarregar modelos: Whisper, LLM ou wake word. Os `hey_jarvis` nunca.
- Instalar ou arrancar o Ollama.
- `allow_real_windows_actions = true` ou o lançador real (01D).
- Qualquer instalação ou configuração no PC do Issa.
- Activar ferramentas Windows no Web Lab.
- Publicar áudio, transcrições, `voice-turns.jsonl` real ou relatórios de preflight não revistos (contêm identificadores de máquina).

## 4. QA real (JAR-SLICE-01C) — só no PC de QA autorizado, por uma pessoa

Seguir [`docs/25_JAR-SLICE-01C_WINDOWS_QA_PLAN.md`](../../../docs/25_JAR-SLICE-01C_WINDOWS_QA_PLAN.md) e [`qa/windows/DEMO_KIT.md`](../../../qa/windows/DEMO_KIT.md).

**Ordem dos gates:** G1 → G2 → G3 → G4; G5 e G6 em paralelo; G7 só com `--diagnose` = `PREFLIGHT READY`; depois G8 → G9 → G10.
- A remoção (R1) só se faz com autorização específica.
- Um FAIL pára os gates dependentes.

**Papel do Claude:**
- preparar instruções;
- rever a evidência **sanitizada** que a RIGHTWARE entregar;
- correr `latency_summary.py`, que lê só métricas: G9 exige ≥ 20 amostras, p50 ≤ 4 s e p95 ≤ 8 s;
- registar PASS/FAIL com o SHA.

Sem essa evidência, as capacidades reais continuam «não testadas».

## 5. Depois da 01C (identificado, não iniciado)

- **01E-WIRE:** ligar o Orb ao `VoiceSession` real pelo mesmo `QueueSink`, depois de G7/G8.
- **01D:** lançador real, com evidência de `SUCCEEDED` definida (JAR-SLICE-01D-EVID).
