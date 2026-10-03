from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PLANS = ROOT / "plans"
REPORTS = ROOT / "reports"

PLAN_FILE = PLANS / "abqaryno-screen-design-v2.json"
REPORT_FILE = REPORTS / "abqaryno-screen-design-v2-report.json"


class ScreenDesignEngineV2:
    VERSION = "2.0"

    def propose(self, screens: list[dict]):
        proposals = []

        for screen in screens:
            sid = screen["id"]

            proposals.append(
                {
                    "screen_id": sid,
                    "title": screen.get("title", sid),
                    "variants": [
                        {
                            "variant": 1,
                            "layout": "لوحة احترافية",
                            "status": "PENDING_APPROVAL",
                        },
                        {
                            "variant": 2,
                            "layout": "بطاقات حديثة",
                            "status": "PENDING_APPROVAL",
                        },
                        {
                            "variant": 3,
                            "layout": "إدارة سجلات",
                            "status": "PENDING_APPROVAL",
                        },
                    ],
                    "approved_variant": None,
                }
            )

        data = {
            "engine": "ABQARYNO_SCREEN_DESIGN_ENGINE",
            "version": self.VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "approval_mode": "USER_SELECTS_VARIANT",
            "proposals": proposals,
        }

        PLAN_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        REPORT_FILE.write_text(
            json.dumps(
                {
                    "report": "ABQARYNO_SCREEN_DESIGN_REPORT",
                    "version": self.VERSION,
                    "status": "PASS",
                    "screens": len(proposals),
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
    ScreenDesignEngineV2().propose(
        [
            {"id": "home", "title": "الشاشة الرئيسية"},
            {"id": "dashboard", "title": "لوحة التحكم"},
        ]
    )
    print("SCREEN_DESIGN_V2_STATUS=PASS")
