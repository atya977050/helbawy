from pathlib import Path
from datetime import datetime, timezone
import json

ROOT = Path(__file__).resolve().parent
PLAN = ROOT / "بلبل-الجديد" / "plans" / "execution-plan.json"
ACTIONS = ROOT / "plans" / "repair-actions.json"

OUT = ROOT / "plans" / "repair-design-manifest.json"
REPORT = ROOT / "reports" / "p45-phase4-design-report.json"
MIGRATION = ROOT / "plans" / "p45-engine-repair-migration-phase4.json"


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if not PLAN.exists() or not ACTIONS.exists():
    print("[!] STOP: Phase 3 outputs are missing.")
    raise SystemExit(1)


plan = json.loads(PLAN.read_text(encoding="utf-8"))
actions_data = json.loads(ACTIONS.read_text(encoding="utf-8"))

candidates = plan.get("repair_candidates", [])
actions = actions_data.get("actions", [])

if len(candidates) != 6:
    print(f"[!] STOP: expected 6 approved candidates, found {len(candidates)}")
    raise SystemExit(1)

if len(actions) != 7:
    print(f"[!] STOP: expected 7 RepairActions, found {len(actions)}")
    raise SystemExit(1)


designs = {
    "P45-REPAIR-CANDIDATE-RC-WEBRTC-001": {
        "design_id": "DESIGN-WEBRTC-001",
        "type": "exact_code_insertion",
        "target": "public/app.js",
        "intent": "Construct RTCPeerConnection before lifecycle methods use peerConnection.",
        "depends_on": [],
        "requires_exact_source_anchor": True,
        "old_text": None,
        "new_text": None,
        "design_status": "DESIGN_ONLY",
    },

    "P45-REPAIR-CANDIDATE-RC-SIGNALING-001": {
        "design_id": "DESIGN-SIGNALING-001",
        "type": "multi_file_signaling_contract",
        "targets": [
            "server.js",
            "public/app.js",
        ],
        "intent": "Create explicit Socket.IO signaling events connecting offer, answer and ICE exchange.",
        "depends_on": [
            "DESIGN-WEBRTC-001",
            "DESIGN-WEBRTC-002",
        ],
        "requires_exact_source_anchor": True,
        "old_text": None,
        "new_text": None,
        "design_status": "DESIGN_ONLY",
    },

    "P45-REPAIR-CANDIDATE-RC-MEDIA-UI-001": {
        "design_id": "DESIGN-MEDIA-UI-001",
        "type": "dom_target_insertion",
        "target": "public/index.html",
        "intent": "Provide a remote video DOM element compatible with remoteVideo.srcObject.",
        "depends_on": [],
        "requires_exact_source_anchor": True,
        "old_text": None,
        "new_text": None,
        "design_status": "DESIGN_ONLY",
    },

    "P45-REPAIR-CANDIDATE-RC-MEDIA-LIFECYCLE-001": {
        "design_id": "DESIGN-MEDIA-LIFECYCLE-001",
        "type": "media_track_binding",
        "target": "public/app.js",
        "intent": "Attach captured local audio/video tracks to the peer connection.",
        "depends_on": [
            "DESIGN-WEBRTC-001",
        ],
        "requires_exact_source_anchor": True,
        "old_text": None,
        "new_text": None,
        "design_status": "DESIGN_ONLY",
    },

    "P45-REPAIR-CANDIDATE-RC-WEBRTC-002": {
        "design_id": "DESIGN-WEBRTC-002",
        "type": "webrtc_negotiation_lifecycle",
        "target": "public/app.js",
        "intent": "Implement offer/answer, local/remote descriptions and ICE candidate lifecycle.",
        "depends_on": [
            "DESIGN-WEBRTC-001",
            "DESIGN-MEDIA-LIFECYCLE-001",
        ],
        "requires_exact_source_anchor": True,
        "old_text": None,
        "new_text": None,
        "design_status": "DESIGN_ONLY",
    },

    "P45-REPAIR-CANDIDATE-RC-RUNTIME-001": {
        "design_id": "DESIGN-RUNTIME-001",
        "type": "runtime_consistency_verification",
        "target": "public/app.js",
        "intent": "Verify that ontrack executes only against an initialized peer connection and renders the remote stream.",
        "depends_on": [
            "DESIGN-WEBRTC-001",
            "DESIGN-MEDIA-UI-001",
        ],
        "requires_exact_source_anchor": False,
        "old_text": None,
        "new_text": None,
        "design_status": "VERIFICATION_ONLY",
    },
}


manifest_actions = []

for action in actions:
    cid = action["candidate_id"]

    if cid not in designs:
        print("[!] STOP: no design for", cid)
        raise SystemExit(1)

    design = designs[cid]

    item = {
        "action_id": action["action_id"],
        "candidate_id": cid,
        "target": action["target"],
        "reason": action["reason"],
        "design": design,
        "approval": action["approval"],
        "evidence": action["evidence"],
        "verification": action["verification"],
        "execution_allowed": False,
        "status": "DESIGN_ONLY",
    }

    manifest_actions.append(item)


manifest = {
    "schema": "P45-RepairDesignManifest-v1",
    "generated_at": now(),
    "source_plan": str(PLAN),
    "source_actions": str(ACTIONS),
    "status": "DESIGN_ONLY",
    "execution_allowed": False,
    "rule": "No old_text/new_text is executable until exact source anchors are verified against the current target files.",
    "actions": manifest_actions,
}


report = {
    "report": "P45-PHASE4-DESIGN-001",
    "timestamp": now(),
    "status": "DESIGN_ONLY",
    "approved_candidates": len(candidates),
    "repair_actions": len(actions),
    "designs": len(designs),
    "execution_allowed": False,
    "important_findings": [
        "WebRTC construction, media attachment and negotiation are dependent operations.",
        "Socket.IO signaling spans server.js and public/app.js.",
        "Remote video requires a DOM target in public/index.html.",
        "RUNTIME-001 is primarily a verification concern, not an independent code insertion.",
    ],
    "next_phase": [
        "verify exact source anchors",
        "derive exact old_text blocks",
        "define evidence-backed new_text",
        "detect overlapping modifications",
        "bind designs to RepairActions",
        "snapshot before application",
    ],
}


migration = {
    "migration": "P45-ENGINE-REPAIR-004",
    "phase": 4,
    "timestamp": now(),
    "status": "DESIGN_ONLY",
    "implemented": [
        "candidate-to-design mapping",
        "repair dependency mapping",
        "multi-file signaling design",
        "runtime verification classification",
        "execution safety remains disabled",
    ],
    "not_implemented": [
        "old_text generation",
        "new_text generation",
        "file modification",
        "snapshot",
        "repair execution",
        "behavioral verification",
        "re-analysis",
        "final report",
    ],
}


write_json(OUT, manifest)
write_json(REPORT, report)
write_json(MIGRATION, migration)

print("=== P45 PHASE 4 REPAIR DESIGN ===")
print("Approved candidates:", len(candidates))
print("Repair actions:", len(actions))
print("Designs:", len(designs))
print("STATUS: DESIGN_ONLY")
print("EXECUTION_ALLOWED: False")
print("MANIFEST:", OUT)
print("REPORT:", REPORT)
print("MIGRATION:", MIGRATION)
