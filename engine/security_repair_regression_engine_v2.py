from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLANS = ROOT / "plans"
REPORTS = ROOT / "reports"

PLAN_FILE = PLANS / "abqaryno-security-repair-regression-v2.json"
REPORT_FILE = REPORTS / "abqaryno-security-repair-regression-v2-report.json"


class SecurityRepairRegressionEngineV2:
    VERSION = "2.0"

    def build(self, project_name: str):
        data = {
            "engine": "ABQARYNO_SECURITY_REPAIR_REGRESSION_ENGINE",
            "version": self.VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "project": project_name,

            "security": {
                "authentication": "PLANNED",
                "authorization": "PLANNED",
                "input_validation": "PLANNED",
                "output_validation": "PLANNED",
                "secret_detection": "PLANNED",
                "file_upload_security": "PLANNED",
                "audit_logging": "PLANNED",
            },

            "repair": {
                "discovery": "PLANNED",
                "classification": "PLANNED",
                "repair_plan": "PLANNED",
                "approval_required": True,
                "automatic_safe_repairs": True,
                "snapshot_before_change": True,
                "repair_execution": "NOT_RUN",
                "verification_after_repair": "NOT_RUN",
            },

            "regression": {
                "baseline": "PLANNED",
                "pre_repair_tests": "NOT_RUN",
                "post_repair_tests": "NOT_RUN",
                "changed_files": [],
                "failed_tests": [],
                "status": "PENDING",
            },

            "safety_gates": {
                "discover_before_repair": True,
                "evidence_before_repair": True,
                "approval_before_risky_change": True,
                "snapshot_before_change": True,
                "verify_after_change": True,
                "regression_after_change": True,
            },

            "approval": {
                "status": "PENDING",
                "mode": "YES_NO",
            },

            "status": "READY_FOR_APPROVAL",
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
                    "report": "ABQARYNO_SECURITY_REPAIR_REGRESSION_REPORT",
                    "version": self.VERSION,
                    "status": "PASS",
                    "security_planned": True,
                    "repair_planned": True,
                    "regression_planned": True,
                    "approval_required": True,
                    "repair_execution": "NOT_RUN",
                    "plan": str(PLAN_FILE),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return data


if __name__ == "__main__":
    SecurityRepairRegressionEngineV2().build("مشروع عبقرينو")
    print("SECURITY_REPAIR_REGRESSION_V2_CREATED")
