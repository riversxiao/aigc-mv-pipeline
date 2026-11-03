"""Build the self-contained Dreamina video bundle for the user's own logged-in computer.

    bundle/
      run_dreamina.py          the runner (verbatim copy of aigc_mv/dreamina_runner.py, python3 stdlib only)
      README.md                Chinese instructions
      manifest.json            episode, take, units, file sizes
      images/<name>.png        every referenced sheet / plate once (generated art only, never refs/canon/)
      units/<id>/request.json  paths relative to the bundle root; prompt.txt; the audio window
    after a run on the user's machine (consumed by `ep ingest-takes`):
      takes/<id>/take-N.mp4, results.json, takes.zip, state.json, logs/<id>.log
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import time
import zipfile
from pathlib import Path
from typing import Optional

from aigc_mv import dreamina_runner

MAX_FILE = 100 * 1000 * 1000      # GitHub hard limit per file
ZIP_LIMIT = 95 * 1000 * 1000      # top-level zip only below this


def _sha(p: Path) -> str:
    return dreamina_runner.file_sha256(p)


def _canon_hashes(ep_dir: Path) -> set:
    d = ep_dir / "refs" / "canon"
    return {_sha(p) for p in d.rglob("*") if p.is_file()} if d.is_dir() else set()


def _upload_name(rel: str) -> str:
    """units/u14/图片3_shayan_sheet.png -> shayan_sheet.png"""
    return re.sub(r"^图片\d+_", "", Path(rel).name)


def unit_ids(ep_dir: Path) -> list:
    summ = ep_dir / "units" / "summary.json"
    if summ.is_file():
        return [s["unit"] for s in json.loads(summ.read_text(encoding="utf-8"))]
    return sorted(p.parent.name for p in (ep_dir / "units").glob("*/request.json"))


def build_bundle(ep_dir: Path, out: Path, units: Optional[list] = None, take: int = 1,
                 make_zip: bool = True) -> dict:
    ep_dir, out = Path(ep_dir), Path(out)
    all_units = unit_ids(ep_dir)
    if not all_units:
        raise FileNotFoundError(f"no units in {ep_dir / 'units'}; run: aigc-mv ep prompts {ep_dir}")
    chosen = [u for u in all_units if not units or u in units]
    missing = [u for u in (units or []) if u not in all_units]
    if missing:
        raise ValueError("unknown units: " + ", ".join(missing))
    if out.exists():
        keep = {"state.json", "takes", "logs", "results.json", "takes.zip"}
        if any(p.name in keep for p in out.iterdir()):
            raise FileExistsError(f"{out} holds a previous run (state.json / takes); choose another --out")
        shutil.rmtree(out)
    (out / "images").mkdir(parents=True)
    canon = _canon_hashes(ep_dir)
    refs_top = {p.name for p in (ep_dir / "refs").glob("*.png")}
    images = {}           # sha -> bundle-relative path
    names = {}            # bundle name -> sha
    rows = []
    for u in chosen:
        src = ep_dir / "units" / u
        req = json.loads((src / "request.json").read_text(encoding="utf-8"))
        dst = out / "units" / u
        dst.mkdir(parents=True)
        new_imgs = []
        for rel in req.get("images") or []:
            p = ep_dir / rel
            if "canon" in Path(rel).parts:
                raise ValueError(f"{u}: {rel} is official art (refs/canon), never bundled")
            h = _sha(p)
            if h in canon:
                raise ValueError(f"{u}: {rel} is byte-identical to a refs/canon file, never bundled")
            name = _upload_name(rel)
            if refs_top and name not in refs_top:
                raise ValueError(f"{u}: {rel} is not a generated sheet/plate from refs/")
            if h not in images:
                if name in names and names[name] != h:
                    name = f"{Path(name).stem}_{h[:8]}{Path(name).suffix}"
                shutil.copy2(p, out / "images" / name)
                images[h], names[name] = f"images/{name}", h
            new_imgs.append(images[h])
        audio = None
        if req.get("audio"):
            a = ep_dir / req["audio"]
            shutil.copy2(a, dst / a.name)
            audio = f"units/{u}/{a.name}"
        ff = req.get("first_frame")
        if ff:
            p = ep_dir / ff
            h = _sha(p)
            if h in canon:
                raise ValueError(f"{u}: first frame {ff} is official art")
            if h not in images:
                shutil.copy2(p, out / "images" / p.name)
                images[h] = f"images/{p.name}"
            ff = images[h]
        req.update({"images": new_imgs, "audio": audio, "first_frame": ff,
                    "upload_order": [f"图片{i}（{Path(x).stem}）" for i, x in enumerate(new_imgs, 1)]
                    + ([f"音频1（{Path(audio).name}）"] if audio else [])})
        (dst / "request.json").write_text(json.dumps(req, ensure_ascii=False, indent=1), encoding="utf-8")
        if (src / "prompt.txt").is_file():
            shutil.copy2(src / "prompt.txt", dst / "prompt.txt")
        rows.append({"unit": u, "kind": req.get("kind"), "duration": req.get("duration"),
                     "images": len(new_imgs), "audio": bool(audio), "chars": len(req.get("prompt") or "")})
    shutil.copy2(dreamina_runner.__file__, out / "run_dreamina.py")
    title = _title(ep_dir)
    (out / "README.md").write_text(readme(title, out.name, rows, take), encoding="utf-8")
    files = sorted(p for p in out.rglob("*") if p.is_file())
    manifest = {
        "episode": ep_dir.name, "title": title, "take": take, "units": chosen,
        "canvas_name": f"{title} 视频",
        "built": time.strftime("%Y-%m-%d %H:%M:%S"), "runner_version": dreamina_runner.RUNNER_VERSION,
        "runner_sha256": hashlib.sha256((out / "run_dreamina.py").read_bytes()).hexdigest(),
        "total_seconds": sum(r["duration"] or 0 for r in rows),
        "files": {str(p.relative_to(out)): p.stat().st_size for p in files},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    files = sorted(p for p in out.rglob("*") if p.is_file())
    big = [str(p) for p in files if p.stat().st_size >= MAX_FILE]
    if big:
        raise ValueError("files >= 100 MB: " + ", ".join(big))
    total = sum(p.stat().st_size for p in files)
    zpath = None
    if make_zip and total < ZIP_LIMIT:
        zpath = out.with_name(out.name + ".zip")
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in files:
                zf.write(p, f"{out.name}/{p.relative_to(out)}")
        if zpath.stat().st_size >= ZIP_LIMIT:
            zpath.unlink()
            zpath = None
    return {"out": out, "units": rows, "images": len(images), "files": len(files), "bytes": total, "zip": zpath,
            "seconds": manifest["total_seconds"]}


def _title(ep_dir: Path) -> str:
    try:
        from aigc_mv.episode import load_episode

        ep = load_episode(ep_dir)
        return f"{ep.show_name} {ep.episode_no} {ep.title}".strip() if getattr(ep, "show_name", "") else ep.title
    except Exception:
        return ep_dir.name


def readme(title: str, folder: str, rows: list, take: int) -> str:
    n = len(rows)
    secs = sum(r["duration"] or 0 for r in rows)
    sung = sum(1 for r in rows if r["kind"] == "sung")
    lo, hi = max(1, round(n * 4 / 3 / 60 + 0.4)), max(2, round(n * 10 / 3 / 60 + 0.4))
    retake = take > 1
    table = "\n".join(f"| {r['unit']} | {'唱段' if r['kind'] == 'sung' else '无口型'} | {r['duration']} 秒 | "
                      f"{r['images']} 张 | {'有' if r['audio'] else '无'} |" for r in rows)
    return f"""# {title}：即梦视频生成包{'（重拍 take-%d）' % take if retake else ''}

这个文件夹在你自己已经登录即梦的电脑上运行，一条命令把 {n} 个单元（{sung} 个唱段、{n - sung} 个无口型，合计 {secs} 秒）
各生成 **1 条** 视频（take-{take}），下载好、打包好，你只需要把打包文件发回来。

每个单元只生成 1 条，不再“抽卡”多生成几条挑一条：先看整体效果，哪几段不满意再单独重拍那几段，最省积分。

## 一、准备（只需一次）

1. 打开“终端”（启动台里搜“终端”）。
2. 确认 Python 3 可用：输入 `python3 --version`，显示 3.8 或更高就行（macOS 第一次可能提示安装开发者工具，点“安装”）。
3. 确认即梦命令行已登录：输入 `dreamina-canvas auth status`，看到 `"loggedIn":true` 就行。
   没登录就运行 `dreamina-canvas auth login`，按提示在浏览器里授权。

## 二、一键运行

把这个文件夹解压到“下载”里，然后在终端运行：

```bash
cd ~/Downloads/{folder} && python3 run_dreamina.py
```

（如果是从 GitHub 页面用 Code → Download ZIP 下载的，解压出来的文件夹名不一样，把命令里的 `{folder}` 换成实际文件夹名即可。
也可以在终端里输入 `cd `（cd 加一个空格）后把文件夹拖进终端窗口，再回车。）

脚本会依次：

1. 显示登录状态、会员和可用积分；
2. 实时查询即梦的 Seedance 模型，自动选能同时参考“图片 + 音频”的最好的一个，并按它的规定调整时长、分辨率（720P）、画幅（16:9）；
3. 新建（或复用）一个画布，上传每个单元的定妆图、场景图和音频片段；
4. 每个单元建一个视频节点并 **报价**，先把 **总报价** 打出来；
5. 按每个节点自己的报价确认积分上限，然后提交生成（同时最多 3 个）；
6. 生成完自动下载到 `takes/<单元>/take-{take}.mp4`，最后写 `results.json` 并打包成 `takes.zip`。

大约需要 {lo} 到 {hi} 小时（取决于即梦排队），电脑不要睡眠。中途可以随时 Ctrl+C，之后重跑同一条命令会接着做。

## 三、积分

- 脚本先报价、后花钱：所有单元报完价，会打印总报价；超过上限或超过账号余额，就 **一分不花直接停止**。
- 默认上限是“总报价 + 10%”。想自己定上限（比如 3000 积分）：

  ```bash
  DREAMINA_CREDIT_CAP=3000 python3 run_dreamina.py
  ```

- 只想先看看要花多少积分，不生成：`python3 run_dreamina.py --quote-only`（会上传素材、建节点、报价，但不扣分）。
- 每个节点都用它自己的报价作为确认上限，价格变高就停下这个单元，不会自动多花。

## 四、中断、报错、重跑

- 每一步都记在 `state.json`，每个单元的详细记录在 `logs/<单元>.log`。
- 任何时候重跑 `python3 run_dreamina.py` 都安全：已经提交过的单元 **只会继续等待和下载，不会重复扣分**（同一个单元永远用同一个提交 ID）。
- 某个单元生成失败（比如被审核拒绝），汇总里会列出来，并给出重拍命令，例如：
  `python3 run_dreamina.py --units u05 --take {take + 1}`（会再次扣分）。
- 只跑部分单元：`python3 run_dreamina.py --units u01,u02,u03`。
- 演练（只打印要执行的命令，不上传、不扣分）：`python3 run_dreamina.py --dry-run`。
- 找不到 `dreamina-canvas`：用 `DREAMINA_CANVAS=/完整路径/dreamina-canvas python3 run_dreamina.py` 指定。
- 提示登录失效：先 `dreamina-canvas auth login`，再重跑。

## 五、下载提醒

- 如果脚本提示某些视频“需手动下载”：在浏览器打开脚本打印的画布链接，找到标题为 `u05 take-{take}` 这样的节点，
  下载后按 `takes/u05/take-{take}.mp4` 的名字放好，再运行一次脚本，它会重新打包。
- 即梦的视频样片最多保存 7 天，过期后不能再用，请生成完尽快下载、发回。

## 六、发回成品

1. 把 `takes.zip`（如果没有就把整个 `takes` 文件夹加上 `results.json`）上传到 Google Drive；
2. 右键 → 共享 → “知道链接的任何人” 设为 “查看者” → 复制链接；
3. 把链接发回来即可。我这边会自动导入、量口型对齐、挑选，并拼成 1080p 成片；需要重拍的单元会再发一个小的重拍包。

## 七、文件说明

| 文件 | 说明 |
| --- | --- |
| `run_dreamina.py` | 运行脚本（只用 Python 自带功能） |
| `units/<单元>/request.json` | 这个单元的提示词、参考图顺序（图片1、图片2…，音频1）、时长、分辨率 |
| `units/<单元>/prompt.txt` | 同样的提示词，方便阅读；网页端手动生成时也可以照着用 |
| `units/<单元>/*.wav` | 这个单元对应的歌曲片段（唱段是人声，无口型段是伴奏） |
| `images/` | 定妆组图和场景图（全部是生成图，没有官方原图） |
| `manifest.json` | 本期信息和文件清单 |

## 八、单元清单

| 单元 | 类型 | 时长 | 参考图 | 音频 |
| --- | --- | --- | --- | --- |
{table}
"""
