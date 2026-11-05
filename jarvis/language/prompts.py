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


def claims_action(text: str) -> bool:
    from jarvis.language.pt import normalize

    return bool(_ACTION_CLAIM.search(normalize(text)))
