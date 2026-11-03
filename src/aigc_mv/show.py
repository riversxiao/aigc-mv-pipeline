"""Variety-show storyboard planner (`format: show`).

Grammar from the shot-by-shot study of 《火影有嘻哈03》 (docs/参考片拆解_火影有嘻哈03.md):

- slow cutting: about 3-3.6 s per shot, one shot holds one or two lines (never one cut per line by rule);
- restrained camera: locked / slow push / long-lens float / light handheld; accents are rationed;
- what makes it read as a real programme is *who is in frame and who reacts*: the singer in close-up with the
  crew blurred behind, the rival's hair in the foreground, nose-to-nose face-offs on the punch lines;
- a line that names someone cuts to that person's reaction (judges, crew, audience cameos);
- one blackout with a single follow spot before the reveal, used once per film.

Every section kind of `episode.Verse.kind` has its own recipe (see `_ShowPlanner.section`). Shots tile the
song 0 -> duration exactly; units come from board.group_units, cuts from board._cut_time.
"""

from __future__ import annotations

from collections import Counter

from aigc_mv import cinema
from aigc_mv.board import MIN_SHOT, Board, BoardShot, _cut_time, group_units
from aigc_mv.episode import Episode
from aigc_mv.timing import Section, TimedLine, Timing
from aigc_mv.tools import han

MERGE_MAX = 4.5    # a shot may hold a second line while it stays this short
FILL_TARGET = 3.2  # instrumental stretches are cut about this often
TAIL_MIN = 1.6     # silence after the last line longer than this gets its own shot(s)

REACT_STAGING = {"judge": "judge_react", "cameo": "cameo_react", "teammate": "teammate_react",
                 "host": "dj_cu", "dj": "dj_cu", "hook": "hook_mic", "rapper": "rival_react"}
VERSE_ROTATION = ["cu_team_bg", "ots_hair", "two_shot", "point_lens"]
BG_FRAMINGS = ("CU", "MCU", "MS", "OTS")
NO_BG_STAGINGS = ("spot_cu",)  # the blackout: only the singer's face is lit

ACTION = {
    "cu_team_bg": "握着话筒对着对手唱，空着的手跟着重音比划，身后的队友跟着节奏点头",
    "ots_hair": "盯着对手的眼睛唱，一字一句往前压",
    "two_shot": "一个唱一个听，唱的人往前逼一步，听的人站着不动",
    "point_lens": "转向镜头，伸手指着镜头唱",
    "mic_to_lens": "开口前先把话筒往镜头前一递，再收回嘴边唱",
    "faceoff_profile": "两人侧脸贴近，鼻尖几乎相碰，唱的人把最后几个字咬得很重，听的人一动不动",
    "hook_mic": "站在立麦前唱副歌，双手扶着话筒架，身体跟着节奏轻轻晃",
    "dj_booth": "主持和DJ站在DJ台后面，说话的人对着镜头，另一个跟着节奏点头搓碟",
    "dj_cu": "对着镜头说话，表情夸张，空着的手往台上一指",
    "high_ws": "场馆高位全景：红黑配色的场馆，地上是节目的太极八卦图案，看台坐满了观众，台上灯光亮起",
    "split_entrance": "分屏：左右两队各三人并排走进场馆，选手走在最前面，队友跟在身后",
    "blackout_spot": "全场灯灭，只剩头顶一束追光打在唱的人身上，从背后拍，只看得到背影剪影",
    "empty_stage_ws": "灭灯后的空舞台，只有追光落在地板的八卦图案上，观众席一片黑",
    "head_down_cu": "低着头，嘴闭着，呼吸很重，停了一拍",
    "spot_cu": "在追光里抬起头，看着对手轻轻说出最后一句",
    "mic_to_crowd": "把话筒伸向观众，另一只手往上招，示意全场一起喊",
}


class _ShowPlanner:
    def __init__(self, ep: Episode, timing: Timing) -> None:
        self.ep, self.timing = ep, timing
        self.beats = timing.grid.beats
        self.shots: list[BoardShot] = []
        self.stagings: Counter = Counter()
        self.moves: Counter = Counter()
        self.last_move = ""
        self.left, self.right = ep.rappers()
        self.judge_i = 0
        self.rot = 0

    # ------------------------------------------------------------------ helpers

    def ok(self, staging: str) -> bool:
        return self.stagings[staging] < cinema.SHOW_STAGINGS[staging].max_per_film

    def src(self, ln: TimedLine):
        v = self.ep.verses[ln.verse]
        return v, v.lines[ln.line]

    def mentions(self, ln: TimedLine) -> list[str]:
        return self.ep.mentions_of(*self.src(ln))

    def lines_in(self, a: float, b: float) -> list[TimedLine]:
        return [ln for ln in self.timing.lines if ln.t0 < b - 0.05 and ln.t1 > a + 0.05]

    def snap(self, t: float, tol: float = 0.25) -> float:
        if self.beats:
            b = min(self.beats, key=lambda x: abs(x - t))
            if abs(b - t) <= tol:
                return round(b, 3)
        return round(t, 3)

    def split_point(self, ln: TimedLine, late: bool = False) -> float | None:
        """Where a reaction takes over: the 2nd half-line (mentions) or the last one (extra reactions)."""
        if len(ln.phrases) >= 2:
            return round(ln.phrases[-1 if late else 1].t0 - 0.08, 3)
        if len(ln.chars) >= 2:
            return round(ln.chars[len(ln.chars) // 2] - 0.08, 3)
        return None

    def move(self, framing: str, sung: bool, forced: str | None = None) -> str:
        if forced:
            m = cinema.MOVES[forced]
            cap = cinema.SHOW_MOVES["accent"].get(forced, m.max_per_film)  # type: ignore[union-attr]
            if self.moves[forced] < min(cap, m.max_per_film) and forced != self.last_move:
                return self._use(forced)
        ok = []
        for order, mid in enumerate(cinema.CALM_MOVES):
            m = cinema.MOVES[mid]
            if framing not in m.framings or (sung and not m.sung_ok):
                continue
            if mid == self.last_move and mid != "locked":
                continue
            ok.append((self.moves[mid], order, mid))
        return self._use(min(ok)[2] if ok else "locked")

    def _use(self, mid: str) -> str:
        self.moves[mid] += 1
        self.last_move = mid
        return mid

    def add(self, a: float, b: float, sec: Section, staging: str, kind: str, who: list[str],
            singer: str | None = None, sung: bool = False, lines: list[int] | None = None, action: str = "",
            note: str = "", background: list[str] | None = None, camera: str | None = None,
            role: str = "mid") -> BoardShot:
        st = cinema.SHOW_STAGINGS[staging]
        self.stagings[staging] += 1
        fr = st.framing
        if lines is None:
            lines = [ln.idx for ln in self.lines_in(a, b)]
        if singer is None and lines:
            singer = self.timing.lines[lines[0]].who
        if (kind == "perform" and singer in (self.left, self.right) and fr in BG_FRAMINGS
                and staging not in NO_BG_STAGINGS):
            background = self.ep.team(singer)  # the crew is the second layer of every rapper shot
        s = BoardShot(id=f"s{len(self.shots) + 1:03d}", t0=round(a, 3), t1=round(b, 3), section=sec.name,
                      kind=kind, who=who, singer=singer, sung=sung, lines=lines, role=role, framing=fr,
                      lens=cinema.lens_for("show", fr), camera=self.move(fr, sung, camera), location="venue",
                      grammar="show", action_cn=action or ACTION.get(staging, ""), note=note, staging=staging,
                      background=list(background or []))
        self.shots.append(s)
        return s

    def name(self, k: str) -> str:
        return self.ep.cast[k].name_cn

    # ------------------------------------------------------------------ shot specs

    def react_spec(self, m: str) -> dict:
        c = self.ep.cast[m]
        stg = REACT_STAGING[c.role]
        bg = self.ep.team(m) if c.role == "rapper" else []
        return dict(staging=stg, kind="react", who=[m], sung=False, action=c.listen_cn, role="react",
                    note=f"{c.name_cn}只听不说，嘴一直闭着", background=bg)

    def performer_spec(self, singer: str) -> dict:
        c = self.ep.cast[singer]
        if c.role == "rapper":
            return dict(staging="cu_team_bg", kind="perform", who=[singer], sung=True,
                        background=self.ep.team(singer))
        if c.role in ("host", "dj"):
            return dict(staging="dj_cu", kind="host", who=[singer], sung=True)
        if c.role == "hook":
            return dict(staging="hook_mic", kind="hook", who=[singer], sung=True)
        return dict(staging=REACT_STAGING[c.role], kind="perform", who=[singer], sung=True,
                    action="站起来对着镜头喊，嘴型清楚")

    def booth(self) -> list[str]:
        return self.ep.members("host", "dj")

    def verse_spec(self, g: list[TimedLine], k: int) -> dict:
        singer = g[0].who
        if self.ep.cast[singer].role != "rapper":
            return self.performer_spec(singer)
        rival = self.ep.other(singer)
        punch = False
        for ln in g:
            _, src = self.src(ln)
            punch = punch or (src.punch if src.punch is not None else ln.line % 4 == 3)
        camera = None
        if k == 0 and self.ok("mic_to_lens"):
            stg, role = "mic_to_lens", "open"
        elif punch and self.ok("faceoff_profile"):
            stg, role, camera = "faceoff_profile", "punch", "snap_zoom"
        else:
            stg = VERSE_ROTATION[self.rot % len(VERSE_ROTATION)]
            self.rot += 1
            role = "punch" if punch else "mid"
        if stg in ("cu_team_bg", "point_lens", "mic_to_lens"):
            who = [singer]
        elif stg == "ots_hair":
            who = [rival, singer]
        else:
            who = [self.left, self.right]
        _, src0 = self.src(g[0])
        fr = cinema.SHOW_STAGINGS[stg].framing
        return dict(staging=stg, kind="perform", who=who, sung=True, role=role, camera=camera,
                    action=src0.action or ACTION[stg],
                    background=self.ep.team(singer) if fr in BG_FRAMINGS else [],
                    note=f"前景是{self.name(rival)}虚化的头发和肩膀" if stg == "ots_hair" else "")

    def line_spec(self, kind: str, g: list[TimedLine], k: int) -> dict:
        singer = g[0].who
        role = self.ep.cast[singer].role
        if kind == "verse":
            return self.verse_spec(g, k)
        if kind == "host":
            if role in ("host", "dj"):
                if k % 2 == 0 and self.booth():
                    return dict(staging="dj_booth", kind="host", who=self.booth(), sung=True)
                return dict(staging="dj_cu", kind="host", who=[singer], sung=True)
            return self.performer_spec(singer)
        if kind in ("hook", "interlude"):
            if k % 2 == 0:
                return self.performer_spec(singer)
            j = k // 2
            if kind == "interlude" and self.booth():
                return dict(staging="dj_booth", kind="host", who=self.booth(), sung=singer in self.booth())
            r = [self.left, self.right][j % 2]
            team = self.ep.team(r)
            if j % 2 == 1 and team:
                return dict(staging="teammate_react", kind="react", who=team, sung=False, role="react",
                            action=self.ep.cast[team[0]].listen_cn, note="队友只听不说，跟着节奏点头")
            return dict(staging="cu_team_bg", kind="react", who=[r], sung=False, role="react",
                        background=team, action=self.ep.cast[r].listen_cn,
                        note=f"{self.name(r)}只听不说，嘴一直闭着")
        if kind == "outro":
            if k == 0 and role == "rapper":
                return dict(staging="mic_to_crowd", kind="perform", who=[singer], sung=True,
                            background=self.ep.team(singer))
            if k % 2 == 1:
                return dict(staging="crowd_ws", kind="crowd", who=[], sung=False, role="crowd",
                            action=self.ep.crowd_cn + "，跟着一起喊")
            return self.performer_spec(singer)
        return self.performer_spec(singer)

    def fill_specs(self, kind: str, where: str, singer_hint: str | None = None) -> list[dict]:
        ep = self.ep
        crowd = dict(staging="crowd_ws", kind="crowd", who=[], role="crowd", action=ep.crowd_cn + "，挥手欢呼")
        booth = dict(staging="dj_booth", kind="host", who=self.booth()) if self.booth() else crowd
        both = [self.left, self.right]
        if kind == "cold_open":
            return [dict(staging="high_ws", kind="establish", who=[], camera="crane_in",
                         action=ep.intro_cn or ACTION["high_ws"], note="节目 logo 和标题叠在这个镜头上"),
                    crowd, booth]
        if kind == "host":
            return [booth]
        if kind == "entrance":
            team = [k for r in both for k in [r, *ep.team(r)]]
            return [dict(staging="split_entrance", kind="entrance", who=team, note="分屏入场：左右各一队")] + [
                dict(staging="cu_team_bg", kind="entrance", who=[r], background=ep.team(r),
                     action=f"{self.name(r)}站定，盯着对面，身后的队友抱着手臂", note="报名字时出名牌")
                for r in both]
        if kind == "faceoff":
            return [dict(staging="ots_hair", kind="react", who=[a, b], role="react",
                         action=f"{self.name(a)}和{self.name(b)}面对面站着，谁都不说话，互相盯着",
                         note=f"前景是{self.name(a)}虚化的头发和肩膀，焦点在{self.name(b)}；主持的声音在画外")
                    for a, b in ((self.left, self.right), (self.right, self.left))]
        if kind == "reveal":
            who = [singer_hint] if singer_hint else []
            return [dict(staging="blackout_spot", kind="blackout", who=who),
                    dict(staging="empty_stage_ws", kind="blackout", who=[]),
                    dict(staging="head_down_cu", kind="react", who=who, role="react")]
        if kind == "interlude":
            hook = ep.members("hook")
            specs = [dict(staging="hook_mic", kind="hook", who=hook[:1], action="闭着眼跟着伴奏晃，手扶着立麦")] \
                if hook else []
            return specs + [booth, crowd]
        if kind == "outro":
            dj = ep.members("dj") or self.booth()
            return [crowd, dict(staging="high_ws", kind="establish", who=[], camera="crane_up",
                                action="场馆高位全景，全场观众站起来挥手，台上两队站在八卦图案两边"),
                    dict(staging="dj_cu", kind="host", who=dj[:1], action="DJ 双手举过头顶，跟着观众一起喊"),
                    dict(staging="two_shot", kind="outro", who=both,
                         action=ep.outro_cn or "两位选手放下话筒，隔着舞台互相看着，嘴角都挑了一下，嘴闭着",
                         note="片尾问题叠在这里")]
        # verse / hook stretches without lyrics
        if where == "tail" and singer_hint and ep.team(singer_hint):
            t = ep.team(singer_hint)
            return [dict(staging="teammate_react", kind="react", who=t, role="react",
                         action="队友冲上来和唱完的人撞肩膀，冲对面挑眉"), crowd]
        return [dict(staging="two_shot", kind="perform", who=both, action="两人对视，等节拍进来，嘴闭着"), crowd]

    # ------------------------------------------------------------------ section recipes

    def fill(self, a: float, b: float, sec: Section, specs: list[dict], first_action: str = "",
             end_on_last: bool = False, exact: bool = False) -> None:
        if b - a < 1e-3:
            return
        n = len(specs) if exact else max(1, round((b - a) / FILL_TARGET))
        n = max(1, min(n, int((b - a) / max(MIN_SHOT, 1.0))))
        if exact and 2 <= n < len(specs):
            chosen = specs[-n:]  # too short for every spec: drop the leading ones (entrance keeps both CUs)
        elif exact or n <= len(specs):
            chosen = specs[:n] if not end_on_last else specs[:n - 1] + [specs[-1]]
        else:
            chosen = [specs[i % len(specs)] for i in range(n)]
            if end_on_last:
                chosen[-1] = specs[-1]
        cuts = [a] + [self.snap(a + (b - a) * i / n) for i in range(1, n)] + [b]
        for i, spec in enumerate(chosen):
            spec = dict(spec)
            spec.pop("sung", None)
            if i == 0 and first_action and spec["staging"] not in ("split_entrance",):
                spec["action"] = first_action
            if spec["staging"] in ("blackout_spot", "head_down_cu", "empty_stage_ws") and not self.ok(spec["staging"]):
                spec = dict(staging="crowd_ws", kind="crowd", who=[], role="crowd")
            self.add(cuts[i], cuts[i + 1], sec, spec.pop("staging"), spec.pop("kind"), spec.pop("who"),
                     sung=False, **spec)

    def group(self, ls: list[TimedLine]) -> list[list[TimedLine]]:
        out, i = [], 0
        while i < len(ls):
            g = [ls[i]]
            if not self.mentions(ls[i]):
                while i + len(g) < len(ls):
                    nxt = ls[i + len(g)]
                    if self.mentions(nxt) or nxt.who != g[0].who:
                        break
                    after = i + len(g) + 1
                    end = _cut_time(ls[after].t0, self.beats) if after < len(ls) else nxt.t1 + 0.35
                    if end - _cut_time(g[0].t0, self.beats) > MERGE_MAX:
                        break
                    g.append(nxt)
            out.append(g)
            i += len(g)
        return out

    def emit(self, sec: Section, g: list[TimedLine], s0: float, s1: float, spec: dict, react: list[str],
             must: bool) -> None:
        """One group of lines: the performer shot, then (optionally) reactions from the last line's 2nd half."""
        spec = dict(spec)
        idx = [ln.idx for ln in g]
        singer = g[0].who
        if react:
            ln = g[-1]
            if s1 - s0 < 2 * MIN_SHOT:
                sp = s0 if must else None
            else:
                sp = self.split_point(ln, late=not must)
                sp = min(max(sp if sp is not None else (s0 + s1) / 2, s0 + MIN_SHOT), s1 - MIN_SHOT)
            if sp is not None:
                if sp > s0:
                    self.add(s0, sp, sec, spec.pop("staging"), spec.pop("kind"), spec.pop("who"), singer=singer,
                             lines=idx, **spec)
                k = len(react)
                if (s1 - sp) / k >= MIN_SHOT:
                    cuts = [sp] + [self.snap(sp + (s1 - sp) * i / k, 0.1) for i in range(1, k)] + [s1]
                    groups = [[m] for m in react]
                else:
                    cuts, groups = [sp, s1], [react]
                for i, ms in enumerate(groups):
                    r = self.react_spec(ms[0])
                    r["who"] = ms
                    self.add(cuts[i], cuts[i + 1], sec, r.pop("staging"), r.pop("kind"), r.pop("who"),
                             singer=singer, lines=[ln.idx], **r)
                return
        self.add(s0, s1, sec, spec.pop("staging"), spec.pop("kind"), spec.pop("who"), singer=singer, lines=idx,
                 **spec)

    def lines_section(self, sec: Section, vi: int, ls: list[TimedLine]) -> None:
        a, b = sec.t0, sec.t1
        v = self.ep.verses[vi]
        kind = v.kind
        groups = self.group(ls)
        starts = [_cut_time(g[0].t0, self.beats) for g in groups]
        if starts[0] - a >= MIN_SHOT:
            self.fill(a, starts[0], sec, self.fill_specs(kind, "pre", ls[0].who), v.shot_cn)
        else:
            starts[0] = a
        ends = starts[1:] + [b]
        tail = None
        last_end = ls[-1].t1
        if kind == "outro" or b - last_end > TAIL_MIN:
            te = self.snap(last_end + 0.3)
            if b - te >= MIN_SHOT and te - starts[-1] >= MIN_SHOT:
                ends[-1], tail = te, te
        # reactions: every mention; per rapper verse at least one rival and one judge reaction
        react: dict[int, list[str]] = {k: self.mentions(g[0]) for k, g in enumerate(groups) if self.mentions(g[0])}
        must = set(react)
        if kind == "verse" and v.who and self.ep.cast[v.who].role == "rapper":
            n = len(groups)
            cand = [k for k, g in enumerate(groups) if k not in react and 0 < k < n - 1
                    and not self._punch(g) and ends[k] - starts[k] >= 2 * MIN_SHOT + 0.4]
            judges = self.ep.members("judge")
            has_judge = any(self.ep.cast[m].role == "judge" for ms in react.values() for m in ms)
            for want, target in ((self.ep.other(v.who), n / 3), (None if has_judge or not judges else "judge", 2 * n / 3)):
                if not want or not cand:
                    continue
                k = min(cand, key=lambda x: abs(x - target))
                cand.remove(k)
                if want == "judge":
                    want = judges[self.judge_i % len(judges)]
                    self.judge_i += 1
                react[k] = [want]
        for k, g in enumerate(groups):
            self.emit(sec, g, starts[k], ends[k], self.line_spec(kind, g, k), react.get(k, []), k in must)
        if tail is not None:
            self.fill(tail, b, sec, self.fill_specs(kind, "tail", ls[-1].who), end_on_last=kind == "outro")

    def _punch(self, g: list[TimedLine]) -> bool:
        for ln in g:
            _, src = self.src(ln)
            if src.punch if src.punch is not None else ln.line % 4 == 3:
                return True
        return False

    def reveal_section(self, sec: Section, vi: int, ls: list[TimedLine]) -> None:
        a, b = sec.t0, sec.t1
        last = ls[-1]
        c = _cut_time(last.t0, self.beats)
        pre = c - a
        specs = self.fill_specs("reveal", "pre", last.who)
        if pre >= 3 * MIN_SHOT:
            w = [0.45, 0.25, 0.30]
            if len(ls) >= 2 and c - ls[-2].t1 >= MIN_SHOT and ls[-2].t1 - a >= 2 * MIN_SHOT:
                hd = self.snap(ls[-2].t1 + 0.05, 0.15)  # head down exactly on the pause
                w = [(hd - a) * 0.62 / pre, (hd - a) * 0.38 / pre, (c - hd) / pre]
        elif pre >= 2 * MIN_SHOT:
            specs, w = [specs[0], specs[2]], [0.6, 0.4]
        elif pre >= MIN_SHOT:
            specs, w = specs[:1], [1.0]
        else:
            specs, w, c = [], [], a
        t = a
        for spec, frac in zip(specs, w):
            t1 = c if spec is specs[-1] else round(t + pre * frac, 3)
            spec = dict(spec)
            self.add(t, t1, sec, spec.pop("staging"), spec.pop("kind"), spec.pop("who"), sung=False, **spec)
            t = t1
        v = self.ep.verses[vi]
        end = b
        tail = None
        if b - last.t1 > TAIL_MIN + 1.0:
            tail = self.snap(last.t1 + 0.3)
            end = tail
        spec = dict(staging="spot_cu", kind="perform", who=[last.who], sung=True, role="punch",
                    action=self.src(last)[1].action or ACTION["spot_cu"])
        if self.ep.cast[last.who].role != "rapper":
            spec = self.performer_spec(last.who)
        m = self.mentions(last)
        self.emit(sec, [last], c, end, spec, m, bool(m))
        if tail is not None:
            rival = self.ep.other(last.who)
            self.fill(tail, b, sec, [self.react_spec(rival) | dict(sung=False)], v.shot_cn)

    def announce_time(self, k: str, ls: list[TimedLine]) -> float | None:
        """When the host says rapper k's name (name_cn / aka / nickname) in the entrance lines.
        Episode.mentions_of skips the rappers on purpose, so the entrance matches names itself."""
        c = self.ep.cast[k]
        for ln in ls:
            pos = [ln.text.find(n) for n in [c.name_cn, c.aka, *c.nicknames] if n]
            pos = [p for p in pos if p >= 0]
            if not pos:
                continue
            i = len(han(ln.text[:min(pos)]))
            if ln.chars:
                return round(ln.chars[min(i, len(ln.chars) - 1)] - 0.08, 3)
            return ln.t0
        return None

    def entrance_section(self, sec: Section, v, ls: list[TimedLine]) -> None:
        """Split screen first, then each rapper's CU (with the name card) cut on the word that names them."""
        a, b = sec.t0, sec.t1
        specs = self.fill_specs("entrance", "body")
        split, cus = specs[0], specs[1:]
        both = [self.left, self.right]
        t = {k: self.announce_time(k, ls) for k in both}
        if b - a < 3 * MIN_SHOT or any(x is None for x in t.values()):
            return self.fill(a, b, sec, specs, v.shot_cn, exact=True)
        order = sorted(both, key=lambda k: t[k])  # whoever is announced first is cut to first
        c1 = min(max(self.snap(t[order[0]], 0.1), a + MIN_SHOT), b - 2 * MIN_SHOT)
        c2 = min(max(self.snap(t[order[1]], 0.1), c1 + MIN_SHOT), b - MIN_SHOT)
        cu = {k: s for k, s in zip(both, cus)}
        for (t0, t1), spec in zip(((a, c1), (c1, c2), (c2, b)), (split, cu[order[0]], cu[order[1]])):
            spec = dict(spec)
            self.add(t0, t1, sec, spec.pop("staging"), spec.pop("kind"), spec.pop("who"), sung=False, **spec)

    def section(self, vi: int, sec: Section) -> None:
        v = self.ep.verses[vi]
        ls = [ln for ln in self.timing.lines if ln.verse == vi]
        if v.kind == "verse":
            self.rot = 0
        if v.kind == "reveal" and ls and self.ok("blackout_spot"):
            return self.reveal_section(sec, vi, ls)
        if v.kind == "entrance" and ls:
            return self.entrance_section(sec, v, ls)
        if not ls or v.kind in ("entrance", "faceoff"):
            exact = v.kind == "entrance"
            return self.fill(sec.t0, sec.t1, sec, self.fill_specs(v.kind, "body", v.who), v.shot_cn,
                             end_on_last=v.kind == "outro", exact=exact)
        return self.lines_section(sec, vi, ls)


def plan_show(ep: Episode, timing: Timing) -> Board:
    if len(timing.sections) != len(ep.verses):
        raise ValueError("timing.json does not match the show sections; re-run: aigc-mv ep analyze")
    p = _ShowPlanner(ep, timing)
    for vi, sec in enumerate(timing.sections):
        p.section(vi, sec)
    shots = p.shots
    # safety: absorb slivers, close the tiling exactly
    out: list[BoardShot] = []
    for s in shots:
        if out and s.t1 - s.t0 < 0.5 and s.kind not in ("react",):
            out[-1].t1 = s.t1
            out[-1].lines = sorted(set(out[-1].lines) | set(s.lines))
            continue
        if out:
            s.t0 = out[-1].t1
        out.append(s)
    out[0].t0 = 0.0
    out[-1].t1 = round(timing.duration, 3)
    for i, s in enumerate(out, 1):
        s.id = f"s{i:03d}"
    units = group_units(ep, out, timing)
    return Board(title=ep.title, grammar="show", look=ep.look, duration=timing.duration, shots=out, units=units)


__all__ = ["plan_show", "MERGE_MAX"]
