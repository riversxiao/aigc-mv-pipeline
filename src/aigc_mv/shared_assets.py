"""Versioned series assets and local production checks; no generation or network."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image

from aigc_mv.board import load_board
from aigc_mv.episode import load_episode
from aigc_mv.timing import load_timing


def file_hash(path: Path) -> str:
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def fingerprint(value: dict | list) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class AssetLibrary:
    SHARED_PREFIXES = (
        "asset:",
        "charsheet:",
        "wardrobe:",
        "stage_v2:",
        "meoogo:",
        "meoogo_16x9:",
        "timeline:",
    )

    def __init__(self, path: Path):
        self.path = Path(path).resolve()
        self.root = self.path.parent
        self.data = json.loads(self.path.read_text(encoding="utf-8"))
        if self.data.get("schema_version") != 1 or not isinstance(self.data.get("assets"), dict):
            raise ValueError("Unsupported shared asset library")
        self._ext_cache: dict[str, dict] = {}

    @classmethod
    def is_shared_reference(cls, value: str | None) -> bool:
        return isinstance(value, str) and value.startswith(cls.SHARED_PREFIXES)

    def _load_extensions(self) -> dict:
        if self._ext_cache:
            return self._ext_cache
        charsheets: dict[str, dict] = {}
        wardrobes: dict[str, dict] = {}
        stage_v2: dict[str, dict] = {}
        meoogo: dict[str, dict] = {}
        meoogo_16x9: dict[str, dict] = {}
        timeline: dict[str, dict] = {}
        drive_index: dict[str, dict] = {}

        # 1. 3D Character Turnaround Sheets & 4x Female Wardrobe Sheets
        cs_path = self.root / "character_sheets" / "character_sheets_catalog.json"
        if cs_path.is_file():
            try:
                cs_data = json.loads(cs_path.read_text(encoding="utf-8"))
                for item in cs_data.get("sheets", []):
                    fname = item.get("file", "")
                    cid = item.get("character_id") or Path(fname).stem.lower()
                    sid = item.get("sheet_id") or f"charsheet.{cid}.v1"
                    zh = item.get("character_zh", "")
                    stype = item.get("sheet_type", "quadview_3d_charsheet")
                    is_wardrobe = "wardrobe" in stype
                    rec = {
                        "kind": "portrait",
                        "path": f"character_sheets/{fname}",
                        "sha256": item.get("sha256"),
                        "characters": [cid],
                        "character_zh": zh,
                        "faction": item.get("faction", ""),
                        "positions": {},
                        "description": f"{zh} ({item.get('faction', '')}) — {stype} 16:9 reference sheet",
                        "view": "wardrobe_4x" if is_wardrobe else "quadview",
                        "sheet_type": stype,
                        "sheet_id": sid,
                    }
                    if is_wardrobe:
                        for k in (sid, cid, zh, Path(fname).stem):
                            if k:
                                wardrobes[k] = rec
                    else:
                        for k in (sid, cid, zh, Path(fname).stem):
                            if k:
                                charsheets[k] = rec
                    # Also allow charsheet:<sid> to resolve explicit wardrobe sheet_id
                    charsheets.setdefault(sid, rec)
            except (OSError, ValueError):
                pass

        # 2. Stage v2.0 Neo-Taoist Concert Arena Assets
        st_path = self.root / "stage_v2" / "catalog.json"
        if st_path.is_file():
            try:
                st_data = json.loads(st_path.read_text(encoding="utf-8"))
                for sid, srec in st_data.get("assets", {}).items():
                    rel = f"stage_v2/{srec['path']}"
                    entry = {
                        "kind": srec.get("kind", "composition"),
                        "path": rel,
                        "sha256": srec.get("sha256"),
                        "characters": srec.get("characters", []),
                        "positions": srec.get("positions", {}),
                        "description": srec.get("description", ""),
                        "view": srec.get("view", "front"),
                    }
                    stage_v2[sid] = entry
                    short = sid.removeprefix("stage_v2.").removesuffix(".v1")
                    stage_v2[short] = entry
                    stage_v2[Path(srec["path"]).stem] = entry
            except (OSError, ValueError):
                pass

        # 3. Meoogo 378-Character Canon 2D Refs & 1344x768 16:9 Padded Inputs
        mg_path = self.root / "meoogo_refs" / "meoogo_characters_catalog.json"
        if mg_path.is_file():
            try:
                mg_data = json.loads(mg_path.read_text(encoding="utf-8"))
                for item in mg_data.get("characters", []):
                    cid = item.get("meoogo_id") or item.get("id", "")
                    name = item.get("name_cn") or item.get("name", "")
                    local_rel = item.get("local_2d_ref") or item.get("local_image", "")
                    pad_rel = item.get("padded_16x9_ref", "")
                    fname = Path(local_rel).name if local_rel else ""
                    pad_fname = Path(pad_rel).name if pad_rel else ""
                    stem = Path(fname).stem if fname else cid
                    desc_parts = [name, item.get("faction", ""), item.get("role_tag", ""), item.get("bio", "")]
                    desc = " | ".join(p for p in desc_parts if p)
                    if fname:
                        raw_rec = {
                            "kind": "portrait",
                            "path": f"meoogo_refs/{fname}",
                            "sha256": item.get("sha256"),
                            "characters": [cid or name],
                            "character_zh": name,
                            "faction": item.get("faction", ""),
                            "positions": {},
                            "description": desc,
                            "view": "front",
                            "micw_quadview_prompt": item.get("micw_quadview_prompt", ""),
                        }
                        for k in (cid, name, stem):
                            if k:
                                meoogo.setdefault(k, raw_rec)
                    if pad_fname:
                        pad_rec = {
                            "kind": "portrait",
                            "path": f"meoogo_padded_16x9/{pad_fname}",
                            "sha256": None,
                            "characters": [cid or name],
                            "character_zh": name,
                            "faction": item.get("faction", ""),
                            "positions": {},
                            "description": desc,
                            "view": "front",
                            "micw_quadview_prompt": item.get("micw_quadview_prompt", ""),
                        }
                        for k in (cid, name, stem, Path(pad_fname).stem):
                            if k:
                                meoogo_16x9.setdefault(k, pad_rec)
            except (OSError, ValueError):
                pass

        # 4. Multi-Age Timeline Reference Cards
        tl_path = self.root / "meoogo_refs" / "meoogo_timeline_multi_age_catalog.json"
        if tl_path.is_file():
            try:
                tl_data = json.loads(tl_path.read_text(encoding="utf-8"))
                for item in tl_data.get("items", []):
                    label = item.get("label", "")
                    lpath = item.get("local_path", "")
                    fname = Path(lpath).name if lpath else ""
                    if label and fname:
                        timeline[label] = {
                            "kind": "portrait",
                            "path": f"meoogo_refs/{fname}",
                            "sha256": item.get("sha256"),
                            "characters": [label],
                            "positions": {},
                            "description": label,
                            "view": "front",
                        }
            except (OSError, ValueError):
                pass

        # 5. Google Drive Sync Index
        drv_path = self.root / "master_asset_library_drive.json"
        if drv_path.is_file():
            try:
                drv_data = json.loads(drv_path.read_text(encoding="utf-8"))
                for item in drv_data.get("files", []):
                    if isinstance(item, dict) and item.get("name"):
                        drive_index[item["name"]] = item
                for k, v in drv_data.get("uploaded_files", {}).items():
                    if isinstance(v, dict):
                        drive_index[k] = v
                        drive_index[Path(k).name] = v
            except (OSError, ValueError):
                pass

        self._ext_cache = {
            "charsheet": charsheets,
            "wardrobe": wardrobes,
            "stage_v2": stage_v2,
            "meoogo": meoogo,
            "meoogo_16x9": meoogo_16x9,
            "timeline": timeline,
            "drive": drive_index,
        }
        return self._ext_cache

    def record(self, reference: str) -> dict:
        if not isinstance(reference, str):
            raise ValueError(f"Unknown shared asset: {reference}")
        if reference.startswith("asset:"):
            key = reference.removeprefix("asset:")
            if key not in self.data["assets"]:
                raise ValueError(f"Unknown shared asset: {reference}")
            return self.data["assets"][key]
        ext = self._load_extensions()
        for prefix in ("charsheet:", "wardrobe:", "stage_v2:", "meoogo:", "meoogo_16x9:", "timeline:"):
            if reference.startswith(prefix):
                bucket = prefix.rstrip(":")
                key = reference.removeprefix(prefix)
                rec = ext.get(bucket, {}).get(key)
                if not isinstance(rec, dict):
                    raise ValueError(f"Unknown shared asset: {reference}")
                return rec
        raise ValueError(f"Unknown shared asset: {reference}")

    def resolve(self, reference: str) -> Path:
        record = self.record(reference)
        path = (self.root / record["path"]).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError(f"Shared asset escapes its library: {reference}")
        if not path.is_file():
            raise FileNotFoundError(f"Restore missing shared asset: {reference} ({path})")
        expected_sha = record.get("sha256")
        if expected_sha and file_hash(path) != expected_sha:
            raise ValueError(f"Shared asset changed: {reference}; register a new version")
        return path

    def cloud_info(self, reference_or_path: str) -> dict | None:
        ext = self._load_extensions()
        drv = ext.get("drive", {})
        if reference_or_path in drv:
            return drv[reference_or_path]
        if self.is_shared_reference(reference_or_path):
            try:
                rec = self.record(reference_or_path)
                rel = rec.get("path", "")
                return drv.get(rel) or drv.get(Path(rel).name)
            except ValueError:
                return None
        return drv.get(Path(reference_or_path).name)

    def character_profile(self, character: str, *, name_cn: str = "", age_variant: str | None = None) -> dict:
        lookup_id = f"{character}_{age_variant}" if age_variant else character
        base = copy.deepcopy(self.data.get("characters", {}).get(lookup_id) or self.data.get("characters", {}).get(character, {}))
        ext = self._load_extensions()
        cs = ext["charsheet"].get(lookup_id) or ext["charsheet"].get(character) or (ext["charsheet"].get(name_cn) if name_cn else None)
        wd = ext["wardrobe"].get(character) or (ext["wardrobe"].get(name_cn) if name_cn else None)
        mg = ext["meoogo"].get(character) or (ext["meoogo"].get(name_cn) if name_cn else None)
        mg16 = ext["meoogo_16x9"].get(character) or (ext["meoogo_16x9"].get(name_cn) if name_cn else None)
        if cs:
            base.setdefault("turnaround_sheet", f"charsheet:{cs['sheet_id']}")
            if age_variant or "portrait" not in base:
                base["portrait"] = f"charsheet:{cs['sheet_id']}"
            base.setdefault("description", cs.get("description", name_cn or character))
        if wd:
            base.setdefault("wardrobe_sheet", f"wardrobe:{wd['sheet_id']}")
        if mg16 and "portrait" not in base:
            base["portrait"] = f"meoogo_16x9:{name_cn or character}"
            base.setdefault("description", mg16.get("description", name_cn or character))
        if mg:
            base.setdefault("canon_2d_ref", f"meoogo:{name_cn or character}")
        return base

    def summary(self) -> dict:
        ext = self._load_extensions()
        cs_unique = {v["path"] for v in ext["charsheet"].values()}
        wd_unique = {v["path"] for v in ext["wardrobe"].values()}
        st_unique = {v["path"] for v in ext["stage_v2"].values()}
        mg_unique = {v["path"] for v in ext["meoogo"].values()}
        mg16_unique = {v["path"] for v in ext["meoogo_16x9"].values() if (self.root / v["path"]).is_file()}
        tl_unique = {v["path"] for v in ext["timeline"].values()}
        drv_unique = {v.get("file_id") or v.get("id") for v in ext["drive"].values() if isinstance(v, dict) and (v.get("file_id") or v.get("id"))}
        return {
            "series_id": self.data.get("series_id"),
            "version": self.data.get("version"),
            "base_characters": len(self.data.get("characters", {})),
            "content_addressed_assets": len(self.data.get("assets", {})),
            "quadview_3d_sheets": len(cs_unique - wd_unique),
            "female_wardrobe_4x_sheets": len(wd_unique),
            "total_3d_character_sheets": len(cs_unique | wd_unique),
            "stage_v2_assets": len(st_unique),
            "meoogo_2d_characters": len(mg_unique),
            "meoogo_padded_16x9_inputs": len(mg16_unique),
            "timeline_multi_age_refs": len(tl_unique),
            "google_drive_synced_files": len(drv_unique),
        }

    def check_cast(self, reference: str, characters: list[str], *, positions: dict | None = None,
                   kind: str | None = None) -> None:
        record = self.record(reference)
        if kind and record["kind"] != kind:
            raise ValueError(f"{reference}: expected {kind}, got {record['kind']}")
        rec_chars = set(record.get("characters", []))
        req_chars = set(characters)
        if reference.startswith("asset:"):
            if rec_chars != req_chars:
                raise ValueError(f"{reference}: character identity differs from this episode's cast")
        else:
            # For extended character sheets / multi-age variants (e.g. zhang_zhiwei_young for zhang_zhiwei)
            if rec_chars != req_chars:
                matched = len(rec_chars) == len(req_chars) and all(
                    any(rc == qc or rc.startswith(qc + "_") or qc.startswith(rc + "_") for rc in rec_chars)
                    for qc in req_chars
                )
                if not matched and not reference.startswith(("meoogo:", "meoogo_16x9:", "timeline:")):
                    raise ValueError(f"{reference}: character identity differs from this episode's cast")
        for character, side in record.get("positions", {}).items():
            if positions is not None and positions.get(character) != side:
                raise ValueError(f"{reference}: stage side changed for {character}; choose a matching first frame")


def register_asset(library_path: Path, asset_id: str, source: Path, kind: str,
                   characters: list[str], *, positions: dict | None = None,
                   description: str = "", view: str = "") -> dict:
    """Copy one immutable, content-addressed object; never replace an existing version."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", asset_id):
        raise ValueError("Use a stable dotted asset ID, e.g. character.wang_ye.front.v1")
    if kind not in ("portrait", "composition", "scene", "voice"):
        raise ValueError("Unsupported shared asset kind")
    if len(characters) != len(set(characters)):
        raise ValueError("Asset character IDs must be unique")
    if kind in ("portrait", "voice") and len(characters) != 1:
        raise ValueError("A portrait or voice reference belongs to exactly one character")
    if kind == "scene" and characters:
        raise ValueError("An empty scene asset cannot contain named characters")
    if positions is not None and not isinstance(positions, dict):
        raise ValueError("Positions must be a JSON object")
    if positions and (set(positions) - set(characters) or set(positions.values()) - {"left", "right", "center"}):
        raise ValueError("Positions must describe the asset's named characters")
    library = AssetLibrary(library_path)
    source = Path(source).resolve()
    if kind == "voice":
        sf.info(source)
    else:
        with Image.open(source) as image:
            image.verify()
    digest = file_hash(source)
    if kind in ("portrait", "voice"):
        for other in library.data["assets"].values():
            if other["kind"] == kind and other["sha256"] == digest and set(other.get("characters", [])) != set(characters):
                raise ValueError(f"The same {kind} bytes are already assigned to another character")
    record = {"kind": kind, "path": f"objects/{digest}{source.suffix.lower()}",
              "sha256": digest, "characters": characters, "positions": positions or {},
              "description": description, "view": view}
    old = library.data["assets"].get(asset_id)
    if old:
        if any(old.get(k) != record[k] for k in ("sha256", "kind", "characters", "positions", "view")):
            raise ValueError(f"{asset_id} already exists; register a new version")
        library.resolve("asset:" + asset_id)
        return old
    target = library.root / record["path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if file_hash(target) != digest:
            raise ValueError("Shared object store is corrupted")
    else:
        shutil.copy2(source, target)
        target.chmod(0o444)
    library.data["assets"][asset_id] = record
    if kind == "portrait" and view == "front":
        profile = library.data.setdefault("characters", {}).setdefault(characters[0], {})
        profile.setdefault("portrait", "asset:" + asset_id)
        profile.setdefault("description", description)
    temp = library.path.with_suffix(library.path.suffix + ".partial")
    temp.write_text(json.dumps(library.data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(library.path)
    return record


def load_asset_config(path: Path) -> tuple[dict, AssetLibrary | None]:
    path = Path(path).resolve()
    cfg = json.loads(path.read_text(encoding="utf-8"))
    library = AssetLibrary(path.parent / cfg["asset_library"]) if cfg.get("asset_library") else None
    if library:
        if cfg.get("series_id", library.data["series_id"]) != library.data["series_id"]:
            raise ValueError("Episode and asset library belong to different series")
        cfg = {**copy.deepcopy(library.data.get("defaults", {})), **cfg}
    return cfg, library


def resolve_reference(value: str, root: Path, library: AssetLibrary | None) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("Asset reference is missing")
    if AssetLibrary.is_shared_reference(value):
        if library is None:
            raise ValueError(f"{value.split(':', 1)[0]}: references require an asset_library")
        return library.resolve(value)
    path = (root / value).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def character_id(member, fallback: str) -> str:
    return getattr(member, "character", fallback)


def portrait_reference(cfg: dict, shot_override: dict, key: str) -> str:
    return shot_override.get("portraits", {}).get(key) or cfg["cast"][key]["portrait"]


def voice_readiness(ep_dir: Path, assets_file: Path, *, require_review: bool = True) -> dict:
    """Validate voice routing and a human listening record, not speaker biometrics."""
    ep_dir, assets_file = Path(ep_dir).resolve(), Path(assets_file).resolve()
    ep = load_episode(ep_dir)
    cfg, library = load_asset_config(assets_file)
    speakers = sorted({ep.cast[ep.singer_of(verse, line)].character
                       for _, _, verse, line in ep.all_lines()})
    errors, rows, voice_ids, reference_hashes, track_hashes = [], [], {}, {}, {}
    sources = {}
    master_duration = None
    for label, relative in (("song", ep.song), ("instrumental", ep.instrumental)):
        try:
            if not relative:
                raise ValueError(f"{label} is not configured")
            path = ep_dir / relative
            sources[label] = file_hash(path)
            if label == "song":
                master_duration = sf.info(path).duration
        except (OSError, ValueError, RuntimeError) as exc:
            errors.append(f"audio.{label}: {exc}")
    audio_cast = cfg.get("audio_cast", {})
    for character in speakers:
        voice = audio_cast.get("voices", {}).get(character, {})
        try:
            voice_id = voice.get("voice_id")
            if not isinstance(voice_id, str) or not voice_id.strip():
                raise ValueError("voice_id is missing")
            reference = voice.get("reference")
            ref = resolve_reference(reference, assets_file.parent, library)
            if reference.startswith("asset:"):
                library.check_cast(reference, [character], kind="voice")
            info = sf.info(ref)
            with sf.SoundFile(ref) as stream:
                samples = stream.read(min(len(stream), info.samplerate * 8), always_2d=True)
            if info.duration < 1 or info.channels not in (1, 2) or np.max(np.abs(samples)) < 1e-5:
                raise ValueError("voice reference must contain audible mono/stereo audio of at least one second")
            relative_track = voice.get("vocals")
            if not isinstance(relative_track, str) or not relative_track:
                raise ValueError("episode-local character vocals track is missing")
            track = (ep_dir / relative_track).resolve()
            if not track.is_relative_to(ep_dir):
                raise ValueError("character vocals belong to this episode; reuse the voice reference, not another episode's lyrics")
            track_info = sf.info(track)
            if master_duration is not None and (track_info.duration < master_duration - 1 / track_info.samplerate
                                               or track_info.duration > master_duration + 1 / ep.fps):
                raise ValueError("character vocals must use the full master timeline, including silence outside their turns")
            peak = 0.0
            with sf.SoundFile(track) as stream:
                for block in stream.blocks(blocksize=65536, dtype="float32", always_2d=True):
                    if not np.isfinite(block).all():
                        raise ValueError("character vocals contain non-finite samples")
                    peak = max(peak, float(np.max(np.abs(block))))
            if track_info.channels not in (1, 2) or peak < 1e-5:
                raise ValueError("character vocals must contain audible mono/stereo performance, not a silent placeholder")
            ref_hash, track_hash = file_hash(ref), file_hash(track)
            for value, used, label in ((voice_id, voice_ids, "voice_id"),
                                       (ref_hash, reference_hashes, "voice reference"),
                                       (track_hash, track_hashes, "character vocal track")):
                if value in used and used[value] != character:
                    raise ValueError(f"{label} is also assigned to {used[value]}")
                used[value] = character
            rows.append({"character": character, "voice_id": voice_id,
                         "reference_sha256": ref_hash, "vocals_sha256": track_hash})
        except (OSError, ValueError, RuntimeError, KeyError) as exc:
            errors.append(f"voice.{character}: {exc}")
    script = [{"character": ep.cast[ep.singer_of(v, line)].character,
               "text": line.text, "spoken": line.spoken} for _, _, v, line in ep.all_lines()]
    expected = fingerprint({"audio": sources, "voices": rows, "script": script}) if not errors else None
    review = audio_cast.get("review", {})
    if require_review:
        if review.get("status") != "approved" or not review.get("notes", "").strip():
            errors.append("Voice listening review is pending: compare the actual characters and final mix before production")
        elif expected and review.get("fingerprint") != expected:
            errors.append("Voice listening review is stale: audio, voice assignment or reference changed")
    return {"ready": not errors, "speakers": speakers, "voices": rows,
            "expected_fingerprint": expected, "errors": errors,
            "scope": "File bindings plus a human listening record; no automatic same-speaker claim"}


def approve_voices(ep_dir: Path, assets_file: Path, notes: str) -> dict:
    if not notes.strip():
        raise ValueError("Listening notes are required")
    report = voice_readiness(ep_dir, assets_file, require_review=False)
    if report["errors"]:
        raise ValueError("; ".join(report["errors"]))
    cfg = json.loads(Path(assets_file).read_text(encoding="utf-8"))
    cfg.setdefault("audio_cast", {})["review"] = {
        "status": "approved", "fingerprint": report["expected_fingerprint"], "notes": notes}
    Path(assets_file).write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return voice_readiness(ep_dir, assets_file)


def production_readiness(ep_dir: Path, assets_file: Path, shots: list[str] | None = None) -> dict:
    ep_dir, assets_file = Path(ep_dir).resolve(), Path(assets_file).resolve()
    ep = load_episode(ep_dir)
    cfg, library = load_asset_config(assets_file)
    errors, used = [], set()

    def check(reference, characters=None, positions=None, kind=None):
        try:
            path = resolve_reference(reference, assets_file.parent, library)
            with Image.open(path) as image:
                image.verify()
            if AssetLibrary.is_shared_reference(reference):
                used.add(reference)
                if characters is not None and library is not None:
                    library.check_cast(reference, characters, positions=positions, kind=kind)
            return path
        except (OSError, ValueError, KeyError) as exc:
            errors.append(str(exc))
            return None

    if not library:
        errors.append("A shared series asset_library is required for series production")
    for key, member in ep.cast.items():
        check(cfg.get("cast", {}).get(key, {}).get("portrait"), [member.character], kind="portrait")
    try:
        board = load_board(ep_dir)
        try:
            timing = load_timing(ep_dir)
            script = [(ep.singer_of(v, line), line.text) for _, _, v, line in ep.all_lines()]
            if [(line.who, line.text) for line in timing.lines] != script:
                errors.append("timing: lyric text or singer assignment differs from episode.yaml")
            if abs(timing.duration - board.duration) > 1 / ep.fps:
                errors.append("timing: board and song timelines differ")
        except (OSError, ValueError) as exc:
            errors.append(f"timing: {exc}")
        selected = [board.shot(sid) for sid in shots] if shots is not None else board.shots
        for shot in selected:
            override = cfg.get("shot_overrides", {}).get(shot.id, {})
            visible = override.get("visible_cast", list(dict.fromkeys(shot.who + shot.background)))
            if any(k not in ep.cast for k in visible):
                errors.append(f"{shot.id}: unknown cast member")
                continue
            if set(override.get("portraits", {})) - set(visible):
                errors.append(f"{shot.id}: portrait override is not a visible character")
            ids = [ep.cast[k].character for k in visible]
            positions = {ep.cast[k].character: ep.cast[k].side for k in visible}
            first_frame = cfg.get("keyframes", {}).get(shot.id)
            check(first_frame, ids, positions)
            rear = override.get("view") == "back"
            if library and isinstance(first_frame, str) and first_frame.startswith("asset:"):
                try:
                    rear = rear or library.record(first_frame).get("view") == "back"
                except ValueError:
                    pass
            for key in visible:
                try:
                    reference = portrait_reference(cfg, override, key)
                except KeyError:
                    reference = None
                check(reference, [ep.cast[key].character], kind="portrait")
                if rear and len(visible) == 1 and library and isinstance(reference, str) and reference.startswith("asset:"):
                    if library.record(reference).get("view") != "back":
                        errors.append(f"{shot.id}: a rear-view shot needs the character's back reference")
            if not visible:
                check(override.get("scene_reference", cfg.get("scene_reference")), [], kind="scene")
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        errors.append(f"board: {exc}")
    visual_errors = list(errors)
    from aigc_mv.directing import direction_readiness
    direction = direction_readiness(ep_dir, assets_file, cfg, shots)
    errors.extend(direction["errors"])
    audio = voice_readiness(ep_dir, assets_file)
    errors.extend(audio["errors"])
    return {"ready_for_h3_production": not errors, "gpu_started": False,
            "visual_assets_ready": not visual_errors, "visual_errors": visual_errors,
            "series_id": cfg.get("series_id"), "shared_assets_used": sorted(used),
            "direction": direction, "audio": audio, "errors": errors}


def scaffold_shared_assets(ep_dir: Path, library_path: Path, output: Path) -> dict:
    """Bind portraits by character identity; leave composition and voice review explicit."""
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    ep = load_episode(ep_dir)
    library = AssetLibrary(library_path)
    cfg = {"schema_version": 4, "mode": "production", "series_id": library.data["series_id"],
           "asset_library": os.path.relpath(library.path, output.parent), "seed_base": 1000000,
           "lead_frames": 8, "lock_guide_audio": True, "cast": {}, "keyframes": {},
           "shot_overrides": {}, "directing_plan": "direction.json", "motion_library": None,
           "audio_cast": {"voices": {}, "review": {"status": "pending"}}}
    for key, member in ep.cast.items():
        profile = library.data.get("characters", {}).get(member.character)
        if not profile:
            profile = library.character_profile(member.character, name_cn=member.name_cn)
        cfg["cast"][key] = {"portrait": profile.get("portrait"),
                            "description": profile.get("description", member.name_cn)}
    for _, _, verse, line in ep.all_lines():
        member = ep.cast[ep.singer_of(verse, line)]
        profile = library.data.get("characters", {}).get(member.character) or library.character_profile(
            member.character, name_cn=member.name_cn
        )
        cfg["audio_cast"]["voices"].setdefault(member.character,
            {"voice_id": None, "reference": None, "vocals": f"audio/{member.character}_vocals.wav",
             "direction": profile.get("voice_direction", "")})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return cfg


def pack_library(library_path: Path, output: Path) -> dict:
    """Portable backup of catalog plus deduplicated objects, without episode lyrics."""
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    library = AssetLibrary(library_path)
    objects = {}
    for key in library.data["assets"]:
        path = library.resolve("asset:" + key)
        objects[library.data["assets"][key]["path"]] = path
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_STORED) as archive:
        archive.write(library.path, "catalog.json")
        for relative, path in sorted(objects.items()):
            archive.write(path, relative)
    return {"archive": str(output), "assets": len(library.data["assets"]),
            "unique_objects": len(objects), "sha256": file_hash(output)}


def unpack_library(archive_path: Path, target: Path) -> Path:
    """Restore into a new folder, verifying every object before publishing it."""
    target = Path(target).resolve()
    if target.exists():
        raise FileExistsError(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as temporary:
        stage = Path(temporary) / "library"
        stage.mkdir()
        with zipfile.ZipFile(archive_path) as archive:
            entries = archive.infolist()
            if len({x.filename for x in entries}) != len(entries):
                raise ValueError("Duplicate archive paths")
            data = json.loads(archive.read("catalog.json"))
            paths = {r["path"] for r in data["assets"].values()}
            if {x.filename for x in entries} != paths | {"catalog.json"}:
                raise ValueError("Archive entries differ from the asset catalog")
            if sum(x.file_size for x in entries) > 2 * 1024**3:
                raise ValueError("Asset archive exceeds the 2 GiB import limit")
            for relative in paths:
                path = (stage / relative).resolve()
                if not relative.startswith("objects/") or not path.is_relative_to(stage):
                    raise ValueError("Unsafe object path in asset archive")
                path.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(relative) as source, path.open("xb") as output:
                    shutil.copyfileobj(source, output)
                path.chmod(0o444)
            (stage / "catalog.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        library = AssetLibrary(stage / "catalog.json")
        for key in library.data["assets"]:
            library.resolve("asset:" + key)
        stage.rename(target)
    return target / "catalog.json"
