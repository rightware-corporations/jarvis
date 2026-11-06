# qa/benchmarks/ — medições de desempenho

Scripts de medição do G9 do [plano de QA 01C](../../docs/25_JAR-SLICE-01C_WINDOWS_QA_PLAN.md): latências por fase (`stt_ms`, `think_ms`, `tts_ms` de `voice-turns.jsonl`, p50/p95), memória do modelo (`ollama ps`) e comparação `qwen3.5:4b` vs `qwen3.5:2b`.

Os scripts leem apenas métricas, nunca o texto. Os resultados brutos ficam no PC de QA (`evidence\`, git-ignored); aqui só entram scripts e, depois de revistos, resumos sem dados pessoais.

- [`latency_summary.py`](latency_summary.py): p50/p95/max de `stt_ms`, `think_ms` e `tts_ms`, e o veredicto de aceitação (resposta p50 ≤ 4 s e p95 ≤ 8 s, com ≥ 20 turnos). Lê apenas `outcome`, `intended`, `action_status` e `metrics`; nunca lê `heard` nem `reply`. Exit code 0 = PASS. Testado em `tests_vexel/test_mission02_qa_kit.py`.
