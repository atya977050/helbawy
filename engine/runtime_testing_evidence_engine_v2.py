from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLANS = ROOT / "plans"
REPORTS = ROOT / "reports"

PLAN_FILE = PLANS / "abqaryno-runtime-testing-evidence-v2.json"
REPORT_FILE = REPORTS / "abqaryno-runtime-testing-evidence-v2-report.json"


class RuntimeTestingEvidenceEngineV2:
    VERSION = "2.0"

    def build(self, project_name: str):
        data = {
            "engine": "ABQARYNO_RUNTIME_TESTING_EVIDENCE_ENGINE",
            "version": self.VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "project": project_name,

            "runtime": {
                "server_start": "NOT_RUN",
                "health_check": "NOT_RUN",
                "api_check": "NOT_RUN",
                "database_check": "NOT_RUN",
                "browser_check": "NOT_RUN",
            },

            "testing": {
                "unit": "NOT_RUN",
                "integration": "NOT_RUN",
                "end_to_end": "NOT_RUN",
                "regression": "NOT_RUN",
            },

            "evidence": {
                "logs": [],
                "screenshots": [],
                "api_results": [],
                "database_results": [],
                "test_results": [],
            },

            "gates": {
                "runtime_gate": "PENDING",
                "testing_gate": "PENDING",
                "evidence_gate": "PENDING",
            },

            "approval": {
                "required": True,
                "status": "PENDING",
            },

            "status": "READY_FOR_RUNTIME",
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
                    "report": "ABQARYNO_RUNTIME_TESTING_EVIDENCE_REPORT",
                    "version": self.VERSION,
                    "status": "PASS",
                    "runtime_verification": "NOT_RUN",
                    "testing": "NOT_RUN",
                    "evidence": "READY",
                    "approval_required": True,
                    "plan": str(PLAN_FILE),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return data


if __name__ == "__main__":
    RuntimeTestingEvidenceEngineV2().build("مشروع عبقرينو")
    print("RUNTIME_TESTING_EVIDENCE_V2_CREATED")
