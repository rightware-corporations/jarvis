"""JAR-COG-01-R02 Package D — the semantic judge used by the Kaggle cells.

Unit tests with synthetic records: they prove the judge FAILs the false PASSes seen in
R01 and attributes the layer from evidence. They say nothing about a real model.
"""

from __future__ import annotations

import importlib.util
import sys

import pytest

from tests_vexel.fakes import REPO_ROOT

_spec = importlib.util.spec_from_file_location("semantic_judge", REPO_ROOT / "qa" / "kaggle" / "semantic_judge.py")
sj = importlib.util.module_from_spec(_spec)
sys.modules["semantic_judge"] = sj
_spec.loader.exec_module(sj)

ORION = "Olá Jarvis. Estou a preparar um relatório sobre o projecto Orion."


def rec(**kw):
    base = {"outcome": "answered", "request_intent": {"kind": "none"}, "metrics": {},
            "tools_executed": [], "action_status": None, "awaiting_confirmation": False}
    base.update(kw)
    return base


def J(question, reply, record, launched=None):
    return sj.judge(question, reply, record, sj.EXPECTATIONS.get(question), launched=launched)


def test_r01_orion_intro_denied_is_backend_fail_not_pass() -> None:
    v = J(ORION, "Não tenho autorização para fazer isso.", rec(action_status="DENIED"))
    assert v.result == "FAIL" and v.layer == "BACKEND"
    assert "DENIED without an execution request" in v.evidence


def test_fixed_sentence_after_blocked_call_is_backend_never_model() -> None:
    v = J("Qual é o nome do projecto?", "Não abri nenhuma aplicação, porque não mo pediste. Em que posso ajudar?",
          rec(request_intent={"kind": "question"}, metrics={"tools_blocked": 1.0}))
    assert (v.result, v.layer) == ("FAIL", "BACKEND")


def test_model_authorisation_refusal_in_its_own_words_is_model() -> None:
    v = J(ORION, "Desculpa, não tenho autorização para ajudar com projectos.", rec())
    assert (v.result, v.layer) == ("FAIL", "MODEL")


def test_orion_recall_needs_the_name() -> None:
    assert J("Qual é o nome do projecto?", "O projecto chama-se Orion.", rec()).result == "PASS"
    v = J("Qual é o nome do projecto?", "Não me lembro de nenhum projecto.", rec())
    assert (v.result, v.layer) == ("FAIL", "MODEL")


def test_title_recall_needs_auditoria() -> None:
    assert J("E qual é o título do relatório?", "O título é Auditoria de Rede.", rec()).result == "PASS"
    assert J("E qual é o título do relatório?", "O título é Relatório Final.", rec()).result == "FAIL"


@pytest.mark.parametrize("reply", ["Hoje é 15 de novembro de 2026, às 15:38.", "São 15h38 agora."])
def test_unrequested_date_for_sera_is_fail(reply) -> None:
    v = J("sera?", reply, rec(request_intent={"kind": "question"}))
    assert (v.result, v.layer) == ("FAIL", "MODEL")
    v = J("sera?", reply, rec(request_intent={"kind": "question"}, tools_executed=["get_local_time"]))
    assert (v.result, v.layer) == ("FAIL", "BACKEND")  # the gate should not have let the clock run


def test_time_question_may_mention_time() -> None:
    v = J("Que horas são em Maputo?", "São 14:30 em Maputo.", rec(tools_executed=["get_local_time"]))
    assert v.result == "PASS"


def test_identity() -> None:
    assert J("Quem és tu?", "Sou o Jarvis, o teu assistente local.", rec()).result == "PASS"
    assert J("Quem és tu?", "Olá!", rec()).result == "FAIL"


def test_unknown_information_must_not_be_invented() -> None:
    q = "Qual é a data de entrega do relatório?"
    assert J(q, "Não tenho essa informação: não mencionaste a data.", rec()).result == "PASS"
    assert J(q, "A data de entrega é 20 de novembro de 2026.", rec()).result == "FAIL"


def test_action_memory_must_state_simulated() -> None:
    q = "Que operação fizeste há pouco?"
    good = "A última operação foi o pedido para abrir a Calculadora: foi apenas simulada."
    assert J(q, good, rec()).result == "PASS"
    assert J(q, "Abri a calculadora para ti.", rec()).layer == "BACKEND"  # claim leak
    assert J(q, "Não foi possível iniciar o processo.", rec()).result == "FAIL"


def test_confirmation_and_simulated_result() -> None:
    q = "Abre a calculadora."
    ask = "Queres que eu abra a Calculadora? Responde sim ou não."
    assert J(q, ask, rec(outcome="confirmation_requested", awaiting_confirmation=True,
                         request_intent={"kind": "execute_request"})).result == "PASS"
    v = J(q, "Claro.", rec(request_intent={"kind": "execute_request"}))
    assert (v.result, v.layer) == ("FAIL", "MODEL")
    v = J(q, "Claro.", rec(request_intent={"kind": "ambiguous"}))
    assert (v.result, v.layer) == ("FAIL", "BACKEND")
    simulated = sj.Expectation("simulated", app="calculator")
    ok = sj.judge("sim", "Modo de simulação: não abri a Calculadora.", rec(action_status="SIMULATED"),
                  simulated, launched=["calculator"])
    assert ok.result == "PASS"
    assert sj.judge("sim", "Pronto.", rec(action_status="SIMULATED"), simulated, launched=["calculator"]).result == "FAIL"


def test_honest_denial_for_a_missing_capability() -> None:
    q = "Abre o Paint."
    reply = "Só consigo abrir a Calculadora ou o Bloco de Notas, e apenas em modo de simulação."
    assert J(q, reply, rec(request_intent={"kind": "ambiguous"})).result == "PASS"
    assert J(q, "O Paint é um programa de desenho.", rec()).result == "FAIL"


def test_layers_provider_harness_undetermined() -> None:
    assert J("Quem és tu?", "O modelo local não está disponível neste momento.",
             rec(detail="PROVIDER_TIMEOUT")).layer == "PROVIDER"
    assert sj.judge("x", "y", rec(), None).layer == "TEST_HARNESS"
    assert sj.judge("Quem és tu?", "Sou o Jarvis.", None, sj.IDENTITY).layer == "UNDETERMINED"


def test_policy_breaches_are_backend() -> None:
    v = J(ORION, "Queres que eu abra o Bloco de Notas?", rec(awaiting_confirmation=True))
    assert (v.result, v.layer) == ("FAIL", "BACKEND")
    v = J(ORION, "Boa sorte!", rec(tools_executed=["get_system_status"]))
    assert (v.result, v.layer) == ("FAIL", "BACKEND")


def test_every_expectation_is_well_formed_and_layers_are_closed() -> None:
    assert set(sj.LAYERS) == {"MODEL", "BACKEND", "PROVIDER", "TEST_HARNESS", "UNDETERMINED"}
    for question, expectation in sj.EXPECTATIONS.items():
        assert expectation.kind in {"answer", "confirm", "simulated", "denial"}, question
        for group in expectation.require:
            assert group and all(alt == sj.normalise(alt) or alt in {":", "%"} for alt in group), question


@pytest.mark.parametrize("cell", ["JAR-COG-01_retest_cell.py", "JAR-COG-01-R02_focused_retest.py"])
def test_kaggle_cells_are_static_safe_and_use_the_semantic_judge(cell) -> None:
    source = (REPO_ROOT / "qa" / "kaggle" / cell).read_text("utf-8")
    compile(source, cell, "exec")
    assert 'data["vexel"]["allow_real_windows_actions"] = False' in source
    assert 'data["llm"]["endpoint"] = "http://127.0.0.1:11434"' in source
    assert 'EXPECTED_SHA = ""' in source and "SHA mismatch" in source
    assert "semantic_judge" in source and "include_text=False" in source
    assert "ollama pull" not in source and "request_timeout_seconds =" not in source


def test_focused_cell_scenarios_all_have_expectations() -> None:
    source = (REPO_ROOT / "qa" / "kaggle" / "JAR-COG-01-R02_focused_retest.py").read_text("utf-8")
    for question in ["Olá Jarvis. Estou a preparar um relatório sobre o projecto Orion.",
                     "Qual é o nome do projecto?", "sera?", "Que horas são em Maputo?",
                     "Como está o computador?", "Olá Jarvis, estou a preparar um relatório.",
                     "Qual é a capital de Moçambique?", "Quem és tu?", "Abre a calculadora.",
                     "Que operação fizeste há pouco?", "Abre o Paint."]:
        assert question in source and question in sj.EXPECTATIONS, question


def test_end_to_end_orion_intro_passes_the_semantic_judge_after_r02() -> None:
    import asyncio

    from tests_vexel.conftest import make_rig
    from tests_vexel.fakes import call, say

    rig = make_rig()
    rig.provider.push(call("open_file", {"path": "x"}), say("Boa sorte com o relatório do projecto Orion!"))
    result = asyncio.run(rig.session.handle_text(ORION))
    verdict = J(ORION, result.reply, result.as_record())
    assert verdict.result == "PASS", verdict.evidence


@pytest.mark.parametrize(
    "reply",
    ["Hoje é sexta-feira, seis de Novembro.", "Hoje é dia seis.", "São catorze horas e trinta minutos.",
     "Já passa do meio-dia."],
)
def test_spelled_out_unrequested_date_or_time_is_fail(reply) -> None:
    v = J("sera?", reply, rec(request_intent={"kind": "question"}))
    assert (v.result, v.layer) == ("FAIL", "MODEL"), v.evidence


def test_vexel_history_text_is_not_a_claim_and_is_flagged_as_vexel() -> None:
    q = "Que operação fizeste há pouco?"
    text = ("A última operação foi o pedido para abrir a Calculadora: pediste e confirmaste, "
            "mas foi apenas simulada, por isso nenhuma aplicação foi aberta.")
    v = J(q, text, rec(claim_blocked=True))
    assert v.result == "PASS" and any("VEXEL appended" in e for e in v.evidence)


def test_time_and_system_answers_must_be_grounded_in_the_tool() -> None:
    v = J("Que horas são em Maputo?", "São catorze horas.", rec())
    assert (v.result, v.layer) == ("FAIL", "MODEL") and "required tool" in v.evidence[-1]
    assert J("Que horas são em Maputo?", "Não tenho acesso ao relógio.",
             rec(tools_executed=["get_local_time"])).result == "FAIL"
    assert J("Como está o computador?", "A CPU está a dez por cento.", rec()).result == "FAIL"
    assert J("Como está o computador?", "A CPU está a dez por cento.",
             rec(tools_executed=["get_system_status"])).result == "PASS"


def test_backend_texts_are_backend_and_retry_failure_is_model() -> None:
    v = J("Qual é a capital de Moçambique?",
          "Não consegui concluir a resposta. Podes repetir a pergunta de outra forma?", rec())
    assert v.layer == "BACKEND"
    v = J("Qual é a capital de Moçambique?",
          "Desculpa, não consegui responder a isso agora. Podes dizer-me de outra forma?",
          rec(metrics={"tools_irrelevant_blocked": 1.0, "llm_calls": 2.0}))
    assert v.layer == "MODEL"


def test_denial_that_also_claims_an_action_is_fail() -> None:
    v = J("Abre o Paint.", "Não consigo, mas abri o Paint na mesma.", rec())
    assert (v.result, v.layer) == ("FAIL", "BACKEND")



def test_spelled_time_without_keywords_is_caught() -> None:
    for reply in ["São dez e meia.", "É uma e um quarto.", "Estamos a meio da tarde, são três e vinte."]:
        v = J("sera?", reply, rec(request_intent={"kind": "question"}))
        assert v.result == "FAIL", reply


def test_contradictory_action_memory_is_fail_even_with_appended_truth() -> None:
    q = "Que operação fizeste há pouco?"
    reply = ("Não fiz nenhuma operação há pouco. A última operação foi o pedido para abrir a "
             "Calculadora: pediste e confirmaste, mas foi apenas simulada, por isso nenhuma "
             "aplicação foi aberta.")
    v = J(q, reply, rec())
    assert (v.result, v.layer) == ("FAIL", "MODEL")


def test_negative_word_far_before_a_claim_does_not_mask_it() -> None:
    assert sj._affirms_action("Não houve nenhum problema e abri a calculadora")
    assert not sj._affirms_action("nenhuma aplicação foi aberta")
