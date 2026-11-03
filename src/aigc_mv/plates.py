"""Environment plates for variety-show episodes (`format: show`): one locked background still per camera
position of the arena, so every generated unit sees the same packed house, stage, LED wall and palette.

Each staging of cinema.SHOW_STAGINGS maps to exactly one plate (`plate_for`). A unit uploads the people
sheets first, then at most MAX_UNIT_PLATES plates; `pick_unit_plates` chooses them by screen time, with
`must` plates (cameo seats, the blackout) always kept. Cameos are never baked into a plate: cameo_seats.png
leaves their seats empty and the unit prompt seats them by `position_cn`.

Nothing here talks to the network: `cost_estimate` only multiplies counts by a per-image price, and
`ledger_image_usd` only reads ledger.jsonl.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from aigc_mv import cinema
from aigc_mv.episode import Episode

MAX_UNIT_PLATES = 2   # environment plates per unit (people sheets come first)
CANDIDATES = 4        # candidates per plate, lock one
# OpenRouter openai/gpt-image-2.5-sunburst, quality high: the ledger shows $0.055-0.060 per 3:4 image with one
# reference. 16:9 is 1536x1024, the same pixel count as 3:4 1024x1536, so the price should be the same.
PLATE_USD = 0.06
PLATE_USD_UPPER = 0.12  # 2x: longer prompt, a second reference, price changes

LED_BLANK_CN = "LED 大屏上只有抽象的红色光纹，没有任何文字、标志和人像，地面图案上也没有字"
LED_BLANK_EN = "the LED wall shows only abstract red light patterns, no text, no logo, no faces"
LIGHT_CN = "舞台顶部的硬光加两侧红色侧光，空气里有薄烟，像电视直播画面但有电影感，细腻颗粒"
LIGHT_EN = "hard top stage light with red side light, thin haze, broadcast realism with cinematic fine grain"
DARK_LIGHT_CN = "全场灯灭，只有头顶一束冷白色追光直直打在舞台中央，追光里能看到薄烟，其余地方几乎全黑，细腻颗粒"
DARK_LIGHT_EN = ("blackout, a single cold white follow spot straight down on the centre of the stage, haze visible "
                 "in the beam, everything else near black, fine grain")
REAL_CN = "像电视直播现场拍下的真实照片，观众是真实的普通人，皮肤有真实纹理"
REAL_EN = "a real photograph taken during a live TV broadcast, real ordinary people with natural skin texture"
NO_TEXT_CN = "综艺节目现场照片，无文字、无水印、无标志"
NO_TEXT_EN = "no text, no letters, no logos"
EMPTY_NEG_EN = "empty seats, empty stands"

# density, said in plates and again in unit video prompts
DENSE_CN = "没有空座位，每个人长得都不一样"
DENSE_PEOPLE_CN = "18 到 60 岁的普通成年观众，男女都有，胖瘦、发型和便装各不相同，表情各异，不是动漫脸，不像任何真实名人"
DENSE_EN = ("every tier packed with spectators, no empty seats, waving red glow sticks, ordinary adult audience aged "
            "18 to 60, men and women with clearly different faces, builds, hairstyles and casual clothes, varied "
            "expressions, no anime faces, nobody resembling a real celebrity")
BOKEH_CN = "背景里的看台也坐满了观众，虚成红色荧光棒的光斑，没有空座位"
BOKEH_EN = "the packed stands behind melted into bokeh of red glow sticks, no empty seats"
DARK_CN = "观众席一片黑，只看得到前几排观众的黑色剪影和零星的红色荧光棒光点"
DARK_EN = "the audience is dark, only black silhouettes of the front rows and scattered red glow-stick dots"


@dataclass(frozen=True)
class Plate:
    file: str
    title_cn: str       # short name used in upload roles and tables
    use_cn: str
    stagings: tuple[str, ...]
    framing: str        # cinema.FRAMINGS key
    lens: str           # cinema.LENSES key
    angle_cn: str
    angle_en: str
    scene_cn: str
    scene_en: str
    crowd: str          # full | bokeh | dark
    needs: tuple[str, ...] = ()  # cast roles that must exist for the plate to be needed
    guide: str = ""     # locked plate uploaded as 图1 (palette / layout)
    must: bool = False  # always kept when a unit has more than MAX_UNIT_PLATES candidates
    aspect: str = "16:9"


PLATES: list[Plate] = [
    Plate("venue.png", "舞台正面", "主场景：选手、队友、对峙、双人镜头的背景（先做这张，锁定后其他场景图都参考它）",
          ("cu_team_bg", "ots_hair", "faceoff_profile", "two_shot", "point_lens", "mic_to_lens", "rival_react",
           "teammate_react", "split_entrance"),
          "WS", "35", "从观众席正前方平视舞台，正面对称，地平线水平，台上没有人",
          "straight-on symmetrical view of the stage from the audience at eye level, level horizon, nobody on stage",
          "舞台在画面中间，背后是 LED 大屏和灯带，两侧和远处的看台层层叠叠",
          "the stage centred with the LED wall and light strips behind it, tiered stands on both sides", "full"),
    Plate("venue_high.png", "场馆高位全景", "开场和片尾的高位全景（摇臂镜头的起幅和落幅）",
          ("high_ws",), "WS", "24w", "从看台最高处往下拍的高位全景，看得到整个舞台、地面图案和四面看台，台上没有人",
          "high-angle wide shot from the top of the stands looking down at the whole stage, the floor graphic and "
          "the stands on every side, nobody on stage",
          "整个场馆一览无余，舞台灯光全亮", "the whole arena in one frame, all stage lights on", "full",
          guide="venue.png"),
    Plate("venue_dark.png", "灭灯舞台", "揭晓前的灭灯：背影追光、空舞台、低头特写和追光特写的背景",
          ("blackout_spot", "empty_stage_ws", "head_down_cu", "spot_cu"),
          "WS", "35", "和舞台正面那张同一个机位：正面平视，台上没有人", "the same straight-on eye-level camera as the "
          "main stage plate, nobody on stage",
          "LED 大屏和灯带全部熄灭，只剩追光落在地面中央", "the LED wall and light strips switched off, only the spot "
          "on the centre of the floor", "dark", guide="venue.png", must=True),
    Plate("crowd.png", "观众席中景", "观众欢呼的空镜（开场、间奏、片尾的观众镜头）",
          ("crowd_ws",), "MS", "50", "站在舞台边上平视前排看台，前三四排观众的脸看得清，后排层层叠叠",
          "from the stage edge at eye level toward the front sections, the first three or four rows clearly visible, "
          "more tiers rising behind", "二三十个看得清脸的观众冲着舞台欢呼、举手",
          "twenty to thirty clearly visible faces cheering toward the stage with raised hands", "full",
          guide="venue_high.png"),
    Plate("crowd_reverse.png", "台上看观众席", "反打：选手在台上把话筒伸向观众时，从台上往外看满场看台",
          ("mic_to_crowd",), "WS", "24w", "反打机位：从舞台后方越过舞台地面往外拍，前景是空的舞台边缘，"
          "看出去是满满的层层看台，台上没有人",
          "reverse angle from the back of the stage across the empty stage floor, looking out at the packed tiered "
          "stands, nobody on stage", "观众朝台上挥手、张嘴喊", "the audience waving and shouting toward the stage",
          "full", guide="venue_high.png"),
    Plate("cameo_seats.png", "前两排座位", "客串角色坐在观众席里的反应镜头（客串不画进这张图，座位留空）",
          ("cameo_react",), "MS", "50", "坐着的眼睛高度平视观众席前两排，正对着看台，第一排和第二排都在画面里",
          "seated eye level facing the first two rows of the stands, both rows in frame",
          "", "", "full", needs=("cameo",), guide="venue_high.png", must=True),
    Plate("judges.png", "评委席", "评委反应镜头的背景", ("judge_react",), "MS", "50",
          "评委席的正面中景，座位上没有人",
          "medium shot of the judges' bench from the front, nobody seated",
          "说唱节目的评委席：舞台边的高台上并排摆着三张高背深色木王座，红色轮廓光",
          "the judges' bench of a rap show: three tall dark wooden thrones side by side on a raised platform beside "
          "the stage, red rim light", "bokeh", needs=("judge",), guide="venue.png"),
    Plate("dj_booth.png", "DJ 台", "主持和 DJ 镜头的背景", ("dj_booth", "dj_cu"), "MS", "50",
          "DJ 台正面中景，台后没有人", "medium shot of the DJ booth from the front, nobody behind it",
          "舞台后方的 DJ 台：黑色台子上两台唱机和一台调音台，几盏小台灯，背后是 LED 大屏",
          "a DJ booth at the back of the stage: a black console with two turntables and a mixer, small lamps, the "
          "LED wall behind", "bokeh", needs=("host", "dj"), guide="venue.png"),
    Plate("hook_mics.png", "副歌立麦", "副歌歌手在立麦前唱的背景（舞台后方的两支立麦）", ("hook_mic",), "MS", "50",
          "立麦正面中景，没有人", "medium shot of the standing microphones from the front, nobody there",
          "舞台后方并排两支银色立麦，话筒架是黑色的，背后是 LED 大屏",
          "two silver microphones on black stands side by side at the back of the stage, the LED wall behind",
          "bokeh", needs=("hook",), guide="venue.png"),
]
BY_FILE = {p.file: p for p in PLATES}
STAGING_PLATE = {s: p.file for p in PLATES for s in p.stagings}
DEFAULT_PLATE = "venue.png"


def needed(ep: Episode, p: Plate) -> bool:
    return not p.needs or bool(ep.members(*p.needs))


def ep_plates(ep: Episode) -> list[Plate]:
    """Plates this episode needs (judges only with judges, cameo seats only with cameos, ...)."""
    return [p for p in PLATES if needed(ep, p)]


def plate_for(ep: Episode, staging: str) -> Plate:
    p = BY_FILE[STAGING_PLATE.get(staging, DEFAULT_PLATE)]
    return p if needed(ep, p) else BY_FILE[DEFAULT_PLATE]


def pick_unit_plates(ep: Episode, shots) -> tuple[list[Plate], list[Plate]]:
    """(kept, dropped): one plate per staging, `must` plates first, then by screen time, at most MAX_UNIT_PLATES."""
    secs: dict[str, float] = {}
    first: dict[str, int] = {}
    for i, s in enumerate(shots):
        f = plate_for(ep, s.staging).file
        secs[f] = secs.get(f, 0.0) + (s.t1 - s.t0)
        first.setdefault(f, i)
    order = sorted(secs, key=lambda f: (not BY_FILE[f].must, -round(secs[f], 3), first[f]))
    plates = [BY_FILE[f] for f in order] or [BY_FILE[DEFAULT_PLATE]]
    return plates[:MAX_UNIT_PLATES], plates[MAX_UNIT_PLATES:]


def upload_role(p: Plate) -> str:
    return f"是场景图（{p.title_cn}）：只用来对齐场馆、灯光和观众席的样子，人物照定妆图，不要把这张图原样当成画面"


def crowd_line(ep: Episode, shots, start: int = 1) -> str:
    """【观众】 for a unit: density restated for shots that show the house, the blackout kept dark."""
    full, bokeh, dark = [], [], []
    for k, s in enumerate(shots, start):
        p = plate_for(ep, s.staging)
        if p.crowd == "dark":
            dark.append(k)
        elif p.crowd == "full" and (p.file != DEFAULT_PLATE or s.framing == "WS"):  # the house is in frame
            full.append(k)
        else:  # close shots on stage: the stands are only bokeh behind
            bokeh.append(k)
    out = []
    crowd = ep.crowd_cn.strip("。，, ")
    if full:
        out.append("镜头" + "、".join(map(str, full)) + f"能看到观众席：{crowd}，{DENSE_CN}，都是普通观众；不要空座位，不要空看台")
    if bokeh:
        out.append(("其余镜头" if full else "") + BOKEH_CN)
    if dark:
        out.append("镜头" + "、".join(map(str, dark)) + f"灭灯了：{DARK_CN}，不要把观众照亮")
    return "【观众】" + "；".join(out) + "。" if out else ""


# --------------------------------------------------------------------------- prompts

_ROW = {"一": "front", "二": "second", "三": "third", "四": "fourth"}


def cameo_seat_cn(pos: str) -> str:
    """The seat a cameo sits in, as the plate leaves it empty (same words in the plate and the unit prompt)."""
    pos = pos or "观众席第二排"
    return pos if ("正中" in pos or "中间" in pos) else pos + "靠中间偏左"


def _seat_en(pos: str) -> str:
    m = re.search(r"第(.)排", pos or "")
    row = _ROW.get(m.group(1), "second") if m else "second"
    where = "centre" if pos and ("正中" in pos or "中间" in pos) else "just left of centre"
    return f"one empty seat in the {row} row {where}"


def _join_cn(*parts: str) -> str:
    return "，".join(x.strip("。，, ") for x in parts if x) + "。"


def _join_en(*parts: str) -> str:
    return ", ".join(x.strip(" ,.") for x in parts if x)


def strip_mj(en: str) -> tuple[str, str]:
    """Midjourney prompt -> (plain text, the --no list), for image APIs that take no MJ params."""
    m = re.search(r"\s--(ar|style|stylize|no|sref|iw|oref)\b", en)
    if not m:
        return en.strip(), ""
    n = re.search(r"--no\s+(.*?)(\s--\w+|$)", en[m.start():])
    return en[:m.start()].strip(" ,"), (n.group(1).strip() if n else "")


def plate_prompts(ep: Episode, p: Plate) -> dict:
    """cn (即梦图片生成), en (Midjourney), gpt (plain prompt for GPT Image via OpenRouter)."""
    fr_cn, fr_en = cinema.FRAMINGS[p.framing]
    lens_cn, lens_en = cinema.LENSES[p.lens]
    arena_cn = "同一个场馆的同一套布景：" + ep.venue.cn.strip("。 ") + "；" + LED_BLANK_CN
    arena_en = "the same arena set in every plate: " + (ep.venue.en or ep.venue.cn).strip(" .") + "; " + LED_BLANK_EN
    crowd_cn = {"full": f"{ep.crowd_cn.strip('。，, ')}，{DENSE_CN}：{DENSE_PEOPLE_CN}", "bokeh": BOKEH_CN,
                "dark": DARK_CN}[p.crowd]
    crowd_en = {"full": DENSE_EN, "bokeh": BOKEH_EN, "dark": DARK_EN}[p.crowd]
    light_cn, light_en = (DARK_LIGHT_CN, DARK_LIGHT_EN) if p.crowd == "dark" else (LIGHT_CN, LIGHT_EN)
    seats_cn = seats_en = ""
    if p.file == "cameo_seats.png":
        pos = [ep.cast[k].position_cn for k in ep.members("cameo")] or [""]
        seats_cn = ("、".join(f"{cameo_seat_cn(x)}留一个空座位" for x in dict.fromkeys(pos))
                    + "（后面客串角色会坐进去），除此之外所有座位都坐满了人")
        seats_en = ("exactly " + " and ".join(_seat_en(x) for x in dict.fromkeys(pos))
                    + " left free for a later guest, every other seat taken")
    guide_cn = (f"图1是已经锁定的场景图 {p.guide}：保持同一个场馆、同样的布景、灯光、配色和看台样式，只换成下面的机位"
                if p.guide else "")
    cn = _join_cn(guide_cn, fr_cn, lens_cn, p.angle_cn, p.scene_cn, arena_cn, crowd_cn, seats_cn, light_cn, REAL_CN,
                  NO_TEXT_CN)
    body_en = _join_en(f"{fr_en}, {lens_en}", p.angle_en, p.scene_en, arena_en, crowd_en, seats_en, light_en, REAL_EN,
                       NO_TEXT_EN)
    neg = cinema.negative_en(ep.realism) + ("" if p.crowd == "dark" else ", " + EMPTY_NEG_EN)
    sref = " --sref <场景图链接>" if p.guide else ""
    en = f"{body_en} --ar {p.aspect} --style raw --stylize 60{sref} --no {neg}"
    text, avoid = strip_mj(en)
    gpt = ""
    if p.guide:
        gpt = (f"The first input image is the locked plate of the same arena ({p.guide}): keep the same stage, floor "
               "graphic, LED wall, light strips, palette and seating, only the camera position changes. ")
    gpt += f"{text}. Landscape {p.aspect}. Avoid: {avoid}."
    return {"cn": cn, "en": en, "gpt": gpt}


# --------------------------------------------------------------------------- cost (no generation)


def ledger_image_usd(ledger: Path) -> list[float]:
    """Real per-image USD of finished OpenRouter image calls in ledger.jsonl (read only)."""
    out = []
    p = Path(ledger)
    if not p.is_file():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("kind") == "image" and d.get("provider") == "openrouter" and d.get("real_usd"):
            out.append(float(d["real_usd"]))
    return out


def cost_estimate(files: list[str], candidates: int = CANDIDATES, per_image: float = PLATE_USD,
                  upper: float = PLATE_USD_UPPER) -> dict:
    """Per-plate and total USD for `candidates` images per plate; pure arithmetic, no API call."""
    rows = [{"file": f, "candidates": candidates, "usd": round(candidates * per_image, 2),
             "usd_upper": round(candidates * upper, 2)} for f in files]
    return {"rows": rows, "images": candidates * len(files), "per_image": per_image, "upper": upper,
            "total": round(candidates * per_image * len(files), 2),
            "total_upper": round(candidates * upper * len(files), 2)}


def per_image_from_ledger(ledger: Path) -> float:
    """The highest real price seen, rounded up to the cent; PLATE_USD when the ledger has none."""
    seen = ledger_image_usd(ledger)
    return max(PLATE_USD, round(max(seen) + 0.005, 2)) if seen else PLATE_USD
