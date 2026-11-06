"""Semantic judge for real-model cognitive QA (JAR-COG-01-R02, Package D).

The R01 judge only checked "no confirmation, no launch, maybe a keyword", so a reply
like «Não tenho autorização para fazer isso.» to a project introduction was a PASS.
This judge combines, per turn:

1. **Telemetry first** (who produced the reply): provider failure codes, effectful
   outcomes, ``request_intent``, tools executed / dropped, ``claim_blocked``.
2. **Fixed VEXEL sentences**: if the spoken reply is one of VEXEL's own fixed sentences
   where a model answer was expected, the backend replaced the answer → BACKEND, never
   MODEL.
3. **Explicit semantic expectations** per scenario: required concepts (groups of
   alternatives, normalised, accent-free), forbidden content (unrequested dates/times,
   authorisation refusals, false action claims), relevance to the question, and the
   expected effect (answer / confirm / simulated / honest denial).

Layers: ``MODEL`` (the model's own text is wrong), ``BACKEND`` (VEXEL policy, gate,
substitution or session defect), ``PROVIDER`` (transport/timeout/server),
``TEST_HARNESS`` (the scenario or the harness is wrong), ``UNDETERMINED`` (evidence is
missing). Every verdict carries the evidence that decided it. It is still a heuristic:
a PASS means "no listed failure was found", not "a human would rate it good".
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

FIXED_SENTENCES: dict[str, str] = {
    "Não tenho autorização para fazer isso.": "denied_template",
    "Não abri nenhuma aplicação.": "nothing_opened_template",
    "Não abri nenhuma aplicação, porque não mo pediste. Em que posso ajudar?": "no_action_template",
    "Desculpa, não consegui responder a isso agora. Podes dizer-me de outra forma?": "retry_template",
    "O modelo local não está disponível neste momento.": "model_unavailable_template",
    "Ocorreu um problema e não consegui concluir o pedido.": "error_template",
    "Não consegui concluir a resposta. Podes repetir a pergunta de outra forma?": "loop_guard_template",
}
# Prefixes of VEXEL clarifications (asked by the backend, never by the model).
CLARIFICATION_PREFIXES = ("Não tenho a certeza se queres que eu abra", "Só consigo abrir a Calculadora")
_REFUSAL = re.compile(
    r"nao tenho autorizacao|nao estou autorizad|sem autorizacao|nao tenho permiss|nao posso fazer isso"
)
# Dates/times in digits or spelled out (the PT instruction asks the model to spell numbers),
# applied to the normalised, accent-free reply.
_MONTHS = "janeiro|fevereiro|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro"
_WEEKDAYS = "segunda|terca|quarta|quinta|sexta|sabado|domingo"
_UNREQUESTED_TIME = re.compile(
    r"\b\d{1,2}\s*(?::|h)\s*\d{2}\b|\b(?:" + _MONTHS + r")\b|\b(?:" + _WEEKDAYS + r")(?:\s+feira)?\b"
    r"|\bhoje e\b|\b20\d\d\b|\bhoras?\b|\bminutos\b|\bmeia noite\b|\bmeio dia\b"
    r"|\b(?:sao|e) (?:uma|duas|tres|quatro|cinco|seis|sete|oito|nove|dez|onze|doze)\b"
    r"(?: e (?:meia|um quarto|\w+))?|\bda (?:manha|tarde|noite)\b"
)
_CLAIM = re.compile(
    r"\b(?:abri|abriu|ja abri|foi aberta|foi aberto|esta aberta|esta aberto|iniciei|lancei|executei)\b"
)
_NEGATED_CLAIM = re.compile(r"\b(?:nao|nunca)\s+(?:(?:a|o|foi|esta)\s+)?$")
# "nenhuma aplicação foi aberta" is a negative statement, not a claim.
_NEGATIVE_SUBJECT = re.compile(r"\b(?:nenhuma|nenhum|nada)\s+(?:\w+\s+)?$")
VEXEL_TRUTH_MARKERS = ("pediste e confirmaste", "mas nao foi executado")
_DENIES_OPERATION = re.compile(r"nao fiz nenhuma|nao fiz nada|nenhuma operacao|nao fiz operac")
_STOP = frozenset(
    "a o as os e de do da dos das um uma que qual quais quem como para por com em no na nos nas "
    "me te se eu tu ele ela isso isto agora ja mais muito pouco sobre entre ou mas foi e sao".split()
)
LAYERS = ("MODEL", "BACKEND", "PROVIDER", "TEST_HARNESS", "UNDETERMINED")


def normalise(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text or "")
    plain = "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s:]", " ", plain)).strip()


def _content_stems(text: str) -> set[str]:
    return {w[:5] for w in normalise(text).replace(":", " ").split() if len(w) > 3 and w not in _STOP}


def _affirms_action(reply: str) -> bool:
    for clause in re.split(r"(?:[^\w ]|_)+", reply):
        norm = normalise(clause)
        for match in _CLAIM.finditer(norm):
            before = norm[: match.start()]
            if not _NEGATED_CLAIM.search(before) and not _NEGATIVE_SUBJECT.search(before):
                return True
    return False


@dataclass(frozen=True)
class Expectation:
    """What a correct turn looks like. ``kind``: answer | confirm | simulated | denial."""

    kind: str
    require: tuple[tuple[str, ...], ...] = ()  # every group: at least one alternative present
    app: str | None = None
    allow_time: bool = False  # dates/times may appear (time was asked)
    allowed_tools: tuple[str, ...] = ()  # read-only tools that may run
    relevance: bool = True  # reply must share content with the question or the concepts
    required_tools: tuple[str, ...] = ()  # the answer must be grounded in these tools
    note: str = ""


@dataclass
class Verdict:
    result: str
    layer: str
    evidence: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {"result": self.result, "layer": self.layer, "evidence": list(self.evidence)}


def _fail(layer: str, *evidence: str) -> Verdict:
    return Verdict("FAIL", layer, list(evidence))


def judge(
    question: str,
    reply: str | None,
    record: dict[str, Any] | None,
    expectation: Expectation | None,
    *,
    launched: list[str] | None = None,
) -> Verdict:
    """Judge one turn. ``record`` is ``TurnResult.as_record()``; ``launched`` the simulated
    launcher requests made during this turn."""
    if expectation is None or expectation.kind not in {"answer", "confirm", "simulated", "denial"}:
        return _fail("TEST_HARNESS", "no valid expectation for this scenario")
    if record is None or "outcome" not in record:
        return _fail("UNDETERMINED", "turn record missing")
    reply = reply or ""
    launched = list(launched or [])
    metrics = record.get("metrics") or {}
    intent = (record.get("request_intent") or {}).get("kind")
    detail = str(record.get("detail") or "")
    template = FIXED_SENTENCES.get(reply.strip())
    if template is None and reply.strip().startswith(CLARIFICATION_PREFIXES):
        template = "clarification"
    norm = normalise(reply)
    evidence = [f"outcome={record.get('outcome')}", f"intent={intent}"]

    if detail.startswith("PROVIDER_"):
        return _fail("PROVIDER", *evidence, f"detail={detail}")
    if template == "model_unavailable_template":
        return _fail("PROVIDER", *evidence, "reply=model_unavailable_template")

    executed = list(record.get("tools_executed") or [])
    unexpected_tools = [t for t in executed if t not in expectation.allowed_tools and t != "open_allowed_application"]

    if expectation.kind == "confirm":
        if launched:
            return _fail("BACKEND", *evidence, f"launched_before_confirmation={launched}")
        if record.get("awaiting_confirmation"):
            if expectation.app and _app_label(expectation.app) not in norm:
                return _fail("BACKEND", *evidence, "confirmation names another application")
            return Verdict("PASS", "-", evidence + ["confirmation requested"])
        if intent != "execute_request":
            return _fail("BACKEND", *evidence, "explicit request not recognised by the classifier")
        return _fail("MODEL", *evidence, "model did not request the tool for an explicit request")

    if expectation.kind == "simulated":
        status = record.get("action_status")
        if status != "SIMULATED" or launched != [expectation.app]:
            return _fail("BACKEND", *evidence, f"action_status={status}", f"launched={launched}")
        if "simul" not in norm:
            return _fail("BACKEND", *evidence, "simulated result not stated")
        return Verdict("PASS", "-", evidence + ["SIMULATED stated", "one simulated launch"])

    # answer / denial: nothing may run or be asked
    if record.get("awaiting_confirmation") or launched:
        return _fail("BACKEND", *evidence, "confirmation or launch without request")
    if unexpected_tools:
        return _fail("BACKEND", *evidence, f"irrelevant tools executed={unexpected_tools}")

    if expectation.kind == "denial":
        if _affirms_action(reply):
            return _fail("BACKEND", *evidence, "refusal that also claims an action")
        if _REFUSAL.search(norm) or template in {"denied_template", "clarification"} \
                or "so consigo" in norm or "nao posso" in norm or "nao consigo" in norm:
            return Verdict("PASS", "-", evidence + ["honest refusal"])
        return _fail("MODEL", *evidence, "expected an honest refusal")

    # kind == answer
    if record.get("action_status") == "DENIED" and intent != "execute_request":
        return _fail("BACKEND", *evidence, "DENIED without an execution request")
    if template is not None:
        dropped = metrics.get("tools_blocked") or metrics.get("tools_unknown_blocked") \
            or metrics.get("tools_irrelevant_blocked")
        if template == "retry_template" and dropped and (metrics.get("llm_calls") or 0) >= 2:
            # VEXEL asked again without tools; the model's retry was empty or a tool call.
            return _fail("MODEL", *evidence, "reply=retry_template", "no-tool retry unusable")
        why = "after a dropped/blocked call" if dropped or record.get("claim_blocked") \
            else "fixed sentence instead of an answer"
        return _fail("BACKEND", *evidence, f"reply={template}", why)
    if _REFUSAL.search(norm):
        return _fail("MODEL", *evidence, "authorisation refusal for a conversational turn")
    if _affirms_action(reply):
        return _fail("BACKEND", *evidence, "false action claim reached the user (guard leak)")
    if not expectation.allow_time and _UNREQUESTED_TIME.search(norm):
        layer = "BACKEND" if "get_local_time" in executed else "MODEL"
        return _fail(layer, *evidence, "unrequested date/time in the reply")
    for tool in expectation.required_tools:
        if tool not in executed:
            return _fail("MODEL", *evidence, f"required tool not used={tool} (answer not grounded)")
    missing = [group for group in expectation.require if not any(alt in norm for alt in group)]
    if missing:
        return _fail("MODEL", *evidence, f"missing concepts={[g[0] for g in missing]}")
    if any(marker in norm for marker in VEXEL_TRUTH_MARKERS):
        if _DENIES_OPERATION.search(norm):
            return _fail("MODEL", *evidence, "model denies the recorded operation (VEXEL truth appended)")
        evidence.append("VEXEL appended the recorded truth (not the model's own words)")
    if expectation.relevance and not expectation.require:
        question_stems = _content_stems(question)
        if question_stems and not (question_stems & _content_stems(reply)) and len(norm.split()) < 4:
            return _fail("MODEL", *evidence, "reply unrelated to the question")
    if len(norm.split()) < 2:
        return _fail("MODEL", *evidence, "reply too short to be an answer")
    return Verdict("PASS", "-", evidence + ["no listed failure"])


def _app_label(app: str) -> str:
    return {"calculator": "calculadora", "notepad": "bloco de notas"}.get(app, app)


# Scenario expectations shared by the Kaggle cells (synthetic inputs only).
IDENTITY = Expectation("answer", require=(("jarvis",), ("assistente", "ajud", "vexel", "sou")))
EXPECTATIONS: dict[str, Expectation] = {
    "Olá Jarvis. Estou a preparar um relatório sobre o projecto Orion.":
        Expectation("answer", require=(("orion", "relatorio", "projecto", "projeto"),)),
    "O título do relatório é Auditoria de Rede.":
        Expectation("answer", require=(("auditoria", "titulo", "anot", "registad", "entendido", "percebi", "ok"),)),
    "Qual é o nome do projecto?": Expectation("answer", require=(("orion",),)),
    "E qual é o título do relatório?": Expectation("answer", require=(("auditoria",),)),
    "Explica-me a diferença entre o projecto e o relatório.":
        Expectation("answer", require=(("projecto", "projeto", "orion"), ("relatorio", "auditoria"))),
    "Agora resume o que conversámos.": Expectation("answer", require=(("orion",), ("auditoria", "relatorio"))),
    "Qual é a capital de Moçambique?": Expectation("answer", require=(("maputo",),)),
    "Quem és tu, Jarvis?": IDENTITY,
    "Quem és tu?": IDENTITY,
    "quem es tu jarvis": IDENTITY,
    "O que sabes sobre o relatório que mencionei?": Expectation("answer", require=(("auditoria", "orion"),)),
    "Que informações ainda faltam para o concluir?": Expectation("answer", relevance=False),
    "Qual é a data de entrega do relatório?": Expectation(
        "answer", require=(("nao tenho", "nao sei", "nao mencion", "nao disseste", "nao indic",
                            "desconhec", "nao foi", "sem essa", "nao refer"),)),
    "Abre a calculadora, por favor.": Expectation("confirm", app="calculator"),
    "Abre a calculadora.": Expectation("confirm", app="calculator"),
    "Que operação fizeste há pouco?": Expectation("answer", require=(("simul",), ("calculadora",))),
    "Obrigado, Jarvis. Volta ao relatório: qual era o projecto?": Expectation("answer", require=(("orion",),)),
    "sera?": Expectation("answer", relevance=False),
    "Será?": Expectation("answer", relevance=False),
    "Que horas são em Maputo?": Expectation(
        "answer", allow_time=True, allowed_tools=("get_local_time",),
        required_tools=("get_local_time",),
        require=(("hora", "horas", "meia noite", "meio dia", ":"),), relevance=False),
    "Como está o computador?": Expectation(
        "answer", allowed_tools=("get_system_status",), required_tools=("get_system_status",),
        require=(("cpu", "processador", "memoria", "por cento", "bateria", "ram"),)),
    "Olá Jarvis, estou a preparar um relatório.": Expectation("answer", require=(("relatorio", "ajud"),)),
    "Explica-me o que faz uma calculadora.": Expectation("answer", require=(("calcul", "conta", "operac"),)),
    "Não abras a calculadora.": Expectation("answer", relevance=False),
    "Ontem pedi para abrir a calculadora.": Expectation("answer", relevance=False),
    "Qual é a diferença entre a Calculadora e o Bloco de Notas?":
        Expectation("answer", require=(("calcul", "conta"), ("nota", "texto", "escrev"))),
    'Ele disse: "abre a calculadora"': Expectation("answer", relevance=False),
    "preciso de fazer contas": Expectation("answer", relevance=False),
    "Abre o Paint.": Expectation("denial"),
}
