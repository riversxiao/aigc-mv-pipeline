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
from aigc_mv import plates
from aigc_mv.prompts import MAX_FACE_REFS, MAX_UPLOADS, characters, refs_plan, upload_warnings, video_prompt
from aigc_mv.providers.base import VideoRequest
from aigc_mv.sheets import sheet_gaps
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
        env = [x for x in plan if x.get("plate")]
        rows = _idol_refs_doc(ep, plan, plate_cost(env, Path(project_dir) / "ledger.jsonl") if env else None)
    else:
        rows = _battle_refs_doc(ep, plan)
    out = Path(project_dir) / "refs" / "REFS.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(rows), encoding="utf-8")
    (Path(project_dir) / "refs" / "refs_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2),
                                                                encoding="utf-8")
    return out


STEP_CN = {1: "第一步 原作图 → 真人正面像", 2: "第二步 用正面像生成其他角度", 3: "第三步 锁定并拼成定妆组图"}


def _uploads_cn(item: dict) -> str:
    ups = item.get("uploads") or []
    if not ups:
        return "不上传图（文生图）"
    return "；".join(f"图{i} = `{u.get('path') or 'refs/' + u['file']}`（{u['role']}）" for i, u in enumerate(ups, 1))


def _idol_refs_doc(ep: Episode, plan: list[dict], cost: dict | None = None) -> list[str]:
    people = [x for x in plan if x.get("cast")]
    rest = [x for x in plan if not x.get("cast")]
    rows = [
        f"# 定妆图与场景图 · {ep.title}", "",
        "## 为什么分三步", "",
        "以前一句文生图直接出「四宫格定妆照」：四格里的脸常常不是同一个人，发色和标志物也会跑偏。现在改成三步，每一步都拿上一步锁定的图当参考：",
        "",
        "1. **原作图 → 真人正面像**（`<key>_face.png`）：推荐把官方图直接从本地上传给即梦图片生成（图1）。"
        "也可以在 Midjourney 里当图片提示（链接放最前面，`--iw 1.5`，只借颜色和构图，不借画风），但要先看下面关于链接的说明。"
        "原创角色没有原作图，直接文生图。",
        "2. **用正面像生成其他角度**：四分之三侧面、正侧面、半身、全身，每张单独生成，每张都上传第一步锁定的"
        "`<key>_face.png`（即梦图1；Midjourney V7 用 `--oref <定妆正面像链接> --ow 100`，V6 用 `--cref <定妆正面像链接> --cw 100`）。"
        "表情四宫格（`<key>_expr.png`）是可选的：只用来试表情、挑招牌表情，不拼进组图，视频单元也不用它，赶时间可以跳过。",
        "3. **锁定并拼图**：face/34/profile/half/full 五张都挑好后跑 `aigc-mv ep sheets <本期目录>`，拼成 `<key>_sheet.png`"
        "（左边全身，右边 2x2 四张，接近 3:2，传给视频模型时脸不会被缩得太小）。五张没齐不会拼；想先拼着看加 `--partial`，"
        "这样拼出来的图 `ep prompts` 会继续提示缺图。视频单元每人只传这一张；锁定后不再改，改了就要重新生成所有用到这个人的镜头。",
        "",
        "原作图只放在本地 `refs/canon/`（`aigc-mv ep canon` 放进去），这个文件夹在 .gitignore 里，官方图有版权，不进 git，也不要自己公开发布。",
        "",
        "关于 Midjourney 链接：Midjourney 只认图片链接，在 Midjourney 网页里上传的图会存到它的服务器上，拿到的链接别人也能打开，"
        "等于把图放到了网上；隐身模式（Stealth）只是不进公开图库，链接本身照样能打开。所以第一步的原作图请用即梦本地上传，"
        "`<原作图链接>` 那条 Midjourney 提示词只在你接受这张官方图留在 Midjourney 服务器上时再用。"
        "第二步上传的是自己生成的真人正面像，不是官方图，上传后复制链接替换提示词里的 `<定妆正面像链接>` 即可。",
        "",
        "挑图标准：每张生成 4 张挑 1 张。发色、发型、眼睛颜色和招牌物件要对得上原作；脸是原创的，不像任何真人演员，"
        "尤其不像真人剧《异人之下》的演员，也不照搬任何已有 AI 节目里的脸；皮肤有真实纹理、不塑料；成年人比例；"
        "第二步的五张必须一眼看出是第一步那个人。即梦用 CN，Midjourney 用 EN，EN 末尾的参数已经写好，不要再加画质堆砌词。",
        "",
        "## 上传清单", "",
        "| 人物 | 第一步上传 | 第二步上传 | 第三步 |",
        "| --- | --- | --- | --- |",
    ]
    order: list[str] = []
    for x in people:
        if x["cast"] not in order:
            order.append(x["cast"])
    for k in order:
        items = [x for x in people if x["cast"] == k]
        face = next(x for x in items if x["step"] == 1)
        s1 = ", ".join(f"`{u.get('path') or u.get('file')}`" for u in face["uploads"]) or "无（原创角色，文生图）"
        n2 = sum(1 for x in items if x["step"] == 2 and not x.get("optional"))
        n_opt = sum(1 for x in items if x["step"] == 2 and x.get("optional"))
        opt = f" + {n_opt} 张可选" if n_opt else ""
        rows.append(f"| {ep.cast[k].name_cn}（{k}） | {s1} | `{k}_face.png`（{n2} 张必做{opt}，各传一次） "
                    f"| `ep sheets` 拼 `{k}_sheet.png` |")
    rows.append("")
    for k in order:
        c = ep.cast[k]
        items = [x for x in people if x["cast"] == k]
        face = next(x for x in items if x["step"] == 1)
        rows += [f"## {c.name_cn}（{k}）", ""]
        if face.get("canon_url"):
            rows.append(f"原作图：`{face['uploads'][0]['path']}`（来源：[Bangumi 角色页]({face['canon_url']})）")
            if face.get("canon_look_cn"):
                rows += ["", f"原作里的样子：{face['canon_look_cn']}"]
        else:
            rows.append("原创角色，无原作图：第一步用文生图。")
        rows.append("")
        step = None
        for x in items:
            if x["step"] != step:
                step = x["step"]
                rows += [f"### {STEP_CN[step]}", ""]
            rows += [f"#### `{x['file']}`", f"用途：{x['use']}", ""]
            if x["step"] == 3:
                rows += ["拼图用：" + "、".join(f"`{t}`" for t in x.get("tiles", [])) + "（`aigc-mv ep sheets` 自动拼，不用提示词）", ""]
                continue
            rows += [f"上传：{_uploads_cn(x)}", "", "即梦 CN：", "```", x["cn"], "```", "Midjourney EN：", "```", x["en"], "```"]
            if x.get("mj_note"):
                rows.append(x["mj_note"] + "。")
            rows.append("")
    env = [x for x in rest if x.get("plate")]
    if env:
        rows += plates_doc(ep, env, cost)
    others = [x for x in rest if not x.get("plate")]
    rows += ["## 首帧和其他场景" if env else "## 场景、评委席、观众和首帧", ""]
    for item in others:
        rows += [f"### `{item['file']}`", f"用途：{item['use']}", ""]
        if item.get("uploads"):
            rows += [f"上传：{_uploads_cn(item)}", ""]
        rows += ["Midjourney EN：", "```", item["en"], "```", "即梦 CN：", "```", item["cn"], "```"]
        if item.get("mj_note"):
            rows.append(item["mj_note"] + "。")
        rows.append("")
    return rows


def _ids(xs: list[str], limit: int = 0) -> str:
    if not xs:
        return "无"
    if limit and len(xs) > limit:
        return "、".join(xs[:limit]) + f" 等 {len(xs)} 个"
    return "、".join(xs)


def plate_cost(env: list[dict], ledger: Path | None = None) -> dict:
    per = plates.per_image_from_ledger(ledger) if ledger else plates.PLATE_USD
    seen = plates.ledger_image_usd(ledger) if ledger else []
    return plates.cost_estimate([x["file"] for x in env], per_image=per, seen=seen)


def plates_doc(ep: Episode, env: list[dict], cost: dict | None = None) -> list[str]:
    """REFS.md section 「场景图 / 背景板」: why, what (and what not), density, cameo seats, uploads, cost, prompts."""
    cost = cost or plate_cost(env)
    by = {r["file"]: r for r in cost["rows"]}
    seen = cost.get("seen") or []
    if not seen:
        seen_cn = "账本里还没有真实的出图价格，按默认价估算；"
    elif len(seen) == 1 or f"{seen[0]:.3f}" == f"{seen[-1]:.3f}":
        seen_cn = f"账本里已经做过的 3:4 高质量图（带一张参考图）实际每张 ${seen[-1]:.3f}；"
    else:
        seen_cn = f"账本里已经做过的 3:4 高质量图（带一张参考图）实际每张 ${seen[0]:.3f} 到 ${seen[-1]:.3f}；"
    first = env[0]["file"]
    cameos = ep.members("cameo")
    rows = [
        "## 场景图 / 背景板", "",
        f"观众席要坐满人，所以场景图要做。即梦按上传的图来认场馆：只传一张空场馆，生成出来的看台常常是空的或者稀稀拉拉，"
        f"每个镜头的场馆样子也会不一样。所以给场馆的每个机位各做一张锁定的背景板，一共 {len(env)} 张；每个镜头按它的调度"
        "自动配一张（分镜表的「场景图」列），视频单元上传它。这些图是原创的场景照片，不来自任何官方图，可以放心上传。", "",
        "### 做哪些、不做哪些", "",
        "| 场景图 | 用途 | 观众 | 用在镜头 | 用在单元（实际上传） |",
        "| --- | --- | --- | --- | --- |",
    ]
    crowd_cn = {"full": "坐满，看得清脸", "bokeh": "坐满，虚成光斑", "dark": "灭灯，只有剪影"}
    for x in env:
        rows.append(f"| `{x['file']}` | {x['use']} | {crowd_cn[x['crowd']]} | {_ids(x['shots'], 8)} | {_ids(x['units'])} |")
    rows += [
        "",
        "不单独做的：地面八卦图案和 LED 大屏的特写图（分镜里没有这两种插入镜头，它们已经在舞台正面、高位全景和 DJ 台三张里）；"
        "每位评委、每位客串各一张座位图（一张评委席、一张前两排座位就够，人物靠定妆图放进去）；"
        "白天、彩排、后台这类场景（这一期全在晚上的直播现场）。", "",
        "### 怎么做", "",
        f"1. 先做 `{first}`（文生图），每张出 2 到 4 张候选，挑一张锁定。锁定以后不再改，改了就要重新生成所有用到它的镜头。",
        "2. 其他场景图都上传一张已经锁定的场景图当图1（每张下面的「上传」写了是哪张），这样灯光、配色、地面图案和看台样式能对上。"
        "Midjourney 里把那张锁定图当 `--sref <场景图链接>`；这是自己生成的图，不是官方图，传上去没问题。",
        "3. 挑图标准：看台是满的，没有空座位；观众是长相各不相同的普通成年人，不是动漫脸、不像任何真实名人；"
        "画面里没有任何文字和标志（节目 logo 是剪辑时叠上去的角标）；和上一张锁定图放在一起像同一个场馆。", "",
        "### 观众密度：图里坐满，提示词里再说一遍", "",
        f"两层都做：场景图本身就是满场（「{ep.crowd_cn.strip('。')}，{plates.DENSE_CN}」），视频模型照着图生成时看台不会空；"
        "每个单元的提示词里还有一行【观众】，点名哪几个镜头能看到观众席，再写一次坐满、不要空座位、不要空看台。"
        "灭灯那几个镜头例外：观众席是黑的，只有剪影和零星的荧光棒，提示词也写明不要把观众照亮。", "",
    ]
    if cameos:
        seats = "；".join(f"{ep.cast[k].name_cn}坐在{s}" for k, s in plates.cameo_seats(ep).items())
        rows += [
            "### 客串角色坐哪儿", "",
            f"客串角色不画进任何场景图。`cameo_seats.png` 把他们的座位留空：{seats}。客串的反应镜头上传这个人的定妆组图和 "
            "`cameo_seats.png`，提示词写明坐在哪个座位（就是图里留空的那个），左右和身后是不认识的普通观众。"
            "同一个人的所有镜头用同一张图、同一句座位描述，所以位置不会跳。观众全景里不要求看到客串角色。", "",
        ]
    rows += [
        "### 视频单元怎么上传", "",
        f"每个单元最多上传 {MAX_UPLOADS} 张图（即梦 Seedance 2.0 全能参考的图片上限）：先放人物，每人只传一张定妆组图"
        f"（最多 {MAX_FACE_REFS} 人），再放场景图，最多 {plates.MAX_UNIT_PLATES} 张。一个单元里调度多于两种场景时，"
        "灭灯和客串座位这两张一定保留，其次保留画面里有那个人的专属场景图（评委反应配评委席、主持和 DJ 配 DJ 台、"
        "副歌歌手配立麦），其余按镜头时长选；超过上限时先去掉背景里虚化的队友，再去掉多出来的场景图。"
        "提示词的每个镜头都写了「背景照 @图片N」。", "",
        "### 费用估算（没有生成任何图）", "",
        f"按 OpenRouter `openai/gpt-image-2.5-sunburst`、quality high、16:9 估算。{seen_cn}"
        f"16:9 是 1536x1024，和 3:4 的 1024x1536 像素一样多，所以按每张 ${cost['per_image']:.2f} 算，"
        f"保守上限按每张 ${cost['upper']:.2f}（{plates.UPPER_FACTOR} 倍，留给更长的提示词、多一张参考图或者调价）。"
        f"每张场景图做 {cost['rows'][0]['candidates'] if cost['rows'] else plates.CANDIDATES} 张候选。", "",
        "| 场景图 | 候选张数 | 估算 USD | 保守上限 USD |",
        "| --- | --- | --- | --- |",
    ]
    for x in env:
        r = by[x["file"]]
        rows.append(f"| `{x['file']}` | {r['candidates']} | ${r['usd']:.2f} | ${r['usd_upper']:.2f} |")
    rows += [f"| 合计 | {cost['images']} | ${cost['total']:.2f} | ${cost['total_upper']:.2f} |", "",
             "付费生成要先确认预算再跑；这里只是估算，没有调用任何接口。", ""]
    for x in env:
        rows += [f"### `{x['file']}`", f"用途：{x['use']}", "", f"机位：{x['camera']}", "",
                 f"用在镜头：{_ids(x['shots'])}", "", f"用在单元：{_ids(x['units'])}", "",
                 f"上传：{_uploads_cn(x)}", "", "即梦 CN：", "```", x["cn"], "```", "Midjourney EN：", "```", x["en"], "```",
                 "GPT Image（OpenRouter，参数已去掉）：", "```", x["gpt"], "```", ""]
    return rows


def _battle_refs_doc(ep: Episode, plan: list[dict]) -> list[str]:
    crit = ("每张图生成 4 张挑 1 张，存成下面的文件名放进 `refs/`。挑图标准：像真人实拍（毛孔、细纹、不对称），"
            "不像任何真实演员；道具和服装在每张图里一致；场景图正面对称。")
    rows = [f"# 定妆图与场景图 · {ep.title}", "", crit, "",
            "Midjourney 用 EN（`--style raw --stylize 60`，不要加 8k / masterpiece 之类的词）；即梦图片用 CN。", ""]
    for item in plan:
        rows += [f"## `{item['file']}`", f"用途：{item['use']}", "", "EN:", "```", item["en"], "```", "CN:", "```",
                 item["cn"], "```", ""]
    return rows


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
        images, missing, missing_env = [], [], []
        up_warn = upload_warnings(ep, board, u)
        for i, (fname, role) in enumerate(up.uploads, 1):
            src = project_dir / "refs" / fname
            dst = d / f"图片{i}_{Path(fname).stem}.png"
            if src.is_file():
                _downscale(src, dst, size)
                images.append(dst)
                gaps = sheet_gaps(src) if fname.endswith("_sheet.png") else []
                if gaps:  # made by `ep sheets --partial`: not locked yet
                    missing.append(f"{fname}（不完整，还缺 " + "、".join(gaps) + "）")
            elif ep.format == "show" and fname in plates.BY_FILE:
                missing_env.append(fname)
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
        if missing_env:
            header.append("【缺图】场景图还没有：" + "、".join(missing_env) + "（见 refs/REFS.md「场景图 / 背景板」）")
        if len(up.uploads) > MAX_UPLOADS:  # unit_refs trims show units; battle units are checked here
            up_warn.append(f"{len(up.uploads)} uploads > {MAX_UPLOADS}")
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
        if missing or missing_env:
            warn.append(f"missing refs: {missing + missing_env}")
        warn += up_warn
        if up.audio and not (d / up.audio).is_file():
            warn.append("audio window not written yet (needs audio/ files)")
        summary.append({"unit": u.id, "kind": u.kind, "duration": u.duration, "chars": len(up.text),
                        "digest": reqd["digest"], "warnings": warn})
    (project_dir / "units" / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                                                        encoding="utf-8")
    return summary
