from __future__ import annotations

import json
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PLANS = ROOT / "plans"
REPORTS = ROOT / "reports"

PLAN_FILE = PLANS / "abqaryno-architecture-environment.json"
REPORT_FILE = REPORTS / "abqaryno-architecture-environment-report.json"


class ArchitectureEnvironmentEngine:
    VERSION = "1.0"

    def scan_environment(self):
        return {
            "python": sys.version.split()[0],
            "node": shutil.which("node") is not None,
            "npm": shutil.which("npm") is not None,
            "platform": platform.platform(),
            "machine": platform.machine(),
        }

    def build(self, project_type="auto"):
        environment = self.scan_environment()

        if project_type == "auto":
            project_type = "python" if environment["python"] else "node"

        architecture = {
            "project_type": project_type,
            "architecture": (
                "Python modular web application"
                if project_type == "python"
                else "Node.js modular web application"
            ),
            "layers": [
                "public",
                "routes",
                "services",
                "database",
                "server",
            ],
            "principles": [
                "separation_of_concerns",
                "traceability",
                "testability",
                "evidence",
                "environment_compatibility",
            ],
        }

        data = {
            "engine": "ABQARYNO_ARCHITECTURE_ENVIRONMENT_ENGINE",
            "version": self.VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "environment": environment,
            "architecture": architecture,
            "compatibility": {
                "status": "PLANNED",
                "verified": False,
            },
        }

        PLAN_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        REPORT_FILE.write_text(
            json.dumps(
                {
                    "report": "ABQARYNO_ARCHITECTURE_ENVIRONMENT_REPORT",
                    "version": self.VERSION,
                    "status": "PASS",
                    "architecture_created": True,
                    "environment_detected": True,
                    "runtime_verification": "NOT_RUN",
                    "plan": str(PLAN_FILE),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return data


if __name__ == "__main__":
    ArchitectureEnvironmentEngine().build()
    print("ARCHITECTURE_ENVIRONMENT_STATUS=PASS")
