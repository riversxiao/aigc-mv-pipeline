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
) -> None:
    """Conform the cut (takes > plates > cards), grade, subtitles, music → final/<title>.mp4."""
    from aigc_mv.edit import render
    from aigc_mv.timing import load_timing

    ep = load_episode(ep_dir)
    rng = tuple(float(x) for x in test.split(":")) if test else None
    out = render(ep_dir, ep, load_board(ep_dir), load_timing(ep_dir), resolution=res, test=rng,  # type: ignore[arg-type]
                 look=not no_look, overlays=not no_text)
    edl = json.loads((ep_dir / "edit" / "edl.json").read_text(encoding="utf-8"))
    src = {}
    for e in edl["entries"]:
        src[e["source"]] = src.get(e["source"], 0) + 1
        if e.get("warn"):
            typer.echo(f"  ! {e['shot']}: {e['warn']}")
    typer.echo(f"sources {src} → {out}")


@app.command("status")
def status_cmd(ep_dir: Path) -> None:
    """What exists and what is next."""
    ep = load_episode(ep_dir)
    checks = [
        ("song", ep_dir / ep.song), ("vocal stem", ep_dir / (ep.vocals or "-")),
        ("timing", ep_dir / "analysis" / "timing.json"), ("board", ep_dir / "board" / "board.json"),
        ("refs plan", ep_dir / "refs" / "REFS.md"), ("prompts", ep_dir / "units" / "summary.json"),
    ]
    for name, p in checks:
        typer.echo(f"{'✓' if p.exists() else '·'} {name:10s} {p}")
    if (ep_dir / "board" / "board.json").is_file():
        b = load_board(ep_dir)
        done = sum(1 for u in b.units if any((ep_dir / "units" / u.id / "takes").glob("*.mp4")))
        typer.echo(f"takes: {done}/{len(b.units)} units have at least one take")
