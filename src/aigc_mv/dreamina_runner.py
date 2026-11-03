#!/usr/bin/env python3
"""即梦（Dreamina）视频批量生成器：每个单元一条视频，可断点续跑。

在已经登录 dreamina-canvas 的电脑上运行（只用 Python 3 标准库）：

    cd 解压目录 && python3 run_dreamina.py

流程：检查登录和积分 -> 实时查询 Seedance 模型能力 -> 创建/复用画布 -> 上传参考图和音频
-> 每个单元保存一个视频节点并报价 -> 先汇总总报价并检查上限 -> 逐个按报价上限确认并提交
-> 等待生成 -> 下载到 takes/<单元>/take-N.mp4 -> 写 results.json 和 takes.zip。

所有身份（画布、素材、节点、提交）都由单元名和 take 号确定性生成并写进 state.json，
重跑只会继续未完成的部分，已经提交过的单元只会继续等待，不会重复扣积分。

This file is part of aigc-mv (src/aigc_mv/dreamina_runner.py) and is copied verbatim into the
bundle as run_dreamina.py. Keep it Python 3.8 compatible and stdlib only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
import wave
import zipfile
from pathlib import Path

RUNNER_VERSION = 1
NAMESPACE = "aigc-mv-dreamina-v1"
CROCKFORD = "0123456789abcdefghjkmnpqrstvwxyz"

RUNNING = {"pending", "queued", "running", "processing", "submitted", "accepted", "in_progress", "waiting",
           "generating", "created", "submitting", "unknown"}
SUCCESS = {"success", "succeeded", "successful", "completed", "complete", "done", "finished"}
FAILED = {"failed", "failure", "canceled", "cancelled", "rejected", "error", "expired", "timeout"}

EXIT_CONFIRM = 10
EXIT_AUTH = 11
EXIT_RESUME = 20


# ---------------------------------------------------------------- identities

def _digest(*parts: str) -> bytes:
    return hashlib.sha256(":".join((NAMESPACE,) + parts).encode("utf-8")).digest()


def stable_uuid(*parts: str) -> str:
    """Deterministic, canonical lowercase UUID (version 4 layout) for retry identities."""
    return str(uuid.UUID(bytes=_digest(*parts)[:16], version=4))


def stable_node_id(*parts: str) -> str:
    """node_ + 10 lowercase Crockford Base32 characters (the CLI's canonical Node ID form)."""
    n = int.from_bytes(_digest("node", *parts)[:8], "big")
    out = ""
    for _ in range(10):
        out += CROCKFORD[n & 31]
        n >>= 5
    return "node_" + out


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def is_mp4(path: Path) -> bool:
    """A real video file: more than 1000 bytes with an ISO BMFF ftyp box at the start."""
    try:
        if not path.is_file() or path.stat().st_size <= 1000:
            return False
        with open(path, "rb") as f:
            return f.read(12)[4:8] == b"ftyp"
    except OSError:
        return False


def unit_ids(project_id: str, unit: str, take: int) -> dict:
    return {
        "node_id": stable_node_id(project_id, unit, str(take)),
        "update_id": stable_uuid("update", project_id, unit, str(take)),
        "submit_id": stable_uuid("submit", project_id, unit, str(take)),
    }


def resource_id_for(project_id: str, sha: str) -> str:
    return stable_uuid("resource", project_id, sha)


# ---------------------------------------------------------------- small utils

def now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def atomic_write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(str(tmp), str(path))


def redact(cmd: list) -> list:
    out, hide = [], False
    for a in cmd:
        out.append("***" if hide else a)
        hide = a == "--credit-token"
    return out


def shell_quote(a: str) -> str:
    if a and re.match(r"^[A-Za-z0-9_@%+=:,./-]+$", a):
        return a
    return "'" + a.replace("'", "'\"'\"'") + "'"


def wav_seconds(path: Path):
    try:
        with wave.open(str(path), "rb") as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        return None


def parse_json(text: str):
    text = (text or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except ValueError:
        pass
    for line in reversed(text.splitlines()):  # last JSON line wins
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except ValueError:
                continue
    return None


def find_cli(explicit: str = "") -> str:
    """DREAMINA_CANVAS env / --cli, then PATH, then common install places."""
    for c in (explicit, os.environ.get("DREAMINA_CANVAS", "")):
        if c:
            p = Path(c).expanduser()
            if p.is_file():
                return str(p)
            w = shutil.which(c)
            if w:
                return w
    w = shutil.which("dreamina-canvas")
    if w:
        return w
    for c in ("~/.local/bin/dreamina-canvas", "~/bin/dreamina-canvas", "/opt/homebrew/bin/dreamina-canvas",
              "/usr/local/bin/dreamina-canvas"):
        p = Path(c).expanduser()
        if p.is_file():
            return str(p)
    return ""


# ---------------------------------------------------------------- CLI layer

class CliResult:
    def __init__(self, code: int, obj, raw: str = ""):
        self.code, self.obj, self.raw = code, obj, raw

    @property
    def ok(self) -> bool:
        return self.code == 0 and isinstance(self.obj, dict) and self.obj.get("ok") is not False

    @property
    def data(self) -> dict:
        return (self.obj or {}).get("data") or {} if isinstance(self.obj, dict) else {}

    @property
    def error(self) -> dict:
        return (self.obj or {}).get("error") or {} if isinstance(self.obj, dict) else {}

    def brief(self) -> str:
        e = self.error
        v = e.get("validation") or {}
        bits = [str(x) for x in (e.get("code"), e.get("class"), v.get("reasonCode"), v.get("fieldPath"),
                                 v.get("detail") or e.get("message"), e.get("requiredAction")) if x]
        rid = ((self.obj or {}).get("meta") or {}).get("requestId") if isinstance(self.obj, dict) else None
        if rid:
            bits.append("requestId=" + str(rid))
        return f"exit {self.code}: " + (" | ".join(bits) if bits else (self.raw or "")[-300:])


class Cli:
    """Thin wrapper: every call gets --format json --non-interactive; write calls are skipped in dry-run."""

    def __init__(self, exe: str, log=None, dry_run: bool = False, runner=None):
        self.exe, self.log, self.dry_run = exe, log, dry_run
        self.runner = runner or self._subprocess
        self.calls = []

    def _subprocess(self, cmd: list, timeout: float):
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")

    def call(self, args: list, write: bool = False, timeout: float = 900, unit_log=None) -> CliResult:
        cmd = [self.exe] + [str(a) for a in args] + ["--format", "json", "--non-interactive"]
        shown = " ".join(shell_quote(a) for a in redact(cmd))
        self.calls.append(redact(cmd))
        for lg in (self.log, unit_log):
            if lg:
                lg(("[演练，未执行] " if (write and self.dry_run) else "$ ") + _short(shown))
        if write and self.dry_run:
            return CliResult(0, {"ok": True, "data": {}, "dryRun": True})
        try:
            code, out, err = self.runner(cmd, timeout)
        except subprocess.TimeoutExpired:
            return CliResult(-1, None, "local subprocess timeout")
        except OSError as e:
            return CliResult(-2, None, str(e))
        obj = parse_json(out) or parse_json(err)
        res = CliResult(code, obj, (out or "") + (err or ""))
        if not res.ok:
            for lg in (self.log, unit_log):
                if lg:
                    lg("  -> " + res.brief())
        return res


def _short(s: str, n: int = 600) -> str:
    return s if len(s) <= n else s[:n] + f" …(+{len(s) - n} 字)"


# ---------------------------------------------------------------- model discovery

def _num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _flag(mode: dict, name: str) -> dict:
    for f in mode.get("flags") or []:
        if str(f.get("flag", "")).lstrip("-") == name:
            return f
    return {}


def _version(item: dict) -> float:
    text = " ".join([str(item.get("model", "")), str(item.get("displayName", ""))] + list(item.get("aliases") or []))
    best = 0.0
    for m in re.finditer(r"(\d+)(?:[._](\d+))?", text):
        v = float(m.group(1) + "." + (m.group(2) or "0"))
        if v < 20:
            best = max(best, v)
    return best


def _tier(item: dict) -> int:
    text = (str(item.get("model", "")) + " " + str(item.get("displayName", ""))).lower()
    if "pro" in text:
        return 2
    if "fast" in text or "lite" in text or "mini" in text:
        return 0
    return 1


def is_seedance(item: dict) -> bool:
    text = " ".join([str(item.get("model", "")), str(item.get("displayName", ""))] + list(item.get("aliases") or []))
    return "seedance" in text.lower() or "即梦视频" in text


def mode_caps(mode: dict) -> dict:
    refs = mode.get("references") or {}
    types = {}
    for t in refs.get("types") or []:
        types[str(t.get("mediaType", "")).lower()] = {"min": t.get("min", 0), "max": t.get("max", 0)}
    excl = {str(x).lower() for x in (refs.get("mutuallyExclusiveTypes") or [])}
    img_max = int(types.get("image", {}).get("max") or 0)
    aud_max = int(types.get("audio", {}).get("max") or 0)
    total = int(refs.get("max") or (img_max + aud_max) or 0)
    together = img_max > 0 and aud_max > 0 and not {"image", "audio"} <= excl
    dur, res, ratio, prompt = _flag(mode, "duration"), _flag(mode, "resolution"), _flag(mode, "ratio"), _flag(mode, "prompt")
    return {
        "image_max": img_max, "audio_max": aud_max, "total_max": total, "image_audio_together": together,
        "mutually_exclusive": sorted(excl),
        "durations": [v for v in (_num(x) for x in dur.get("values") or []) if v is not None],
        "duration_min": dur.get("min"), "duration_max": dur.get("max"), "duration_step": dur.get("step"),
        "duration_required": bool(dur.get("required")),
        "resolutions": list(res.get("values") or []), "ratios": list(ratio.get("values") or []),
        "prompt_max": prompt.get("maxLength"), "vip_required": bool(mode.get("vipRequired")),
        "vip_resolutions": list(mode.get("vipResolutions") or []),
    }


def choose_model(items: list, prefer: str = "") -> dict:
    """Best Seedance model for multimodal reference video (image + audio refs), with the fallback plan.

    Ranking: m2v with image+audio together > m2v images only > first_last_frame; then higher version,
    pro > standard > fast/lite, more reference slots. Returns a spec dict (see mode_caps) plus model/mode/why.
    """
    cands = []
    for it in items:
        if prefer and prefer not in (it.get("model"), it.get("displayName")) and prefer not in (it.get("aliases") or []):
            continue
        if not prefer and not is_seedance(it):
            continue
        for m in it.get("modes") or []:
            name = str(m.get("name", "")).lower()
            if name not in ("m2v", "multi_modal", "first_last_frame"):
                continue
            caps = mode_caps(m)
            if name != "first_last_frame" and caps["image_max"] <= 0:
                continue
            rank = 2 if (name != "first_last_frame" and caps["image_audio_together"]) else (
                1 if name != "first_last_frame" else 0)
            key = (rank, _version(it), _tier(it), caps["total_max"], 0 if caps["vip_required"] else 1)
            cands.append((key, it, "m2v" if name != "first_last_frame" else "first_last_frame", caps))
    if not cands:
        return {}
    cands.sort(key=lambda c: c[0], reverse=True)
    key, it, mode, caps = cands[0]
    spec = dict(caps)
    spec.update({
        "model": it.get("model"), "display_name": it.get("displayName") or it.get("model"), "mode": mode,
        "why": ["多模态参考，图片和音频可同时上传" if key[0] == 2 else (
            "多模态参考，但图片和音频不能同时用（唱段改用首帧模式，口型需人工检查）" if key[0] == 1 else
            "只有首帧模式（口型需人工检查）"),
            f"版本 {key[1]:g}"],
        "alternatives": [f"{c[1].get('model')}:{c[2]}" for c in cands[1:6]],
    })
    # first-frame mode on the same model (fallback for sung units when image+audio is impossible)
    spec["first_frame_mode"] = any(str(m.get("name", "")).lower() == "first_last_frame" for m in it.get("modes") or [])
    return spec


def pick_duration(want: float, spec: dict):
    vals = sorted(set(spec.get("durations") or []))
    if vals:
        up = [v for v in vals if v >= want - 1e-6]
        return (up[0] if up else vals[-1]), (None if up else f"模型最长 {vals[-1]:g} 秒，短于单元 {want:g} 秒")
    lo, hi, st = _num(spec.get("duration_min")), _num(spec.get("duration_max")), _num(spec.get("duration_step"))
    v = float(want)
    if lo is not None and v < lo:
        v = lo
    if st and st > 0:
        base = lo or 0.0
        v = base + math.ceil(round((v - base) / st, 6)) * st
    if hi is not None and v > hi:
        return hi, f"模型最长 {hi:g} 秒，短于单元 {want:g} 秒"
    return v, None


def _res_num(r: str) -> int:
    m = re.search(r"(\d+)", str(r))
    return int(m.group(1)) if m else 0


def pick_resolution(want: str, spec: dict) -> str:
    vals = spec.get("resolutions") or []
    if not vals:
        return want.upper()
    for v in vals:
        if str(v).lower() == want.lower():
            return v
    w = _res_num(want)
    return sorted(vals, key=lambda v: (abs(_res_num(v) - w), -_res_num(v)))[0]


def pick_ratio(want: str, spec: dict) -> str:
    vals = spec.get("ratios") or []
    return want if (not vals or want in vals) else vals[0]


def fmt_num(v) -> str:
    return f"{v:g}" if isinstance(v, float) else str(v)


# ---------------------------------------------------------------- per-unit plan + prompt

def is_sheet(path: str) -> bool:
    return Path(path).stem.endswith("_sheet")


def ref_names(prompt: str) -> dict:
    """{N: 名字} from the 【参考图】 clauses '@图片N是名字（角色）'."""
    return {int(m.group(1)): m.group(2) for m in re.finditer(r"@图片(\d+)是([^（(，,：:。\s]+)", prompt)}


def plan_unit(req: dict, spec: dict) -> dict:
    """Decide mode, kept images, audio, duration, resolution, ratio for one unit under the live model spec."""
    images = list(req.get("images") or [])
    audio = req.get("audio")
    kind = req.get("kind", "motion")
    notes = []
    mode = spec.get("mode", "m2v")
    keep = list(range(1, len(images) + 1))
    use_audio = bool(audio)
    first_frame = None
    if mode == "m2v" and audio and not spec.get("image_audio_together"):
        if kind == "sung" and spec.get("first_frame_mode"):
            mode = "first_frame"
        else:
            use_audio = False
            notes.append("模型不能同时参考图片和音频：不上传音频，成片音轨以原曲为准")
    if mode == "first_last_frame":
        mode = "first_frame"
    if mode == "first_frame":
        ff = req.get("first_frame")
        if ff:
            first_frame = ff
        else:
            plates = [i for i, p in enumerate(images, 1) if not is_sheet(p)]
            idx = plates[0] if plates else 1
            first_frame = images[idx - 1] if images else None
        keep, use_audio = [], False
        notes.append("首帧模式：没有音频参考，口型对不上的概率大，必须人工看口型；"
                     "ep sync 只有在成片原样带着这段音频时才能量对齐")
    else:
        lim_img = spec.get("image_max") or len(images)
        total = spec.get("total_max") or (len(images) + 1)
        if use_audio and spec.get("audio_max", 1) < 1:
            use_audio = False
        lim = max(1, min(lim_img, total - (1 if use_audio else 0)))
        if len(keep) > lim:
            dropped = []
            for pred in (lambda i: not is_sheet(images[i - 1]), lambda i: i != 1):  # plates first, then extra people
                for i in reversed(list(keep)):
                    if len(keep) <= lim:
                        break
                    if pred(i):
                        keep.remove(i)
                        dropped.append(i)
            notes.append("参考数超过模型上限 {}：去掉 ".format(lim) + "、".join(
                f"图片{i}（{Path(images[i - 1]).stem}）" for i in sorted(dropped)))
    dur, dnote = pick_duration(float(req.get("duration") or 5), spec)
    if dnote:
        notes.append(dnote)
    elif abs(dur - float(req.get("duration") or 5)) > 1e-6:
        notes.append(f"时长 {fmt_num(req.get('duration'))} 秒不在可选项里，用 {fmt_num(dur)} 秒（剪辑时裁掉多余部分）")
    res = pick_resolution(str(req.get("resolution") or "720p"), spec)
    if res.lower() != str(req.get("resolution") or "720p").lower():
        notes.append(f"分辨率改用 {res}")
    ratio = pick_ratio(str(req.get("aspect_ratio") or "16:9"), spec)
    if ratio != (req.get("aspect_ratio") or "16:9"):
        notes.append(f"画幅改用 {ratio}")
    return {"mode": "first_last_frame" if mode == "first_frame" else "m2v", "keep": keep,
            "use_audio": use_audio, "first_frame": first_frame, "duration": dur, "resolution": res,
            "ratio": ratio, "notes": notes}


def build_prompt(prompt: str, n_images: int, keep_rids: dict, audio_rid, placeholders: bool = True) -> str:
    """@图片N -> {{res:<id>}} for kept images (the CLI's prompt binding); dropped ones fall back to their name.

    keep_rids: {N: resourceId}. audio_rid: resourceId or None (then @音频1 becomes plain words).
    """
    names = ref_names(prompt)
    text = prompt.replace("{{", "\\{{") if placeholders else prompt
    dropped = [i for i in range(1, n_images + 1) if i not in keep_rids]
    for i in dropped:  # remove the dropped clause from 【参考图】, then mention by name
        text = re.sub(r"@图片%d是[^，,：:。]*([，,]?)" % i, "", text)
    text = re.sub(r"[，,]+([：:。])", r"\1", text).replace("】：", "】").replace("】，", "】")
    if dropped:  # a rule sentence whose whole group was dropped ("。：只用来对齐场景。") goes too
        text = re.sub(r"([。\n])[：:][^。\n]*。", r"\1", text)

    def img(m):
        i = int(m.group(1))
        if i in keep_rids:
            return "{{res:%s}}" % keep_rids[i] if placeholders else m.group(0)
        return names.get(i, "参考场景")

    text = re.sub(r"@图片(\d+)", img, text)

    def aud(m):
        if audio_rid:
            return "{{res:%s}}" % audio_rid if placeholders else m.group(0)
        return "原曲"

    return re.sub(r"@音频(\d+)", aud, text)


# ---------------------------------------------------------------- runner

class Runner:
    def __init__(self, root: Path, args, cli: Cli, out=print):
        self.root, self.args, self.cli, self.out = root, args, cli, out
        self.state_path = root / "state.json"
        self.state = self._load_state()
        self.logs = root / "logs"
        self.logs.mkdir(exist_ok=True)
        self.manifest = self._load_manifest()
        self.take = int(args.take or self.manifest.get("take") or 1)

    # -- bookkeeping
    def _load_state(self) -> dict:
        if self.state_path.is_file():
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        return {"version": RUNNER_VERSION, "resources": {}, "units": {}}

    def _load_manifest(self) -> dict:
        p = self.root / "manifest.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}

    def save(self) -> None:
        if not self.args.dry_run:
            atomic_write_json(self.state_path, self.state)

    def log(self, msg: str) -> None:
        with open(self.logs / "run.log", "a", encoding="utf-8") as f:
            f.write(f"{now()} {msg}\n")

    def ulog(self, unit: str):
        path = self.logs / f"{unit}.log"

        def w(msg: str) -> None:
            with open(path, "a", encoding="utf-8") as f:
                f.write(f"{now()} {msg}\n")
        return w

    def say(self, msg: str) -> None:
        self.out(msg)
        self.log(msg)

    def key(self, unit: str) -> str:
        return f"{unit}/take-{self.take}"

    def units(self) -> list:
        names = self.manifest.get("units") or sorted(p.name for p in (self.root / "units").iterdir()
                                                    if (p / "request.json").is_file())
        if self.args.units:
            want = [u.strip() for u in self.args.units.split(",") if u.strip()]
            unknown = [u for u in want if u not in names]
            if unknown:
                raise SystemExit("找不到这些单元：" + "、".join(unknown))
            names = [u for u in names if u in want]
        return names

    def request(self, unit: str) -> dict:
        return json.loads((self.root / "units" / unit / "request.json").read_text(encoding="utf-8"))

    def rec(self, unit: str) -> dict:
        r = self.state["units"].setdefault(self.key(unit), {"unit": unit, "take": self.take, "status": "new"})
        return r

    # -- steps
    def preflight(self) -> bool:
        a = self.args
        r = self.cli.call(["version"])
        self.say(f"dreamina-canvas：{self.cli.exe}（版本 {r.data.get('version', '未知')}）")
        st = self.cli.call(["auth", "status"])
        if not st.ok or not st.data.get("loggedIn"):
            self.say("还没有登录即梦：请先在终端运行  dreamina-canvas auth login  按提示在浏览器里授权，然后重跑本脚本。")
            if not a.dry_run:
                return False
            self.say("（演练模式：继续用假设的模型能力打印命令）")
            return True
        self.say(f"登录状态：已登录（区域 {st.data.get('region', '?')}，账号配置 {st.data.get('profile', '?')}）")
        acc = self.cli.call(["auth", "account"])
        if acc.ok:
            d = acc.data
            credits = d.get("availableCredits") or (d.get("credits") or {}).get("available")
            self.balance = _num(credits)
            vip = d.get("vipLevel") or ("会员" if d.get("isVip") else "非会员")
            exp = d.get("vipLevelExpiresAt") or ""
            self.say(f"账号：{d.get('displayName') or d.get('userId')}，会员：{vip}{('（到期 ' + exp + '）') if exp else ''}，"
                     f"可用积分：{credits if credits is not None else '未知'}")
        else:
            self.say("读取账号积分失败（继续，但无法预先比较余额）：" + acc.brief())
        return True

    balance = None

    def discover(self) -> dict:
        a = self.args
        items = []
        for args in (["model", "find", "seedance", "--type", "video"], ["model", "list", "--type", "video"]):
            r = self.cli.call(args)
            if r.ok:
                for it in r.data.get("items") or []:
                    if it.get("model") and all(x.get("model") != it.get("model") for x in items):
                        items.append(it)
        spec = choose_model(items, a.model or "")
        if not spec:
            if a.dry_run:
                spec = {"model": a.model or "<seedance模型>", "display_name": "演练假设", "mode": "m2v",
                        "image_max": 9, "audio_max": 3, "total_max": 12, "image_audio_together": True,
                        "durations": [], "duration_min": 4, "duration_max": 15, "duration_step": 1,
                        "resolutions": ["480P", "720P"], "ratios": ["16:9"], "prompt_max": None,
                        "first_frame_mode": True, "why": ["演练：未查询到模型，假设多模态参考"], "alternatives": []}
            else:
                self.say("没有找到可用的 Seedance 视频模型（需要支持多模态参考的图片输入）。可用 --model 指定。")
                return {}
        full = self.cli.call(["model", spec["model"], "--type", "video"])
        if full.ok:
            for m in full.data.get("matches") or []:
                g = m.get("generation") or {}
                if g.get("generationKind"):
                    spec["generation_kind"] = g.get("generationKind")
                mats = g.get("materials") or {}
                for t in mats.get("types") or []:
                    if t.get("limits"):
                        spec.setdefault("limits", {})[str(t.get("mediaType", "")).lower()] = t["limits"]
                if mats.get("maxTotalAudioDurationMs"):
                    spec["max_total_audio_ms"] = mats["maxTotalAudioDurationMs"]
        dur = (", ".join(fmt_num(x) for x in spec["durations"]) if spec.get("durations") else
               f"{fmt_num(spec.get('duration_min'))}-{fmt_num(spec.get('duration_max'))} 步长 {fmt_num(spec.get('duration_step'))}")
        self.say(f"选用模型：{spec['display_name']}（{spec['model']}，模式 {spec['mode']}）；"
                 f"{'；'.join(spec['why'])}；参考上限：图片 {spec.get('image_max')}、音频 {spec.get('audio_max')}、"
                 f"合计 {spec.get('total_max')}；互斥类型 {spec.get('mutually_exclusive') or '无'}；"
                 f"时长 {dur}；分辨率 {spec.get('resolutions') or '未声明'}；画幅 {spec.get('ratios') or '未声明'}")
        if spec.get("alternatives"):
            self.say("其他候选：" + "、".join(spec["alternatives"]))
        if str(spec.get("generation_kind", "")).lower() == "sample":
            self.say("注意：该模型生成的是“样片”，样片最多保存 7 天，过期后不能再用来生成正式视频，请尽快下载。")
        self.state["model"] = {k: spec.get(k) for k in ("model", "display_name", "mode", "image_max", "audio_max",
                                                         "total_max", "image_audio_together", "generation_kind")}
        return spec

    def canvas(self) -> bool:
        a = self.args
        ep = self.manifest.get("episode") or self.root.name
        pid = a.project_id or self.state.get("project_id") or stable_uuid("project", ep)
        self.state["project_id"] = pid
        self.save()
        if self.state.get("canvas_ok"):
            self.say(f"画布：{self.state.get('web_url', pid)}")
            return True
        name = self.manifest.get("canvas_name") or f"{ep} 视频"
        r = self.cli.call(["canvas", "create", name, "--project-id", pid], write=True)
        url = (r.data.get("project") or {}).get("webUrl") if r.ok else None
        if not r.ok:
            cursor = None
            for _ in range(20):  # maybe it already exists (earlier run): look it up
                args = ["canvas", "ls", "--limit", "100"] + (["--cursor", cursor] if cursor else [])
                ls = self.cli.call(args)
                if not ls.ok:
                    break
                hit = [i for i in ls.data.get("items") or [] if i.get("projectId") == pid]
                if hit:
                    url = hit[0].get("webUrl")
                    break
                if not ls.data.get("hasMore"):
                    break
                cursor = ls.data.get("nextCursor")
            if not url:
                self.say("创建画布失败：" + r.brief())
                return False
        self.state.update({"canvas_ok": not a.dry_run, "web_url": url or ""})
        self.save()
        self.say(f"画布：{url or pid}（可以在浏览器里打开看进度）")
        return True

    def upload(self, path: Path, kind: str, ulog) -> str:
        sha = file_sha256(path)
        pid = self.state["project_id"]
        known = self.state["resources"].get(sha)
        if known and known.get("uploaded"):
            return known["resourceId"]
        rid = resource_id_for(pid, sha)
        self.state["resources"][sha] = {"resourceId": rid, "file": path.name, "type": kind, "uploaded": False}
        self.save()
        r = self.cli.call(["resource", "upload", "--file", str(path), "--project-id", pid, "--resource-id", rid,
                           "--type", kind, "--name", path.name], write=True, unit_log=ulog)
        if not r.ok:
            raise StepError("上传失败 " + path.name + "：" + r.brief())
        got = r.data.get("resourceId") or rid
        self.state["resources"][sha].update({"resourceId": got, "uploaded": not self.args.dry_run})
        self.save()
        return got

    def prepare(self, unit: str, spec: dict) -> None:
        """Upload refs, save the video node (no run), quote it."""
        rec = self.rec(unit)
        if rec.get("status") not in ("new", "prepare_error", "saved", "quote_error", "quoted", "needs_approval"):
            return  # submitted or later: never touch the node again
        # needs_approval: the confirm or run was refused for price, so nothing ran; re-quote the same saved node
        # (same node and submit id) and confirm again at the new quote under the cap.
        ulog = self.ulog(unit)
        req = self.request(unit)
        pid = self.state["project_id"]
        ids = unit_ids(pid, unit, self.take)
        rec.update({k: rec.get(k) or v for k, v in ids.items()})
        plan = plan_unit(req, spec)
        for n in plan["notes"]:
            ulog("调整：" + n)
        images = req.get("images") or []
        try:
            limits = spec.get("limits") or {}
            aud_lim = limits.get("audio") or {}
            if plan["use_audio"] and req.get("audio"):
                secs = wav_seconds(self.root / req["audio"])
                if secs is not None and aud_lim.get("minDurationMs") and secs * 1000 < aud_lim["minDurationMs"]:
                    plan["notes"].append(f"音频 {secs:.1f} 秒短于模型下限，改为不传音频")
                    plan["use_audio"] = False
            keep_rids = {}
            if plan["mode"] == "first_last_frame":
                refs = [self.upload(self.root / plan["first_frame"], "image", ulog)] if plan["first_frame"] else []
                audio_rid = None
            else:
                for i in plan["keep"]:
                    keep_rids[i] = self.upload(self.root / images[i - 1], "image", ulog)
                refs = [keep_rids[i] for i in plan["keep"]]
                audio_rid = self.upload(self.root / req["audio"], "audio", ulog) if plan["use_audio"] else None
                if audio_rid:
                    refs.append(audio_rid)
            if plan["mode"] == "first_last_frame":
                prompt = build_prompt(req["prompt"], len(images), {}, None)
            else:
                prompt = build_prompt(req["prompt"], len(images), keep_rids, audio_rid)
                pmax = spec.get("prompt_max")
                if pmax and len(prompt) > pmax:
                    plain = build_prompt(req["prompt"], len(images), keep_rids, audio_rid, placeholders=False)
                    if len(plain) <= pmax:
                        plan["notes"].append(f"提示词带引用占位符后 {len(prompt)} 字超过上限 {pmax}，改用 @图片N 文字"
                                             "（按上传顺序对应）")
                        prompt = plain
                    else:
                        raise StepError(f"提示词 {len(plain)} 字超过模型上限 {pmax} 字，需要先缩短")
            (self.logs / f"{unit}.prompt.txt").write_text(prompt, encoding="utf-8")
            rec.update({"mode": plan["mode"], "duration": plan["duration"], "resolution": plan["resolution"],
                        "ratio": plan["ratio"], "refs": refs, "notes": plan["notes"], "model": spec["model"],
                        "requested_duration": req.get("duration"), "kind": req.get("kind")})
            args = ["node", "create", "video", "--project-id", pid, "--node-id", rec["node_id"],
                    "--update-id", rec["update_id"], "--title", f"{unit} take-{self.take}",
                    "--mode", plan["mode"], "--model", spec["model"], "--prompt", prompt]
            for r_ in refs:
                args += ["--ref", "res:" + r_]
            args += ["--ratio", plan["ratio"], "--resolution", plan["resolution"],
                     "--duration", fmt_num(plan["duration"])]
            if not rec.get("saved"):
                if self.args.dry_run and self.args.validate:
                    v = self.cli.call(args + ["--dry-run"], unit_log=ulog)
                    if not v.ok:
                        raise StepError("命令本地校验失败：" + v.brief())
                r = self.cli.call(args, write=True, unit_log=ulog)
                if not r.ok:
                    show = self.cli.call(["node", "show", "--project-id", pid, "--node-id", rec["node_id"]],
                                         unit_log=ulog)
                    found = [n for n in show.data.get("nodes") or [] if n.get("node")] if show.ok else []
                    if not found:
                        raise StepError("保存视频节点失败：" + r.brief())
                    ulog("节点已存在，沿用")
                else:
                    eff = (r.data.get("mutation") or {}).get("effectiveGeneration") or {}
                    if eff:
                        rec["effective"] = eff
                        ulog("服务端生效参数：" + json.dumps(eff, ensure_ascii=False))
                rec.update({"status": "saved", "saved": not self.args.dry_run})
                self.save()
            if self.args.dry_run:
                rec.update({"status": "quoted", "quote": None})
                return
            q = self.cli.call(["node", "quote", "--project-id", pid, "--node-id", rec["node_id"]], unit_log=ulog)
            item = next((i for i in q.data.get("items") or [] if i.get("nodeId") == rec["node_id"]), None) if q.ok else None
            if not item or item.get("error") or item.get("maxCredits") is None:
                err = (item or {}).get("error") or {}
                raise StepError("报价失败：" + (json.dumps(err, ensure_ascii=False) if err else q.brief()), "quote_error")
            rec.update({"quote": int(item["maxCredits"]), "status": "quoted",
                        "confirmation_required": q.data.get("confirmationRequired")})
            ulog(f"报价 {rec['quote']} 积分")
            self.save()
        except StepError as e:
            rec.update({"status": e.status, "error": str(e)})
            ulog("错误：" + str(e))
            self.save()

    def submit(self, unit: str) -> str:
        """confirm with the node's own quote as ceiling, persist the submit id, run. Returns new status."""
        rec, ulog, pid = self.rec(unit), self.ulog(unit), self.state["project_id"]
        token = None
        c = self.cli.call(["node", "confirm", "--project-id", pid, "--node-id", rec["node_id"],
                           "--credit-ceiling", str(rec.get("quote") if rec.get("quote") is not None else 0)],
                          write=True, unit_log=ulog)
        if c.ok:
            token = c.data.get("creditConfirmationToken")  # memory only, never written to state or logs
        elif rec.get("confirmation_required") is not False:
            rec.update({"status": "needs_approval", "error": "确认积分上限失败：" + c.brief()})
            self.save()
            return rec["status"]
        rec.update({"status": "submitting", "submitted_at": now(), "ceiling": rec.get("quote")})
        self.save()  # submit id is persisted BEFORE the run request
        args = ["node", "run", "--project-id", pid, "--node-id", rec["node_id"], "--submit-id", rec["submit_id"]]
        if token:
            args += ["--credit-token", token]
        r = self.cli.call(args, write=True, unit_log=ulog)
        if self.args.dry_run:
            return "submitted"
        item = next((i for i in r.data.get("items") or [] if i.get("nodeId") == rec["node_id"]), {}) if r.ok else {}
        if r.code == EXIT_CONFIRM:
            rec.update({"status": "needs_approval", "error": "最新价格超过已确认上限：" + r.brief()})
        elif r.ok and item.get("error"):
            rec.update({"status": "rejected", "error": json.dumps(item["error"], ensure_ascii=False)})
        elif r.ok:
            rec["status"] = "submitted"
        else:
            rec["error"] = "提交结果不确定（不会重新提交，只会继续查询）：" + r.brief()  # stays "submitting"
        self.save()
        return rec["status"]

    def poll(self, unit: str) -> str:
        """One read-only look at the operation; returns the (possibly new) status."""
        rec, ulog, pid = self.rec(unit), self.ulog(unit), self.state["project_id"]
        r = self.cli.call(["operation", "wait", rec["submit_id"], "--project-id", pid, "--timeout", "0"],
                          unit_log=ulog, timeout=300)
        if r.code == EXIT_AUTH:
            raise AuthLost(r.brief())
        d = r.data
        sub = d.get("submission") or {}
        if str(sub.get("state", "")).lower() == "absent" and rec["status"] == "submitting":
            if sub.get("resubmittable"):
                ulog("服务端没有这次提交的记录且允许重提：用同一个提交 ID 重新提交")
                rec["status"] = "quoted"
                self.save()
                return "quoted"
            rec.update({"status": "needs_attention", "error": "服务端查不到这次提交（不自动重提，请在画布上确认）："
                        + json.dumps(sub, ensure_ascii=False)})
            self.save()
            return rec["status"]
        state = str(d.get("state", "")).lower()
        if not r.ok or state in RUNNING or not state:
            rec["polls"] = rec.get("polls", 0) + 1
            if rec["status"] == "submitting" and r.ok:
                rec["status"] = "submitted"
            if r.code not in (0, EXIT_RESUME):
                rec["poll_errors"] = rec.get("poll_errors", 0) + 1
            self.save()
            return rec["status"]
        res = d.get("resources") or []
        good = [x for x in res if str(x.get("state", "")).lower() in SUCCESS]
        if not good and state in SUCCESS:
            good = [x for x in res if str(x.get("state", "")).lower() not in FAILED and x.get("resourceId")]
        if good:
            rec.update({"status": "generated", "resource_id": good[0]["resourceId"], "error": None})
            ulog("生成完成：" + good[0]["resourceId"])
        else:
            err = d.get("submissionError") or res
            rec.update({"status": "failed", "error": json.dumps(err, ensure_ascii=False)[:800]})
            ulog("生成失败：" + rec["error"])
        self.save()
        return rec["status"]

    def download(self, unit: str) -> str:
        rec, ulog, pid = self.rec(unit), self.ulog(unit), self.state["project_id"]
        dst = self.root / "takes" / unit / f"take-{self.take}.mp4"
        dst.parent.mkdir(parents=True, exist_ok=True)
        if rec.get("status") == "manual_download" and is_mp4(dst):
            rec.update({"status": "downloaded", "file": str(dst.relative_to(self.root)), "size": dst.stat().st_size,
                        "sha256": file_sha256(dst), "error": None, "manual": True})
            ulog(f"已找到手动放好的 {rec['file']}（{rec['size']} 字节），不再下载")
            self.save()
            return rec["status"]
        info = self.cli.call(["resource", "get", rec["resource_id"], "--project-id", pid], unit_log=ulog)
        if info.ok:
            v = info.data.get("video") or {}
            rec["video"] = {k: v.get(k) for k in ("width", "height", "durationSeconds", "fps", "resolution")}
            if info.data.get("generationKind"):
                rec["generation_kind"] = info.data.get("generationKind")
        if dst.exists():
            dst.unlink()
        r = self.cli.call(["resource", "download", rec["resource_id"], "-o", str(dst), "--project-id", pid],
                          unit_log=ulog, timeout=1800)
        ok = r.ok and dst.is_file() and dst.stat().st_size > 1000
        if ok:
            ok = is_mp4(dst)
            if not ok:
                ulog("下载的文件不是 mp4")
        if ok:
            rec.update({"status": "downloaded", "file": str(dst.relative_to(self.root)),
                        "size": r.data.get("size") or dst.stat().st_size, "sha256": r.data.get("sha256"),
                        "error": None})
            ulog(f"已下载 {rec['file']}（{rec['size']} 字节）")
        else:
            if dst.exists() and not ok:
                dst.unlink()
            rec.update({"status": "manual_download",
                        "error": "命令行没能下载这条视频：" + (r.brief() if not r.ok else "文件无效")})
            ulog(rec["error"])
        self.save()
        return rec["status"]

    # -- main
    def run(self) -> int:
        a = self.args
        self.say(f"==== {now()} 开始（take-{self.take}{'，演练模式' if a.dry_run else ''}）")
        if not self.preflight():
            return 2
        spec = self.discover()
        if not spec:
            return 3
        if not self.canvas():
            return 4
        units = self.units()
        self.say(f"共 {len(units)} 个单元；第一步：上传参考并保存节点、报价（不花积分）")
        for i, u in enumerate(units, 1):
            st = self.rec(u).get("status")
            self.prepare(u, spec)
            rec = self.rec(u)
            if rec.get("status") in ("prepare_error", "quote_error") or (not a.dry_run and st != rec.get("status")):
                self.out(f"  [{i}/{len(units)}] {u}：{_STATUS_CN.get(rec['status'], rec['status'])}"
                         + (f"，报价 {rec.get('quote')} 积分" if rec.get("quote") is not None else "")
                         + (f"（{rec.get('error')}）" if rec.get("error") and "error" in rec["status"] else ""))
        todo = [u for u in units if self.rec(u)["status"] == "quoted"]
        waiting = [u for u in units if self.rec(u)["status"] in ("submitting", "submitted")]
        total = sum(int(self.rec(u).get("quote") or 0) for u in todo)
        cap = a.credit_cap if a.credit_cap is not None else _num(os.environ.get("DREAMINA_CREDIT_CAP"))
        cap_txt = (f"你设定的总上限 {fmt_num(cap)} 积分" if cap is not None else
                   "没有设总上限（以账号余额和每个单元自己的报价为准；可用 DREAMINA_CREDIT_CAP 或 --credit-cap 设定）")
        self.say(f"待提交 {len(todo)} 个单元，总报价 {total} 积分；{cap_txt}；"
                 f"上次已提交、继续等待的 {len(waiting)} 个")
        if todo and not a.dry_run:
            if cap is not None and total > cap:
                self.say(f"总报价 {total} 超过上限 {fmt_num(cap)}：没有花任何积分，已停止。"
                         "可以设置 DREAMINA_CREDIT_CAP 或 --credit-cap 提高上限，或用 --units 分批。")
                self.finish(units)
                return 5
            if self.balance is not None and total > self.balance:
                self.say(f"账号可用积分 {fmt_num(self.balance)} 少于总报价 {total}：没有花任何积分，已停止。"
                         "充值后重跑，或用 --units 分批。")
                self.finish(units)
                return 5
        if a.quote_only:
            self.say("只报价模式：到此为止，没有花积分。")
            self.finish(units)
            return 0
        self.loop(units, todo, cap)
        return self.finish(units)

    def loop(self, units: list, todo: list, cap) -> None:
        a = self.args
        spent = 0
        queue = list(todo)
        inflight = [u for u in units if self.rec(u)["status"] in ("submitting", "submitted")]
        ready = [u for u in units if self.rec(u)["status"] in ("generated", "manual_download")]
        started = {u: time.time() for u in inflight}
        for u in ready:
            self.download(u)
        if a.dry_run:
            for u in queue:
                self.submit(u)
            self.say("演练结束：以上 node confirm / node run 只是打印，没有执行。")
            return
        while queue or inflight:
            while queue and len(inflight) < a.parallel:
                u = queue[0]
                q = int(self.rec(u).get("quote") or 0)
                if cap is not None and spent + q > cap:
                    self.say(f"{u}：再提交会超过上限 {fmt_num(cap)}（已确认 {spent}），停止提交。")
                    queue = []
                    break
                queue.pop(0)
                st = self.submit(u)
                if st in ("submitted", "submitting"):
                    spent += q
                    inflight.append(u)
                    started[u] = time.time()
                    self.say(f"已提交 {u}（上限 {q} 积分，提交 ID {self.rec(u)['submit_id']}）")
                else:
                    self.say(f"{u} 没有提交：{_STATUS_CN.get(st, st)}（{self.rec(u).get('error')}）")
            if not inflight:
                break
            time.sleep(a.interval)
            for u in list(inflight):
                try:
                    st = self.poll(u)
                except AuthLost as e:
                    self.say("登录失效，停止（已提交的单元下次运行会继续等待）：" + str(e))
                    return
                if st == "quoted":  # resubmittable with the same submit id
                    inflight.remove(u)
                    queue.insert(0, u)
                    spent -= int(self.rec(u).get("quote") or 0)
                elif st == "generated":
                    inflight.remove(u)
                    self.download(u)
                    self.say(f"{u} 完成：{_STATUS_CN.get(self.rec(u)['status'])}")
                elif st not in ("submitted", "submitting"):
                    inflight.remove(u)
                    self.say(f"{u}：{_STATUS_CN.get(st, st)}（{self.rec(u).get('error')}）")
                elif time.time() - started.get(u, time.time()) > a.max_wait * 60 or self.rec(u).get("poll_errors", 0) > 20:
                    inflight.remove(u)
                    self.say(f"{u} 等待超过 {a.max_wait} 分钟，先放一放；下次运行会用同一个提交 ID 继续等，不会重复扣分。")

    def finish(self, units: list) -> int:
        rows = []
        for u in units:
            r = self.rec(u)
            rows.append({k: r.get(k) for k in ("unit", "take", "status", "file", "size", "sha256", "kind", "model",
                                               "mode", "requested_duration", "duration", "resolution", "ratio",
                                               "quote", "notes", "node_id", "submit_id", "resource_id", "video",
                                               "generation_kind", "error")})
        res = {"episode": self.manifest.get("episode"), "take": self.take, "runner_version": RUNNER_VERSION,
               "updated": now(), "model": self.state.get("model"), "project_id": self.state.get("project_id"),
               "web_url": self.state.get("web_url"), "units": rows}
        if not self.args.dry_run:
            atomic_write_json(self.root / "results.json", res)
        if self.args.dry_run:
            self.say(f"演练汇总：{len(rows)} 个单元的命令都已打印（详见 logs/<单元>.log），没有上传、保存或扣分。")
            return 0
        done = [x for x in rows if x["status"] == "downloaded"]
        manual = [x for x in rows if x["status"] == "manual_download"]
        bad = [x for x in rows if x["status"] not in ("downloaded", "manual_download", "submitted", "submitting",
                                                      "quoted", "saved", "new")]
        pending = [x for x in rows if x["status"] in ("submitted", "submitting")]
        if done and not self.args.dry_run:
            z = self.root / "takes.zip"
            tmp = z.with_name("takes.zip.tmp")
            with zipfile.ZipFile(tmp, "w", zipfile.ZIP_STORED) as zf:
                for p in sorted((self.root / "takes").glob("*/*.mp4")):
                    zf.write(p, str(p.relative_to(self.root)))
                zf.write(self.root / "results.json", "results.json")
            os.replace(str(tmp), str(z))
            self.say(f"已打包 {z.name}（{z.stat().st_size / 1e6:.1f} MB）：把它上传到 Google Drive，发“任何人可查看”的链接回来")
        self.say(f"汇总：已下载 {len(done)}，需手动下载 {len(manual)}，仍在生成 {len(pending)}，有问题 {len(bad)}，共 {len(rows)}")
        if manual:
            self.say("命令行没能下载的视频：请在浏览器打开画布 " + (self.state.get("web_url") or "") +
                     "，找到标题为下面这些的节点，右键下载，存成 takes/<单元>/take-%d.mp4：" % self.take)
            for x in manual:
                self.say(f"  {x['unit']} take-{self.take}（资源 ID {x['resource_id']}）")
            self.say("提醒：样片最多保存 7 天，请尽快下载。")
        if bad:
            for x in bad:
                self.say(f"  {x['unit']}：{_STATUS_CN.get(x['status'], x['status'])}（{x.get('error')}）")
            redo = ",".join(x["unit"] for x in bad if x["status"] in ("failed", "rejected"))
            if redo:
                self.say(f"失败的单元可以换一个 take 号重新生成（会再次扣分）：python3 run_dreamina.py --units {redo} "
                         f"--take {self.take + 1}")
            if any(x["status"] == "needs_approval" for x in bad):
                self.say("“需要重新确认积分”的单元还没有扣分：重跑同一条命令会重新报价，在上限和余额之内按新报价确认并提交"
                         "（同一个节点和提交 ID）。")
        if pending:
            self.say("还有单元在生成：过一会儿再运行同一条命令，会继续等待并下载，不会重复扣分。")
        return 0 if not bad else 1


_STATUS_CN = {
    "new": "未开始", "saved": "节点已保存", "quoted": "已报价", "prepare_error": "准备失败", "quote_error": "报价失败",
    "submitting": "提交中（结果待确认）", "submitted": "生成中", "generated": "已生成", "downloaded": "已下载",
    "manual_download": "需手动下载", "failed": "生成失败", "rejected": "提交被拒", "needs_approval": "需要重新确认积分",
    "needs_attention": "需要人工确认",
}


class StepError(Exception):
    def __init__(self, msg: str, status: str = "prepare_error"):
        super().__init__(msg)
        self.status = status


class AuthLost(Exception):
    pass


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="即梦视频批量生成（每个单元一条，可断点续跑）")
    p.add_argument("--units", default="", help="只跑这些单元，逗号分隔，如 u01,u02")
    p.add_argument("--take", type=int, default=0, help="take 号（默认 manifest 里的，通常 1；重拍用 2、3…）")
    p.add_argument("--credit-cap", type=float, default=None, help="本次最多花多少积分（也可用环境变量 DREAMINA_CREDIT_CAP）")
    p.add_argument("--dry-run", action="store_true", help="演练：只打印会执行的写操作，不上传、不保存、不扣分")
    p.add_argument("--no-validate", dest="validate", action="store_false",
                   help="演练时不调用 node create video --dry-run 做本地校验")
    p.add_argument("--quote-only", action="store_true", help="只上传、保存节点和报价，不提交生成")
    p.add_argument("--parallel", type=int, default=3, help="同时生成的单元数（默认 3）")
    p.add_argument("--interval", type=float, default=15, help="查询进度的间隔秒数（默认 15）")
    p.add_argument("--max-wait", type=float, default=60, help="每个单元本次最多等多少分钟（默认 60）")
    p.add_argument("--model", default="", help="指定模型（canonical 名），默认自动选最好的 Seedance")
    p.add_argument("--project-id", default="", help="指定画布 UUID（默认由本期名称确定）")
    p.add_argument("--cli", default="", help="dreamina-canvas 路径（也可用环境变量 DREAMINA_CANVAS）")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(__file__).resolve().parent
    if not (root / "units").is_dir():
        root = Path.cwd()
    exe = find_cli(args.cli)
    if not exe:
        print("找不到 dreamina-canvas：请先安装并登录（dreamina-canvas auth login），"
              "或用环境变量 DREAMINA_CANVAS=/完整路径/dreamina-canvas 指定。")
        return 2
    runner = Runner(root, args, Cli(exe, dry_run=args.dry_run))
    runner.cli.log = runner.log
    try:
        return runner.run()
    except KeyboardInterrupt:
        runner.save()
        print("\n已中断。状态已保存，重跑同一条命令会从中断处继续（已提交的不会重复扣分）。")
        return 130


if __name__ == "__main__":
    sys.exit(main())
