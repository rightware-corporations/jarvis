"""JAR-COG-01 Package C — PT-MZ conversation corpus and the Kaggle retest cell.

SYSTEM CONTEXT DELIVERY only (deterministic, scripted provider): the backend hands the
whole session history to the provider. MODEL CONTEXT COMPREHENSION needs a real model
and is checked by ``qa/kaggle/JAR-COG-01_retest_cell.py`` (not run here).
"""

from __future__ import annotations

import asyncio
import json

from jarvis.language.intent import classify_request
from tests_vexel.conftest import make_rig
from tests_vexel.fakes import REPO_ROOT, call, say

CORPUS = json.loads((REPO_ROOT / "qa" / "corpus" / "pt_mz_conversation_v1.json").read_text("utf-8"))


def run(rig, text):
    return asyncio.run(rig.session.handle_text(text))


def open_app(arguments, call_id="c1"):
    return call("open_allowed_application", arguments, call_id=call_id)


def _messages_sent(rig, request: int = -1):
    return rig.provider.requests[request][0][1:]  # without the system prompt


def test_corpus_session_delivers_the_whole_history_to_the_provider() -> None:
    rig = make_rig()
    replies = []
    for index, turn in enumerate(CORPUS["turns"]):
        if turn["tool"].startswith("confirm:"):
            rig.provider.push(open_app({"app": turn["tool"].split(":")[1]}, f"k{index}"))
        elif turn["tool"].startswith("simulated:"):
            rig.provider.push(say("Pronto."))
        else:
            reply = f"Resposta {index}."
            replies.append(reply)
            rig.provider.push(say(reply))
    results = [run(rig, turn["input"]) for turn in CORPUS["turns"]]

    assert [r.turn_index for r in results] == list(range(1, len(results) + 1))
    assert len({r.session_id for r in results}) == 1
    # A confirmation turn ("sim") carries the scope of the request it confirms.
    assert [r.request_intent["kind"] if r.request_intent else "none" for r in results] == [
        "execute_request" if t["input"] == "sim" else t["intent"] for t in CORPUS["turns"]
    ]
    assert all(classify_request(t["input"]).kind.value == t["intent"] for t in CORPUS["turns"])
    assert rig.launcher.requested == ["calculator"]  # only the explicit request, once
    assert results[11].awaiting_confirmation and results[12].action_status == "SIMULATED"
    # The last request carries every earlier user turn (except the local "sim").
    sent_users = [m.content for m in _messages_sent(rig) if m.role == "user"]
    expected_users = [t["input"] for t in CORPUS["turns"] if t["input"] != "sim"]
    assert sent_users == expected_users
    sent_assistant = [m.content for m in _messages_sent(rig) if m.role == "assistant" and m.content]
    assert all(reply in sent_assistant for reply in replies[:-1])
    assert results[-1].metrics["context_dropped"] == 0.0


def test_kaggle_retest_cell_is_static_safe() -> None:
    """The cell is Kaggle-only (never run in CI): it must compile, pin loopback and keep
    applications simulated, and it must refuse to run without the expected SHA."""
    source = (REPO_ROOT / "qa" / "kaggle" / "JAR-COG-01_retest_cell.py").read_text("utf-8")
    compile(source, "JAR-COG-01_retest_cell.py", "exec")
    assert 'data["vexel"]["allow_real_windows_actions"] = False' in source
    assert 'data["llm"]["endpoint"] = "http://127.0.0.1:11434"' in source
    assert 'EXPECTED_SHA = ""' in source and "SHA mismatch" in source
    assert "include_text=False" in source and "ollama pull" not in source and "\"pull\"" not in source
