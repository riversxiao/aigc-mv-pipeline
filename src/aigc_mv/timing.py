"""Song analysis: beat grid + downbeats, line / half-line timing, sections and per-bar energy.

Writes `analysis/timing.json`. Two alignment modes:

* ``asr``  – faster-whisper character times on the vocal stem, matched to the lyric sheet by pinyin
             (homophones count), unmatched characters interpolated. Needs ``pip install faster-whisper pypinyin``.
* ``grid`` – no ASR: one lyric line per bar from the beat grid. Good enough to board and previz;
             re-run with ASR once the real Suno take is locked. Show episodes (and ``line_beats: auto``) use a
             beat cursor instead: every line lasts its own number of beats (``beats`` or from its length).

Rules carried over from production (ancient-rap-battle + claudia.gallery):
- the beat grid sits on the kick, never on hats; tempo is searched in a pinned range to avoid half/double time;
- every beat is snapped to the strongest onset within ±30 ms so Suno's tempo drift is followed;
- line starts never sit on the previous line's spilled last syllable.
"""

from __future__ import annotations

import difflib
import math
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, Field

from aigc_mv.episode import Episode, LyricLine
from aigc_mv.tools import han, load_audio, media_duration


class BeatGrid(BaseModel):
    bpm: float
    beats: list[float]
    downbeats: list[float]
    duration: float
    source: str = "flux"

    @property
    def beat(self) -> float:
        return 60.0 / self.bpm

    @property
    def bar(self) -> float:
        return 240.0 / self.bpm

    def bar_index(self, t: float) -> int:
        """Index of the bar containing t (−1 before the first downbeat)."""
        idx = int(np.searchsorted(np.array(self.downbeats), t + 1e-6, side="right")) - 1
        return idx

    def nearest_beat(self, t: float) -> float:
        b = np.array(self.beats)
        return float(b[np.argmin(np.abs(b - t))]) if len(b) else t


class Phrase(BaseModel):
    text: str
    t0: float
    t1: float


class TimedLine(BaseModel):
    idx: int = Field(..., description="Global line index in song order")
    verse: int
    line: int
    who: str
    text: str
    t0: float
    t1: float
    bar: int
    phrases: list[Phrase]
    chars: list[float] = Field(default_factory=list, description="Start time of every CJK character")
    kind: str = Field("verse", description="Kind of the section the line belongs to")
    spoken: bool = False


class Section(BaseModel):
    name: str
    kind: Literal["intro", "verse", "break", "outro", "cold_open", "host", "entrance", "faceoff", "hook",
                  "interlude", "reveal"]
    t0: float
    t1: float
    who: str | None = None


class Timing(BaseModel):
    duration: float
    grid: BeatGrid
    lines: list[TimedLine]
    sections: list[Section]
    bar_energy: list[float] = Field(default_factory=list, description="0-1 mix RMS per bar")
    mode: str = "grid"


# --------------------------------------------------------------------------- beat grid

ONSET_N = 512  # analysis window (46 ms at 11.025 kHz)
# a flux peak appears when the onset reaches ~3/4 of the Hann window: report that point, not the frame start
ONSET_OFFSET = 0.75


def _onset_envelope(x: np.ndarray, sr: int, hop: int, lo_hz: float = 0, hi_hz: float = 1e9):
    n = ONSET_N
    if len(x) < n + hop:
        x = np.pad(x, (0, n + hop - len(x)))
    frames = np.lib.stride_tricks.sliding_window_view(x, n)[::hop] * np.hanning(n)
    spec = np.abs(np.fft.rfft(frames, axis=1))
    freqs = np.fft.rfftfreq(n, 1 / sr)
    band = (freqs >= lo_hz) & (freqs <= hi_hz)
    sp = np.log1p(spec[:, band])
    on = np.maximum(np.diff(sp, axis=0), 0).sum(1)
    k = 40
    on = np.maximum(on - np.convolve(on, np.ones(k) / k, "same"), 0)
    return np.concatenate([[0.0], on])


def beat_grid(audio: Path, bpm_hint: float | None = None, bpm_range=(70.0, 160.0)) -> BeatGrid:
    """Single-tempo grid fitted by phase search, then every beat snapped to a local onset (±30 ms)."""
    x, sr = load_audio(audio, sr=11025)
    dur = len(x) / sr
    hop = int(sr / 200)  # 5 ms
    fps = sr / hop
    on = _onset_envelope(x, sr, hop)
    kick = _onset_envelope(x, sr, hop, 30, 150)

    lo, hi = bpm_range
    if bpm_hint:
        lo, hi = bpm_hint * 0.94, bpm_hint * 1.06

    def score(bpm_list):
        best = (-1.0, 0.0, 0.0)
        for bpm in bpm_list:
            p = 60.0 / bpm * fps
            k = np.arange(0, max(1, int(len(on) / p) - 1))
            for ph in np.arange(0, p, 1.0):
                idx = (ph + k * p).astype(int)
                idx = idx[idx < len(on)]
                s = float(on[idx].sum())
                if s > best[0]:
                    best = (s, float(bpm), ph / fps)
        return best

    _, bpm, b0 = score(np.arange(lo, hi, 0.25))
    _, bpm, b0 = score(np.arange(bpm - 0.3, bpm + 0.3, 0.02))
    period = 60.0 / bpm
    beats = list(np.arange(b0, dur, period))
    # snap each beat to the strongest onset within ±30 ms (follows Suno's drift)
    snapped = []
    w = int(0.03 * fps)
    for t in beats:
        c = int(t * fps)
        a, b = max(0, c - w), min(len(on), c + w + 1)
        if b > a and on[a:b].max() > 0:
            snapped.append((a + int(np.argmax(on[a:b]))) / fps)
        else:
            snapped.append(t)
    centre = ONSET_OFFSET * ONSET_N / sr
    beats = [float(round(t + centre, 4)) for t in snapped]
    # downbeat phase: the beat phase (mod 4) with the most kick energy
    votes = []
    for ph in range(4):
        idx = [int((t - centre) * fps) for t in beats[ph::4] if 0 <= int((t - centre) * fps) < len(kick)]
        votes.append(float(kick[idx].sum()) if idx else 0.0)
    ph = int(np.argmax(votes))
    downbeats = beats[ph::4]
    # extend the grid backwards so bar 0 starts at or before 0.5 s
    while downbeats and downbeats[0] - 4 * period > -0.15:
        downbeats.insert(0, round(max(0.0, downbeats[0] - 4 * period), 4))
    return BeatGrid(bpm=round(bpm, 3), beats=beats, downbeats=downbeats, duration=round(dur, 3))


def synthetic_grid(duration: float, bpm: float) -> BeatGrid:
    period = 60.0 / bpm
    beats = [round(t, 4) for t in np.arange(0.0, duration, period)]
    return BeatGrid(bpm=bpm, beats=beats, downbeats=beats[::4], duration=duration, source="synthetic")


def bar_energy(audio: Path, grid: BeatGrid) -> list[float]:
    x, sr = load_audio(audio, sr=11025)
    out = []
    db = grid.downbeats + [grid.duration]
    for a, b in zip(db, db[1:]):
        seg = x[int(max(0, a) * sr): int(max(0, b) * sr)]
        out.append(float(np.sqrt(np.mean(seg**2))) if len(seg) else 0.0)
    m = max(out) if out else 1.0
    return [round(v / m, 3) if m > 0 else 0.0 for v in out]


# --------------------------------------------------------------------------- alignment


def _phrases_from_chars(text: str, chars: list[float], t_end: float) -> list[Phrase]:
    halves = [p for p in text.split() if p] or [text]
    out, k = [], 0
    for h in halves:
        n = len(han(h)) or 1
        ts = chars[k:k + n]
        k += n
        if not ts:
            continue
        nxt = chars[k] if k < len(chars) else t_end
        out.append(Phrase(text=h, t0=round(ts[0], 3), t1=round(max(ts[-1] + 0.12, nxt - 0.04), 3)))
    for a, b in zip(out, out[1:]):  # neighbouring half-lines never overlap
        a.t1 = round(min(a.t1, b.t0 - 0.02), 3)
    return out


def align_grid(ep: Episode, grid: BeatGrid) -> list[TimedLine]:
    """One line per bar: verse 1 after `intro_bars`, `break_bars` between verses."""
    lines: list[TimedLine] = []
    bar = ep.intro_bars
    db = grid.downbeats
    idx = 0
    for vi, v in enumerate(ep.verses):
        if vi > 0:
            bar += ep.break_bars
        for li, ln in enumerate(v.lines):
            if bar + 1 >= len(db):
                raise ValueError("song too short for the lyric sheet on this beat grid")
            t0 = db[bar] + 0.04
            t_bar_end = db[bar + 1]
            n = max(1, len(han(ln.text)))
            span = (t_bar_end - t0) * 0.88
            chars = [round(t0 + span * i / n, 3) for i in range(n)]
            t1 = round(t0 + span, 3)
            lines.append(TimedLine(idx=idx, verse=vi, line=li, who=ep.singer_of(v, ln), text=ln.text,
                                   t0=round(t0, 3), t1=t1, bar=bar, phrases=_phrases_from_chars(ln.text, chars, t1),
                                   chars=chars, kind=v.kind, spoken=ln.spoken))
            idx += 1
            bar += 1
    return lines


# --------------------------------------------------------------------------- beat-cursor layout (show / auto)


def line_beats(ln: LyricLine) -> float:
    """Beats a line occupies: `beats`, else ceil(han / 3) rounded up to even, clamped to 2-8."""
    if ln.beats:
        return float(ln.beats)
    n = math.ceil(len(han(ln.text)) / 3.0)
    n += n % 2
    return float(min(8, max(2, n)))


class _Block(BaseModel):
    start: float  # beats from the first downbeat
    end: float
    lines: list[tuple[float, float]] = Field(default_factory=list)  # (start beat, length in beats)


def beat_layout(ep: Episode) -> list[_Block]:
    """Section and line positions in beats. Sections start on a downbeat after `gap_bars`
    (+ intro_bars before the first); lines follow each other after their `pause_beats`."""
    show = ep.format == "show"
    out: list[_Block] = []
    cur = ep.intro_bars * 4.0
    for vi, v in enumerate(ep.verses):
        gap = v.gap_bars if v.gap_bars is not None else (0 if show or vi == 0 else ep.break_bars)
        cur = math.ceil(cur / 4.0 - 1e-9) * 4.0 + gap * 4.0
        start = cur
        blk = _Block(start=start, end=start)
        for ln in v.lines:
            cur += ln.pause_beats
            b = line_beats(ln)
            blk.lines.append((cur, b))
            cur += b
        if v.bars:
            cur = max(cur, start + v.bars * 4.0)
        cur = math.ceil(cur / 4.0 - 1e-9) * 4.0
        blk.end = cur
        out.append(blk)
    return out


def layout_bars(ep: Episode) -> int:
    """Song length in bars for the synthetic grid (beat-cursor layout + outro_bars)."""
    lay = beat_layout(ep)
    return int(round((lay[-1].end if lay else 0) / 4.0)) + ep.outro_bars


def _beat_time(grid: BeatGrid, pos: float) -> float:
    db = grid.downbeats
    bar = int(pos // 4)
    if db and abs(pos - 4 * (len(db) - 1)) < 1e-9:
        return db[-1]
    if bar + 1 >= len(db):
        raise ValueError("song too short for the lyric sheet on this beat grid")
    return db[bar] + (db[bar + 1] - db[bar]) * (pos - 4 * bar) / 4.0


def align_beats(ep: Episode, grid: BeatGrid) -> list[TimedLine]:
    """Beat-cursor alignment: each line lasts line_beats(); characters spread over 0.88 of it."""
    lines: list[TimedLine] = []
    idx = 0
    for vi, (v, blk) in enumerate(zip(ep.verses, beat_layout(ep))):
        for li, (ln, (pos, nb)) in enumerate(zip(v.lines, blk.lines)):
            t0 = _beat_time(grid, pos) + 0.04
            t_end = _beat_time(grid, pos + nb)
            n = max(1, len(han(ln.text)))
            span = (t_end - t0) * 0.88
            chars = [round(t0 + span * i / n, 3) for i in range(n)]
            t1 = round(t0 + span, 3)
            lines.append(TimedLine(idx=idx, verse=vi, line=li, who=ep.singer_of(v, ln), text=ln.text,
                                   t0=round(t0, 3), t1=t1, bar=int(pos // 4),
                                   phrases=_phrases_from_chars(ln.text, chars, t1), chars=chars, kind=v.kind,
                                   spoken=ln.spoken))
            idx += 1
    return lines


def _asr_chars(vocals: Path, prompt: str) -> list[tuple[str, float]]:  # pragma: no cover - heavy model
    from faster_whisper import WhisperModel

    x, sr = load_audio(vocals, sr=16000)
    m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
    segs, _ = m.transcribe(x, language="zh", word_timestamps=True, initial_prompt=prompt[:200],
                           condition_on_previous_text=False, beam_size=5)
    out = []
    for s in segs:
        for w in s.words:
            cs = [c for c in w.word.strip() if "\u4e00" <= c <= "\u9fff"]
            step = (w.end - w.start) / max(1, len(cs))
            out += [(c, w.start + i * step) for i, c in enumerate(cs)]
    return out


def _key(c: str) -> str:
    try:
        from pypinyin import lazy_pinyin

        return lazy_pinyin(c)[0]
    except Exception:
        return c


def match_chars(sheet: list[str], heard: list[tuple[str, float]]) -> list[float | None]:
    """Time for every sheet character (None if unmatched), matched by pinyin so homophones count."""
    a = [_key(c) for c in sheet]
    b = [_key(c) for c, _ in heard]
    t: list[float | None] = [None] * len(sheet)
    for i, j, n in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(n):
            t[i + k] = heard[j + k][1]
    return t


def interpolate(t: list[float | None], step: float = 0.18) -> list[float]:
    out = list(t)
    known = [i for i, v in enumerate(out) if v is not None]
    if not known:
        raise ValueError("no lyric characters were recognised in the vocal")
    for i in range(len(out)):
        if out[i] is not None:
            continue
        p = max((k for k in known if k < i), default=None)
        n = min((k for k in known if k > i), default=None)
        if p is not None and n is not None:
            out[i] = out[p] + (out[n] - out[p]) * (i - p) / (n - p)
        elif p is not None:
            out[i] = out[p] + step * (i - p)
        else:
            out[i] = out[n] - step * (n - i)
    # monotonic
    for i in range(1, len(out)):
        out[i] = max(out[i], out[i - 1] + 0.02)
    return [round(float(v), 3) for v in out]


def align_asr(ep: Episode, grid: BeatGrid, heard: list[tuple[str, float]]) -> list[TimedLine]:
    sheet, owner = [], []
    for gi, (vi, li, v, ln) in enumerate(ep.all_lines()):
        for c in han(ln.text):
            sheet.append(c)
            owner.append(gi)
    times = interpolate(match_chars(sheet, heard))
    lines: list[TimedLine] = []
    flat = ep.all_lines()
    for gi, (vi, li, v, ln) in enumerate(flat):
        chars = [times[k] for k in range(len(sheet)) if owner[k] == gi]
        nxt = next((times[k] for k in range(len(sheet)) if owner[k] == gi + 1), None)
        t1 = chars[-1] + 0.25
        if nxt is not None:
            t1 = min(t1, nxt - 0.05)
        lines.append(TimedLine(idx=gi, verse=vi, line=li, who=ep.singer_of(v, ln), text=ln.text, t0=chars[0],
                               t1=round(t1, 3), bar=max(0, grid.bar_index(chars[0] + 0.13)),
                               phrases=_phrases_from_chars(ln.text, chars, t1), chars=chars, kind=v.kind,
                               spoken=ln.spoken))
    return lines


def show_sections(ep: Episode, lines: list[TimedLine], duration: float, grid: BeatGrid) -> list[Section]:
    """One Section per show section (instrumental ones included), tiling 0 -> duration.

    Starts come from the beat layout, then are clamped to the aligned lines: a section never starts after its
    own first line nor before the previous section's last line has ended. With the grid alignment this changes
    nothing; with ASR on a real take (lines drift off the layout) it keeps every line inside its own section."""
    out: list[Section] = []
    try:
        lay = [_beat_time(grid, blk.start) for blk in beat_layout(ep)]
    except ValueError:  # real song shorter than the layout: fall back to the lines alone
        lay = [None] * len(ep.verses)
    first = {vi: min(ln.t0 for ln in lines if ln.verse == vi) for vi in {ln.verse for ln in lines}}
    prev_end = 0.0
    for vi, v in enumerate(ep.verses):
        ls = [ln for ln in lines if ln.verse == vi]
        nxt = min((first[k] for k in first if k >= vi), default=duration)  # own first line, or the next one
        t0 = lay[vi] if lay[vi] is not None else (ls[0].t0 - 0.1 if ls else prev_end)
        if not vi:
            t0 = 0.0
        else:
            t0 = min(max(t0, prev_end + 0.05), nxt - 0.1)
            t0 = max(t0, out[-1].t0)
        if ls:
            prev_end = max(prev_end, max(ln.t1 for ln in ls))
        out.append(Section(name=f"s{vi + 1:02d}_{v.kind}", kind=v.kind, t0=round(max(0.0, t0), 3), t1=0.0,
                           who=v.who))
    for a, b in zip(out, out[1:]):
        a.t1 = b.t0
    if out:
        out[-1].t1 = round(duration, 3)
    return out


def sections_from_lines(ep: Episode, lines: list[TimedLine], duration: float,
                        grid: BeatGrid | None = None) -> list[Section]:
    if ep.format == "show":
        if grid is None:
            raise ValueError("show sections need the beat grid")
        return show_sections(ep, lines, duration, grid)
    out: list[Section] = []
    first = lines[0].t0
    out.append(Section(name="intro", kind="intro", t0=0.0, t1=round(first - 0.05, 3)))
    for vi, v in enumerate(ep.verses):
        ls = [ln for ln in lines if ln.verse == vi]
        a = ls[0].t0 - 0.05
        b = ls[-1].t1 + 0.3
        if vi + 1 < len(ep.verses):
            nxt = next(ln for ln in lines if ln.verse == vi + 1).t0 - 0.05
            b = min(b, nxt)
            out.append(Section(name=f"verse{vi + 1}", kind="verse", t0=round(a, 3), t1=round(b, 3), who=v.who))
            if nxt - b > 0.3:
                out.append(Section(name=f"break{vi + 1}", kind="break", t0=round(b, 3), t1=round(nxt, 3)))
        else:
            out.append(Section(name=f"verse{vi + 1}", kind="verse", t0=round(a, 3), t1=round(b, 3), who=v.who))
            if duration - b > 0.3:
                out.append(Section(name="outro", kind="outro", t0=round(b, 3), t1=round(duration, 3)))
    # make sections tile the song
    for a, b in zip(out, out[1:]):
        a.t1 = b.t0
    return out


def analyze(project_dir: Path, ep: Episode, mode: Literal["auto", "asr", "grid"] = "auto",
            bpm: float | None = None, duration: float | None = None) -> Timing:
    """Run the analysis. Without a song file, `bpm` + `duration` produce a synthetic grid (board/previz)."""
    project_dir = Path(project_dir)
    song = project_dir / ep.song
    if song.is_file():
        grid = beat_grid(song, bpm_hint=bpm or ep.bpm_hint)
        dur = grid.duration
        energy = bar_energy(song, grid)
    else:
        b = bpm or ep.bpm_hint
        if not b:
            raise FileNotFoundError(f"{song} not found; pass --bpm (and --duration) for a synthetic grid")
        if ep.format == "show" or ep.line_beats == "auto":
            bars = layout_bars(ep)
        else:
            n_lines = sum(len(v.lines) for v in ep.verses)
            bars = ep.intro_bars + n_lines + ep.break_bars * (len(ep.verses) - 1) + ep.outro_bars
        dur = duration or round(bars * 240.0 / b + 0.5, 3)
        grid = synthetic_grid(dur, b)
        energy = []
    vocals = project_dir / ep.vocals if ep.vocals else None
    use_asr = mode == "asr"
    if mode == "auto" and vocals and vocals.is_file():
        try:
            import faster_whisper  # noqa: F401

            use_asr = True
        except ImportError:
            use_asr = False
    if use_asr:
        if not (vocals and vocals.is_file()):
            raise FileNotFoundError("ASR alignment needs the vocal stem (episode.vocals)")
        prompt = " ".join(c.name_cn for c in ep.cast.values()) + " " + " ".join(
            ln.text for _, _, _, ln in ep.all_lines()[:6])
        lines = align_asr(ep, grid, _asr_chars(vocals, prompt))
        used = "asr"
    elif ep.format == "show" or ep.line_beats == "auto":
        lines = align_beats(ep, grid)
        used = "grid"
    else:
        lines = align_grid(ep, grid)
        used = "grid"
    return Timing(duration=dur, grid=grid, lines=lines, sections=sections_from_lines(ep, lines, dur, grid),
                  bar_energy=energy, mode=used)


def load_timing(project_dir: Path) -> Timing:
    p = Path(project_dir) / "analysis" / "timing.json"
    if not p.is_file():
        raise FileNotFoundError(f"missing {p}; run: aigc-mv ep analyze {project_dir}")
    return Timing.model_validate_json(p.read_text(encoding="utf-8"))


__all__ = ["BeatGrid", "Timing", "TimedLine", "Phrase", "Section", "analyze", "align_beats", "beat_layout",
           "line_beats", "load_timing", "media_duration"]
