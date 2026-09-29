from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)


def command_version(command: str) -> str | None:
    path = shutil.which(command)
    if not path:
        return None

    try:
        result = subprocess.run(
            [command, "--version"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=10,
        )
        return (result.stdout or result.stderr).strip()
    except Exception as exc:
        return f"ERROR: {exc}"


def collect_files(directory: Path, max_depth: int = 3) -> list[str]:
    if not directory.exists():
        return []

    result = []

    for path in directory.rglob("*"):
        if not path.is_file():
            continue

        try:
            relative = path.relative_to(ROOT)
        except ValueError:
            continue

        if len(relative.parts) <= max_depth:
            result.append(str(relative))

    return sorted(result)


def check_python_file(path: Path) -> dict:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
        )

        return {
            "file": str(path.relative_to(ROOT)),
            "passed": result.returncode == 0,
            "exit_code": result.returncode,
            "stderr": result.stderr[-2000:],
        }

    except Exception as exc:
        return {
            "file": str(path.relative_to(ROOT)),
            "passed": False,
            "exit_code": None,
            "stderr": str(exc),
        }


def main() -> int:
    python_files = sorted(ROOT.rglob("*.py"))

    # Ignore generated cache files.
    python_files = [
        path for path in python_files
        if "__pycache__" not in path.parts
    ]

    python_tests = [
        check_python_file(path)
        for path in python_files
    ]

    required_paths = [
        "engine",
        "studio",
        "core",
        "reports",
        "plans",
        "studio/server.py",
        "engine/creation.py",
        "engine/abqaryno_master_factory.py",
    ]

    required = {
        item: (ROOT / item).exists()
        for item in required_paths
    }

    checks = {
        "required_paths": all(required.values()),
        "python_files_compile": all(
            item["passed"] for item in python_tests
        ),
        "studio_server_exists": (ROOT / "studio/server.py").exists(),
        "creation_engine_exists": (ROOT / "engine/creation.py").exists(),
        "master_factory_exists": (
            ROOT / "engine/abqaryno_master_factory.py"
        ).exists(),
    }

    overall = all(checks.values())

    report = {
        "report": "ABQARYNO_BASELINE_REPORT",
        "version": "1.0",
        "status": "PASS" if overall else "FAIL",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_root": str(ROOT),
        "runtime": {
            "python": sys.version,
            "python_executable": sys.executable,
            "node": command_version("node"),
            "npm": command_version("npm"),
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "required_paths": required,
        "checks": checks,
        "python_file_count": len(python_files),
        "python_compile_tests": python_tests,
        "top_level_files": collect_files(ROOT, 2),
        "engine_files": collect_files(ROOT / "engine", 2),
        "studio_files": collect_files(ROOT / "studio", 3),
    }

    report_path = REPORTS / "ABQARYNO_BASELINE_REPORT.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n=== ABQARYNO BASELINE ENGINE ===")
    print(f"Project : {ROOT}")
    print(f"Python  : {command_version('python')}")
    print(f"Node    : {command_version('node') or 'NOT_FOUND'}")
    print(f"NPM     : {command_version('npm') or 'NOT_FOUND'}")
    print(f"Python files checked: {len(python_files)}")

    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'} | {name}")

    print(f"\nREPORT: {report_path}")
    print(f"BASELINE_STATUS={'PASS' if overall else 'FAIL'}")

    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
