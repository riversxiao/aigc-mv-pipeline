"""`aigc-mv ep …` – the episode pipeline (battle / MV), stage by stage.

    init → suno → analyze → board → refs → prompts → approve → (generate) → sync / pick → render
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Optional

import typer

from aigc_mv.board import audit, load_board, plan, render_sheet
from aigc_mv.episode import load_episode
from aigc_mv.tools import jsave

app = typer.Typer(help="Episode pipeline: photoreal rap battles / MVs (Suno + Seedance/即梦)", no_args_is_help=True)

_REPO = Path(__file__).resolve().parents[2]
_EXAMPLE = _REPO / "projects" / "xiangyu_vs_liubang"


def _fail(msg: str) -> None:
    typer.echo(f"ERROR: {msg}", err=True)
    raise typer.Exit(code=1)


@app.command("init")
def init(name: str, root: Path = typer.Option(None, "--root")) -> None:
    """Copy the example episode into projects/NAME."""
    dst = (root or _REPO / "projects") / name
    if dst.exists():
        _fail(f"refusing to overwrite {dst}")
    shutil.copytree(_EXAMPLE, dst, ignore=shutil.ignore_patterns("analysis", "board", "units", "edit", "final",
                                                                 "audio", "*.jsonl", "approvals.json", "REFS.md",
                                                                 "refs_plan.json", "suno.md", "*.png"))
    for sub in ("audio", "refs"):
        (dst / sub).mkdir(exist_ok=True)
    typer.echo(f"created {dst} – edit episode.yaml, then: aigc-mv ep suno {dst}")


@app.command("suno")
def suno(ep_dir: Path, knowledge: Path = typer.Option(None, "--knowledge")) -> None:
    """Write suno.md: two-pass (A, then Extend with B) style + lyric fields."""
    from aigc_mv.prompts import characters, suno_sheets

    ep = load_episode(ep_dir)
    out = ep_dir / "suno.md"
    out.write_text(suno_sheets(ep, characters(ep, knowledge)), encoding="utf-8")
    typer.echo(f"wrote {out}")


@app.command("analyze")
def analyze_cmd(
    ep_dir: Path,
    mode: str = typer.Option("auto", "--mode", help="auto | asr | grid"),
    bpm: Optional[float] = typer.Option(None, "--bpm", help="Tempo hint / synthetic grid without a song"),
    duration: Optional[float] = typer.Option(None, "--duration"),
) -> None:
    """Beat grid, line + half-line times, sections → analysis/timing.json."""
    from aigc_mv.timing import analyze

    ep = load_episode(ep_dir)
    try:
        t = analyze(ep_dir, ep, mode=mode, bpm=bpm, duration=duration)  # type: ignore[arg-type]
    except (FileNotFoundError, ValueError) as e:
        _fail(str(e))
    jsave(ep_dir / "analysis" / "timing.json", t)
    typer.echo(f"{t.grid.bpm} BPM · bar {t.grid.bar:.3f}s · {len(t.lines)} lines · {t.duration:.1f}s · align={t.mode}")
    for ln in t.lines[:4]:
        typer.echo(f"  {ln.t0:6.2f}  {ln.text}")
    if t.mode == "asr":
        flagged = [ln for ln in t.lines if ln.flags]
        typer.echo(f"  {len(t.lines) - len(flagged)} lines clean, {len(flagged)} flagged")
        typer.echo(f"wrote {_write_timing_report(ep_dir, ep, t)}")


def _write_timing_report(ep_dir: Path, ep, t, notes: Optional[Path] = None, out: Optional[Path] = None) -> Path:
    from aigc_mv.timing import envelope_db
    from aigc_mv.timing_report import timing_report

    files, envs = {}, {}
    for name, rel in (("vocals", ep.vocals), ("song", ep.song), ("instrumental", ep.instrumental)):
        if rel and (ep_dir / rel).is_file():
            files[name] = rel
            if name != "song":
                envs[name] = envelope_db(ep_dir / rel)
    text = timing_report(ep, t, envs, files, notes.read_text(encoding="utf-8") if notes else "")
    dst = out or ep_dir / "analysis" / "timing_report.md"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    return dst


@app.command("timing-report")
def timing_report_cmd(
    ep_dir: Path,
    notes: Optional[Path] = typer.Option(None, "--notes", help="Markdown appended at the end (hand-checked findings)"),
    out: Optional[Path] = typer.Option(None, "--out", help="Default analysis/timing_report.md"),
) -> None:
    """Chinese per-line timing report of analysis/timing.json: sections, every line with confidence / source /
    flags, the lines to check by ear, pauses, beat drops, vocals outside the lyric sheet."""
    from aigc_mv.timing import load_timing

    ep = load_episode(ep_dir)
    try:
        t = load_timing(ep_dir)
    except FileNotFoundError as e:
        _fail(str(e))
    typer.echo(f"wrote {_write_timing_report(ep_dir, ep, t, notes, out)}")


@app.command("board")
def board_cmd(ep_dir: Path) -> None:
    """Plan shots + generation units, run the audit, write board/board.json + board/board.md."""
    from aigc_mv.timing import load_timing

    ep = load_episode(ep_dir)
    timing = load_timing(ep_dir)
    b = plan(ep, timing)
    res = audit(ep, b, timing)
    jsave(ep_dir / "board" / "board.json", b)
    jsave(ep_dir / "board" / "audit.json", res)
    (ep_dir / "board" / "board.md").write_text(render_sheet(ep, b, timing, res), encoding="utf-8")
    _print_audit(res)
    typer.echo(f"wrote {ep_dir / 'board' / 'board.md'}")


def _print_audit(res) -> None:
    typer.echo(json.dumps(res.stats, ensure_ascii=False))
    for e in res.errors:
        typer.echo(f"  ✗ {e}")
    for w in res.warnings:
        typer.echo(f"  ! {w}")
    typer.echo("audit: PASS" if res.ok else "audit: FAIL")


@app.command("audit")
def audit_cmd(ep_dir: Path) -> None:
    """Re-run the board audit (exit 1 on errors)."""
    from aigc_mv.timing import load_timing

    ep = load_episode(ep_dir)
    res = audit(ep, load_board(ep_dir), load_timing(ep_dir))
    _print_audit(res)
    if not res.ok:
        raise typer.Exit(code=1)


@app.command("refs")
def refs_cmd(ep_dir: Path, knowledge: Path = typer.Option(None, "--knowledge")) -> None:
    """refs/REFS.md: every still to make (face sheets, venue, locations, crowd, first frames)."""
    from aigc_mv.packs import write_refs_doc

    ep = load_episode(ep_dir)
    typer.echo(f"wrote {write_refs_doc(ep_dir, ep, load_board(ep_dir), knowledge)}")


@app.command("plates")
def plates_cmd(ep_dir: Path, candidates: int = typer.Option(4, "--candidates", help="Candidates per plate")) -> None:
    """Show episodes: the arena plate set, the units uploading each plate, and a cost estimate (no API call)."""
    from aigc_mv import plates
    from aigc_mv.prompts import plate_items

    ep = load_episode(ep_dir)
    if ep.format != "show":
        _fail("plates are for show episodes (format: show)")
    env = plate_items(ep, load_board(ep_dir))
    per = plates.per_image_from_ledger(Path(ep_dir) / "ledger.jsonl")
    cost = plates.cost_estimate([x["file"] for x in env], candidates=candidates, per_image=per)
    for x, r in zip(env, cost["rows"]):
        typer.echo(f"{x['file']:<18} {len(x['shots']):>3} shots  units {','.join(x['units']) or '-'}  "
                   f"{r['candidates']} x ${per:.2f} = ${r['usd']:.2f} (upper ${r['usd_upper']:.2f})")
    typer.echo(f"total {cost['images']} images: ${cost['total']:.2f} (upper ${cost['total_upper']:.2f}); "
               "estimate only, nothing generated")


@app.command("canon")
def canon_cmd(
    ep_dir: Path,
    src: Optional[Path] = typer.Option(None, "--src", help="Local folder with <card_id>.jpg/.png/.webp official art (stored as JPEG)"),
    knowledge: Path = typer.Option(None, "--knowledge"),
) -> None:
    """refs/canon/<card_id>.jpg: official art for every canon cast member (gitignored, never commit)."""
    from aigc_mv.canon_refs import fetch_canon

    ep = load_episode(ep_dir)
    res = fetch_canon(ep_dir, ep, src, knowledge)
    for k, how in res.placed.items():
        typer.echo(f"  原作图  {ep.cast[k].name_cn} ({ep.cast[k].character}): {how}")
    for k in res.original:
        typer.echo(f"  原创    {ep.cast[k].name_cn} ({ep.cast[k].character}): 无原作图，第一步用文生图")
    for k, err in res.failed.items():
        typer.echo(f"  失败    {ep.cast[k].name_cn} ({ep.cast[k].character}): {err}", err=True)
    typer.echo(f"wrote {Path(ep_dir) / 'refs' / 'canon'} ({len(res.placed)} canon, {len(res.original)} original)")
    if res.failed:
        raise typer.Exit(code=1)


@app.command("sheets")
def sheets_cmd(
    ep_dir: Path,
    force: bool = typer.Option(False, "--force", help="Also replace sheets that were not made by this command"),
    partial: bool = typer.Option(False, "--partial", help="Also tile incomplete sets (ep prompts keeps flagging them)"),
) -> None:
    """Step 3 of 定妆: tile refs/<key>_face/_34/_profile/_half/_full.png into refs/<key>_sheet.png."""
    from aigc_mv.sheets import build_sheets

    ep = load_episode(ep_dir)
    res = build_sheets(ep_dir, ep, force=force, partial=partial)
    for k in ep.cast:
        nm = ep.cast[k].name_cn
        if k in res.written:
            note = "（不完整，ep prompts 会继续提示缺图）" if k in res.missing else ""
            typer.echo(f"  拼好  {nm}: {k}_sheet.png ← {len(res.written[k])} 张{note}")
        elif k in res.kept:
            typer.echo(f"  保留  {nm}: {k}_sheet.png 是手工做的，没有覆盖（要覆盖加 --force）")
        elif k in res.skipped:
            typer.echo(f"  跳过  {nm}: 五张没齐，不拼（先拼着看加 --partial）")
        if k in res.missing:
            typer.echo(f"  缺图  {nm}: " + "、".join(res.missing[k]) + "（见 refs/REFS.md 第一步、第二步）")
    typer.echo(f"{len(res.written)} sheets written, {len(res.missing)} people still missing views")


@app.command("facetest")
def facetest_cmd(
    ep_dir: Path,
    keys: str = typer.Option("a,b", "--keys", help="Comma-separated cast keys"),
    n: int = typer.Option(4, "--n", help="Candidates per key in this run"),
    cap_usd: float = typer.Option(3.0, "--cap-usd", help="Hard cap on OpenRouter-reported spend (all facetest runs)"),
    max_images: int = typer.Option(8, "--max-images", help="Hard cap on images made (all facetest runs)"),
    model: str = typer.Option(None, "--model", help="OpenRouter image model (default openai/gpt-image-2.5-sunburst)"),
    quality: str = typer.Option("high", "--quality"),
) -> None:
    """Paid step-1 test: canon art -> photoreal front portrait candidates in refs/candidates/ (needs OPENROUTER_API_KEY)."""
    from aigc_mv.facetest import contact_sheet, face_specs, run_facetest, write_readme
    from aigc_mv.providers.base import SpendGate
    from aigc_mv.providers.openrouter import DEFAULT_MODEL, OpenRouterImage

    ep = load_episode(ep_dir)
    try:
        specs = face_specs(ep_dir, ep, [k.strip() for k in keys.split(",") if k.strip()])
        provider = OpenRouterImage(model=model or DEFAULT_MODEL, quality=quality)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        _fail(str(e))
    gate = SpendGate(ep_dir, ep.budget)
    res = run_facetest(ep_dir, gate, provider, specs, n=n, cap_usd=cap_usd, max_images=max_images, log=typer.echo)
    if any(True for _ in (ep_dir / "refs" / "candidates").glob("*_face_cand_*.png")):
        typer.echo(f"wrote {contact_sheet(ep_dir, specs)}")
    typer.echo(f"wrote {write_readme(ep_dir, gate, specs, provider.model)}")
    typer.echo(f"facetest total: {res.images} images, ${res.spent_usd:.4f} (cap ${cap_usd:.2f} / {max_images} images); "
               f"{len(res.failed)} failed or declined")


@app.command("prompts")
def prompts_cmd(ep_dir: Path, knowledge: Path = typer.Option(None, "--knowledge")) -> None:
    """Audio windows + units/<id>/prompt.txt + request.json for every unit."""
    from aigc_mv.packs import write_packs
    from aigc_mv.timing import load_timing
    from aigc_mv.windows import write_windows

    ep = load_episode(ep_dir)
    timing, b = load_timing(ep_dir), load_board(ep_dir)
    try:
        n = len(write_windows(ep_dir, ep, timing, b))
        typer.echo(f"{n} audio windows")
    except FileNotFoundError as e:
        typer.echo(f"(no audio windows: {e})")
    for s in write_packs(ep_dir, ep, b, timing, knowledge):
        typer.echo(f"{s['unit']} {s['kind']:6s} {s['duration']:2d}s {s['chars']:5d} chars "
                   + ("; ".join(s["warnings"]) if s["warnings"] else "ok"))


@app.command("approve")
def approve_cmd(ep_dir: Path, units: list[str] = typer.Argument(None), all_: bool = typer.Option(False, "--all")) -> None:
    """Record that you READ these prompts; the spend gate refuses anything not approved."""
    from aigc_mv.providers.base import SpendGate

    ep = load_episode(ep_dir)
    gate = SpendGate(ep_dir, ep.budget)
    summ = json.loads((ep_dir / "units" / "summary.json").read_text(encoding="utf-8"))
    chosen = [s for s in summ if all_ or (units and s["unit"] in units)]
    if not chosen:
        _fail("name units (u01 u02 …) or pass --all")
    for s in chosen:
        gate.approve(s["unit"], s["digest"])
        typer.echo(f"approved {s['unit']} ({s['digest']})")


@app.command("sync")
def sync_cmd(ep_dir: Path, unit: str) -> None:
    """Measure every take in units/<unit>/takes/ against its audio window (lag, in-sync spans)."""
    from aigc_mv.board import load_board as lb
    from aigc_mv.sync import load_unit_takes, measure, save_unit_takes, takes_dir

    b = lb(ep_dir)
    u = next((x for x in b.units if x.id == unit), None) or _fail(f"no unit {unit}")
    d = takes_dir(ep_dir, unit)
    clips = sorted(d.glob("*.mp4"))
    if not clips:
        _fail(f"no takes in {d}")
    ut = load_unit_takes(ep_dir, unit)
    ref = ep_dir / "units" / unit / (f"{unit}_vocal.wav" if u.audio == "vocal" else f"{unit}_inst.wav")
    ut.takes = []
    for c in clips:
        if u.kind == "sung" and ref.is_file():
            ts = measure(ref, c)
        else:
            from aigc_mv.sync import TakeSync
            from aigc_mv.tools import media_duration

            ts = TakeSync(take=c.name, copy=False, duration=media_duration(c))
        ut.takes.append(ts)
        typer.echo(f"{c.name}: lag {ts.lag:+.2f}s ncc {ts.ncc:.2f} copy={ts.copy_} synced={ts.synced} "
                   f"diverge={ts.diverge_at}")
    save_unit_takes(ep_dir, ut)


@app.command("pick")
def pick_cmd(ep_dir: Path, unit: str, take: str, notes: str = typer.Option("", "--notes")) -> None:
    """The director's choice of take for a unit (your eyes beat the meter)."""
    from aigc_mv.sync import load_unit_takes, save_unit_takes

    ut = load_unit_takes(ep_dir, unit)
    name = take if take.endswith(".mp4") else f"{take}.mp4"
    if not any(t.take == name for t in ut.takes):
        _fail(f"{name} not measured yet; run: aigc-mv ep sync {ep_dir} {unit}")
    ut.pick, ut.notes = name, notes
    save_unit_takes(ep_dir, ut)
    typer.echo(f"{unit} → {name}")


@app.command("render")
def render_cmd(
    ep_dir: Path,
    res: str = typer.Option("720p", "--res", help="480p | 720p | 1080p | 2k"),
    test: Optional[str] = typer.Option(None, "--test", help="from:to seconds"),
    no_look: bool = typer.Option(False, "--no-look"),
    no_text: bool = typer.Option(False, "--no-text"),
    previz: Optional[bool] = typer.Option(None, "--previz/--no-previz",
                                          help="Placeholder plates for shots without take / plate (default: on for shows)"),
) -> None:
    """Conform the cut (takes > plates > previz > cards), grade, subtitles, music → final/<title>.mp4."""
    from aigc_mv.edit import render
    from aigc_mv.timing import load_timing

    ep = load_episode(ep_dir)
    rng = tuple(float(x) for x in test.split(":")) if test else None
    out = render(ep_dir, ep, load_board(ep_dir), load_timing(ep_dir), resolution=res, test=rng,  # type: ignore[arg-type]
                 look=not no_look, overlays=not no_text, previz=previz)
    edl = json.loads((ep_dir / "edit" / "edl.json").read_text(encoding="utf-8"))
    src = {}
    for e in edl["entries"]:
        src[e["source"]] = src.get(e["source"], 0) + 1
        if e.get("warn"):
            typer.echo(f"  ! {e['shot']}: {e['warn']}")
    typer.echo(f"sources {src} → {out}")


@app.command("previz")
def previz_cmd(ep_dir: Path) -> None:
    """Free previz: audio/previz_beat.wav + edit/previz/sheet_NN.png contact sheets of the placeholder plates."""
    from aigc_mv.previz import contact_sheets, synth_beat
    from aigc_mv.timing import load_timing

    ep = load_episode(ep_dir)
    timing, b = load_timing(ep_dir), load_board(ep_dir)
    typer.echo(f"wrote {synth_beat(timing, ep_dir / 'audio' / 'previz_beat.wav', ep)}")
    for p in contact_sheets(ep, b.shots, ep_dir / "edit" / "previz"):
        typer.echo(f"wrote {p}")
    typer.echo(f"next: aigc-mv ep render {ep_dir} --res 480p --previz")


_ROLE_CN = {"rapper": "选手", "teammate": "队友", "judge": "评委", "host": "主持", "dj": "DJ", "hook": "副歌",
            "cameo": "客串"}


@app.command("status")
def status_cmd(ep_dir: Path) -> None:
    """What exists and what is next."""
    ep = load_episode(ep_dir)
    typer.echo(f"{ep.title} · {ep.format} · {ep.realism} · look {ep.look} · {len(ep.cast)} cast")
    for role, cn in _ROLE_CN.items():
        keys = ep.members(role)
        if keys:
            typer.echo(f"  {cn}: " + "、".join(f"{ep.cast[k].name_cn}({k})" for k in keys))
    checks = [
        ("song", ep_dir / ep.song), ("vocal stem", ep_dir / (ep.vocals or "-")),
        ("timing", ep_dir / "analysis" / "timing.json"), ("board", ep_dir / "board" / "board.json"),
        ("refs plan", ep_dir / "refs" / "REFS.md"), ("prompts", ep_dir / "units" / "summary.json"),
        ("previz beat", ep_dir / "audio" / "previz_beat.wav"),
    ]
    for name, p in checks:
        typer.echo(f"{'✓' if p.exists() else '·'} {name:10s} {p}")
    if (ep_dir / "board" / "board.json").is_file():
        b = load_board(ep_dir)
        done = sum(1 for u in b.units if any((ep_dir / "units" / u.id / "takes").glob("*.mp4")))
        typer.echo(f"takes: {done}/{len(b.units)} units have at least one take")
