"""Experimental, single-shot H3 motion-reference comparisons (no cloud calls).

Pose videos here are visual R2V references, not ControlNet constraints or 3D rigs.
All variants retain one seed, first frame and guide audio; only reference input
and its explicit prompt relationship change. Pilot outputs cannot enter an edit.
"""
from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

from aigc_mv.h3 import validate_graph
from aigc_mv.h3_runner import verify_bundle
from aigc_mv.shared_assets import file_hash, fingerprint


def inspect_reference(path: Path, expected_frames: int) -> dict:
    """Decode the actual clip; reject audio, variable timing and mismatched lengths."""
    import av  # Optional pilot tool dependency; not required by the main pipeline.

    with av.open(str(path)) as container:
        if len(container.streams.video) != 1 or container.streams.audio:
            raise ValueError("Motion references need one video stream and no source audio")
        stream = container.streams.video[0]
        count, origin = 0, None
        width, height = stream.width, stream.height
        for frame in container.decode(stream):
            if frame.time is None:
                raise ValueError("Motion reference has no presentation timestamps")
            if origin is None:
                origin = frame.time
            if abs(frame.time - origin - count / 24) > 0.002:
                raise ValueError("Motion reference must use constant 24 fps")
            count += 1
        if count != expected_frames:
            raise ValueError(f"Motion reference has {count} frames; expected {expected_frames}")
        if not 48 <= count <= 362:
            raise ValueError("Use a 2–15 second motion reference")
    return {"frames": count, "fps": 24, "width": width, "height": height,
            "sha256": file_hash(path), "source_audio_connected": False}


def reference_graph(graph: dict, video: str) -> dict:
    graph = copy.deepcopy(graph)
    if graph["20"]["class_type"] != "MiniMaxH3ReferenceToVideo":
        raise ValueError("The motion pilot requires the native H3 R2V node")
    if "300" in graph or "301" in graph:
        raise ValueError("Reserved motion-reference node IDs already exist")
    inputs = graph["20"]["inputs"]
    if any(k.startswith(("ref_videos.", "ref_video_audios.")) for k in inputs):
        raise ValueError("Baseline already contains a reference video")
    graph["300"] = {"class_type": "LoadVideo", "inputs": {"file": video}}
    graph["301"] = {"class_type": "GetVideoComponents", "inputs": {"video": ["300", 0]}}
    inputs["ref_videos.ref_video_0"] = ["301", 0]
    # GetVideoComponents.audio is deliberately unconnected. Only our target
    # guide drives speech; the source clip supplies no voice or lyric track.
    validate_graph(graph)
    return graph


def compile_comparison(baseline: Path, raw_video: Path, pose_video: Path,
                       output: Path, motion_description: str) -> dict:
    """Build three immutable pilot bundles; never submits them or approves a take."""
    baseline, output = Path(baseline), Path(output)
    if output.exists():
        raise FileExistsError(output)
    manifest = verify_bundle(baseline)
    if manifest.get("mode") != "pilot" or len(manifest["jobs"]) != 1:
        raise ValueError("Motion comparison requires exactly one pilot shot")
    source = manifest["jobs"][0]
    if len(source["visible_cast"]) != 1 or not source.get("pilot_override"):
        raise ValueError("Use one isolated, visibly identified pilot performer")
    if not motion_description.strip():
        raise ValueError("Describe the selected source performance explicitly")
    clips = {"raw_reference": Path(raw_video), "pose_reference": Path(pose_video)}
    metadata = {key: inspect_reference(path, source["frames"]) for key, path in clips.items()}
    if any((m["width"], m["height"]) != (metadata["raw_reference"]["width"], metadata["raw_reference"]["height"])
           for m in metadata.values()):
        raise ValueError("Raw and pose references must use the same crop and canvas")
    output.mkdir(parents=True)
    report = {"status": "compiled_not_generated", "gpu_started": False,
              "control_mode": "native_r2v_visual_reference_not_controlnet",
              "variants": {}, "motion_description": motion_description,
              "reference_media": metadata}
    for variant in ("text_only", "raw_reference", "pose_reference"):
        target = output / variant
        shutil.copytree(baseline, target)
        current = copy.deepcopy(manifest)
        job = current["jobs"][0]
        graph = json.loads((target / job["workflow"]).read_text())
        if variant in clips:
            path = clips[variant]
            name = f"{metadata[variant]['sha256'][:16]}_{variant}.mp4"
            shutil.copy2(path, target / "input" / name)
            current["files"]["input/" + name] = metadata[variant]["sha256"]
            graph = reference_graph(graph, name)
            form = "a color performance reference" if variant == "raw_reference" else "a skeleton-only performance reference"
            prompt = job["prompt"]
            prompt = prompt.replace("\n\nsummary:",
                f"\n<Video 1> is {form} for <Subject 1>'s body movement only. "
                "The target character, clothing, stage and camera come from the approved image inputs.\n\nsummary:", 1)
            prompt = prompt.replace("\n\noverall_soundscape:",
                "\nFollow the reference performance's body-action order, rhythm and held pauses: "
                + motion_description + " Preserve the target microphone grip and camera. "
                "Source faces, costume, background and mouth articulation do not define the target. "
                "Target lip articulation follows the fixed guide soundtrack.\n\noverall_soundscape:", 1)
            job["prompt"] = graph["20"]["inputs"]["prompt"] = prompt
        signature = copy.deepcopy(graph)
        signature["35"]["inputs"]["filename_prefix"] = "__OUTPUT__"
        signature["37"]["inputs"]["checkpoint_name"] = "__CHECKPOINT__"
        key = source["shot"] + "_" + fingerprint({"variant": variant, "graph": signature,
                                                     "files": current["files"]})[:12]
        job.update(job_id=key, output_prefix="H3Motion_" + key,
                   checkpoint_name="H3Motion_" + key + "_av.pt")
        job["pilot_override"].update(motion_experiment=variant,
            motion_control="visual reference, not a pose or depth ControlNet")
        graph["35"]["inputs"]["filename_prefix"] = job["output_prefix"]
        graph["37"]["inputs"]["checkpoint_name"] = job["checkpoint_name"]
        old_workflow = job["workflow"]
        job["workflow"] = "workflows/" + key + ".json"
        (target / old_workflow).unlink()
        current["files"].pop(old_workflow)
        (target / job["workflow"]).write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n")
        current["files"][job["workflow"]] = file_hash(target / job["workflow"])
        current["motion_experiment"] = {"variant": variant, "mode": report["control_mode"]}
        (target / "manifest.json").write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n")
        verify_bundle(target)
        report["variants"][variant] = {"bundle": str(target), "job_id": key,
            "seed": job["seed"], "guide_sha256": current["files"]["input/" + job["audio"]],
            "frames": job["frames"], "visual_status": "unreviewed"}
    (output / "comparison.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report
