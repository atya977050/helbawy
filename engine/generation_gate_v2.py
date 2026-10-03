
from engine.studio_approval_state_v2 import StudioApprovalStateV2


class GenerationGateV2:
    VERSION = "2.0"

    REQUIRED_APPROVALS = (
        "requirements",
        "screens",
        "build",
    )

    @classmethod
    def evaluate(cls):
        state = StudioApprovalStateV2.load()
        evaluation = StudioApprovalStateV2.evaluate(state)

        missing = []

        for name in cls.REQUIRED_APPROVALS:
            if not state["approvals"][name]["approved"]:
                missing.append(name)

        allowed = (
            evaluation["generation_allowed"] is True
            and not missing
        )

        return {
            "gate": "GENERATION_GATE_V2",
            "status": "OPEN" if allowed else "LOCKED",
            "execution": "NOT_RUN",
            "generation_allowed": allowed,
            "missing_approvals": missing,
            "requirements_approved":
                evaluation["requirements_approved"],
            "screens_approved":
                evaluation["screens_approved"],
            "build_approved":
                evaluation["build_approved"],
            "runtime_allowed": False,
            "deployment_allowed": False,
            "release_allowed": False,
            "safe_stop": not allowed,
        }

    @classmethod
    def assert_allowed(cls):
        result = cls.evaluate()

        if not result["generation_allowed"]:
            missing = ", ".join(result["missing_approvals"]) or "UNKNOWN"
            raise PermissionError(
                "GENERATION_BLOCKED: " + missing
            )

        return result

    @classmethod
    def contract(cls):
        return {
            "controller": "GenerationGateV2",
            "version": cls.VERSION,
            "status": "LINKED",
            "execution": "NOT_RUN",
            "required_approvals": list(cls.REQUIRED_APPROVALS),
            "rule": "ALL_REQUIRED_APPROVALS",
            "generation_allowed": False,
            "engine_execution": "BLOCKED_UNTIL_GATE_OPEN",
            "project_execution": "BLOCKED",
            "legal_project_execution": "BLOCKED",
            "runtime": "BLOCKED",
            "deployment": "BLOCKED",
            "release": "BLOCKED",
            "safe_stop": True,
        }
