"""Canon grounding: demo cards carry official-art metadata, `ep canon` places local refs without the network."""

import io
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from aigc_mv import canon_refs, cinema
from aigc_mv.episode import load_episode
from aigc_mv.prompts import characters

REPO = Path(__file__).resolve().parents[1]
DEMO = REPO / "projects" / "wangye_vs_zhugeqing"

BANGUMI = {
    "zhuge_qing": 61836, "wang_ye": 61837, "zhuge_bai": 127662, "zhang_chulan": 42202, "zhang_zhiwei": 103754,
    "lu_jin": 103755, "feng_zhenghao": 45136, "xu_si": 42205, "xu_san": 42204, "feng_baobao": 42203,
    "zhang_lingyu": 42208, "feng_shayan": 42213,
}
ORIGINAL = {"zhuge_menren", "wudang_daotong", "zhuge_zhanglao"}


def test_demo_cards_canon_fields():
    chars = characters(load_episode(DEMO))
    assert len(chars) == 15
    seen = set()
    for k, c in chars.items():
        seen.add(c.id)
        if c.id in ORIGINAL:
            assert not c.canon_refs, c.id
            assert "原创角色，无原作图，第一步用文生图" in c.notes
            continue
        assert [r.id for r in c.canon_refs] == [BANGUMI[c.id]], c.id
        r = c.canon_refs[0]
        assert r.site == "bangumi" and r.url == f"https://bgm.tv/character/{r.id}"
        assert c.signature_cn and c.signature_en and c.canon_look_cn, c.id
        assert r.url in c.notes, c.id
        text = " ".join([c.identity, c.identity_short, c.identity_cn, c.wardrobe_default, c.wardrobe_cn,
                         c.props_cn, c.signature_cn, c.signature_en, c.canon_look_cn])
        assert not cinema.banned_hits(text), (c.id, cinema.banned_hits(text))
        assert "\u2014" not in text + c.notes
        for w in ("烟", "cigarette"):
            assert w not in text, (c.id, w)
    assert seen == set(BANGUMI) | ORIGINAL


def test_demo_cards_follow_official_art():
    chars = {c.id: c for c in characters(load_episode(DEMO)).values()}
    assert "深藏青" in chars["zhuge_qing"].identity_cn and "背带" in chars["zhuge_qing"].wardrobe_cn
    assert "玉坠" in chars["zhuge_qing"].signature_cn and "马尾" not in chars["zhuge_qing"].identity_cn
    assert "亮蓝色" in chars["zhuge_bai"].identity_cn and "波波头" in chars["zhuge_bai"].identity_cn and "礼帽" in chars["zhuge_bai"].wardrobe_cn
    assert "银白" in chars["feng_shayan"].identity_cn
    bb = chars["feng_baobao"]
    assert "长直发" in bb.identity_cn and "浅灰" in bb.wardrobe_cn and "长裙" in bb.wardrobe_cn
    assert "墨镜" not in chars["xu_si"].identity_cn and "眼镜" in chars["xu_san"].identity_cn
    assert "圆形细金属框眼镜" in chars["feng_zhenghao"].identity_cn


def test_battle_cards_still_load():
    from aigc_mv.canon import load_character

    for cid in ("xiang_yu", "liu_bang"):
        c = load_character(cid)
        assert c.canon_refs == [] and c.signature_cn == ""


def _mini_ep(tmp_path: Path) -> Path:
    d = tmp_path / "ep"
    d.mkdir()
    shutil.copy(DEMO / "episode.yaml", d / "episode.yaml")
    return d


def test_fetch_canon_copies_from_src(tmp_path, monkeypatch):
    def no_net(*a, **kw):
        raise AssertionError("network must not be used when --src has the file")

    monkeypatch.setattr(canon_refs.urllib.request, "urlopen", no_net)
    src = tmp_path / "src"
    src.mkdir()
    for cid in BANGUMI:
        (src / f"{cid}.jpg").write_bytes(b"\xff\xd8" + cid.encode())
    d = _mini_ep(tmp_path)
    res = canon_refs.fetch_canon(d, load_episode(d), src)
    assert not res.failed
    assert set(res.placed.values()) == {"copied"} and len(res.placed) == 12
    assert {load_episode(d).cast[k].character for k in res.original} == ORIGINAL
    out = d / "refs" / "canon"
    assert (out / "zhuge_qing.jpg").read_bytes() == b"\xff\xd8zhuge_qing"
    assert "https://bgm.tv/character/61836" in (out / "SOURCES.md").read_text(encoding="utf-8")
    again = canon_refs.fetch_canon(d, load_episode(d), src)  # existing files are skipped
    assert set(again.placed.values()) == {"exists"}


def test_fetch_canon_downloads_from_bangumi(tmp_path, monkeypatch):
    calls = []

    def fake_urlopen(req, timeout=None):
        url = req.full_url
        calls.append((url, req.get_header("User-agent")))
        if url.startswith("https://api.bgm.tv/v0/characters/"):
            cid = url.rsplit("/", 1)[1]
            body = json.dumps({"images": {"large": f"https://lain.bgm.tv/pic/crt/l/{cid}.jpg"}}).encode()
        else:
            body = b"\xff\xd8img"
        return io.BytesIO(body)

    monkeypatch.setattr(canon_refs.urllib.request, "urlopen", fake_urlopen)
    d = _mini_ep(tmp_path)
    res = canon_refs.fetch_canon(d, load_episode(d), None)
    assert not res.failed and set(res.placed.values()) == {"downloaded"}
    urls = [u for u, _ in calls]
    assert "https://api.bgm.tv/v0/characters/61836" in urls
    assert "https://lain.bgm.tv/pic/crt/l/61836.jpg" in urls
    assert all(ua and "aigc-mv-pipeline" in ua for _, ua in calls)
    assert (d / "refs" / "canon" / "wang_ye.jpg").read_bytes() == b"\xff\xd8img"


def test_canon_folder_is_gitignored():
    if shutil.which("git") is None:
        pytest.skip("git not available")
    r = subprocess.run(
        ["git", "check-ignore", "-q", "projects/wangye_vs_zhugeqing/refs/canon/zhuge_qing.jpg"], cwd=REPO
    )
    assert r.returncode == 0
