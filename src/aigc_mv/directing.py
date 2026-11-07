"""Shot performance planning and reference-role checks adapted for our H3 pipeline.

Inspired by Emily2040/seedance-2.0's shot table and reference transfer contract;
see docs/UPSTREAM_Seedance.md. Structural checks do not judge acting quality.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from aigc_mv.board import load_board
from aigc_mv.episode import load_episode
from aigc_mv.motion_assets import MotionLibrary
from aigc_mv.shared_assets import file_hash, fingerprint, load_asset_config

REVIEW_CRITERIA = ["identity", "performance", "hands_props", "lip_sync", "continuity"]
REFERENCE_ROLES = {"portraits": "identity_costume", "first_frame": "composition_stage_light",
                   "motion": "body_only", "audio": "target_guide_timing", "camera": "shot_plan"}


def scaffold_direction(ep_dir: Path, assets: Path, output: Path,
                       shots: list[str] | None = None) -> dict:
    if output.exists():
        raise FileExistsError(output)
    ep = load_episode(ep_dir)
    board = load_board(ep_dir)
    cfg, _ = load_asset_config(assets)
    selected = [board.shot(sid) for sid in shots] if shots else board.shots
    plan = {"schema_version": 1, "episode_sha256": file_hash(ep_dir/"episode.yaml"),
            "board_sha256": file_hash(ep_dir/"board/board.json"),
            "reference_roles": REFERENCE_ROLES, "floor_plan": "", "shots": {}}
    for shot in selected:
        override = cfg.get("shot_overrides", {}).get(shot.id, {})
        visible = override.get("visible_cast", list(dict.fromkeys(shot.who+shot.background)))
        primary = shot.singer if shot.sung else (shot.who[0] if shot.who else None)
        ids = [ep.cast[k].character for k in visible]
        subject = ep.cast[primary].character if primary in visible else None
        plan["shots"][shot.id] = {"status": "draft", "primary": subject,
            "framing": override.get("framing", shot.framing if cfg.get("mode")=="production" else "MCU"),
            "camera": override.get("camera", shot.camera) if cfg.get("mode")=="production" else "locked",
            "camera_side": "", "light": "", "view": "front",
            "blocking": {cid: {"position": "", "facing": "", "eyeline": ""} for cid in ids},
            "emotion": "", "primary_action": "", "ending": "",
            "beats": {"prepare": "", "accent": "", "settle": ""},
            "others": {cid: "" for cid in ids if cid != subject},
            "microphone": {"mode": "handheld" if shot.sung else "none", "hand": "right" if shot.sung else "none", "position": ""},
            "motion": {"required": bool(shot.sung), "asset_id": None, "fit": "retime", "start": 0, "end": None}}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan, ensure_ascii=False, indent=2)+"\n")
    return plan


def direction_readiness(ep_dir: Path, assets: Path, cfg: dict,
                        shots: list[str] | None = None) -> dict:
    """Return local planning failures; pending libraries are explicit, never guessed."""
    errors, rows = [], {}
    reference = cfg.get("directing_plan")
    if not reference:
        return {"ready": cfg.get("schema_version", 3) < 4, "shots": {},
                "errors": ["directing_plan is required for schema_version 4"] if cfg.get("schema_version", 3)>=4 else [],
                "gpu_started": False}
    try:
        ep, board = load_episode(ep_dir), load_board(ep_dir)
        path = (assets.parent/reference).resolve()
        plan = json.loads(path.read_text())
        if plan.get("schema_version") != 1 or plan.get("reference_roles") != REFERENCE_ROLES:
            raise ValueError("Use direction schema 1 and the explicit reference role separation")
        if plan.get("episode_sha256") != file_hash(ep_dir/"episode.yaml") or plan.get("board_sha256") != file_hash(ep_dir/"board/board.json"):
            raise ValueError("Direction plan is stale: episode or storyboard changed")
        if not isinstance(plan.get("floor_plan"), str) or not plan["floor_plan"].strip():
            errors.append("direction.floor_plan: describe stage landmarks and the camera axis")
        selected = [board.shot(sid) for sid in shots] if shots is not None else board.shots
        library = None
        for shot in selected:
            before = len(errors)
            row = plan.get("shots", {}).get(shot.id, {})
            if not isinstance(row, dict):
                errors.append(f"direction.{shot.id}: plan row must be an object")
                continue
            override = cfg.get("shot_overrides", {}).get(shot.id, {})
            visible = override.get("visible_cast", list(dict.fromkeys(shot.who+shot.background)))
            ids = [ep.cast[k].character for k in visible]
            def issue(text):
                errors.append(f"direction.{shot.id}: {text}")
            if row.get("status") != "ready":
                issue("performance plan is still draft")
            for field in ("camera_side", "light", "emotion", "primary_action", "ending"):
                if not isinstance(row.get(field), str) or not row[field].strip():
                    issue(f"{field} is missing")
            expected_framing = override.get("framing", shot.framing if cfg.get("mode")=="production" else "MCU")
            expected_camera = override.get("camera", shot.camera) if cfg.get("mode")=="production" else "locked"
            if row.get("framing") != expected_framing or row.get("camera") != expected_camera:
                issue("camera or framing differs from the executable shot")
            if set(row.get("blocking", {})) != set(ids):
                issue("blocking must match visible stable character IDs")
            for cid, block in row.get("blocking", {}).items():
                if not isinstance(block, dict) or any(not isinstance(block.get(k),str) or not block[k].strip() for k in ("position","facing","eyeline")):
                    issue(f"{cid}: position, facing and eyeline are required")
            primary = row.get("primary")
            if primary not in ids and (ids or primary is not None):
                issue("primary must be a visible stable character ID")
            if shot.sung and primary != ep.cast[shot.singer].character:
                issue("the primary performer must be the visible singer")
            if set(row.get("others", {})) != set(ids)-{primary} or any(not isinstance(v,str) or not v.strip() for v in row.get("others", {}).values()):
                issue("give each other visible character one quiet idle action")
            if any(not isinstance(row.get("beats",{}).get(k),str) or not row["beats"][k].strip() for k in ("prepare","accent","settle")):
                issue("prepare, accent and settle beats are required")
            microphone = row.get("microphone", {})
            hand = microphone.get("hand")
            mic_mode = microphone.get("mode", "handheld" if shot.sung else "none")
            if mic_mode not in ("handheld", "lavalier", "headset", "none"):
                issue("specify a supported microphone mode")
            if hand not in ("left", "right", "none") or (shot.sung and mic_mode == "handheld" and hand == "none"):
                issue("specify the performer's microphone hand")
            if mic_mode in ("lavalier", "headset") and hand != "none":
                issue("a wearable microphone leaves both hands free; use hand=none")
            if shot.sung and mic_mode == "none":
                issue("a sung shot needs a handheld or wearable microphone")
            if shot.sung and not row.get("microphone",{}).get("position", "").strip():
                issue("specify a microphone position that leaves the lips visible")
            motion = row.get("motion", {})
            prepared = None
            if motion.get("required") or motion.get("asset_id"):
                try:
                    if not motion.get("asset_id") or not cfg.get("motion_library"):
                        raise ValueError("motion selection/library is pending; bind the external skeleton index")
                    if primary is None:
                        raise ValueError("A body reference needs a visible primary performer")
                    if library is None:
                        library = MotionLibrary(assets.parent/cfg["motion_library"])
                    people = int(motion.get("people", 1))
                    allow_free_hands = bool(motion.get("allow_free_hands", False)) or (not shot.sung and hand == "none")
                    prepared = library.resolve(
                        motion["asset_id"],
                        hand=hand,
                        framing=expected_framing,
                        view=row.get("view"),
                        people=people,
                        allow_free_hands=allow_free_hands,
                    )
                    if motion.get("fit") not in ("retime", "trim_hold"):
                        raise ValueError("Specify motion fit=retime or trim_hold")
                    start, end = motion.get("start",0), motion.get("end")
                    if isinstance(start,bool) or not isinstance(start,(int,float)) or not math.isfinite(start) or start < 0:
                        raise ValueError("Motion start must be a finite nonnegative number")
                    stop = prepared["media"]["duration"] if end is None else end
                    if isinstance(stop,bool) or not isinstance(stop,(int,float)) or not math.isfinite(stop) or not start < stop <= prepared["media"]["duration"]+0.002 or stop-start > 15:
                        raise ValueError("Select an available motion interval of at most 15 seconds")
                except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
                    issue(str(exc))
            if len(errors) == before:
                rows[shot.id] = {"plan": row, "motion": prepared, "floor_plan":plan["floor_plan"],
                    "fingerprint": fingerprint({"floor_plan":plan["floor_plan"],"roles":REFERENCE_ROLES,
                        "shot":row,"motion":{k:v for k,v in prepared.items() if k not in ("source","library")} if prepared else None})}
    except (OSError, ValueError, KeyError, StopIteration, TypeError, AttributeError) as exc:
        errors.append(f"direction: {exc}")
    return {"ready": not errors, "errors": errors, "shots": rows, "gpu_started": False}


def render_direction(row: dict, labels: dict[str, str]) -> str:
    """Compile director fields into H3 English prose without overriding audio timing."""
    if not labels and row.get("primary") is None:
        beats = row["beats"]
        return (f"Camera side: {row['camera_side']}. Lighting: {row['light']}. "
                f"Atmosphere: {row['emotion']}. Primary action: {row['primary_action']}. "
                f"Prepare: {beats['prepare']}. Accent: {beats['accent']}. "
                f"Settle: {beats['settle']}. End within this framing on {row['ending']}. "
                "The scene reference and first frame control architectural geometry, materials and lighting; "
                "the shot plan controls camera. The central performance stage stays completely uninhabited.")
    name = labels.get(row["primary"], "the environment")
    blocking = " ".join(f"{labels[cid]} stays {b['position']}, faces {b['facing']}, and looks {b['eyeline']}."
                        for cid,b in row["blocking"].items())
    others = " ".join(f"{labels[cid]}: {action}; keep the mouth closed." for cid,action in row["others"].items())
    beats = row["beats"]
    mic = row["microphone"]
    mic_mode = mic.get("mode", "handheld")
    if mic_mode in ("lavalier", "headset"):
        props = f"{name} wears a discreet {mic_mode} microphone, {mic['position']}; both hands remain free."
    else:
        props = f"{name} retains the microphone in the {mic['hand']} hand, {mic['position']}." if mic["hand"]!="none" else ""
    return (f"Camera side: {row['camera_side']}. Lighting: {row['light']}. {blocking} "
            f"{name} feels {row['emotion']}. Primary action: {row['primary_action']}. "
            f"Prepare: {beats['prepare']}. At the lyric accent: {beats['accent']}. "
            f"Settle: {beats['settle']}. End within this framing on {row['ending']}. {props} {others} "
            "Portraits control identity and costume; the first frame controls stage and composition; "
            "the shot plan controls camera. The target guide is the sole vocal clock. "
            "A skeleton reference controls body motion only, with no source face, outfit, background, voice or camera transfer.")
