from pathlib import Path
import json
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
ENGINE = ROOT / "engine"
PLAN = ROOT / "plans" / "execution-plan.json"
REPORT = ROOT / "reports" / "p45-engine-repair-report.json"

def utc():
    return datetime.now(timezone.utc).isoformat()

def read(path):
    return path.read_text(encoding="utf-8")

def write(path, text):
    path.write_text(text, encoding="utf-8")

def patch_exact(path, old, new, label):
    text = read(path)

    count = text.count(old)

    if count == 0:
        return {
            "label": label,
            "status": "NOT_APPLIED",
            "reason": "EXACT_ANCHOR_NOT_FOUND",
            "file": str(path.relative_to(ROOT)),
        }

    if count != 1:
        return {
            "label": label,
            "status": "NOT_APPLIED",
            "reason": f"EXACT_ANCHOR_OCCURS_{count}_TIMES",
            "file": str(path.relative_to(ROOT)),
        }

    write(path, text.replace(old, new, 1))

    return {
        "label": label,
        "status": "APPLIED",
        "file": str(path.relative_to(ROOT)),
    }

def run(cmd):
    p = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    return {
        "command": cmd,
        "returncode": p.returncode,
        "stdout": p.stdout[-4000:],
        "stderr": p.stderr[-4000:],
    }

def main():
    results = []

    required = [
        ROOT / "repair-repository.py",
        ENGINE / "repair.py",
        ENGINE / "approval.py",
        ENGINE / "execution_log.py",
    ]

    missing = [str(p) for p in required if not p.exists()]

    if missing:
        print("P45_ENGINE_REPAIR_ABORTED")
        print("Missing:")
        for x in missing:
            print(x)
        sys.exit(2)

    print("=== P45 ENGINE REPAIR ===")
    print("ROOT:", ROOT)
    print("TIME:", utc())

    # ---------------------------------------------------------
    # 1. RepairAction model
    # ---------------------------------------------------------
    contracts = ENGINE / "contracts.py"

    if contracts.exists():
        text = read(contracts)

        if "class RepairAction" not in text:
            print("[!] RepairAction class not found.")
            print("[!] This stage is intentionally not guessed.")
            print("[!] STOP — inspect contracts.py before modifying it.")
            sys.exit(3)

        print("[OK] RepairAction model exists.")

    # ---------------------------------------------------------
    # 2. Validate current approval implementation
    # ---------------------------------------------------------
    approval = ENGINE / "approval.py"
    approval_text = read(approval)

    required_approval_symbols = [
        "class ApprovalGate",
        "def approve",
        "def require_approved",
    ]

    for symbol in required_approval_symbols:
        if symbol not in approval_text:
            print("[!] Missing approval symbol:", symbol)
            sys.exit(4)

    print("[OK] ApprovalGate contract exists.")

    # ---------------------------------------------------------
    # 3. Validate exact repair engine
    # ---------------------------------------------------------
    repair = ENGINE / "repair.py"
    repair_text = read(repair)

    required_repair_symbols = [
        "class DeepRepairEngine",
        "def apply_exact_change",
        "approved=True",
    ]

    for symbol in required_repair_symbols:
        if symbol not in repair_text:
            print("[!] Missing repair symbol:", symbol)
            sys.exit(5)

    print("[OK] DeepRepairEngine contract exists.")

    # ---------------------------------------------------------
    # 4. Repair CLI: non-zero exit behavior
    #
    # We do NOT blindly rewrite the CLI.
    # First locate the known NOT_EXECUTED / FAILED paths.
    # ---------------------------------------------------------
    cli = ROOT / "repair-repository.py"
    cli_text = read(cli)

    if "NOT_EXECUTED" not in cli_text:
        print("[!] CLI NOT_EXECUTED path not found.")
        sys.exit(6)

    if "Status: FAILED" not in cli_text:
        print("[!] CLI FAILED path not found.")
        sys.exit(7)

    print("[OK] CLI failure paths detected.")

    # ---------------------------------------------------------
    # 5. Execution-log contract
    # ---------------------------------------------------------
    log_text = read(ENGINE / "execution_log.py")

    for symbol in [
        "record_phase",
        "record_repair",
    ]:
        if symbol not in log_text:
            print("[!] Missing execution-log symbol:", symbol)
            sys.exit(8)

    print("[OK] Execution log API detected.")

    # ---------------------------------------------------------
    # 6. Compile current engine BEFORE migration
    # ---------------------------------------------------------
    compile_targets = [
        "repair-repository.py",
        "engine/approval.py",
        "engine/repair.py",
        "engine/contracts.py",
        "engine/execution_log.py",
    ]

    before = run([sys.executable, "-m", "py_compile", *compile_targets])
    results.append({"stage": "compile_before", **before})

    if before["returncode"] != 0:
        print("[!] Current P45 does not compile.")
        print(before["stderr"])
        sys.exit(9)

    print("[OK] Current P45 compiles.")

    # ---------------------------------------------------------
    # 7. Write an explicit migration specification.
    #
    # This is deliberately data-driven so future assistants can
    # continue from a durable artifact instead of chat history.
    # ---------------------------------------------------------
    migration = {
        "migration": "P45-ENGINE-REPAIR-001",
        "created_at": utc(),
        "status": "DISCOVERED",
        "objective": "Close execution-architecture gaps discovered during بلبل forced-repair experiments.",
        "gaps": [
            "GAP-CANDIDATE-EXEC-001",
            "GAP-CANDIDATE-EXEC-002",
            "GAP-CANDIDATE-EXEC-003",
            "GAP-CANDIDATE-EXEC-004",
            "GAP-CANDIDATE-EXEC-005",
            "GAP-CANDIDATE-EXEC-006",
            "GAP-CANDIDATE-EXEC-007",
            "GAP-CANDIDATE-EXEC-008",
            "GAP-CANDIDATE-EXEC-009",
            "GAP-CANDIDATE-EXEC-010",
            "GAP-CANDIDATE-EXEC-011",
            "GAP-CANDIDATE-EXEC-012",
        ],
        "required_lifecycle": [
            "CANDIDATE",
            "APPROVAL",
            "REPAIR_ACTION",
            "SNAPSHOT",
            "EXACT_REPAIR",
            "TEST",
            "VERIFY",
            "RE_ANALYZE",
            "REPORT",
        ],
        "rules": [
            "Approved candidate must resolve its own target when unambiguous.",
            "Multi-file candidate must expand into independent repair actions.",
            "Repair action must remain bound to candidate_id.",
            "FAILED must return non-zero exit status.",
            "NOT_EXECUTED must return non-zero exit status.",
            "Exact repair must never write when old_text is absent or duplicated.",
            "Exact verification does not imply behavioral verification.",
            "Applied does not imply verified.",
            "No repair strategy may be invented from diagnosis alone.",
        ],
        "next_implementation_order": [
            "RepairAction schema",
            "candidate_to_actions",
            "target_resolution",
            "multi_file_execution",
            "candidate_action_binding",
            "exit_codes",
            "execution_log",
            "test_layer",
            "exact_verification",
            "behavioral_verification",
            "re_analysis",
            "final_report",
        ],
    }

    PLAN.parent.mkdir(parents=True, exist_ok=True)

    # Preserve existing execution plan; migration is separate.
    migration_path = ROOT / "plans" / "p45-engine-repair-migration.json"
    migration_path.write_text(
        json.dumps(migration, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("[OK] Migration specification written:")
    print(migration_path)

    # ---------------------------------------------------------
    # 8. Final compile after artifact creation
    # ---------------------------------------------------------
    after = run([sys.executable, "-m", "py_compile", *compile_targets])
    results.append({"stage": "compile_after", **after})

    status = "READY_FOR_CONTROLLED_IMPLEMENTATION"

    if after["returncode"] != 0:
        status = "FAILED"

    report = {
        "report": "P45-ENGINE-REPAIR-001",
        "timestamp": utc(),
        "status": status,
        "results": results,
        "migration_file": str(migration_path.relative_to(ROOT)),
        "important": [
            "No بلبل source file was modified.",
            "No repair candidate was fabricated.",
            "No old_text/new_text was invented.",
            "Existing P45 source was modified only if an exact patch is explicitly implemented.",
        ],
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print()
    print("======================================")
    print("P45_ENGINE_REPAIR_001:", status)
    print("REPORT:", REPORT)
    print("MIGRATION:", migration_path)
    print("======================================")

    sys.exit(0 if status != "FAILED" else 10)

if __name__ == "__main__":
    main()
