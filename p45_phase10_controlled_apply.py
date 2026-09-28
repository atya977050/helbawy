from pathlib import Path
import json
import hashlib
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
TARGET_ROOT = ROOT / "بلبل-الجديد"

GATE = ROOT / "plans" / "p45-apply-gate.json"
COMPOSITION = ROOT / "plans" / "repair-composition-plan.json"
VERIFY = ROOT / "plans" / "repair-composition-verification.json"
SNAPSHOT = ROOT / "plans" / "p45-snapshot-manifest.json"

OUT = ROOT / "plans" / "p45-controlled-apply-result.json"
REPORT = ROOT / "reports" / "p45-phase10-controlled-apply-report.json"


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    print("=== P45 PHASE 10 — CONTROLLED APPLY ===")
    print(f"TIME: {now()}")

    for required in (GATE, COMPOSITION, VERIFY, SNAPSHOT):
        if not required.is_file():
            raise SystemExit(f"STOP: missing artifact: {required}")

    gate = json.loads(GATE.read_text(encoding="utf-8"))
    composition = json.loads(COMPOSITION.read_text(encoding="utf-8"))
    verification = json.loads(VERIFY.read_text(encoding="utf-8"))
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))

    if gate.get("status") != "APPLY_GATE_READY":
        raise SystemExit("STOP: APPLY_GATE_READY required.")

    if verification.get("status") != "COMPOSITION_VERIFIED_NO_EXECUTION":
        raise SystemExit("STOP: Phase 7 verification invalid.")

    if snapshot.get("snapshot_status") != "CREATED":
        raise SystemExit("STOP: valid pre-repair snapshot required.")

    targets = composition.get("targets", [])
    if not targets:
        raise SystemExit("STOP: no composed targets.")

    applied = []
    failures = []

    for target_info in targets:
        target_name = target_info["target"]
        target_path = TARGET_ROOT / target_name

        if not target_path.is_file():
            failures.append({
                "target": target_name,
                "reason": "Target file missing",
            })
            continue

        current = target_path.read_text(encoding="utf-8")
        current_sha = sha256_text(current)
        expected_original = target_info["original_sha256"]

        print(f"--- {target_name} ---")
        print(f"CURRENT SHA: {current_sha}")
        print(f"EXPECTED SHA: {expected_original}")

        if current_sha != expected_original:
            failures.append({
                "target": target_name,
                "reason": "Current SHA differs from snapshotted composition source",
                "current_sha": current_sha,
                "expected_sha": expected_original,
            })
            print("STATUS: BLOCKED_SHA_MISMATCH")
            continue

        working = current
        steps = []
        target_failed = False

        for step in target_info.get("actions", []):
            action_id = step["action_id"]
            old_text = step["old_text"]
            new_text = step["new_text"]

            before_sha = sha256_text(working)
            expected_before = step["before_sha256"]

            if before_sha != expected_before:
                failures.append({
                    "target": target_name,
                    "action_id": action_id,
                    "reason": "Step before-SHA mismatch",
                    "current_sha": before_sha,
                    "expected_sha": expected_before,
                })
                target_failed = True
                break

            matches = working.count(old_text)

            if matches != 1:
                failures.append({
                    "target": target_name,
                    "action_id": action_id,
                    "reason": "Exact anchor count is not 1",
                    "matches": matches,
                })
                target_failed = True
                break

            working = working.replace(old_text, new_text, 1)

            after_sha = sha256_text(working)

            if after_sha != step["after_sha256"]:
                failures.append({
                    "target": target_name,
                    "action_id": action_id,
                    "reason": "Step after-SHA mismatch",
                    "actual": after_sha,
                    "expected": step["after_sha256"],
                })
                target_failed = True
                break

            steps.append({
                "action_id": action_id,
                "before_sha256": before_sha,
                "after_sha256": after_sha,
                "status": "APPLIED_IN_MEMORY",
            })

        if target_failed:
            print("STATUS: BLOCKED")
            continue

        final_sha = sha256_text(working)
        expected_final = target_info["composed_sha256"]

        if final_sha != expected_final:
            failures.append({
                "target": target_name,
                "reason": "Final composed SHA mismatch",
                "actual": final_sha,
                "expected": expected_final,
            })
            print("STATUS: BLOCKED_FINAL_SHA")
            continue

        # Final write happens only after every pre-write check succeeded.
        target_path.write_text(working, encoding="utf-8")

        written = target_path.read_text(encoding="utf-8")
        written_sha = sha256_text(written)

        if written_sha != expected_final:
            failures.append({
                "target": target_name,
                "reason": "Post-write SHA mismatch",
                "actual": written_sha,
                "expected": expected_final,
            })
            print("STATUS: POST_WRITE_SHA_FAILURE")
            continue

        applied.append({
            "target": target_name,
            "original_sha256": current_sha,
            "final_sha256": written_sha,
            "actions": steps,
            "status": "APPLIED_AND_SHA_VERIFIED",
        })

        print(f"FINAL SHA: {written_sha}")
        print("STATUS: APPLIED_AND_SHA_VERIFIED")

    status = (
        "APPLIED_AND_EXACTLY_VERIFIED"
        if not failures and len(applied) == len(targets)
        else "PARTIAL_OR_FAILED"
    )

    result = {
        "schema": "P45-ControlledApply-v1",
        "phase": 10,
        "created_at": now(),
        "status": status,
        "targets_expected": len(targets),
        "targets_applied": len(applied),
        "failures": failures,
        "applied": applied,
        "snapshot_used": snapshot.get("archive"),
        "execution_mode": "CONTROLLED_EXACT_COMPOSITION",
        "target_modification": (
            "APPLIED" if applied else "NONE"
        ),
    }

    OUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    REPORT.write_text(
        json.dumps({
            "phase": 10,
            "status": status,
            "targets_expected": len(targets),
            "targets_applied": len(applied),
            "failures": len(failures),
            "created_at": now(),
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("=" * 38)
    print(f"EXPECTED TARGETS: {len(targets)}")
    print(f"APPLIED TARGETS: {len(applied)}")
    print(f"FAILURES: {len(failures)}")
    print(f"STATUS: {status}")
    print(f"RESULT: {OUT}")
    print(f"REPORT: {REPORT}")
    print("=" * 38)

    if failures:
        print("--- FAILURES ---")
        for failure in failures:
            print(json.dumps(failure, ensure_ascii=False))

    if status != "APPLIED_AND_EXACTLY_VERIFIED":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
