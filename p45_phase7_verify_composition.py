from pathlib import Path
import json
import hashlib
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
PLAN = ROOT / "plans" / "repair-composition-plan.json"
OUT = ROOT / "plans" / "repair-composition-verification.json"
REPORT = ROOT / "reports" / "p45-phase7-composition-verification-report.json"


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    print("=== P45 PHASE 7 — COMPOSITION VERIFICATION ===")
    print(f"TIME: {now()}")

    if not PLAN.exists():
        raise SystemExit(f"STOP: missing {PLAN}")

    data = json.loads(PLAN.read_text(encoding="utf-8"))
    targets = data.get("targets")

    if not isinstance(targets, list) or not targets:
        raise SystemExit("STOP: composition targets missing.")

    verified = []
    failures = []

    for target in targets:
        target_name = target["target"]
        steps = target.get("actions", [])
        original_sha = target.get("original_sha256")
        composed_sha = target.get("composed_sha256")

        working_sha = original_sha
        target_ok = True
        step_results = []

        for step in steps:
            before_sha = step.get("before_sha256")
            after_sha = step.get("after_sha256")
            match_count = step.get("match_count")

            checks = {
                "before_sha_present": bool(before_sha),
                "after_sha_present": bool(after_sha),
                "match_exactly_one": match_count == 1,
                "sha_transition_changed": (
                    bool(before_sha)
                    and bool(after_sha)
                    and before_sha != after_sha
                ),
            }

            ok = all(checks.values())

            if before_sha != working_sha:
                checks["chain_continuity"] = False
                ok = False
            else:
                checks["chain_continuity"] = True

            step_results.append({
                "action_id": step.get("action_id"),
                "step": step.get("step"),
                "checks": checks,
                "status": "VERIFIED" if ok else "FAILED",
            })

            if not ok:
                target_ok = False
                failures.append({
                    "target": target_name,
                    "action_id": step.get("action_id"),
                    "step": step.get("step"),
                })

            if after_sha:
                working_sha = after_sha

        final_sha_ok = working_sha == composed_sha

        if not final_sha_ok:
            target_ok = False
            failures.append({
                "target": target_name,
                "reason": "Final composed SHA mismatch",
                "expected": composed_sha,
                "actual": working_sha,
            })

        verified.append({
            "target": target_name,
            "original_sha256": original_sha,
            "expected_composed_sha256": composed_sha,
            "verified_composed_sha256": working_sha,
            "action_count": len(steps),
            "status": "VERIFIED" if target_ok else "FAILED",
            "steps": step_results,
        })

    status = (
        "COMPOSITION_VERIFIED_NO_EXECUTION"
        if not failures
        else "COMPOSITION_VERIFICATION_FAILED"
    )

    result = {
        "schema": "P45-CompositionVerification-v1",
        "phase": 7,
        "created_at": now(),
        "status": status,
        "execution_allowed": False,
        "target_modification": "NONE",
        "failures": failures,
        "targets": verified,
        "rule": (
            "Verification confirms only the integrity of the composed "
            "in-memory action chain. It does not authorize execution."
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    OUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report = {
        "phase": 7,
        "status": status,
        "targets": len(targets),
        "failures": len(failures),
        "execution_allowed": False,
        "target_modification": "NONE",
        "created_at": now(),
    }

    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("=" * 38)
    print(f"TARGETS: {len(targets)}")
    print(f"FAILURES: {len(failures)}")
    print(f"STATUS: {status}")
    print("TARGET MODIFICATION: NONE")
    print("EXECUTION_ALLOWED: False")
    print(f"VERIFICATION: {OUT}")
    print(f"REPORT: {REPORT}")
    print("=" * 38)

    for item in verified:
        print(
            f"{item['target']} | "
            f"ACTIONS={item['action_count']} | "
            f"{item['status']}"
        )


if __name__ == "__main__":
    main()
