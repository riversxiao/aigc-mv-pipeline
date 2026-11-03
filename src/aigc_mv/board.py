"""Storyboard planner + audit.

Turns `episode.yaml` + `analysis/timing.json` into `board/board.json`: shots that tile the song, each with a
kind, framing, lens, ONE camera move and an action, grouped into generation *units* (one Seedance request
each). Also writes `board/board.md`, the sheet the director reviews before any money is spent.

Shot grammar (per 4-line stanza), built from the two reference films:

    line 1  perform   open move (whip / push / steadicam)   – the singer owns the frame
    line 2  perform   the rival is in frame (2S / OTS)       – Keynes-vs-Hayek: the opponent always present
    line 3  perform → react on the 2nd half-line             – 火影有嘻哈: long-lens reaction cam
    line 4  punch     accent move (snap zoom / low push)     – the punchline lands on a move, not a cut

A line with `cutaway:` keeps its first half-line on the singer and cuts to a story insert for the rest.
Sections: intro = establishing crane/push, break = crowd + next rapper raising the mic, outro = winner/loser.

`format: show` episodes are planned by aigc_mv.show.plan_show (variety-show grammar of 《火影有嘻哈03》).
"""

from __future__ import annotations

import math
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from aigc_mv import cinema
from aigc_mv.episode import Episode
from aigc_mv.timing import TimedLine, Timing
from aigc_mv.tools import han

LEAD = 0.30          # silence before the first sung word in every sung window
PRE_ROLL = 0.10      # cut this long before a line's first word (the mouth is already on screen)
MIN_SHOT = 0.8
UNIT_MIN, UNIT_MAX = 4, 12  # Seedance request length limits used here (seconds)
SUNG_MAX = 8                # sung windows: lip sync degrades past ~8 s (claudia.gallery)

ShotKind = Literal["establish", "perform", "react", "cutaway", "crowd", "outro", "host", "hook", "entrance",
                   "blackout"]
SUNG_KINDS = ("perform", "react", "host", "hook")  # shots that join a singer's sung unit


class BoardShot(BaseModel):
    id: str
    t0: float
    t1: float
    section: str
    kind: ShotKind
    who: list[str] = Field(default_factory=list, description="Cast keys visible in frame")
    singer: str | None = Field(None, description="Whose voice is heard")
    sung: bool = Field(False, description="The visible singer's mouth must sync")
    lines: list[int] = Field(default_factory=list)
    role: str = "mid"
    framing: str = "MCU"
    lens: str = "50"
    camera: str = "locked"
    location: str = "venue"
    grammar: str = "show"
    action_cn: str = ""
    unit: str = ""
    note: str = ""
    staging: str = Field("", description="Show staging id in cinema.SHOW_STAGINGS")
    background: list[str] = Field(default_factory=list, description="Teammates blurred behind the singer")

    @property
    def dur(self) -> float:
        return self.t1 - self.t0


class Unit(BaseModel):
    """One generation request (one Seedance clip)."""

    id: str
    kind: Literal["sung", "motion"]
    shots: list[str]
    song_t0: float = Field(..., description="Song time of the clip's frame 0")
    duration: int
    singer: str | None = None
    audio: Literal["vocal", "instrumental", "none"] = "vocal"
    location: str = "venue"


class Board(BaseModel):
    title: str
    grammar: str
    look: str
    duration: float
    shots: list[BoardShot]
    units: list[Unit]

    def shot(self, sid: str) -> BoardShot:
        return next(s for s in self.shots if s.id == sid)

    def unit_shots(self, u: Unit) -> list[BoardShot]:
        return [self.shot(s) for s in u.shots]


# --------------------------------------------------------------------------- planning helpers


class _Picker:
    """Chooses moves and framings with variety rules: no repeat of the last move, ration rare moves."""

    def __init__(self) -> None:
        self.history: list[str] = []
        self.framings: list[str] = []
        self.counts: Counter = Counter()

    def move(self, role: str, framing: str, grammar: str, sung: bool, forced: str | None = None) -> str:
        if forced:
            if forced not in cinema.MOVES:
                raise ValueError(f"unknown camera move {forced!r}; choose from {sorted(cinema.MOVES)}")
            self._use(forced)
            return forced
        pool = cinema.STANZA_ROLE_MOVES.get(role, ["locked"]) + ["push_slow", "locked", "handheld"]
        ok = []
        for order, mid in enumerate(dict.fromkeys(pool)):
            m = cinema.MOVES[mid]
            if framing not in m.framings or grammar not in m.grammars:
                continue
            if sung and not m.sung_ok:
                continue
            if mid in self.history[-2:]:
                continue
            if self.counts[mid] >= m.max_per_film:
                continue
            ok.append((self.counts[mid], order, mid))
        mid = min(ok)[2] if ok else "locked"
        self._use(mid)
        return mid

    def _use(self, mid: str) -> None:
        self.history.append(mid)
        self.counts[mid] += 1

    def framing(self, choices: list[str], forced: str | None = None) -> str:
        if forced:
            self.framings.append(forced)
            return forced
        recent = self.framings[-6:]
        ok = [f for f in choices if not self.framings or self.framings[-1] != f] or choices
        f = min(ok, key=lambda x: (recent.count(x), choices.index(x)))
        self.framings.append(f)
        return f


FRAMING_BY_ROLE = {
    "show": {"open": ["MCU", "MS"], "mid": ["CU", "OTS", "2S", "MCU"], "punch": ["MCU", "MS"],
             "react": ["CU", "MCU"]},
    "mv": {"open": ["MS", "MWS"], "mid": ["MCU", "2S", "CU"], "punch": ["CU", "MCU"], "react": ["MCU", "CU"]},
}

DEFAULT_ACTION = {
    "open": "举起话筒开口，空着的那只手指向对手",
    "mid": "跟着节拍点头，空着的手随着重音比划",
    "punch": "最后两个字咬得很重，身体前倾逼近对手",
}


def _cut_time(t: float, grid_beats: list[float], tol: float = 0.12) -> float:
    """Cut PRE_ROLL before the word, pulled onto a beat when one is within `tol`."""
    target = t - PRE_ROLL
    if grid_beats:
        b = min(grid_beats, key=lambda x: abs(x - target))
        if abs(b - target) <= tol and b <= t - 0.04:
            return round(b, 3)
    return round(target, 3)


def announce_time(ep: Episode, k: str, lines: list[TimedLine]) -> float | None:
    """When the host says rapper k's name (name_cn / aka / nickname) in the entrance lines.
    Episode.mentions_of skips the rappers on purpose, so the entrance matches names itself."""
    c = ep.cast[k]
    for ln in lines:
        pos = [ln.text.find(n) for n in [c.name_cn, c.aka, *c.nicknames] if n]
        pos = [p for p in pos if p >= 0]
        if not pos:
            continue
        i = len(han(ln.text[:min(pos)]))
        if ln.chars:
            return round(ln.chars[min(i, len(ln.chars) - 1)] - 0.08, 3)
        return ln.t0
    return None


def plan(ep: Episode, timing: Timing) -> Board:
    if ep.format == "show":
        from aigc_mv.show import plan_show

        return plan_show(ep, timing)
    picker = _Picker()
    shots: list[BoardShot] = []
    beats = timing.grid.beats
    lines = timing.lines
    n_sid = 0

    def add(**kw) -> BoardShot:
        nonlocal n_sid
        n_sid += 1
        s = BoardShot(id=f"s{n_sid:03d}", **kw)
        shots.append(s)
        return s

    cast = list(ep.cast)
    both = sorted(cast, key=lambda k: 0 if ep.cast[k].side == "left" else 1)

    reacted: set[tuple[int, int]] = set()  # one reaction cutaway per stanza
    # cut points: one per line start; sections in between
    cuts = [_cut_time(ln.t0, beats) for ln in lines]
    first_cut = cuts[0]

    # --- intro: establishing
    if first_cut > 0.2:
        fr = "WS"
        add(t0=0.0, t1=first_cut, section="intro", kind="establish", who=both, framing=fr,
            lens=cinema.lens_for("mv", fr), camera=picker.move("crowd", fr, "show", False, "crane_in"),
            grammar="show", action_cn=ep.intro_cn or "两人在台上面对面对峙，互相盯着，都不说话，手里都拿着话筒",
            note="标题叠在这个镜头上")

    for gi, ln in enumerate(lines):
        verse = ep.verses[ln.verse]
        src = verse.lines[ln.line]
        me, other = ln.who, ep.other(ln.who)
        loc_key, _loc = ep.location_of(verse, src)
        cut_loc = loc_key
        if src.cutaway:  # the singer stays where the verse is; only the insert goes to the story location
            loc_key = verse.location or "venue"
        grammar = ep.grammar if ep.grammar != "hybrid" else ("show" if loc_key == "venue" else "mv")
        t0 = cuts[gi]
        is_last_in_verse = gi + 1 >= len(lines) or lines[gi + 1].verse != ln.verse
        if is_last_in_verse:
            # the last line holds until the next section (break / outro) starts
            t1 = min(round(ln.t1 + 0.35, 3), cuts[gi + 1] if gi + 1 < len(cuts) else timing.duration)
        else:
            t1 = cuts[gi + 1]
        pos = ln.line % 4
        punch = src.punch if src.punch is not None else (pos == 3 or is_last_in_verse)
        role = "open" if ln.line == 0 else ("punch" if punch else "mid")
        section = f"verse{ln.verse + 1}"
        action = src.action or DEFAULT_ACTION[role]

        def perform(a: float, b: float, role_: str, framing_forced=None, cam_forced=None) -> BoardShot:
            choices = FRAMING_BY_ROLE[grammar][role_]
            if ep.cast[other].name_cn in action:  # the gag touches the rival: he must be in frame
                choices = ["2S", "OTS", "MS"]
            fr = picker.framing(choices, framing_forced)
            who = [me] if fr in ("ECU", "CU", "MCU") else both
            if fr == "OTS":
                who = both
            return add(t0=a, t1=b, section=section, kind="perform", who=who, singer=me, sung=True, lines=[gi],
                       role=role_, framing=fr, lens=cinema.lens_for(grammar, fr, ln.line),
                       camera=picker.move(role_, fr, grammar, True, cam_forced), location=loc_key,
                       grammar=grammar, action_cn=action)

        halves = ln.phrases
        split = halves[1].t0 - 0.08 if len(halves) >= 2 else None
        if src.cutaway:
            if split and split - t0 >= MIN_SHOT:
                perform(t0, round(split, 3), role, src.framing, src.camera)
                a = round(split, 3)
            else:
                a = t0
            fr = "MS"
            add(t0=a, t1=t1, section=section, kind="cutaway", who=[], singer=me, sung=False, lines=[gi],
                role="cutaway", framing=fr, lens=cinema.lens_for("mv", fr),
                camera=picker.move("cutaway", fr, "mv", False), location=cut_loc, grammar="mv",
                action_cn=src.cutaway, note="叙事插入：照典故字面演，画面里没人张嘴唱")
        elif (pos in (1, 2) and not punch and (ln.verse, ln.line // 4) not in reacted and split
              and split - t0 >= 0.7 and t1 - split >= MIN_SHOT):
            reacted.add((ln.verse, ln.line // 4))
            perform(t0, round(split, 3), role, src.framing, src.camera)
            fr = picker.framing(FRAMING_BY_ROLE[grammar]["react"])
            add(t0=round(split, 3), t1=t1, section=section, kind="react", who=[other], singer=me, sung=False,
                lines=[gi], role="react", framing=fr, lens=cinema.lens_for("show", fr),
                camera=picker.move("react", fr, grammar, False), location=loc_key, grammar=grammar,
                action_cn=ep.cast[other].listen_cn, note=f"{ep.cast[other].name_cn}只听不说，嘴一直闭着")
        else:
            perform(t0, t1, role, src.framing, src.camera)

        # break after a verse
        if is_last_in_verse and gi + 1 < len(lines):
            b0, b1 = t1, cuts[gi + 1]
            if b1 - b0 >= MIN_SHOT:
                nxt = lines[gi + 1].who
                mid = round((b0 + b1) / 2, 3) if b1 - b0 >= 2 * MIN_SHOT + 0.4 else None
                if mid:
                    add(t0=b0, t1=mid, section=f"break{ln.verse + 1}", kind="crowd", who=[], framing="WS",
                        lens="35", camera=picker.move("crowd", "WS", "show", False), grammar="show",
                        action_cn=ep.break_cn or "台下观众挤在一起，举着火把和拳头齐声喊口号，情绪激动",
                        note=f"口号：{ep.break_chant}" if ep.break_chant else "")
                add(t0=mid or b0, t1=b1, section=f"break{ln.verse + 1}", kind="react", who=[nxt], framing="MCU",
                    lens="85", camera=picker.move("react", "MCU", "show", False), grammar="show",
                    action_cn=f"{ep.cast[nxt].name_cn}慢悠悠举起话筒，嘴角一挑，准备开口", note="下一位上场")
            elif shots:
                shots[-1].t1 = b1

    # outro
    end0 = shots[-1].t1
    if timing.duration - end0 >= MIN_SHOT:
        winner = lines[-1].who
        loser = ep.other(winner)
        half = round(end0 + (timing.duration - end0) * 0.55, 3)
        add(t0=end0, t1=half, section="outro", kind="outro", who=[winner], framing="MCU", lens="85",
            camera=picker.move("react", "MCU", "show", False), grammar="show",
            action_cn=ep.outro_cn or f"{ep.cast[winner].name_cn}慢慢放下话筒，嘴角一点点挑起，得意地看着对手，嘴闭着",
            note="不要全景、不要拉远、不要走路：近景最稳")
        add(t0=half, t1=round(timing.duration, 3), section="outro", kind="outro", who=both, framing="2S",
            lens="50", camera=picker.move("react", "2S", "show", False), grammar="show",
            action_cn=f"{ep.cast[loser].name_cn}无奈地轻轻摇头；{ep.cast[winner].name_cn}把话筒举过头顶，两人都站在原地，嘴闭着",
            note="片尾问题叠在这里")
    else:
        shots[-1].t1 = round(timing.duration, 3)

    units = group_units(ep, shots, timing)
    return Board(title=ep.title, grammar=ep.grammar, look=ep.look, duration=timing.duration, shots=shots,
                 units=units)


def group_units(ep: Episode, shots: list[BoardShot], timing: Timing) -> list[Unit]:
    """Sung units: consecutive perform/react shots of one singer in one location, ≤ UNIT_MAX seconds.
    Motion units: every cutaway / establish / crowd / outro shot on its own."""
    units: list[Unit] = []
    cur: list[BoardShot] = []
    line_end = {ln.idx: ln.t1 for ln in timing.lines}
    line_start = {ln.idx: ln.t0 for ln in timing.lines}

    def sung_t0(group: list[BoardShot]) -> float:
        """Frame 0 sits LEAD before the first sung word (and before the first cut)."""
        first_word = min(line_start[i] for s in group for i in s.lines)
        return round(max(0.0, min(group[0].t0 - (LEAD - PRE_ROLL), first_word - LEAD)), 3)

    def sung_end(group: list[BoardShot]) -> float:
        """A sung take covers its lines to the last word, even when the cut leaves early for a cutaway:
        a window that stops inside a word gets re-sung."""
        ends = [line_end[i] + 0.25 for s in group for i in s.lines]
        return max([group[-1].t1, *ends])

    def flush_sung() -> None:
        if not cur:
            return
        song_t0 = sung_t0(cur)
        d = int(min(UNIT_MAX, max(UNIT_MIN, math.ceil(sung_end(cur) - song_t0 - 1e-6))))
        u = Unit(id=f"u{len(units) + 1:02d}", kind="sung", shots=[s.id for s in cur], song_t0=song_t0,
                 duration=d, singer=cur[0].singer, audio="vocal", location=cur[0].location)
        for s in cur:
            s.unit = u.id
        units.append(u)
        cur.clear()

    for s in shots:
        if s.kind in SUNG_KINDS and s.singer and s.lines:
            if cur and (cur[0].singer != s.singer or cur[0].location != s.location
                        or sung_end(cur + [s]) - sung_t0(cur) > SUNG_MAX):
                flush_sung()
            cur.append(s)
            continue
        flush_sung()
        handle = 0.5
        song_t0 = round(max(0.0, s.t0 - handle), 3)
        d = int(min(UNIT_MAX, max(UNIT_MIN, math.ceil(s.t1 - song_t0 + handle))))
        u = Unit(id=f"u{len(units) + 1:02d}", kind="motion", shots=[s.id], song_t0=song_t0, duration=d,
                 singer=None, audio="instrumental", location=s.location)
        s.unit = u.id
        units.append(u)
    flush_sung()
    return units


# --------------------------------------------------------------------------- audit


class AuditResult(BaseModel):
    ok: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    stats: dict = Field(default_factory=dict)


def audit(ep: Episode, board: Board, timing: Timing) -> AuditResult:
    err, warn = [], []
    shots = board.shots
    # tile
    if shots and abs(shots[0].t0) > 1e-3:
        err.append(f"tile: first shot starts at {shots[0].t0}, not 0")
    for a, b in zip(shots, shots[1:]):
        if abs(a.t1 - b.t0) > 1e-3:
            err.append(f"tile: gap/overlap between {a.id} ({a.t1}) and {b.id} ({b.t0})")
    if shots and abs(shots[-1].t1 - board.duration) > 0.05:
        err.append(f"tile: last shot ends at {shots[-1].t1}, song is {board.duration}")
    # lengths
    for s in shots:
        if s.dur < 0.5:
            err.append(f"length: {s.id} is {s.dur:.2f}s (< 0.5 s)")
        elif s.dur < MIN_SHOT:
            warn.append(f"length: {s.id} is {s.dur:.2f}s (< {MIN_SHOT}s)")
    # variety
    for a, b in zip(shots, shots[1:]):
        if a.camera == b.camera and a.camera != "locked":
            warn.append(f"camera: {a.id} and {b.id} both use {a.camera}")
    for a, b, c in zip(shots, shots[1:], shots[2:]):
        if a.framing == b.framing == c.framing:
            warn.append(f"framing: {a.id}-{c.id} three {a.framing} in a row")
    cnt = Counter(s.camera for s in shots)
    for mid, n in cnt.items():
        if n > cinema.MOVES[mid].max_per_film:
            err.append(f"camera: {mid} used {n}× (max {cinema.MOVES[mid].max_per_film})")
    show = ep.format == "show"
    # lead share: the singer on camera and in sync during verses
    if show:  # show: verse sections only (host / hook / reactions elsewhere are not the rapper's time)
        verse_secs = {sec.name for sec in timing.sections if sec.kind == "verse"}
        in_verse = [s for s in shots if s.section in verse_secs]
        verse_t = sum(s.dur for s in in_verse)
        floor = 0.5
    else:
        in_verse = shots
        verse_t = sum(s.dur for s in shots if s.section.startswith("verse"))
        floor = 0.6
    sung_t = sum(s.dur for s in in_verse if s.sung)
    share = sung_t / verse_t if verse_t else 0.0
    if share < floor:
        err.append(f"lead share: singer on camera {share:.0%} of verse time (< {floor:.0%})")
    elif share > 0.9:
        warn.append(f"lead share: {share:.0%} — add reactions / cutaways so it breathes")
    # units
    for u in board.units:
        if not (UNIT_MIN <= u.duration <= UNIT_MAX):
            err.append(f"unit {u.id}: duration {u.duration}s outside {UNIT_MIN}-{UNIT_MAX}s")
        ss = board.unit_shots(u)
        if ss[-1].t1 - u.song_t0 > u.duration + 0.01:
            err.append(f"unit {u.id}: shots run past the clip ({ss[-1].t1 - u.song_t0:.2f}s > {u.duration}s)")
    # every lyric line has a shot
    covered = {i for s in shots for i in s.lines}
    for ln in timing.lines:
        if ln.idx not in covered:
            err.append(f"line {ln.idx} '{ln.text}' has no shot")
    # banned words in creative text
    for s in shots:
        hits = cinema.banned_hits(s.action_cn)
        if hits:
            warn.append(f"banned words in {s.id} action: {hits}")
    # budget
    gen_s = sum(u.duration for u in board.units)
    est = gen_s * ep.budget.price_per_sec_usd * 2  # takes run ~2x the cut (claudia.gallery measurement)
    if est > ep.budget.cap_usd:
        warn.append(f"budget: estimate ${est:.2f} (2 takes per unit) > cap ${ep.budget.cap_usd:.2f}")
    extra: dict = {}
    if show:
        _audit_show(ep, board, timing, err, warn, extra)
    stats = {
        "shots": len(shots),
        "units": len(board.units),
        "sung_units": sum(1 for u in board.units if u.kind == "sung"),
        "generated_seconds": gen_s,
        "estimate_usd_2_takes": round(est, 2),
        "lead_share": round(share, 3),
        "mean_shot_s": round(sum(s.dur for s in shots) / max(1, len(shots)), 2),
        "camera_moves": dict(cnt),
        **extra,
    }
    return AuditResult(ok=not err, errors=err, warnings=warn, stats=stats)


def _audit_show(ep: Episode, board: Board, timing: Timing, err: list[str], warn: list[str], stats: dict) -> None:
    """Variety-show rules (docs/参考片拆解_火影有嘻哈03.md)."""
    shots = board.shots
    mean = sum(s.dur for s in shots) / max(1, len(shots))
    if not 2.5 <= mean <= 4.5:
        warn.append(f"show: mean shot {mean:.2f}s outside 2.5-4.5 s (reference film ~3.4 s)")
    # every line that names someone cuts to that person's reaction
    for ln in timing.lines:
        v = ep.verses[ln.verse]
        for m in ep.mentions_of(v, v.lines[ln.line]):
            if not any(s.kind == "react" and m in s.who and s.t0 < ln.t1 and s.t1 > ln.t0 for s in shots):
                err.append(f"mention: line {ln.idx} '{ln.text}' names {ep.cast[m].name_cn} but has no reaction shot")
    # every line sits inside its own section (with ASR on a real take, lines can drift off the beat layout)
    if len(timing.sections) == len(ep.verses):
        out_of = [ln for ln in timing.lines
                  if ln.t0 < timing.sections[ln.verse].t0 - 0.05 or ln.t1 > timing.sections[ln.verse].t1 + 0.3]
        for ln in out_of[:5]:
            sec = timing.sections[ln.verse]
            warn.append(f"section: line {ln.idx} '{ln.text}' ({ln.t0:.2f}-{ln.t1:.2f}s) runs outside {sec.name} "
                        f"({sec.t0:.2f}-{sec.t1:.2f}s); fix the lyric timing or the section bars / gap_bars")
        if len(out_of) > 5:
            warn.append(f"section: {len(out_of) - 5} more lines run outside their sections")
    # entrance: each rapper's CU (and name card) starts on the word that announces them
    for vi, v in enumerate(ep.verses):
        if v.kind != "entrance" or vi >= len(timing.sections):
            continue
        ls = [ln for ln in timing.lines if ln.verse == vi]
        if not ls:
            continue
        sec = timing.sections[vi]
        for k in ep.rappers():
            name = ep.cast[k].name_cn
            t = announce_time(ep, k, ls)
            if t is None:
                warn.append(f"entrance: no {sec.name} line names {name} (name_cn / aka / nicknames); "
                            "the CU falls back to an even split and drifts off the announcement")
                continue
            cu = [s for s in shots if s.section == sec.name and s.kind == "entrance" and s.who == [k]]
            if not cu or abs(cu[0].t0 - t) > 0.3:
                at = f"{cu[0].t0:.2f}s" if cu else "nowhere"
                warn.append(f"entrance: {name} is announced at {t:.2f}s but the CU starts {at} (> 0.3 s off)")
    st = Counter(s.staging for s in shots if s.staging)
    n_black = st.get("blackout_spot", 0)
    has_reveal = any(v.kind == "reveal" for v in ep.verses)
    if n_black > 1:
        err.append(f"blackout: blackout_spot used {n_black}× (exactly once per film)")
    elif has_reveal and n_black == 0:
        err.append("blackout: the reveal section has no blackout_spot shot")
    for sid, n in st.items():
        if sid not in cinema.SHOW_STAGINGS:
            err.append(f"staging: unknown staging {sid!r}")
        elif n > cinema.SHOW_STAGINGS[sid].max_per_film:
            err.append(f"staging: {sid} used {n}× (max {cinema.SHOW_STAGINGS[sid].max_per_film})")
    accents = cinema.SHOW_MOVES["accent"]
    for mid, cap in accents.items():  # type: ignore[union-attr]
        n = sum(1 for s in shots if s.camera == mid)
        if n > cap:
            err.append(f"camera: {mid} used {n}× in a show (max {cap})")
    calm = sum(1 for s in shots if s.camera in cinema.CALM_MOVES) / max(1, len(shots))
    if calm < 0.7:
        warn.append(f"camera: only {calm:.0%} calm moves (show wants >= 70% locked / push / float / handheld)")
    if not 180 <= board.duration <= 260:
        warn.append(f"show: duration {board.duration:.0f}s outside 180-260 s")
    reactions = Counter(ep.cast[w].role for s in shots if s.kind == "react" for w in s.who)
    stats.update({"stagings": dict(st), "reactions_by_role": dict(reactions), "calm_share": round(calm, 3)})


# --------------------------------------------------------------------------- review sheet


def render_sheet(ep: Episode, board: Board, timing: Timing, result: AuditResult) -> str:
    text = {ln.idx: ln.text for ln in timing.lines}
    rows = [f"# 分镜表 · {ep.title}", "",
            f"语法 `{board.grammar}` · 画风 `{board.look}` · {result.stats['shots']} 个镜头 · "
            f"{result.stats['units']} 次生成（{result.stats['generated_seconds']} 秒，按每条 2 次约 "
            f"${result.stats['estimate_usd_2_takes']}）· 唱的人在画面里 {result.stats['lead_share']:.0%} · "
            f"平均镜头 {result.stats['mean_shot_s']} 秒", ""]
    show = board.grammar == "show"  # battle sheets keep their original columns
    if show:
        rows += ["| 镜头 | 时间 | 段落 | 类型 | 调度 | 景别 / 镜头 | 运镜 | 画面 | 歌词 | 生成 |",
                 "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    else:
        rows += ["| 镜头 | 时间 | 段落 | 类型 | 景别 / 镜头 | 运镜 | 画面 | 歌词 | 生成 |",
                 "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for s in board.shots:
        who = "、".join(ep.cast[w].name_cn for w in s.who) or ("空镜" if show else "—")
        if s.background:
            who += "（身后：" + "、".join(ep.cast[w].name_cn for w in s.background) + "）"
        lyr = " / ".join(text[i] for i in s.lines)
        if show:
            stg = cinema.SHOW_STAGINGS[s.staging].cn if s.staging in cinema.SHOW_STAGINGS else ""
            rows.append(
                f"| {s.id} | {s.t0:.2f}–{s.t1:.2f} | {s.section} | {s.kind} | {stg} | {s.framing} · {s.lens} | "
                f"{s.camera} | {who}：{s.action_cn} | {lyr} | {s.unit} |")
        else:
            rows.append(
                f"| {s.id} | {s.t0:.2f}–{s.t1:.2f} | {s.section} | {s.kind} | {s.framing} · {s.lens} | {s.camera} | "
                f"{who}：{s.action_cn} | {lyr} | {s.unit} |")
    rows += ["", "## 审核", ""]
    rows += [f"- ❌ {e}" for e in result.errors] or ["- ✅ 全部通过"]
    rows += [f"- ⚠️ {w}" for w in result.warnings]
    rows += ["", "改法：在 episode.yaml 的对应歌词行写 `framing:` / `camera:` / `cutaway:` / `action:`，然后重跑 `aigc-mv ep board`。"]
    return "\n".join(rows) + "\n"


def load_board(project_dir: Path) -> Board:
    p = Path(project_dir) / "board" / "board.json"
    if not p.is_file():
        raise FileNotFoundError(f"missing {p}; run: aigc-mv ep board {project_dir}")
    return Board.model_validate_json(p.read_text(encoding="utf-8"))
