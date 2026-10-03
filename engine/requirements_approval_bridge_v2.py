
from engine.studio_approval_state_v2 import StudioApprovalStateV2


class RequirementsApprovalBridgeV2:
    VERSION = "2.0"

    @classmethod
    def approve(cls, approved):
        return StudioApprovalStateV2.set_requirements(bool(approved))

    @classmethod
    def state(cls):
        state = StudioApprovalStateV2.load()
        return {
            "stage": "REQUIREMENTS",
            "route": "/create/requirements",
            "approval": state["approvals"]["requirements"],
            "generation_allowed": state["generation_allowed"],
            "execution": "NOT_RUN",
            "safe_stop": state["safe_stop"],
        }

    @classmethod
    def contract(cls):
        return {
            "status": "LINKED",
            "execution": "NOT_RUN",
            "route": "/create/requirements",
            "approval_type": "YES_NO",
            "controller": "StudioApprovalStateV2",
            "next_stage": "SCREEN_DESIGN",
            "rejection_blocks_next_stage": True,
            "safe_stop": True,
        }
