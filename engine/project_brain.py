from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PLANS = ROOT / "plans"
REPORTS = ROOT / "reports"

BRAIN_FILE = PLANS / "abqaryno-project-brain.json"
REPORT_FILE = REPORTS / "abqaryno-project-brain-report.json"


class ProjectBrain:
    VERSION = "2.0"

    def __init__(self, project_name: str, idea: str = ""):
        self.data = {
            "brain": "ABQARYNO_PROJECT_BRAIN",
            "version": self.VERSION,
            "project": {
                "name": project_name,
                "idea": idea,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            "lifecycle": [
                "idea",
                "understanding",
                "requirements",
                "approved_requirements",
                "screen_design",
                "approved_screens",
                "architecture",
                "environment",
                "database",
                "backend",
                "frontend",
                "integration",
                "runtime",
                "testing",
                "evidence",
                "repair",
                "regression",
                "version",
                "documentation",
                "deployment",
                "final_verification",
            ],
            "requirements": [],
            "screens": [],
            "contracts": [],
            "capabilities": [],
            "architecture": {},
            "environment": {},
            "database": {},
            "implementation": {},
            "tests": [],
            "evidence": [],
            "status": "INITIALIZED",
        }

    def add(self, section: str, value):
        if section not in self.data:
            raise KeyError(section)
        if isinstance(self.data[section], list):
            self.data[section].append(value)
        elif isinstance(self.data[section], dict):
            self.data[section].update(value)
        else:
            self.data[section] = value

    def save(self):
        PLANS.mkdir(exist_ok=True)
        REPORTS.mkdir(exist_ok=True)

        self.data["updated_at"] = datetime.now(timezone.utc).isoformat()

        BRAIN_FILE.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        report = {
            "report": "ABQARYNO_PROJECT_BRAIN_REPORT",
            "version": self.VERSION,
            "status": "PASS",
            "brain_file": str(BRAIN_FILE),
            "sections": {
                key: len(value) if isinstance(value, list) else bool(value)
                for key, value in self.data.items()
                if key not in {"project", "lifecycle"}
            },
        }

        REPORT_FILE.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return self.data


def main():
    brain = ProjectBrain(
        "مشروع عبقرينو",
        "منصة إنشاء البرامج من فكرة المستخدم حتى المشروع النهائي",
    )
    brain.save()

    print("PROJECT_BRAIN_STATUS=PASS")
    print(f"BRAIN={BRAIN_FILE}")
    print(f"REPORT={REPORT_FILE}")


if __name__ == "__main__":
    main()
