"""Prompt builders: Seedance (即梦) video prompts per unit, still prompts for refs/plates, Suno sheets.

Video prompts are written like a script (claudia.gallery): labelled 【】 sections, the audio policy at the top
AND the bottom, blocking, then a timeline whose every half-line carries its own seconds to 0.01 s
(ancient-rap-battle: timed half-lines are what made the lips land first try). Duration / resolution /
aspect ratio go into the API request, never into the prompt.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aigc_mv import cinema, plates
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


# Sung show units only: the same camera moves and long lenses in fewer words (long sung prompts make Seedance
# re-sing instead of copying the audio). Moves missing here keep their full text.
SHORT_MOVE_CN = {
    "locked": "固定机位，几乎不动",
    "push_slow": "缓慢平稳地推近一个景别",
    "tele_float": "长焦跟拍，随人物轻微漂移",
    "handheld": "肩扛手持跟拍，轻微晃动，不剧烈",
    "snap_zoom": "前面稳定，最后半秒急推到大特写",
}
SHORT_LENS_CN = {
    "24w": "24mm 广角贴近人物",
    "135": "135mm 长焦，空间压缩，背景虚成大片光斑",
}
# Sung show units always upload at least one locked environment plate: the venue look is carried by it.
SHOW_PLATE_LOOK_CN = "场馆、擂台、灯光和配色照场景图；像电视直播画面但有电影感，细腻颗粒。"


def _move_text(ep: Episode, shot: BoardShot, who: str | None, other: str | None, short: bool = False) -> str:
    m = cinema.MOVES[shot.camera]
    if short and shot.camera in SHORT_MOVE_CN:
        return SHORT_MOVE_CN[shot.camera]
    return m.cn.format(
        who=ep.cast[who].name_cn if who else "人物",
        other=ep.cast[other].name_cn if other else "对手",
        fg="观众举起的灯牌和手" if ep.format == "show" else "观众举起的手和火把", reveal="整个舞台和台下的观众",
    )


def _beat_landing(timing: Timing, u: Unit, a: float, b: float) -> str:
    """'运镜从 X 秒的重拍开始，Y 秒停稳' – moves start on a downbeat and rest before the cut."""
    dbs = [d - u.song_t0 for d in timing.grid.downbeats]
    start = next((d for d in dbs if a - 0.01 <= d < b - 0.8), a)
    beat = timing.grid.beat
    end = max(start + 0.8, b - beat)
    return f"运镜从 {start:.1f} 秒开始，{end:.1f} 秒停稳"


def sides_cn(ep: Episode) -> str:
    left, right = (ep.cast[k] for k in ep.rappers())
    return f"站位固定：{left.name_cn}永远在画面左边、身体朝右；{right.name_cn}永远在画面右边、身体朝左，谁都不换边。"


@dataclass
class UnitPrompt:
    unit: str
    uploads: list[tuple[str, str]]  # (file name in refs/, role sentence)
    audio: str | None
    duration: int
    text: str


ROLE_CN = {"rapper": "选手", "teammate": "队友", "judge": "评委", "host": "主持", "dj": "DJ", "hook": "副歌",
           "cameo": "客串"}
# 即梦 Seedance 2.0「全能参考」: at most 9 images per generation (plus up to 3 videos and 3 audio, 12 files in
# all). Check again when the API field spec arrives (docs/接口对接.md).
MAX_UPLOADS = 9
MAX_FACE_REFS = 6  # one sheet per person; leaves room for the environment plates (plates.MAX_UNIT_PLATES)


def _show_people(board_shots: list[BoardShot]) -> tuple[list[str], list[str]]:
    """(foreground in order singer -> others, background teammates) of a show unit."""
    singers, fg, bg = [], [], []
    for s in board_shots:
        if s.singer and s.singer in s.who and s.singer not in singers:
            singers.append(s.singer)
        for w in s.who:
            if w not in fg:
                fg.append(w)
    fg = singers + [w for w in fg if w not in singers]
    for s in board_shots:
        for w in s.background:
            if w not in fg and w not in bg:
                bg.append(w)
    return fg, bg


def show_unit_uploads(ep: Episode, board: Board, u: Unit) -> tuple[list[tuple[str, str]], list[str]]:
    """(uploads, warnings) of a show unit: one sheet per person (singer first, background crew last), then the
    environment plates of its stagings (plates.pick_unit_plates). Over MAX_UPLOADS, background people go first,
    then extra plates; one plate always stays."""
    shots = board.unit_shots(u)
    fg, bg = _show_people(shots)
    warn: list[str] = []
    people = (fg + bg)[:MAX_FACE_REFS]
    if len(fg + bg) > MAX_FACE_REFS:
        warn.append("more than %d people, not uploaded: %s" % (MAX_FACE_REFS, ", ".join((fg + bg)[MAX_FACE_REFS:])))
    env, dropped = plates.pick_unit_plates(ep, shots)
    if dropped:
        warn.append("plates over %d per unit, not uploaded: %s" % (plates.MAX_UNIT_PLATES,
                                                                  ", ".join(p.file for p in dropped)))
    while len(people) + len(env) > MAX_UPLOADS and any(w in bg for w in people):
        w = next(w for w in reversed(people) if w in bg)
        people.remove(w)
        warn.append(f"over {MAX_UPLOADS} uploads: background {w}_sheet.png dropped")
    while len(people) + len(env) > MAX_UPLOADS and len(env) > 1:
        warn.append(f"over {MAX_UPLOADS} uploads: plate {env.pop().file} dropped")
    while len(people) + len(env) > MAX_UPLOADS:
        warn.append(f"over {MAX_UPLOADS} uploads: {people.pop()}_sheet.png dropped")
    refs: list[tuple[str, str]] = []
    for w in people:
        c = ep.cast[w]
        role = f"是{c.name_cn}（{ROLE_CN[c.role]}）的锁定定妆图（正侧面和全身），只用来认脸、发型和服装，不要把这张图当成画面出现"
        if w in bg:
            role += f"；{c.name_cn}只在背景里虚化出现"
        refs.append((f"{w}_sheet.png", role))
    refs += [(p.file, plates.upload_role(p)) for p in env]
    return refs, warn


def _show_unit_refs(ep: Episode, board: Board, u: Unit) -> list[tuple[str, str]]:
    return show_unit_uploads(ep, board, u)[0]


def upload_warnings(ep: Episode, board: Board, u: Unit) -> list[str]:
    return show_unit_uploads(ep, board, u)[1] if ep.format == "show" else []


def unit_refs(ep: Episode, board: Board, u: Unit) -> list[tuple[str, str]]:
    """Reference images by upload order, one role each (claudia.gallery: one image of a face per take)."""
    if ep.format == "show":
        return _show_unit_refs(ep, board, u)
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


SHOW_SHEET_RULE_CN = "每人一张锁定定妆图（正侧面和全身），只用来认脸、发型和服装，不要把这些图当成画面出现"
SHOW_PLATE_RULE_CN = "只用来对齐场馆、灯光和观众席的样子，人物照定妆图，不要把场景图原样当成画面"


def _show_ref_text(ep: Episode, uploads: list[tuple[str, str]]) -> str:
    """【参考图】 of a show unit in two sentences: every @图片N named once, the identity-only rule and the
    background-only rule said once for all sheets and once for all plates (sung prompts must stay short)."""
    sheets, envs, other = [], [], []
    for i, (f, role) in enumerate(uploads, 1):
        key = f[: -len("_sheet.png")] if f.endswith("_sheet.png") else ""
        if key in ep.cast:
            c = ep.cast[key]
            sheets.append(f"@图片{i}是{c.name_cn}（{ROLE_CN[c.role]}）")
        elif f in plates.BY_FILE:
            envs.append(f"@图片{i}是场景图（{plates.BY_FILE[f].title_cn}）")
        else:
            other.append(f"@图片{i}{role}。")
    out = "【参考图】"
    if sheets:
        out += "，".join(sheets) + f"：{SHOW_SHEET_RULE_CN}。"
    if envs:
        out += "，".join(envs) + f"：{SHOW_PLATE_RULE_CN}。"
    return out + "".join(other)


def _show_person_cn(name: str, c: Character) -> str:
    """Foreground person of a show unit: the sheet carries face, hair and costume, so only age and sex (first
    clause of the card), the signature details and what the hands do are restated."""
    ident = (c.identity_cn or c.identity).replace(",", "，").split("，")[0].strip("。；; ")
    bits = [ident, c.signature_cn, c.props_cn]
    return f"{name}：" + "；".join(b.strip("。；; ") for b in bits if b) + "。"


def _show_goal(ep: Episode, u: Unit) -> str:
    show = ep.show_name or "节目"
    c = ep.cast[u.singer]
    if c.role == "rapper":
        rival = ep.cast[ep.other(u.singer)].name_cn
        return (f"【目标】{show}现场，{c.name_cn}在擂台上开唱，{rival}就在对面听着；"
                "像综艺节目的多机位直播，一镜一两句，被点名的人给反应镜头。")
    if c.role in ("host", "dj"):
        return f"【目标】{show}现场，{c.name_cn}在串场，像综艺节目的开场和串词，台下观众跟着起哄。"
    if c.role == "hook":
        return f"【目标】{show}现场，{c.name_cn}站在立麦前唱副歌，台上的人跟着节奏晃。"
    return f"【目标】{show}现场，{c.name_cn}开口说话，全场都看着。"


def _position_cn(ep: Episode, w: str) -> str:
    """'老夫子坐在评委席中间的王座，' for judges / cameos / teammates; '' for everyone else."""
    c = ep.cast[w]
    if c.role not in ("judge", "cameo", "teammate"):
        return ""
    pos = c.position_cn or (f"{ep.cast[c.team].name_cn}身后" if c.role == "teammate" and c.team else "")
    if not pos:
        return ""
    return f"{c.name_cn}{'站在' if c.role == 'teammate' else '坐在'}{pos}，"


def _cameo_seat_cn(ep: Episode, w: str, plate_idx: dict[str, int]) -> str:
    """'沙燕坐在观众席第二排靠中间偏左（@图片5 里留空的那个座位），左右和身后…' (same seat in every shot)."""
    c = ep.cast[w]
    n = plate_idx.get("cameo_seats.png")
    ref = f"（@图片{n} 里留空的那个座位）" if n else ""
    return (f"{c.name_cn}坐在{plates.cameo_seats(ep)[w]}{ref}，"
            "左右和身后坐满了不认识的普通观众，长相各不相同，都不是剧中角色；")


def _show_timeline(ep: Episode, timing: Timing, u: Unit, shots: list[BoardShot],
                   lines_by_idx: dict, plate_idx: dict[str, int] | None = None) -> list[str]:
    """Timeline of a variety-show unit: staging first, then who says / sings what, reactions by seat."""
    plate_idx = plate_idx or {}
    short = u.kind == "sung"
    out = []
    for k, s in enumerate(shots, 1):
        a, b = s.t0 - u.song_t0, s.t1 - u.song_t0
        if k == len(shots):
            b = u.duration
        fr = cinema.FRAMINGS[s.framing][0]
        lens = SHORT_LENS_CN.get(s.lens, cinema.LENSES[s.lens][0]) if short else cinema.LENSES[s.lens][0]
        visible_singer = s.singer if s.singer and s.singer in s.who else None
        focus = s.who[0] if s.kind == "react" and s.who else (visible_singer or (s.who[0] if s.who else None))
        move = _move_text(ep, s, focus, ep.other(focus) if focus else None, short=short)
        land = _beat_landing(timing, u, a, b)
        head = f"镜头{k}（{a:.1f}–{b:.1f} 秒）：{fr}，{lens}；运镜：{move}，{land}。"
        if s.staging in cinema.SHOW_STAGINGS:
            head += f"调度：{cinema.SHOW_STAGINGS[s.staging].cn}。"
        n_plate = plate_idx.get(plates.plate_for(ep, s.staging).file)
        if n_plate:
            head += f"背景照 @图片{n_plate}。"
        bg = ""
        if s.background:
            front = visible_singer or (s.who[0] if s.who else None)
            names = "、".join(ep.cast[w].name_cn for w in s.background)
            bg = (f"{names}站在{ep.cast[front].name_cn}身后，虚化在背景里，不抢画面。" if front
                  else f"{names}虚化在背景里，不抢画面。")
        if s.sung and s.lines and visible_singer:
            spoken = any(lines_by_idx[i].spoken for i in s.lines)
            verb = "说" if spoken else "唱"
            said = []
            for i in s.lines:
                for ph in lines_by_idx[i].phrases:
                    p0, p1 = ph.t0 - u.song_t0, ph.t1 - u.song_t0
                    if p1 <= a + 0.05 or p0 >= b - 0.3:
                        continue
                    said.append(f"{max(p0, 0):.2f}–{min(p1, u.duration - 0.02):.2f} 秒「{ph.text}」")
            if not said:
                said = [f"「{lines_by_idx[i].text}」" for i in s.lines]
            singer = ep.cast[visible_singer].name_cn
            listen = ""
            for w in s.who:
                if w == visible_singer:
                    continue
                c = ep.cast[w]
                if c.role == "rapper":
                    listen += f"{c.name_cn}只听不说，嘴一直闭着，{c.listen_cn}。"
                else:
                    listen += f"{c.name_cn}不说话，嘴闭着。"
            out.append(head + f"{singer}{verb}：" + "，".join(said)
                       + f"，嘴型逐字对上 @音频1 这几秒的声音；{singer}边{verb}边{s.action_cn}。" + listen + bg)
        elif s.kind == "react" and s.who:
            nm = _who_cn(ep, s.who)
            seat = "".join(_cameo_seat_cn(ep, w, plate_idx) if ep.cast[w].role == "cameo" else _position_cn(ep, w)
                           for w in s.who)
            voice = f"{ep.cast[s.singer].name_cn}的声音在画外继续，" if s.singer and s.lines else ""
            out.append(head + f"{seat}{nm}的反应镜头：{voice}{nm}嘴一直闭着，不说不唱，{s.action_cn}。" + bg)
        else:
            voice = f"{ep.cast[s.singer].name_cn}的声音在画外，" if s.singer and s.lines else ""
            mouths = "画面里的人嘴都闭着。" if s.lines and s.who else ""
            out.append(head + voice + s.action_cn + "。" + mouths + bg)
    return out


def video_prompt(ep: Episode, board: Board, timing: Timing, u: Unit,
                 chars: dict[str, Character]) -> UnitPrompt:
    look = cinema.LOOKS.get(ep.look, cinema.LOOKS["night_arena"])
    shots = board.unit_shots(u)
    uploads = unit_refs(ep, board, u)
    lines_by_idx = {ln.idx: ln for ln in timing.lines}
    show = ep.format == "show"
    who_all: list[str] = []
    bg: list[str] = []
    if show:
        fg, bg = _show_people(shots)
        who_all = fg + bg
    else:
        for s in shots:
            for w in s.who + ([s.singer] if s.singer and s.kind == "perform" else []):
                if w not in who_all:
                    who_all.append(w)

    if show:
        ref_text = _show_ref_text(ep, uploads)
    else:
        ref_text = "【参考图】" + "".join(f"@图片{i}{role}。" for i, (_, role) in enumerate(uploads, 1))
    people = []
    for w in who_all:
        c = chars[w]
        if show:  # the locked sheet carries the identity; blurred background people get one shared sentence
            if w not in bg:
                people.append(_show_person_cn(ep.cast[w].name_cn, c))
            continue
        bits = [c.identity_cn or c.identity, c.wardrobe_cn or c.wardrobe_default, c.props_cn]
        people.append(f"{ep.cast[w].name_cn}：" + "；".join(b.strip("。 ") for b in bits if b) + "。")
    rappers = ep.rappers()
    if show:
        sides = sides_cn(ep) if len(rappers) == 2 and any(w in rappers for w in who_all) else ""
    else:
        sides = sides_cn(ep) if len(ep.cast) == 2 else ""
    if show and bg:
        people.append(f"{_who_cn(ep, bg)}只在背景里虚化出现，长相和服装照定妆图。")
    people_txt = "【人物】" + "".join(people) + sides

    loc_full = ep.venue.cn if u.location == "venue" else ep.locations[u.location].cn
    loc_name = loc_full.replace("；", "，").split("，")[0]
    timeline = []
    crowd_txt = ""
    if show:
        plate_idx = {f: i for i, (f, _) in enumerate(uploads, 1) if f in plates.BY_FILE}
        timeline = _show_timeline(ep, timing, u, shots, lines_by_idx, plate_idx)
        crowd_txt = plates.crowd_line(ep, shots)
    for k, s in enumerate([] if show else shots, 1):
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
        if show:
            goal = _show_goal(ep, u)
        else:
            goal = f"【目标】{loc_name}，{singer}在说唱对决里正面开火，一镜一句、动作照歌词字面演。"
        look_cn = SHOW_PLATE_LOOK_CN if show and any(f in plates.BY_FILE for f, _ in uploads) else look.cn
        body = [AUDIO_COPY_CN, goal, ref_text, people_txt, crowd_txt, "【分镜】", *timeline, LIPSYNC_CN,
                "【画面】" + look_cn + cinema.realism_cn(ep.realism, sung=True),
                CORE_CN + cinema.NO_TEXT_CN, AUDIO_COPY_CN]
    else:
        if show:
            goal = f"【目标】{ep.show_name or loc_name}现场，综艺节目的多机位画面。" + (shots[0].note or "")
        else:
            goal = f"【目标】{loc_name}。" + (shots[0].note or "")
        body = [AUDIO_RHYTHM_CN if u.audio == "instrumental" else "【音频】无声视频。", goal, ref_text,
                people_txt if who_all else "", crowd_txt, "【分镜】", *timeline,
                "【画面】" + look.cn + cinema.realism_cn(ep.realism) + cinema.MOTION_CN + cinema.CAMERA_REAL_CN,
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
        cinema.realism_en(ep.realism) if char else "",
        "no text, no letters, no logos",
    ]
    p = ", ".join(x for x in parts if x)
    return f"{p} --ar {ar} --style raw --stylize 60 --no {cinema.negative_en(ep.realism)}"


def still_prompt_cn(ep: Episode, char: Character | None, framing: str, lens: str, scene_cn: str) -> str:
    """即梦 / Seedream 图片版：同样的顺序，中文。"""
    look = cinema.LOOKS.get(ep.look, cinema.LOOKS["night_arena"])
    parts = [cinema.FRAMINGS[framing][0], cinema.LENSES[lens][0]]
    if char:
        parts += [char.identity_cn or char.identity, char.wardrobe_cn or char.wardrobe_default, char.props_cn]
    parts += [scene_cn, look.cn]
    if char:
        parts.append(cinema.realism_cn(ep.realism))
    parts.append("综艺节目现场照片，无文字、无水印、无标志" if ep.realism == "idol_show" else "电影剧照，无文字、无水印、无标志")
    return "，".join(x.strip("。，, ") for x in parts if x) + "。"


SHEET_TILES = ("face", "34", "profile", "half", "full")  # step-2 views tiled into <key>_sheet.png by `ep sheets`
FACE_ROLE_CN = "定妆正面像：保持同一张脸、发型和发色"
CANON_ROLE_CN = "原作图：只参考发色、发型、眼睛和服装配色，不照抄画风，变成真人照片"
MJ_V6_NOTE = "Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替"


def _mj(ar: str, ep: Episode) -> str:
    return f"--ar {ar} --style raw --stylize 60 --no {cinema.negative_en(ep.realism)}"


def _cn(*parts: str) -> str:
    return "，".join(x.strip("。，, ") for x in parts if x) + "。"


def _en(*parts: str) -> str:
    return ", ".join(x.strip(" ,.") for x in parts if x)


def _idol_steps(ep: Episode, k: str, ch: Character) -> list[dict]:
    """定妆 for an 'idol_show' episode in three image-guided steps (docs/方法论.md):
    1 official art -> photoreal front portrait (text-to-image for original characters),
    2 that portrait uploaded as the reference for every other view, 3 `ep sheets` tiles the locked views."""
    from aigc_mv.canon_refs import CANON_DIR  # canon_refs imports this module

    c = ep.cast[k]
    nm, role = c.name_cn, ROLE_CN[c.role]
    who = f"{nm}（{role}）"
    mic = c.role in ("rapper", "host", "dj", "hook")
    ident_cn, ident_en = ch.identity_cn or ch.identity, ch.identity
    wear_cn, wear_en = ch.wardrobe_cn or ch.wardrobe_default, ch.wardrobe_default
    sig_cn = f"招牌特征不能丢：{ch.signature_cn}" if ch.signature_cn else ""
    sig_en = f"signature details that must stay: {ch.signature_en}" if ch.signature_en else ""
    base = {"cast": k, "en": "", "cn": "", "mj_params": "", "uploads": []}
    out = []

    # step 1: the front portrait everything else is built from
    canon = bool(ch.canon_refs)
    face = dict(base, file=f"{k}_face.png", step=1, kind="face",
                use=f"{who}第一步 定妆正面像：挑一张锁定，第二步每张图都上传它")
    front_cn = "正面头肩像，正对镜头，眼睛平视"
    front_en = "front head-and-shoulders portrait facing the camera straight on, eyes level"
    if canon:
        face["uploads"] = [{"path": str(CANON_DIR / f"{c.character}.jpg"), "role": CANON_ROLE_CN}]
        face["canon_url"] = ch.canon_refs[0].url
        face["canon_look_cn"] = ch.canon_look_cn
        face["mj_params"] = f"--iw 1.5 {_mj('3:4', ep)}"
        face["cn"] = _cn(f"把图1里的动漫角色拍成真人综艺定妆照（{CANON_ROLE_CN}）", front_cn, ident_cn, sig_cn,
                         wear_cn, cinema.SHOW_LOOK_CN, cinema.SHEET_SHOOT_CN, "是真实拍摄的照片，不是画，无文字、无水印、无标志")
        face["en"] = ("<原作图链接> " + _en(
            front_en, "photoreal live-action costume test photo of the character in the image prompt, only the hair "
            "colour, hairstyle, eyes and costume palette are taken from it, not the drawing style", ident_en, sig_en,
            wear_en, cinema.SHOW_LOOK_EN, cinema.SHEET_SHOOT_EN, "a real photograph, no text, no letters, no logos")
            + " " + face["mj_params"])
    else:
        face["mj_params"] = _mj("3:4", ep)
        face["cn"] = _cn(f"{nm}的真人综艺定妆照（原创角色，没有原作图，直接文生图）", front_cn, ident_cn, sig_cn, wear_cn,
                         cinema.SHOW_LOOK_CN, cinema.SHEET_SHOOT_CN, "无文字、无水印、无标志")
        face["en"] = _en(front_en, ident_en, sig_en, wear_en, cinema.SHOW_LOOK_EN, cinema.SHEET_SHOOT_EN,
                         "no text, no letters, no logos") + " " + face["mj_params"]
    out.append(face)

    # step 2: every other view, each generated with the locked portrait uploaded
    turn_cn = {"left": "朝右", "right": "朝左"}.get(c.side, "微微朝左")
    turn_en = {"left": "to the right", "right": "to the left"}.get(c.side, "slightly to the left")
    mic_cn = "，右手拿着银色有线话筒，话筒在嘴的斜下方" if mic else ""
    mic_en = ", holding a silver corded microphone below the mouth" if mic else ""
    listen = (c.listen_cn or "").strip("。 ")
    views = [
        ("34", "四分之三侧面", f"四分之三侧面头肩像，身体和脸{turn_cn}", f"three-quarter head-and-shoulders view turned {turn_en}", "3:4"),
        ("profile", "正侧面", f"正侧面头肩像，脸{turn_cn}，看得清侧脸轮廓和发型", f"strict profile head-and-shoulders view facing {turn_en}", "3:4"),
        ("half", "半身", f"腰以上半身照，身体微微{turn_cn}，穿全套舞台服装{mic_cn}",
         f"waist-up shot turned slightly {turn_en} in the full stage wardrobe{mic_en}", "3:4"),
        ("expr", "表情四宫格", f"同一个人的表情四宫格，2x2 拼在一张图里：笑、认真、惊讶、招牌表情（{listen or '角色平时的样子'}），四格都是正面头肩",
         "a 2x2 expression grid of the same person, four front head-and-shoulders frames: laughing, serious, "
         "surprised, and the character's signature reaction face", "1:1"),
        ("full", "全身", f"全身照，从头到鞋都在画面里，站姿自然，身体{turn_cn}，穿全套舞台服装和鞋{mic_cn}",
         f"full-body shot head to shoes, natural stance turned {turn_en}, full stage costume and shoes{mic_en}", "2:3"),
    ]
    for tag, label, v_cn, v_en, ar in views:
        use = f"{who}第二步 {label}：上传锁定的 {k}_face.png 生成"
        if tag not in SHEET_TILES:
            use += "（可选：只用来试表情、挑招牌表情，不拼进组图，视频单元不用）"
        it = dict(base, file=f"{k}_{tag}.png", step=2, kind=tag, use=use, optional=tag not in SHEET_TILES)
        it["uploads"] = [{"file": f"{k}_face.png", "role": FACE_ROLE_CN}]
        it["mj_params"] = f"--oref <定妆正面像链接> --ow 100 {_mj(ar, ep)}"
        it["mj_note"] = MJ_V6_NOTE
        it["cn"] = _cn(f"图1是{nm}的{FACE_ROLE_CN}", f"拍同一个人的{v_cn}", ident_cn, sig_cn, wear_cn,
                       cinema.SHOW_LOOK_CN, cinema.SHEET_SHOOT_CN,
                       "无文字、无水印、无标志")
        it["en"] = _en(v_en, "the same person as the omni reference, same face, hairstyle and hair colour", ident_en,
                       sig_en, wear_en, cinema.SHOW_LOOK_EN, cinema.SHEET_SHOOT_EN,
                       "no text, no letters, no logos") + " " + it["mj_params"]
        out.append(it)

    # step 3: assembled locally, no prompt
    out.append(dict(base, file=f"{k}_sheet.png", step=3, kind="sheet",
                    tiles=[f"{k}_{t}.png" for t in SHEET_TILES],
                    use=f"{who}第三步 定妆组图：由 aigc-mv ep sheets 把锁定的 face/34/profile/half/full 拼成，"
                        f"视频单元只传这一张（所有含{nm}的生成都上传，只认脸，不当画面）"))
    return out


def refs_plan(ep: Episode, board: Board, chars: dict[str, Character]) -> list[dict]:
    """Every image the episode needs, with file name, use and both prompt languages."""
    out = []
    idol = ep.realism == "idol_show"
    for k, c in ep.cast.items():
        ch = chars[k]
        if idol:
            out += _idol_steps(ep, k, ch)
            continue
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
    show = ep.format == "show"
    if show:  # the arena plate set replaces venue / judges / DJ booth / crowd stills
        out += plate_items(ep, board)
    scenes = [] if show else [("venue.png", "主场景（正面、对称、平视；开场推镜头要正对着推）", ep.venue)]
    scenes += [(f"loc_{k}.png", f"叙事场景：{v.cn}", v) for k, v in ep.locations.items()]
    for f, use, loc in scenes:
        out.append({
            "file": f, "use": use,
            "en": still_prompt_en(ep, None, "WS", "35",
                                  "symmetrical straight-on view at eye level, level horizon, nobody in frame, "
                                  + (loc.en or loc.cn)),
            "cn": still_prompt_cn(ep, None, "WS", "35", "正面对称平视，地平线水平，画面里没有人，" + loc.cn),
        })
    if ep.members("judge") and not show:
        out.append({
            "file": "judges.png", "use": "评委席（评委反应镜头的场景图）",
            "en": still_prompt_en(ep, None, "MS", "50",
                                  "the judges' bench of a rap show: three tall dark wooden thrones side by side on a "
                                  "raised platform beside the stage, red rim light, nobody seated, "
                                  + (ep.venue.en or ep.venue.cn)),
            "cn": still_prompt_cn(ep, None, "MS", "50", "说唱节目的评委席：舞台边的高台上并排摆着三张高背深色木王座，"
                                  "红色轮廓光，座位上没有人，" + ep.venue.cn),
        })
    if ep.members("dj") and not show:
        out.append({
            "file": "dj_booth.png", "use": "DJ 台（主持和 DJ 镜头的场景图）",
            "en": still_prompt_en(ep, None, "MS", "50",
                                  "a DJ booth at the back of the stage: a black console with two turntables and a "
                                  "mixer, small lamps, the red LED wall behind, nobody in frame, "
                                  + (ep.venue.en or ep.venue.cn)),
            "cn": still_prompt_cn(ep, None, "MS", "50", "舞台后方的 DJ 台：黑色台子上两台唱机和一台调音台，几盏小台灯，"
                                  "背后是红色 LED 大屏，画面里没有人，" + ep.venue.cn),
        })
    if not show:
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
        item = {
            "file": f"plate_{u.id}.png", "use": f"{u.id} 首帧（{s.section} · {s.kind}）",
            "en": still_prompt_en(ep, char, s.framing, s.lens, f"{s.action_cn}; {loc.en or loc.cn}"),
            "cn": still_prompt_cn(ep, char, s.framing, s.lens, f"{s.action_cn}，{loc.cn}"),
        }
        if show and s.location == "venue":  # first frames sit in the locked environment plate
            env = plates.plate_for(ep, s.staging)
            item["env_plate"] = env.file
            item["uploads"] = [{"file": env.file, "role": "场景图：保持同一个场馆、灯光、配色和观众席"}]
            lead = f"图1是场景图 {env.file}（{env.title_cn}）：保持同一个场馆、同样的灯光、配色和观众席"
            if s.who:
                k = s.who[0]
                item["uploads"].append({"file": f"{k}_sheet.png", "role": f"{ep.cast[k].name_cn}的锁定定妆组图"})
                lead += f"，图2是{ep.cast[k].name_cn}的锁定定妆组图：只认脸、发型和服装"
            if env.crowd == "full":
                lead += f"，{ep.crowd_cn.strip('。，, ')}，{plates.DENSE_CN}"
            elif env.crowd == "dark":
                lead += f"，{plates.DARK_CN}"
            item["cn"] = lead + "，" + item["cn"]
            item["mj_note"] = f"Midjourney 里把锁定的 {env.file} 当 --sref 风格参考，或者用即梦上传它当图1"
        out.append(item)
    return out


def plate_items(ep: Episode, board: Board) -> list[dict]:
    """refs_plan entries of the environment plates, with the shots and units that use each one."""
    uploads = {u.id: {f for f, _ in _show_unit_refs(ep, board, u)} for u in board.units}
    out = []
    for p in plates.ep_plates(ep):
        pr = plates.plate_prompts(ep, p)
        shots = [s.id for s in board.shots if plates.plate_for(ep, s.staging).file == p.file]
        out.append({
            "file": p.file, "plate": True, "title": p.title_cn, "use": p.use_cn, "stagings": list(p.stagings),
            "camera": f"{cinema.FRAMINGS[p.framing][0]}，{cinema.LENSES[p.lens][0]}；{p.angle_cn}",
            "crowd": p.crowd, "aspect": p.aspect, "candidates": plates.CANDIDATES, "must": p.must,
            "shots": shots, "units": [u.id for u in board.units if p.file in uploads[u.id]],
            "uploads": [{"file": p.guide, "role": "已锁定的场景图：保持同一个场馆、布景、灯光和配色"}] if p.guide else [],
            "cn": pr["cn"], "en": pr["en"], "gpt": pr["gpt"],
        })
    return out


# --------------------------------------------------------------------------- Suno


DEFAULT_VOICE = {
    "rapper": "confident male rapper",
    "hook": "melodic female vocal singing the hook",
    "host": "energetic TV show host, spoken, not sung",
    "dj": "hype DJ shouting, spoken",
    "teammate": "crew member backing shouts",
    "judge": "calm judge, spoken",
    "cameo": "audience member shout, spoken",
}


KIND_CN = {"cold_open": "开场", "host": "主持", "entrance": "入场", "faceoff": "对峙", "hook": "副歌", "verse": "主歌",
           "interlude": "间奏", "reveal": "揭晓", "outro": "收尾"}


def suno_passes(ep: Episode) -> list[list[int]]:
    """Section indices per Suno pass: Verse.suno_pass when set, else 1 = up to the first rapper verse,
    2 = up to the second, 3 = the rest."""
    n_rv, auto = 0, []
    for v in ep.verses:
        auto.append(min(n_rv + 1, 3))
        if v.kind == "verse" and v.who and ep.cast[v.who].role == "rapper":
            n_rv += 1
    nums = [v.suno_pass if v.suno_pass is not None else auto[i] for i, v in enumerate(ep.verses)]
    return [[i for i, n in enumerate(nums) if n == p] for p in sorted(set(nums))]


def _voice(ep: Episode, chars: dict[str, Character], k: str) -> str:
    c = ep.cast[k]
    return c.voice or chars[k].voice or DEFAULT_VOICE[c.role]


def _suno_show(ep: Episode, chars: dict[str, Character]) -> str:
    """Variety show: several voices per pass, Extend between passes, section tags in the lyric field."""
    bpm = int(ep.bpm_hint or 92)
    style_base = (f"Chinese hip hop variety show, rap battle on a TV stage, boom bap, {bpm} BPM, hard punchy drums, "
                  "deep sub bass, DJ scratches, live TV-show crowd, clear Mandarin diction")
    passes = suno_passes(ep)
    title = ep.show_name + (f" · {ep.episode_no}" if ep.episode_no else "")
    out = [f"# Suno · {ep.title}" + (f"（{title}）" if title else ""), "",
           "设置：Advanced · Variety 0 · Weirdness 35% · Style Influence 70% · 不选 Voice/Persona。",
           f"一共 {len(passes)} 段：先生成第 1 段，挑一条后 Extend 接第 2 段，再 Extend 接第 3 段；"
           "每段换成那一段自己的 Styles，Lyrics 只填那一段。",
           "Lyrics 里的方括号是段落和人声标签：[Spoken Word: 名字] 是念白，[Chorus: 名字] 是副歌，[Verse: 名字] 是主歌，"
           "[Break: silence] 是全场静音的一拍。",
           "主持和 DJ 的念白也可以不让 Suno 唱：那几句在 Suno 里留成伴奏，另外用 TTS 配音，剪辑时按 analysis/timing.json 的时间铺上。",
           "生僻字在 Suno 栏写同音字（sung_as），字幕保留原字。拿到歌后用 Suno 自带的 stem 分离导出人声和伴奏。", ""]
    last_pass = len(passes) - 1
    for pi, idx in enumerate(passes):
        voices: list[str] = []
        for vi in idx:
            v = ep.verses[vi]
            for ln in v.lines:
                k = ep.singer_of(v, ln)
                if k not in voices:
                    voices.append(k)
        vtxt = "; ".join(f"{ep.cast[k].name_en or ep.cast[k].name_cn}: {_voice(ep, chars, k)}" for k in voices)
        kinds = [ep.verses[vi].kind for vi in idx]
        lyr: list[str] = []
        for vi in idx:
            lyr += _suno_section(ep, vi)
        if pi == last_pass:
            lyr.append("[End]")
        names = "、".join(ep.cast[k].name_cn for k in voices) or "伴奏"
        kinds_cn = "、".join(dict.fromkeys(KIND_CN.get(x, x) for x in kinds))
        out += [f"## 第 {pi + 1} 段 · {kinds_cn} · {names}", ""]
        if pi > 0:
            prev = ep.verses[passes[pi - 1][-1]]
            prev_last = next((ln.text for ln in reversed(prev.lines)), "")
            out += [f"Extend：在第 {pi} 段挑好的那条上点 Extend，Extend from 设在第 {pi} 段最后一个字唱完处"
                    + (f"（「{prev_last}」之后）" if prev_last else "") + "，Styles 换成下面这段，Lyrics 只填本段。", ""]
        out += ["Styles:", "```", style_base + (f", voices in order: {vtxt}" if vtxt else "")
                + (", short intro" if pi == 0 else "") + (", ends on a crowd chant" if pi == last_pass else ""),
                "```", "Lyrics:", "```", "\n".join(lyr).strip(), "```", ""]
    return "\n".join(out) + "\n"


def _suno_section(ep: Episode, vi: int) -> list[str]:
    v = ep.verses[vi]
    bars = f"{v.bars} bars, " if v.bars else ""
    head = {
        "cold_open": f"[Intro: {bars}crowd noise, DJ scratch]",
        "entrance": f"[Interlude: {bars}walk-in beat, crowd cheering]",
        "faceoff": f"[Break: {bars}beat drops low, tension]",
        "interlude": f"[Interlude: {bars}instrumental]",
        "outro": "[Outro: crowd call]",
    }.get(v.kind, "")
    out = [head] if head else []
    tag_prev = None
    for ln in v.lines:
        k = ep.singer_of(v, ln)
        nm = ep.cast[k].name_cn
        if ln.pause_beats:
            out.append("[Break: silence]")
            tag_prev = None
        if ln.spoken:
            tag = f"[Spoken Word: {nm}]"
        elif v.kind in ("interlude", "outro"):
            tag = None  # the section header carries it (onomatopoeia / crowd call)
        elif v.kind == "hook" or ep.cast[k].role == "hook":
            tag = f"[Chorus: {nm}]"
        else:
            tag = f"[Verse: {nm}]"
        if tag and tag != tag_prev:
            out.append(tag)
        tag_prev = tag or tag_prev
        out.append(ln.sung_as or ln.text)
    return out + [""]


def suno_sheets(ep: Episode, chars: dict[str, Character]) -> str:
    """Two-pass Suno plan (A first, then Extend with B) so the two voices really differ."""
    if ep.format == "show":
        return _suno_show(ep, chars)
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
