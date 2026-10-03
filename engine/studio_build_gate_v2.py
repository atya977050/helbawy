from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class StudioBuildGateV2:
    VERSION = "2.0"

    REQUIRED_APPROVALS = (
        "requirements",
        "screens",
        "build",
    )

    BLOCKED_ACTIONS = (
        "CREATE_PROJECT",
        "RUN_ENGINE",
        "RUN_PROJECT",
        "RUN_LEGAL_PROJECT",
        "DEPLOY",
        "RELEASE",
    )

    def contract(self):
        return {
            "engine": "StudioBuildGateV2",
            "version": self.VERSION,
            "status": "LINKED",
            "execution": "NOT_RUN",
            "gate": "STUDIO_BUILD_GATE",
            "route": "/create/build",
            "mode": "APPROVAL_BEFORE_EXECUTION",
            "required_approvals": [
                {
                    "id": "requirements",
                    "source": "/create/requirements",
                    "mode": "YES_NO",
                    "required": True,
                    "status": "PENDING",
                },
                {
                    "id": "screens",
                    "source": "/create/plan",
                    "mode": "USER_SELECTS_VARIANT",
                    "required": True,
                    "status": "PENDING",
                },
                {
                    "id": "build",
                    "source": "/create/build",
                    "mode": "YES_NO",
                    "required": True,
                    "status": "PENDING",
                },
            ],
            "transition": {
                "from": "BUILD_APPROVAL",
                "to": "ARCHITECTURE",
                "condition": "ALL_REQUIRED_APPROVALS",
                "status": "LOCKED",
                "execution": "NOT_RUN",
            },
            "rules": {
                "requirements_must_be_approved": True,
                "screens_must_be_approved": True,
                "build_must_be_approved": True,
                "files_created_only_after_gate": True,
                "engine_execution_only_after_gate": True,
                "runtime_only_after_build": True,
                "deployment_blocked": True,
                "release_blocked": True,
            },
            "blocked_actions": list(self.BLOCKED_ACTIONS),
            "safe_stop": True,
        }

    def status(self):
        return {
            "gate": "STUDIO_BUILD_GATE",
            "status": "LOCKED",
            "execution": "NOT_RUN",
            "safe_stop": True,
        }
