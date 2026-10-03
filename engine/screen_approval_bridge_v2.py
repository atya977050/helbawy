
from engine.studio_approval_state_v2 import StudioApprovalStateV2


class ScreenApprovalBridgeV2:
    VERSION = "2.0"

    @classmethod
    def approve(cls, selected_variant):
        if not selected_variant:
            raise ValueError("SCREEN_VARIANT_REQUIRED")

        return StudioApprovalStateV2.set_screens(
            True,
            selected_variant=selected_variant,
        )

    @classmethod
    def reject(cls):
        return StudioApprovalStateV2.set_screens(
            False,
            selected_variant=None,
        )

    @classmethod
    def state(cls):
        state = StudioApprovalStateV2.load()

        return {
            "stage": "SCREEN_DESIGN",
            "route": "/create/plan",
            "approval": state["approvals"]["screens"],
            "requirements_approved":
                state["approvals"]["requirements"]["approved"],
            "generation_allowed": state["generation_allowed"],
            "execution": "NOT_RUN",
            "safe_stop": state["safe_stop"],
        }

    @classmethod
    def contract(cls):
        return {
            "status": "LINKED",
            "execution": "NOT_RUN",
            "route": "/create/plan",
            "approval_type": "USER_SELECTS_VARIANT",
            "controller": "StudioApprovalStateV2",
            "previous_stage": "REQUIREMENTS",
            "next_stage": "BUILD_APPROVAL",
            "variant_required": True,
            "rejected_blocks_next_stage": True,
            "safe_stop": True,
        }
