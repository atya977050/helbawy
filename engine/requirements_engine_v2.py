from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PLANS = ROOT / "plans"
REPORTS = ROOT / "reports"

PLAN_FILE = PLANS / "abqaryno-requirements-v2.json"
REPORT_FILE = REPORTS / "abqaryno-requirements-v2-report.json"


class RequirementsEngineV2:
    VERSION = "2.0"

    def build(self, idea: str, requirements: list[str] | None = None):
        requirements = requirements or []

        data = {
            "engine": "ABQARYNO_REQUIREMENTS_ENGINE",
            "version": self.VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "idea": idea,
            "requirements": [
                {
                    "id": f"REQ-{index:04d}",
                    "text": item,
                    "status": "PENDING_APPROVAL",
                    "approved": False,
                }
                for index, item in enumerate(requirements, 1)
            ],
            "approval": {
                "mode": "YES_NO",
                "approved_count": 0,
                "rejected_count": 0,
                "pending_count": len(requirements),
                "status": "PENDING",
            },
        }

        PLAN_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        REPORT_FILE.write_text(
            json.dumps(
                {
                    "report": "ABQARYNO_REQUIREMENTS_ENGINE_REPORT",
                    "version": self.VERSION,
                    "status": "PASS",
                    "requirements_count": len(requirements),
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
    RequirementsEngineV2().build(
        "إنشاء برنامج من فكرة المستخدم",
        [
            "تسجيل المستخدم",
            "حفظ البيانات",
            "إدارة الشاشات",
            "إدارة الصلاحيات",
        ],
    )
    print("REQUIREMENTS_ENGINE_V2_STATUS=PASS")
