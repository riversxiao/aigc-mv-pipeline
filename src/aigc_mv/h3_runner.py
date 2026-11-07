#!/usr/bin/env python3
"""Stdlib-only, resumable local-Comfy runner for an exported H3 bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import time
import urllib.error
import urllib.request
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic(path, data):
    tmp = path.with_suffix(".partial")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    tmp.replace(path)


def api(base, route, data=None):
    req = urllib.request.Request(base + route, None if data is None else json.dumps(data).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Comfy {route}: HTTP {e.code}: {e.read().decode()[:2000]}") from e


def verify_bundle(root):
    manifest = json.loads((root / "manifest.json").read_text())
    for rel, want in manifest["files"].items():
        path = (root / rel).resolve()
        if not path.is_relative_to(root.resolve()) or digest(path) != want:
            raise ValueError(f"Bundle checksum mismatch: {rel}")
    return manifest


def run(root, comfy, output, base, max_seconds=900, dry_run=False):
    manifest = verify_bundle(root)
    if dry_run:
        return {"verified_inputs": len(manifest["files"]), "jobs": len(manifest["jobs"]), "submitted": 0}
    output.mkdir(parents=True, exist_ok=True)
    state_path = output / "state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {"jobs": {}}
    # BUNNY keeps its small adapter in the plugin's own models folder; the shared
    # model cache is already on NVMe and need not be read back through DriveFS.
    bunny = comfy / "models/model_patches/BUNNY_H3_ActionLogic_Bridge_V2.safetensors"
    bunny_dir = comfy / "custom_nodes/BUNNY_H3_Conditioning_Bridge/models"
    if bunny.is_file():
        bunny_dir.mkdir(parents=True, exist_ok=True)
        if not (bunny_dir / bunny.name).is_file():
            shutil.copy2(bunny, bunny_dir / bunny.name)
    nodes = api(base, "/object_info")
    for job in manifest["jobs"]:
        graph = json.loads((root / job["workflow"]).read_text())
        missing = {n["class_type"] for n in graph.values()} - set(nodes)
        if missing:
            raise ValueError(f"Missing Comfy nodes: {sorted(missing)}")
    (comfy / "input").mkdir(exist_ok=True)
    for f in (root / "input").iterdir():
        shutil.copy2(f, comfy / "input" / f.name)
    deadline = time.monotonic() + max_seconds
    for job in manifest["jobs"]:
        key = job["job_id"]
        job_deadline = min(deadline, time.monotonic() + 900)
        rec = state["jobs"].get(key, {})
        if rec.get("status") == "complete":
            for f in rec["files"]:
                if digest(output / f["file"]) != f["sha256"]:
                    raise ValueError(f"Completed output changed: {key}")
            print("REUSED", key, flush=True)
            continue
        if rec.get("status") == "submitting":
            raise RuntimeError(f"Submission outcome unknown for {key}; reconcile queue/history before retrying")
        graph = json.loads((root / job["workflow"]).read_text())
        if not rec.get("prompt_id"):
            if (comfy / "output" / "latents" / job["checkpoint_name"]).exists():
                raise RuntimeError(f"Native AV checkpoint already exists for {key}; recover/decode it before any resampling")
            if list((comfy / "output").glob(job["output_prefix"] + "_*.mp4")):
                raise RuntimeError(f"Existing output without matching state for {key}; reconcile before retrying")
            if time.monotonic() >= deadline:
                raise TimeoutError("Batch deadline reached before submission")
            rec = state["jobs"][key] = {"status": "submitting", "started": time.time()}
            atomic(state_path, state)
            response = api(base, "/prompt", {"prompt": graph, "client_id": key,
                                           "extra_data": {"h3_job_id": key}})
            if not response.get("prompt_id"):
                raise RuntimeError(f"Comfy rejected {key}: {response}")
            rec.update(status="queued", prompt_id=response["prompt_id"])
            atomic(state_path, state)
            print("SUBMITTED", key, rec["prompt_id"], flush=True)
        while True:
            entry = api(base, "/history/" + rec["prompt_id"]).get(rec["prompt_id"])
            if entry:
                status = entry.get("status", {})
                if status.get("status_str") == "error":
                    rec.update(status="failed", history=entry)
                    atomic(state_path, state)
                    raise RuntimeError(f"Comfy failed {key}: {status.get('messages')}")
                if status.get("completed"):
                    break
            if time.monotonic() >= job_deadline:
                raise TimeoutError("Batch deadline reached; queued job state retained")
            time.sleep(5)
        videos = sorted((comfy / "output").glob(job["output_prefix"] + "_*.mp4"),
                        key=lambda f: f.stat().st_mtime)
        latent = comfy / "output" / "latents" / job["checkpoint_name"]
        if len(videos) != 1 or not latent.is_file():
            raise RuntimeError(f"Expected one video and a latent checkpoint for {key}")
        files = []
        for source, name in [(videos[0], key + "_raw.mp4"), (latent, key + "_av.pt")]:
            target = output / name
            shutil.copy2(source, target)
            files.append({"file": name, "size": target.stat().st_size, "sha256": digest(target)})
        (output / (key + "_history.json")).write_text(json.dumps(entry, ensure_ascii=False, indent=2))
        rec.update(status="complete", finished=time.time(), files=files,
                   visual_status="unreviewed", audio_alignment_is_not_visual_verification=True)
        atomic(state_path, state)
        print("COMPLETE", key, json.dumps(files), flush=True)
    return state


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bundle", type=Path, default=Path(__file__).resolve().parent)
    p.add_argument("--comfy", type=Path, default=Path("/content/ComfyUI"))
    p.add_argument("--out", type=Path)
    p.add_argument("--api", default="http://127.0.0.1:8188")
    p.add_argument("--max-seconds", type=int, default=900)
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    result = run(a.bundle, a.comfy, a.out or a.bundle / "results", a.api, a.max_seconds, a.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
