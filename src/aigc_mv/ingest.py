"""Bring Dreamina takes back into the episode: `aigc-mv ep ingest-takes <ep> <dir-or-zip>`.

Input is what run_dreamina.py hands back: a folder or a zip with `takes/<unit>/take-N.mp4` and `results.json`
(also inside a wrapper folder, e.g. a zipped `dreamina_bundle/` or a Google Drive download folder; a folder
that only holds `takes.zip` is read through that zip). Each take is copied to `units/<unit>/takes/`:
an identical file already there is left alone, a different file with the same name is kept under a new
name (`take-1.v2.mp4`), nothing is overwritten. The per-take facts from results.json (model, mode, status,
notes) accumulate in `units/ingest.json`; `retakes()` turns takes + those facts into `units/retakes.json`
and `units/retakes.md` with a ready `ep dreamina-bundle … --units … --take N` command.
"""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO, Callable

from aigc_mv.sync import best_take, lips_verified, long_enough, load_unit_takes, takes_dir

TAKE_RE = re.compile(r"(?:^|/)([^/]+)/(take-(\d+)(?:\.v\d+)?\.mp4)$", re.I)
INGEST_LOG = "ingest.json"
RETAKES_JSON = "retakes.json"
RETAKES_MD = "retakes.md"
RETRY_STATUSES = {"failed", "rejected", "needs_attention", "needs_approval"}


@dataclass
class Found:
    unit: str
    name: str
    origin: str
    open: Callable[[], BinaryIO]


@dataclass
class Scan:
    takes: list[Found] = field(default_factory=list)
    results: list[dict] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)
    zips: list[zipfile.ZipFile] = field(default_factory=list)

    def close(self) -> None:
        for z in self.zips:
            z.close()


def _skip(rel: str) -> bool:
    parts = rel.split("/")
    return "__MACOSX" in parts or parts[-1].startswith("._")


def _add(scan: Scan, rel: str, opener: Callable[[], BinaryIO], origin: str, units: set[str]) -> None:
    m = TAKE_RE.search(rel)
    if not m:
        return
    unit, name = m.group(1), m.group(2).lower()
    if unit not in units:
        scan.unknown.append(origin)
        return
    scan.takes.append(Found(unit, name, origin, opener))


def _read_results(text: str, origin: str) -> list[dict]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    rows = data.get("units") if isinstance(data, dict) else None
    out = []
    for r in rows or []:
        if isinstance(r, dict) and r.get("unit"):
            out.append({**r, "_results": origin, "_model": data.get("model"), "_web_url": data.get("web_url")})
    return out


def _scan_zip(scan: Scan, zpath: Path, units: set[str]) -> None:
    z = zipfile.ZipFile(zpath)
    scan.zips.append(z)
    names = [n for n in z.namelist() if not n.endswith("/") and not _skip(n)]
    for n in names:
        _add(scan, n, (lambda n=n: z.open(n)), f"{zpath.name}:{n}", units)
    res = sorted((n for n in names if n.rsplit("/", 1)[-1] == "results.json"), key=lambda n: n.count("/"))
    for n in res:
        scan.results += _read_results(z.read(n).decode("utf-8", errors="replace"), f"{zpath.name}:{n}")


def scan_source(src: Path, units: set[str]) -> Scan:
    src = Path(src)
    scan = Scan()
    if src.is_file():
        if not zipfile.is_zipfile(src):
            raise ValueError(f"{src} is not a zip or a folder")
        _scan_zip(scan, src, units)
        return scan
    if not src.is_dir():
        raise FileNotFoundError(f"no such folder or zip: {src}")
    files = sorted(p for p in src.rglob("*") if p.is_file() and not _skip(p.relative_to(src).as_posix()))
    for p in files:
        rel = p.relative_to(src).as_posix()
        _add(scan, rel, (lambda p=p: p.open("rb")), rel, units)
    for p in sorted((p for p in files if p.name == "results.json"), key=lambda p: len(p.parts)):
        scan.results += _read_results(p.read_text(encoding="utf-8", errors="replace"), p.relative_to(src).as_posix())
    if not scan.takes:  # e.g. the bundle folder after the run: takes live in takes.zip
        for p in files:
            if p.suffix.lower() == ".zip" and zipfile.is_zipfile(p):
                _scan_zip(scan, p, units)
    return scan


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _free_name(d: Path, name: str) -> str:
    stem = name[:-4]
    k = 2
    while (d / f"{stem}.v{k}.mp4").exists():
        k += 1
    return f"{stem}.v{k}.mp4"


def place(f: Found, dst_dir: Path) -> tuple[str, str]:
    """Copy one take into dst_dir. Returns (file name, 'new' | 'same' | 'renamed' | 'invalid')."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    part = dst_dir / ".ingest.partial"
    h = hashlib.sha256()
    head = b""
    with f.open() as r, part.open("wb") as w:
        for b in iter(lambda: r.read(1 << 20), b""):
            if len(head) < 12:
                head += b[:12]
            h.update(b)
            w.write(b)
    if head[4:8] != b"ftyp":
        part.unlink()
        return f.name, "invalid"
    sha = h.hexdigest()
    for p in sorted(dst_dir.glob("*.mp4")):
        if p.stat().st_size == part.stat().st_size and _sha(p) == sha:
            part.unlink()
            return p.name, "same"
    name, state = f.name, "new"
    if (dst_dir / name).exists():
        name, state = _free_name(dst_dir, f.name), "renamed"
    part.rename(dst_dir / name)
    return name, state


def _load_log(ep_dir: Path) -> dict:
    p = Path(ep_dir) / "units" / INGEST_LOG
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


META_KEYS = ("status", "model", "mode", "requested_duration", "duration", "resolution", "ratio", "notes",
             "error", "node_id", "resource_id", "generation_kind", "sha256")


def ingest(ep_dir: Path, src: Path, board) -> dict:
    """Copy takes, record results.json facts. Returns {units: {unit: [{take, file, state, origin}]}, unknown,
    results: n rows, status: {unit: results row without a file}}."""
    ep_dir = Path(ep_dir)
    units = {u.id for u in board.units}
    scan = scan_source(src, units)
    log = _load_log(ep_dir)
    rows = {}
    for r in scan.results:  # shallowest results.json first; later duplicates do not override
        rows.setdefault((r["unit"], f"take-{int(r.get('take') or 1)}.mp4"), r)
    placed: dict[str, list[dict]] = {}
    seen: set[tuple[str, str]] = set()
    try:
        for f in scan.takes:
            name, state = place(f, takes_dir(ep_dir, f.unit))
            if state != "invalid" and (f.unit, name) in seen:
                continue
            seen.add((f.unit, name))
            placed.setdefault(f.unit, []).append({"take": f.name, "file": name, "state": state, "origin": f.origin})
            r = rows.get((f.unit, f.name))
            if r and state != "invalid":
                log.setdefault(f.unit, {})[name] = {k: r.get(k) for k in META_KEYS if r.get(k) not in (None, "", [])}
    finally:
        scan.close()
    pending = {}
    for (unit, take), r in rows.items():
        if unit in units and not any(x["take"] == take and x["state"] != "invalid" for x in placed.get(unit, [])):
            pending[unit] = {"take": take, **{k: r.get(k) for k in ("status", "mode", "notes", "error")
                                             if r.get(k) not in (None, "", [])}}
            if r.get("_web_url"):
                pending[unit]["web_url"] = r["_web_url"]
    for unit, info in pending.items():
        log.setdefault(unit, {})["_last_status"] = info
    for unit in placed:
        log.get(unit, {}).pop("_last_status", None)
    p = ep_dir / "units" / INGEST_LOG
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"units": placed, "unknown": scan.unknown, "results": len(scan.results), "status": pending}


def _take_no(name: str) -> int:
    m = re.match(r"take-(\d+)", name)
    return int(m.group(1)) if m else 0


REASON_CN = {
    "no_take": "没有成片",
    "lip_not_verified": "口型没对上（音轨与参考音频对不齐）",
    "too_short": "成片比单元短",
    "failed": "生成失败",
    "rejected": "审核未通过",
    "needs_attention": "需要处理（提交状态未知）",
    "needs_approval": "需要确认积分",
}


def retakes(ep_dir: Path, board, ep_arg: str | None = None) -> dict:
    """units/retakes.json + units/retakes.md: what to regenerate, what to check by eye, what to download by hand."""
    ep_dir = Path(ep_dir)
    log = _load_log(ep_dir)
    redo, by_eye, manual = [], [], []
    max_take = 1
    for u in board.units:
        ut = load_unit_takes(ep_dir, u.id)
        meta = log.get(u.id, {})
        for t in ut.takes:
            max_take = max(max_take, _take_no(t.take))
        last = meta.get("_last_status") or {}
        t = next((x for x in ut.takes if x.take == ut.pick), None) or best_take(ut, u)
        if t is None:
            st = last.get("status", "")
            if st == "manual_download":
                manual.append({"unit": u.id, "take": last.get("take"), "web_url": last.get("web_url", "")})
                continue
            reasons = ["no_take"] + ([st] if st in RETRY_STATUSES else [])
            redo.append({"unit": u.id, "kind": u.kind, "reasons": reasons, "take": None,
                         "detail": last.get("error") or ""})
            continue
        m = meta.get(t.take, {})
        eye = u.kind == "sung" and (m.get("mode") == "first_last_frame" or (not t.copy_ and t.ncc == 0.0))
        reasons = []
        if u.kind == "sung" and not lips_verified(t) and not eye:
            reasons.append("lip_not_verified")
        if not long_enough(t, u):
            reasons.append("too_short")
        detail = f"{t.take}: lag {t.lag:+.2f}s ncc {t.ncc:.2f} synced {t.synced} 时长 {t.duration:.2f}/{u.duration}s"
        if reasons:
            redo.append({"unit": u.id, "kind": u.kind, "reasons": reasons, "take": t.take, "detail": detail})
        if eye:
            by_eye.append({"unit": u.id, "take": t.take, "mode": m.get("mode", ""), "detail": detail})
    ids = [r["unit"] for r in redo]
    ep_s = ep_arg or str(ep_dir)
    cmd = f"aigc-mv ep dreamina-bundle {ep_s} --units {','.join(ids)} --take {max_take + 1}" if ids else ""
    out = {"retake": redo, "by_eye": by_eye, "manual_download": manual, "take": max_take + 1, "command": cmd}
    d = ep_dir / "units"
    d.mkdir(parents=True, exist_ok=True)
    (d / RETAKES_JSON).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (d / RETAKES_MD).write_text(retakes_md(out), encoding="utf-8")
    return out


def retakes_md(r: dict) -> str:
    lines = ["# 重拍清单", ""]
    if r["retake"]:
        lines += [f"需要重拍 {len(r['retake'])} 个单元：", ""]
        for x in r["retake"]:
            why = "、".join(REASON_CN.get(k, k) for k in x["reasons"])
            lines.append(f"- {x['unit']}（{'唱段' if x['kind'] == 'sung' else '动作'}）：{why}"
                         + (f"；{x['detail']}" if x["detail"] else ""))
        lines += ["", "打重拍包：", "", f"    {r['command']}", ""]
    else:
        lines += ["没有需要重拍的单元。", ""]
    if r["by_eye"]:
        lines += ["口型只能靠肉眼检查（首尾帧模式或成片没有音轨，量不出对齐）：", ""]
        lines += [f"- {x['unit']} {x['take']}" for x in r["by_eye"]] + [""]
    if r["manual_download"]:
        lines += ["已经生成但命令行没下载下来，请到网页画布上手动下载后重新导入：", ""]
        lines += [f"- {x['unit']} {x['take'] or ''} {x['web_url']}".rstrip() for x in r["manual_download"]] + [""]
    return "\n".join(lines)
