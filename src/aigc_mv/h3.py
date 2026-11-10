"""Export independent, audio-guided H3 shot jobs without changing the song timeline.

Compilation is local. Missing approved cast/frames fail before any GPU work. A bundle
contains its graphs, hashed inputs and a stdlib-only Comfy runner; it never carries
credentials. Visual acceptance is separate from soundtrack similarity.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import shutil
from pathlib import Path

import numpy as np
import soundfile as sf

from aigc_mv.board import load_board
from aigc_mv.cinema import FRAMINGS, LENSES, MOVES
from aigc_mv.episode import load_episode
from aigc_mv.timing import load_timing
from aigc_mv.tools import ffmpeg_exe, han
from aigc_mv.shared_assets import (character_id, file_hash, load_asset_config,
                                  portrait_reference, production_readiness, resolve_reference)
from aigc_mv.directing import REVIEW_CRITERIA, direction_readiness, render_direction
from aigc_mv.motion_assets import prepare_motion


DEFAULT_STEPS = 12
LORA_NODES = ("2", "3")  # template LoRA loaders; strength 0 unless the model profile says otherwise
TAKE_SEED_STRIDE = 100_000  # take N of a shot never collides with another shot's seed
MAX_TAKE = 99


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def render_profile(cfg: dict, template_file: Path, steps: int | None = None) -> dict:
    """Sampler settings every job of an episode shares, so shots differ only by their own inputs.

    ``model_profile.template_sha256`` pins the validated Comfy workflow (required for schema 4
    production); ``model_profile.steps`` fixes the step count, and ``model_profile.lora_strengths``
    sets the template LoRA loaders (default 0.0, the previous fixed behaviour).
    """
    profile = cfg.get("model_profile") or {}
    if not isinstance(profile, dict):
        raise ValueError("model_profile must be a JSON object")
    actual = sha256(template_file)
    pinned = profile.get("template_sha256")
    if pinned and pinned != actual:
        raise ValueError(f"Workflow template {Path(template_file).name} (sha256 {actual[:12]}) is not the "
                         f"model_profile template ({str(pinned)[:12]}); use the pinned file, or pin the new "
                         "workflow in model_profile after validating it")
    if not pinned and cfg.get("mode") == "production" and cfg.get("schema_version", 2) >= 4:
        raise ValueError("Production needs model_profile.template_sha256 pinned to the validated workflow; "
                         f"this template is {actual}")
    fixed = profile.get("steps")
    if fixed is not None:
        if steps is not None and steps != fixed:
            raise ValueError(f"model_profile fixes steps={fixed}; --steps {steps} would change the look between shots")
        steps = fixed
    steps = DEFAULT_STEPS if steps is None else steps
    if isinstance(steps, bool) or not isinstance(steps, int) or not 1 <= steps <= 40:
        raise ValueError("steps must be an integer from 1 to 40")
    loras = {k: 0.0 for k in LORA_NODES}
    raw = profile.get("lora_strengths") or {}
    if not isinstance(raw, dict):
        raise ValueError("model_profile.lora_strengths must map template node ids to strengths")
    for node, value in raw.items():
        if node not in LORA_NODES or isinstance(value, bool) or not isinstance(value, (int, float)) \
                or not math.isfinite(value) or not 0 <= value <= 2:
            raise ValueError(f"model_profile.lora_strengths: node {node!r} must be one of {LORA_NODES} "
                             "with a strength from 0 to 2")
        loras[node] = float(value)
    return {"template_sha256": actual, "steps": steps, "lora_strengths": loras}


def shot_seed(cfg: dict, shot_id: str, take: int = 1) -> int:
    """Deterministic per shot and take: rerunning take N reproduces it; take N+1 is a recorded re-roll."""
    if isinstance(take, bool) or not isinstance(take, int) or not 1 <= take <= MAX_TAKE:
        raise ValueError(f"take must be an integer from 1 to {MAX_TAKE}")
    return int(cfg.get("seed_base", 2026110500)) + int(shot_id.lstrip("s")) + (take - 1) * TAKE_SEED_STRIDE


def frame_count(seconds: float, minimum: int = 90) -> int:
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("Shot duration must be positive and finite")
    n = max(minimum, math.ceil(seconds * 24 - 1e-8))
    n += (5 - n) % 17
    if n > 362:
        raise ValueError("Shot exceeds 362 frames; split it at an authored edit")
    return n


def audio_window(source: Path, target: Path, start: float, end: float,
                 lead: float, frames: int, gate_ranges: list[tuple[float, float]] | None = None) -> dict:
    """Keep source samples on their original clock; resample, never tempo-stretch."""
    import subprocess

    if start < 0 or end <= start or lead < 0:
        raise ValueError("Invalid audio window")
    with sf.SoundFile(source) as f:
        sr = f.samplerate
        i0, i1 = round(start * sr), round(end * sr)
        if i1 > len(f):
            raise ValueError("Audio window extends past the source")
        f.seek(i0)
        samples = f.read(i1 - i0, dtype="float32", always_2d=True)
    if gate_ranges is not None:
        mask = np.zeros(len(samples), dtype=np.float32)
        for a, b in gate_ranges:
            lo, hi = max(0, round(a * sr) - i0), min(len(samples), round(b * sr) - i0)
            if hi <= lo:
                continue
            mask[lo:hi] = 1
            fade = min(round(.002 * sr), (hi - lo) // 2)
            if fade:
                mask[lo:lo + fade] = np.linspace(0, 1, fade)
                mask[hi - fade:hi] = np.linspace(1, 0, fade)
        samples *= mask[:, None]
    if lead + len(samples) / sr > frames / 24 + 1e-5:
        raise ValueError("The frame budget would truncate the source audio")
    padded = np.concatenate([np.zeros((round(lead * sr), samples.shape[1])), samples])
    tail = round(frames / 24 * sr) - len(padded)
    padded = np.pad(padded, ((0, tail), (0, 0)))
    intermediate = target.with_suffix(".source.wav")
    sf.write(intermediate, padded, sr, subtype="PCM_16")
    try:
        subprocess.run([ffmpeg_exe(), "-v", "error", "-y", "-i", str(intermediate),
                        "-ar", "32000", "-ac", "2", "-c:a", "pcm_s16le", str(target)], check=True)
    finally:
        intermediate.unlink(missing_ok=True)
    return {"source_t0": start, "source_t1": end, "lead_silence": lead,
            "sample_rate": 32000, "channels": 2, "duration": frames / 24,
            "target_vocal_ranges": gate_ranges}


def graph_for(template: dict, job: dict) -> dict:
    ids = ["1", "2", "3", "4", "5", "6", "7", "8", "20", "21", "22", "23",
           "24", "25", "26", "27", "30", "31", "32", "34", "35"]
    graph = {k: copy.deepcopy(template[k]) for k in ids}
    for k in LORA_NODES:
        graph[k]["inputs"]["strength_model"] = job.get("lora_strengths", {}).get(k, 0.0)
    r2v = graph["20"]["inputs"]
    for key in list(r2v):
        if key.startswith(("ref_images.", "ref_audios.", "ref_videos.")):
            del r2v[key]
    for i, ref in enumerate(job["portraits"]):
        nid = str(100 + i)
        graph[nid] = {"class_type": "LoadImage", "inputs": {"image": ref}}
        r2v[f"ref_images.ref_image_{i}"] = [nid, 0]
    if job.get("scene_reference"):
        graph["200"] = {"class_type": "LoadImage", "inputs": {"image": job["scene_reference"]}}
        r2v[f"ref_images.ref_image_{len(job['portraits'])}"] = ["200", 0]
    r2v.update(width=1344, height=768, length=job["frames"],
               ref_image_size="match", prompt=job["prompt"])
    graph["10"] = {"class_type": "LoadImage", "inputs": {"image": job["keyframe"]}}
    graph["12"] = {"class_type": "LoadAudio", "inputs": {"audio": job["audio"]}}
    graph["36"] = {"class_type": "MiniMaxH3AddGuide", "inputs": {
        "positive": ["21", 0], "latent": ["20", 1], "vae": ["7", 0],
        "audio_vae": ["8", 0], "image": ["10", 0], "audio": ["12", 0], "frame_idx": 0}}
    graph["26"]["inputs"]["conditioning"] = ["36", 0]
    if job.get("lock_guide_audio"):
        graph["39"] = {"class_type": "H3LockGuideAudio", "inputs": {
            "latent": ["20", 1], "audio_vae": ["8", 0], "audio": ["12", 0]}}
        graph["27"]["inputs"]["latent_image"] = ["39", 0]
        graph["36"]["inputs"]["latent"] = ["39", 0]
    graph["21"]["inputs"]["alpha"] = 0.10
    graph["22"]["inputs"]["steps"] = job["steps"]
    graph["25"]["inputs"]["noise_seed"] = job["seed"]
    graph["34"]["inputs"] = {"images": ["31", 0], "audio": ["32", 0], "fps": 24.0}
    graph["35"]["inputs"]["filename_prefix"] = job["output_prefix"]
    graph["37"] = {"class_type": "H3SaveAVLatent", "inputs": {
        "latent": ["27", 0], "checkpoint_name": job["checkpoint_name"]}}
    # Decoding must depend on the checkpoint, so a decoder failure cannot discard
    # an already sampled AV latent merely because parallel output nodes run later.
    graph["30"]["inputs"]["av_latent"] = ["37", 0]
    if job.get("motion_video"):
        from aigc_mv.h3_motion import reference_graph
        graph = reference_graph(graph, job["motion_video"])
    validate_graph(graph)
    return graph


def validate_graph(graph: dict) -> None:
    for nid, node in graph.items():
        for value in node.get("inputs", {}).values():
            if isinstance(value, list) and len(value) == 2 and isinstance(value[0], str):
                if value[0] not in graph:
                    raise ValueError(f"Dangling graph edge {nid} -> {value[0]}")
    if graph["20"]["inputs"]["length"] % 17 != 5:
        raise ValueError("Invalid H3 frame count")
    if any("MotionContext" in n["class_type"] for n in graph.values()):
        raise ValueError("An independent camera shot cannot inherit previous AV context")
    guide = graph["36"]["inputs"]
    if "audio" not in guide or guide["frame_idx"] != 0:
        raise ValueError("Target audio must be time-anchored at frame zero")


def export_bundle(ep_dir: Path, assets_file: Path, template_file: Path,
                  out: Path, shots: list[str], steps: int | None = None, *, take: int = 1,
                  allow_legacy_audio: bool = False) -> dict:
    if not shots or len(shots) != len(set(shots)):
        raise ValueError("Select unique shot ids explicitly")
    shot_seed({}, "s1", take)  # validate the take number before any work
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite bundle {out}")
    ep_dir, assets_file = Path(ep_dir).resolve(), Path(assets_file).resolve()
    ep = load_episode(ep_dir)
    cfg, library = load_asset_config(assets_file)
    mode = cfg.get("mode", "pilot")
    if mode not in ("pilot", "production"):
        raise ValueError("H3 mode must be pilot or production")
    if mode == "production" and cfg.get("schema_version", 2) < 3 and not allow_legacy_audio:
        raise ValueError("Legacy production audio has no character voice review; migrate with ep shared-assets. "
                         "Historical regeneration only: explicitly allow legacy audio.")
    directions = {"shots": {}}
    if cfg.get("schema_version", 2) >= 3 and mode == "production":
        readiness = production_readiness(ep_dir, assets_file, shots)
        if not readiness["ready_for_h3_production"]:
            raise ValueError("Series production preflight failed:\n" + "\n".join(readiness["errors"]))
        directions = readiness["direction"]
    elif cfg.get("directing_plan"):
        directions = direction_readiness(ep_dir, assets_file, cfg, shots)
        if not directions["ready"]:
            raise ValueError("Direction preflight failed:\n" + "\n".join(directions["errors"]))
    board, timing = load_board(ep_dir), load_timing(ep_dir)
    profile = render_profile(cfg, template_file, steps)
    steps = profile["steps"]
    template = json.loads(Path(template_file).read_text())
    asset_root = assets_file.parent

    def approved_path(rel: str) -> Path:
        return resolve_reference(rel, asset_root, library)

    prepared = []
    for sid in shots:
        s = board.shot(sid)
        override = cfg.get("shot_overrides", {}).get(sid, {})
        visible = override.get("visible_cast", list(dict.fromkeys(s.who + s.background)))
        if s.sung and s.singer not in visible:
            raise ValueError(f"{sid}: visible singer is missing")
        if len(visible) != len(set(visible)) or any(k not in ep.cast for k in visible):
            raise ValueError(f"{sid}: invalid visible cast")
        if not visible and not cfg.get("scene_reference"):
            raise ValueError(f"{sid}: an environment shot needs an approved scene reference")
        portrait_refs = [portrait_reference(cfg, override, k) for k in visible]
        if library:
            for key, reference in zip(visible, portrait_refs):
                if reference.startswith("asset:"):
                    library.check_cast(reference, [character_id(ep.cast[key], key)], kind="portrait")
            reference = cfg["keyframes"][sid]
            if reference.startswith("asset:"):
                library.check_cast(reference, [character_id(ep.cast[k], k) for k in visible],
                                   positions={character_id(ep.cast[k], k): ep.cast[k].side for k in visible})
        portraits = [approved_path(ref) for ref in portrait_refs]
        keyframe = approved_path(cfg["keyframes"][sid])
        # The edit may cut a few frames before the last phoneme. Preserve that small
        # tail for generation while keeping the authored edit duration unchanged.
        end = s.t1
        for i in s.lines:
            line_end = timing.lines[i].t1
            if 0 < line_end - end <= 0.20:
                end = line_end
        lead = cfg.get("lead_frames", 7.2) / 24
        tail = 0.25
        if not math.isfinite(lead) or lead < 0:
            raise ValueError("Invalid guide lead")
        frames = frame_count(end - s.t0 + lead + tail)
        source_rel = ep.vocals if s.sung else ep.instrumental or ep.song
        if s.sung:
            voice = cfg.get("audio_cast", {}).get("voices", {}).get(character_id(ep.cast[s.singer], s.singer), {})
            source_rel = voice.get("vocals") or source_rel
        if not source_rel:
            raise ValueError(f"{sid}: no target vocal stem configured")
        source = ep_dir / source_rel
        if not source.is_file():
            raise FileNotFoundError(source)
        prepared.append((s, override, visible, portraits, keyframe, source, end, frames, lead))

    (out / "input").mkdir(parents=True)
    (out / "workflows").mkdir()
    files, jobs = {}, []

    def put(path: Path) -> str:
        digest = sha256(path)
        name = f"{digest[:16]}_{path.name}"
        dst = out / "input" / name
        if not dst.exists():
            shutil.copy2(path, dst)
        files["input/" + name] = digest
        return name

    for index, (s, override, visible, portraits, kf, source, end, frames, lead) in enumerate(prepared):
        refs, keyframe = [put(p) for p in portraits], put(kf)
        scene_reference = put(approved_path(override.get("scene_reference", cfg["scene_reference"]))) if not visible else None
        audio = f"{s.id}_guide.wav"
        gates = [(timing.lines[i].t0 - .02, timing.lines[i].t1 + .02) for i in s.lines] if s.sung else None
        audio_meta = audio_window(source, out / "input" / audio, s.t0, end, lead, frames, gates)
        files["input/" + audio] = sha256(out / "input" / audio)
        direction = directions["shots"].get(s.id)
        motion_video, motion_metadata = None, None
        if direction and direction["motion"]:
            selected_motion = direction["motion"]
            motion_video = s.id + "_motion.mp4"
            binding = direction["plan"]["motion"]
            motion_metadata = prepare_motion(Path(selected_motion["source"]), out/"input"/motion_video,
                expected_sha256=selected_motion["sha256"], frames=frames,
                lead_frames=round(lead*24), active_frames=math.ceil((end-s.t0)*24-1e-8),
                fit=binding["fit"], start=binding.get("start",0), end=binding.get("end"))
            motion_metadata["asset_id"] = selected_motion["asset_id"]
            files["input/"+motion_video] = motion_metadata["prepared_sha256"]
        definitions = []
        for i, key in enumerate(visible):
            description = cfg["cast"][key]["description"]
            if library and key in override.get("portraits", {}):
                ref = portrait_reference(cfg, override, key)
                if ref.startswith("asset:"):
                    description = library.record(ref).get("description") or description
            definitions.append(f"<Subject {i+1}> is {ep.cast[key].name_en or ep.cast[key].name_cn} "
                               f"in <Picture {i+1}>. {description}")
        if not visible:
            definitions.append("<Subject 1> is the empty Luotian arena environment in <Picture 1>; preserve its architectural identity. It is not a person.")
        singer_index = visible.index(s.singer) + 1 if s.singer in visible else None
        lyrics = " / ".join(timing.lines[i].text for i in s.lines)
        if "lyric_excerpt" in override:
            excerpt = override["lyric_excerpt"]
            if not s.sung or not isinstance(excerpt, str) or not han(excerpt) or han(excerpt) not in han(lyrics):
                raise ValueError(f"{s.id}: lyric_excerpt must be a contiguous part of the selected sung lines")
            lyrics = excerpt.strip()
        if s.sung:
            performance = (f"<Subject {singer_index}> alone articulates the Mandarin rap in the fixed, "
                           f"time-anchored guide soundtrack: <d>[Mandarin]{lyrics}</d>. "
                           f"Match every syllable, onset, rest and rhythm to that guide; do not recompose "
                           f"or repeat it. Keep lips closed during the initial {lead:.2f}s and all guide silences. "
                           "All other subjects stay silent with closed mouths.")
        else:
            performance = ("All visible people keep their mouths closed; no speech or singing."
                           if visible else "No foreground performer enters; no speech or singing.")
        action = override.get("action", s.action_cn)
        framing = override.get("framing", s.framing if mode == "production" else "MCU")
        lens = override.get("lens", s.lens) if mode == "production" else "85"
        camera = override.get("camera", s.camera) if mode == "production" else "locked"
        if framing not in FRAMINGS or lens not in LENSES or camera not in MOVES:
            raise ValueError(f"{s.id}: unsupported framing, lens or camera")
        # Name people in the camera text by their subject label, the same token the
        # subject definitions bind to a picture (a Chinese name here matched nothing).
        if singer_index:
            who_name = f"<Subject {singer_index}>"
        elif visible:
            who_name = "<Subject 1>"
        else:
            who_name = "the primary subject"
        other_name = "the rival"
        camera_text = MOVES[camera].en.format(who_en=who_name, other_en=other_name,
                       fg_en="the rival's blurred shoulder", reveal_en="the supporting teammates")
        camera_text = override.get("camera_description", camera_text)
        composition = override.get("composition", "Preserve the first-frame subject positions and stage axis.")
        acting = "Natural small nods and breathing at normal speed. " if visible else ""
        visible_characters = {character_id(ep.cast[k], k) for k in visible}
        if "wang_ye" in visible_characters:
            acting += "Wang Ye has half-lidded eyes, level low eyebrows, a smooth forehead, relaxed jaw and tiny chin motions; his delivery is quietly detached. "
        if "zhang_zhiwei" in visible_characters:
            acting += "Lao Tianshi has clean evenly toned luminous elder skin, no black or brown facial spots, serene clear eyes, fine silver-white brows and beard. Preserve natural wrinkles and age. "
        if s.sung:
            acting += "Keep the microphone at lower sternum height, never obscure the singer's lips. "
        rear = override.get("view") == "back"
        if library and cfg["keyframes"][s.id].startswith("asset:"):
            rear = rear or library.record(cfg["keyframes"][s.id]).get("view") == "back"
        if rear:
            acting = "Only tiny shoulder breathing; the back of the head and shoulders stay toward camera, with the face continuously unseen. "
        acting = override.get("acting_description", acting)
        look = override.get("look_description", cfg.get("look_description",
                  "Premium refined semi-realistic Chinese cinematic character rendering, detailed hair and fabric, "
                  "soft dimensional skin, flattering neutral key with cool hair edge, indigo stone, jade and bronze."))
        gallery = override.get("gallery_description", cfg.get("gallery_description",
                  "Preserve the exact background population and placement from the first frame. "
                  "Add no new spectators or people. Existing spectators remain in their original seats; "
                  "the performance floor stays clear except for the defined performers."))
        if direction:
            labels = {character_id(ep.cast[k],k): f"<Subject {i+1}>" for i,k in enumerate(visible)}
            if visible:
                action = "Stage geography: " + direction["floor_plan"] + ". " + render_direction(direction["plan"],labels)
            else:
                action = render_direction(direction["plan"], labels)
            acting = ""  # The explicit performance plan replaces random nods and generic acting defaults.
            if motion_video:
                definitions.append(f"<Video 1> is the isolated body-motion visual reference for {labels[direction['plan']['primary']]} only; transfer body movement, retaining the target face, costume, microphone and stage. Ignore source mannequin materials, hand artifacts and mouth motion.")
        if visible:
            summary_block = ("Begin at the approved first-frame camera; preserve stage coordinates, lighting and costume.\n\nretention_analysis:\n"
                             "Every visible subject preserves the facial identity, hair and costume of their own numbered picture. "
                             "The first-frame guide fixes composition, not a still-image display.\n\ndetailed_description:\n")
            headroom_clause = "Maintain complete heads and hairstyles with comfortable headroom. "
        else:
            summary_block = ("Begin at the approved first-frame camera; preserve stage coordinates, architectural geometry and lighting.\n\nretention_analysis:\n"
                             "Preserve the exact architectural geometry, stone, jade, bronze ring and lighting of <Picture 1>. "
                             "The central taiji stage floor stays completely empty with no foreground performer.\n\ndetailed_description:\n")
            headroom_clause = "Maintain clean wide architectural framing with the central taiji stage floor unobstructed. "
        prompt = ("subject_definitions:\n" + "\n".join(definitions) + "\n\nsummary:\n"
                  "[reference generation] A single continuous shot in the approved Luotian mountain-temple rap arena. "
                  + summary_block
                  + look + " "
                  f"[Shot 1] {FRAMINGS[framing][1]}; {LENSES[lens][1]}; {camera_text}. "
                  + headroom_clause
                  + "No camera cut or location change, no crossing the two-rival stage axis. "
                  + composition + " " + performance + " " + action + " " + acting
                  + gallery + " "
                  "No subtitles, text, logos or watermark.\n\noverall_soundscape:\n"
                  "Use the fixed guide vocal timing, no extra speech, harmony or sound effects.\n\nnon_diegetic_music:\nN/A")
        seed = shot_seed(cfg, s.id, take)
        identity = {"shot": s.id, "refs": refs, "keyframe": keyframe, "scene_reference": scene_reference,
                    "mode": mode,
                    "lock_guide_audio": bool(cfg.get("lock_guide_audio", False)),
                    "audio_sha256": files["input/" + audio], "frames": frames, "steps": steps,
                    "seed": seed, "template_sha256": profile["template_sha256"], "prompt": prompt}
        # Only non-default settings enter the identity, so existing take-1 job ids stay valid.
        if take != 1:
            identity["take"] = take
        if any(profile["lora_strengths"].values()):
            identity["lora_strengths"] = profile["lora_strengths"]
        if direction:
            identity.update(direction_fingerprint=direction["fingerprint"], motion_video=motion_video,
                            motion_metadata=motion_metadata)
        if cfg.get("schema_version", 2) >= 3:
            # Include the executable graph (with output names normalized) and
            # conditioning implementation so new jobs cannot silently reuse old takes.
            draft = {**identity, "portraits": refs, "keyframe": keyframe, "audio": audio,
                     "lora_strengths": profile["lora_strengths"],
                     "output_prefix": "__OUTPUT__", "checkpoint_name": "__CHECKPOINT__"}
            graph_signature = graph_for(template, draft)
            identity.update(workflow_sha256=hashlib.sha256(json.dumps(graph_signature, sort_keys=True).encode()).hexdigest(),
                            audio_lock_sha256=file_hash(Path(__file__).with_name("h3_audio_lock.py")),
                            model_profile=cfg.get("model_profile", {}),
                            voice_review=cfg.get("audio_cast", {}).get("review", {}).get("fingerprint"))
        job_id = s.id + "_" + hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:12]
        job = {"job_id": job_id, "shot": s.id, "unit": s.unit, "sung": s.sung,
               "lock_guide_audio": bool(cfg.get("lock_guide_audio", False)),
               "visible_cast": visible, "source_visible_cast": s.who, "source_background": s.background,
               "mode": mode, "pilot_override": override if mode == "pilot" else {},
               "production_override": override if mode == "production" else {},
               "framing": framing, "lens": lens, "camera": camera,
               "scene_reference": scene_reference,
               "portraits": refs, "keyframe": keyframe, "audio": audio,
               "audio_meta": audio_meta, "song_t0": s.t0, "song_t1": s.t1,
               "clip_in": lead, "frames": frames, "fps": 24, "steps": steps,
               "seed": seed, "take": take, "lora_strengths": profile["lora_strengths"],
               "output_prefix": "LuotianMV_" + job_id,
               "checkpoint_name": "LuotianMV_" + job_id + "_av.pt", "prompt": prompt,
               "visual_status": "unreviewed", "workflow": "workflows/" + job_id + ".json"}
        if direction:
            job.update(motion_video=motion_video, motion_metadata=motion_metadata,
                       direction_fingerprint=direction["fingerprint"],
                       review_contract={"version":1,"direction_fingerprint":direction["fingerprint"],
                           "criteria":[k for k in REVIEW_CRITERIA if s.sung or k!="lip_sync"]})
        graph = graph_for(template, job)
        path = out / job["workflow"]
        path.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n")
        files[job["workflow"]] = sha256(path)
        jobs.append(job)
    if cfg.get("lock_guide_audio"):
        node_file = out / "h3_audio_lock.py"
        shutil.copy2(Path(__file__).with_name("h3_audio_lock.py"), node_file)
        files["h3_audio_lock.py"] = sha256(node_file)
    manifest = {"version": 2, "mode": mode, "title": ep.title, "jobs": jobs, "files": files,
                "render_profile": {**profile, "take": take},
                "audio_policy": "Original 48k master retained; guide is resampled, never tempo-stretched.",
                "visual_acceptance_required": True}
    if library:
        manifest["shared_library"] = {"series_id": library.data["series_id"],
                                      "version": library.data.get("version"), "sha256": file_hash(library.path)}
    manifest["voice_policy"] = "reviewed_character_tracks" if cfg.get("schema_version", 2) >= 3 and mode == "production" else "legacy_or_pilot_unverified"
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    shutil.copy2(Path(__file__).with_name("h3_runner.py"), out / "run_h3.py")
    return manifest


def ingest_shot_results(ep_dir: Path, bundle: Path, results: Path) -> dict:
    """Copy generated shot candidates without treating matching audio as lip approval."""
    manifest = json.loads((bundle / "manifest.json").read_text())
    state = json.loads((results / "state.json").read_text())
    index = ep_dir / "h3" / "shot_takes.json"
    data = json.loads(index.read_text()) if index.exists() else {}
    for job in manifest["jobs"]:
        rec = state["jobs"].get(job["job_id"], {})
        if rec.get("status") != "complete":
            continue
        video = next((f for f in rec.get("files", []) if f["file"].endswith("_raw.mp4")), None)
        if video is None:
            raise ValueError(f"{job['job_id']}: marked complete but has no _raw.mp4 in state.json")
        source = results / video["file"]
        if sha256(source) != video["sha256"]:
            raise ValueError("Result checksum mismatch: " + video["file"])
        dest = ep_dir / "h3" / "takes" / job["shot"] / source.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and sha256(dest) != video["sha256"]:
            raise FileExistsError(dest)
        if not dest.exists():
            shutil.copy2(source, dest)
        old = next((r for r in data.get(job["shot"], []) if r["job_id"] == job["job_id"]), None)
        if old:
            continue
        take = {
            "job_id": job["job_id"], "file": dest.relative_to(ep_dir).as_posix(),
            "sha256": video["sha256"], "src_in": job["clip_in"], "duration": job["frames"] / 24,
            "song_t0": job["song_t0"], "song_t1": job["song_t1"], "sung": job["sung"],
            "visual_status": "unreviewed", "identity_status": "unreviewed", "notes": "",
            "mode": job.get("mode", "pilot"), "take": job.get("take", 1), "seed": job.get("seed"),
            "production_override": job.get("production_override", {}),
            "pilot_override": job.get("pilot_override", {})}
        if job.get("review_contract"):
            take.update(review_contract=job["review_contract"],
                generation_contract={k:job.get(k) for k in ("job_id","frames","fps","steps","seed","framing","lens","camera","portraits","keyframe","audio","audio_meta","motion_video","motion_metadata","direction_fingerprint")},
                criteria_status={k:"unreviewed" for k in job["review_contract"]["criteria"]})
            inputs = job["portraits"] + [job.get(k) for k in ("keyframe","audio","motion_video","scene_reference")]
            take["generation_contract"].update(
                input_sha256={name:manifest["files"]["input/"+name] for name in inputs if name},
                workflow_sha256=manifest["files"][job["workflow"]])
        data.setdefault(job["shot"], []).append(take)
    index.parent.mkdir(parents=True, exist_ok=True)
    index.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return data


def approved_shot_takes(ep_dir: Path) -> dict:
    """Only explicit visual + identity acceptance can enter the production EDL."""
    index = ep_dir / "h3" / "shot_takes.json"
    data = json.loads(index.read_text()) if index.exists() else {}
    out = {}
    from aigc_mv.shot_review import review_passed
    for shot, candidates in data.items():
        approved = [r for r in candidates if r.get("visual_status") == "pass"
                    and r.get("identity_status") == "pass" and not r.get("pilot_override")
                    and r.get("mode", "production") == "production" and review_passed(r)]
        if not approved:
            continue
        selected = [r for r in approved if r.get("selected")]
        if len(selected) > 1:
            raise ValueError(f"{shot}: more than one selected H3 take")
        if selected:
            chosen = selected[0]
        elif len(approved) == 1:
            chosen = approved[0]
        else:
            # Never let file order decide which of several good takes reaches the cut.
            raise ValueError(f"{shot}: {len(approved)} approved H3 takes "
                             f"({', '.join(r['job_id'] for r in approved)}); choose one with "
                             f"`aigc-mv ep h3-select <ep> {shot} <job_id>`")
        path = (ep_dir / chosen["file"]).resolve()
        if not path.is_relative_to(ep_dir.resolve()) or sha256(path) != chosen["sha256"]:
            raise ValueError("Approved H3 take changed: " + shot)
        out[shot] = chosen
    return out


def select_shot_take(ep_dir: Path, shot: str, job_id: str) -> dict:
    """Mark one approved take as the shot's pick; the others stay recorded but unused."""
    from aigc_mv.shot_review import review_passed

    ep_dir = Path(ep_dir)
    index = ep_dir / "h3" / "shot_takes.json"
    data = json.loads(index.read_text()) if index.exists() else {}
    candidates = data.get(shot, [])
    matches = [r for r in candidates if r["job_id"] == job_id]
    if len(matches) != 1:
        raise ValueError(f"{shot}: no single take with job id {job_id}")
    take = matches[0]
    if not (take.get("visual_status") == "pass" and take.get("identity_status") == "pass"
            and not take.get("pilot_override") and take.get("mode", "production") == "production"
            and review_passed(take)):
        raise ValueError(f"{shot}: {job_id} is not an approved production take; review it with ep h3-review first")
    path = (ep_dir / take["file"]).resolve()
    if not path.is_relative_to(ep_dir.resolve()) or sha256(path) != take["sha256"]:
        raise ValueError("The selected take changed: " + shot)
    for r in candidates:
        r.pop("selected", None)
    take["selected"] = True
    temporary = index.with_suffix(".partial")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(index)
    return take


def missing_h3_shots(ep_dir: Path, board) -> list[str]:
    """Shots of the board that have no approved, selected H3 take (for an H3-only cut)."""
    approved = approved_shot_takes(Path(ep_dir))
    return [s.id for s in board.shots if s.id not in approved]
