from datetime import datetime, timezone


class ApprovalStateGateV2:
    VERSION = "2.0"

    APPROVALS = (
        "REQUIREMENTS_APPROVAL",
        "SCREEN_APPROVAL",
        "BUILD_APPROVAL",
    )

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    @classmethod
    def initial_state(cls):
        return {
            "status": "LINKED",
            "execution": "NOT_RUN",
            "safe_stop": True,
            "project_status": "NOT_STARTED",
            "requirements": {
                "status": "PENDING",
                "value": None,
                "timestamp": None,
            },
            "screens": {
                "status": "PENDING",
                "value": None,
                "timestamp": None,
            },
            "build": {
                "status": "PENDING",
                "value": None,
                "timestamp": None,
            },
            "generation_allowed": False,
            "runtime_allowed": False,
            "deployment_allowed": False,
            "release_allowed": False,
        }

    @classmethod
    def evaluate(cls, state=None):
        state = state or cls.initial_state()

        requirements_ok = (
            state["requirements"]["status"] == "APPROVED"
            and state["requirements"]["value"] is True
        )

        screens_ok = (
            state["screens"]["status"] == "APPROVED"
            and state["screens"]["value"] is True
        )

        build_ok = (
            state["build"]["status"] == "APPROVED"
            and state["build"]["value"] is True
        )

        all_ok = requirements_ok and screens_ok and build_ok

        return {
            "status": "READY" if all_ok else "LOCKED",
            "execution": "NOT_RUN",
            "requirements_approved": requirements_ok,
            "screens_approved": screens_ok,
            "build_approved": build_ok,
            "all_required_approvals": all_ok,
            "generation_allowed": all_ok,
            "runtime_allowed": False,
            "deployment_allowed": False,
            "release_allowed": False,
            "safe_stop": not all_ok,
        }

    @classmethod
    def approve(cls, state, approval, value):
        if approval not in cls.APPROVALS:
            raise ValueError("UNKNOWN_APPROVAL")

        if not isinstance(value, bool):
            raise ValueError("APPROVAL_VALUE_MUST_BE_BOOLEAN")

        key = {
            "REQUIREMENTS_APPROVAL": "requirements",
            "SCREEN_APPROVAL": "screens",
            "BUILD_APPROVAL": "build",
        }[approval]

        state[key]["value"] = value
        state[key]["timestamp"] = cls._now()
        state[key]["status"] = "APPROVED" if value else "REJECTED"

        evaluation = cls.evaluate(state)
        state["generation_allowed"] = evaluation["generation_allowed"]
        state["runtime_allowed"] = evaluation["runtime_allowed"]
        state["deployment_allowed"] = evaluation["deployment_allowed"]
        state["release_allowed"] = evaluation["release_allowed"]

        return state

    @classmethod
    def contract(cls):
        return {
            "controller": "ApprovalStateGateV2",
            "version": cls.VERSION,
            "status": "LINKED",
            "execution": "NOT_RUN",
            "approval_order": list(cls.APPROVALS),
            "generation_rule": "ALL_REQUIRED_APPROVALS",
            "runtime_rule": "BUILD_COMPLETED_FIRST",
            "deployment_rule": "FINAL_VERIFICATION_FIRST",
            "release_rule": "DEPLOYMENT_FIRST",
            "safe_stop": True,
            "initial_evaluation": cls.evaluate(),
        }
