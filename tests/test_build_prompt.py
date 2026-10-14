from pathlib import Path

import pytest

from aigc_mv.canon import build_prompt, get_canon, list_character_ids

REPO = Path(__file__).resolve().parents[1]
KNOWLEDGE = REPO / "knowledge"


def test_list_and_get_canon():
    ids = list_character_ids(KNOWLEDGE)
    assert "example_poet" in ids
    canon = get_canon("example_poet", KNOWLEDGE)
    assert canon["id"] == "example_poet"
    assert "poet" in canon["identity"].lower() or "Tang" in canon["identity"]


def test_build_prompt_order_and_verbatim():
    canon = get_canon("example_poet", KNOWLEDGE)
    identity = canon["identity"].strip()
    result = build_prompt(
        "example_poet",
        scene="on a tavern stage gripping a chrome microphone",
        framing="MCU",
        knowledge_dir=KNOWLEDGE,
    )
    prompt = result["prompt"]
    assert identity in prompt
    assert prompt.index("medium close-up") < prompt.index(identity)
    assert "no text, no letters, no logos" in prompt
    assert "on a tavern stage" in prompt
    assert "params" in result and "ar" in result["params"]
    assert any("verbatim" in c.lower() for c in result["checklist"])
    assert result["mj_string"].startswith(prompt)


def test_missing_character():
    with pytest.raises(FileNotFoundError):
        get_canon("does_not_exist", KNOWLEDGE)
