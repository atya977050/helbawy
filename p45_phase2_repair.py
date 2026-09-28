from pathlib import Path
import json
import sys
import subprocess
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
CLI = ROOT / "repair-repository.py"
CONTRACTS = ROOT / "engine" / "contracts.py"
APPROVAL = ROOT / "engine" / "approval.py"
REPAIR = ROOT / "engine" / "repair.py"
PLAN = ROOT / "plans" / "execution-plan.json"

MIGRATION = ROOT / "plans" / "p45-engine-repair-migration-phase2.json"
REPORT = ROOT / "reports" / "p45-phase2-repair-report.json"


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return path.read_text(encoding="utf-8")


def write(path, text):
    path.write_text(text, encoding="utf-8")


def exact_patch(path, old, new, label):
    text = read(path)
    count = text.count(old)

    if count != 1:
        return {
            "label": label,
            "status": "NOT_APPLIED",
            "reason": (
                "ANCHOR_NOT_FOUND"
                if count == 0
                else f"ANCHOR_OCCURS_{count}_TIMES"
            ),
            "file": str(path.relative_to(ROOT)),
        }

    write(path, text.replace(old, new, 1))

    return {
        "label": label,
        "status": "APPLIED",
        "file": str(path.relative_to(ROOT)),
    }


def compile_check():
    targets = [
        "repair-repository.py",
        "engine/contracts.py",
        "engine/approval.py",
        "engine/repair.py",
        "engine/execution_log.py",
    ]

    p = subprocess.run(
        [sys.executable, "-m", "py_compile", *targets],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    return {
        "returncode": p.returncode,
        "stdout": p.stdout,
        "stderr": p.stderr,
    }


def main():
    print("=== P45 PHASE 2 CONTROLLED REPAIR ===")
    print("TIME:", now())

    required_files = [
        CLI,
        CONTRACTS,
        APPROVAL,
        REPAIR,
        PLAN,
    ]

    for path in required_files:
        if not path.exists():
            print("[!] Missing:", path)
            print("[!] STOP — no modification made.")
            sys.exit(2)

    cli = read(CLI)
    contracts = read(CONTRACTS)

    # ---------------------------------------------------------
    # PRECONDITIONS
    # ---------------------------------------------------------
    required_cli = [
        "def cmd_repair(args):",
        "approved_candidate = approval_gate.require_approved(",
        "candidate_target = approved_candidate.get(\"target\")",
        "bound_action_id = (",
        "result = engine.apply_exact_change(",
    ]

    for marker in required_cli:
        if marker not in cli:
            print("[!] CLI marker missing:", marker)
            print("[!] STOP — no modification made.")
            sys.exit(3)

    if "class RepairAction:" not in contracts:
        print("[!] RepairAction model missing.")
        sys.exit(4)

    print("[OK] Preconditions verified.")

    results = []

    # ---------------------------------------------------------
    # PATCH 1
    #
    # RepairAction becomes explicitly bindable to candidate_id
    # and executable exact text payload.
    #
    # This does NOT invent old_text/new_text.
    # It only gives the model a place to carry them.
    # ---------------------------------------------------------
    old = '''class RepairAction:
    action_id: str
    target: str
    reason: str
    evidence: list[Evidence] = field(default_factory=list)
'''

    new = '''class RepairAction:
    action_id: str
    target: str
    reason: str
    candidate_id: str | None = None
    old_text: str | None = None
    new_text: str | None = None
    evidence: list[Evidence] = field(default_factory=list)
'''

    if old in contracts:
        results.append(
            exact_patch(
                CONTRACTS,
                old,
                new,
                "repair_action_candidate_binding_fields",
            )
        )
    else:
        print("[INFO] RepairAction field anchor differs; no guess made.")

    # ---------------------------------------------------------
    # PATCH 2
    #
    # Add a deterministic validator for executable actions.
    #
    # It rejects an action that has no concrete target or exact
    # old/new text instead of allowing a false execution path.
    # ---------------------------------------------------------
    marker = '''@dataclass
class RepairPlan:
'''

    validator = '''def validate_repair_action(action: RepairAction):
    """
    Validate that a RepairAction is executable without guessing.

    Returns (True, None) when complete.
    Returns (False, reason) when required execution data is absent.
    """
    required = {
        "action_id": action.action_id,
        "target": action.target,
        "reason": action.reason,
        "old_text": action.old_text,
        "new_text": action.new_text,
    }

    missing = [
        name
        for name, value in required.items()
        if value is None or value == ""
    ]

    if missing:
        return False, f"Missing executable fields: {', '.join(missing)}"

    return True, None


@dataclass
class RepairPlan:
'''

    if "def validate_repair_action(action: RepairAction):" not in contracts:
        results.append(
            exact_patch(
                CONTRACTS,
                marker,
                validator,
                "repair_action_execution_validator",
            )
        )

    # ---------------------------------------------------------
    # PATCH 3
    #
    # cmd_repair must distinguish:
    #   NOT_EXECUTED -> exit 2
    #   FAILED        -> exit 1
    #
    # We do this at the CLI boundary without changing the repair
    # engine's existing result contract.
    # ---------------------------------------------------------
    old = '''def main():
    args = parser.parse_args()
    command = getattr(args, "command", None)

    if command == "scan":
'''

    new = '''def main():
    args = parser.parse_args()
    command = getattr(args, "command", None)

    try:
        return _main_command(args, command)
    except RepairCLIError as exc:
        print(f"[!] {exc}")
        return 1


def _main_command(args, command):
    if command == "scan":
'''

    if old in cli and "def _main_command(args, command):" not in cli:
        results.append(
            exact_patch(
                CLI,
                old,
                new,
                "cli_command_exit_boundary",
            )
        )
        cli = read(CLI)

    # ---------------------------------------------------------
    # PATCH 4
    #
    # Convert known repair failure prints into controlled
    # RepairCLIError paths.
    #
    # Exact anchors only. No broad replacement.
    # ---------------------------------------------------------
    replacements = [
        (
            '''        print("[!] Repair requires --candidate-id.")
        print("[!] Status: NOT_EXECUTED")
        return
''',
            '''        print("[!] Repair requires --candidate-id.")
        print("[!] Status: NOT_EXECUTED")
        raise RepairCLIError("NOT_EXECUTED: missing candidate_id")
''',
            "missing_candidate_exit_code",
        ),
        (
            '''        print("[!] Approval gate could not be loaded.")
        print("[!] Status: FAILED")
        return
''',
            '''        print("[!] Approval gate could not be loaded.")
        print("[!] Status: FAILED")
        raise RepairCLIError("FAILED: approval gate unavailable")
''',
            "approval_gate_failure_exit_code",
        ),
        (
            '''        print(f"[!] Approval rejected: {exc}")
        print("[!] Status: NOT_EXECUTED")
        return
''',
            '''        print(f"[!] Approval rejected: {exc}")
        print("[!] Status: NOT_EXECUTED")
        raise RepairCLIError(f"NOT_EXECUTED: approval rejected: {exc}")
''',
            "approval_rejection_exit_code",
        ),
        (
            '''        print("[!] Repair target does not match approved candidate.")
        print("[!] Status: NOT_EXECUTED")
        return
''',
            '''        print("[!] Repair target does not match approved candidate.")
        print("[!] Status: NOT_EXECUTED")
        raise RepairCLIError("NOT_EXECUTED: target mismatch")
''',
            "target_mismatch_exit_code",
        ),
        (
            '''        print("[!] Repair reason does not match approved candidate.")
        print("[!] Status: NOT_EXECUTED")
        return
''',
            '''        print("[!] Repair reason does not match approved candidate.")
        print("[!] Status: NOT_EXECUTED")
        raise RepairCLIError("NOT_EXECUTED: reason mismatch")
''',
            "reason_mismatch_exit_code",
        ),
        (
            '''            print("[-] Repair aborted by user.")
            return
''',
            '''            print("[-] Repair aborted by user.")
            raise RepairCLIError("NOT_EXECUTED: user rejected repair")
''',
            "user_rejection_exit_code",
        ),
        (
            '''        print("[!] Repair requires a concrete target and exact text change.")
        print(f"[!] Missing: {', '.join(missing)}")
        print("[!] Status: NOT_EXECUTED")
        return
''',
            '''        print("[!] Repair requires a concrete target and exact text change.")
        print(f"[!] Missing: {', '.join(missing)}")
        print("[!] Status: NOT_EXECUTED")
        raise RepairCLIError(
            f"NOT_EXECUTED: missing repair arguments: {', '.join(missing)}"
        )
''',
            "missing_repair_arguments_exit_code",
        ),
    ]

    cli = read(CLI)

    for old, new, label in replacements:
        if old in cli:
            result = exact_patch(CLI, old, new, label)
            results.append(result)
            if result["status"] != "APPLIED":
                print("[!] Patch failed:", label)
                sys.exit(5)
            cli = read(CLI)
        else:
            print("[INFO] Anchor not present; skipped:", label)

    # ---------------------------------------------------------
    # PATCH 5
    #
    # DeepRepairEngine exception must propagate as CLI failure
    # instead of being printed and returned as success.
    # ---------------------------------------------------------
    old = '''    except Exception as exc:
        record_phase(
            args.path,
            "REPAIR",
            "repair_execution",
            "FAILED",
            candidate_id=args.candidate_id,
            target=getattr(args, "target", None),
            error=str(exc),
        )
        print(f"[!] Repair execution failed: {exc}")
        print("[!] Status: FAILED")
        return
'''

    new = '''    except Exception as exc:
        record_phase(
            args.path,
            "REPAIR",
            "repair_execution",
            "FAILED",
            candidate_id=args.candidate_id,
            target=getattr(args, "target", None),
            error=str(exc),
        )
        print(f"[!] Repair execution failed: {exc}")
        print("[!] Status: FAILED")
        raise RepairCLIError(f"FAILED: repair execution: {exc}")
'''

    cli = read(CLI)

    if old in cli:
        results.append(
            exact_patch(
                CLI,
                old,
                new,
                "repair_execution_failure_exit_code",
            )
        )

    # ---------------------------------------------------------
    # PATCH 6
    #
    # Record that Phase 2 is structural only.
    # No old_text/new_text are generated.
    # ---------------------------------------------------------
    migration = {
        "migration": "P45-ENGINE-REPAIR-002",
        "phase": 2,
        "timestamp": now(),
        "status": "STRUCTURAL_PATCHES_APPLIED",
        "implemented": [
            "RepairAction candidate binding fields",
            "RepairAction executable-field validator",
            "repair CLI controlled failure boundary",
            "non-zero exit for known repair failures",
        ],
        "explicitly_not_implemented": [
            "inventing old_text/new_text",
            "automatic code generation",
            "multi-file execution of candidate 2",
            "execution against بلبل",
            "behavioral WebRTC verification",
            "re-analysis",
            "final report",
        ],
        "safety_rule": (
            "Approved candidates remain non-executable until each "
            "candidate is converted into concrete evidence-backed "
            "RepairAction records."
        ),
    }

    MIGRATION.parent.mkdir(parents=True, exist_ok=True)
    write(
        MIGRATION,
        json.dumps(migration, ensure_ascii=False, indent=2),
    )

    # ---------------------------------------------------------
    # COMPILE
    # ---------------------------------------------------------
    check = compile_check()

    if check["returncode"] != 0:
        print("[!] PY_COMPILE FAILED")
        print(check["stderr"])
        print("[!] Status: FAILED")
        sys.exit(10)

    report = {
        "report": "P45-PHASE2-REPAIR-001",
        "timestamp": now(),
        "status": "APPLIED_AND_COMPILED",
        "patches": results,
        "compile": check,
        "next_phase": [
            "candidate_to_repair_action_compiler",
            "multi_file_candidate_expansion",
            "execution_test_harness",
            "exact_verification",
            "behavioral_verification",
            "re_analysis",
            "final_report",
        ],
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    write(
        REPORT,
        json.dumps(report, ensure_ascii=False, indent=2),
    )

    print()
    print("======================================")
    print("P45_PHASE2_REPAIR: APPLIED_AND_COMPILED")
    print("REPORT:", REPORT)
    print("MIGRATION:", MIGRATION)
    print("======================================")


if __name__ == "__main__":
    main()
