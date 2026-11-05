# qa/benchmarks/ — medições de desempenho

Lugar para os scripts de medição do G9 do [plano de QA 01C](../../docs/25_JAR-SLICE-01C_WINDOWS_QA_PLAN.md): latências por fase (`stt_ms`, `think_ms`, `tts_ms` de `voice-turns.jsonl`, p50/p95), memória do modelo (`ollama ps`) e comparação `qwen3.5:4b` vs `qwen3.5:2b`.

Os scripts leem apenas métricas, nunca o texto. Os resultados brutos ficam no PC de QA (`evidence\`, git-ignored); aqui só entram scripts e, depois de revistos, resumos sem dados pessoais.
