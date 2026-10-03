class BuildScreenBridgeV2:
    VERSION = "2.0"

    @classmethod
    def contract(cls):
        return {
            "controller": "CreationControllerV2",
            "approval_gate": "ApprovalStateGateV2",
            "status": "LINKED",
            "execution": "NOT_RUN",
            "route": "/create/build",
            "required_approvals": [
                "REQUIREMENTS_APPROVAL",
                "SCREEN_APPROVAL",
                "BUILD_APPROVAL",
            ],
            "generation_rule": "ALL_REQUIRED_APPROVALS",
            "safe_stop": True,
            "generation_allowed": False,
            "execution_allowed": False,
            "deployment_allowed": False,
            "release_allowed": False,
        }

    @classmethod
    def initial_view_state(cls):
        return {
            "requirements": "PENDING",
            "screens": "PENDING",
            "build": "PENDING",
            "generation": "LOCKED",
            "execution": "NOT_RUN",
            "safe_stop": True,
        }
