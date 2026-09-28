from pathlib import Path
from datetime import datetime, timezone
import json

ROOT = Path(__file__).resolve().parent
PLAN = ROOT / "بلبل-الجديد" / "plans" / "execution-plan.json"
OUT = ROOT / "plans" / "repair-actions.json"
MIGRATION = ROOT / "plans" / "p45-engine-repair-migration-phase3.json"
REPORT = ROOT / "reports" / "p45-phase3-repair-report.json"


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


print("=== P45 PHASE 3 CANDIDATE -> REPAIR ACTIONS ===")
print("TIME:", now())

if not PLAN.exists():
    print("[!] STOP: بلبل execution-plan.json غير موجود.")
    raise SystemExit(1)

data = json.loads(PLAN.read_text(encoding="utf-8"))

candidates = data.get("repair_candidates")

if not isinstance(candidates, list):
    print("[!] STOP: repair_candidates ليست قائمة.")
    raise SystemExit(1)

approved = [
    c for c in candidates
    if c.get("status") == "APPROVED"
    and c.get("approved") is True
]

print(f"[+] Approved candidates found: {len(approved)}")

if not approved:
    print("[!] STOP: لا توجد candidates معتمدة.")
    raise SystemExit(1)


actions = []

for candidate in approved:
    cid = candidate.get("candidate_id")
    target = candidate.get("target")
    reason = candidate.get("reason")

    if not cid or not target or not reason:
        print(f"[!] STOP: candidate ناقص بيانات أساسية: {cid}")
        raise SystemExit(1)

    targets = [
        x.strip()
        for x in target.split("+")
        if x.strip()
    ]

    for index, concrete_target in enumerate(targets, start=1):
        action_id = f"{cid}:ACTION-{index:02d}"

        action = {
            "action_id": action_id,
            "candidate_id": cid,
            "target": concrete_target,
            "reason": reason,
            "title": candidate.get("title"),
            "classification": candidate.get("classification"),
            "severity": candidate.get("severity"),
            "status": "PLANNED",
            "approval": {
                "status": "APPROVED",
                "approved": True,
                "approved_at": candidate.get("approved_at"),
            },
            "evidence": candidate.get("evidence", []),
            "verification": candidate.get("verification", []),

            # Intentionally empty:
            # P45 must not invent source/replacement code.
            "old_text": None,
            "new_text": None,

            "snapshot_required": True,
            "execution_allowed": False,

            "blocking_requirements": [
                "Concrete exact old_text must be supplied from evidence.",
                "Concrete exact new_text must be supplied from an approved repair design.",
                "Snapshot must exist before application.",
                "Exact verification must pass after application.",
                "Behavioral verification is required where candidate verification demands runtime proof.",
            ],
        }

        actions.append(action)


report = {
    "report": "P45-PHASE3-REPAIR-ACTIONS-001",
    "timestamp": now(),
    "status": "STRUCTURED_NOT_EXECUTABLE",
    "source_plan": str(PLAN),
    "approved_candidates": len(approved),
    "repair_actions": len(actions),
    "execution_allowed": False,
    "actions": [
        {
            "action_id": a["action_id"],
            "candidate_id": a["candidate_id"],
            "target": a["target"],
            "status": a["status"],
            "execution_allowed": a["execution_allowed"],
            "missing": [
                "old_text",
                "new_text",
            ],
        }
        for a in actions
    ],
    "next_phase": [
        "evidence-backed exact repair design",
        "old_text/new_text binding",
        "multi-file action validation",
        "snapshot binding",
        "execution test harness",
        "exact verification",
        "behavioral verification",
        "re-analysis",
        "final report",
    ],
}

migration = {
    "migration": "P45-ENGINE-REPAIR-003",
    "phase": 3,
    "timestamp": now(),
    "status": "STRUCTURED_NOT_EXECUTABLE",
    "implemented": [
        "read approved candidates from بلبل execution plan",
        "candidate to RepairAction expansion",
        "multi-file candidate expansion",
        "candidate-bound action identity",
        "approval metadata preservation",
        "evidence preservation",
        "verification requirements preservation",
        "execution safety gate remains false",
    ],
    "explicitly_not_implemented": [
        "inventing old_text",
        "inventing new_text",
        "automatic code generation",
        "execution against بلبل",
        "snapshot creation",
        "behavioral verification",
        "re-analysis",
        "final report",
    ],
    "safety_rule": (
        "Approved candidates are structured into RepairActions, "
        "but remain non-executable until each action has an "
        "evidence-backed exact old_text/new_text pair."
    ),
}

write_json(OUT, {
    "schema": "P45-RepairActions-v1",
    "generated_at": now(),
    "source_plan": str(PLAN),
    "execution_allowed": False,
    "actions": actions,
})

write_json(REPORT, report)
write_json(MIGRATION, migration)

print()
print("======================================")
print("P45_PHASE3_ACTIONS: STRUCTURED")
print("ACTIONS:", len(actions))
print("EXECUTION_ALLOWED: False")
print("REPAIR ACTIONS:", OUT)
print("REPORT:", REPORT)
print("MIGRATION:", MIGRATION)
print("======================================")
