"""Write every unit's request to disk: prompt, uploads (downscaled PNG), audio window, settings.

`units/<id>/prompt.txt` is copy-paste ready for the 即梦 web app today and is also exactly what the Dreamina
adapter will send (`units/<id>/request.json`), so the approval digest covers what is generated.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from aigc_mv.board import Board
from aigc_mv.cinema import banned_hits
from aigc_mv.edit import SIZES
from aigc_mv.episode import Episode
from aigc_mv.prompts import characters, refs_plan, video_prompt
from aigc_mv.providers.base import VideoRequest
from aigc_mv.timing import Timing

SUNG_PROMPT_WARN = 1800  # characters; long sung prompts make Seedance re-sing instead of copy


def _downscale(src: Path, dst: Path, size: tuple[int, int]) -> None:
    im = Image.open(src).convert("RGB")
    im.thumbnail(size, Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, "PNG")


def write_refs_doc(project_dir: Path, ep: Episode, board: Board, knowledge_dir: Path | None = None) -> Path:
    chars = characters(ep, knowledge_dir)
    plan = refs_plan(ep, board, chars)
    if ep.realism == "idol_show":
        crit = ("每张图生成 4 张挑 1 张，存成下面的文件名放进 `refs/`。挑图标准：好看但像真人上节目：皮肤有真实纹理、不塑料；"
                "脸是原创的，不像任何真人演员（包括真人剧《异人之下》的演员）；表情像真人；同一角色每张图服装道具一致；"
                "场景图正面对称。")
    else:
        crit = ("每张图生成 4 张挑 1 张，存成下面的文件名放进 `refs/`。挑图标准：像真人实拍（毛孔、细纹、不对称），"
                "不像任何真实演员；道具和服装在每张图里一致；场景图正面对称。")
    rows = [f"# 定妆图与场景图 · {ep.title}", "", crit, "",
            "Midjourney 用 EN（`--style raw --stylize 60`，不要加 8k / masterpiece 之类的词）；即梦图片用 CN。", ""]
    for item in plan:
        rows += [f"## `{item['file']}`", f"用途：{item['use']}", "", "EN:", "```", item["en"], "```", "CN:", "```",
                 item["cn"], "```", ""]
    out = Path(project_dir) / "refs" / "REFS.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(rows), encoding="utf-8")
    (Path(project_dir) / "refs" / "refs_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2),
                                                                encoding="utf-8")
    return out


def write_packs(project_dir: Path, ep: Episode, board: Board, timing: Timing,
                knowledge_dir: Path | None = None) -> list[dict]:
    project_dir = Path(project_dir)
    chars = characters(ep, knowledge_dir)
    size = SIZES.get(ep.resolution, SIZES["720p"])
    summary = []
    for u in board.units:
        d = project_dir / "units" / u.id
        d.mkdir(parents=True, exist_ok=True)
        up = video_prompt(ep, board, timing, u, chars)
        images, missing = [], []
        for i, (fname, role) in enumerate(up.uploads, 1):
            src = project_dir / "refs" / fname
            dst = d / f"图片{i}_{Path(fname).stem}.png"
            if src.is_file():
                _downscale(src, dst, size)
                images.append(dst)
            else:
                missing.append(fname)
        first = project_dir / "refs" / f"plate_{u.id}.png"
        first_frame = None
        if u.kind == "motion" and first.is_file():
            first_frame = d / "首帧.png"
            _downscale(first, first_frame, size)
        audio = d / up.audio if up.audio else None
        req = VideoRequest(unit=u.id, prompt=up.text, duration=u.duration, images=[p.relative_to(project_dir) for p in images],
                           audio=audio.relative_to(project_dir) if audio else None,
                           first_frame=first_frame.relative_to(project_dir) if first_frame else None,
                           resolution=ep.resolution, aspect_ratio=ep.aspect)
        header = [
            f"【单元】{u.id} · {'对口型' if u.kind == 'sung' else '无口型'} · 歌曲 {u.song_t0:.2f}s 起 · {len(board.unit_shots(u))} 个镜头",
            "【上传】" + "、".join(f"图片{i}（{Path(f).stem}）" for i, (f, _) in enumerate(up.uploads, 1))
            + (f"、音频1（{up.audio}）" if up.audio else "") + ("、首帧.png（作为首帧）" if first_frame else ""),
            f"【设置】{ep.aspect}，时长 {u.duration} 秒（和音频一样长），{ep.resolution}；先低清测试，满意后用「超清」放大同一条",
            "【下载】生成的视频存进本文件夹的 takes/ 子文件夹（take-1.mp4、take-2.mp4…），然后跑 aigc-mv ep sync",
        ]
        if missing:
            header.append("【缺图】refs/ 里还没有：" + "、".join(missing) + "（见 refs/REFS.md）")
        (d / "prompt.txt").write_text("\n".join(header) + "\n\n【提示词】\n" + up.text + "\n", encoding="utf-8")
        (d / "takes").mkdir(exist_ok=True)
        reqd = {"unit": u.id, "kind": u.kind, "duration": u.duration, "resolution": ep.resolution,
                "aspect_ratio": ep.aspect, "song_t0": u.song_t0, "images": [str(p) for p in req.images],
                "audio": str(req.audio) if req.audio else None,
                "first_frame": str(req.first_frame) if req.first_frame else None,
                "prompt": up.text, "digest": req.digest()}
        (d / "request.json").write_text(json.dumps(reqd, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        warn = []
        if u.kind == "sung" and len(up.text) > SUNG_PROMPT_WARN:
            warn.append(f"sung prompt is {len(up.text)} chars (> {SUNG_PROMPT_WARN}); consider fewer shots per unit")
        hits = banned_hits(up.text)
        if hits:
            warn.append(f"banned words: {hits}")
        if missing:
            warn.append(f"missing refs: {missing}")
        if up.audio and not (d / up.audio).is_file():
            warn.append("audio window not written yet (needs audio/ files)")
        summary.append({"unit": u.id, "kind": u.kind, "duration": u.duration, "chars": len(up.text),
                        "digest": reqd["digest"], "warnings": warn})
    (project_dir / "units" / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                                                        encoding="utf-8")
    return summary
