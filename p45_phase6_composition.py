from pathlib import Path
import json
import hashlib
import tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
GENERATED = ROOT / "plans" / "repair-actions-generated.json"
OUT = ROOT / "plans" / "repair-composition-plan.json"
REPORT = ROOT / "reports" / "p45-phase6-composition-report.json"

TARGET_ROOT = ROOT / "بلبل-الجديد"


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    print("=== P45 PHASE 6 — COMPOSITION / RE-GENERATION GATE ===")
    print(f"TIME: {now()}")

    if not GENERATED.exists():
        raise SystemExit(f"STOP: missing {GENERATED}")

    data = json.loads(GENERATED.read_text(encoding="utf-8"))
    actions = data.get("actions")

    if not isinstance(actions, list) or not actions:
        raise SystemExit("STOP: generated actions are missing or empty.")

    grouped = {}
    for action in actions:
        target = action.get("target")
        if not target:
            raise SystemExit(
                f"STOP: action has no target: {action.get('action_id')}"
            )
        grouped.setdefault(target, []).append(action)

    composition = []
    conflicts = []

    for target, target_actions in grouped.items():
        target_path = TARGET_ROOT / target

        if not target_path.is_file():
            raise SystemExit(
                f"STOP: target file does not exist: {target_path}"
            )

        original = target_path.read_text(encoding="utf-8")
        original_sha = sha256_text(original)

        entry = {
            "target": target,
            "original_sha256": original_sha,
            "action_count": len(target_actions),
            "actions": [],
            "status": "READY",
            "execution_allowed": False,
        }

        working = original

        # Preserve generated-action order.
        for index, action in enumerate(target_actions, 1):
            action_id = action.get("action_id")
            old_text = action.get("old_text")
            new_text = action.get("new_text")

            if not old_text or not new_text:
                entry["status"] = "BLOCKED"
                entry["actions"].append({
                    "action_id": action_id,
                    "step": index,
                    "status": "MISSING_EXECUTABLE_TEXT",
                })
                continue

            before_sha = sha256_text(working)
            matches = working.count(old_text)

            step = {
                "action_id": action_id,
                "step": index,
                "before_sha256": before_sha,
                "old_text": old_text,
                "new_text": new_text,
                "match_count": matches,
            }

            if matches != 1:
                step["status"] = "BLOCKED"
                entry["status"] = "BLOCKED"
                entry["actions"].append(step)
                continue

            working = working.replace(old_text, new_text, 1)

            after_sha = sha256_text(working)

            step["after_sha256"] = after_sha
            step["status"] = "COMPOSED"

            entry["actions"].append(step)

        if len(target_actions) > 1:
            conflicts.append({
                "target": target,
                "action_count": len(target_actions),
                "status": (
                    "RESOLVED_IN_MEMORY"
                    if entry["status"] == "READY"
                    else "CONFLICT_REMAINS"
                ),
            })

        entry["composed_sha256"] = sha256_text(working)
        entry["execution_allowed"] = False
        composition.append(entry)

    status = (
        "COMPOSITION_READY_NO_EXECUTION"
        if all(x["status"] == "READY" for x in composition)
        else "BLOCKED_COMPOSITION"
    )

    result = {
        "schema": "P45-RepairCompositionPlan-v1",
        "phase": 6,
        "created_at": now(),
        "status": status,
        "execution_allowed": False,
        "target_modification": "NONE",
        "rule": (
            "Composition is performed only in memory. "
            "Original target files remain untouched. "
            "Composed actions require later snapshot, approval binding, "
            "exact verification, and execution gates."
        ),
        "targets": composition,
        "conflicts": conflicts,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    OUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report = {
        "phase": 6,
        "status": status,
        "generated_actions": len(actions),
        "targets": len(grouped),
        "conflicts": len(conflicts),
        "execution_allowed": False,
        "target_modification": "NONE",
        "composition_mode": "IN_MEMORY_ONLY",
        "created_at": now(),
    }

    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("=" * 38)
    print(f"GENERATED ACTIONS: {len(actions)}")
    print(f"TARGETS: {len(grouped)}")
    print(f"CONFLICT GROUPS: {len(conflicts)}")
    print(f"STATUS: {status}")
    print("COMPOSITION: IN-MEMORY ONLY")
    print("TARGET MODIFICATION: NONE")
    print("EXECUTION_ALLOWED: False")
    print(f"PLAN: {OUT}")
    print(f"REPORT: {REPORT}")
    print("=" * 38)

    for item in conflicts:
        print(
            f"CONFLICT: {item['target']} | "
            f"ACTIONS={item['action_count']} | "
            f"{item['status']}"
        )


if __name__ == "__main__":
    main()
