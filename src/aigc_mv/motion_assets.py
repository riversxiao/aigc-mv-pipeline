"""Read an external skeleton library and prepare silent, shot-timed H3 references.

Extraction belongs to the library producer. This adapter never downloads models,
starts a GPU, changes the song clock, or treats metadata as an aesthetic verdict.
"""
from __future__ import annotations

import json
import math
from fractions import Fraction
from pathlib import Path

from aigc_mv.shared_assets import file_hash


def _media():
    try:
        import av
        return av
    except ImportError as exc:
        raise ValueError("Install optional motion dependencies: pip install -e '.[motion]'") from exc


class MotionLibrary:
    KNOWN_CATEGORIES = (
        "battle_rap",
        "instruments",
        "kpop_dance",
        "luotian_combat",
        "piano",
        "drums",
        "stage_performance",
    )

    def __init__(self, path: Path):
        raw_path = Path(path).resolve()
        if raw_path.is_dir():
            candidate = raw_path / "catalog.json"
            self.path = candidate if candidate.is_file() else raw_path
        else:
            self.path = raw_path

        self._base_dirs: dict[str, Path] = {}
        self._categories: dict[str, str] = {}

        if self.path.is_dir():
            self.data = {"schema_version": 1, "motions": {}, "categories": {}}
            self._load_sibling_categories(self.path)
        else:
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
            if self.data.get("schema_version") != 1:
                raise ValueError("Motion library needs schema_version=1 and a motions index")
            if not isinstance(self.data.get("motions"), dict):
                if isinstance(self.data.get("categories"), dict):
                    self.data["motions"] = {}
                else:
                    raise ValueError("Motion library needs schema_version=1 and a motions index")
            primary_cat = self.data.get("category") or self.path.parent.name
            for mid in self.data["motions"]:
                self._base_dirs[mid] = self.path.parent
                self._categories[mid] = primary_cat
            # Load federated categories if declared or if sibling category folders exist
            if isinstance(self.data.get("categories"), dict):
                self._load_declared_categories(self.path.parent, self.data["categories"])
            if self.path.parent.name in self.KNOWN_CATEGORIES:
                self._load_sibling_categories(self.path.parent.parent)
            elif (self.path.parent / "battle_rap" / "catalog.json").is_file():
                self._load_sibling_categories(self.path.parent)

    def _load_declared_categories(self, root_dir: Path, categories_map: dict) -> None:
        for cat_name, cat_meta in categories_map.items():
            rel = cat_meta.get("catalog_path") if isinstance(cat_meta, dict) else None
            candidates = []
            if rel:
                candidates.append((root_dir / rel).resolve())
                candidates.append((root_dir.parent.parent / rel).resolve())
            candidates.append((root_dir / cat_name / "catalog.json").resolve())
            for cpath in candidates:
                if cpath.is_file() and cpath != self.path:
                    self._merge_subcatalog(cat_name, cpath)
                    break

    def _load_sibling_categories(self, motions_root: Path) -> None:
        if not motions_root.is_dir():
            return
        for sub in sorted(motions_root.iterdir()):
            if not sub.is_dir() or sub.name.startswith(".") or sub.name == "incoming":
                continue
            cpath = sub / "catalog.json"
            if cpath.is_file() and cpath != self.path:
                self._merge_subcatalog(sub.name, cpath)

    def _merge_subcatalog(self, cat_name: str, cpath: Path) -> None:
        try:
            sub_data = json.loads(cpath.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        sub_motions = sub_data.get("motions")
        if not isinstance(sub_motions, dict):
            return
        for mid, mrec in sub_motions.items():
            if mid not in self.data["motions"]:
                self.data["motions"][mid] = mrec
                self._base_dirs[mid] = cpath.parent
                self._categories[mid] = sub_data.get("category") or cat_name

    def categories(self) -> list[str]:
        return sorted(set(self._categories.values()))

    def search(
        self,
        *,
        category: str | None = None,
        pose_format: str | None = None,
        hand: str | None = None,
        framing: str | None = None,
        view: str | None = None,
        people: int | None = None,
        tag: str | None = None,
        character: str | None = None,
        ready_only: bool = True,
    ) -> list[dict]:
        results = []
        for mid, rec in self.data["motions"].items():
            if not isinstance(rec, dict):
                continue
            if ready_only and rec.get("status") != "ready":
                continue
            cat = self._categories.get(mid, "default")
            if category and cat != category:
                continue
            if pose_format and rec.get("pose_format") != pose_format:
                continue
            if people is not None and rec.get("people") != people:
                continue
            if hand is not None and rec.get("microphone_hand") not in (hand, "either"):
                continue
            if framing is not None and framing not in rec.get("framings", []):
                continue
            if view is not None and view not in rec.get("views", []):
                continue
            if tag is not None and tag not in rec.get("tags", []):
                continue
            if character is not None and character not in rec.get("characters", []):
                continue
            results.append({"asset_id": mid, "category": cat, **rec})
        return results

    def summary(self) -> dict:
        by_category: dict[str, dict[str, int]] = {}
        by_pose_format: dict[str, int] = {}
        total_ready = 0
        for mid, rec in self.data["motions"].items():
            if not isinstance(rec, dict):
                continue
            cat = self._categories.get(mid, "default")
            bucket = by_category.setdefault(cat, {"total": 0, "ready": 0, "single_1p": 0, "duel_2p": 0})
            bucket["total"] += 1
            if rec.get("status") == "ready":
                total_ready += 1
                bucket["ready"] += 1
                if rec.get("people") == 2:
                    bucket["duel_2p"] += 1
                else:
                    bucket["single_1p"] += 1
                pf = rec.get("pose_format", "unknown")
                by_pose_format[pf] = by_pose_format.get(pf, 0) + 1
        return {
            "library": str(self.path),
            "total_motions": len(self.data["motions"]),
            "ready_motions": total_ready,
            "categories": by_category,
            "by_pose_format": by_pose_format,
        }

    def resolve(
        self,
        asset_id: str,
        *,
        hand: str,
        framing: str,
        view: str,
        people: int = 1,
        allow_free_hands: bool = False,
    ) -> dict:
        record = self.data["motions"].get(asset_id)
        if not isinstance(record, dict):
            raise ValueError(f"Unknown motion asset: {asset_id}")
        if record.get("kind") != "pose_video" or record.get("status") != "ready":
            raise ValueError(f"{asset_id}: an inspected, ready pose_video is required")
        if people == 1 and record.get("people") != 1:
            raise ValueError(f"{asset_id}: this adapter needs an isolated single-person skeleton")
        if people != 1 and record.get("people") != people:
            raise ValueError(f"{asset_id}: motion people={record.get('people')} does not match expected people={people}")
        rec_hand = record.get("microphone_hand")
        if rec_hand not in (hand, "either") and not (allow_free_hands and rec_hand == "none"):
            raise ValueError(f"{asset_id}: microphone hand differs; select or explicitly prepare a matching motion")
        if framing not in record.get("framings", []) or view not in record.get("views", []):
            raise ValueError(f"{asset_id}: framing or view does not match this shot")
        base_dir = self._base_dirs.get(asset_id, self.path.parent if self.path.is_file() else self.path)
        rel_path = record.get("path") or record.get("file")
        if not isinstance(rel_path, str) or not rel_path:
            raise ValueError(f"{asset_id}: missing relative path in motion record")
        path = (base_dir / rel_path).resolve()
        if not path.is_relative_to(base_dir):
            raise ValueError(f"{asset_id}: path escapes the motion library")
        if not path.is_file() or path.stat().st_size > 200 * 1024**2:
            raise ValueError(f"{asset_id}: missing or oversized pose video (limit 200 MiB)")
        if file_hash(path) != record.get("sha256"):
            raise ValueError(f"{asset_id}: motion bytes changed; register a new version")
        av = _media()
        with av.open(str(path)) as container:
            if len(container.streams.video) != 1 or container.streams.audio:
                raise ValueError(f"{asset_id}: skeleton video needs one video stream and no audio")
            stream = container.streams.video[0]
            if stream.duration is None or stream.duration*stream.time_base <= 0:
                raise ValueError(f"{asset_id}: remux the video to provide valid duration metadata")
            if next(container.decode(stream), None) is None:
                raise ValueError(f"{asset_id}: video has no decodable frame")
            media = {"duration":float(stream.duration*stream.time_base), "width":stream.width,
                     "height":stream.height, "native_fps":str(stream.average_rate) if stream.average_rate else None}
        return {"asset_id": asset_id, "source": str(path), "sha256": record["sha256"],
                "library": str(self.path), "microphone_hand": record["microphone_hand"],
                "framing": framing, "view": view, "kind": "pose_video", "media":media}


def prepare_motion(source: Path, target: Path, *, expected_sha256: str, frames: int,
                   lead_frames: int, active_frames: int, fit: str = "retime",
                   start: float = 0, end: float | None = None) -> dict:
    """Fit a selected motion interval to a guide; only the motion clock changes."""
    av = _media()

    if target.exists():
        raise FileExistsError(target)
    if frames % 17 != 5 or not 48 <= frames <= 362:
        raise ValueError("Use a legal H3 reference length at 24 fps")
    if lead_frames < 0 or active_frames < 1 or lead_frames + active_frames > frames:
        raise ValueError("Motion lead, active span and H3 frame budget conflict")
    if fit not in ("retime", "trim_hold") or not math.isfinite(start) or start < 0:
        raise ValueError("Specify motion fit=retime or trim_hold and a nonnegative start")
    if file_hash(source) != expected_sha256:
        raise ValueError("Motion source changed after preflight")
    images = []
    with av.open(str(source)) as container:
        if len(container.streams.video) != 1 or container.streams.audio:
            raise ValueError("Skeleton library videos must have one video stream and no audio")
        stream = container.streams.video[0]
        if stream.duration is None:
            raise ValueError("Motion video needs duration metadata; remux it before import")
        duration = float(stream.duration * stream.time_base)
        stop = duration if end is None else end
        if not math.isfinite(stop) or stop <= start or stop > duration + 0.002 or stop-start > 15:
            raise ValueError("Select an available motion interval of at most 15 seconds")
        speed = (stop-start) / (active_frames/24) if fit == "retime" else 1.0
        if fit == "retime" and not 0.5 <= speed <= 2:
            raise ValueError("Motion would require over 2x speed change; select a closer performance")
        # Preserve the aspect ratio; cap conditioning pixels and align the VAE canvas.
        scale = min(1.0, 960/stream.width, 544/stream.height)
        width = max(32, round(stream.width*scale/32)*32)
        height = max(32, round(stream.height*scale/32)*32)
        requested = [start + i/24*speed for i in range(active_frames)]
        container.seek(int(start/stream.time_base), stream=stream)
        last = None
        for frame in container.decode(stream):
            if frame.time is None:
                raise ValueError("Motion frames require presentation timestamps")
            if frame.time < start:
                continue
            if frame.time >= stop:
                break
            last = frame.reformat(width=width, height=height, format="rgb24").to_ndarray()
            while len(images) < active_frames and requested[len(images)] <= frame.time+1e-6:
                images.append(last)
            if len(images) == active_frames:
                break
        if last is None:
            raise ValueError("No decodable motion frames in the selected interval")
        images.extend([last] * (active_frames-len(images)))
    images = [images[0]]*lead_frames + images + [images[-1]]*(frames-lead_frames-active_frames)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.stem + ".partial.mp4")
    try:
        with av.open(str(temporary), "w") as container:
            stream = container.add_stream("libx264", rate=24)
            stream.width, stream.height, stream.pix_fmt = width, height, "yuv420p"
            stream.options = {"crf": "17", "preset": "fast"}
            for i, image in enumerate(images):
                frame = av.VideoFrame.from_ndarray(image, format="rgb24")
                frame.pts, frame.time_base = i, Fraction(1, 24)
                for packet in stream.encode(frame):
                    container.mux(packet)
            for packet in stream.encode():
                container.mux(packet)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return {"source_sha256": expected_sha256, "prepared_sha256": file_hash(target),
            "source_interval": [start, stop], "fit": fit, "motion_speed": speed,
            "frames": frames, "fps": 24, "lead_frames": lead_frames,
            "active_frames": active_frames, "tail_hold_frames": frames-lead_frames-active_frames,
            "source_audio_used": False, "target_audio_retimed": False}
