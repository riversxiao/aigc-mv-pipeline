"""Tests for lore knowledge layer."""

from pathlib import Path

import pytest

from aigc_mv.lore import (
    get_lore,
    get_lore_path,
    list_lore_ids,
    load_lore,
    render_lyric_brief,
)
from aigc_mv.schemas import LoreStory, ProjectBrief

REPO = Path(__file__).resolve().parents[1]
KNOWLEDGE = REPO / "knowledge"


def test_list_and_load_lore():
    ids = list_lore_ids(KNOWLEDGE)
    assert "guan_bao_zhi_jiao" in ids
    assert "wan_bi_gui_zhao" in ids
    assert "wo_xin_chang_dan" in ids
    lore = load_lore("guan_bao_zhi_jiao", KNOWLEDGE)
    assert isinstance(lore, LoreStory)
    assert lore.id == "guan_bao_zhi_jiao"
    assert lore.source == "史记"
    assert "管鲍" in lore.classic_title or "管鲍" in lore.classic_summary
    assert lore.lyric_seeds
    assert lore.scene_beats


def test_avoid_includes_political_satire():
    for lid in list_lore_ids(KNOWLEDGE):
        lore = load_lore(lid, KNOWLEDGE)
        joined = " ".join(lore.avoid)
        assert "政治" in joined or "political" in joined.lower()


def test_get_lore_dict_and_path():
    data = get_lore("wan_bi_gui_zhao", KNOWLEDGE)
    assert data["classic_title"]
    path = get_lore_path("wan_bi_gui_zhao", KNOWLEDGE)
    assert path.name == "wan_bi_gui_zhao.yaml"
    assert path.is_file()


def test_lyric_brief_chinese():
    text = render_lyric_brief("guan_bao_zhi_jiao", KNOWLEDGE)
    assert "管鲍" in text
    assert "歌词种子" in text
    assert "借古讽今" in text
    assert "政治" in text


def test_missing_lore():
    with pytest.raises(FileNotFoundError):
        load_lore("does_not_exist", KNOWLEDGE)


def test_brief_with_lore_id():
    b = ProjectBrief(
        name="demo_guanbao",
        concept="友情",
        characters=["example_poet"],
        lore_id="guan_bao_zhi_jiao",
    )
    assert b.lore_id == "guan_bao_zhi_jiao"
    bare = ProjectBrief(name="x", concept="y")
    assert bare.lore_id is None
