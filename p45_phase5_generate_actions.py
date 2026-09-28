from pathlib import Path
import json
from datetime import datetime, timezone

ROOT = Path(".").resolve()
TARGET = ROOT / "بلبل-الجديد"
ACTIONS_FILE = ROOT / "plans/repair-actions.json"
OUT_FILE = ROOT / "plans/repair-actions-generated.json"
REPORT_FILE = ROOT / "reports/p45-phase5-generation-report.json"
MIGRATION_FILE = ROOT / "plans/p45-engine-repair-migration-phase5.json"

if not TARGET.is_dir():
    raise SystemExit("STOP: بلبل-الجديد غير موجود.")

if not ACTIONS_FILE.is_file():
    raise SystemExit("STOP: plans/repair-actions.json غير موجود.")

plan_data = json.loads(ACTIONS_FILE.read_text(encoding="utf-8"))

if not isinstance(plan_data, dict):
    raise SystemExit("STOP: repair-actions.json يجب أن يكون كائنًا.")

actions = plan_data.get("actions")

if not isinstance(actions, list):
    raise SystemExit("STOP: مفتاح actions غير موجود أو ليس قائمة.")

if not actions:
    raise SystemExit("STOP: قائمة actions فارغة.")

from engine.repair_generator import RepairGenerator

generator = RepairGenerator("بلبل-الجديد")

generated = []
failures = []

for action in actions:
    item = dict(action)

    target = item.get("target")
    design_type = item.get("design_type") or item.get("repair_type")

    if not target:
        failures.append({
            "action_id": item.get("action_id"),
            "reason": "Missing target"
        })
        generated.append(item)
        continue

    # Phase 5: لا ننفذ أي تعديل.
    # نحتاج ملفًا واحدًا لكل RepairAction.
    target_path = TARGET / target

    if not target_path.is_file():
        failures.append({
            "action_id": item.get("action_id"),
            "target": target,
            "reason": "Target file not found"
        })
        generated.append(item)
        continue

    old_text = target_path.read_text(encoding="utf-8")

    try:
        result = generator.generate(
            action={
                **item,
                "old_text": old_text,
                "design_type": design_type,
            },
            source_text=old_text,
        )

        if isinstance(result, dict):
            new_text = result.get("new_text")
        else:
            new_text = getattr(result, "new_text", None)

        if not new_text:
            raise ValueError("Generator returned empty new_text.")

        if new_text == old_text:
            raise ValueError("Generator produced no change.")

        item["old_text"] = old_text
        item["new_text"] = new_text
        item["generation_status"] = "GENERATED"
        item["execution_allowed"] = False
        item["generated_at"] = datetime.now(timezone.utc).isoformat()

    except Exception as exc:
        item["generation_status"] = "FAILED"
        item["execution_allowed"] = False
        failures.append({
            "action_id": item.get("action_id"),
            "target": target,
            "reason": str(exc),
        })

    generated.append(item)

OUT_FILE.write_text(
    json.dumps(generated, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

report = {
    "phase": 5,
    "status": "GENERATION_ONLY",
    "execution_allowed": False,
    "total_actions": len(generated),
    "generated": sum(
        1 for x in generated
        if x.get("generation_status") == "GENERATED"
    ),
    "failed": len(failures),
    "failures": failures,
    "source": str(ACTIONS_FILE),
    "output": str(OUT_FILE),
    "generated_at": datetime.now(timezone.utc).isoformat(),
}

REPORT_FILE.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

migration = {
    "migration": "P45-ENGINE-REPAIR-005",
    "phase": 5,
    "status": "GENERATION_ONLY",
    "implemented": [
        "source target resolution",
        "RepairAction generation attempt",
        "old_text capture from real target",
        "new_text generation",
        "generation report",
    ],
    "not_implemented": [
        "snapshot",
        "approval mutation",
        "target modification",
        "repair application",
        "behavioral verification",
        "re-analysis",
        "final report",
    ],
    "safety_rule": (
        "Generated RepairActions remain non-executable. "
        "No target file was modified."
    ),
}

MIGRATION_FILE.write_text(
    json.dumps(migration, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print("======================================")
print("P45 PHASE 5 — REPAIR ACTION GENERATION")
print(f"ACTIONS: {len(generated)}")
print(
    "GENERATED:",
    sum(1 for x in generated if x.get("generation_status") == "GENERATED")
)
print("FAILED:", len(failures))
print("EXECUTION_ALLOWED: False")
print(f"GENERATED ACTIONS: {OUT_FILE}")
print(f"REPORT: {REPORT_FILE}")
print(f"MIGRATION: {MIGRATION_FILE}")
print("TARGET MODIFICATION: NONE")
print("======================================")

if failures:
    print("\n--- GENERATION FAILURES ---")
    for failure in failures:
        print(json.dumps(failure, ensure_ascii=False))

    raise SystemExit(2)

print("STATUS: REPAIR_ACTIONS_GENERATED")
