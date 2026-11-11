"""`rea-video` reference benchmarking & post-render closed-loop audit.

Bridges JuneYaooo/rea-video (`rea-video decompose` / `breakdown.json`) with our AIGC MV orchestration
pipeline so rendered episodes are quantitatively audited against reference benchmarks such as
《火影有嘻哈 EP03》 (`HUOYING_BENCHMARK`) and flagged shots receive targeted H3 repair recipes:

- `ref2va_pose`: Ref2VA (character sheet + stage plate) + ControlNet DWPose (21 body/hand joints, no face
  points) + H3LockGuideAudio (`control_strength=0.72, end_percent=0.84`) -> cures talking-portrait body
  freeze and repeated Frame-0 hand poses on sung rap shots.
- `ref2va_depth`: Ref2VA + ControlNet Depth (`control_strength=0.68, end_percent=0.82`) -> cures flat
  planar Ken Burns (`still_motion`) on martial-arts, qi, crowd, and instrument cutaways without depth bleed.
- `fl2va_morph`: Dual-keyframe (`_a.png` -> `_b.png`) H3 I2V -> reserved exclusively for explicit state or
  cross-age transformations where start and end poses are verified distinct.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel, Field

from aigc_mv.tools import ffmpeg_exe


class BenchmarkProfile(BaseModel):
    """Quantitative quality gates distilled from reference MV dissection (`rea-video`)."""

    name: str = "huoying_ep03"
    title_cn: str = "《火影有嘻哈 EP03》写实说唱擂台基准"
    max_still_motion_ratio: float = Field(0.03, description="Max duration share of still_motion + static_hold")
    max_avatar_ratio: float = Field(0.02, description="Max duration share of rigid talking-head avatar shots")
    min_moving_camera_ratio: float = Field(0.90, description="Min share of moving + handheld camera support")
    max_jump_cuts: int = Field(1, description="Max same-framing/same-bg hard jump cuts")
    min_avg_shot_s: float = Field(1.8, description="Lower bound on mean shot length (avoid erratic micro-chopping)")
    max_avg_shot_s: float = Field(3.8, description="Upper bound on mean shot length (avoid sluggish talking heads)")
    min_shot_sizes: int = Field(3, description="At least N distinct shot sizes with >= 5% share each")
    min_median_flow_px: float = Field(
        0.12, description="Optical-flow/frame-diff motion floor (px @ 160x90) to catch frozen bodies"
    )


HUOYING_BENCHMARK = BenchmarkProfile()


class RedoCandidate(BaseModel):
    shot_id: str
    index: int
    start: float
    end: float
    duration: float
    label: str
    camera_motion: str = ""
    median_flow_px: float | None = None
    reasons: list[str] = Field(default_factory=list)
    recommended_mode: str = Field(..., description="ref2va_pose | ref2va_depth | fl2va_morph | trim_or_cutaway")
    control_type: str = Field("", description="pose | depth | dual_keyframe | editorial")
    control_strength: float = 0.0
    end_percent: float = 0.0
    recipe_cn: str = ""


class ReaAuditMetrics(BaseModel):
    duration: float
    shots: int
    avg_shot_s: float
    cuts_per_min: float
    still_motion_ratio: float
    avatar_ratio: float
    moving_camera_ratio: float
    fixed_camera_ratio: float
    jump_cuts: int
    distinct_shot_sizes: int
    shot_sizes: dict[str, float] = Field(default_factory=dict)
    production_mix: dict[str, float] = Field(default_factory=dict)
    mean_flow_px: float | None = None


class ReaAuditReport(BaseModel):
    source: str
    benchmark: str
    passed: bool
    metrics: ReaAuditMetrics
    gaps: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    redo_candidates: list[RedoCandidate] = Field(default_factory=list)


def rea_exe() -> str | None:
    """Locate `rea-video` next to the active Python interpreter or on PATH."""
    sibling = Path(sys.executable).resolve().parent / "rea-video"
    if sibling.is_file():
        return str(sibling)
    return shutil.which("rea-video")


def run_rea_decompose(video_path: Path, out_dir: Path, every: float = 0.5, lang: str = "zh") -> Path:
    """Run `rea-video decompose` on `video_path` and return `<out_dir>/breakdown.json`."""
    exe = rea_exe()
    if not exe:
        raise RuntimeError("rea-video CLI not found; install https://github.com/JuneYaooo/rea-video into the venv")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [exe, "decompose", str(video_path), "-o", str(out_dir), "--every", str(every), "--lang", lang]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"rea-video decompose failed ({proc.returncode}): {proc.stderr[-600:]}")
    bd = out_dir / "breakdown.json"
    if not bd.is_file():
        raise FileNotFoundError(f"rea-video finished without writing {bd}")
    return bd


def load_rea_breakdown(path_or_dir: Path) -> dict[str, Any]:
    """Load a `rea-video` breakdown from either `<dir>` or `<dir>/breakdown.json`."""
    p = Path(path_or_dir)
    if p.is_dir():
        p = p / "breakdown.json"
    if not p.is_file():
        raise FileNotFoundError(f"no rea-video breakdown.json at {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def measure_shot_motion_luma(video_path: Path, shots: list[dict[str, Any]], width: int = 160,
                             height: int = 90, fps: int = 12) -> dict[str, float]:
    """Fast deterministic motion proxy (displacement in px at 160x90 via gradient-normalized frame diff).

    Catches H3 `talking-portrait body freeze` where only 2% of mouth pixels move while the torso, hands,
    and background remain frozen (`flow_px < 0.12`).
    """
    out: dict[str, float] = {}
    for s in shots:
        sid = str(s.get("id", f"shot_{s.get('index', 0):03d}"))
        t0 = float(s.get("start", 0.0))
        dur = max(0.25, float(s.get("duration", float(s.get("end", t0 + 1.0)) - t0)))
        proc = subprocess.run(
            [
                ffmpeg_exe(), "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", str(video_path),
                "-vf", f"fps={fps},scale={width}:{height},format=gray", "-f", "rawvideo", "-pix_fmt", "gray", "-",
            ],
            capture_output=True,
        )
        frame_bytes = width * height
        n_frames = len(proc.stdout) // frame_bytes
        if n_frames < 2:
            continue
        frames = np.frombuffer(proc.stdout[: n_frames * frame_bytes], dtype=np.uint8).reshape(
            n_frames, height, width
        ).astype(np.float32)
        # Lucas-Kanade 1D magnitude proxy: |I_t| / (|I_x| + |I_y| + eps) median across interior pixels
        it = np.abs(np.diff(frames, axis=0))
        gx = np.abs(np.diff(frames[:-1], axis=2, append=frames[:-1, :, -1:]))
        gy = np.abs(np.diff(frames[:-1], axis=1, append=frames[:-1, -1:, :]))
        disp = it / (0.5 * (gx + gy) + 6.0)
        per_step = np.median(disp[:, 6:-6, 10:-10], axis=(1, 2))
        out[sid] = round(float(np.median(per_step)), 4)
    return out


def _shot_label(shot: dict[str, Any]) -> str:
    base = shot.get("base") or {}
    if isinstance(base, dict) and base.get("label"):
        return str(base["label"])
    if shot.get("label"):
        return str(shot["label"])
    det = shot.get("deterministic") or {}
    return str(det.get("label", "unknown"))


def _shot_camera_motion(shot: dict[str, Any]) -> str:
    asp = (shot.get("aspects") or {}).get("camera") or {}
    meas = asp.get("measured") or {}
    if meas.get("motion"):
        return str(meas["motion"])
    res = asp.get("result") or {}
    return str(res.get("support") or "")


def _has_vocal_activity(shot: dict[str, Any], breakdown: dict[str, Any]) -> bool:
    sid = str(shot.get("id", ""))
    pca = breakdown.get("per_clip_audio")
    if isinstance(pca, dict):
        clip = pca.get(sid)
        if isinstance(clip, dict):
            return bool(clip.get("has_speech") or clip.get("speech") or float(clip.get("vocal_ratio", 0.0)) > 0.25)
    elif isinstance(pca, list):
        start, end = float(shot.get("start", 0.0)), float(shot.get("end", 0.0))
        for clip in pca:
            if not isinstance(clip, dict):
                continue
            cs, ce = float(clip.get("start", -1.0)), float(clip.get("end", -1.0))
            if abs(cs - start) < 0.15 and abs(ce - end) < 0.15:
                return bool(clip.get("has_speech") or float(clip.get("vocal_ratio", 0.0)) > 0.25)
    faces = shot.get("faces")
    if isinstance(faces, (int, float)):
        return float(faces) >= 0.5
    if isinstance(faces, dict):
        return float(faces.get("present_ratio", 0.0)) >= 0.5
    return False


def recommend_h3_repair(shot: dict[str, Any], breakdown: dict[str, Any], reasons: list[str],
                        flow_px: float | None = None) -> RedoCandidate:
    """Map a flagged shot to the verified H3 dual-track repair recipe."""
    sid = str(shot.get("id", f"shot_{shot.get('index', 0):03d}"))
    idx = int(shot.get("index", 0))
    start = float(shot.get("start", 0.0))
    end = float(shot.get("end", start))
    dur = float(shot.get("duration", max(0.0, end - start)))
    label = _shot_label(shot)
    cam = _shot_camera_motion(shot)
    vocal = _has_vocal_activity(shot, breakdown)

    if any("jump" in r for r in reasons) and label not in ("still_motion", "static_hold", "avatar") and (
        flow_px is None or flow_px >= 0.12
    ):
        return RedoCandidate(
            shot_id=sid, index=idx, start=start, end=end, duration=dur, label=label,
            camera_motion=cam, median_flow_px=flow_px, reasons=reasons,
            recommended_mode="trim_or_cutaway", control_type="editorial",
            control_strength=0.0, end_percent=0.0,
            recipe_cn="同机位硬跳切：插入 1.2–2.0s 听者闭口两拍微反应（OTS/评委/观众图生图）或切换相差两档景别。",
        )
    if vocal or label == "avatar":
        return RedoCandidate(
            shot_id=sid, index=idx, start=start, end=end, duration=dur, label=label,
            camera_motion=cam, median_flow_px=flow_px, reasons=reasons,
            recommended_mode="ref2va_pose", control_type="pose",
            control_strength=0.72, end_percent=0.84,
            recipe_cn="改用 Ref2VA（角色定妆组图 + 舞台空镜）+ ControlNet Union 2.0 Pose（21 关键点去面部点，strength=0.72, end_percent=0.84）+ H3LockGuideAudio + 六层生物力学多拍手势。",
        )
    return RedoCandidate(
        shot_id=sid, index=idx, start=start, end=end, duration=dur, label=label,
        camera_motion=cam, median_flow_px=flow_px, reasons=reasons,
        recommended_mode="ref2va_depth", control_type="depth",
        control_strength=0.68, end_percent=0.82,
        recipe_cn="改用 Ref2VA + ControlNet Union 2.0 Depth（前后景三层深度视差，strength=0.68, end_percent=0.82，防深度灰雾残留）；若为变身转场则改用首尾姿态显著不同的 fl2va 双关键帧。",
    )


def extract_metrics(breakdown: dict[str, Any], motion_by_shot: dict[str, float] | None = None) -> ReaAuditMetrics:
    summary = breakdown.get("summary") or {}
    shots = breakdown.get("shots") or []
    dur = float(summary.get("duration") or breakdown.get("duration") or sum(float(s.get("duration", 0)) for s in shots))
    n_shots = int(summary.get("shots") or len(shots))
    avg_s = round(dur / max(1, n_shots), 3)
    cuts_per_min = round(max(0, n_shots - 1) / max(dur / 60.0, 1e-6), 2)

    mix: dict[str, float] = {}
    for item in summary.get("production_mix") or []:
        mix[str(item.get("label", ""))] = float(item.get("ratio", 0.0))
    if not mix and shots and dur > 0:
        acc: dict[str, float] = {}
        for s in shots:
            lb = _shot_label(s)
            acc[lb] = acc.get(lb, 0.0) + float(s.get("duration", 0.0))
        mix = {k: round(v / dur, 4) for k, v in acc.items()}

    still_ratio = round(mix.get("still_motion", 0.0) + mix.get("static_hold", 0.0), 4)
    avatar_ratio = round(mix.get("avatar", 0.0), 4)

    top_asp = breakdown.get("aspects") if isinstance(breakdown.get("aspects"), dict) else {}
    cam_shares = ((top_asp.get("camera") or {}).get("support_shares")) or {}
    if cam_shares:
        moving_ratio = round(float(cam_shares.get("moving", 0.0)) + float(cam_shares.get("handheld", 0.0)), 4)
        fixed_ratio = round(float(cam_shares.get("fixed", 0.0)), 4)
    elif shots and dur > 0:
        mv_dur = 0.0
        fx_dur = 0.0
        for s in shots:
            sd = float(s.get("duration", 0.0))
            cm = _shot_camera_motion(s)
            if cm in ("moving", "handheld", "smooth_move", "handheld_like", "planar_zoom_pan"):
                mv_dur += sd
            elif cm in ("fixed", "static", "static_with_subject_motion"):
                fx_dur += sd
        tot = mv_dur + fx_dur
        moving_ratio = round(mv_dur / tot, 4) if tot > 0 else 0.0
        fixed_ratio = round(fx_dur / tot, 4) if tot > 0 else 0.0
    else:
        moving_ratio, fixed_ratio = 0.0, 0.0

    shot_sizes_raw = ((top_asp.get("framing") or {}).get("shot_sizes")) or {}
    shot_sizes = {str(k): round(float(v), 4) for k, v in shot_sizes_raw.items()}
    distinct_sizes = sum(1 for v in shot_sizes.values() if v >= 0.05)
    if not shot_sizes and shots:
        counts: dict[str, float] = {}
        for s in shots:
            sz = (((s.get("aspects") or {}).get("framing") or {}).get("result") or {}).get("shot_size")
            if sz:
                counts[str(sz)] = counts.get(str(sz), 0.0) + float(s.get("duration", 1.0))
        tot_sz = sum(counts.values()) or 1.0
        shot_sizes = {k: round(v / tot_sz, 4) for k, v in counts.items()}
        distinct_sizes = sum(1 for v in shot_sizes.values() if v >= 0.05)

    trans = summary.get("transitions") or {}
    jump_cuts = int(trans.get("jump", 0))
    mean_flow = round(float(np.mean(list(motion_by_shot.values()))), 4) if motion_by_shot else None

    return ReaAuditMetrics(
        duration=round(dur, 3),
        shots=n_shots,
        avg_shot_s=avg_s,
        cuts_per_min=cuts_per_min,
        still_motion_ratio=still_ratio,
        avatar_ratio=avatar_ratio,
        moving_camera_ratio=moving_ratio,
        fixed_camera_ratio=fixed_ratio,
        jump_cuts=jump_cuts,
        distinct_shot_sizes=distinct_sizes,
        shot_sizes=shot_sizes,
        production_mix=mix,
        mean_flow_px=mean_flow,
    )


def audit_breakdown(
    breakdown: dict[str, Any],
    benchmark: BenchmarkProfile = HUOYING_BENCHMARK,
    motion_by_shot: dict[str, float] | None = None,
) -> ReaAuditReport:
    """Compare a `rea-video` breakdown against `benchmark` and emit shot-level H3 repair recipes."""
    metrics = extract_metrics(breakdown, motion_by_shot)
    gaps: list[str] = []
    strengths: list[str] = []

    if metrics.still_motion_ratio > benchmark.max_still_motion_ratio:
        gaps.append(
            f"静图推拉/定格占比过高：{metrics.still_motion_ratio:.1%} > 基准上限 {benchmark.max_still_motion_ratio:.1%}"
        )
    else:
        strengths.append(
            f"静图推拉占比达标：{metrics.still_motion_ratio:.1%} <= {benchmark.max_still_motion_ratio:.1%}"
        )

    if metrics.avatar_ratio > benchmark.max_avatar_ratio:
        gaps.append(f"站桩数字人口播占比过高：{metrics.avatar_ratio:.1%} > 基准上限 {benchmark.max_avatar_ratio:.1%}")

    if metrics.moving_camera_ratio < benchmark.min_moving_camera_ratio:
        gaps.append(
            f"移动+手持机位占比偏低：{metrics.moving_camera_ratio:.1%} < 基准下限 {benchmark.min_moving_camera_ratio:.1%}"
        )
    else:
        strengths.append(
            f"动态运镜（移动+手持）达标：{metrics.moving_camera_ratio:.1%} >= {benchmark.min_moving_camera_ratio:.1%}"
        )

    if metrics.jump_cuts > benchmark.max_jump_cuts:
        gaps.append(f"同机位跳切过多：{metrics.jump_cuts} 处 > 基准上限 {benchmark.max_jump_cuts} 处")
    else:
        strengths.append(f"剪辑连续性达标：跳切仅 {metrics.jump_cuts} 处（<= {benchmark.max_jump_cuts}）")

    if not (benchmark.min_avg_shot_s <= metrics.avg_shot_s <= benchmark.max_avg_shot_s):
        gaps.append(
            f"平均镜长偏离甜区：{metrics.avg_shot_s:.2f}s 不在 [{benchmark.min_avg_shot_s:.1f}s, {benchmark.max_avg_shot_s:.1f}s]"
        )
    else:
        strengths.append(f"平均镜长处于说唱对决甜区：{metrics.avg_shot_s:.2f}s（{metrics.cuts_per_min:.1f} 刀/分钟）")

    if metrics.shot_sizes and metrics.distinct_shot_sizes < benchmark.min_shot_sizes:
        gaps.append(
            f"景别变化单一：占比 >=5% 的景别仅 {metrics.distinct_shot_sizes} 类 < 基准 {benchmark.min_shot_sizes} 类 ({metrics.shot_sizes})"
        )
    elif metrics.shot_sizes:
        strengths.append(f"多景别覆盖均衡：{metrics.distinct_shot_sizes} 类主力景别 {metrics.shot_sizes}")

    redo: list[RedoCandidate] = []
    shots = breakdown.get("shots") or []
    total_shots = len(shots)
    for s in shots:
        sid = str(s.get("id", f"shot_{s.get('index', 0):03d}"))
        idx = int(s.get("index", 0))
        dur = float(s.get("duration", 0.0))
        lb = _shot_label(s)
        cam = _shot_camera_motion(s)
        flow = motion_by_shot.get(sid) if motion_by_shot else None
        is_endcard = idx == total_shots and dur <= 3.5 and lb in ("code_render", "cg_3d", "still_motion", "static_hold")
        if is_endcard:
            continue
        reasons: list[str] = []
        if lb in ("still_motion", "static_hold"):
            reasons.append(f"rea-video 判定为 {lb}（纯刚体推拉或静帧）")
        if lb == "avatar":
            reasons.append("rea-video 判定为 avatar（嘴动身不动口播态）")
        if flow is not None and flow < benchmark.min_median_flow_px and dur >= 1.2:
            reasons.append(f"全画幅运动位移 {flow:.3f}px < 下限 {benchmark.min_median_flow_px:.2f}px（疑似锁首帧静帧感）")
        if s.get("transition_in") == "jump" and metrics.jump_cuts > benchmark.max_jump_cuts:
            reasons.append("与上一镜同机位跳切（transition_in=jump）")
        if cam in ("static", "fixed") and dur > 4.2 and lb != "live_action":
            reasons.append(f"固定机位持续过长（{dur:.2f}s > 4.2s）")
        if reasons:
            redo.append(recommend_h3_repair(s, breakdown, reasons, flow))

    if motion_by_shot:
        frozen_n = sum(1 for c in redo if c.median_flow_px is not None and c.median_flow_px < benchmark.min_median_flow_px)
        if frozen_n:
            gaps.append(f"检测到 {frozen_n} 个低动态疑似静帧镜头（位移 < {benchmark.min_median_flow_px:.2f}px）")
        else:
            strengths.append(f"光流动态复核通过：全部正文镜头位移 >= {benchmark.min_median_flow_px:.2f}px")

    src = str((breakdown.get("source") or {}).get("path") or breakdown.get("video") or "breakdown.json")
    return ReaAuditReport(
        source=src,
        benchmark=benchmark.name,
        passed=len(gaps) == 0,
        metrics=metrics,
        gaps=gaps,
        strengths=strengths,
        redo_candidates=redo,
    )


def render_rea_audit_md(report: ReaAuditReport, ref_metrics: ReaAuditMetrics | None = None) -> str:
    """Render a concise Chinese Markdown report comparing `report` against `HUOYING_BENCHMARK` (and optional ref)."""
    m = report.metrics
    status = "PASS（达到《火影有嘻哈》动态基准）" if report.passed else "NEEDS_REDO（存在静态帧/跳切/景别短板）"
    lines = [
        f"# `rea-video` 闭环质检报告 · {status}",
        "",
        f"- **被测成片**：`{report.source}`",
        f"- **对标基准**：`{report.benchmark}`",
        "",
        "## 1. 核心指标对标",
        "",
        "| 指标 | 当前成片 | 对标阈值（火影有嘻哈基准） |" + (" 参考片实测 |" if ref_metrics else ""),
        "| --- | --- | --- |" + (" --- |" if ref_metrics else ""),
        f"| 总时长 / 镜头数 | {m.duration:.1f}s / {m.shots} 镜 | - |"
        + (f" {ref_metrics.duration:.1f}s / {ref_metrics.shots} 镜 |" if ref_metrics else ""),
        f"| 平均镜长 / 剪切率 | {m.avg_shot_s:.2f}s（{m.cuts_per_min:.1f} 刀/分） | 1.8–3.8s |"
        + (f" {ref_metrics.avg_shot_s:.2f}s（{ref_metrics.cuts_per_min:.1f} 刀/分） |" if ref_metrics else ""),
        f"| `still_motion` 静图推拉占比 | {m.still_motion_ratio:.1%} | <= 3.0% |"
        + (f" {ref_metrics.still_motion_ratio:.1%} |" if ref_metrics else ""),
        f"| 移动 + 手持机位占比 | {m.moving_camera_ratio:.1%} | >= 90.0% |"
        + (f" {ref_metrics.moving_camera_ratio:.1%} |" if ref_metrics else ""),
        f"| 同机位硬跳切 (`jump`) | {m.jump_cuts} 处 | <= 1 处 |"
        + (f" {ref_metrics.jump_cuts} 处 |" if ref_metrics else ""),
        f"| 主力景别种类（>=5%） | {m.distinct_shot_sizes} 类 | >= 3 类 |"
        + (f" {ref_metrics.distinct_shot_sizes} 类 |" if ref_metrics else ""),
    ]
    if m.mean_flow_px is not None:
        lines.append(
            f"| 镜头中位位移均值 (`160x90`) | {m.mean_flow_px:.3f} px | >= 0.120 px |"
            + (f" {ref_metrics.mean_flow_px:.3f} px |" if (ref_metrics and ref_metrics.mean_flow_px) else (" - |" if ref_metrics else ""))
        )
    lines += ["", "## 2. 达标项与短板诊断", ""]
    for s in report.strengths:
        lines.append(f"- [x] {s}")
    for g in report.gaps:
        lines.append(f"- [ ] **短板**：{g}")
    lines += ["", f"## 3. 靶向返修清单（共 {len(report.redo_candidates)} 镜）", ""]
    if not report.redo_candidates:
        lines.append("无需返修，可直接进入母带封装与交付。")
    else:
        lines += [
            "| 镜头 | 时间段 | 当前分类 | 位移(px) | 问题原因 | 推荐 H3 修复路由 | 具体处方 |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for c in report.redo_candidates:
            fl = f"{c.median_flow_px:.3f}" if c.median_flow_px is not None else "-"
            why = "；".join(c.reasons)
            ctl = f"`{c.recommended_mode}`" + (
                f" ({c.control_type} {c.control_strength:.2f}@{c.end_percent:.2f})" if c.control_strength else ""
            )
            lines.append(f"| `{c.shot_id}` | {c.start:.2f}–{c.end:.2f}s | `{c.label}` | {fl} | {why} | {ctl} | {c.recipe_cn} |")
    return "\n".join(lines) + "\n"
