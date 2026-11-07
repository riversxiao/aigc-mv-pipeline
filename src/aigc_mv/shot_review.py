"""Evidence-bearing take review and one-change retake proposals; never submits jobs."""
from __future__ import annotations

import json
from pathlib import Path

from aigc_mv.directing import REVIEW_CRITERIA
from aigc_mv.shared_assets import file_hash


def _take(ep_dir: Path, shot: str, job_id: str):
    index = ep_dir/"h3/shot_takes.json"
    data = json.loads(index.read_text())
    matches = [r for r in data.get(shot, []) if r["job_id"] == job_id]
    if len(matches) != 1:
        raise ValueError("Select exactly one existing shot/job ID")
    take = matches[0]
    path = (ep_dir/take["file"]).resolve()
    if not path.is_relative_to(ep_dir.resolve()) or file_hash(path) != take["sha256"]:
        raise ValueError("The reviewed take changed")
    return index, data, take


def record_review(ep_dir: Path, shot: str, job_id: str, review_file: Path) -> dict:
    index, data, take = _take(ep_dir, shot, job_id)
    review = json.loads(review_file.read_text())
    if not isinstance(review, dict):
        raise ValueError("Review must be a JSON object")
    if review.get("job_id") != job_id or review.get("video_sha256") != take["sha256"]:
        raise ValueError("Review must identify the exact job and video SHA256")
    verdict = review.get("verdict")
    if verdict not in ("keep", "retake", "post", "reject"):
        raise ValueError("Review verdict must be keep, retake, post or reject")
    required = take.get("review_contract", {}).get("criteria", REVIEW_CRITERIA)
    checks = review.get("checks", {})
    if not isinstance(checks, dict):
        raise ValueError("Review checks must map criterion names to status and evidence")
    for key in required:
        check = checks.get(key, {})
        if not isinstance(check, dict) or check.get("status") not in ("pass", "fail") or not isinstance(check.get("evidence"), str) or not check["evidence"].strip():
            raise ValueError(f"{key}: record pass/fail and observed evidence (time/frame where relevant)")
    passed = all(checks[key]["status"] == "pass" for key in required)
    if verdict == "keep" and not passed:
        raise ValueError("A kept take must pass every required review criterion")
    if verdict == "retake" and passed:
        raise ValueError("A retake needs a concrete failed criterion")
    if take.get("review") != review:
        take.setdefault("review_history", []).append(review)
    take.update(review=review, criteria_status={k:checks[k]["status"] for k in required},
                visual_status="pass" if verdict == "keep" else "unreviewed",
                identity_status="pass" if verdict == "keep" else "unreviewed")
    temporary = index.with_suffix(".partial")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n")
    temporary.replace(index)
    return take


def review_passed(take: dict) -> bool:
    """New contracts cannot be approved by the old visual/identity flags alone."""
    contract = take.get("review_contract")
    if not contract:
        return True  # Legacy accepted footage retains its existing rules.
    expected = set(REVIEW_CRITERIA) if take.get("sung") else {"identity","performance","hands_props","continuity"}
    if not expected.issubset(contract.get("criteria", [])):
        return False
    review = take.get("review", {})
    if review.get("verdict") != "keep" or review.get("job_id") != take.get("job_id") or review.get("video_sha256") != take.get("sha256"):
        return False
    checks = review.get("checks", {})
    return isinstance(checks, dict) and all(isinstance(checks.get(k),dict)
               and checks[k].get("status") == "pass" and isinstance(checks[k].get("evidence"), str)
               and checks[k]["evidence"].strip() for k in contract["criteria"])


def retake_plan(ep_dir: Path, shot: str, job_id: str, proposal_file: Path, output: Path) -> dict:
    if output.exists():
        raise FileExistsError(output)
    _, _, take = _take(ep_dir, shot, job_id)
    review = take.get("review", {})
    if review.get("verdict") != "retake":
        raise ValueError("Record an evidence-bearing retake review first")
    if review.get("job_id") != job_id or review.get("video_sha256") != take["sha256"]:
        raise ValueError("Retake review no longer matches this job and video")
    proposal = json.loads(proposal_file.read_text())
    changes = proposal.get("changes", [])
    if len(changes) != 1 or not isinstance(changes[0],dict) or not changes[0].get("field") or "value" not in changes[0]:
        raise ValueError("A diagnostic retake proposal changes exactly one named field")
    if not isinstance(proposal.get("hypothesis"), str) or not proposal["hypothesis"].strip():
        raise ValueError("Record a testable hypothesis, not an asserted hidden-model cause")
    result = {"status":"proposal_only", "gpu_started":False, "submitted":False,
              "parent_job_id":job_id, "parent_video_sha256":take["sha256"],
              "failed_criteria":{k:v for k,v in review["checks"].items() if v["status"]=="fail"},
              "hypothesis":proposal["hypothesis"], "changes":changes,
              "preserve":take.get("generation_contract", {}),
              "review_contract":take.get("review_contract", {}),
              "note":"Prepare the changed configuration and recompile; do not resubmit an uncertain prior job."}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    return result
