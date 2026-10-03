
from engine.studio_approval_state_v2 import StudioApprovalStateV2


class BuildApprovalBridgeV2:
    VERSION = "2.0"

    @classmethod
    def approve(cls, approved):
        state = StudioApprovalStateV2.set_build(bool(approved))

        evaluation = StudioApprovalStateV2.evaluate(state)

        return {
            "state": state,
            "evaluation": evaluation,
        }

    @classmethod
    def state(cls):
        state = StudioApprovalStateV2.load()
        evaluation = StudioApprovalStateV2.evaluate(state)

        return {
            "stage": "BUILD_APPROVAL",
            "route": "/create/build",
            "requirements_approved":
                state["approvals"]["requirements"]["approved"],
            "screens_approved":
                state["approvals"]["screens"]["approved"],
            "build_approved":
                state["approvals"]["build"]["approved"],
            "selected_variant":
                state["approvals"]["screens"].get("selected_variant"),
            "generation_allowed":
                evaluation["generation_allowed"],
            "execution": "NOT_RUN",
            "safe_stop": evaluation["safe_stop"],
        }

    @classmethod
    def contract(cls):
        return {
            "status": "LINKED",
            "execution": "NOT_RUN",
            "route": "/create/build",
            "approval_type": "YES_NO",
            "controller": "StudioApprovalStateV2",
            "required_before_generation": [
                "REQUIREMENTS_APPROVAL",
                "SCREEN_APPROVAL",
                "BUILD_APPROVAL",
            ],
            "generation_rule": "ALL_REQUIRED_APPROVALS",
            "generation_allowed": False,
            "execution_allowed": False,
            "deployment_allowed": False,
            "release_allowed": False,
            "safe_stop": True,
        }
