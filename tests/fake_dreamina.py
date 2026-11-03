"""A fake dreamina-canvas (v1.2.1 JSON contract, no network) for runner tests and dry runs.

In-process: FakeDreamina()(cmd, timeout) -> (exit code, stdout, stderr); plug it into Cli(runner=...).
As a script: FAKE_DREAMINA_STATE=/path/state.json python fake_dreamina.py <args>  (state persists in that file).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SEEDANCE_2 = {
    "type": "video", "model": "seedance_2_0", "displayName": "Seedance 2.0", "aliases": ["seedance2"],
    "modes": [
        {"name": "m2v", "flags": [
            {"flag": "--duration", "required": True, "values": [str(x) for x in range(4, 16)]},
            {"flag": "--resolution", "required": False, "values": ["480P", "720P", "1080P"]},
            {"flag": "--ratio", "required": False, "values": ["16:9", "9:16", "1:1"]},
            {"flag": "--prompt", "required": True, "maxLength": 5000}],
         "references": {"min": 1, "max": 12, "types": [{"mediaType": "image", "min": 0, "max": 9},
                                                       {"mediaType": "video", "min": 0, "max": 3},
                                                       {"mediaType": "audio", "min": 0, "max": 3}],
                        "requireAnyOfTypes": ["image", "video"]}},
        {"name": "first_last_frame", "flags": [{"flag": "--duration", "required": True, "values": ["5", "10"]}],
         "references": {"min": 1, "max": 2, "types": [{"mediaType": "image", "min": 1, "max": 2}]}},
        {"name": "t2v", "flags": []},
    ],
}
SEEDANCE_1_FAST = {
    "type": "video", "model": "seedance_1_0_fast", "displayName": "Seedance 1.0 Fast",
    "modes": [{"name": "first_last_frame", "flags": [{"flag": "--duration", "values": ["5", "10"]}],
               "references": {"min": 1, "max": 2, "types": [{"mediaType": "image", "min": 1, "max": 2}]}}],
}
MP4 = b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2" + b"\x00" * 4096


def ok(data) -> tuple:
    return 0, json.dumps({"schemaVersion": "1", "ok": True, "data": data}), ""


def fail(code: int, err: dict, **extra) -> tuple:
    obj = {"schemaVersion": "1", "ok": False, "error": err}
    obj.update(extra)
    return code, json.dumps(obj), ""


def _flags(args: list) -> tuple:
    pos, fl = [], {}
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("-") and a not in ("--dry-run", "--non-interactive", "--run", "--wait", "--use"):
            fl.setdefault(a.lstrip("-"), []).append(args[i + 1])
            i += 2
        else:
            if a.startswith("-"):
                fl.setdefault(a.lstrip("-"), []).append(True)
            else:
                pos.append(a)
            i += 1
    return pos, fl


class FakeDreamina:
    def __init__(self, state: dict | None = None, models=None, logged_in=True, credits="5000",
                 polls_to_finish=1, download_works=True, fail_units=(), lose_run_response=False):
        self.s = state if state is not None else {}
        for k, v in (("nodes", {}), ("runs", {}), ("polls", {}), ("uploads", {}), ("canvases", {}), ("log", [])):
            self.s.setdefault(k, v)
        self.models = models if models is not None else [SEEDANCE_2, SEEDANCE_1_FAST]
        self.logged_in, self.credits, self.polls_to_finish = logged_in, credits, polls_to_finish
        self.download_works, self.fail_units, self.lose_run_response = download_works, set(fail_units), lose_run_response

    def __call__(self, cmd: list, timeout: float = 0) -> tuple:
        args = [a for a in cmd[1:] if a not in ("--non-interactive",)]
        if "--format" in args:
            i = args.index("--format")
            del args[i:i + 2]
        self.s["log"].append(args)
        pos, fl = _flags(args)
        head = " ".join(pos[:3])
        if pos[:1] == ["version"]:
            return ok({"version": "1.2.1"})
        if pos[:2] == ["auth", "status"]:
            return ok({"loggedIn": self.logged_in, "profile": "default", "region": "cn"})
        if not self.logged_in:
            return fail(11, {"code": "cli.authentication_required", "class": "auth_required", "requiredAction": "login"})
        if pos[:2] == ["auth", "account"]:
            return ok({"displayName": "测试用户", "availableCredits": self.credits, "userId": 1, "isVip": True,
                       "vipLevel": "高级会员"})
        if pos[:2] == ["model", "find"]:
            q = pos[2].lower()
            return ok({"items": [m for m in self.models if q in (m["model"] + m.get("displayName", "")).lower()]})
        if pos[:2] == ["model", "list"]:
            return ok({"items": self.models})
        if pos[:1] == ["model"]:
            return ok({"query": pos[1], "matches": [{"kind": "generation", "resourceType": "video",
                                                     "generation": {"model": pos[1], "mode": "m2v",
                                                                    "generationKind": "standard"}}]})
        if pos[:2] == ["canvas", "create"]:
            pid = fl["project-id"][0]
            if pid in self.s["canvases"]:
                return fail(2, {"code": "cli.conflict", "class": "invalid_input"})
            self.s["canvases"][pid] = pos[2]
            return ok({"project": {"projectId": pid, "name": pos[2], "webUrl": f"https://example.invalid/canvas/{pid}"},
                       "current": False})
        if pos[:2] == ["canvas", "ls"]:
            return ok({"items": [{"projectId": p, "name": n, "webUrl": f"https://example.invalid/canvas/{p}"}
                                 for p, n in self.s["canvases"].items()], "hasMore": False})
        if pos[:2] == ["resource", "upload"]:
            rid = fl["resource-id"][0]
            if not Path(fl["file"][0]).is_file():
                return fail(2, {"code": "cli.file_not_found"})
            self.s["uploads"][rid] = self.s["uploads"].get(rid, 0) + 1
            return ok({"resourceId": rid, "mediaType": fl["type"][0]})
        if head == "node create video":
            if "dry-run" in fl:
                return ok({"dryRun": True, "validationScope": "local"})
            nid = fl["node-id"][0]
            if nid in self.s["nodes"]:
                return fail(2, {"code": "cli.node_exists"})
            self.s["nodes"][nid] = {"title": fl["title"][0], "prompt": fl["prompt"][0], "refs": fl.get("ref", []),
                                    "duration": float(fl["duration"][0]), "mode": fl["mode"][0],
                                    "model": fl["model"][0], "resolution": fl["resolution"][0]}
            return ok({"node": {"nodeId": nid, "type": "video"},
                       "mutation": {"action": "create", "savedDraftVersion": 1,
                                    "effectiveGeneration": {"mode": fl["mode"][0], "durationSeconds": float(fl["duration"][0]),
                                                            "resolution": fl["resolution"][0]}}})
        if pos[:2] == ["node", "show"]:
            nid = fl["node-id"][0]
            n = self.s["nodes"].get(nid)
            return ok({"nodes": [{"nodeId": nid, "result": "FOUND", "node": {"nodeId": nid}} if n else
                                 {"nodeId": nid, "result": "NOT_FOUND"}]})
        if pos[:2] == ["node", "quote"]:
            items = [{"nodeId": n, "maxCredits": int(self.s["nodes"][n]["duration"] * 10)} for n in fl["node-id"]]
            return ok({"items": items, "totalMaxCredits": sum(i["maxCredits"] for i in items), "draftVersion": 1,
                       "confirmable": True, "confirmationRequired": True})
        if pos[:2] == ["node", "confirm"]:
            n = fl["node-id"][0]
            need = int(self.s["nodes"][n]["duration"] * 10)
            if int(fl["credit-ceiling"][0]) < need:
                return fail(10, {"code": "cli.generation_confirmation_required", "requiredAction": "confirm"},
                            creditConfirmation={"reason": "below_estimate", "minimumCreditCeiling": need})
            return ok({"creditConfirmationToken": "tok-" + n, "creditCeiling": int(fl["credit-ceiling"][0]),
                       "expiresAt": "2099-01-01T00:00:00Z"})
        if pos[:2] == ["node", "run"]:
            n, sid = fl["node-id"][0], fl["submit-id"][0]
            if fl.get("credit-token", [None])[0] != "tok-" + n:
                return fail(10, {"code": "cli.generation_confirmation_required", "requiredAction": "confirm"})
            self.s["runs"][sid] = self.s["runs"].get(sid, 0) + 1
            self.s["nodes"][n]["submit"] = sid
            if self.lose_run_response:
                return -1, "", "connection reset"
            return ok({"items": [{"nodeId": n, "submitId": sid, "state": "ACCEPTED", "resources": []}]})
        if pos[:2] == ["operation", "wait"]:
            sid = pos[2]
            if sid not in self.s["runs"]:
                return ok({"operationRef": sid, "state": "unknown", "resources": [],
                           "submission": {"state": "absent", "resubmittable": False, "adviceCode": "inspect",
                                          "advice": "inspect canvas"}})
            self.s["polls"][sid] = self.s["polls"].get(sid, 0) + 1
            node = next(k for k, v in self.s["nodes"].items() if v.get("submit") == sid)
            if self.s["polls"][sid] < self.polls_to_finish:
                return fail(20, {"code": "cli.operation_incomplete", "class": "operation_incomplete",
                                 "requiredAction": "resume", "retryable": False},
                            data={"operationRef": sid, "state": "running", "resources": []})
            if self.s["nodes"][node]["title"].split()[0] in self.fail_units:
                return ok({"operationRef": sid, "state": "failed", "resources": [{"resourceId": "r-" + sid, "state": "failed"}],
                           "submissionError": {"serviceCode": 4001, "message": "content rejected", "retryable": False,
                                               "requiredAction": "fix_input"}})
            return ok({"operationRef": sid, "state": "succeeded",
                       "resources": [{"resourceId": "r-" + sid, "state": "succeeded", "width": 1280, "height": 720}]})
        if pos[:2] == ["resource", "get"]:
            return ok({"resourceId": pos[2], "type": "video", "status": "success", "generationKind": "standard",
                       "video": {"width": 1280, "height": 720, "durationSeconds": 6.0, "fps": 24, "resolution": "720P"}})
        if pos[:2] == ["resource", "download"]:
            if not self.download_works:
                return fail(2, {"code": "cli.resource_type_unsupported", "class": "invalid_input",
                                "message": "only image resources can be downloaded"})
            out = Path(fl["o"][0] if "o" in fl else fl["output"][0])
            out.write_bytes(MP4)
            return ok({"resourceId": pos[2], "path": str(out), "size": len(MP4), "sha256": "0" * 64})
        return fail(2, {"code": "cli.invalid_command", "message": "fake: unknown " + " ".join(pos)})


def main() -> int:
    sp = Path(os.environ.get("FAKE_DREAMINA_STATE", "fake_dreamina_state.json"))
    state = json.loads(sp.read_text(encoding="utf-8")) if sp.is_file() else {}
    code, out, err = FakeDreamina(state, polls_to_finish=int(os.environ.get("FAKE_DREAMINA_POLLS", "2")),
                                  logged_in=os.environ.get("FAKE_DREAMINA_LOGGED_IN", "1") == "1")(["fake"] + sys.argv[1:])
    sp.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    sys.stdout.write(out + "\n")
    sys.stderr.write(err)
    return code


if __name__ == "__main__":
    sys.exit(main())
