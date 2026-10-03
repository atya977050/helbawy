from pathlib import Path


class StudioFlowContractV2:
    VERSION = "2.0"

    FLOW = (
        {
            "stage": "IDEA",
            "route": "/create",
            "approval": None,
            "next": "UNDERSTANDING",
            "execution": "NOT_RUN",
        },
        {
            "stage": "UNDERSTANDING",
            "route": "/create/understanding",
            "approval": None,
            "next": "REQUIREMENTS",
            "execution": "NOT_RUN",
        },
        {
            "stage": "REQUIREMENTS",
            "route": "/create/requirements",
            "approval": "YES_NO",
            "next": "APPROVED_REQUIREMENTS",
            "execution": "NOT_RUN",
        },
        {
            "stage": "SCREEN_DESIGN",
            "route": "/create/plan",
            "approval": "USER_SELECTS_VARIANT",
            "next": "APPROVED_SCREENS",
            "execution": "NOT_RUN",
        },
        {
            "stage": "BUILD_APPROVAL",
            "route": "/create/build",
            "approval": "YES_NO",
            "next": "ARCHITECTURE",
            "execution": "NOT_RUN",
        },
    )

    @classmethod
    def contract(cls):
        return {
            "name": "StudioFlowContractV2",
            "version": cls.VERSION,
            "status": "LINKED",
            "execution": "NOT_RUN",
            "safe_stop": True,
            "flow": list(cls.FLOW),
            "rules": {
                "requirements_approval_required": True,
                "screen_approval_required": True,
                "build_approval_required": True,
                "generation_before_build_approval": False,
                "engine_execution_before_build_approval": False,
                "project_execution": "NOT_RUN",
                "legal_project_execution": "NOT_RUN",
                "deployment": "BLOCKED",
                "release": "BLOCKED",
            },
        }
