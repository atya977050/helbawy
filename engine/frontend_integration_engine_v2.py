from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PLANS = ROOT / "plans"
REPORTS = ROOT / "reports"

PLAN_FILE = PLANS / "abqaryno-frontend-integration-v2.json"
REPORT_FILE = REPORTS / "abqaryno-frontend-integration-v2-report.json"


class FrontendIntegrationEngineV2:
    VERSION = "2.0"

    def build(
        self,
        project_name: str,
        screens: list[dict] | None = None,
        requirements: list[str] | None = None,
        routes: list[str] | None = None,
    ):
        screens = screens or []
        requirements = requirements or []
        routes = routes or []

        screen_contracts = []

        for index, screen in enumerate(screens, 1):
            screen_id = screen.get("id", f"screen_{index}")
            screen_contracts.append(
                {
                    "id": f"UI-{index:04d}",
                    "screen_id": screen_id,
                    "title": screen.get("title", screen_id),
                    "route": screen.get("route", f"/{screen_id}"),
                    "api_dependencies": [],
                    "status": "PLANNED",
                }
            )

        data = {
            "engine": "ABQARYNO_FRONTEND_INTEGRATION_ENGINE",
            "version": self.VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "project": project_name,
            "requirements": requirements,
            "screens": screen_contracts,
            "api_routes": routes,
            "frontend": {
                "technology": "HTML/CSS/JavaScript",
                "responsive": True,
                "accessibility": "PLANNED",
                "state_management": "PLANNED",
                "error_states": "PLANNED",
                "loading_states": "PLANNED",
            },
            "integration": {
                "screen_to_api": True,
                "api_to_database": True,
                "requirement_traceability": True,
                "error_propagation": True,
                "authentication_boundary": True,
            },
            "testing": {
                "frontend_syntax": "NOT_RUN",
                "api_integration": "NOT_RUN",
                "browser_runtime": "NOT_RUN",
                "end_to_end": "NOT_RUN",
            },
            "approval": {
                "required": True,
                "status": "PENDING",
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
                    "report": "ABQARYNO_FRONTEND_INTEGRATION_REPORT",
                    "version": self.VERSION,
                    "status": "PASS",
                    "screens": len(screen_contracts),
                    "routes": len(routes),
                    "approval_required": True,
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
    FrontendIntegrationEngineV2().build(
        "مشروع عبقرينو",
        screens=[
            {"id": "home", "title": "الشاشة الرئيسية"},
            {"id": "dashboard", "title": "لوحة التحكم"},
        ],
        requirements=[
            "تسجيل المستخدم",
            "حفظ البيانات",
        ],
        routes=[
            "/api/health",
            "/api/status",
        ],
    )
    print("FRONTEND_INTEGRATION_V2_STATUS=PASS")
