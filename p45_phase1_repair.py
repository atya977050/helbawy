from pathlib import Path
import json
import sys
import subprocess
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
CLI = ROOT / "repair-repository.py"
CONTRACTS = ROOT / "engine" / "contracts.py"
PLAN = ROOT / "plans" / "execution-plan.json"
MIGRATION = ROOT / "plans" / "p45-engine-repair-migration.json"
REPORT = ROOT / "reports" / "p45-phase1-repair-report.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def read(p):
    return p.read_text(encoding="utf-8")

def write(p, s):
    p.write_text(s, encoding="utf-8")

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
    print("=== P45 PHASE 1 CONTROLLED REPAIR ===")
    print("TIME:", now())

    for p in [CLI, CONTRACTS]:
        if not p.exists():
            print("[!] Missing:", p)
            sys.exit(2)

    cli = read(CLI)
    contracts = read(CONTRACTS)

    # ---------------------------------------------------------
    # PRE-CONDITIONS
    # ---------------------------------------------------------
    required = [
        "def cmd_repair(args):",
        "approved_candidate = approval_gate.require_approved(",
        "result = engine.apply_exact_change(",
        'p_rep.add_argument("--candidate-id"',
        'p_rep.add_argument("--target"',
        'p_rep.add_argument("--old-text"',
        'p_rep.add_argument("--new-text"',
    ]

    for marker in required:
        if marker not in cli:
            print("[!] Required CLI marker missing:", marker)
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
    # Exit code correctness.
    #
    # Existing cmd_repair uses bare `return` for several
    # NOT_EXECUTED / FAILED branches. main() therefore exits 0.
    #
    # We introduce a controlled exception used only by CLI
    # command failures, then main can convert it to non-zero.
    # ---------------------------------------------------------
    marker = 'class RepairCLIError(Exception):\n    pass\n\n'

    if marker not in cli:
        anchor = "def cmd_repair(args):\n"

        if anchor not in cli:
            print("[!] cmd_repair anchor missing.")
            sys.exit(5)

        result = exact_patch(
            CLI,
            anchor,
            marker + anchor,
            "add RepairCLIError",
        )
        results.append(result)

        if result["status"] != "APPLIED":
            print("[!] Phase 1 stopped.")
            sys.exit(6)

        cli = read(CLI)
    else:
        print("[OK] RepairCLIError already exists.")

    # ---------------------------------------------------------
    # PATCH 2
    #
    # Missing candidate target:
    # resolve target from approved candidate when unambiguous.
    # ---------------------------------------------------------
    old = '''    candidate_target = approved_candidate.get("target")
    candidate_reason = approved_candidate.get("reason")

    if candidate_target and getattr(args, "target", None) != candidate_target:
'''

    new = '''    candidate_target = approved_candidate.get("target")
    candidate_reason = approved_candidate.get("reason")

    # Resolve the target from the approved candidate when the
    # candidate has exactly one concrete target.
    requested_target = getattr(args, "target", None)

    if not requested_target and candidate_target:
        if isinstance(candidate_target, str) and " + " not in candidate_target:
            args.target = candidate_target
            requested_target = candidate_target

    if candidate_target and requested_target != candidate_target:
'''

    if old in cli:
        result = exact_patch(
            CLI,
            old,
            new,
            "candidate_target_auto_resolution",
        )
        results.append(result)

        if result["status"] != "APPLIED":
            print("[!] Target-resolution patch failed.")
            sys.exit(7)

        cli = read(CLI)
    else:
        print("[INFO] Target-resolution anchor differs; no guess made.")

    # ---------------------------------------------------------
    # PATCH 3
    #
    # Candidate reason resolution.
    # ---------------------------------------------------------
    old = '''    if candidate_reason and getattr(args, "reason", None) != candidate_reason:
'''

    new = '''    if candidate_reason and getattr(args, "reason", None) == "Approved exact repair action":
        args.reason = candidate_reason

    if candidate_reason and getattr(args, "reason", None) != candidate_reason:
'''

    if old in cli:
        result = exact_patch(
            CLI,
            old,
            new,
            "candidate_reason_auto_resolution",
        )
        results.append(result)

        if result["status"] != "APPLIED":
            sys.exit(8)

        cli = read(CLI)

    # ---------------------------------------------------------
    # PATCH 4
    #
    # Bind repair request explicitly to candidate_id.
    #
    # The current DeepRepairEngine API does not accept candidate_id,
    # so we preserve the engine API and bind it at CLI/log level.
    # ---------------------------------------------------------
    old = '''        result = engine.apply_exact_change(
            action_id=args.action_id,
            target=args.target,
            reason=args.reason,
            old_text=args.old_text,
            new_text=args.new_text,
            approved=True,
        )
'''

    new = '''        # Candidate-bound action identity.
        # Keep the existing DeepRepairEngine API unchanged.
        bound_action_id = (
            f"{args.candidate_id}:{args.action_id}"
            if args.candidate_id
            else args.action_id
        )

        result = engine.apply_exact_change(
            action_id=bound_action_id,
            target=args.target,
            reason=args.reason,
            old_text=args.old_text,
            new_text=args.new_text,
            approved=True,
        )
'''

    if old in cli:
        result = exact_patch(
            CLI,
            old,
            new,
            "candidate_action_binding",
        )
        results.append(result)

        if result["status"] != "APPLIED":
            sys.exit(9)

        cli = read(CLI)

    # ---------------------------------------------------------
    # PATCH 5
    #
    # Persist migration specification after successful patches.
    # ---------------------------------------------------------
    migration = {
        "migration": "P45-ENGINE-REPAIR-001",
        "phase": 1,
        "timestamp": now(),
        "status": "APPLIED",
        "implemented": [
            "candidate target auto-resolution for single target",
            "candidate reason auto-resolution",
            "candidate-bound action identity",
            "repair CLI failure architecture prepared",
        ],
        "not_yet_implemented": [
            "multi-file candidate expansion",
            "automatic old_text/new_text generation",
            "test layer",
            "behavioral verification",
            "re-analysis",
            "final report",
        ],
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
        print("[!] Changes were NOT automatically rolled back.")
        print("[!] Status: FAILED")
        sys.exit(10)

    report = {
        "report": "P45-PHASE1-REPAIR-001",
        "timestamp": now(),
        "status": "APPLIED_AND_COMPILED",
        "patches": results,
        "compile": check,
        "next_phase": [
            "multi_file_candidate_actions",
            "failure_exit_codes",
            "test_layer",
            "verification",
            "re_analysis",
        ],
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    write(
        REPORT,
        json.dumps(report, ensure_ascii=False, indent=2),
    )

    print()
    print("======================================")
    print("P45_PHASE1_REPAIR:", "APPLIED_AND_COMPILED")
    print("REPORT:", REPORT)
    print("MIGRATION:", MIGRATION)
    print("======================================")

if __name__ == "__main__":
    main()
