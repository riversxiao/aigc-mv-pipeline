"""`aigc-mv ep …` – the episode pipeline (battle / MV), stage by stage.

    init → suno → analyze → board → refs → prompts → approve → (generate) → sync / pick → render
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Optional

import typer

from aigc_mv.board import audit, load_board, plan, render_sheet
from aigc_mv.episode import load_episode
from aigc_mv.tools import jsave

app = typer.Typer(help="Episode pipeline: shared series assets, character voices, H3 / Seedance and frame-exact edit", no_args_is_help=True)

_REPO = Path(__file__).resolve().parents[2]
_EXAMPLE = _REPO / "projects" / "xiangyu_vs_liubang"


@app.command("h3-bundle")
def h3_bundle_cmd(
    ep_dir: Path,
    assets: Path = typer.Option(..., "--assets", help="Approved portraits, shot first frames and overrides JSON"),
    template: Path = typer.Option(..., "--template", help="Validated Comfy H3 API workflow JSON"),
    out: Path = typer.Option(..., "--out"),
    shots: str = typer.Option(..., "--shots", help="Explicit comma-separated shot ids"),
    steps: int = typer.Option(12, "--steps", min=1, max=40),
    allow_legacy_audio: bool = typer.Option(False, "--allow-legacy-audio", help="Historical regeneration only; voice identity remains unverified"),
) -> None:
    """Compile independent H3 shot graphs and target audio locally; never starts Colab."""
    from aigc_mv.h3 import export_bundle

    try:
        result = export_bundle(ep_dir, assets, template, out,
                               [x.strip() for x in shots.split(",") if x.strip()], steps,
                               allow_legacy_audio=allow_legacy_audio)
    except (ValueError, KeyError, FileNotFoundError, FileExistsError) as e:
        _fail(str(e))
    typer.echo(f"H3 bundle: {len(result['jobs'])} jobs, {len(result['files'])} verified inputs → {out}")


@app.command("h3-ingest")
def h3_ingest_cmd(ep_dir: Path, bundle: Path, results: Path) -> None:
    """Import H3 shot candidates; visual/identity review stays unreviewed."""
    from aigc_mv.h3 import ingest_shot_results
    data = ingest_shot_results(ep_dir.resolve(), bundle, results)
    typer.echo(f"Imported candidates for {len(data)} shots; visual acceptance is still required")


def _fail(msg: str) -> None:
    typer.echo(f"ERROR: {msg}", err=True)
    raise typer.Exit(code=1)


@app.command("shared-assets")
def shared_assets_cmd(ep_dir: Path, library: Path = typer.Option(..., "--library"),
                      out: Optional[Path] = typer.Option(None, "--out")) -> None:
    """Create a series H3 draft, binding portraits by stable character identity."""
    from aigc_mv.shared_assets import scaffold_shared_assets
    target = out or ep_dir / "h3_assets.json"
    try:
        scaffold_shared_assets(ep_dir, library, target)
    except (OSError, ValueError, KeyError) as exc:
        _fail(str(exc))
    typer.echo(f"Shared asset draft: {target}; finish direction, motion selection, first frames and voice review before production")


@app.command("direct-plan")
def direct_plan_cmd(ep_dir: Path, assets: Path = typer.Option(..., "--assets"),
                    out: Optional[Path] = typer.Option(None, "--out"),
                    shots: Optional[str] = typer.Option(None, "--shots")) -> None:
    """Create and attach a draft shot-performance plan; never starts generation."""
    from aigc_mv.directing import scaffold_direction
    target = out or ep_dir/"direction.json"
    try:
        scaffold_direction(ep_dir, assets, target, [x.strip() for x in shots.split(",")] if shots else None)
        cfg = json.loads(assets.read_text())
        cfg["directing_plan"] = os.path.relpath(target.resolve(), assets.resolve().parent)
        assets.write_text(json.dumps(cfg, ensure_ascii=False, indent=2)+"\n")
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        _fail(str(exc))
    typer.echo(f"Direction draft: {target}; fill stage geometry, performance beats, other actors and motion bindings")


@app.command("direction-check")
def direction_check_cmd(ep_dir: Path, assets: Path = typer.Option(..., "--assets"),
                        shots: Optional[str] = typer.Option(None, "--shots")) -> None:
    """Check the shot plan and external motion index locally, independently of voice casting."""
    from aigc_mv.directing import direction_readiness
    from aigc_mv.shared_assets import load_asset_config
    try:
        cfg, _ = load_asset_config(assets)
        report = direction_readiness(ep_dir.resolve(), assets.resolve(), cfg,
                                    [x.strip() for x in shots.split(",")] if shots else None)
    except (OSError, ValueError, KeyError) as exc:
        _fail(str(exc))
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ready"]:
        raise typer.Exit(1)


@app.command("h3-review")
def h3_review_cmd(ep_dir: Path, shot: str, job_id: str,
                  review: Path = typer.Option(..., "--review")) -> None:
    """Record actual take checks; a keep decision requires every criterion to pass."""
    from aigc_mv.shot_review import record_review
    try:
        result = record_review(ep_dir.resolve(), shot, job_id, review)
    except (OSError, ValueError, KeyError) as exc:
        _fail(str(exc))
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("h3-retake-plan")
def h3_retake_plan_cmd(ep_dir: Path, shot: str, job_id: str,
                       proposal: Path = typer.Option(..., "--proposal"),
                       out: Path = typer.Option(..., "--out")) -> None:
    """Write an evidence-based, one-change retake proposal; submits nothing."""
    from aigc_mv.shot_review import retake_plan
    try:
        result = retake_plan(ep_dir.resolve(), shot, job_id, proposal, out)
    except (OSError, ValueError, KeyError) as exc:
        _fail(str(exc))
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("asset-register")
def asset_register_cmd(library: Path = typer.Option(..., "--library"),
                       asset_id: str = typer.Option(..., "--id"),
                       source: Path = typer.Option(..., "--source"),
                       kind: str = typer.Option(..., "--kind"),
                       characters: str = typer.Option("", "--characters", help="Stable character IDs, comma-separated"),
                       description: str = typer.Option("", "--description"),
                       view: str = typer.Option("", "--view"),
                       positions: str = typer.Option("{}", "--positions", help="JSON mapping stable character IDs to stage sides")) -> None:
    """Register an immutable portrait, scene, composition or voice asset locally."""
    from aigc_mv.shared_assets import register_asset
    try:
        record = register_asset(library, asset_id, source, kind,
                                [x.strip() for x in characters.split(",") if x.strip()],
                                description=description, view=view, positions=json.loads(positions))
    except (OSError, ValueError, KeyError) as exc:
        _fail(str(exc))
    typer.echo(json.dumps({"id": asset_id, **record}, ensure_ascii=False, indent=2))


@app.command("production-check")
def production_check_cmd(ep_dir: Path, assets: Path = typer.Option(..., "--assets")) -> None:
    """Check shared identities, first frames and voice casting locally, without GPU work."""
    from aigc_mv.shared_assets import production_readiness
    try:
        report = production_readiness(ep_dir, assets)
    except (OSError, ValueError, KeyError) as exc:
        _fail(str(exc))
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ready_for_h3_production"]:
        raise typer.Exit(1)


@app.command("asset-pack")
def asset_pack_cmd(library: Path = typer.Option(..., "--library"),
                   out: Path = typer.Option(..., "--out")) -> None:
    """Package a shared library for backup or transfer to another machine."""
    from aigc_mv.shared_assets import pack_library
    try:
        report = pack_library(library, out)
    except (OSError, ValueError, KeyError) as exc:
        _fail(str(exc))
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2))


@app.command("asset-unpack")
def asset_unpack_cmd(archive: Path, out: Path = typer.Option(..., "--out")) -> None:
    """Restore and verify a shared library into a new directory."""
    from aigc_mv.shared_assets import unpack_library
    try:
        catalog = unpack_library(archive, out)
    except (OSError, ValueError, KeyError) as exc:
        _fail(str(exc))
    typer.echo(f"Restored verified library: {catalog}")


@app.command("asset-library-summary")
def asset_library_summary_cmd(
    library: Path = typer.Option(_REPO / "libraries/luotian/catalog.json", "--library"),
    motion_library: Optional[Path] = typer.Option(_REPO / "libraries/motions", "--motion-library"),
) -> None:
    """Inspect unified series visual/audio/character-sheet assets and federated motion libraries."""
    from aigc_mv.motion_assets import MotionLibrary
    from aigc_mv.shared_assets import AssetLibrary
    try:
        lib = AssetLibrary(library)
        report: dict = {"visual_and_character_library": lib.summary()}
        if motion_library and Path(motion_library).exists():
            mlib = MotionLibrary(motion_library)
            report["motion_library"] = mlib.summary()
    except (OSError, ValueError, KeyError) as exc:
        _fail(str(exc))
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2))


@app.command("motion-search")
def motion_search_cmd(
    library: Path = typer.Option(_REPO / "libraries/motions", "--library"),
    category: Optional[str] = typer.Option(None, "--category"),
    pose_format: Optional[str] = typer.Option(None, "--pose-format"),
    hand: Optional[str] = typer.Option(None, "--hand"),
    framing: Optional[str] = typer.Option(None, "--framing"),
    view: Optional[str] = typer.Option(None, "--view"),
    people: Optional[int] = typer.Option(None, "--people"),
    tag: Optional[str] = typer.Option(None, "--tag"),
    character: Optional[str] = typer.Option(None, "--character"),
) -> None:
    """Search federated motion catalogs (battle_rap, instruments, kpop_dance, luotian_combat, etc.)."""
    from aigc_mv.motion_assets import MotionLibrary
    try:
        mlib = MotionLibrary(library)
        matches = mlib.search(
            category=category,
            pose_format=pose_format,
            hand=hand,
            framing=framing,
            view=view,
            people=people,
            tag=tag,
            character=character,
        )
    except (OSError, ValueError, KeyError) as exc:
        _fail(str(exc))
    typer.echo(json.dumps({"count": len(matches), "matches": matches}, ensure_ascii=False, indent=2))


@app.command("voice-review")
def voice_review_cmd(ep_dir: Path, assets: Path = typer.Option(..., "--assets"),
                     approve: bool = typer.Option(False, "--approve"),
                     notes: str = typer.Option("", "--notes")) -> None:
    """Inspect voice bindings, or record completed listening review of the actual mix."""
    from aigc_mv.shared_assets import approve_voices, voice_readiness
    try:
        report = approve_voices(ep_dir, assets, notes) if approve else voice_readiness(ep_dir, assets)
    except (OSError, ValueError, KeyError) as exc:
        _fail(str(exc))
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ready"]:
        raise typer.Exit(1)


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


@app.command("batch")
def batch_cmd(
    ep_dir: Path,
    plates: str = typer.Option("", "--plates", help="Comma-separated plate files (venue.png,...)"),
    step2: str = typer.Option("", "--step2", help="Comma-separated cast keys for step-2 views"),
    views: str = typer.Option("34,profile,half,full", "--views", help="Step-2 views (34,profile,half,full,expr)"),
    step1: str = typer.Option("", "--step1", help="Comma-separated cast keys for step-1 front portraits"),
    n: int = typer.Option(4, "--n", help="Candidates per plate / step-1 portrait in this run"),
    n_step2: int = typer.Option(2, "--n-step2", help="Candidates per step-2 view in this run"),
    cap_usd: float = typer.Option(..., "--cap-usd", help="Hard cap on provider-reported spend (all runs of --tag)"),
    max_images: int = typer.Option(..., "--max-images", help="Hard cap on images made (all runs of --tag)"),
    workers: int = typer.Option(3, "--workers"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print the items and prompts, call nothing"),
    provider: str = typer.Option("openrouter", "--provider", help="openrouter (OPENROUTER_API_KEY) | apimart "
                                 "(APIMART_API_KEY)"),
    tag: str = typer.Option(None, "--tag", help="Ledger tag the caps count (default refs-batch / refs-batch-apimart)"),
    est_usd: float = typer.Option(None, "--est-usd", help="Per-image reservation (default per provider)"),
    model: str = typer.Option(None, "--model"),
    quality: str = typer.Option("high", "--quality"),
    resolution: str = typer.Option("1k", "--resolution", help="apimart only: 1k | 2k | 4k"),
) -> None:
    """Paid reference batch (plates, step-2 views, step-1 portraits) into refs/candidates/ (key from the env)."""
    from aigc_mv import refbatch as rb
    from aigc_mv.providers.base import SpendGate

    if provider == "openrouter":
        from aigc_mv.providers.openrouter import DEFAULT_MODEL, OpenRouterImage

        def make():
            return OpenRouterImage(model=model or DEFAULT_MODEL, quality=quality)
        tag = tag or rb.TAG
        est = est_usd if est_usd is not None else rb.EST_USD
    elif provider == "apimart":
        from aigc_mv.providers import apimart

        def make():
            return apimart.ApiMartImage(model=model or apimart.DEFAULT_MODEL, quality=quality, resolution=resolution)
        tag = tag or rb.TAG + "-apimart"
        est = est_usd if est_usd is not None else apimart.EST_USD
    else:
        _fail(f"unknown provider {provider!r} (openrouter | apimart)")

    def split(s: str) -> list[str]:
        return [x.strip() for x in s.split(",") if x.strip()]

    ep = load_episode(ep_dir)
    try:
        s2 = rb.step2_items(ep_dir, ep, split(step2), split(views))
        for it in s2:
            it.n = n_step2
        items = rb.plate_items(ep_dir, split(plates)) + s2 + rb.step1_items(ep_dir, ep, split(step1))
    except (FileNotFoundError, ValueError) as e:
        _fail(str(e))
    if dry_run:
        for it in items:
            typer.echo(f"{it.file} [{it.aspect}] refs={[p.name for p in it.refs]}\n  {it.prompt}\n")
        return
    try:
        make()
    except RuntimeError as e:
        _fail(str(e))
    gate = SpendGate(ep_dir, ep.budget)
    res = rb.run_batch(ep_dir, gate, make, items, n=n, cap_usd=cap_usd, max_images=max_images, est_usd=est,
                       workers=workers, log=typer.echo, tag=tag)
    typer.echo(f"batch total ({tag}): {res.images} images, ${res.spent_usd:.4f} (cap ${cap_usd:.2f} / "
               f"{max_images} images); this run {len(res.made)} made, {len(res.failed)} failed or declined"
               + (f"; stopped: {res.stopped}" if res.stopped else ""))


@app.command("lock")
def lock_cmd(
    ep_dir: Path, file: str, cand: int, reason: str = typer.Option(..., "--reason"),
    by: str = typer.Option("agent", "--by", help="agent | user"), force: bool = typer.Option(False, "--force"),
) -> None:
    """Copy refs/candidates/<stem>_cand_<n>.png to refs/<file> and record the pick in picks.json."""
    from aigc_mv.refbatch import lock

    try:
        typer.echo(f"locked {lock(ep_dir, file, cand, reason, by=by, force=force)}")
    except (FileNotFoundError, FileExistsError) as e:
        _fail(str(e))


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
    from aigc_mv.sync import sync_unit, takes_dir

    b = lb(ep_dir)
    u = next((x for x in b.units if x.id == unit), None) or _fail(f"no unit {unit}")
    d = takes_dir(ep_dir, unit)
    if not any(d.glob("*.mp4")):
        _fail(f"no takes in {d}")
    for ts in sync_unit(ep_dir, u).takes:
        _echo_sync(ts)


def _echo_sync(ts, prefix: str = "") -> None:
    typer.echo(f"{prefix}{ts.take}: lag {ts.lag:+.2f}s ncc {ts.ncc:.2f} copy={ts.copy_} synced={ts.synced} "
               f"diverge={ts.diverge_at} dur {ts.duration:.2f}s")


def _auto_pick_all(ep_dir: Path, board, units: Optional[list[str]], force: bool) -> None:
    from aigc_mv.sync import auto_pick

    for u in board.units:
        if units is not None and u.id not in units:
            continue
        ut, what = auto_pick(ep_dir, u, force=force)
        if what == "picked":
            typer.echo(f"  {u.id} → {ut.pick}（自动）")
        elif what == "kept":
            typer.echo(f"  {u.id} → {ut.pick}（保留你手动选的，--force 可改为自动）")


@app.command("pick")
def pick_cmd(
    ep_dir: Path,
    unit: Optional[str] = typer.Argument(None),
    take: Optional[str] = typer.Argument(None),
    notes: str = typer.Option("", "--notes"),
    auto: bool = typer.Option(False, "--auto", help="Pick the best measured take of every unit (or of UNIT)"),
    force: bool = typer.Option(False, "--force", help="With --auto: also replace picks you made by hand"),
) -> None:
    """The director's choice of take for a unit (your eyes beat the meter); --auto picks by the sync meter."""
    from aigc_mv.sync import load_unit_takes, save_unit_takes

    if auto:
        _auto_pick_all(ep_dir, load_board(ep_dir), [unit] if unit else None, force)
        return
    if not unit or not take:
        _fail("usage: aigc-mv ep pick <ep> <unit> <take>  or  aigc-mv ep pick <ep> --auto")
    ut = load_unit_takes(ep_dir, unit)
    name = take if take.endswith(".mp4") else f"{take}.mp4"
    if not any(t.take == name for t in ut.takes):
        _fail(f"{name} not measured yet; run: aigc-mv ep sync {ep_dir} {unit}")
    ut.pick, ut.notes, ut.auto = name, notes, False
    save_unit_takes(ep_dir, ut)
    typer.echo(f"{unit} → {name}")


def _echo_retakes(r: dict) -> None:
    from aigc_mv.ingest import REASON_CN

    if r["retake"]:
        typer.echo(f"需要重拍 {len(r['retake'])} 个单元：")
        groups: dict[str, list[str]] = {}
        for x in r["retake"]:
            groups.setdefault("、".join(REASON_CN.get(k, k) for k in x["reasons"]), []).append(x["unit"])
        for why, ids in groups.items():
            typer.echo(f"  {why}：{' '.join(ids)}")
        typer.echo(f"重拍包：{r['command']}")
    else:
        typer.echo("没有需要重拍的单元")
    if r["by_eye"]:
        typer.echo("口型靠肉眼检查：" + " ".join(f"{x['unit']}/{x['take']}" for x in r["by_eye"]))
    if r["manual_download"]:
        typer.echo("请到网页画布手动下载：" + " ".join(x["unit"] for x in r["manual_download"]))


@app.command("retakes")
def retakes_cmd(ep_dir: Path) -> None:
    """Write units/retakes.json + units/retakes.md (no take, lips not verified, too short) and the bundle command."""
    from aigc_mv.ingest import retakes

    r = retakes(ep_dir, load_board(ep_dir), ep_arg=str(ep_dir))
    _echo_retakes(r)
    typer.echo(f"清单：{ep_dir / 'units' / 'retakes.md'}")


@app.command("ingest-takes")
def ingest_takes_cmd(
    ep_dir: Path,
    src: Path = typer.Argument(..., help="Folder or zip from run_dreamina.py (takes/<unit>/take-N.mp4, results.json)"),
    force: bool = typer.Option(False, "--force", help="Auto pick also replaces picks you made by hand"),
) -> None:
    """Import Dreamina takes: copy into units/<id>/takes/ (never overwrite), ep sync, auto pick, retake list."""
    from aigc_mv.ingest import ingest, retakes
    from aigc_mv.sync import sync_unit

    b = load_board(ep_dir)
    try:
        rep = ingest(ep_dir, src, b)
    except (FileNotFoundError, ValueError) as e:
        _fail(str(e))
    cn = {"new": "新增", "same": "已有相同文件，跳过", "renamed": "同名但内容不同，另存", "invalid": "不是 mp4，跳过"}
    n_new = 0
    for unit, rows in sorted(rep["units"].items()):
        for x in rows:
            n_new += x["state"] in ("new", "renamed")
            typer.echo(f"  {unit}/{x['take']} → units/{unit}/takes/{x['file']}：{cn[x['state']]}")
    for o in rep["unknown"]:
        typer.echo(f"  ! 不认识的单元，跳过：{o}")
    for unit, st in sorted(rep["status"].items()):
        typer.echo(f"  ! {unit}/{st['take']}：没有文件（状态 {st.get('status', '?')}）")
    typer.echo(f"导入 {n_new} 条新成片，{len(rep['units'])} 个单元，results.json {rep['results']} 行")
    units = {u.id: u for u in b.units}
    touched = [u for u in sorted(rep["units"]) if any(x["state"] != "invalid" for x in rep["units"][u])]
    typer.echo("口型对齐测量：")
    for uid in touched:
        for ts in sync_unit(ep_dir, units[uid]).takes:
            _echo_sync(ts, prefix=f"  {uid}/")
    typer.echo("自动挑选：")
    _auto_pick_all(ep_dir, b, touched, force)
    _echo_retakes(retakes(ep_dir, b, ep_arg=str(ep_dir)))
    typer.echo(f"清单：{ep_dir / 'units' / 'retakes.md'}")
    typer.echo(f"下一步：aigc-mv ep render {ep_dir} --res 1080p")


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


@app.command("dreamina-bundle")
def dreamina_bundle_cmd(
    ep_dir: Path,
    out: Optional[Path] = typer.Option(None, "--out", help="Bundle folder (default <ep>/dreamina_bundle)"),
    units: str = typer.Option("", "--units", help="Only these units, comma separated (retakes)"),
    take: int = typer.Option(1, "--take", help="Take number the runner generates (1; 2, 3 … for retakes)"),
    zip_: bool = typer.Option(True, "--zip/--no-zip", help="Also write <out>.zip when the bundle is < 95 MB"),
) -> None:
    """Self-contained Dreamina video bundle (run_dreamina.py + units + refs + Chinese README) for a logged-in Mac."""
    from aigc_mv.dreamina_bundle import build_bundle

    dst = out or ep_dir / "dreamina_bundle"
    want = [u.strip() for u in units.split(",") if u.strip()] or None
    try:
        r = build_bundle(ep_dir, dst, units=want, take=take, make_zip=zip_)
    except (FileNotFoundError, FileExistsError, ValueError) as e:
        _fail(str(e))
    typer.echo(f"{len(r['units'])} units ({r['seconds']} s), {r['images']} images, {r['files']} files, "
               f"{r['bytes'] / 1e6:.1f} MB → {r['out']}")
    typer.echo(f"zip: {r['zip']}" if r["zip"] else "zip: none (bundle >= 95 MB or --no-zip)")
    typer.echo(f"on the logged-in Mac: cd {Path(r['out']).name} && python3 run_dreamina.py")


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
