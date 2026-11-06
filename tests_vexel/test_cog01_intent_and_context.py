"""JAR-COG-01 — intent safety at the policy boundary and in-session context hygiene.

All simulated: scripted providers play an *adversarial* model that emits
``open_allowed_application`` where the user never asked for it (as the real
qwen3.5:2b did in JAR-INFER-01/B7). Nothing here is evidence about a real model.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from wyzer.models import ChatMessage, NativeFunctionCall, NativeToolCall

from jarvis.brain.pt_provider import SAY_NO_ACTION_REPLY, EffectGate
from jarvis.core.conversation import NOT_EXECUTED_RESULT, settle_and_trim
from jarvis.core.voice_loop import TurnOutcome
from jarvis.language.intent import IntentKind, classify_request
from jarvis.language.prompts import SAY_NOTHING_OPENED
from jarvis.runtime import text_mode
from jarvis.ui.events import VoiceState
from tests_vexel.conftest import make_rig
from tests_vexel.fakes import ScriptedProvider, call, say, slice_config

CALC = {"app": "calculator"}
NOTEPAD = {"app": "notepad"}


def run(rig, text):
    return asyncio.run(rig.session.handle_text(text))


def open_app(arguments, call_id="c1"):
    return call("open_allowed_application", arguments, call_id=call_id)


def awaiting(rig) -> int:
    return rig.sink.states.count(VoiceState.AWAITING_CONFIRMATION)


# ======================================================== A1 classifier matrix


CLASSIFIER_MATRIX = [
    ("Qual é a capital de Moçambique?", IntentKind.QUESTION, ()),
    ("Quem és tu?", IntentKind.QUESTION, ()),
    ("quem es tu jarvis", IntentKind.QUESTION, ()),
    ("Será?", IntentKind.QUESTION, ()),
    ("sera?", IntentKind.QUESTION, ()),
    ("Explica-me o que faz uma calculadora.", IntentKind.QUESTION, ()),
    ("Não abras a calculadora.", IntentKind.NEGATION, ()),
    ("Nunca abras o bloco de notas", IntentKind.NEGATION, ()),
    ("Ontem pedi para abrir a calculadora.", IntentKind.PAST_REFERENCE, ()),
    ("Já abriste a calculadora?", IntentKind.PAST_REFERENCE, ()),
    ("Qual é a diferença entre a Calculadora e o Bloco de Notas?", IntentKind.QUESTION, ()),
    ('Ele disse: "abre a calculadora"', IntentKind.CITATION, ()),
    ("O meu colega disse abre a calculadora", IntentKind.CITATION, ()),
    ("A mensagem diz que deves abrir o bloco de notas", IntentKind.CITATION, ()),
    ("Abre a calculadora.", IntentKind.EXECUTE_REQUEST, ("calculator",)),
    ("Jarvis, podes abrir o Bloco de Notas?", IntentKind.EXECUTE_REQUEST, ("notepad",)),
    ("Por favor, inicia a calculadora.", IntentKind.EXECUTE_REQUEST, ("calculator",)),
    ("abra a calculadora", IntentKind.EXECUTE_REQUEST, ("calculator",)),
    ("abre a calculdora", IntentKind.EXECUTE_REQUEST, ("calculator",)),
    ("abrir calculadora", IntentKind.EXECUTE_REQUEST, ("calculator",)),
    ("jarvis abre o bloco de notas faz favor", IntentKind.EXECUTE_REQUEST, ("notepad",)),
    ("Consegues abrir o bloco de notas?", IntentKind.EXECUTE_REQUEST, ("notepad",)),
    ("quero que abras a calculadora", IntentKind.EXECUTE_REQUEST, ("calculator",)),
    ("Abre a calculadora e o bloco de notas", IntentKind.EXECUTE_REQUEST, ("calculator", "notepad")),
    ("Abre a calculadora mas não abras o bloco de notas", IntentKind.EXECUTE_REQUEST, ("calculator",)),
    ("Abre a calculadora e diz as horas", IntentKind.EXECUTE_REQUEST, ("calculator",)),
    ("a calculadora seria útil", IntentKind.AMBIGUOUS, ()),
    ("preciso de fazer contas", IntentKind.AMBIGUOUS, ()),
    ("abre isso", IntentKind.AMBIGUOUS, ()),
    ("Olá Jarvis.", IntentKind.NONE, ()),
    ("O título do relatório é Auditoria de Rede.", IntentKind.NONE, ()),
    ("sim", IntentKind.NONE, ()),
    ("", IntentKind.NONE, ()),
]


@pytest.mark.parametrize(("text", "kind", "apps"), CLASSIFIER_MATRIX, ids=[c[0][:40] for c in CLASSIFIER_MATRIX])
def test_classifier_matrix(text, kind, apps) -> None:
    verdict = classify_request(text)
    assert verdict.kind is kind
    assert verdict.applications == apps
    # Only EXECUTE_REQUEST can authorise; the record never contains the user's text.
    assert verdict.authorises("calculator") is (kind is IntentKind.EXECUTE_REQUEST and "calculator" in apps)
    assert text.strip() == "" or text not in json.dumps(verdict.as_record(), ensure_ascii=False)


def test_classifier_respects_configured_allowlist_and_fails_closed(monkeypatch) -> None:
    assert classify_request("Abre o bloco de notas", ("calculator",)).kind is not IntentKind.EXECUTE_REQUEST
    import jarvis.language.intent as intent

    def boom(*args, **kwargs):
        raise RuntimeError("internal")

    monkeypatch.setattr(intent, "_classify", boom)
    verdict = intent.classify_request("Abre a calculadora")
    assert verdict.kind is IntentKind.NONE and verdict.reasons == ("classifier_error",)


# ====================================== A2 policy boundary (adversarial model)


@pytest.mark.parametrize(
    ("text", "model_text"),
    [
        ("Qual é a capital de Moçambique?", "A capital de Moçambique é Maputo."),
        ("Quem és tu?", "Sou o Jarvis, o teu assistente."),
        ("sera?", "Talvez. Podes explicar melhor?"),
        ("Explica-me o que faz uma calculadora.", "Uma calculadora faz contas."),
        ("Não abras a calculadora.", "Está bem, não abro."),
        ("Ontem pedi para abrir a calculadora.", "Lembro-me de que falaste nisso."),
        ("Qual é a diferença entre a Calculadora e o Bloco de Notas?", "Uma calcula, o outro escreve."),
        ('Ele disse: "abre a calculadora"', "Percebo o que ele disse."),
    ],
)
def test_unrequested_effectful_call_is_blocked_and_answered_in_text(text, model_text) -> None:
    rig = make_rig()
    rig.provider.push(open_app(CALC), say(model_text))  # model opens; the retry has no tools
    result = run(rig, text)
    assert result.outcome is TurnOutcome.ANSWERED and not result.awaiting_confirmation
    assert result.reply == model_text and rig.pending is None
    assert rig.launcher.requested == [] and awaiting(rig) == 0
    assert result.metrics["tools_blocked"] == 1.0
    assert rig.provider.requests[1][1] == []  # the text-only retry offers no tool at all


def test_b7_replay_time_tool_then_unrequested_notepad() -> None:
    """B7: get_local_time, then open_allowed_application(notepad). When the clock is
    relevant it runs, but it never chains into an action the user did not ask for."""
    rig = make_rig()
    rig.provider.push(
        call("get_local_time", call_id="t1"),
        open_app(NOTEPAD, "c2"),
        say("São catorze e trinta, e a capital é Maputo."),
    )
    result = run(rig, "Que horas são, e qual é a capital de Moçambique?")
    assert result.outcome is TurnOutcome.ANSWERED
    assert result.reply == "São catorze e trinta, e a capital é Maputo."
    assert rig.pending is None and rig.launcher.requested == [] and awaiting(rig) == 0
    assert result.tools_executed == ["get_local_time"]  # read-only never chains into an action
    assert result.metrics["tools_blocked"] == 1.0
    assert result.request_intent["kind"] == "question"


def test_b7_irrelevant_clock_is_not_consulted() -> None:
    """JAR-COG-01-R02: for a question that needs no time, the clock is not even consulted."""
    rig = make_rig()
    rig.provider.push(call("get_local_time", call_id="t1"), say("A capital de Moçambique é Maputo."))
    result = run(rig, "Qual é a capital de Moçambique?")
    assert result.reply == "A capital de Moçambique é Maputo."
    assert result.tools_executed == [] and result.metrics["tools_irrelevant_blocked"] == 1.0
    assert result.tools_rejected == ["get_local_time:DROPPED_BY_GATE"]
    assert rig.probe.reads == 0

def test_model_switching_application_is_blocked() -> None:
    rig = make_rig()
    rig.provider.push(open_app(NOTEPAD), say("Posso abrir a calculadora, se quiseres."))
    result = run(rig, "Abre a calculadora")
    assert result.outcome is TurnOutcome.ANSWERED and rig.pending is None
    assert rig.launcher.requested == []


def test_switch_in_continuation_after_confirmation_is_blocked() -> None:
    rig = make_rig()
    rig.provider.push(open_app(CALC), open_app(NOTEPAD, "c2"), say("Pronto."))
    assert run(rig, "Abre a calculadora").awaiting_confirmation
    done = run(rig, "sim")
    assert done.outcome is TurnOutcome.CONFIRMED and done.action_status == "SIMULATED"
    assert rig.launcher.requested == ["calculator"] and rig.pending is None and awaiting(rig) == 1


def test_two_requested_applications_get_independent_confirmations() -> None:
    rig = make_rig()
    rig.provider.push(open_app(CALC), open_app(NOTEPAD, "c2"), say("Feito."))
    first = run(rig, "Abre a calculadora e o bloco de notas")
    assert first.awaiting_confirmation and rig.pending.arguments == CALC
    second = run(rig, "sim")
    assert second.awaiting_confirmation and rig.pending.arguments == NOTEPAD
    assert rig.launcher.requested == ["calculator"]  # notepad not approved by the first "sim"
    assert run(rig, "não").outcome is TurnOutcome.REJECTED
    assert rig.launcher.requested == ["calculator"]


@pytest.mark.parametrize(
    "text",
    ["Abre a calculadora.", "Por favor, inicia a calculadora.", "abra a calculdora", "Podes abrir a calculadora?"],
)
def test_explicit_requests_still_need_confirmation(text) -> None:
    rig = make_rig()
    rig.provider.push(open_app(CALC), say("Pronto."))
    asked = run(rig, text)
    assert asked.outcome is TurnOutcome.CONFIRMATION_REQUESTED and rig.launcher.requested == []
    assert run(rig, "sim").action_status == "SIMULATED"
    assert rig.launcher.requested == ["calculator"]


@pytest.mark.parametrize("text", ["a calculadora seria útil", "preciso de fazer contas"])
def test_ambiguous_request_gets_clarification_not_confirmation(text) -> None:
    rig = make_rig()
    rig.provider.push(open_app(CALC))
    result = run(rig, text)
    assert result.outcome is TurnOutcome.ANSWERED and not result.awaiting_confirmation
    assert result.reply.startswith("Não tenho a certeza se queres que eu abra a Calculadora.")
    assert rig.pending is None and awaiting(rig) == 0
    assert run(rig, "sim").outcome is TurnOutcome.NOTHING_TO_CONFIRM
    assert rig.launcher.requested == []


def test_gate_without_authorization_blocks_everything_and_errors_fail_closed(monkeypatch) -> None:
    gate = EffectGate()
    tool_call = NativeToolCall(id="x", function=NativeFunctionCall(name="open_allowed_application", arguments=CALC))
    kept, blocked = gate.split([tool_call])
    assert kept == [] and blocked == [tool_call]  # default authorization is NO_REQUEST

    rig = make_rig()
    monkeypatch.setattr(rig.parts.provider.gate, "split", lambda calls: (_ for _ in ()).throw(RuntimeError()))
    rig.provider.push(open_app(CALC), say("Não consegui."))
    result = run(rig, "Abre a calculadora")
    assert not result.awaiting_confirmation and rig.pending is None and rig.launcher.requested == []


def test_text_only_retry_that_still_returns_tools_falls_back_to_fixed_reply() -> None:
    rig = make_rig()
    rig.provider.push(open_app(CALC), open_app(CALC, "c2"))
    result = run(rig, "Qual é a capital de Moçambique?")
    assert result.reply == SAY_NO_ACTION_REPLY and rig.launcher.requested == []


def test_authorization_is_closed_after_every_turn() -> None:
    rig = make_rig()
    rig.provider.push(say("Olá."))
    run(rig, "Abre a calculadora")
    assert rig.parts.provider.gate.authorization.kind is IntentKind.NONE
    rig.provider.push(open_app(CALC), say("Não."))
    run(rig, "E agora?")  # a later turn does not inherit the earlier request
    assert rig.launcher.requested == [] and rig.pending is None


# ===================================================== A4 truth about actions


def test_identity_answer_is_not_replaced_by_a_no_action_template() -> None:
    rig = make_rig()
    rig.provider.push(say("Sou o Jarvis, um assistente local em português."))
    result = run(rig, "quem es tu")
    assert result.reply == "Sou o Jarvis, um assistente local em português."
    assert not result.claim_blocked and SAY_NOTHING_OPENED not in result.reply


def test_false_claim_sentence_is_removed_and_the_rest_kept() -> None:
    rig = make_rig()
    rig.provider.push(say("Sou o Jarvis. Abri a calculadora para ti."))
    result = run(rig, "quem es tu jarvis")
    assert result.claim_blocked and result.reply == "Sou o Jarvis."


def test_reply_made_only_of_a_false_claim_becomes_the_truth() -> None:
    rig = make_rig()
    rig.provider.push(say("Abri a calculadora."))
    result = run(rig, "Abre a calculadora")
    assert result.claim_blocked and result.reply == SAY_NOTHING_OPENED


# ===================================================== B3 context hygiene


def _messages_sent(rig, request: int = -1) -> list[ChatMessage]:
    return rig.provider.requests[request][0][1:]  # without the system prompt


@pytest.mark.parametrize("answer", ["não", "talvez", "cancela"])
def test_refused_confirmation_is_settled_before_the_next_request(answer) -> None:
    rig = make_rig()
    rig.provider.push(open_app(NOTEPAD), say("Maputo."))
    run(rig, "Abre o bloco de notas")
    run(rig, answer)
    result = run(rig, "Qual é a capital de Moçambique?")
    sent = _messages_sent(rig)
    roles = [m.role for m in sent]
    assert roles == ["user", "assistant", "tool", "user"]
    assert sent[2].content == NOT_EXECUTED_RESULT and sent[2].name == "open_allowed_application"
    assert result.metrics["context_settled"] == 1.0 and rig.launcher.requested == []


def test_dropped_repeat_is_settled_and_confirmed_call_keeps_its_real_result() -> None:
    rig = make_rig()
    rig.provider.push(open_app(CALC), open_app(CALC, "c2"), say("Maputo."))
    run(rig, "Abre a calculadora")
    run(rig, "sim")
    run(rig, "Qual é a capital de Moçambique?")
    tools = [m for m in _messages_sent(rig) if m.role == "tool"]
    assert [json.loads(m.content)["ok"] for m in tools] == [True, False]  # real, then NOT_EXECUTED


def test_settle_and_trim_drops_orphans_and_cuts_at_user_boundaries() -> None:
    orphan = ChatMessage(role="tool", name="get_local_time", content="{}")
    history = [orphan]
    for i in range(30):
        history += [ChatMessage(role="user", content=f"pergunta {i} " + "x" * 200),
                    ChatMessage(role="assistant", content=f"resposta {i} " + "y" * 200)]
    cleaned, counts = settle_and_trim(history, max_characters=2_000)
    assert cleaned[0].role == "user" and counts["context_orphans"] == 1
    assert counts["context_dropped"] > 0 and counts["context_messages"] == len(cleaned)
    assert cleaned[-1].content.startswith("resposta 29")
    assert sum(len(m.content or "") for m in cleaned) <= 2_000


def test_trim_always_keeps_the_last_user_message() -> None:
    huge = [ChatMessage(role="user", content="z" * 50_000)]
    cleaned, _ = settle_and_trim(huge, max_characters=100)
    assert cleaned == huge


# ======================================== B1/B2 session identity and logs


class Console:
    def __init__(self, lines):
        self.lines = list(lines)
        self.written = []

    def read_line(self):
        return self.lines.pop(0) if self.lines else None

    def write(self, text):
        self.written.append(text)


def test_text_mode_new_conversation_has_new_identity_and_clean_context(tmp_path: Path) -> None:
    providers = [ScriptedProvider([say("Anotado."), say("Orion.")]), ScriptedProvider([say("Não sei.")])]
    console = Console(["O projecto chama-se Orion.", "Qual é o projecto?", "nova conversa", "Qual é o projecto?", "sair"])
    deps = text_mode.TextRuntimeDeps(
        provider_factory=lambda _config: providers.pop(0), console=console, log_directory=tmp_path
    )
    result = asyncio.run(text_mode.run_text_mode(slice_config(), deps))

    first, second = result.sessions
    assert first != second
    assert [t["session_id"] for t in result.turns] == [first, first, second]
    assert [t["turn_index"] for t in result.turns] == [1, 2, 1]
    # The new conversation never sees the old one.
    new_provider_users = [m.content for m in deps_last_requests(result, second)]
    assert new_provider_users == ["Qual é o projecto?"]
    events = [json.loads(line) for line in (tmp_path / "text-sessions.jsonl").read_text("utf-8").splitlines()]
    assert [(e["event"], e["reason"]) for e in events] == [
        ("session_start", "process_start"),
        ("session_end", "user_restart"),
        ("session_start", "user_restart"),
        ("session_end", "user_quit"),
    ]
    log = (tmp_path / "text-turns.jsonl").read_text("utf-8")
    assert "Orion" not in log and "projecto" not in log  # no conversation text by default
    record = json.loads(log.splitlines()[0])
    assert {"session_id", "turn_index", "request_intent", "tools_executed"} <= set(record)
    assert "context_messages" in record["metrics"] and "llm_calls" in record["metrics"]


_LAST_REQUESTS: dict[str, list] = {}


def deps_last_requests(result, session_id):
    return _LAST_REQUESTS.get(session_id, [])


@pytest.fixture(autouse=True)
def _capture_requests(monkeypatch):
    """Record, per session, the user messages each provider received."""
    original = ScriptedProvider.chat

    async def chat(self, messages, tools, settings=None):
        _LAST_REQUESTS[getattr(self, "_session_tag", "")] = [m for m in messages if m.role == "user"]
        return await original(self, messages, tools, settings)

    monkeypatch.setattr(ScriptedProvider, "chat", chat)
    from jarvis.core import assistant

    real_build = assistant.build_voice_session

    def build(config, provider, **kwargs):
        session, parts = real_build(config, provider, **kwargs)
        provider._session_tag = session.session_id
        return session, parts

    monkeypatch.setattr(assistant, "build_voice_session", build)
    yield
    _LAST_REQUESTS.clear()


def test_two_sessions_never_share_state() -> None:
    one, two = make_rig(), make_rig()
    one.provider.push(open_app(CALC))
    run(one, "Abre a calculadora")
    two.provider.push(say("Nada pendente."))
    assert run(two, "sim").outcome is TurnOutcome.NOTHING_TO_CONFIRM
    assert one.session.session_id != two.session.session_id
    assert two.launcher.requested == [] and one.pending is not None


def test_cancel_in_flight_closes_authorization() -> None:
    rig = make_rig(delay=0.5)
    rig.provider.push(open_app(CALC))

    async def scenario():
        task = asyncio.create_task(rig.session.handle_text("Abre a calculadora"))
        await rig.provider.started.wait()
        rig.session.cancel(reason="test")
        return await task

    result = asyncio.run(scenario())
    assert result.outcome is TurnOutcome.DISCARDED and rig.pending is None
    assert rig.parts.provider.gate.authorization.kind is IntentKind.NONE
    assert rig.launcher.requested == []



@pytest.mark.parametrize(
    "arguments",
    [{"app": "cmd"}, {"app": "calculator", "path": "x"}, {"app": "Calculator"}, {}, {"app": ["calculator"]}],
    ids=["other_app", "extra_arg", "wrong_case", "missing", "list"],
)
def test_any_effectful_call_without_request_is_blocked_before_wyzer(arguments) -> None:
    rig = make_rig()
    rig.provider.push(open_app(arguments), say("A capital é Maputo."))
    result = run(rig, "Qual é a capital de Moçambique?")
    assert result.reply == "A capital é Maputo." and result.action_status is None
    assert not result.awaiting_confirmation and rig.launcher.requested == []
    assert result.metrics["tools_blocked"] == 1.0


@pytest.mark.parametrize(
    ("model_text"),
    ["Vou abrir o Bloco de Notas para ti.", "Queres que eu abra o Bloco de Notas? Responde sim ou não."],
)
def test_text_sent_with_a_blocked_call_is_discarded(model_text) -> None:
    rig = make_rig()
    template = open_app(NOTEPAD)
    blocked = template.model_copy(
        update={"message": template.message.model_copy(update={"content": model_text})}
    )
    rig.provider.push(blocked, say("A capital é Maputo."))
    result = run(rig, "Qual é a capital de Moçambique?")
    assert result.reply == "A capital é Maputo." and model_text not in rig.tts.spoken


def test_non_configured_application_on_a_question_never_asks_confirmation() -> None:
    rig = make_rig(allowed=("calculator",))
    rig.provider.push(open_app(NOTEPAD), say("Maputo."))
    result = run(rig, "Qual é a capital de Moçambique?")
    assert not result.awaiting_confirmation and rig.pending is None and awaiting(rig) == 0


@pytest.mark.parametrize(
    "reply",
    ["Não, abri a calculadora.", "Claro que não demorei: abri a calculadora.", "Pronto! Abri a calculadora."],
)
def test_negation_in_another_clause_does_not_hide_a_false_claim(reply) -> None:
    rig = make_rig()
    rig.provider.push(say(reply))
    result = run(rig, "Abriste a calculadora?")
    assert result.claim_blocked and result.reply == SAY_NOTHING_OPENED


@pytest.mark.parametrize(
    "text",
    [
        "abre a calculadora? não", "abre a calculadora nem pensar", "abre calculadora não",
        "consegues abrir a calculadora? não, deixa", "abrir a calculadora é fácil",
        "vamos supor que abres a calculadora", "abres a calculadora", "tu abres a calculadora",
        "inicia a conversa sobre a calculadora", "abre o jogo sobre a calculadora",
        "abria a calculadora", "abriria a calculadora", "abraça a calculadora",
    ],
)
def test_review_counterexamples_never_authorise(text) -> None:
    assert classify_request(text).kind is not IntentKind.EXECUTE_REQUEST


@pytest.mark.parametrize("separator", [", ", " – ", " — ", "-", "\n", ". ", "! ", ": ", " (", "; ", " / ", " … ", "_"])
def test_any_separator_between_negation_and_claim_keeps_the_claim(separator) -> None:
    from jarvis.language.prompts import claims_action

    assert claims_action(f"Não{separator}abri a calculadora para ti.")
    assert not claims_action("Não abri nenhuma aplicação.")


@pytest.mark.parametrize(
    "text",
    [
        "abrir a calculadora e facil", "abrir a calculadora custa",
        "quero saber se podes abrir a calculadora", "podes abrir a calculadora se eu pedir",
        "abre a calculadora, mentira", "abre a calculadora estou a brincar",
        "abre a calculadora amanhã", "abre a calculadora daqui a pouco",
    ],
)
def test_second_review_counterexamples_never_authorise(text) -> None:
    assert classify_request(text).kind is not IntentKind.EXECUTE_REQUEST
