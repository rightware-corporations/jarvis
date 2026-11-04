"""Deterministic Portuguese control phrases.

Confirmation, refusal and cancellation are never decided by the language model. An
utterance counts as a control only if, after normalisation, it is *exactly* one of
the approved phrases below. Anything else is ``ControlIntent.NONE``; while a
confirmation is pending the voice loop treats NONE as a refusal.
"""

from __future__ import annotations

import re
import unicodedata
from enum import StrEnum


class ControlIntent(StrEnum):
    CONFIRM = "confirm"
    REJECT = "reject"
    CANCEL = "cancel"
    NONE = "none"


# Approved variants (JAR-SLICE-01B). Stored already normalised: lower case, no accents.
CONFIRM_PHRASES: frozenset[str] = frozenset(
    {
        "sim",
        "sim confirmo",
        "sim pode",
        "sim por favor",
        "confirmo",
        "confirmado",
        "pode",
        "pode avancar",
        "avanca",
    }
)
REJECT_PHRASES: frozenset[str] = frozenset(
    {
        "nao",
        "nao obrigado",
        "nao quero",
        "esquece",
        "deixa",
        "deixa estar",
    }
)
CANCEL_PHRASES: frozenset[str] = frozenset(
    {
        "cancela",
        "cancelar",
        "cancela isso",
        "cancela essa operacao",
        "cancela a operacao",
        "cancela tudo",
        "para",
        "pare",
        "interrompe",
        "chega",
    }
)

_VOCATIVE = re.compile(r"^(?:(?:ei|hey|ok|ola)\s+)?jarvis\b\s*", re.IGNORECASE)
_NON_WORD = re.compile(r"[^\w\s]+", re.UNICODE)
_SPACES = re.compile(r"\s+")


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def normalize(text: str) -> str:
    """Lower-case, accent-free, punctuation-free, single-spaced."""
    lowered = strip_accents(text).casefold()
    return _SPACES.sub(" ", _NON_WORD.sub(" ", lowered)).strip()


def strip_vocative(text: str) -> str:
    """Remove a leading 'Jarvis' / 'Ei Jarvis' from a transcribed command."""
    stripped = _VOCATIVE.sub("", text.strip(), count=1)
    return stripped.lstrip(" ,.:;!-").strip()


def classify_control(text: str) -> ControlIntent:
    phrase = normalize(strip_vocative(text))
    if phrase in CONFIRM_PHRASES:
        return ControlIntent.CONFIRM
    if phrase in REJECT_PHRASES:
        return ControlIntent.REJECT
    if phrase in CANCEL_PHRASES:
        return ControlIntent.CANCEL
    return ControlIntent.NONE
