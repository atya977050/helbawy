from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLANS = ROOT / "plans"
REPORTS = ROOT / "reports"

MATRIX = PLANS / "abqaryno-platform-capabilities.json"


def load_matrix():
    if not MATRIX.exists():
        raise SystemExit("CAPABILITY_MATRIX_MISSING")
    return json.loads(MATRIX.read_text(encoding="utf-8"))


def exists(root: Path, relative: str) -> bool:
    return (root / relative).exists()


def detect_project(root: Path) -> dict:
    return {
        "python": any(root.glob("**/*.py")),
        "node": exists(root, "package.json"),
        "server_py": exists(root, "server/server.py"),
        "server_js": exists(root, "server.js"),
        "database": (
            exists(root, "database/schema.sql")
            or exists(root, "database")
        ),
        "frontend": (
            exists(root, "public/index.html")
            or exists(root, "frontend")
            or exists(root, "src")
        ),
        "routes": exists(root, "routes"),
        "services": exists(root, "services"),
        "requirements": exists(root, ".abqaryno-requirements.json"),
        "auth": any(
            p.exists()
            for p in [
                root / "middleware/auth.py",
                root / "middleware/auth.js",
                root / "routes/auth.py",
                root / "routes/auth.js",
                root / "services/auth.py",
                root / "services/auth.js",
            ]
        ),
    }


def python_syntax_test(root: Path) -> tuple[bool, str]:
    files = [
        p for p in root.rglob("*.py")
        if "__pycache__" not in p.parts
    ]

    failures = []

    for path in files:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(path)],
            cwd=root,
            text=True,
            capture_output=True,
        )

        if result.returncode != 0:
            failures.append(
                f"{path.relative_to(root)}: "
                f"{result.stderr[-1000:]}"
            )

    return not failures, "\n".join(failures)


def verify_capability(cap, project):
    cid = cap["id"]
    root = project["root"]

    if cid == "requirements":
        requirements_file = root / ".abqaryno-requirements.json"

        if not requirements_file.exists():
            return "FAIL"

        try:
            requirements = json.loads(
                requirements_file.read_text(encoding="utf-8")
            )
        except Exception:
            return "FAIL"

        if not isinstance(requirements, dict):
            return "FAIL"

        screens = requirements.get("screens", [])
        capabilities = requirements.get("capabilities", [])

        return (
            "PASS"
            if isinstance(screens, list)
            and len(screens) > 0
            and isinstance(capabilities, list)
            and len(capabilities) > 0
            else "FAIL"
        )

    if cid == "screen_design":
        return "PASS" if project["frontend"] else "FAIL"

    if cid == "project_architecture":
        if project["python"] and project["server_py"]:
            return "PASS"
        if project["node"] and project["server_js"]:
            return "PASS"
        return "FAIL"

    if cid == "database":
        return "PASS" if project["database"] else "FAIL"

    if cid == "authentication":
        if project["auth"]:
            return "PASS"
        if project["server_js"]:
            try:
                text = (root / "server.js").read_text(encoding="utf-8")
                auth_markers = [
                    "/api/auth/login",
                    "/api/auth/logout",
                    "getAuthenticatedUser",
                    "requireAuth",
                    "password_hash",
                    "auth_sessions",
                ]
                matched = sum(1 for marker in auth_markers if marker in text)
                return "PASS" if matched >= 4 else "NOT_IMPLEMENTED"
            except Exception:
                return "NOT_IMPLEMENTED"
        return "NOT_IMPLEMENTED"

    if cid == "api":
        if project["server_py"] and project["routes"]:
            return "PASS"
        if project["server_js"]:
            try:
                text = (root / "server.js").read_text(
                    encoding="utf-8"
                )
                return "PASS" if "/api/" in text else "FAIL"
            except Exception:
                return "FAIL"
        return "FAIL"

    if cid == "responsive_ui":
        return "PASS" if project["frontend"] else "FAIL"

    if cid in {
        "realtime",
        "file_uploads",
        "notifications",
        "payments",
        "search",
    }:
        return "NOT_IMPLEMENTED"

    if cid == "security":
        if not project["server_js"]:
            return "NOT_IMPLEMENTED"

        try:
            source = (root / "server.js").read_text(encoding="utf-8")
        except Exception:
            return "FAIL"

        security_markers = [
            "crypto.scryptSync",
            "password_hash",
            "password_salt",
            "auth_sessions",
            "Bearer ",
            "requireAuth",
            "express.json({ limit:",
            "app.use((err, req, res, next)",
        ]

        matched = sum(
            1 for marker in security_markers
            if marker in source
        )

        return "PASS" if matched >= 6 else "NOT_IMPLEMENTED"

    if cid == "runtime":
        if project["server_py"]:
            passed, _ = python_syntax_test(root)
            return "PASS" if passed else "FAIL"

        if project["server_js"]:
            result = subprocess.run(
                ["node", "--check", "server.js"],
                cwd=root,
                text=True,
                capture_output=True,
            )
            return "PASS" if result.returncode == 0 else "FAIL"

        return "FAIL"

    if cid == "verification":
        evidence_file = root / ".abqaryno-evidence.json"

        if not evidence_file.exists():
            return "FAIL"

        try:
            evidence = json.loads(
                evidence_file.read_text(encoding="utf-8")
            )
        except Exception:
            return "FAIL"

        creation = evidence.get("creation_verification", {})
        gate = evidence.get("creation_gate", {})

        if (
            evidence.get("verified") is True
            and evidence.get("status") == "PASS"
            and creation.get("status") == "PASSED"
            and gate.get("status") == "PASSED"
        ):
            return "PASS"

        return "FAIL"

    if cid == "evidence":
        evidence_file = root / ".abqaryno-evidence.json"
        if not evidence_file.exists():
            return "FAIL"
        try:
            evidence = json.loads(
                evidence_file.read_text(encoding="utf-8")
            )
        except Exception:
            return "FAIL"

        if not isinstance(evidence, dict):
            return "FAIL"

        if evidence.get("status") == "PASS" and evidence.get("verified") is True:
            return "PASS"

        return "FAIL"

    return "NOT_IMPLEMENTED"


def main() -> int:
    matrix = load_matrix()

    if len(sys.argv) < 2:
        raise SystemExit(
            "USAGE: python engine/capability_verifier.py PROJECT_PATH"
        )

    project_root = Path(sys.argv[1]).expanduser().resolve()

    if not project_root.exists():
        raise SystemExit(
            f"PROJECT_NOT_FOUND: {project_root}"
        )

    project = detect_project(project_root)
    project["root"] = project_root

    results = []

    for capability in matrix["capabilities"]:
        status = verify_capability(capability, project)

        results.append({
            "id": capability["id"],
            "name": capability["name"],
            "required": capability["required"],
            "verification": capability["verification"],
            "status": status,
        })

    required_failures = [
        item for item in results
        if item["required"] and item["status"] != "PASS"
    ]

    overall = not required_failures

    report = {
        "report": "ABQARYNO_CAPABILITY_VERIFICATION",
        "version": "2.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project": str(project_root),
        "project_type": (
            "python"
            if project["server_py"]
            else "node"
            if project["server_js"]
            else "unknown"
        ),
        "status": "PASS" if overall else "FAIL",
        "results": results,
        "required_failures": [
            item["id"] for item in required_failures
        ],
    }

    report_path = (
        REPORTS / "abqaryno-capability-verification.json"
    )

    report_path.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\n=== ABQARYNO CAPABILITY VERIFICATION v2 ===")

    for item in results:
        print(
            f"{item['status']:16} | "
            f"{item['id']}"
        )

    print()
    print(f"PROJECT_TYPE : {report['project_type']}")
    print(f"PROJECT      : {project_root}")
    print(f"REPORT       : {report_path}")
    print(
        "CAPABILITY_STATUS="
        f"{'PASS' if overall else 'FAIL'}"
    )

    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
