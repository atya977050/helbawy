#!/usr/bin/env python3
"""
🛠️ مستودع الإصلاح (Repair Repository)
Engineering Diagnosis, Planning, Repair & Verification System
"""

import argparse
import sys
import json
from pathlib import Path

# إعداد المسارات الأساسية
BASE_DIR = Path(__file__).resolve().parent
ENGINE_DIR = BASE_DIR / "engine"
PLANS_DIR = BASE_DIR / "plans"
REPORTS_DIR = BASE_DIR / "reports"
SNAPSHOTS_DIR = BASE_DIR / "snapshots"
LOGS_DIR = BASE_DIR / "logs"

for d in [PLANS_DIR, REPORTS_DIR, SNAPSHOTS_DIR, LOGS_DIR, ENGINE_DIR]:
    d.mkdir(exist_ok=True, parents=True)

# استيراد محركات النظام بطريقة آمنة
sys.path.insert(0, str(ENGINE_DIR))

try:
    from scanner import ProjectScanner
except ImportError:
    ProjectScanner = None

try:
    from socketio import SocketIOAnalyzer
except ImportError:
    SocketIOAnalyzer = None

try:
    from planner import EngineeringPlanner
except ImportError:
    EngineeringPlanner = None

try:
    from contract_graph import ContractGraphEngine
except ImportError:
    ContractGraphEngine = None

try:
    from root_cause import RootCauseEngine
except ImportError:
    RootCauseEngine = None

try:
    from execution_log import ExecutionLog
except ImportError:
    ExecutionLog = None

try:
    from repair import DeepRepairEngine, RepairError
except ImportError:
    DeepRepairEngine = None
    RepairError = None

try:
    from engine.approval import ApprovalGate, ApprovalError
except ImportError:
    ApprovalGate = None
    ApprovalError = None

try:
    from engine.repair_gate import RepairGate, RepairGateError
except ImportError:
    RepairGate = None
    RepairGateError = None

try:
    from verification import VerificationEngine, VerificationError
except ImportError:
    VerificationEngine = None
    VerificationError = None

try:
    from repair_generator import RepairGenerator, RepairGenerationError
except ImportError:
    RepairGenerator = None
    RepairGenerationError = None

def get_execution_log(path):
    if ExecutionLog is None:
        return None
    return ExecutionLog(path)


def record_phase(path, phase, action, status, **details):
    log = get_execution_log(path)
    if log is None:
        return None
    return log.record(phase, action, status, **details)


def print_banner():
    print("=" * 60)
    print(" 🛠️ مستودع الإصلاح (Repair Repository v1.0)")
    print(" Engineering Diagnosis, Planning, Repair & Verification System")
    print("=" * 60)

def cmd_scan(args):
    print(f"\n[+] Scanning project path: {args.path}")
    if ProjectScanner:
        scanner = ProjectScanner(args.path)
        result = scanner.scan()
        print("\n[✓] Scan completed successfully. Project Structure Classification:")
        print(json.dumps(result["classification"], indent=2))
        
        reports_dir = Path(args.path).resolve() / "reports"
        reports_dir.mkdir(exist_ok=True, parents=True)
        scan_report_path = reports_dir / "scan-report.json"
        with open(scan_report_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"\n[+] Scan report saved to: {scan_report_path}")
    else:
        print("[-] Error: scanner.py engine not found.")

def cmd_contracts(args):
    print(f"\n[+] Analyzing Socket.IO contracts in path: {args.path}")
    if SocketIOAnalyzer:
        analyzer = SocketIOAnalyzer(args.path)
        result = analyzer.analyze()
        print("\n[✓] Contract analysis completed:")
        print(json.dumps(result, indent=2))
        
        reports_dir = Path(args.path).resolve() / "reports"
        reports_dir.mkdir(exist_ok=True, parents=True)
        contracts_report_path = reports_dir / "contracts-report.json"
        with open(contracts_report_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"\n[+] Contracts report saved to: {contracts_report_path}")
    else:
        print("[-] Error: socketio.py engine not found in engine/ directory.")

def cmd_plan(args):
    print(f"\n[+] Generating execution plan for goal: '{args.goal}'")
    if EngineeringPlanner:
        planner = EngineeringPlanner(args.path, args.goal)
        plan = planner.diagnose_and_plan()
        print("\n[✓] Execution Plan Generated Successfully:")
        print(json.dumps(plan, indent=2))
    else:
        print("[-] Error: planner.py engine not found.")

def cmd_diagnose(args):
    print(f"\n[+] Diagnosing project problems against requirements...")
    if EngineeringPlanner:
        planner = EngineeringPlanner(args.path, "root_cause_diagnosis")
        plan = planner.diagnose_and_plan()
        print("\n[✓] Diagnosis Findings & Evidence:")
        print(json.dumps(plan["diagnosis_findings"], indent=2))
    else:
        print("[-] Error: planner.py engine not found.")

def cmd_repair_gate(args):
    if RepairGate is None or RepairGateError is None:
        print("[!] Repair Gate could not be loaded.")
        print("[!] Status: FAILED")
        return

    try:
        result = RepairGate(args.path).show()
    except RepairGateError as exc:
        print(f"[!] Repair Gate failed: {exc}")
        print("[!] Status: FAILED")
        return

    if result is None:
        print("[!] No repair candidate approved.")
        return

    print("[+] Repair candidate approved.")
    print("[+] No repair was executed by the gate.")


class RepairCLIError(Exception):
    pass

def cmd_repair(args):
    direct_mode = args.direct_repair

    if not getattr(args, "candidate_id", None):
        record_phase(
            args.path,
            "APPROVAL",
            "candidate_binding",
            "NOT_EXECUTED",
            reason="Missing candidate_id",
        )
        print("[!] Repair requires --candidate-id.")
        print("[!] Status: NOT_EXECUTED")
        raise RepairCLIError("NOT_EXECUTED: missing candidate_id")

    if ApprovalGate is None or ApprovalError is None:
        record_phase(
            args.path,
            "APPROVAL",
            "approval_gate",
            "FAILED",
            candidate_id=args.candidate_id,
            reason="ApprovalGate is unavailable.",
        )
        print("[!] Approval gate could not be loaded.")
        print("[!] Status: FAILED")
        raise RepairCLIError("FAILED: approval gate unavailable")

    try:
        approval_gate = ApprovalGate(args.path)
        approved_candidate = approval_gate.require_approved(
            args.candidate_id
        )
    except ApprovalError as exc:
        record_phase(
            args.path,
            "APPROVAL",
            "candidate_approval",
            "REJECTED",
            candidate_id=args.candidate_id,
            error=str(exc),
        )
        print(f"[!] Approval rejected: {exc}")
        print("[!] Status: NOT_EXECUTED")
        raise RepairCLIError(f"NOT_EXECUTED: approval rejected: {exc}")

    candidate_target = approved_candidate.get("target")
    candidate_reason = approved_candidate.get("reason")

    # Resolve the target from the approved candidate when the
    # candidate has exactly one concrete target.
    requested_target = getattr(args, "target", None)

    if not requested_target and candidate_target:
        if isinstance(candidate_target, str) and " + " not in candidate_target:
            args.target = candidate_target
            requested_target = candidate_target

    if candidate_target and requested_target != candidate_target:
        record_phase(
            args.path,
            "APPROVAL",
            "candidate_target_binding",
            "REJECTED",
            candidate_id=args.candidate_id,
            expected_target=candidate_target,
            requested_target=getattr(args, "target", None),
        )
        print("[!] Repair target does not match approved candidate.")
        print("[!] Status: NOT_EXECUTED")
        raise RepairCLIError("NOT_EXECUTED: target mismatch")

    if candidate_reason and getattr(args, "reason", None) == "Approved exact repair action":
        args.reason = candidate_reason

    if candidate_reason and getattr(args, "reason", None) != candidate_reason:
        record_phase(
            args.path,
            "APPROVAL",
            "candidate_reason_binding",
            "REJECTED",
            candidate_id=args.candidate_id,
            expected_reason=candidate_reason,
            requested_reason=getattr(args, "reason", None),
        )
        print("[!] Repair reason does not match approved candidate.")
        print("[!] Status: NOT_EXECUTED")
        raise RepairCLIError("NOT_EXECUTED: reason mismatch")

    record_phase(
        args.path,
        "REPAIR_REQUEST",
        "repair_command_started",
        "REQUESTED",
        candidate_id=args.candidate_id,
        target=candidate_target,
        reason=candidate_reason,
        direct_mode=direct_mode,
    )

    print(
        f"\n[!] Repair Mode: "
        f"{'DIRECT REPAIR AUTHORIZED' if direct_mode else 'PRODUCTION / APPROVAL MODE'}"
    )

    if not direct_mode:
        approval = input(
            "Do you approve executing the repair plan? (yes/no): "
        ).strip().lower()

        if approval not in ["yes", "y"]:
            record_phase(
                args.path,
                "APPROVAL",
                "repair_approval",
                "REJECTED",
            )
            print("[-] Repair aborted by user.")
            raise RepairCLIError("NOT_EXECUTED: user rejected repair")

    required = ["target", "old_text", "new_text"]
    missing = [
        name for name in required
        if not getattr(args, name, None)
    ]

    if missing:
        record_phase(
            args.path,
            "REPAIR",
            "repair_execution",
            "NOT_EXECUTED",
            reason="Missing repair arguments",
            missing=missing,
        )
        print("[!] Repair requires a concrete target and exact text change.")
        print(f"[!] Missing: {', '.join(missing)}")
        print("[!] Status: NOT_EXECUTED")
        raise RepairCLIError(
            f"NOT_EXECUTED: missing repair arguments: {', '.join(missing)}"
        )

    if DeepRepairEngine is None:
        record_phase(
            args.path,
            "REPAIR",
            "repair_engine",
            "FAILED",
            reason="DeepRepairEngine is unavailable.",
        )
        print("[!] Repair engine could not be loaded.")
        print("[!] Status: FAILED")
        return

    try:
        engine = DeepRepairEngine(args.path)

        # Candidate-bound action identity.
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

        print("[+] Exact repair applied.")
        print(f"[+] Target: {result.target}")
        print(f"[+] Action: {result.action_id}")
        print(f"[+] Before SHA-256: {result.before_sha256}")
        print(f"[+] After SHA-256:  {result.after_sha256}")
        print("[+] Status: APPLIED")

        return result

    except Exception as exc:
        record_phase(
            args.path,
            "REPAIR",
            "repair_execution",
            "FAILED",
            target=args.target,
            error=str(exc),
        )
        print(f"[!] Repair execution failed: {exc}")
        print("[!] Status: FAILED")
        return


def cmd_verify(args):
    record_phase(
        args.path,
        "VERIFY",
        "verification_requested",
        "REQUESTED",
    )

    required = ["target", "old_text", "new_text"]
    missing = [
        name for name in required
        if not getattr(args, name, None)
    ]

    if missing:
        record_phase(
            args.path,
            "VERIFY",
            "verification_execution",
            "NOT_EXECUTED",
            reason="Missing verification arguments",
            missing=missing,
        )
        print("[!] Verification requires a concrete target and exact change.")
        print(f"[!] Missing: {', '.join(missing)}")
        print("[!] Status: NOT_EXECUTED")
        return

    if VerificationEngine is None:
        record_phase(
            args.path,
            "VERIFY",
            "verification_engine",
            "FAILED",
            reason="VerificationEngine is unavailable.",
        )
        print("[!] Verification engine could not be loaded.")
        print("[!] Status: FAILED")
        return

    try:
        engine = VerificationEngine(args.path)

        result = engine.verify_exact_change(
            action_id=args.action_id,
            target=args.target,
            old_text=args.old_text,
            new_text=args.new_text,
        )

        print("[+] Verification completed.")
        print(f"[+] Target: {result['target']}")
        print(f"[+] Action: {result['action_id']}")
        print("[+] Checks:")
        for name, passed in result["checks"].items():
            print(f"    {'PASS' if passed else 'FAIL'}: {name}")
        print("[+] Status: VERIFIED")

        return result

    except Exception as exc:
        record_phase(
            args.path,
            "VERIFY",
            "verification_execution",
            "FAILED",
            target=args.target,
            error=str(exc),
        )
        print(f"[!] Verification failed: {exc}")
        print("[!] Status: FAILED")
        return


def cmd_full(args):
    print_banner()
    print(f"[*] Running full engineering repair cycle on: {args.path}")

    results = {}

    stages = [
        ("scan", cmd_scan),
        ("contracts", cmd_contracts),
    ]

    # Contract Graph و Root Cause هما محركات موجودة بالفعل.
    # Full Cycle يربطهما فقط؛ لا يعيد بناء وظائفهما.
    if ContractGraphEngine is None:
        raise RuntimeError("contract_graph.py engine not available")

    if RootCauseEngine is None:
        raise RuntimeError("root_cause.py engine not available")

    # تنفيذ المراحل الأولية قبل Graph و Root Cause
    # لأن Graph يعتمد على Scan/Contracts المحدثة.
    for name, command in stages:
        try:
            results[name] = command(args)
        except Exception as exc:
            record_phase(
                args.path,
                "FULL",
                name,
                "FAILED",
                error=str(exc),
            )
            print(f"[!] Full cycle stopped at {name}: {exc}")
            return

    stages = []

    try:
        graph, graph_output = ContractGraphEngine(args.path).build()
        results["contract_graph"] = {
            "status": "EVIDENCED",
            "output": str(graph_output),
            "nodes": len(graph.get("nodes", [])),
            "edges": len(graph.get("edges", [])),
        }
    except Exception as exc:
        record_phase(
            args.path,
            "FULL",
            "contract_graph",
            "FAILED",
            error=str(exc),
        )
        print(f"[!] Full cycle stopped at contract_graph: {exc}")
        return

    try:
        root_cause, root_cause_output = RootCauseEngine(args.path).build()
        results["root_cause"] = {
            "status": "EVIDENCED",
            "output": str(root_cause_output),
            "causes": len(root_cause.get("root_causes", [])),
        }
    except Exception as exc:
        record_phase(
            args.path,
            "FULL",
            "root_cause",
            "FAILED",
            error=str(exc),
        )
        print(f"[!] Full cycle stopped at root_cause: {exc}")
        return

    stages = [
        ("plan", cmd_plan),
        ("diagnose", cmd_diagnose),
    ]

    for name, command in stages:
        try:
            results[name] = command(args)
        except Exception as exc:
            record_phase(
                args.path,
                "FULL",
                name,
                "FAILED",
                error=str(exc),
            )
            print(f"[!] Full cycle stopped at {name}: {exc}")
            return

    # الإصلاح لا يُعتبر جزءًا منفذًا من الدورة إلا إذا
    # وُجدت بيانات إصلاح صريحة وموافقة مباشرة.
    if (
        getattr(args, "direct_repair", False)
        and getattr(args, "target", None)
        and getattr(args, "old_text", None) is not None
        and getattr(args, "new_text", None) is not None
    ):
        try:
            results["repair"] = cmd_repair(args)
        except Exception as exc:
            record_phase(
                args.path,
                "FULL",
                "repair",
                "FAILED",
                error=str(exc),
            )
            print(f"[!] Full cycle repair failed: {exc}")
            return
    else:
        results["repair"] = {
            "status": "NOT_APPLIED",
            "reason": "No explicitly authorized repair action supplied.",
        }
        record_phase(
            args.path,
            "FULL",
            "repair",
            "NOT_APPLIED",
            reason="No explicitly authorized repair action supplied.",
        )

    # التحقق لا يُنفذ كنجاح وهمي.
    if (
        results["repair"].get("status") == "APPLIED"
        and getattr(args, "target", None)
        and getattr(args, "old_text", None) is not None
        and getattr(args, "new_text", None) is not None
    ):
        try:
            results["verify"] = cmd_verify(args)
        except Exception as exc:
            record_phase(
                args.path,
                "FULL",
                "verify",
                "FAILED",
                error=str(exc),
            )
            print(f"[!] Full cycle verification failed: {exc}")
            return
    else:
        results["verify"] = {
            "status": "NOT_APPLIED",
            "reason": "Verification requires an actually applied repair.",
        }
        record_phase(
            args.path,
            "FULL",
            "verify",
            "NOT_APPLIED",
            reason="Verification requires an actually applied repair.",
        )

    final_status = "COMPLETED"
    if results["verify"].get("status") == "FAILED":
        final_status = "FAILED"
    elif results["verify"].get("status") == "NOT_APPLIED":
        final_status = "ANALYSIS_COMPLETED_REPAIR_NOT_APPLIED"

    record_phase(
        args.path,
        "FULL",
        "full_cycle",
        final_status,
        stages=list(results.keys()),
    )

    print("\n" + "=" * 60)
    print(f" P45 Full Cycle Status: {final_status}")
    print(" Analysis stages completed without false success.")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="Repair Repository CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    p_scan = subparsers.add_parser("scan", help="Scan project and discover structure")
    p_scan.add_argument("--path", default=".", help="Path to project directory")

    p_contracts = subparsers.add_parser("contracts", help="Analyze Socket.IO and communication contracts")
    p_contracts.add_argument("--path", default=".", help="Path to project directory")

    p_plan = subparsers.add_parser("plan", help="Generate execution plan")
    p_plan.add_argument("--goal", required=True, help="Natural language description of goal/problem")
    p_plan.add_argument("--path", default=".", help="Path to project directory")

    p_diag = subparsers.add_parser("diagnose", help="Diagnose root causes")
    p_diag.add_argument("--path", default=".", help="Path to project directory")

    p_gate = subparsers.add_parser("repair-gate", help="Review and approve a repair candidate")
    p_gate.add_argument("--path", default=".", help="Path to project directory")

    p_rep = subparsers.add_parser("repair", help="Execute repair plan")
    p_rep.add_argument("--candidate-id", required=True, help="Approved repair candidate identifier")
    p_rep.add_argument("--direct-repair", action="store_true", help="Authorize direct repair without prompt")
    p_rep.add_argument("--path", default=".", help="Path to project directory")
    p_rep.add_argument("--action-id", default="CLI-REPAIR-001", help="Repair action identifier")
    p_rep.add_argument("--target", help="Project-relative file to repair")
    p_rep.add_argument("--reason", default="Approved exact repair action", help="Reason for the repair")
    p_rep.add_argument("--old-text", help="Exact existing text")
    p_rep.add_argument("--new-text", help="Exact replacement text")

    p_ver = subparsers.add_parser("verify", help="Run tests and verify contracts")
    p_ver.add_argument("--path", default=".", help="Path to project directory")
    p_ver.add_argument("--action-id", default="CLI-VERIFY-001", help="Verification action identifier")
    p_ver.add_argument("--target", help="Project-relative file to verify")
    p_ver.add_argument("--old-text", help="Exact previous text")
    p_ver.add_argument("--new-text", help="Exact expected replacement text")

    p_full = subparsers.add_parser("full", help="Run full lifecycle cycle")
    p_full.add_argument("--goal", default="general_repair", help="Goal or problem description")
    p_full.add_argument("--direct-repair", action="store_true", help="Authorize direct repair")
    p_full.add_argument("--path", default=".", help="Path to project directory")
    p_full.add_argument("--action-id", default="CLI-FULL-001", help="Repair action identifier")
    p_full.add_argument("--target", help="Project-relative file to repair")
    p_full.add_argument("--reason", default="Approved full-cycle exact repair", help="Reason for the repair")
    p_full.add_argument("--old-text", help="Exact existing text")
    p_full.add_argument("--new-text", help="Exact replacement text")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "scan": cmd_scan,
        "contracts": cmd_contracts,
        "plan": cmd_plan,
        "diagnose": cmd_diagnose,
        "repair-gate": cmd_repair_gate,
        "repair": cmd_repair,
        "verify": cmd_verify,
        "full": cmd_full
    }

    if args.command in commands:
        commands[args.command](args)

if __name__ == "__main__":
    main()
