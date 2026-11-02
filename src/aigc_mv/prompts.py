"""Prompt builders: Seedance (即梦) video prompts per unit, still prompts for refs/plates, Suno sheets.

Video prompts are written like a script (claudia.gallery): labelled 【】 sections, the audio policy at the top
AND the bottom, blocking, then a timeline whose every half-line carries its own seconds to 0.01 s
(ancient-rap-battle: timed half-lines are what made the lips land first try). Duration / resolution /
aspect ratio go into the API request, never into the prompt.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aigc_mv import cinema
from aigc_mv.board import Board, BoardShot, Unit
from aigc_mv.canon import load_character
from aigc_mv.episode import Episode
from aigc_mv.schemas import Character
from aigc_mv.timing import Timing

AUDIO_COPY_CN = (
    "【音频】视频的声音就是 @音频1 本身：从第一帧到最后一帧原样保留，时间、音高、音量都不变。"
    "不要重新唱、不要重新配音、不要改快慢；不要加音乐、伴奏、音效、和声、旁白。"
)
AUDIO_RHYTHM_CN = (
    "【音频】@音频1 只是节奏参考，输出的声音就是 @音频1 原样，不加任何别的声音。"
    "画面里没有任何人唱歌或说话，所有人的嘴自然闭着，嘴不跟着音乐动。"
)
LIPSYNC_CN = (
    "【口型】嘴型逐字对上 @音频1：每个字的开口和收口都和 @音频1 里的声音同时发生，不早不晚；"
    "@音频1 没有声音的地方嘴自然闭上。唱的人嘴一直清楚可见，不被话筒、手、头发或道具挡住，"
    "话筒拿在嘴的斜下方；一只手始终握着话筒，动作只用空着的那只手。"
)
CORE_CN = (
    "【要求】1. 人物的脸、年龄、发型、胡子、帽子、服装全程和参考图一致，不变形、不变年轻；画面里每个人只出现一次。"
    "2. 解剖正常：脖子肩膀自然，手是五根手指，不多指、不粘连，四肢始终完整。"
    "3. 动作流畅、符合物理，没有抖动、闪烁、扭曲或融化。4. 只在分镜写到的时间切镜头，其余时间一个镜头不切。"
)


def characters(ep: Episode, knowledge_dir: Path | None = None) -> dict[str, Character]:
    out = {}
    for k, c in ep.cast.items():
        out[k] = load_character(c.character, knowledge_dir)
    return out


def _who_cn(ep: Episode, keys: list[str]) -> str:
    return "、".join(ep.cast[k].name_cn for k in keys)


def _move_text(ep: Episode, shot: BoardShot, who: str | None, other: str | None) -> str:
    m = cinema.MOVES[shot.camera]
    return m.cn.format(
        who=ep.cast[who].name_cn if who else "人物",
        other=ep.cast[other].name_cn if other else "对手",
        fg="观众举起的手和火把", reveal="整个舞台和台下的观众",
    )


def _beat_landing(timing: Timing, u: Unit, a: float, b: float) -> str:
    """'运镜从 X 秒的重拍开始，Y 秒停稳' – moves start on a downbeat and rest before the cut."""
    dbs = [d - u.song_t0 for d in timing.grid.downbeats]
    start = next((d for d in dbs if a - 0.01 <= d < b - 0.8), a)
    beat = timing.grid.beat
    end = max(start + 0.8, b - beat)
    return f"运镜从 {start:.1f} 秒开始，{end:.1f} 秒停稳"


def sides_cn(ep: Episode) -> str:
    left = next(c for c in ep.cast.values() if c.side == "left")
    right = next(c for c in ep.cast.values() if c.side == "right")
    return f"站位固定：{left.name_cn}永远在画面左边、身体朝右；{right.name_cn}永远在画面右边、身体朝左，谁都不换边。"


@dataclass
class UnitPrompt:
    unit: str
    uploads: list[tuple[str, str]]  # (file name in refs/, role sentence)
    audio: str | None
    duration: int
    text: str


def unit_refs(ep: Episode, board: Board, u: Unit) -> list[tuple[str, str]]:
    """Reference images by upload order, one role each (claudia.gallery: one image of a face per take)."""
    shots = board.unit_shots(u)
    present = []
    for s in shots:
        for w in s.who + ([s.singer] if s.singer and s.kind == "perform" else []):
            if w not in present:
                present.append(w)
    refs: list[tuple[str, str]] = []
    for w in present:
        nm = ep.cast[w].name_cn
        refs.append((f"{w}_sheet.png", f"是{nm}的定妆照（正面、侧面、表情），只用来认他的脸、发型和服装，不要把这张图当成画面出现"))
    loc = u.location
    if loc == "venue":
        refs.append(("venue.png", f"是场景：{ep.venue.cn}"))
    else:
        refs.append((f"loc_{loc}.png", f"是场景：{ep.locations[loc].cn}"))
    if any(s.kind in ("crowd", "establish") for s in shots):
        refs.append(("crowd.png", "是台下观众的样子（每个人长得都不一样）"))
    return refs


def video_prompt(ep: Episode, board: Board, timing: Timing, u: Unit,
                 chars: dict[str, Character]) -> UnitPrompt:
    look = cinema.LOOKS.get(ep.look, cinema.LOOKS["night_arena"])
    shots = board.unit_shots(u)
    uploads = unit_refs(ep, board, u)
    lines_by_idx = {ln.idx: ln for ln in timing.lines}
    who_all = []
    for s in shots:
        for w in s.who + ([s.singer] if s.singer and s.kind == "perform" else []):
            if w not in who_all:
                who_all.append(w)

    ref_text = "【参考图】" + "".join(f"@图片{i}{role}。" for i, (_, role) in enumerate(uploads, 1))
    people = []
    for w in who_all:
        c = chars[w]
        bits = [c.identity_cn or c.identity, c.wardrobe_cn or c.wardrobe_default, c.props_cn]
        people.append(f"{ep.cast[w].name_cn}：" + "；".join(b.strip("。 ") for b in bits if b) + "。")
    people_txt = "【人物】" + "".join(people) + (sides_cn(ep) if len(ep.cast) == 2 else "")

    loc_full = ep.venue.cn if u.location == "venue" else ep.locations[u.location].cn
    loc_name = loc_full.replace("；", "，").split("，")[0]
    timeline = []
    for k, s in enumerate(shots, 1):
        a, b = s.t0 - u.song_t0, s.t1 - u.song_t0
        if k == len(shots):
            b = u.duration
        fr = cinema.FRAMINGS[s.framing][0]
        lens = cinema.LENSES[s.lens][0]
        other = ep.other(s.singer) if s.singer else None
        focus = s.who[0] if s.kind == "react" and s.who else (s.singer or (s.who[0] if s.who else None))
        move = _move_text(ep, s, focus, ep.other(focus) if focus else None)
        land = _beat_landing(timing, u, a, b)
        head = f"镜头{k}（{a:.1f}–{b:.1f} 秒）：{fr}，{lens}；运镜：{move}，{land}。"
        if s.kind == "perform":
            ln = lines_by_idx[s.lines[0]]
            sung = []
            for ph in ln.phrases:
                p0, p1 = ph.t0 - u.song_t0, ph.t1 - u.song_t0
                if p1 <= a + 0.05 or p0 >= b - 0.3:
                    continue
                sung.append(f"{max(p0, 0):.2f}–{min(p1, u.duration - 0.02):.2f} 秒「{ph.text}」")
            singer = ep.cast[s.singer].name_cn
            if s.grammar == "mv" or s.role == "open" or s.lens == "24w":
                facing = "转过来直接对着镜头说唱，像在冲着台下观众喊话"
            else:
                facing = f"对着{ep.cast[other].name_cn}说唱"
            listen = ""
            if other in s.who:
                listen = f"{ep.cast[other].name_cn}只听不说，嘴一直闭着，{ep.cast[other].listen_cn}。"
            timeline.append(head + f"{singer}{facing}，唱：" + "，".join(sung)
                            + f"，嘴型逐字对上 @音频1 这几秒的声音；{singer}边唱边{s.action_cn}。" + listen)
        elif s.kind == "react":
            nm = _who_cn(ep, s.who)
            voice = f"{ep.cast[s.singer].name_cn}的声音在画外继续，" if s.singer else ""
            timeline.append(head + f"{nm}的反应镜头：{voice}{nm}嘴一直闭着，不说不唱，{s.action_cn}。")
        else:
            timeline.append(head + s.action_cn + "。")

    if u.kind == "sung":
        singer = ep.cast[u.singer].name_cn
        goal = f"【目标】{loc_name}，{singer}在说唱对决里正面开火，一镜一句、动作照歌词字面演。"
        body = [AUDIO_COPY_CN, goal, ref_text, people_txt, "【分镜】", *timeline, LIPSYNC_CN,
                "【画面】" + look.cn + "真实实拍质感：真实的成年演员，皮肤有毛孔、细纹和汗光，不磨皮、不加滤镜。动作正常速度、有重量感，不要慢动作。",
                CORE_CN + cinema.NO_TEXT_CN, AUDIO_COPY_CN]
    else:
        goal = f"【目标】{loc_name}。" + (shots[0].note or "")
        body = [AUDIO_RHYTHM_CN if u.audio == "instrumental" else "【音频】无声视频。", goal, ref_text,
                people_txt if who_all else "", "【分镜】", *timeline,
                "【画面】" + look.cn + cinema.REALISM_CN + cinema.MOTION_CN + cinema.CAMERA_REAL_CN,
                CORE_CN + cinema.NO_TEXT_CN,
                AUDIO_RHYTHM_CN if u.audio == "instrumental" else ""]
    text = "\n\n".join(x for x in body if x)
    audio = f"{u.id}_{'vocal' if u.audio == 'vocal' else 'inst'}.wav" if u.audio != "none" else None
    return UnitPrompt(unit=u.id, uploads=uploads, audio=audio, duration=u.duration, text=text)


# --------------------------------------------------------------------------- stills (refs & plates)


def still_prompt_en(ep: Episode, char: Character | None, framing: str, lens: str, scene: str,
                    ar: str = "16:9") -> str:
    """Midjourney order: framing+lens → identity verbatim → wardrobe → scene → light/film → realism → ban."""
    look = cinema.LOOKS.get(ep.look, cinema.LOOKS["night_arena"])
    ident = ""
    if char:
        ident = char.identity_short if framing in ("WS", "MWS") and char.identity_short else char.identity
    parts = [
        f"{cinema.FRAMINGS[framing][1]}, {cinema.LENSES[lens][1]}",
        ident.strip(),
        (char.wardrobe_default.strip() if char else ""),
        scene.strip(),
        look.en,
        cinema.REALISM_EN if char else "",
        "no text, no letters, no logos",
    ]
    p = ", ".join(x for x in parts if x)
    return f"{p} --ar {ar} --style raw --stylize 60 --no {cinema.NO_EN}"


def still_prompt_cn(ep: Episode, char: Character | None, framing: str, lens: str, scene_cn: str) -> str:
    """即梦 / Seedream 图片版：同样的顺序，中文。"""
    look = cinema.LOOKS.get(ep.look, cinema.LOOKS["night_arena"])
    parts = [cinema.FRAMINGS[framing][0], cinema.LENSES[lens][0]]
    if char:
        parts += [char.identity_cn or char.identity, char.wardrobe_cn or char.wardrobe_default, char.props_cn]
    parts += [scene_cn, look.cn]
    if char:
        parts.append(cinema.REALISM_CN)
    parts.append("电影剧照，无文字、无水印、无标志")
    return "，".join(x.strip("。，, ") for x in parts if x) + "。"


def refs_plan(ep: Episode, board: Board, chars: dict[str, Character]) -> list[dict]:
    """Every image the episode needs, with file name, use and both prompt languages."""
    out = []
    for k, c in ep.cast.items():
        ch = chars[k]
        facing = "three-quarters to the right" if c.side == "left" else "three-quarters to the left"
        out.append({
            "file": f"{k}_sheet.png", "use": f"{c.name_cn} 定妆：所有含{c.name_cn}的生成都上传（只认脸，不当画面）",
            "en": ("character reference sheet of the same man on a plain mid-grey seamless backdrop, soft even studio "
                   "light: a front head-and-shoulders portrait, a three-quarter view, a profile, and a waist-up view "
                   f"{facing} holding a silver corded microphone, " + ch.identity + ", " + ch.wardrobe_default
                   + ", " + cinema.REALISM_EN + ", photographed on 35mm film, fine grain, no text, no letters, no logos"
                   + f" --ar 16:9 --style raw --stylize 50 --no {cinema.NO_EN}"),
            "cn": still_prompt_cn(ep, ch, "MS", "50", f"中灰色无缝背景布，柔和均匀的影棚光，同一个人的正面头肩、四分之三侧面、"
                                  f"正侧面和一张{'朝右' if c.side == 'left' else '朝左'}的半身照，四格拼在一张图里"),
        })
    scenes = [("venue.png", "主场景（正面、对称、平视；开场推镜头要正对着推）", ep.venue)]
    scenes += [(f"loc_{k}.png", f"叙事场景：{v.cn}", v) for k, v in ep.locations.items()]
    for f, use, loc in scenes:
        out.append({
            "file": f, "use": use,
            "en": still_prompt_en(ep, None, "WS", "35",
                                  "symmetrical straight-on view at eye level, level horizon, nobody in frame, "
                                  + (loc.en or loc.cn)),
            "cn": still_prompt_cn(ep, None, "WS", "35", "正面对称平视，地平线水平，画面里没有人，" + loc.cn),
        })
    out.append({
        "file": "crowd.png", "use": "观众（开场、间奏、片尾）",
        "en": still_prompt_en(ep, None, "MS", "50",
                              "a packed crowd of about twenty people aged 18 to 60 with clearly different faces, "
                              "builds and clothes, cheering toward the stage, " + (ep.venue.en or ep.venue.cn)),
        "cn": still_prompt_cn(ep, None, "MS", "50", ep.crowd_cn + "，大约二十个人，年龄和长相各不相同，冲着舞台欢呼"),
    })
    # first frames for motion units (cutaways etc.): one still per shot, never reused
    for u in board.units:
        if u.kind != "motion":
            continue
        s = board.unit_shots(u)[0]
        char = chars.get(s.who[0]) if s.who else None
        loc = ep.venue if s.location == "venue" else ep.locations[s.location]
        out.append({
            "file": f"plate_{u.id}.png", "use": f"{u.id} 首帧（{s.section} · {s.kind}）",
            "en": still_prompt_en(ep, char, s.framing, s.lens, f"{s.action_cn}; {loc.en or loc.cn}"),
            "cn": still_prompt_cn(ep, char, s.framing, s.lens, f"{s.action_cn}，{loc.cn}"),
        })
    return out


# --------------------------------------------------------------------------- Suno


def suno_sheets(ep: Episode, chars: dict[str, Character]) -> str:
    """Two-pass Suno plan (A first, then Extend with B) so the two voices really differ."""
    style_base = ("Chinese battle rap, old school boom bap, {bpm} BPM, dark cinematic, hard punchy drums, vinyl scratches, "
                  "guqin and pipa samples, war drums, deep sub bass, live crowd hype, clear Mandarin diction")
    bpm = int(ep.bpm_hint or 92)
    out = [f"# Suno · {ep.title}", "",
           "设置：Advanced · Variety 0 · Weirdness 35% · Style Influence 70% · 不选 Voice/Persona。",
           "先生成第一段（前奏 + 第一位），挑一条后 Extend，Extend from 设在第一位最后一个字唱完处，再填第二段。",
           "生僻字在 Suno 栏写同音字（sung_as），字幕保留原字。拿到歌后用 Suno 自带的 stem 分离导出人声和伴奏。", ""]
    for vi, v in enumerate(ep.verses):
        c = ep.cast[v.who]
        voice = c.voice or chars[v.who].voice or "confident male rapper"
        lyr = "\n".join((ln.sung_as or ln.text) for ln in v.lines)
        head = "[Intro: 1 bar DJ scratch]\n\n" if vi == 0 else (
            f"[Break: 2 bars, crowd chanting]\n{(ep.break_chant + ' ') * 4}\n\n" if ep.break_chant else "[Break: 2 bars]\n\n")
        tail = f"\n\n[Outro: crowd chanting]\n{(c.name_cn + ' ') * 3}\n[End]" if vi == len(ep.verses) - 1 else ""
        out += [f"## 第 {vi + 1} 段 · {c.name_cn}", "", "Styles:", "```",
                style_base.format(bpm=bpm) + f", solo {voice}, {'very short intro' if vi == 0 else 'short ending'}",
                "```", "Lyrics:", "```", f"{head}[Verse {vi + 1}: {c.name_en or c.name_cn}]\n{lyr}{tail}", "```", ""]
    return "\n".join(out) + "\n"
