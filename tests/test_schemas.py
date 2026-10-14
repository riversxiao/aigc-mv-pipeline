from aigc_mv.schemas import Beatmap, Character, LyricSegment, ProjectBrief, Shot, Timeline


def test_character_roundtrip():
    c = Character(
        id="x",
        display_name="X",
        identity="a tall adult figure with a silver pin",
        wardrobe_default="black coat",
    )
    assert c.id == "x"
    assert "silver pin" in c.identity


def test_beatmap_segments():
    bm = Beatmap(
        project="demo",
        duration_sec=10.0,
        segments=[LyricSegment(text="a", t0=0.0, t1=5.0)],
    )
    assert bm.segments[0].t1 == 5.0


def test_shot_and_timeline():
    s = Shot(shot_id="s01", t0=0, t1=2, who=["example_poet"], framing="MCU")
    assert s.framing == "MCU"
    t = Timeline(project="demo", duration_sec=2, clips=[])
    assert t.output.endswith("preview.mp4")


def test_brief():
    b = ProjectBrief(name="n", concept="c", characters=["example_poet"])
    assert b.target_duration_sec == 30.0
