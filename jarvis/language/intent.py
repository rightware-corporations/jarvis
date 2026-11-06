"""Request intent for effectful tools (JAR-COG-01, Package A).

A tool call produced by the language model is **not** evidence that the user asked
for that action. Opening an application needs a sufficiently explicit execution request
*from the user's own utterance*, naming an allowlisted application. This module turns
that utterance into an ``IntentVerdict``; ``jarvis.brain.pt_provider`` enforces it on
every model response, after the model and before Wyzer can confirm or execute.

How the verdict is built (no single regex decides):

1. Normalise (lower case, no accents, punctuation removed) and drop the vocative and
   politeness markers (``por favor``, ``faz favor``, ``se faz favor``).
2. Split into clauses on ``,``/``;``/``e``/``mas``/``depois``; a clause that names an
   application without a verb inherits the verb of the previous clause
   ("abre a calculadora e o bloco de notas").
3. Per clause, resolve application mentions against the allowlist (exact phrases and
   bounded-edit typos such as "calculdora"), find an execution verb (imperative,
   infinitive or subjunctive of abrir/iniciar/lançar/arrancar/executar/ligar, with
   typo tolerance), and the frame around it: imperative at the start, capability
   question ("podes/pode/consegues/podias abrir …?"), desire frame ("quero que
   abras …"), negation before the verb, past-tense markers, reported speech/quotes.
4. Combine: any clause with reported speech → ``CITATION``; an execution clause that
   is negated → ``NEGATION``; past markers → ``PAST_REFERENCE``; an execution verb in
   a request frame with a resolved application → ``EXECUTE_REQUEST`` for exactly those
   applications; an application or an application hint ("fazer contas") without a
   request frame → ``AMBIGUOUS``; an interrogative without request → ``QUESTION``;
   otherwise ``NONE``.

Limitations (documented, not hidden):

* It is a closed, conservative grammar for a two-application allowlist, not semantic
  understanding. Unusual phrasings of a genuine request fall to ``AMBIGUOUS`` (the
  user is asked to rephrase) — the safe direction. It never upgrades doubt to
  execution.
* It reads only the user's own utterance: model text, tool results and earlier turns
  never authorise anything. A request made in an earlier turn must be repeated.
* Mixed clauses keep only non-negated execution clauses; nested or ironic negation and
  long-distance negation ("não sei se queres que abras") are treated as negation or
  ambiguity, never as a request.
* Every opening still needs the spoken PT confirmation (``sim``) bound to the digest:
  this verdict is an additional gate, never a replacement.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from enum import StrEnum

from jarvis.language.pt import normalize, strip_vocative


class IntentKind(StrEnum):
    EXECUTE_REQUEST = "execute_request"
    QUESTION = "question"
    NEGATION = "negation"
    PAST_REFERENCE = "past_reference"
    CITATION = "citation"
    AMBIGUOUS = "ambiguous"
    NONE = "none"


@dataclass(frozen=True, slots=True)
class IntentVerdict:
    """Auditable result. ``reasons`` are fixed codes; the user's text is never kept."""

    kind: IntentKind
    applications: tuple[str, ...] = ()  # authorised targets: only for EXECUTE_REQUEST
    hinted_applications: tuple[str, ...] = ()  # AMBIGUOUS: what to ask about
    reasons: tuple[str, ...] = field(default_factory=tuple)
    mentioned: tuple[str, ...] = ()  # named in the utterance; never authorises

    def authorises(self, application: str) -> bool:
        return self.kind is IntentKind.EXECUTE_REQUEST and application in self.applications

    def as_record(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "applications": list(self.applications),
            "mentioned": list(self.mentioned),
            "reasons": list(self.reasons),
        }


NO_REQUEST = IntentVerdict(IntentKind.NONE, reasons=("no_utterance",))

# Application phrases (normalised). Single tokens also match with small typos.
_APP_PHRASES: dict[str, tuple[str, ...]] = {
    "calculator": ("calculadora", "calculador", "calc", "calculator", "maquina de calcular"),
    "notepad": ("bloco de notas", "bloco das notas", "bloco notas", "bloco de nota", "notepad"),
}
_APP_TYPO_TOKENS: dict[str, tuple[str, ...]] = {
    "calculator": ("calculadora",),
    "notepad": ("notepad",),
}
# Hints of a need without a request ("preciso de fazer contas").
_APP_HINTS: dict[str, tuple[str, ...]] = {
    "calculator": ("fazer contas", "fazer uma conta", "calcular", "somar", "fazer calculos"),
    "notepad": ("tomar notas", "tirar notas", "escrever uma nota", "apontar"),
}

# Execution verbs (normalised). Present imperative, subjunctive and infinitive forms.
_EXEC_VERBS: frozenset[str] = frozenset(
    {
        "abre", "abra", "abrir", "abram", "abras",
        "inicia", "inicie", "iniciar", "inicies",
        "lanca", "lance", "lancar", "lances",
        "arranca", "arranque", "arrancar", "arranques",
        "executa", "execute", "executar", "executes",
        "liga", "ligue", "ligar", "ligues",
        "corre", "corra", "correr",
    }
)
_EXEC_TYPO_ROOTS: tuple[str, ...] = ("abre", "abra", "abrir", "inicia", "iniciar")
# Close to "abre/abrir" but other verbs or tenses: never typo-matched to a request.
_NOT_EXEC_PREFIXES: tuple[str, ...] = ("abri", "abrac", "abrig", "abrev", "abro")
# Indicative forms describe, they do not ask ("abres a calculadora", "tu abres …").
_INDICATIVE: frozenset[str] = frozenset(
    {"abres", "abrem", "abrires", "abrimos", "inicias", "iniciam", "lancas", "ligas", "executas"}
)
_RAW_COPULA = re.compile(r"\b(?:é|está|era|seria|fica|parece|foi)\b", re.IGNORECASE)
# Unaccented STT output loses "é": words that make a leading infinitive a statement.
_STATEMENT_WORDS: frozenset[str] = frozenset(
    {"facil", "dificil", "possivel", "impossivel", "simples", "custa", "demora", "rapido",
     "lento", "seguro", "perigoso", "util", "inutil"}
)
# The user takes it back, defers it, or makes it conditional: never a request now.
_RETRACTIONS: frozenset[str] = frozenset({"mentira", "brincar", "brincadeira", "gozar", "gozo"})
_DEFERRALS: frozenset[str] = frozenset({"amanha", "logo", "tarde", "daqui", "proxima", "semana"})
_CONDITIONAL: frozenset[str] = frozenset({"se", "caso", "quando", "talvez"})
_COPULAS: frozenset[str] = frozenset({"e", "esta", "era", "seria", "fica", "parece", "foi"})
_REFUSALS: frozenset[str] = frozenset({"nao", "nunca", "jamais", "nem", "deixa", "esquece"})
_OBJECT_WINDOW = 3  # the application must follow the verb closely (direct object)
# Past forms and time markers: talking about something already done or asked.
_PAST_TOKENS: frozenset[str] = frozenset(
    {
        "abri", "abriste", "abriu", "abrimos", "abriram", "abrira", "abriras",
        "iniciei", "iniciaste", "iniciou", "pedi", "pediste", "pediu", "pedimos",
        "ontem", "anteontem", "antes", "anteriormente", "ja", "passado", "passada",
    }
)
_NEGATION_TOKENS: frozenset[str] = frozenset({"nao", "nunca", "jamais", "nem", "sem"})
# Reported speech: past/report verbs and "diz que"; the imperative "diz" is not one.
_CITATION_TOKENS: frozenset[str] = frozenset(
    {"disse", "disseste", "dizia", "dizem", "escreveu", "citou", "cita", "frase", "ouvi",
     "ouviste", "perguntou", "pediram", "mandou", "mandaram"}
)
_CITATION_BIGRAMS: tuple[str, ...] = ("diz que", "dizer que", "escreve que", "a mensagem diz")
_QUESTION_STARTS: frozenset[str] = frozenset(
    {"qual", "quais", "que", "quem", "como", "porque", "porques", "quando", "onde",
     "quanto", "quantos", "quantas", "sera", "explica", "explicame", "define",
     "diferenca", "sabes", "conheces", "existe", "resume", "resumo"}
)
_QUESTION_BIGRAMS: frozenset[str] = frozenset({"o que", "e o", "e a", "e qual", "e quem", "diz me"})
_CAPABILITY_VERBS: frozenset[str] = frozenset(
    {"podes", "pode", "podias", "podia", "poderias", "poderia", "consegues", "consegue",
     "conseguias", "conseguirias", "importas", "importa"}
)
_DESIRE_FRAMES: tuple[str, ...] = (
    "quero que", "queria que", "preciso que", "gostava que", "gostaria que",
    "faz me o favor de", "por favor",
)
_POLITENESS = re.compile(r"\b(?:por favor|se faz favor|faz favor|faca favor|obrigado|obrigada)\b")
_CLAUSE_SPLIT = re.compile(r"\s*(?:[,;]|\be\b|\bmas\b|\bdepois\b|\bentao\b|\btambem\b)\s*")
_QUOTE_CHARS = ('"', "“", "”", "«", "»", "'", "‘", "’")


def _similar(a: str, b: str, threshold: float) -> bool:
    return len(a) >= 4 and abs(len(a) - len(b)) <= 2 and SequenceMatcher(None, a, b).ratio() >= threshold


def _first_app_position(tokens: list[str], app: str) -> int | None:
    """Token index where the application is named (phrase start or fuzzy token)."""
    for phrase in _APP_PHRASES.get(app, ()):
        words = phrase.split()
        for index in range(len(tokens) - len(words) + 1):
            if tokens[index : index + len(words)] == words:
                return index
    for index, token in enumerate(tokens):
        if any(_similar(token, root, 0.8) for root in _APP_TYPO_TOKENS.get(app, ())):
            return index
        if app == "notepad" and token == "bloco":
            return index
    return None


def _applications_in(clause: str, allowed: Iterable[str]) -> list[str]:
    found: list[str] = []
    tokens = clause.split()
    padded = f" {clause} "
    for app in allowed:
        phrases = _APP_PHRASES.get(app, ())
        if any(f" {phrase} " in padded for phrase in phrases):
            found.append(app)
            continue
        typo_roots = _APP_TYPO_TOKENS.get(app, ())
        if any(_similar(token, root, 0.8) for token in tokens for root in typo_roots):
            found.append(app)
            continue
        if app == "notepad" and "bloco" in tokens:
            index = tokens.index("bloco")
            tail = tokens[index + 1 : index + 4]
            if any(_similar(token, "notas", 0.75) for token in tail):
                found.append(app)
    return found


def _hinted_in(clause: str, allowed: Iterable[str]) -> list[str]:
    padded = f" {clause} "
    return [app for app in allowed if any(f" {h} " in padded for h in _APP_HINTS.get(app, ()))]


def _verb_index(tokens: list[str]) -> int | None:
    for index, token in enumerate(tokens):
        base = token.split("me")[0] if token.endswith("me") and len(token) > 4 else token
        if token in _EXEC_VERBS or base in _EXEC_VERBS:
            return index
        if token in _PAST_TOKENS or token in _INDICATIVE:
            continue
        if token.startswith(_NOT_EXEC_PREFIXES) and token != "abrir":
            continue
        if len(token) <= 6 and any(_similar(token, root, 0.8) for root in _EXEC_TYPO_ROOTS):
            return index
    return None


@dataclass
class _Clause:
    text: str
    apps: list[str]
    hints: list[str]
    verb: int | None
    tokens: list[str]


def _analyse(clauses: list[str], allowed: tuple[str, ...]) -> list[_Clause]:
    analysed: list[_Clause] = []
    for raw in clauses:
        tokens = raw.split()
        if not tokens:
            continue
        analysed.append(
            _Clause(raw, _applications_in(raw, allowed), _hinted_in(raw, allowed), _verb_index(tokens), tokens)
        )
    return analysed


def classify_request(
    utterance: str | None, allowed_applications: Iterable[str] = ("calculator", "notepad")
) -> IntentVerdict:
    """Classify the user's own utterance. Never raises: any error means ``NONE``."""
    try:
        return _classify(utterance, tuple(allowed_applications))
    except Exception:  # fail closed: an internal error never authorises anything
        return IntentVerdict(IntentKind.NONE, reasons=("classifier_error",))


def _classify(utterance: str | None, allowed: tuple[str, ...]) -> IntentVerdict:
    if not utterance or not utterance.strip():
        return NO_REQUEST
    raw = utterance.strip()
    is_interrogative = raw.endswith("?") or raw.startswith("¿")
    quoted = any(char in raw for char in _QUOTE_CHARS) or ":" in raw
    text = normalize(strip_vocative(raw))
    text = _POLITENESS.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return IntentVerdict(IntentKind.NONE, reasons=("politeness_only",))
    tokens = text.split()
    if (
        tokens
        and tokens[0].endswith("r")
        and tokens[0] in _EXEC_VERBS
        and (_RAW_COPULA.search(raw) or _STATEMENT_WORDS & set(tokens))
    ):
        # "Abrir a calculadora é fácil": a statement about opening, not a request.
        return IntentVerdict(IntentKind.NONE, (), (), ("infinitive_statement",))
    clauses = _analyse(_CLAUSE_SPLIT.split(text), allowed)
    # Coordination: "abre a calculadora e o bloco de notas" — verbless app clause inherits.
    previous_verb_clause: _Clause | None = None
    for clause in clauses:
        if clause.verb is not None:
            previous_verb_clause = clause
        elif clause.apps and previous_verb_clause is not None:
            clause.verb = -1  # inherited
            clause.tokens = previous_verb_clause.tokens
    reasons: list[str] = []
    mentioned = sorted({app for c in clauses for app in c.apps})
    hinted = sorted({app for c in clauses for app in c.hints} - set(mentioned))

    citation = (
        quoted
        or bool(_CITATION_TOKENS & set(tokens))
        or any(f" {bigram} " in f" {text} " for bigram in _CITATION_BIGRAMS)
    )
    if citation and any(c.verb is not None for c in clauses):
        return IntentVerdict(IntentKind.CITATION, (), tuple(hinted), ("reported_speech",), tuple(mentioned))

    if _PAST_TOKENS & set(tokens) and not any(
        c.verb is not None and c.verb >= 0 and c.tokens[c.verb] in {"abre", "abra", "abrir", "inicia", "inicie", "iniciar"}
        and not (_PAST_TOKENS & set(c.tokens[: c.verb]))
        for c in clauses
    ):
        return IntentVerdict(IntentKind.PAST_REFERENCE, (), tuple(hinted), ("past_marker",), tuple(mentioned))

    if _RETRACTIONS & set(tokens):
        return IntentVerdict(IntentKind.NEGATION, (), tuple(hinted), ("retracted",), tuple(mentioned))
    if (_CONDITIONAL | _DEFERRALS) & set(tokens) and any(c.verb is not None for c in clauses):
        return IntentVerdict(
            IntentKind.AMBIGUOUS, (), tuple(mentioned or hinted), ("conditional_or_deferred",)
        )
    # A clause that is only a refusal ("? não", "não, deixa", "nem pensar") negates all.
    if any(c.verb is None and not c.apps and set(c.tokens) & _REFUSALS for c in clauses):
        return IntentVerdict(IntentKind.NEGATION, (), tuple(hinted), ("refusal_clause",), tuple(mentioned))

    requested: list[str] = []
    negated: list[str] = []
    capability_question = False
    for clause in clauses:
        if clause.verb is None or not clause.apps:
            continue
        index = clause.verb if clause.verb >= 0 else 0
        before = clause.tokens[:index] if clause.verb >= 0 else []
        after = clause.tokens[index + 1 :] if clause.verb >= 0 else []
        if _NEGATION_TOKENS & set(before) or _REFUSALS & set(after):
            negated.extend(clause.apps)
            continue
        if clause.verb >= 0 and clause.tokens[index].endswith("r") and _COPULAS & set(after):
            continue  # "abrir a calculadora é fácil": a statement, not a request
        if clause.verb >= 0:
            # The application must be the verb's direct object, right after it.
            objects = [
                app for app in clause.apps
                if (pos := _first_app_position(clause.tokens, app)) is not None
                and 0 < pos - index <= _OBJECT_WINDOW
            ]
            if len(clause.apps) > 1 and objects:
                objects = list(clause.apps)  # "abre a calculadora e o bloco" (coordinated)
            clause.apps = objects
            if not clause.apps:
                continue
        if _PAST_TOKENS & set(before):
            continue
        prefix = " ".join(before)
        imperative = clause.verb == -1 or index == 0 or all(t in {"o", "a", "me", "tu", "voce"} for t in before)
        capability = bool(_CAPABILITY_VERBS & set(before))
        desire = any(frame in f"{prefix} " or prefix.startswith(frame) for frame in _DESIRE_FRAMES)
        if imperative or capability or desire:
            requested.extend(clause.apps)
            capability_question = capability_question or capability
            reasons.append("capability_question" if capability else "desire_frame" if desire else "imperative")
        # Any other frame ("a calculadora abre rapido?", "o que abre …") is not a request.

    requested = sorted(set(requested) - set(negated))
    if negated and not requested:
        return IntentVerdict(IntentKind.NEGATION, (), tuple(hinted), ("negated",), tuple(mentioned))
    if requested:
        if negated:
            reasons.append("partial_negation")
        if is_interrogative and not capability_question:
            # "Abro a calculadora?" style or a question that merely contains a verb.
            return IntentVerdict(IntentKind.AMBIGUOUS, (), tuple(requested), ("interrogative_without_request",))
        return IntentVerdict(IntentKind.EXECUTE_REQUEST, tuple(requested), (), tuple(dict.fromkeys(reasons)))

    has_verb = any(c.verb is not None for c in clauses)
    starts_like_question = bool(tokens) and (
        tokens[0] in _QUESTION_STARTS or " ".join(tokens[:2]) in _QUESTION_BIGRAMS
    )
    if is_interrogative or (starts_like_question and not has_verb):
        return IntentVerdict(IntentKind.QUESTION, (), tuple(hinted), ("interrogative",), tuple(mentioned))
    if mentioned or hinted:
        return IntentVerdict(IntentKind.AMBIGUOUS, (), tuple(mentioned or hinted), ("target_without_request",))
    if has_verb:
        return IntentVerdict(IntentKind.AMBIGUOUS, (), (), ("verb_without_target",))
    return IntentVerdict(IntentKind.NONE, reasons=("conversational",))
