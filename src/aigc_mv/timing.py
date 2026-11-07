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
    conf: float = Field(1.0, description="ASR: share of the line's characters heard (0-1); grid: 1")
    source: str = Field("", description="ASR: audio the line was matched on (vocals / song / instrumental)")
    flags: list[str] = Field(default_factory=list, description="ASR checks: low_conf, interpolated, ...")
    heard: str = Field("", description="ASR: what was recognised over the line's span")


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


ASR_MODEL = "large-v3-turbo"


ASR_CHUNK = (8.0, 24.0)  # min / max chunk length (s); whisper drops whole phrases on long rap files
# whisper's well-known silence / music hallucinations (subtitle credits, video-site boilerplate)
HALLUCINATIONS = ("字幕", "志愿者", "李宗盛", "杨茜茜", "优优", "独播", "剧场", "YoYo", "Television", "感谢观看",
                  "不吝", "点赞", "订阅", "转发", "打赏", "明镜", "栏目")


def quiet_cuts(x: np.ndarray, sr: int, lo: float = ASR_CHUNK[0], hi: float = ASR_CHUNK[1]) -> list[tuple[int, int]]:
    """Split audio into chunks of lo..hi seconds, each cut at the quietest 100 ms frame of the search range."""
    w = max(1, int(0.1 * sr))
    n = len(x) // w
    rms = np.sqrt(np.mean(x[: n * w].reshape(n, w) ** 2, axis=1)) if n else np.zeros(0)
    out, a = [], 0
    while (len(x) - a) / sr > hi:
        f0, f1 = int((a / sr + lo) / 0.1), min(n, int((a / sr + hi) / 0.1))
        k = f0 + int(np.argmin(rms[f0:f1])) if f1 > f0 else f1
        b = int((k + 0.5) * w)
        out.append((a, b))
        a = b
    out.append((a, len(x)))
    return out


def clean_words(words: list[list]) -> list[list]:
    """Drop hallucinated credits (also when whisper splits them into one-character words) and zero-length runs
    (3+ words stacked on one timestamp)."""
    text, owner = "", []
    for i, w in enumerate(words):
        s = str(w[0]).strip()
        text += s
        owner += [i] * len(s)
    bad = set()
    for h in HALLUCINATIONS:
        k = text.find(h)
        while k >= 0:
            bad.update(owner[k:k + len(h)])
            k = text.find(h, k + 1)
    keep = [w for i, w in enumerate(words) if i not in bad]
    out = []
    for i, w in enumerate(keep):
        run = [v for v in keep[max(0, i - 2): i + 3] if v[2] - v[1] < 0.02]
        if w[2] - w[1] < 0.02 and len(run) >= 3:
            continue
        out.append(w)
    return out


def _transcribe_words(audio: Path, prompt: str = "") -> list[list]:  # pragma: no cover - heavy model
    from faster_whisper import WhisperModel

    x, sr = load_audio(audio, sr=16000)
    m = WhisperModel(ASR_MODEL, device="cpu", compute_type="int8")
    out: list[list] = []
    for a, b in quiet_cuts(x, sr):
        segs, _ = m.transcribe(x[a:b], language="zh", word_timestamps=True, initial_prompt=prompt or None,
                               condition_on_previous_text=False, beam_size=5)
        t0 = a / sr
        out += [[w.word, round(t0 + w.start, 3), round(t0 + w.end, 3), round(w.probability, 3)]
                for s in segs for w in s.words]
    return clean_words(out)


def chars_from_words(words: list[list]) -> list[tuple[str, float, float]]:
    """Split ASR words ([text, start, end, prob]) into (CJK char, start, end), spread evenly over the word."""
    out: list[tuple[str, float, float]] = []
    for w in words:
        cs = [c for c in str(w[0]).strip() if "\u4e00" <= c <= "\u9fff"]
        step = (w[2] - w[1]) / max(1, len(cs))
        out += [(c, round(w[1] + i * step, 3), round(w[1] + (i + 1) * step, 3)) for i, c in enumerate(cs)]
    return out


def asr_words(audio: Path, prompt: str = "", cache: Path | None = None) -> list[list]:
    """faster-whisper words ([text, start, end, prob]) for one audio file, transcribed in chunks cut at quiet
    points, cached as JSON (keyed on file size + mtime + model + chunking + prompt)."""
    import json

    audio = Path(audio)
    st = audio.stat()
    key = {"audio": audio.name, "size": st.st_size, "mtime": int(st.st_mtime), "model": ASR_MODEL,
           "chunk": list(ASR_CHUNK), "prompt": prompt}
    if cache is not None and cache.is_file():
        try:
            d = json.loads(cache.read_text(encoding="utf-8"))
            if d.get("key") == key:
                return d["words"]
        except (ValueError, KeyError):
            pass
    words = _transcribe_words(audio, prompt)
    if cache is not None:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({"key": key, "words": words}, ensure_ascii=False, indent=0), encoding="utf-8")
    return words


def _asr_chars(vocals: Path, prompt: str = "", cache: Path | None = None) -> list[tuple[str, float]]:
    return chars_from_words(asr_words(vocals, prompt, cache))


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


# ---- ASR alignment on a real take: monotonic DP per stem, per-line fallback, confidence + flags

CONF_OK = 0.6  # a line below this share of heard characters is flagged low_conf
# a line the lead stem heard at CONF_OK or better only moves to a fallback stem if that stem hears at least this
# much more of it (one extra character is not worth the mix's blurrier onsets); weaker lines move on any gain
FALLBACK_GAIN = 0.15
CHAR_STEP = 0.18  # seconds per unheard character when there is room
LONG_GAP = 1.2  # a pause inside one line longer than this is flagged
ONSET_DB = 12.0  # a vocal frame this far under the coming peak counts as quiet (onset snapping)
CLUSTER_GAP = 2.5  # heard characters of one line further apart than this are not the same take of the line
_FUZZY = (("zh", "z"), ("ch", "c"), ("sh", "s"), ("ing", "in"), ("eng", "en"))


def fuzzy_key(c: str) -> str:
    """Toneless pinyin with the usual rap / ASR mergers folded (zh=z, ch=c, sh=s, ing=in, eng=en)."""
    k = _key(c)
    for a, b in _FUZZY:
        k = k.replace(a, b)
    return k


def dp_match(sheet: list[str], heard: list[str]) -> list[int | None]:
    """Monotonic alignment of sheet keys to heard keys: the heard index for every sheet item (None = unheard).

    Unlike difflib's greedy longest-block-first matching, this maximises the total score over the whole song,
    with runs of consecutive matches worth more than scattered single characters, so a phrase that recurs in
    two sections (奇门, 睡到天明, 说了算) cannot pull one section's line onto the other section's audio."""
    n, m = len(sheet), len(heard)
    if not n or not m:
        return [None] * n
    eq = np.array(sheet, dtype=object)[:, None] == np.array(heard, dtype=object)[None, :]
    neg = -(10**8)
    best = np.zeros((n + 1, m + 1), dtype=np.int64)
    run = np.full((n + 1, m + 1), neg, dtype=np.int64)
    for i in range(1, n + 1):
        r = np.full(m + 1, neg, dtype=np.int64)
        r[1:] = np.where(eq[i - 1], np.maximum(best[i - 1, :-1] + 1, run[i - 1, :-1] + 2), neg)
        run[i] = r
        best[i] = np.maximum.accumulate(np.maximum(best[i - 1], r))
    out: list[int | None] = [None] * n
    i, j, in_run = n, m, False
    while i > 0 and j > 0:
        if in_run:
            out[i - 1] = j - 1
            in_run = run[i - 1, j - 1] > neg and run[i - 1, j - 1] + 2 == run[i, j]
            i, j = i - 1, j - 1
        elif best[i, j] == best[i, j - 1]:  # ties go to the earliest heard character
            j -= 1
        elif run[i, j] > neg and run[i, j] == best[i, j]:
            in_run = True
        else:
            i -= 1
    return out


def _trusted(match: list[int | None], times: list[float], n_line: int) -> list[int | None]:
    """Keep runs of 2+ consecutive matches; a lone matched character survives only next to the line's runs
    (within 1 s). A line of 3+ characters with no run at all counts as unheard (stray 你 / 的 matches)."""
    runs = [False] * len(match)
    for k, j in enumerate(match):
        if j is None:
            continue
        if (k > 0 and match[k - 1] is not None and match[k - 1] == j - 1) or (
                k + 1 < len(match) and match[k + 1] is not None and match[k + 1] == j + 1):
            runs[k] = True
    rt = [times[j] for k, j in enumerate(match) if j is not None and runs[k]]
    if not rt:
        return list(match) if n_line <= 2 else [None] * len(match)
    lo, hi = min(rt) - 1.0, max(rt) + 1.0
    match = [j if j is not None and (runs[k] or lo <= times[j] <= hi) else None for k, j in enumerate(match)]
    # one line cannot be split by a long silence: keep the largest time cluster (whisper sometimes starts a word
    # seconds early, e.g. 嘞 stretched over a scat break)
    ks = [k for k, j in enumerate(match) if j is not None]
    groups, cur = [], [ks[0]] if ks else []
    for a, b in zip(ks, ks[1:]):
        if times[match[b]] - times[match[a]] > CLUSTER_GAP:  # type: ignore[index]
            groups.append(cur)
            cur = []
        cur.append(b)
    if cur:
        groups.append(cur)
    if len(groups) > 1:
        keep = set(max(groups, key=len))
        match = [j if k in keep else None for k, j in enumerate(match)]
    return match


def _place(t: list[float | None], lo: float, hi: float, step: float = CHAR_STEP) -> list[float]:
    """Fill unheard characters of one line between its heard ones, never below lo or above hi."""
    known = [i for i, v in enumerate(t) if v is not None]
    n = len(t)
    if not known:
        span = min(step * n, max(0.02 * n, hi - lo))
        return [lo + span * i / max(1, n) for i in range(n)]
    out = list(t)
    for a, b in zip(known, known[1:]):
        for i in range(a + 1, b):
            out[i] = out[a] + (out[b] - out[a]) * (i - a) / (b - a)
    f, last = known[0], known[-1]
    if f:
        s = min(step, max(0.0, out[f] - lo) / (f + 1))
        for i in range(f):
            out[i] = out[f] - s * (f - i)
    if last < n - 1:
        s = min(step, max(0.0, hi - out[last]) / (n - last))
        for i in range(last + 1, n):
            out[i] = out[last] + s * (i - last)
    return [float(v) for v in out]  # type: ignore[arg-type]


def _onset(t0: float, env: tuple[np.ndarray, float] | None, lo: float, hi: float = 1e9,
           end: float | None = None) -> float:
    """Snap a heard line start to the vocal onset (whisper word starts are often 50-400 ms off). Quiet means
    ONSET_DB under the loudest frame of the next 0.6 s. If t0 sits in a quiet stretch of 80 ms or more, move
    forward to the first loud frame (<= 0.5 s, before hi); otherwise move back to the last quiet -> loud step
    (after >= 40 ms of quiet within 0.4 s, or after a >= 100 ms pause within 0.8 s; never before lo, so never
    into the previous line's last syllable), or, with no pause there (legato), to the latest sharp rise.
    Before all that: whisper often stretches the first word back over a pause (its heard span t0..`end`
    holds >= 150 ms of quiet); then the syllable starts at the first loud frame after the last such pause."""
    if env is None:
        return t0
    db, fps = env
    a, c, e = int(max(lo, t0 - 0.4) * fps), int(t0 * fps), int((t0 + 0.6) * fps)
    if c < 0 or e > len(db) or e <= c:
        return t0
    thr = float(db[c:e].max()) - ONSET_DB
    if end is not None and end - t0 > 0.2:
        w = int(min(len(db), (end + 0.3) * fps))
        thr_w = float(db[c:w].max()) - ONSET_DB
        quiet = db[c:int(end * fps)] < thr_w
        k, run, last = 0, 0, None
        for k, qk in enumerate(quiet):
            run = run + 1 if qk else 0
            if run >= int(0.15 * fps):
                last = k + 1  # end of a long enough pause
        if last is not None:
            loud = np.nonzero(db[c + last:w] >= thr_w)[0]
            if len(loud):
                return round((c + last + int(loud[0])) / fps, 3)
    if db[c] < thr:
        f = int(min(t0 + 0.5, hi) * fps)
        loud = np.nonzero(db[c:f] >= thr)[0]
        if len(loud) and loud[0] >= 0.08 * fps:
            return round(max(t0, (c + int(loud[0])) / fps), 3)
    if c <= a:
        return t0

    def steps(a0: int, quiet_s: float) -> list[int]:
        q = max(1, int(quiet_s * fps))
        return [k for k in range(a0, c) if db[k] < thr <= db[k + 1] and bool((db[max(0, k - q + 1):k + 1] < thr).all())]

    # quiet -> loud after >= 40 ms of quiet within 0.4 s, or after a real pause (>= 100 ms) within 0.8 s
    up = steps(a, 0.04) or steps(int(max(lo, t0 - 0.8) * fps), 0.1)
    if up:
        return round(max(lo, (up[-1] + 1) / fps), 3)
    # no pause before the line: take the latest sharp rise (>= 8 dB in 30 ms up to the line's level)
    k3 = max(1, int(0.03 * fps))
    rise = [k for k in range(a, c + 1) if k + k3 < len(db) and db[k + k3] - db[k] >= 8.0
            and db[k + k3] >= float(db[k:e].max()) - 6.0]
    return round(max(lo, rise[-1] / fps), 3) if rise else t0


def envelope_db(audio: Path, fps: float = 100.0) -> tuple[np.ndarray, float]:
    x, sr = load_audio(audio, sr=16000)
    w = int(sr / fps)
    n = len(x) // w
    rms = np.sqrt(np.mean(x[: n * w].reshape(n, w) ** 2, axis=1))
    return 20 * np.log10(rms + 1e-9), fps


Heard = list[tuple]  # (char, start) or (char, start, end), time-ordered


def align_asr(ep: Episode, grid: BeatGrid, heard: Heard | dict[str, Heard],
              envs: dict[str, tuple[np.ndarray, float]] | None = None) -> list[TimedLine]:
    """Lines timed from ASR characters.

    `heard` is one character list, or {stem: characters} in priority order (lead vocal first, then the full mix,
    then the other stem). The whole sheet is DP-matched on the first stem; every line not fully heard there is
    then re-matched on the next stems, but only against what was heard between its neighbours (no
    cross-matching). A line under CONF_OK moves to a stem that hears strictly more of it; a line the lead stem
    heard at CONF_OK or better moves only if the other stem hears at least FALLBACK_GAIN more.
    Unheard characters are placed between their neighbours inside the line's own section."""
    stems = heard if isinstance(heard, dict) else {"vocals": heard}
    names = list(stems)
    keys = {s: [fuzzy_key(h[0]) for h in stems[s]] for s in names}
    flat = ep.all_lines()
    texts = [han(ln.text) for _, _, _, ln in flat]
    n_lines = len(flat)
    # per line: (times or None per char, heard end per char, source stem)
    got: list[list[float | None]] = [[None] * len(t) for t in texts]
    ends: list[list[float | None]] = [[None] * len(t) for t in texts]
    src = [""] * n_lines

    def take(gi: int, stem: str, match: list[int | None]) -> None:
        hs = stems[stem]
        got[gi] = [hs[j][1] if j is not None else None for j in match]
        ends[gi] = [(hs[j][2] if len(hs[j]) > 2 else None) if j is not None else None for j in match]
        src[gi] = stem if any(j is not None for j in match) else ""

    lead = names[0]
    sheet = [fuzzy_key(c) for t in texts for c in t]
    m = dp_match(sheet, keys[lead])
    lead_t = [h[1] for h in stems[lead]]
    k = 0
    for gi, t in enumerate(texts):
        take(gi, lead, _trusted(m[k:k + len(t)], lead_t, len(t)))
        k += len(t)

    def conf(gi: int) -> float:
        return sum(v is not None for v in got[gi]) / max(1, len(got[gi]))

    def bounds(gi: int) -> tuple[float, float]:
        lo = max((v for g in range(gi) for v in got[g] if v is not None), default=0.0)
        hi = min((v for g in range(gi + 1, n_lines) for v in got[g] if v is not None), default=grid.duration)
        return lo, hi

    for gi, t in enumerate(texts):
        if conf(gi) >= 1.0:
            continue
        for stem in names[1:]:
            lo, hi = bounds(gi)
            idx = [j for j, h in enumerate(stems[stem]) if lo + 0.02 < h[1] < hi - 0.02]
            if not idx:
                continue
            sub = dp_match([fuzzy_key(c) for c in t], [keys[stem][j] for j in idx])
            sub = _trusted(sub, [stems[stem][j][1] for j in idx], len(t))
            match = [idx[j] if j is not None else None for j in sub]
            share, c0 = sum(j is not None for j in match) / max(1, len(t)), conf(gi)
            strong = src[gi] == lead and c0 >= CONF_OK
            if (share >= c0 + FALLBACK_GAIN - 1e-9) if strong else (share > c0 + 1e-9):
                take(gi, stem, match)
    if not any(v is not None for g in got for v in g):
        raise ValueError("no lyric characters were recognised in the vocal")

    # place unheard characters: inside the line between heard ones; whole unheard lines between their
    # neighbours, each line of a run of unheard lines getting an equal share of the gap
    times: list[list[float]] = [[] for _ in texts]
    gi = 0
    while gi < n_lines:
        if any(v is not None for v in got[gi]):
            lo, hi = bounds(gi)
            times[gi] = _place(got[gi], lo + 0.05, hi - 0.05)
            gi += 1
            continue
        j = gi
        while j < n_lines and not any(v is not None for v in got[j]):
            j += 1
        n_ch = sum(map(len, texts[gi:j]))
        hi = bounds(j - 1)[1] - 0.1 if j < n_lines else grid.duration - 0.1
        lo = times[gi - 1][-1] + 0.3 if gi else max(0.0, hi - CHAR_STEP * n_ch - 0.5)
        hi = max(hi, lo + 0.02 * n_ch)
        share = (hi - lo) / (j - gi)
        for g in range(gi, j):
            a = lo + share * (g - gi)
            times[g] = _place(got[g], a, a + share * 0.9)
        gi = j

    lines: list[TimedLine] = []
    prev_last = -1.0
    for gi, (vi, li, v, ln) in enumerate(flat):
        flags: list[str] = []
        ts = times[gi]
        if got[gi] and got[gi][0] is None:
            flags.append("interpolated")
        if any(v is not None for v in got[gi]):
            env = (envs or {}).get(lead)  # the lead stem holds every voice; the mix's beat hides the onsets
            e0 = ends[gi][0] if got[gi][0] is not None else None
            ts = [_onset(ts[0], env, prev_last + 0.1, end=e0)] + ts[1:]  # later characters are pushed on below
        pushed = False
        out = []
        for x in ts:
            y = max(x, (out[-1] if out else prev_last) + 0.02)
            pushed |= not out and y > x + 1e-6
            out.append(round(y, 3))
        if pushed:
            flags.append("overlaps_prev")
        c = conf(gi)
        if c == 0:
            flags.append("possibly_skipped")
        elif c < CONF_OK:
            flags.append("low_conf")
        if any(b - a > LONG_GAP for a, b in zip(out, out[1:])):
            flags.append("long_gap")
        prev_last = out[-1]
        heard_end = max((e for e in ends[gi] if e is not None), default=0.0)
        t1 = max(out[-1] + 0.25, min(heard_end, out[-1] + 1.2))
        heard_txt = ""
        if src[gi]:
            h0 = min([out[0]] + [v for v in got[gi] if v is not None])
            heard_txt = "".join(h[0] for h in stems[src[gi]] if h0 - 0.05 <= h[1] <= t1)
            if 0 < c < CONF_OK and len(heard_txt) >= CONF_OK * len(out):
                flags.append("sung_differently")
        lines.append(TimedLine(idx=gi, verse=vi, line=li, who=ep.singer_of(v, ln), text=ln.text, t0=out[0],
                               t1=round(t1, 3), bar=max(0, grid.bar_index(out[0] + 0.13)), phrases=[],
                               chars=out, kind=v.kind, spoken=ln.spoken, conf=round(c, 3), source=src[gi],
                               flags=flags, heard=heard_txt))
    for a, b in zip(lines, lines[1:]):
        a.t1 = round(max(a.chars[-1] + 0.02, min(a.t1, b.t0 - 0.05)), 3)
    for ln in lines:
        ln.phrases = _phrases_from_chars(ln.text, ln.chars, ln.t1)
    return lines


def _line_starts(ep: Episode, lines: list[TimedLine], duration: float, grid: BeatGrid) -> list[float]:
    """Section starts from the aligned lines alone (a real take): a sung section starts on a downbeat up to one
    beat before its first line, else on a beat up to half a beat before it, else 0.1 s before it (never on the
    previous section's last line); a section without lines starts on the first downbeat after the previous
    line has ended."""
    db = list(grid.downbeats)
    n = len(ep.verses)
    first = {vi: min(ln.t0 for ln in lines if ln.verse == vi) for vi in {ln.verse for ln in lines}}
    last = {vi: max(ln.t1 for ln in lines if ln.verse == vi) for vi in first}
    starts: list[float] = []
    prev_end = 0.0
    for vi in range(n):
        if not vi:
            starts.append(0.0)
        elif vi in first:
            f = first[vi]
            lo = prev_end + 0.05
            on_db = [d for d in db if max(lo, f - grid.beat) <= d <= f - 0.05]
            on_beat = [d for d in grid.beats if max(lo, f - grid.beat / 2) <= d <= f - 0.05]
            pick = on_db or on_beat
            starts.append(max(pick[-1] if pick else max(prev_end + 0.02, f - 0.1), starts[-1]))
        else:
            nxt = min((first[k] for k in first if k > vi), default=duration)
            cand = [d for d in db if prev_end + 0.05 <= d <= nxt - 0.6]
            starts.append(max(cand[0] if cand else (prev_end + nxt) / 2, starts[-1]))
        if vi in last:
            prev_end = max(prev_end, last[vi])
    return starts


def show_sections(ep: Episode, lines: list[TimedLine], duration: float, grid: BeatGrid,
                  layout: bool = True) -> list[Section]:
    """One Section per show section (instrumental ones included), tiling 0 -> duration.

    layout=True (grid alignment): starts come from the beat layout, then are clamped to the aligned lines: a
    section never starts after its own first line nor before the previous section's last line has ended.
    layout=False (ASR on a real take, which never matches the synthetic layout): starts come from the lines
    themselves, snapped to downbeats (see _line_starts), instrumental sections included."""
    out: list[Section] = []
    lay: list[float | None]
    if not layout:
        lay = list(_line_starts(ep, lines, duration, grid))
    else:
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
                        grid: BeatGrid | None = None, layout: bool = True) -> list[Section]:
    if ep.format == "show":
        if grid is None:
            raise ValueError("show sections need the beat grid")
        return show_sections(ep, lines, duration, grid, layout=layout)
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
        heard, envs = {}, {}
        for name, rel in (("vocals", ep.vocals), ("song", ep.song), ("instrumental", ep.instrumental)):
            p = project_dir / rel if rel else None
            if p is None or not p.is_file():
                continue
            heard[name] = _asr_chars(p, cache=project_dir / "analysis" / f"asr_{name}.json")
            envs[name] = envelope_db(p)
        lines = align_asr(ep, grid, heard, envs)
        used = "asr"
    elif ep.format == "show" or ep.line_beats == "auto":
        lines = align_beats(ep, grid)
        used = "grid"
    else:
        lines = align_grid(ep, grid)
        used = "grid"
    sections = sections_from_lines(ep, lines, dur, grid, layout=used != "asr")
    if used == "asr":
        flag_sections(lines, sections, show=ep.format == "show")
    return Timing(duration=dur, grid=grid, lines=lines, sections=sections, bar_energy=energy, mode=used)


def flag_sections(lines: list[TimedLine], sections: list[Section], show: bool = True) -> None:
    """Flag lines that do not sit inside their own section (show: one section per verse) or start out of order."""
    prev = -1.0
    for ln in lines:
        if show and ln.verse < len(sections):
            s = sections[ln.verse]
            if not (s.t0 <= ln.t0 and ln.t1 <= s.t1 + 0.3) and "outside_section" not in ln.flags:
                ln.flags.append("outside_section")
        if ln.t0 <= prev and "overlaps_prev" not in ln.flags:
            ln.flags.append("overlaps_prev")
        prev = ln.t0


def load_timing(project_dir: Path) -> Timing:
    p = Path(project_dir) / "analysis" / "timing.json"
    if not p.is_file():
        raise FileNotFoundError(f"missing {p}; run: aigc-mv ep analyze {project_dir}")
    return Timing.model_validate_json(p.read_text(encoding="utf-8"))


__all__ = ["BeatGrid", "Timing", "TimedLine", "Phrase", "Section", "analyze", "align_beats", "beat_layout",
           "line_beats", "load_timing", "media_duration"]
