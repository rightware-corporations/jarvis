"""Portuguese user-facing text built by VEXEL, never by the language model.

* Confirmation questions are generated from the pending, digest-bound call that the
  Wyzer Orchestrator holds, so what is asked always matches what would execute.
* The Orchestrator's fixed English replies are translated through a closed map.
  Anything not mapped is passed through unchanged and flagged for the evidence log.
"""

from __future__ import annotations

import re

from wyzer.models import PendingConfirmation

APPLICATION_LABELS: dict[str, str] = {
    "calculator": "a Calculadora",
    "notepad": "o Bloco de Notas",
}

SAY_CANCELLED = "Cancelei."
SAY_CANCELLED_NO_CONFIRMATION = "Cancelei, porque não ouvi uma confirmação."
SAY_CANCELLED_UNCLEAR = "Cancelei, porque não percebi a confirmação."
SAY_NOTHING_TO_CANCEL = "Não há nada em curso para cancelar."
SAY_NOT_HEARD = "Não ouvi nada."
SAY_ERROR = "Ocorreu um problema e não consegui concluir o pedido."
SAY_MODEL_UNAVAILABLE = "O modelo local não está disponível neste momento."

# Exact English strings emitted by wyzer/app/orchestrator.py (v0.3.1) that can reach
# the user in this slice. Prefix matches are used only for messages with variable tails.
_EXACT: dict[str, str] = {
    "Okay, I cancelled it.": SAY_CANCELLED,
    "Okay, I stopped it.": "Parei.",
    "There is no active task.": SAY_NOTHING_TO_CANCEL,
    "I didn't catch anything.": SAY_NOT_HEARD,
    "That confirmation expired. Please ask me to do it again.": (
        "Essa confirmação expirou. Pede-me de novo, por favor."
    ),
}
_PREFIXES: tuple[tuple[str, str], ...] = (
    ("I couldn't confirm it because", "Não consegui confirmar, porque o pedido mudou."),
    ("A tool-capable local model is not configured", SAY_MODEL_UNAVAILABLE),
    # Wyzer's loop guard (maximum tool rounds) must not reach the user in English.
    ("I stopped after", "Não consegui concluir a resposta. Podes repetir a pergunta de outra forma?"),
    # Orchestrator text when a provider call raises past the PT wrapper (defence in depth).
    ("The local model could not respond", SAY_MODEL_UNAVAILABLE),
)


def confirmation_prompt(pending: PendingConfirmation) -> str:
    if pending.tool_name == "open_allowed_application":
        app = str(pending.arguments.get("app", ""))
        label = APPLICATION_LABELS.get(app)
        if label is not None:
            return f"Queres que eu abra {label}? Responde sim ou não."
    return "Esta acção precisa da tua confirmação. Responde sim ou não."


def translate_wyzer_reply(text: str) -> tuple[str, bool]:
    """Return (portuguese_text, was_translated)."""
    stripped = text.strip()
    if stripped in _EXACT:
        return _EXACT[stripped], True
    for prefix, replacement in _PREFIXES:
        if stripped.startswith(prefix):
            return replacement, True
    return text, False


# ------------------------------------------------------------ action outcomes
# Built from the recorded tool result, never from model text (JAR-SLICE-01B-R01 P1).

SAY_NOTHING_OPENED = "Não abri nenhuma aplicação."
SAY_DENIED = "Não tenho autorização para fazer isso."
SAY_TTS_UNAVAILABLE_CONFIRMATION = "Cancelei, porque não consegui apresentar a confirmação."


def operation_history_text(app: str | None, status: str) -> str:
    """The truth about the session's last effectful operation (JAR-COG-01-R02)."""
    label = APPLICATION_LABELS.get(app or "", "uma aplicação")
    if status == "SIMULATED":
        return (
            f"A última operação foi o pedido para abrir {label}: pediste e confirmaste, "
            "mas foi apenas simulada, por isso nenhuma aplicação foi aberta."
        )
    if status == "SUCCEEDED":
        return f"A última operação foi abrir {label}, e foi aberta."
    if status == "FAILED":
        return f"A última operação foi tentar abrir {label}, mas falhou."
    if status == "DENIED":
        return f"O último pedido para abrir {label} foi recusado."
    return (
        f"O último pedido foi abrir {label}, mas não foi executado: "
        "não foi confirmado ou foi interrompido."
    )


_OPERATION_WORDS = re.compile(
    r"\b(?:operacao|operacoes|fizeste|abriste|executaste|fizemos|acao|accao|acoes|accoes|"
    r"iniciaste|lancaste|o que aconteceu|correu bem|ja esta aberta|ja esta aberto)\b"
)


def asks_about_operations(text: str | None) -> bool:
    from jarvis.language.pt import normalize

    return bool(text) and bool(_OPERATION_WORDS.search(normalize(text or "")))


def action_outcome_text(status: str, app: str | None) -> str:
    """Spoken result for an effectful action. ``status`` is an ``ActionStatus`` value."""
    label = APPLICATION_LABELS.get(app or "")
    if status == "SUCCEEDED" and label is not None:
        return f"Abri {label}."
    if status == "SIMULATED" and label is not None:
        return f"Modo de simulação: não abri {label}. Nenhuma aplicação foi iniciada."
    if status == "FAILED" and label is not None:
        return f"Não consegui abrir {label}."
    if status == "FAILED":
        return "Não consegui concluir a acção."
    return SAY_DENIED


# Phrases in which the model claims an application was opened or a command executed.
_ACTION_CLAIM = re.compile(
    r"\b(?:abri|abriu|abrimos|abrindo|ja abri|ja esta aberta?o?|esta aberta|esta aberto|"
    r"foi aberta|foi aberto|aberta com sucesso|aberto com sucesso|iniciei|inicializei|"
    r"lancei|executei|arranquei|pronto,? a calculadora|pronto,? o bloco)\b"
)


def clarification_text(
    applications: tuple[str, ...] | list[str], *, simulated: bool = True
) -> str:
    """A question back to the user: never a confirmation and never an action. It names
    the exact phrase to say, so the next turn is an explicit request (no loop)."""
    labels = [APPLICATION_LABELS[app] for app in applications if app in APPLICATION_LABELS]
    if len(labels) == 1:
        return (
            f"Não tenho a certeza se queres que eu abra {labels[0]}. "
            f"Se quiseres, diz: «abre {labels[0].lower()}»."
        )
    mode = " (em modo de simulação)" if simulated else ""
    return (
        f"Só consigo abrir a Calculadora ou o Bloco de Notas{mode}. "
        "Diz, por exemplo: «abre a calculadora» ou «abre o bloco de notas»."
    )


def strip_action_claims(text: str) -> tuple[str, bool]:
    """Remove only the sentences that claim an action; keep the rest of the reply."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    kept = [sentence for sentence in sentences if sentence and not claims_action(sentence)]
    removed = len(kept) != len([s for s in sentences if s])
    cleaned = " ".join(kept).strip()
    # A leftover like "Pronto!" or "e o bloco de notas" still implies the claim.
    if removed and len(cleaned.split()) < 3:
        cleaned = ""
    return cleaned, removed


# Negation directly before the claimed verb, in the same clause ("não abri", "não a
# abri", "nunca foi aberta"). A negation in another clause ("Não, abri …") does not count.
_NEGATED_BEFORE = re.compile(
    r"\b(?:nao|nunca|jamais)\s+(?:(?:a|o|os|as|lhe|me|te|se|ja|foi|esta)\s+)?$"
)
# Any character that is not a letter, digit or plain space ends the clause: punctuation,
# quotes, dashes (-, –, —), line breaks. Only "não abri" side by side is a negation.
_CLAUSE_BREAK = re.compile(r"(?:[^\w ]|_)+")


def claims_action(text: str) -> bool:
    """True when the text affirms an action. A statement negated in its own clause
    ("não abri nenhuma aplicação") is the truth, not a claim (JAR-COG-01)."""
    from jarvis.language.pt import normalize

    for clause in _CLAUSE_BREAK.split(text):
        normalised = normalize(clause)
        for match in _ACTION_CLAIM.finditer(normalised):
            if not _NEGATED_BEFORE.search(normalised[: match.start()]):
                return True
    return False
