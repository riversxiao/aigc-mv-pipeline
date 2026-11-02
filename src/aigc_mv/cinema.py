"""Film language library: framings, lenses, camera moves, look presets and the realism ("de-AI") rules.

This module is pure data + tiny helpers. The board planner picks from it; the prompt builders paste its
sentences verbatim. Edit wording here, not inside prompts.

Sources of the rules (see docs/方法论.md):
- claudia.gallery wiki: one calm classical move per shot with a start, a direction and an end; moves answer
  audible sounds; never orbit everything; downscale stills; no learned upscalers; grade in post.
- ancient-rap-battle pitfalls: fixed stage sides, mouth visible, one hand always on the mic, faces drift on
  turns / walks / wide pull-backs.
- Reference films: Keynes vs Hayek ("Fear the Boom and Bust": wide lens close to the face, direct address,
  real locations, the rival present in frame) and 火影有嘻哈 (variety-show multicam: long-lens close-ups with
  the crowd melted into bokeh, reaction cams, a performer pointing into the lens).
"""

from __future__ import annotations

from dataclasses import dataclass, field

# --------------------------------------------------------------------------- framing & lens

FRAMINGS: dict[str, tuple[str, str]] = {
    # key: (中文, english)
    "ECU": ("大特写，只拍眼睛到嘴", "extreme close-up"),
    "CU": ("特写，头和肩膀", "close-up"),
    "MCU": ("近景，胸口以上", "medium close-up, chest up"),
    "MS": ("中景，腰以上", "medium shot, waist up"),
    "MWS": ("中全景，膝盖以上", "medium wide shot, knees up"),
    "WS": ("全景", "wide shot"),
    "OTS": ("过肩镜头", "over-the-shoulder shot"),
    "2S": ("双人镜头，两人都在画面里", "two-shot"),
}

LENSES: dict[str, tuple[str, str]] = {
    "24w": ("24mm 广角镜头离人物很近，人物几乎贴着镜头，背景有自然的广角透视",
            "24mm wide lens very close to the face, natural wide-angle perspective"),
    "35": ("35mm 镜头，纪实感，人物和环境都看得清", "35mm lens, documentary feel"),
    "50": ("50mm 标准镜头", "50mm lens"),
    "85": ("85mm 镜头，浅景深，背景柔和虚化", "85mm lens, shallow depth of field"),
    "135": ("135mm 长焦镜头，空间被压缩，背景的观众和灯虚成大片光斑，像综艺直播的长焦机位",
            "135mm telephoto, compressed space, crowd and lights melted into large bokeh, broadcast long-lens camera"),
    "200": ("200mm 长焦镜头从远处偷拍，前景有虚化的人头", "200mm telephoto from far back, out-of-focus heads in the foreground"),
}

# framing -> lens choices per grammar (first is the default)
LENS_FOR: dict[str, dict[str, list[str]]] = {
    "show": {"ECU": ["135", "85"], "CU": ["135", "85"], "MCU": ["85", "135"], "MS": ["50", "85"],
             "MWS": ["35", "50"], "WS": ["24w", "35"], "OTS": ["85", "135"], "2S": ["50", "35"]},
    "mv": {"ECU": ["50", "85"], "CU": ["24w", "50"], "MCU": ["24w", "35"], "MS": ["24w", "35"],
           "MWS": ["35", "24w"], "WS": ["24w", "35"], "OTS": ["35", "50"], "2S": ["24w", "35"]},
}

# --------------------------------------------------------------------------- camera moves


@dataclass(frozen=True)
class Move:
    id: str
    cn: str
    en: str
    energy: int  # 0 calm, 1 driving, 2 accent
    framings: tuple[str, ...]
    grammars: tuple[str, ...] = ("show", "mv")
    sung_ok: bool = True  # safe while the mouth must stay readable
    max_per_film: int = 99
    note: str = ""


MOVES: dict[str, Move] = {m.id: m for m in [
    Move("locked", "机位固定在三脚架上不动，只有极轻微的呼吸感漂移",
         "locked-off on a tripod, only a barely perceptible drift", 0,
         ("ECU", "CU", "MCU", "MS", "2S", "WS", "MWS")),
    Move("push_slow", "镜头从起幅开始缓慢、平稳地向前推近，落幅时比起幅近一个景别",
         "slow steady dolly push-in, ending one shot size tighter", 0,
         ("CU", "MCU", "MS", "MWS", "2S", "WS")),
    Move("tele_float", "长焦机位跟拍，镜头随人物轻微漂移、微调构图，像直播摄像师在操作",
         "long-lens operator shot, the frame floats gently with the performer like a broadcast camera", 1,
         ("ECU", "CU", "MCU", "OTS"), ("show",)),
    Move("handheld", "肩扛手持跟拍，有真实的呼吸感和轻微晃动，镜头跟着人物的动作走，但不剧烈",
         "shoulder-mounted handheld, real breathing sway, follows the action, never shaky", 1,
         ("CU", "MCU", "MS", "2S", "OTS")),
    Move("truck", "镜头在轨道上横向平移，和人物保持平行，前景有东西划过",
         "lateral dolly track parallel to the performer, foreground elements slide past", 1,
         ("MCU", "MS", "MWS", "2S")),
    Move("arc_short", "镜头以人物为中心沿弧线缓慢绕行约 30 度，只在人物正面一侧移动，绝不绕到背后",
         "slow 30-degree arc around the performer, staying on the face side, never behind", 1,
         ("MCU", "MS", "2S"), max_per_film=4, note="orbits everywhere read as AI; ration them"),
    Move("rack_focus", "前景是虚焦的{fg}，焦点从前景慢慢转移到{who}的脸上",
         "foreground {fg_en} out of focus, focus racks to {who_en}'s face", 0,
         ("CU", "MCU", "MS", "OTS")),
    Move("ots_drift", "越过{other}虚化的肩膀拍{who}，镜头缓慢向侧面漂移",
         "over {other_en}'s blurred shoulder onto {who_en}, slow sideways drift", 0, ("OTS",)),
    Move("low_push", "低机位仰拍，缓慢推近，画面上方看得到吊灯和灯光",
         "low angle looking up, slow push-in, practical lights visible above", 1,
         ("MCU", "MS", "MWS"), max_per_film=6),
    Move("tilt_reveal", "镜头从{who}手里的道具缓慢上摇到脸上，落幅是脸",
         "slow tilt up from the prop in {who_en}'s hand to the face", 1, ("MCU", "MS"), sung_ok=False),
    Move("whip_in", "镜头从画面一侧快速甩过来，停稳在{who}脸上，之后保持稳定",
         "fast whip pan in from the side, settles on {who_en}'s face and holds", 2,
         ("CU", "MCU", "MS"), max_per_film=4),
    Move("snap_zoom", "前面镜头稳定，最后半秒镜头急速变焦推到大特写，像综艺节目抓爆点",
         "steady, then a fast snap zoom into an extreme close-up in the last half second", 2,
         ("MCU", "MS", "2S"), ("show",), max_per_film=5, note="punchlines only"),
    Move("crane_up", "摇臂从人群头顶高度缓慢升起，越过观众俯瞰整个舞台",
         "crane rises slowly over the crowd's heads to look down on the whole stage", 1,
         ("WS",), sung_ok=False, max_per_film=3),
    Move("crane_in", "摇臂从高处缓慢下降并推向舞台，落幅是两人对峙",
         "crane descends from high and pushes toward the stage, ends on the two rivals face to face", 1,
         ("WS", "MWS"), sung_ok=False, max_per_film=2),
    Move("pull_reveal", "从特写缓慢拉远，露出{who}身后的{reveal}",
         "slow pull back from close-up revealing {reveal_en} behind {who_en}", 1,
         ("MCU", "MS"), sung_ok=False, max_per_film=3, note="pull-backs drift faces; keep short"),
    Move("steadicam", "稳定器在{who}前方倒退引导拍摄，{who}一边往前走一边对着镜头说唱",
         "steadicam leads backwards while {who_en} walks toward camera rapping", 1,
         ("MS", "MWS"), ("mv",), max_per_film=3, note="walking drifts faces: medium shots only"),
]}

# Which moves suit which beat of the stanza (planner hint)
STANZA_ROLE_MOVES = {
    "open": ["whip_in", "push_slow", "low_push", "steadicam", "truck"],
    "mid": ["tele_float", "handheld", "truck", "rack_focus", "ots_drift", "arc_short", "locked"],
    "punch": ["snap_zoom", "low_push", "push_slow", "whip_in"],
    "react": ["tele_float", "locked", "rack_focus", "handheld"],
    "crowd": ["crane_up", "handheld", "tele_float"],
    "cutaway": ["push_slow", "truck", "pull_reveal", "tilt_reveal", "handheld", "locked"],
}

# --------------------------------------------------------------------------- realism rules

REALISM_CN = (
    "真实电影实拍质感，像用电影摄影机在真实场景里拍的历史片现场，不是 CG、不是游戏、不是动画。"
    "人物是真实的成年演员：皮肤有毛孔、细纹、汗光、晒斑和不均匀的肤色，胡茬和碎发清楚，五官有自然的不对称；"
    "不磨皮、不加滤镜，长相像普通人而不是模特，皮肤不能光滑得像塑料、蜡像或瓷器。"
    "服装是真实的布料、皮革和金属，有褶皱、磨损、灰尘和使用痕迹。"
)
MOTION_CN = (
    "动作是正常速度，有重量和惯性：说唱时胸口和肩膀随呼吸起伏，会眨眼、吞咽、皱眉，衣服和头发随动作自然摆动；"
    "不要慢动作，不要漂浮感，不要突然变形。"
)
CAMERA_REAL_CN = "镜头像真实摄影师在操作：起幅和落幅清楚，运动有加速和减速，焦点跟着人物。"
NO_TEXT_CN = "画面里没有字幕、文字、水印和标志。不要卡通、动漫、3D 渲染、游戏 CG、过度锐化、过饱和。"

REALISM_EN = (
    "real adult actor, natural skin texture with visible pores, fine lines, uneven skin tone, light sweat, "
    "natural facial asymmetry, worn and creased costume fabric, no retouching"
)
NO_EN = "cgi, 3d render, plastic skin, airbrushed, smooth skin, doll, porcelain, anime, illustration, beauty filter, idol, oversaturated, text, letters, logo, watermark"

# Words that pull image/video models toward the glossy AI look. The audit flags them in prompts.
BANNED_WORDS = [
    "唯美", "绝美", "精致五官", "完美", "仙气", "仙侠", "帅气", "美颜", "网红", "偶像", "高颜值", "惊艳", "梦幻",
    "flawless", "perfect skin", "beautiful", "handsome", "gorgeous", "stunning", "idol", "masterpiece",
    "8k", "hyper-detailed", "ultra detailed", "octane", "unreal engine", "trending on artstation",
]


@dataclass(frozen=True)
class Look:
    id: str
    cn: str  # light + film block for video prompts
    en: str  # style family tail for stills
    practicals_cn: str
    grade: dict = field(default_factory=dict)  # post look, see edit.LOOK_DEFAULT


LOOKS: dict[str, Look] = {lk.id: lk for lk in [
    Look(
        "night_arena",
        "夜晚，光线来自画面里真实存在的火盆、灯笼和头顶一盏冷白色追光，暖色火光和冷色追光混在一起，空气里有薄烟；"
        "亮部有轻微光晕，暗部保留细节，不是每个人都打轮廓光。35mm 电影胶片质感，细腻颗粒，镜头有一点老镜头的柔和。",
        "night, lit only by practical braziers, paper lanterns and one cold overhead follow spot, haze in the air, "
        "photographed on 35mm motion picture film, Kodak Vision3 500T, gentle halation, fine grain, vintage lens softness",
        "火盆、灯笼和头顶的追光",
        {"warm": 0.02},
    ),
    Look(
        "palace_day",
        "白天，阳光从高窗斜射进大殿，灰尘在光束里飘，室内其余地方靠反光照亮，色彩克制偏暖；"
        "35mm 电影胶片质感，细腻颗粒，高光柔和不过曝。",
        "daylight through high palace windows, dust in the light shafts, soft bounce fill, restrained warm palette, "
        "photographed on 35mm film, Kodak Vision3 250D, fine grain",
        "高窗射进来的阳光",
        {"warm": 0.015},
    ),
    Look(
        "battlefield_dusk",
        "黄昏的战场，低角度的夕阳逆光，尘土和烟雾，远处有火光；色彩偏橙和灰蓝，"
        "35mm 电影胶片质感，颗粒明显，像战争片的实拍。",
        "battlefield at dusk, low backlit sun through dust and smoke, distant fires, orange and slate-blue palette, "
        "photographed on 35mm film, visible grain, war-film realism",
        "夕阳和远处的火光",
        {"warm": 0.03},
    ),
    Look(
        "tv_arena",
        "室内说唱综艺的比赛现场：观众席层层叠叠，红色灯牌和舞台灯在背景里虚成光斑，主光是舞台上方的硬光，"
        "像综艺节目的直播画面但更有电影感，细腻颗粒。",
        "indoor rap battle TV show arena, tiered crowd, red light boxes and stage lights melted into bokeh, "
        "hard top stage light, broadcast realism with cinematic grain",
        "舞台顶光和观众席的灯牌",
        {"warm": 0.0},
    ),
]}


def lens_for(grammar: str, framing: str, i: int = 0) -> str:
    g = "show" if grammar == "show" else "mv"
    choices = LENS_FOR[g].get(framing, ["35"])
    return choices[i % len(choices)]


def banned_hits(text: str) -> list[str]:
    low = text.lower()
    return [w for w in BANNED_WORDS if w.lower() in low]
