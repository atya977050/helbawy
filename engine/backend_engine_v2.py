from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PLANS = ROOT / "plans"
REPORTS = ROOT / "reports"

PLAN_FILE = PLANS / "abqaryno-backend-v2.json"
REPORT_FILE = REPORTS / "abqaryno-backend-v2-report.json"


class BackendEngineV2:
    VERSION = "2.0"

    def build(
        self,
        project_name: str,
        requirements: list[str] | None = None,
        entities: list[str] | None = None,
        capabilities: list[str] | None = None,
    ):
        requirements = requirements or []
        entities = entities or []
        capabilities = capabilities or []

        routes = [
            {
                "id": "API-0001",
                "method": "GET",
                "path": "/api/health",
                "purpose": "health_check",
                "status": "PLANNED",
            },
            {
                "id": "API-0002",
                "method": "GET",
                "path": "/api/status",
                "purpose": "application_status",
                "status": "PLANNED",
            },
        ]

        services = [
            {
                "id": f"SVC-{index:04d}",
                "name": capability,
                "status": "PLANNED",
            }
            for index, capability in enumerate(capabilities, 1)
        ]

        data = {
            "engine": "ABQARYNO_BACKEND_ENGINE",
            "version": self.VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "project": project_name,
            "requirements": requirements,
            "entities": entities,
            "capabilities": capabilities,
            "routes": routes,
            "services": services,
            "contracts": {
                "request_validation": True,
                "response_schema": True,
                "error_handling": True,
                "authentication_boundary": True,
                "authorization_boundary": True,
                "traceability": True,
            },
            "security": {
                "authentication": "PLANNED",
                "authorization": "PLANNED",
                "input_validation": "PLANNED",
                "audit": "PLANNED",
            },
            "testing": {
                "syntax": "NOT_RUN",
                "api": "NOT_RUN",
                "integration": "NOT_RUN",
                "runtime": "NOT_RUN",
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
                    "report": "ABQARYNO_BACKEND_ENGINE_REPORT",
                    "version": self.VERSION,
                    "status": "PASS",
                    "routes": len(routes),
                    "services": len(services),
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
    BackendEngineV2().build(
        "مشروع عبقرينو",
        requirements=[
            "تسجيل المستخدم",
            "حفظ البيانات",
        ],
        entities=[
            "users",
            "projects",
        ],
        capabilities=[
            "authentication",
            "database",
            "api",
        ],
    )
    print("BACKEND_ENGINE_V2_STATUS=PASS")
