"""Episode file (`episode.yaml`): the one creative source of truth for a battle / MV / variety show.

Everything downstream (analysis, board, prompts, edit) reads this file; nothing writes it.

`format: show` is the variety-show template modelled on 《火影有嘻哈03》 (docs/参考片拆解_火影有嘻哈03.md):
a multi-role cast (two rappers, their teammates, judges, host, DJ, hook singers, audience cameos) and an
ordered list of sections (`verses`, each with a `kind`) from the cold open to the crowd-call outro.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator


class LyricLine(BaseModel):
    """One rap line = one bar. Half-lines are separated by a single space."""

    text: str
    note: str = Field("", description="史料注释, shown under the subtitle")
    action: str = Field("", description="照字面演的动作 (the gag the performer acts out)")
    cutaway: str = Field(
        "",
        description="Optional narrative insert that enacts the allusion (Keynes-vs-Hayek style). "
        "Becomes its own non-sung shot over this line.",
    )
    location: str | None = Field(None, description="Key into Episode.locations; overrides the verse")
    sung_as: str = Field("", description="Homophone spelling for Suno (生僻字), subtitles keep text")
    punch: bool | None = Field(None, description="Punchline; default = last line of each 4-line stanza")
    framing: str | None = Field(None, description="Force framing (ECU/CU/MCU/MS/WS/OTS/2S)")
    camera: str | None = Field(None, description="Force a camera move id from cinema.MOVES")
    who: str | None = Field(None, description="Per-line singer override (cast key); default = the section's who")
    beats: float | None = Field(None, description="Line length in beats (show / line_beats=auto); default from length")
    pause_beats: float = Field(0, description="Silence before the line in beats (the reveal pause)")
    mentions: list[str] = Field(default_factory=list, description="Cast keys this line names (cut to their reaction)")
    spoken: bool = Field(False, description="念白: host lines and shouted crowd calls")

    @property
    def halves(self) -> list[str]:
        parts = [p for p in self.text.split() if p]
        return parts or [self.text]


SectionKind = Literal["verse", "cold_open", "host", "entrance", "faceoff", "hook", "interlude", "reveal", "outro"]


class Verse(BaseModel):
    """A section of the song. Battle / MV episodes only use `kind: verse`; shows use the whole list."""

    who: str | None = Field(None, description="Cast key of the section's singer, e.g. 'a' or 'b'")
    kind: SectionKind = "verse"
    location: str | None = Field(None, description="Default location key for this verse")
    lines: list[LyricLine] = Field(default_factory=list, description="Empty for instrumental sections")
    bars: int | None = Field(None, description="Length of a section without lines, or its minimum length")
    gap_bars: int | None = Field(
        None, description="Instrumental bars before the section; None = break_bars between verses (battle/mv), 0 (show)")
    shot_cn: str = Field("", description="Picture for instrumental / host sections (show planner)")
    suno_pass: int | None = Field(None, description="Which Suno generation / Extend pass sings this section")


Role = Literal["rapper", "teammate", "judge", "host", "dj", "hook", "cameo"]


class CastMember(BaseModel):
    character: str = Field(..., description="Character id in knowledge/characters")
    name_cn: str
    name_en: str = ""
    aka: str = ""
    role: Role = "rapper"
    side: Literal["left", "right", "center"] = "left"
    team: str | None = Field(None, description="Cast key of the rapper a teammate backs")
    position_cn: str = Field("", description="Where the person is in the venue, e.g. 评委席中间的王座 / DJ台后面")
    title_cn: str = Field("", description="Lower-third caption")
    nicknames: list[str] = Field(default_factory=list, description="Extra names used for mention detection")
    voice: str = Field("", description="Suno voice description (style field)")
    listen_cn: str = Field("冷眼看着，嘴角一点点冷笑", description="Reaction while the other raps")
    pitch: float = 0.0


class Location(BaseModel):
    cn: str
    en: str = ""
    light_cn: str = ""
    light_en: str = ""


class Budget(BaseModel):
    cap_usd: float = 60.0
    price_per_sec_usd: float = Field(0.23, description="List price per generated second (720p)")
    confirm_over_usd: float = 5.0
    frozen: bool = False


class Episode(BaseModel):
    title: str
    format: Literal["battle", "mv", "show"] = "battle"
    grammar: Literal["show", "mv", "hybrid"] = Field(
        "hybrid",
        description="show = 综艺擂台多机位直播感; mv = 叙事 MV (location performance + story); hybrid = both",
    )
    look: str = Field("night_arena", description="Look preset key in cinema.LOOKS")
    realism: Literal["gritty", "idol_show"] = Field(
        "gritty", description="gritty = 历史片实拍质感; idol_show = 选秀综艺棚拍质感 (still real skin)")
    show_name: str = Field("", description="Programme name (show format)")
    episode_no: str = Field("", description="e.g. 第一期")
    logo_bug: str = Field("", description="Corner logo text; empty = show_name")
    show_notes: bool = Field(True, description="Burn line notes into the subtitles")
    line_beats: Literal["bar", "auto"] = Field(
        "bar", description="bar = one line per bar (battle/mv default); auto = per-line beats (always on for show)")
    aspect: str = "16:9"
    fps: int = 24
    resolution: str = "720p"

    song: str = "audio/song.wav"
    vocals: str | None = Field("audio/vocals.wav", description="Suno lead-vocal stem (preferred)")
    instrumental: str | None = "audio/instrumental.wav"
    bpm_hint: float | None = None
    intro_bars: int = Field(1, description="Bars before the first line (grid alignment fallback)")
    break_bars: int = Field(2, description="Bars between verses (grid alignment fallback)")
    outro_bars: int = 3

    cast: dict[str, CastMember]
    venue: Location
    locations: dict[str, Location] = Field(default_factory=dict)
    crowd_cn: str = "台下挤满了观众，举着火把和拳头"
    verses: list[Verse]

    intro_cn: str = ""
    break_cn: str = ""
    outro_cn: str = ""
    break_chant: str = ""
    end_question: str = "下一场|你想看谁的对决？"
    watermark: str = ""
    disclaimer: str = "AI生成  仅供娱乐"
    subtitle_style: Literal["broadcast", "gold"] = "broadcast"
    budget: Budget = Field(default_factory=Budget)

    @model_validator(mode="after")
    def _check(self) -> "Episode":
        for k, c in self.cast.items():
            if c.team is not None:
                if c.team not in self.cast:
                    raise ValueError(f"cast.{k}.team={c.team!r} not in cast {list(self.cast)}")
                if self.cast[c.team].role != "rapper":
                    raise ValueError(f"cast.{k}.team={c.team!r} is not a rapper")
        rappers = [k for k, c in self.cast.items() if c.role == "rapper"]
        if self.format in ("battle", "show"):
            if len(rappers) != 2:
                raise ValueError(f"a {self.format} needs exactly two rappers (role: rapper), got {rappers}")
            if {self.cast[k].side for k in rappers} != {"left", "right"}:
                raise ValueError("the two rappers must stand on different sides (left / right)")
        elif len(rappers) == 2 and self.cast[rappers[0]].side == self.cast[rappers[1]].side:
            raise ValueError("the two rappers must stand on different sides (left / right)")
        beat_mode = self.format == "show" or self.line_beats == "auto"
        for vi, v in enumerate(self.verses):
            if v.who is not None and v.who not in self.cast:
                raise ValueError(f"verse.who={v.who!r} not in cast {list(self.cast)}")
            if v.kind == "verse" and (v.who is None or self.cast[v.who].role != "rapper"):
                raise ValueError(f"section {vi + 1} (kind verse) must be sung by a rapper, got who={v.who!r}")
            if not v.lines and (not beat_mode or not v.bars):
                raise ValueError(f"section {vi + 1} ({v.kind}) has no lines: give it `bars` (show / line_beats auto)")
            for ln in v.lines:
                if ln.who is not None and ln.who not in self.cast:
                    raise ValueError(f"line.who={ln.who!r} not in cast ({ln.text!r})")
                if (ln.who or v.who) is None:
                    raise ValueError(f"line {ln.text!r} has no singer: set who on the line or the section")
                for m in ln.mentions:
                    if m not in self.cast:
                        raise ValueError(f"line.mentions {m!r} not in cast ({ln.text!r})")
            keys = [v.location] + [ln.location for ln in v.lines]
            for k in keys:
                if k and k not in self.locations:
                    raise ValueError(f"location {k!r} not defined in episode.locations")
        return self

    def rappers(self) -> list[str]:
        """[left rapper, right rapper] (battle / show); other formats: rappers in yaml order."""
        keys = self.members("rapper")
        return sorted(keys, key=lambda k: {"left": 0, "center": 1, "right": 2}[self.cast[k].side])

    def members(self, *roles: str) -> list[str]:
        """Cast keys with one of `roles` (all when empty), in yaml order."""
        return [k for k, c in self.cast.items() if not roles or c.role in roles]

    def other(self, who: str) -> str:
        """The other rapper; for a non-rapper, the first rapper."""
        rs = self.rappers()
        if who in rs:
            keys = [k for k in rs if k != who]
            return keys[0] if keys else who
        return rs[0] if rs else who

    def team(self, rapper: str) -> list[str]:
        return [k for k, c in self.cast.items() if c.role == "teammate" and c.team == rapper]

    def singer_of(self, verse: Verse, line: LyricLine) -> str:
        return line.who or verse.who  # type: ignore[return-value]

    def mentions_of(self, verse: Verse, line: LyricLine) -> list[str]:
        """Cast members a line names (explicit `mentions` first, then names found in the text, by position),
        minus the singer and the two rappers (the rival is 'you' in every line)."""
        skip = {self.singer_of(verse, line), *self.rappers()}
        found: list[tuple[int, str]] = []
        for k, c in self.cast.items():
            pos = [line.text.find(n) for n in [c.name_cn, c.aka, *c.nicknames] if n]
            pos = [p for p in pos if p >= 0]
            if pos:
                found.append((min(pos), k))
        out: list[str] = []
        for k in [*line.mentions, *(k for _, k in sorted(found))]:
            if k not in skip and k not in out:
                out.append(k)
        return out

    def all_lines(self) -> list[tuple[int, int, Verse, LyricLine]]:
        """(verse index, line index, verse, line) in song order."""
        return [(vi, li, v, ln) for vi, v in enumerate(self.verses) for li, ln in enumerate(v.lines)]

    def location_of(self, verse: Verse, line: LyricLine) -> tuple[str, Location]:
        key = line.location or verse.location
        if key:
            return key, self.locations[key]
        return "venue", self.venue


def load_episode(project_dir: Path) -> Episode:
    path = Path(project_dir) / "episode.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"no episode.yaml in {project_dir}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return Episode.model_validate(data)
