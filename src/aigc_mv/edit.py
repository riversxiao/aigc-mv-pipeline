"""Edit list + conform render + grade + packaging.

`build_edl` decides, for every board shot, what plays: the picked take of its unit (placed by its measured
lag), else the unit's first-frame plate animated with the shot's own camera move (so the animatic previews
the camera language before any spend), else a labelled card. `render` is frame-exact on song time:

    frames(shot) = round(t1·fps) − round(t0·fps)

Grade, in two layers (claudia.gallery §57, simplified to ffmpeg filters):
1. per shot: measured exposure + white-balance normalisation and black point (takes vary wildly);
2. one film look on the whole cut: soft tone curve, a little less saturation, highlight bloom, fine grain.
No learned upscaling, no sharpening: those are what make generated skin look waxy.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
from pydantic import BaseModel, Field

from aigc_mv.board import Board, BoardShot
from aigc_mv.episode import Episode
from aigc_mv.overlays import Sheet
from aigc_mv.sync import load_unit_takes, takes_dir
from aigc_mv.timing import Timing
from aigc_mv.tools import ffmpeg_exe, run_ffmpeg

SIZES = {"480p": (854, 480), "720p": (1280, 720), "1080p": (1920, 1080), "2k": (2560, 1440)}

LOOK_FILTER = (
    "curves=all='0/0 0.05/0.035 0.2/0.18 0.5/0.53 0.8/0.84 0.95/0.93 1/0.97',"
    "eq=saturation=0.94,format=gbrp,"
    "split[lk_a][lk_b];[lk_b]curves=all='0/0 0.7/0 1/1',gblur=sigma={bloom_sigma}[lk_h];"
    "[lk_a][lk_h]blend=all_mode=screen:all_opacity=0.12,"
    "noise=alls={grain}:allf=t"
)


class EdlEntry(BaseModel):
    shot: str
    t0: float
    t1: float
    source: str = Field(..., description="take | plate | card")
    file: str | None = None
    src_in: float = 0.0
    move: str = "locked"
    grade: dict = Field(default_factory=dict)
    warn: str = ""


class Edl(BaseModel):
    fps: int
    size: tuple[int, int]
    entries: list[EdlEntry]


def _pick_take(project_dir: Path, unit: str):
    ut = load_unit_takes(project_dir, unit)
    if not ut.takes:
        return None, None
    t = next((x for x in ut.takes if x.take == ut.pick), None) or max(ut.takes, key=lambda x: x.ncc)
    return t, ut


def build_edl(project_dir: Path, ep: Episode, board: Board, size: tuple[int, int]) -> Edl:
    project_dir = Path(project_dir)
    units = {u.id: u for u in board.units}
    entries = []
    for s in board.shots:
        u = units[s.unit]
        take, _ = _pick_take(project_dir, u.id)
        e = EdlEntry(shot=s.id, t0=s.t0, t1=s.t1, source="card", move=s.camera)
        if take is not None:
            lag = take.lag if (u.kind == "sung" and take.copy_) else 0.0
            src_in = round(s.t0 - u.song_t0 + lag, 3)
            e.source, e.file, e.src_in = "take", str((takes_dir(project_dir, u.id) / take.take).relative_to(project_dir)), max(0.0, src_in)
            if s.sung and take.synced:
                a, b = src_in, src_in + s.dur
                if not any(x0 - 0.15 <= a and b <= x1 + 0.15 for x0, x1 in take.synced):
                    e.warn = f"lips not verified in {a:.2f}-{b:.2f}s of {take.take} (synced {take.synced})"
            if src_in + s.dur > take.duration + 0.05:
                e.warn = (e.warn + "; " if e.warn else "") + "take shorter than shot: last frame held"
        else:
            for cand in (f"refs/plate_{u.id}.png", f"refs/plate_{s.id}.png",
                         f"refs/{s.singer}_sheet.png" if s.singer and s.kind == "perform" else "",
                         "refs/venue.png" if s.location == "venue" else f"refs/loc_{s.location}.png"):
                if cand and (project_dir / cand).is_file():
                    e.source, e.file = "plate", cand
                    break
        entries.append(e)
    return Edl(fps=ep.fps, size=size, entries=entries)


# --------------------------------------------------------------------------- grade


def measure_grade(path: Path, t_in: float, dur: float) -> dict:
    """Exposure / white balance / black point from 8 frames of the used range."""
    proc = subprocess.run(
        [ffmpeg_exe(), "-v", "error", "-ss", f"{t_in:.3f}", "-t", f"{max(dur, 0.2):.3f}", "-i", str(path),
         "-vf", f"fps={8 / max(dur, 0.2):.4f},scale=64:36", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True,
    )
    raw = np.frombuffer(proc.stdout, dtype=np.uint8)
    if raw.size < 64 * 36 * 3:
        return {}
    px = raw[: raw.size // 3 * 3].reshape(-1, 3).astype(np.float32) / 255.0
    y = px @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    p1, p50 = float(np.percentile(y, 1)), float(np.percentile(y, 50))
    mean = px.mean(0)
    grey = float(mean.mean())
    target = 0.36
    exp = float(np.clip((target / max(p50, 1e-3)) ** 0.5, 0.8, 1.35))
    wb = [float(np.clip((grey / max(m, 1e-3)) ** 0.4, 0.92, 1.08)) for m in mean]
    black = float(np.clip(p1 - 0.025, 0.0, 0.08)) if p1 > 0.04 else 0.0
    return {"exposure": round(exp, 3), "wb": [round(v, 3) for v in wb], "black": round(black, 3),
            "p50": round(p50, 3), "p1": round(p1, 3)}


def grade_filter(g: dict, warm: float = 0.0) -> str:
    if not g:
        return "null"
    e, (r, gg, b) = g["exposure"], g["wb"]
    f = f"colorchannelmixer=rr={e * r * (1 + warm):.4f}:gg={e * gg:.4f}:bb={e * b * (1 - warm):.4f}"
    if g.get("black", 0) > 0:
        f += f",curves=all='{g['black']:.3f}/0 1/1'"
    return f


# --------------------------------------------------------------------------- still → camera move


def zoompan_expr(move: str, n: int, fps: int) -> tuple[str, str, str]:
    N = max(1, n)
    c_x, c_y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    if move in ("push_slow", "low_push", "rack_focus", "ots_drift"):
        return f"1+0.10*on/{N}", c_x, c_y
    if move == "pull_reveal":
        return f"1.14-0.14*on/{N}", c_x, c_y
    if move in ("truck", "arc_short", "steadicam"):
        return "1.12", f"(iw-iw/zoom)*on/{N}", c_y
    if move in ("crane_up", "tilt_reveal"):
        return "1.12", c_x, f"(ih-ih/zoom)*(1-on/{N})"
    if move == "crane_in":
        return f"1+0.12*on/{N}", c_x, f"(ih/2-(ih/zoom/2))*on/{N}"
    if move == "whip_in":
        k = max(1, int(0.3 * fps))
        return "1.12", f"(iw-iw/zoom)/2*min(1,on/{k})", c_y
    if move == "snap_zoom":
        k = min(N - 1, max(1, int(0.45 * fps)))
        return f"if(gt(on,{N - k}),1.02+0.33*(on-{N - k})/{k},1.02)", c_x, c_y
    if move in ("handheld", "tele_float"):
        return "1.08", "(iw-iw/zoom)/2+6*sin(on/9)", "(ih-ih/zoom)/2+4*sin(on/13)"
    return f"1+0.03*on/{N}", c_x, c_y


def _segment(project_dir: Path, ep: Episode, e: EdlEntry, s: BoardShot, out: Path, size, fps, sheet: Sheet,
             tmp: Path, timing: Timing) -> None:
    W, H = size
    n = round(e.t1 * fps) - round(e.t0 * fps)
    dur = n / fps
    enc = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", "-r", str(fps), "-an"]
    warm = 0.0
    if e.source == "take":
        src = project_dir / e.file
        if not e.grade:
            e.grade = measure_grade(src, e.src_in, dur)
        vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1,fps={fps},"
              f"{grade_filter(e.grade, warm)},tpad=stop_mode=clone:stop_duration={dur:.3f},setpts=N/({fps}*TB)")
        run_ffmpeg(["-ss", f"{e.src_in:.3f}", "-i", str(src), "-vf", vf, "-frames:v", str(n), *enc, str(out)])
        return
    if e.source == "plate":
        img = project_dir / e.file
    else:
        img = tmp / f"card_{s.id}.png"
        text = {ln.idx: ln.text for ln in timing.lines}
        who = "、".join(ep.cast[w].name_cn for w in s.who) or "—"
        sheet.card([f"{s.id}  {s.framing} · {s.lens} · {s.camera}", f"{s.kind} · {who}", s.action_cn[:60],
                    " / ".join(text[i] for i in s.lines)]).save(img)
    z, x, y = zoompan_expr(e.move if e.source == "plate" else "locked", n, fps)
    vf = (f"scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase,crop={W * 2}:{H * 2},"
          f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={fps},setsar=1,setpts=N/({fps}*TB)")
    run_ffmpeg(["-loop", "1", "-i", str(img), "-vf", vf, "-frames:v", str(n), *enc, str(out)])


def render(project_dir: Path, ep: Episode, board: Board, timing: Timing, resolution: str = "720p",
           test: tuple[float, float] | None = None, look: bool = True, overlays: bool = True) -> Path:
    project_dir = Path(project_dir)
    size = SIZES[resolution]
    fps = ep.fps
    edl = build_edl(project_dir, ep, board, size)
    tmp = project_dir / "edit" / "parts"
    tmp.mkdir(parents=True, exist_ok=True)
    sheet = Sheet(*size, style=ep.subtitle_style)
    shots = {s.id: s for s in board.shots}
    parts = []
    for e in edl.entries:
        if test and (e.t1 <= test[0] or e.t0 >= test[1]):
            continue
        out = tmp / f"{e.shot}.mp4"
        _segment(project_dir, ep, e, shots[e.shot], out, size, fps, sheet, tmp, timing)
        parts.append((e, out))
    (project_dir / "edit" / "edl.json").write_text(edl.model_dump_json(indent=2) + "\n", encoding="utf-8")
    lst = tmp / "concat.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for _, p in parts), encoding="utf-8")
    picture = project_dir / "edit" / "picture.mp4"
    run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(picture)])
    t_from = parts[0][0].t0 if parts else 0.0
    t_to = parts[-1][0].t1 if parts else 0.0
    return package(project_dir, ep, board, timing, picture, size, t_from, t_to, look, overlays,
                   suffix="_test" if test else "")


def package(project_dir: Path, ep: Episode, board: Board, timing: Timing, picture: Path, size, t_from: float,
            t_to: float, look: bool, overlays: bool, suffix: str = "") -> Path:
    W, H = size
    fps = ep.fps
    tmp = project_dir / "edit" / "layers"
    tmp.mkdir(parents=True, exist_ok=True)
    sheet = Sheet(W, H, style=ep.subtitle_style)
    layers: list[tuple[str, float, float, float]] = []
    lines = timing.lines
    if overlays:
        left, right = (ep.cast[k] for k in ep.rappers())
        sheet.title(left.name_cn, right.name_cn, ep.disclaimer).save(tmp / "title.png")
        layers.append(("title.png", 0.0, max(0.5, lines[0].t0 - 0.1), 0.3))
        for k, c in ep.cast.items():
            mine = [ln for ln in lines if ln.who == k]
            if mine:
                sheet.name(c.name_cn, c.aka, c.side == "right").save(tmp / f"name_{k}.png")
                end = mine[1].t1 if len(mine) > 1 else mine[0].t1
                layers.append((f"name_{k}.png", mine[0].t0 - 0.08, end - 0.1, 0.25))
        notes = {(ln_v, ln_l): ep.verses[ln_v].lines[ln_l].note for ln_v, ln_l in ((x.verse, x.line) for x in lines)}
        for i, ln in enumerate(lines):
            sheet.lyric(ln.text, notes[(ln.verse, ln.line)], i).save(tmp / f"line_{i:03d}.png")
            last = i + 1 == len(lines) or lines[i + 1].verse != ln.verse
            end = ln.t1 + 0.4 if last else lines[i + 1].t0 - 0.07
            layers.append((f"line_{i:03d}.png", ln.t0 - 0.05, end, 0.0))
        q = ep.end_question.split("|")
        sheet.end(q[0], q[-1]).save(tmp / "end.png")
        layers.append(("end.png", max(0.0, board.duration - 4.0), board.duration, 0.5))
        if ep.watermark:
            sheet.watermark(ep.watermark).save(tmp / "wm.png")
            layers.append(("wm.png", 0.0, board.duration, 0.0))

    look_cfg = {"bloom_sigma": max(6, int(W / 110)), "grain": 7}
    fc = [f"[0:v]{LOOK_FILTER.format(**look_cfg) if look else 'null'},format=yuv420p,setparams=range=tv:color_primaries=bt709:color_trc=bt709:colorspace=bt709[base]"]
    inputs = ["-i", str(picture)]
    song = project_dir / ep.song
    if song.is_file():
        inputs += ["-ss", f"{t_from:.3f}", "-t", f"{t_to - t_from:.3f}", "-i", str(song)]
    else:
        inputs += ["-f", "lavfi", "-t", f"{t_to - t_from:.3f}", "-i", "anullsrc=r=44100:cl=stereo"]
    last, k = "base", 2
    for idx, (png, st, en, fade) in enumerate(layers):
        st, en = max(st, t_from) - t_from, min(en, t_to) - t_from
        if en - st < 0.05:
            continue
        d = en - st
        inputs += ["-loop", "1", "-framerate", str(fps), "-t", f"{d:.3f}", "-i", str(tmp / png)]
        ch = f"[{k}:v]format=rgba"
        if fade:
            ch += f",fade=t=in:st=0:d={fade}:alpha=1,fade=t=out:st={max(0, d - fade):.3f}:d={fade}:alpha=1"
        fc += [ch + f",setpts=PTS-STARTPTS+{st:.3f}/TB[l{idx}]",
               f"[{last}][l{idx}]overlay=0:0:eof_action=pass[o{idx}]"]
        last, k = f"o{idx}", k + 1
    out = project_dir / "final" / f"{ep.title}{suffix}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg([*inputs, "-filter_complex", ";".join(fc), "-map", f"[{last}]", "-map", "1:a",
                "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(fps),
                "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", str(out)])
    return out
