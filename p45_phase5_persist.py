from pathlib import Path
import json
from datetime import datetime, timezone

from engine.repair_generator import RepairGenerator


ROOT = Path(".").resolve()
TARGET = ROOT / "بلبل-الجديد"

MANIFEST = ROOT / "plans/repair-design-manifest.json"
OUTPUT = ROOT / "plans/repair-actions-generated.json"
REPORT = ROOT / "reports/p45-phase5-generation-report.json"


def now():
    return datetime.now(timezone.utc).isoformat()


def fail(msg):
    raise SystemExit(f"STOP: {msg}")


manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
actions = manifest.get("actions")

if not isinstance(actions, list):
    fail("manifest actions is not a list")

g = RepairGenerator("بلبل-الجديد")

anchors = {
    "P45-REPAIR-CANDIDATE-RC-WEBRTC-001:ACTION-01":
        (
            "public/app.js",
            "const servers = { iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] };"
        ),

    "P45-REPAIR-CANDIDATE-RC-SIGNALING-001:ACTION-01":
        (
            "server.js",
            "server.listen(3000, () => console.log('Server running on port 3000'));"
        ),

    "P45-REPAIR-CANDIDATE-RC-SIGNALING-001:ACTION-02":
        (
            "public/app.js",
            "const socket = io();"
        ),

    "P45-REPAIR-CANDIDATE-RC-MEDIA-UI-001:ACTION-01":
        (
            "public/index.html",
            "</body>"
        ),

    "P45-REPAIR-CANDIDATE-RC-MEDIA-LIFECYCLE-001:ACTION-01":
        (
            "public/app.js",
            "localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });"
        ),

    "P45-REPAIR-CANDIDATE-RC-WEBRTC-002:ACTION-01":
        (
            "public/app.js",
            "init();"
        ),
}


generated = []
verification_only = []
target_shas = {}
failures = []

for action in actions:
    aid = action["action_id"]
    design = action.get("design") or {}
    dtype = design.get("type")

    if dtype == "runtime_consistency_verification":
        verification_only.append({
            "action_id": aid,
            "candidate_id": action.get("candidate_id"),
            "target": action.get("target"),
            "type": dtype,
            "status": "VERIFICATION_ONLY",
            "execution_allowed": False,
        })
        continue

    if aid not in anchors:
        failures.append({
            "action_id": aid,
            "status": "FAILED",
            "reason": "No exact anchor registered for generation test.",
        })
        continue

    target_name, anchor = anchors[aid]
    path = TARGET / target_name

    if not path.exists():
        failures.append({
            "action_id": aid,
            "status": "FAILED",
            "reason": f"Target does not exist: {target_name}",
        })
        continue

    source = path.read_text(encoding="utf-8")
    count = source.count(anchor)

    if count != 1:
        failures.append({
            "action_id": aid,
            "status": "FAILED",
            "reason": f"Anchor uniqueness failed: count={count}",
            "target": target_name,
        })
        continue

    action_copy = dict(action)
    action_copy["execution_allowed"] = False

    try:
        result = g.generate(
            action=action_copy,
            anchor=anchor,
        )
    except Exception as exc:
        failures.append({
            "action_id": aid,
            "status": "FAILED",
            "reason": str(exc),
            "target": target_name,
        })
        continue

    if result.old_text != anchor:
        failures.append({
            "action_id": aid,
            "status": "FAILED",
            "reason": "Generated old_text does not equal exact anchor.",
        })
        continue

    if result.new_text == result.old_text:
        failures.append({
            "action_id": aid,
            "status": "FAILED",
            "reason": "Generated new_text equals old_text.",
        })
        continue

    if result.execution_allowed is not False:
        failures.append({
            "action_id": aid,
            "status": "FAILED",
            "reason": "Generator returned execution_allowed=True.",
        })
        continue

    target_shas.setdefault(target_name, set()).add(result.before_sha256)

    generated.append({
        "action_id": result.action_id,
        "candidate_id": result.candidate_id,
        "target": result.target,
        "old_text": result.old_text,
        "new_text": result.new_text,
        "before_sha256": result.before_sha256,
        "generator": result.generator,
        "status": "GENERATED",
        "execution_allowed": False,
        "anchor_verified": True,
        "generated_at": result.generated_at,
    })


# ---------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------

target_action_counts = {}

for item in generated:
    target_action_counts.setdefault(item["target"], []).append(
        item["action_id"]
    )

conflicts = []

for target, action_ids in target_action_counts.items():
    if len(action_ids) > 1:
        conflicts.append({
            "target": target,
            "action_ids": action_ids,
            "reason": (
                "Multiple generated actions depend on the same "
                "pre-repair file state. Sequential application is unsafe "
                "without regeneration/composition against the updated source."
            ),
            "status": "CONFLICT_PENDING",
        })


if conflicts:
    execution_status = "BLOCKED_CONFLICT_PENDING"
else:
    execution_status = "GENERATED_NOT_EXECUTABLE"


output = {
    "schema": "P45-RepairActionsGenerated-v1",
    "generated_at": now(),
    "source_manifest": str(MANIFEST),
    "target_project": str(TARGET),
    "status": execution_status,
    "execution_allowed": False,
    "generated_count": len(generated),
    "verification_only_count": len(verification_only),
    "failure_count": len(failures),
    "conflict_count": len(conflicts),
    "rule": (
        "Generated actions are never executable automatically. "
        "All actions must remain bound to approved candidates and "
        "exact source SHA. Multiple actions targeting one file require "
        "composition or regeneration before application."
    ),
    "actions": generated,
    "verification_only": verification_only,
    "conflicts": conflicts,
    "failures": failures,
}

OUTPUT.write_text(
    json.dumps(output, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

report = {
    "schema": "P45-Phase5-GenerationReport-v1",
    "generated_at": now(),
    "status": execution_status,
    "generated": len(generated),
    "verification_only": len(verification_only),
    "failures": len(failures),
    "conflicts": len(conflicts),
    "target_modification": "NONE",
    "execution_allowed": False,
    "output": str(OUTPUT),
}

REPORT.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print("=== P45 PHASE 5 — PERSIST GENERATED ACTIONS ===")
print("GENERATED:", len(generated))
print("VERIFICATION_ONLY:", len(verification_only))
print("FAILURES:", len(failures))
print("CONFLICTS:", len(conflicts))
print("STATUS:", execution_status)
print("OUTPUT:", OUTPUT)
print("REPORT:", REPORT)
print("TARGET MODIFICATION: NONE")
print("EXECUTION_ALLOWED: False")

if failures:
    print("\n--- FAILURES ---")
    for item in failures:
        print(item)

if conflicts:
    print("\n--- CONFLICTS ---")
    for item in conflicts:
        print("TARGET:", item["target"])
        print("ACTIONS:", ", ".join(item["action_ids"]))
        print("STATUS:", item["status"])

print("\n======================================")
