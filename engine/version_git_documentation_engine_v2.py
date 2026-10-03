from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLANS = ROOT / "plans"
REPORTS = ROOT / "reports"

PLAN_FILE = PLANS / "abqaryno-version-git-documentation-v2.json"
REPORT_FILE = REPORTS / "abqaryno-version-git-documentation-v2-report.json"


class VersionGitDocumentationEngineV2:
    VERSION = "2.0"

    def git_status(self):
        try:
            result = subprocess.run(
                ["git", "status", "--short"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=10,
            )
            return {
                "available": result.returncode == 0,
                "status": result.stdout.splitlines(),
            }
        except Exception as exc:
            return {
                "available": False,
                "status": [],
                "error": str(exc),
            }

    def build(self, project_name: str):
        data = {
            "engine": "ABQARYNO_VERSION_GIT_DOCUMENTATION_ENGINE",
            "version": self.VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "project": project_name,

            "versioning": {
                "version_scheme": "MAJOR.MINOR.PATCH",
                "current_version": "0.1.0",
                "snapshot_before_release": True,
                "release_notes": "PLANNED",
            },

            "git": {
                "repository": "PLANNED",
                "branch_strategy": "PLANNED",
                "commit_strategy": "PLANNED",
                "remote": "PLANNED",
                "current_status": self.git_status(),
            },

            "documentation": {
                "README": "PLANNED",
                "architecture": "PLANNED",
                "requirements": "PLANNED",
                "api": "PLANNED",
                "database": "PLANNED",
                "deployment": "PLANNED",
                "testing": "PLANNED",
                "change_log": "PLANNED",
            },

            "traceability": {
                "requirements_to_code": True,
                "screens_to_code": True,
                "code_to_tests": True,
                "tests_to_evidence": True,
                "release_to_snapshot": True,
            },

            "approval": {
                "required": True,
                "status": "PENDING",
            },

            "status": "READY_FOR_VERSIONING",
        }

        PLANS.mkdir(exist_ok=True)
        REPORTS.mkdir(exist_ok=True)

        PLAN_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        REPORT_FILE.write_text(
            json.dumps(
                {
                    "report": "ABQARYNO_VERSION_GIT_DOCUMENTATION_REPORT",
                    "version": self.VERSION,
                    "status": "PASS",
                    "versioning_planned": True,
                    "git_planned": True,
                    "documentation_planned": True,
                    "approval_required": True,
                    "release_execution": "NOT_RUN",
                    "plan": str(PLAN_FILE),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return data


if __name__ == "__main__":
    VersionGitDocumentationEngineV2().build("مشروع عبقرينو")
    print("VERSION_GIT_DOCUMENTATION_V2_CREATED")
