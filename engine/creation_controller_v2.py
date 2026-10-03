from pathlib import Path
from datetime import datetime, timezone
import json


ROOT = Path(__file__).resolve().parents[1]
PLANS = ROOT / "plans"
REPORTS = ROOT / "reports"

STATE_FILE = PLANS / "abqaryno-creation-controller-v2.json"
REPORT_FILE = REPORTS / "abqaryno-creation-controller-v2-report.json"


class CreationControllerV2:
    VERSION = "2.0"

    STAGES = (
        "IDEA",
        "UNDERSTANDING",
        "REQUIREMENTS",
        "APPROVED_REQUIREMENTS",
        "SCREEN_DESIGN",
        "APPROVED_SCREENS",
        "BUILD_APPROVAL",
        "ARCHITECTURE",
        "DATABASE",
        "BACKEND",
        "FRONTEND",
        "RUNTIME",
        "TESTING",
        "EVIDENCE",
        "SECURITY",
        "REGRESSION",
        "FINAL_VERIFICATION",
        "DEPLOYMENT",
        "RELEASE",
    )

    def contract(self):
        return {
            "controller": "CreationControllerV2",
            "version": self.VERSION,
            "status": "LINKED",
            "execution": "NOT_RUN",
            "safe_stop": True,
            "current_stage": "IDEA",
            "next_stage": "UNDERSTANDING",
            "project_status": "NOT_STARTED",
            "approval_status": "PENDING",
            "evidence_status": "PENDING",
            "routes": {
                "idea": "/create",
                "understanding": "/create/understanding",
                "requirements": "/create/requirements",
                "screens": "/create/plan",
                "build": "/create/build",
            },
            "approval_chain": [
                {
                    "stage": "REQUIREMENTS",
                    "approval": "YES_NO",
                    "required": True,
                    "status": "PENDING",
                },
                {
                    "stage": "SCREEN_DESIGN",
                    "approval": "USER_SELECTS_VARIANT",
                    "required": True,
                    "status": "PENDING",
                },
                {
                    "stage": "BUILD_APPROVAL",
                    "approval": "YES_NO",
                    "required": True,
                    "status": "PENDING",
                },
            ],
            "transition_rules": {
                "requirements_before_screens": True,
                "approved_requirements_before_build": True,
                "approved_screens_before_build": True,
                "build_approval_before_generation": True,
                "generation_before_runtime": True,
                "runtime_before_final_verification": True,
                "final_verification_before_deployment": True,
                "deployment_before_release": True,
            },
            "blocked_actions": [
                "CREATE_PROJECT",
                "RUN_ENGINE",
                "RUN_PROJECT",
                "RUN_LEGAL_PROJECT",
                "DEPLOY",
                "RELEASE",
            ],
        }

    def initial_state(self):
        return {
            "controller": "CreationControllerV2",
            "version": self.VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "execution": "NOT_RUN",
            "project_execution": "NOT_RUN",
            "legal_project_execution": "NOT_RUN",
            "current_stage": "IDEA",
            "next_stage": "UNDERSTANDING",
            "project_status": "NOT_STARTED",
            "approval_status": "PENDING",
            "evidence_status": "PENDING",
            "safe_stop": True,
        }

    def approval_gate(self):
        return {
            "status": "LOCKED",
            "execution": "NOT_RUN",
            "requirements": "PENDING",
            "screens": "PENDING",
            "build": "PENDING",
            "can_generate": False,
            "reason": "REQUIRED_APPROVALS_NOT_COMPLETE",
        }

    def artifact_contract(self):
        return {
            "status": "LINKED",
            "execution": "NOT_RUN",
            "plans": str(PLANS),
            "reports": str(REPORTS),
            "controller_state": str(STATE_FILE),
            "controller_report": str(REPORT_FILE),
            "master": str(engine_path("master_orchestrator_v2.py")),
            "build_gate": str(engine_path("studio_build_gate_v2.py")),
        }


def engine_path(name):
    return ROOT / "engine" / name
