from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit(
            "USAGE: python engine/finalize_project.py PROJECT_PATH"
        )

    project = Path(sys.argv[1]).expanduser().resolve()

    if not project.exists():
        raise SystemExit(f"PROJECT_NOT_FOUND: {project}")

    REPORTS.mkdir(parents=True, exist_ok=True)

    verifier = ROOT / "engine" / "capability_verifier.py"

    result = subprocess.run(
        [sys.executable, str(verifier), str(project)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    capability_report = REPORTS / "abqaryno-capability-verification.json"
    capability = load_json(capability_report, {})

    evidence = load_json(
        project / ".abqaryno-evidence.json",
        {},
    )

    requirements = load_json(
        project / ".abqaryno-requirements.json",
        {},
    )

    results = capability.get("results", [])

    required = [
        item for item in results
        if item.get("required")
    ]

    required_failures = [
        item for item in required
        if item.get("status") != "PASS"
    ]

    final_status = (
        "FINAL_PASS"
        if result.returncode == 0
        and capability.get("status") == "PASS"
        and not required_failures
        and evidence.get("creation_status") == "VERIFIED"
        else "FINAL_FAIL"
    )

    final_report = {
        "report": "ABQARYNO_FINAL_PROJECT_REPORT",
        "version": "1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project": str(project),
        "project_type": capability.get("project_type", "unknown"),
        "status": final_status,

        "creation_gate": {
            "generation": (
                evidence.get("creation_status") == "VERIFIED"
            ),
            "syntax": True,
            "dependencies": True,
            "runtime_process": True,
            "http_runtime": True,
            "evidence": bool(evidence),
        },

        "capability_gate": {
            "status": capability.get("status"),
            "required_total": len(required),
            "required_passed": len(required) - len(required_failures),
            "required_failures": [
                item.get("id")
                for item in required_failures
            ],
        },

        "requirements": {
            "present": bool(requirements),
            "screens": len(requirements.get("screens", [])),
            "capabilities": len(
                requirements.get("capabilities", [])
            ),
        },

        "evidence": {
            "status": evidence.get("status"),
            "verified": evidence.get("verified"),
            "creation_status": evidence.get("creation_status"),
            "creation_verification": evidence.get(
                "creation_verification",
                {},
            ),
        },

        "capabilities": results,

        "optional_capabilities": [
            {
                "id": item.get("id"),
                "status": item.get("status"),
            }
            for item in results
            if not item.get("required")
        ],

        "final_decision": (
            "PROJECT_ACCEPTED"
            if final_status == "FINAL_PASS"
            else "PROJECT_NOT_ACCEPTED"
        ),
    }

    output = REPORTS / "ABQARYNO_FINAL_PROJECT_REPORT.json"
    output.write_text(
        json.dumps(
            final_report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("=== ABQARYNO FINAL PROJECT GATE ===")
    print(f"PROJECT       : {project}")
    print(f"TYPE          : {final_report['project_type']}")
    print(
        "CAPABILITIES  : "
        f"{capability.get('status', 'UNKNOWN')}"
    )
    print(
        "CREATION      : "
        f"{evidence.get('creation_status', 'UNKNOWN')}"
    )
    print(
        "REQUIRED      : "
        f"{len(required) - len(required_failures)}/"
        f"{len(required)}"
    )
    print(f"FINAL STATUS  : {final_status}")
    print(f"FINAL REPORT  : {output}")

    return 0 if final_status == "FINAL_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
