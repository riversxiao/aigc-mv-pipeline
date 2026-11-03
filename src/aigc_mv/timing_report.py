"""Chinese per-line timing report for an ASR-aligned real take (analysis/timing_report.md).

Everything here is measured from timing.json (+ optional stem envelopes); hand-written findings (what Suno
sang differently, episode.yaml edits) come in as a notes markdown file appended at the end.
"""

from __future__ import annotations

import numpy as np

from aigc_mv.episode import Episode
from aigc_mv.timing import Timing, TimedLine

FLAG_CN = {
    "low_conf": "置信度低",
    "interpolated": "起点是估的",
    "outside_section": "超出段落",
    "overlaps_prev": "和上一句挤在一起",
    "long_gap": "句中有长停顿",
    "possibly_skipped": "可能没唱",
    "sung_differently": "唱的和歌词不一样",
}
SOURCE_CN = {"vocals": "主唱轨", "song": "整曲", "instrumental": "伴奏轨（去主唱）", "": "无"}
KIND_CN = {"cold_open": "冷开场", "host": "主持开场", "entrance": "入场", "faceoff": "对峙", "hook": "副歌",
           "verse": "主歌", "interlude": "间奏", "reveal": "揭晓", "outro": "结尾", "intro": "前奏",
           "break": "间奏"}
CHECK_MAX = 8


def _t(x: float) -> str:
    m, s = divmod(max(0.0, x), 60)
    return f"{int(m)}:{s:05.2f}"


def spans(mask: np.ndarray, fps: float, min_s: float) -> list[tuple[float, float]]:
    """(start, end) seconds of every True run of at least min_s."""
    out, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]:
                j += 1
            if (j - i) / fps >= min_s:
                out.append((round(i / fps, 2), round(j / fps, 2)))
            i = j
        else:
            i += 1
    return out


def unsung_vocals(timing: Timing, env: tuple[np.ndarray, float], min_s: float = 2.0,
                  floor_db: float = -40.0) -> list[tuple[float, float]]:
    """Stretches where the lead stem is singing but no lyric line is timed (ad-libs, extra la-la, a repeat)."""
    db, fps = env
    active = db > floor_db
    for ln in timing.lines:
        a, b = int(max(0.0, ln.t0 - 0.2) * fps), int((ln.t1 + 0.6) * fps)
        active[a:b] = False
    # bridge breaths shorter than 0.3 s so one sung phrase is one span
    k = int(0.3 * fps)
    sm = np.convolve(active.astype(float), np.ones(k), "same") > 0
    return spans(sm & (db > floor_db - 10), fps, min_s)


def silence_before(prev: TimedLine, ln: TimedLine, env: tuple[np.ndarray, float] | None) -> float:
    """Longest vocal silence (20 dB under the louder side) between prev's last character and ln's start;
    without an envelope: the gap after prev's last character minus a 0.25 s syllable."""
    if env is None:
        return max(0.0, ln.t0 - prev.chars[-1] - 0.25)
    db, fps = env
    a, b = int(prev.chars[-1] * fps), int(ln.t0 * fps) + 1
    if b <= a:
        return 0.0
    ref = float(db[max(0, a - int(0.3 * fps)):min(len(db), b + int(0.3 * fps))].max())
    runs = spans(db[a:b] < ref - 20.0, fps, 0.0)
    return max((y - x for x, y in runs), default=0.0)


def worst_lines(timing: Timing, n: int = CHECK_MAX) -> list[TimedLine]:
    """Lines most worth an ear check: unheard / low confidence first, then estimated starts and other flags."""
    w = {"possibly_skipped": 3.0, "outside_section": 2.5, "low_conf": 1.5, "sung_differently": 1.0,
         "interpolated": 0.8, "overlaps_prev": 0.6, "long_gap": 0.4}

    def score(ln: TimedLine) -> float:
        return (1.0 - ln.conf) * 2 + sum(w.get(f, 0.3) for f in ln.flags)

    cand = [ln for ln in timing.lines if ln.flags or ln.conf < 1.0]
    return sorted(cand, key=score, reverse=True)[:n]


def _why(ln: TimedLine) -> str:
    parts = [FLAG_CN.get(f, f) for f in ln.flags]
    if ln.conf < 1.0:
        parts.append(f"只听出 {ln.conf:.0%} 的字")
    if ln.heard:
        parts.append(f"ASR 听到「{ln.heard}」")
    return "；".join(parts)


def timing_report(ep: Episode, timing: Timing, envs: dict[str, tuple[np.ndarray, float]] | None = None,
                  files: dict[str, str] | None = None, notes: str = "") -> str:
    g = timing.grid
    envs = envs or {}
    name = {k: c.name_cn for k, c in ep.cast.items()}
    out = [f"# {ep.show_name or ep.title} {ep.episode_no} · 真实歌曲对时报告".replace("  ", " "), ""]
    out.append(f"对时方式 `{timing.mode}`：faster-whisper 逐字时间（主唱轨优先，听不清的句子再到整曲 / 伴奏轨里找，"
               "只在前后两句之间找，不会跨段乱配），按拼音匹配歌词（同音字算对），句首再对齐到主唱轨的起音。")
    out += ["", "## 音频", ""]
    for k, v in (files or {}).items():
        out.append(f"- {SOURCE_CN.get(k, k)}：`{v}`")
    first_db = next((d for d in g.downbeats if d > 0.0), g.downbeats[0] if g.downbeats else 0.0)
    out += [f"- 时长 {timing.duration:.1f} 秒",
            f"- 实测速度 {g.bpm:.2f} BPM（一拍 {g.beat:.3f} 秒，一小节 {g.bar:.3f} 秒），共 {len(g.beats)} 拍",
            f"- 第一拍 {g.beats[0]:.3f} 秒，第一个强拍 {first_db:.3f} 秒" if g.beats else "- 没有拍点"]
    if ep.bpm_hint and abs(ep.bpm_hint - g.bpm) > 0.5:
        out.append(f"- 注意：episode.yaml 的 bpm_hint 是 {ep.bpm_hint}，和实测差 {g.bpm - ep.bpm_hint:+.2f}")

    out += ["", "## 段落", "", "| 段落 | 类型 | 谁 | 开始 | 结束 | 时长 | 句数 |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for vi, s in enumerate(timing.sections):
        n = sum(1 for ln in timing.lines if ln.verse == vi)
        out.append(f"| {s.name} | {KIND_CN.get(s.kind, s.kind)} | {name.get(s.who or '', s.who or '')} | "
                   f"{_t(s.t0)} | {_t(s.t1)} | {s.t1 - s.t0:.1f} 秒 | {n} |")

    out += ["", "## 逐句时间", "",
            "置信度 = 这一句里被 ASR 听出来的字的比例（同音字算对）。来源音轨 = 这一句是在哪条音轨上对上的。",
            "", "| 序号 | 段落 | 谁 | 歌词 | 起 | 止 | 置信度 | 来源音轨 | 标记 | ASR 听到 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for ln in timing.lines:
        sec = timing.sections[ln.verse].name if ln.verse < len(timing.sections) else str(ln.verse)
        flags = "、".join(FLAG_CN.get(f, f) for f in ln.flags)
        out.append(f"| {ln.idx + 1} | {sec} | {name.get(ln.who, ln.who)} | {ln.text} | {_t(ln.t0)} | {_t(ln.t1)} | "
                   f"{ln.conf:.2f} | {SOURCE_CN.get(ln.source, ln.source)} | {flags} | {ln.heard} |")
    n_ok = sum(1 for ln in timing.lines if not ln.flags and ln.conf >= 0.9)
    out += ["", f"共 {len(timing.lines)} 句：{n_ok} 句干净（置信度 ≥ 0.9 且没有标记），"
                f"{sum(1 for ln in timing.lines if ln.flags)} 句有标记。"]

    out += ["", "## 建议先听一下核对", "", "按问题大小排序。用播放器跳到起点，前后各多听一秒。", ""]
    for ln in worst_lines(timing):
        out.append(f"- **{_t(ln.t0)} – {_t(ln.t1)}** 第 {ln.idx + 1} 句「{ln.text}」（{name.get(ln.who, ln.who)}）："
                   f"{_why(ln)}")

    pauses = []
    for i, ln in enumerate(timing.lines):
        src = ep.verses[ln.verse].lines[ln.line] if ln.verse < len(ep.verses) else None
        if src is not None and src.pause_beats and i:
            gap = silence_before(timing.lines[i - 1], ln, envs.get("vocals"))
            pauses.append(f"- 「{ln.text}」前面：歌词表写停 {src.pause_beats:g} 拍（{src.pause_beats * g.beat:.2f} 秒），"
                          f"实测上一句结束到这句开口 {max(0.0, gap):.2f} 秒（{max(0.0, gap) / g.beat:.1f} 拍）")
    if pauses:
        out += ["", "## 停顿实测", ""] + pauses

    if "instrumental" in envs:
        db, fps = envs["instrumental"]
        drops = spans(db < -55.0, fps, 1.0)
        if drops:
            out += ["", "## 伴奏停下来的地方（清唱 / 静音，≥ 1 秒）", ""]
            for a, b in drops:
                inside = [ln for ln in timing.lines if ln.t0 < b and ln.t1 > a]
                what = "、".join(f"「{ln.text}」" for ln in inside[:3]) + ("等" if len(inside) > 3 else "")
                out.append(f"- {_t(a)} – {_t(b)}（{b - a:.1f} 秒）" + (f"：这时在唱 {what}" if what else "：没有人声"))
    lead = envs.get("vocals")
    if lead is not None:
        extra = unsung_vocals(timing, lead)
        if extra:
            out += ["", "## 歌词表以外的人声", "", "主唱轨里有声音、但不属于任何一句歌词的地方（加唱、和声、即兴、重复）：", ""]
            out += [f"- {_t(a)} – {_t(b)}（{b - a:.1f} 秒）" for a, b in extra]

    diff = [ln for ln in timing.lines if {"sung_differently", "possibly_skipped", "low_conf"} & set(ln.flags)]
    if diff:
        out += ["", "## 自动发现的歌词差异", ""]
        for ln in diff:
            out.append(f"- 第 {ln.idx + 1} 句「{ln.text}」：{_why(ln)}")
    if notes.strip():
        out += ["", notes.strip()]
    return "\n".join(out) + "\n"
