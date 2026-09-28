from pathlib import Path
import json
import hashlib
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
VERIFY = ROOT / "plans" / "repair-composition-verification.json"
SNAPSHOT = ROOT / "plans" / "p45-snapshot-manifest.json"
GENERATED = ROOT / "plans" / "repair-actions-generated.json"

OUT = ROOT / "plans" / "p45-apply-gate.json"
REPORT = ROOT / "reports" / "p45-phase9-apply-gate-report.json"


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    print("=== P45 PHASE 9 — APPLY GATE ===")
    print(f"TIME: {now()}")

    for required in (VERIFY, SNAPSHOT, GENERATED):
        if not required.is_file():
            raise SystemExit(f"STOP: missing required artifact: {required}")

    verification = json.loads(VERIFY.read_text(encoding="utf-8"))
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    generated = json.loads(GENERATED.read_text(encoding="utf-8"))

    failures = []

    if verification.get("status") != "COMPOSITION_VERIFIED_NO_EXECUTION":
        failures.append("Phase 7 verification is not valid.")

    if verification.get("execution_allowed") is not False:
        failures.append("Phase 7 execution_allowed is not False.")

    if snapshot.get("snapshot_status") != "CREATED":
        failures.append("Snapshot was not created.")

    if snapshot.get("execution_allowed") is not False:
        failures.append("Snapshot execution_allowed is not False.")

    actions = generated.get("actions")
    if not isinstance(actions, list) or len(actions) != 6:
        failures.append("Expected exactly 6 generated executable actions.")

    for action in actions or []:
        if action.get("status") != "GENERATED":
            failures.append(
                f"Action not GENERATED: {action.get('action_id')}"
            )

        if action.get("anchor_verified") is not True:
            failures.append(
                f"Anchor not verified: {action.get('action_id')}"
            )

        if action.get("execution_allowed") is not False:
            failures.append(
                f"Action execution_allowed is not False: {action.get('action_id')}"
            )

        if not action.get("before_sha256"):
            failures.append(
                f"Missing before SHA: {action.get('action_id')}"
            )

    archive = Path(snapshot["archive"])
    if not archive.is_file():
        failures.append("Snapshot archive file is missing.")
    else:
        actual_archive_sha = sha256_file(archive)
        if actual_archive_sha != snapshot.get("archive_sha256"):
            failures.append("Snapshot archive SHA mismatch.")

    status = (
        "APPLY_GATE_READY"
        if not failures
        else "APPLY_GATE_BLOCKED"
    )

    result = {
        "schema": "P45-ApplyGate-v1",
        "phase": 9,
        "created_at": now(),
        "status": status,
        "execution_allowed": False,
        "target_modification": "NONE",
        "failures": failures,
        "preconditions": {
            "composition_verified": not any(
                "Phase 7" in x for x in failures
            ),
            "snapshot_created": snapshot.get("snapshot_status") == "CREATED",
            "generated_actions": len(actions or []),
            "snapshot_archive_verified": not any(
                "archive SHA" in x or "archive file" in x
                for x in failures
            ),
        },
        "rule": (
            "Apply Gate validates readiness only. "
            "It never modifies the target and never authorizes execution "
            "by itself."
        ),
    }

    OUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    REPORT.write_text(
        json.dumps({
            "phase": 9,
            "status": status,
            "failures": len(failures),
            "execution_allowed": False,
            "target_modification": "NONE",
            "created_at": now(),
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("=" * 38)
    print(f"ACTIONS: {len(actions or [])}")
    print(f"FAILURES: {len(failures)}")
    print(f"STATUS: {status}")
    print("TARGET MODIFICATION: NONE")
    print("EXECUTION_ALLOWED: False")
    print(f"GATE: {OUT}")
    print(f"REPORT: {REPORT}")

    if failures:
        print("--- FAILURES ---")
        for failure in failures:
            print(f"- {failure}")

    print("=" * 38)


if __name__ == "__main__":
    main()
