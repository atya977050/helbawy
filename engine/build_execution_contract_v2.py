from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.generation_gate_v2 import GenerationGateV2


class BuildExecutionContractV2:
    VERSION = "2.0"
    CONTRACT = "BUILD_EXECUTION_CONTRACT_V2"

    EXECUTION_MODE = "EXPLICIT_USER_COMMAND"
    DEFAULT_EXECUTION = "NOT_RUN"
    SAFE_STOP = True

    PRECONDITIONS = [
        "REQUIREMENTS_APPROVED",
        "SCREEN_APPROVED",
        "BUILD_APPROVED",
        "GENERATION_GATE_OPEN",
    ]

    EXECUTION_ORDER = [
        "MATERIALIZE_APPROVED_PLAN",
        "PROJECT_BRAIN",
        "REQUIREMENTS",
        "SCREEN_DESIGN",
        "ARCHITECTURE_ENVIRONMENT",
        "DATABASE",
        "BACKEND",
        "FRONTEND_INTEGRATION",
        "RUNTIME_TESTING_EVIDENCE",
        "SECURITY_REPAIR_REGRESSION",
        "VERSION_GIT_DOCUMENTATION",
        "FINAL_VERIFICATION",
    ]

    BLOCKED_UNTIL_COMPLETE = [
        "DEPLOYMENT",
        "RELEASE",
    ]

    @classmethod
    def contract(cls):
        return {
            "contract": cls.CONTRACT,
            "version": cls.VERSION,
            "status": "LINKED",
            "execution_mode": cls.EXECUTION_MODE,
            "execution": cls.DEFAULT_EXECUTION,
            "safe_stop": cls.SAFE_STOP,
            "preconditions": cls.PRECONDITIONS,
            "execution_order": cls.EXECUTION_ORDER,
            "blocked_until_complete": cls.BLOCKED_UNTIL_COMPLETE,
            "project_execution": "NOT_RUN",
            "legal_project_execution": "NOT_RUN",
            "deployment": "BLOCKED",
            "release": "BLOCKED",
        }

    @classmethod
    def preflight(cls):
        gate = GenerationGateV2()
        gate_result = gate.evaluate()

        return {
            "contract": cls.CONTRACT,
            "execution": "NOT_RUN",
            "generation_gate": gate_result,
            "preconditions_required": cls.PRECONDITIONS,
            "execution_allowed": bool(
                gate_result.get("generation_allowed", False)
            ),
            "safe_stop": True,
        }

    @classmethod
    def assert_ready(cls):
        GenerationGateV2.assert_allowed()
        return {
            "ready": True,
            "execution": "NOT_RUN",
            "safe_stop": True,
            "execution_mode": cls.EXECUTION_MODE,
            "next_action": "EXPLICIT_USER_EXECUTION_COMMAND",
        }


if __name__ == "__main__":
    print("BUILD_EXECUTION_CONTRACT_V2=READY")
    print("STATUS=LINKED")
    print("EXECUTION_MODE=EXPLICIT_USER_COMMAND")
    print("EXECUTION=NOT_RUN")
    print("SAFE_STOP=ACTIVE")
