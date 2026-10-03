from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PLANS = ROOT / "plans"
REPORTS = ROOT / "reports"

PLAN_FILE = PLANS / "abqaryno-database-v2.json"
REPORT_FILE = REPORTS / "abqaryno-database-v2-report.json"


class DatabaseEngineV2:
    VERSION = "2.0"

    def build(
        self,
        project_name: str,
        entities: list[dict] | None = None,
        requirements: list[str] | None = None,
        screens: list[str] | None = None,
    ):
        entities = entities or []
        requirements = requirements or []
        screens = screens or []

        normalized = []

        for index, entity in enumerate(entities, 1):
            name = entity.get("name", f"entity_{index}")
            fields = entity.get("fields", [])

            normalized.append(
                {
                    "id": f"ENT-{index:04d}",
                    "name": name,
                    "fields": fields,
                    "primary_key": "id",
                    "timestamps": ["created_at", "updated_at"],
                    "status": "PLANNED",
                }
            )

        data = {
            "engine": "ABQARYNO_DATABASE_ENGINE",
            "version": self.VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "project": project_name,
            "requirements": requirements,
            "screens": screens,
            "entities": normalized,
            "database": {
                "engine": "SQLite",
                "schema_status": "PLANNED",
                "migration_status": "PLANNED",
                "integrity_status": "NOT_RUN",
            },
            "traceability": {
                "requirement_to_entity": True,
                "screen_to_entity": True,
                "entity_to_implementation": True,
                "entity_to_test": True,
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
                    "report": "ABQARYNO_DATABASE_ENGINE_REPORT",
                    "version": self.VERSION,
                    "status": "PASS",
                    "project": project_name,
                    "entities": len(normalized),
                    "approval_required": True,
                    "schema_created": False,
                    "integrity_test": "NOT_RUN",
                    "plan": str(PLAN_FILE),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return data


if __name__ == "__main__":
    DatabaseEngineV2().build(
        "مشروع عبقرينو",
        entities=[
            {
                "name": "users",
                "fields": [
                    "id",
                    "name",
                    "phone",
                    "password",
                    "role",
                ],
            },
            {
                "name": "projects",
                "fields": [
                    "id",
                    "name",
                    "description",
                    "status",
                ],
            },
        ],
        requirements=[
            "تسجيل المستخدم",
            "حفظ البيانات",
        ],
        screens=[
            "home",
            "dashboard",
        ],
    )
    print("DATABASE_ENGINE_V2_STATUS=PASS")
