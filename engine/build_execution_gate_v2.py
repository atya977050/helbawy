from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.generation_gate_v2 import GenerationGateV2
from engine.build_execution_contract_v2 import BuildExecutionContractV2


class BuildExecutionGateV2:
    VERSION = "2.0"
    GATE = "BUILD_EXECUTION_GATE_V2"
    SAFE_STOP = True

    REQUIRED_APPROVALS = [
        "REQUIREMENTS_APPROVAL",
        "SCREEN_APPROVAL",
        "BUILD_APPROVAL",
    ]

    @classmethod
    def evaluate(cls):
        generation = GenerationGateV2()
        generation_result = generation.evaluate()

        generation_open = bool(
            generation_result.get("generation_allowed", False)
        )

        return {
            "gate": cls.GATE,
            "version": cls.VERSION,
            "status": "OPEN" if generation_open else "LOCKED",
            "execution_allowed": False,
            "generation_gate": (
                "OPEN" if generation_open else "LOCKED"
            ),
            "required_approvals": cls.REQUIRED_APPROVALS,
            "execution_mode": "EXPLICIT_USER_COMMAND",
            "execution": "NOT_RUN",
            "project_execution": "NOT_RUN",
            "legal_project_execution": "NOT_RUN",
            "runtime": "BLOCKED",
            "deployment": "BLOCKED",
            "release": "BLOCKED",
            "safe_stop": cls.SAFE_STOP,
        }

    @classmethod
    def authorize(cls):
        result = cls.evaluate()

        if result["generation_gate"] != "OPEN":
            raise PermissionError(
                "BUILD_EXECUTION_BLOCKED: GENERATION_GATE_LOCKED"
            )

        return {
            "authorized": True,
            "execution": "NOT_RUN",
            "execution_mode": "EXPLICIT_USER_COMMAND",
            "safe_stop": True,
            "next_action": "EXPLICIT_USER_EXECUTION_COMMAND",
        }

    @classmethod
    def contract(cls):
        return {
            "status": "LINKED",
            "execution": "NOT_RUN",
            "gate": cls.GATE,
            "generation_gate": "REQUIRED",
            "required_approvals": cls.REQUIRED_APPROVALS,
            "execution_contract": "BuildExecutionContractV2",
            "execution_mode": "EXPLICIT_USER_COMMAND",
            "project_execution": "NOT_RUN",
            "legal_project_execution": "NOT_RUN",
            "runtime": "BLOCKED",
            "deployment": "BLOCKED",
            "release": "BLOCKED",
            "safe_stop": True,
        }


if __name__ == "__main__":
    print("BUILD_EXECUTION_GATE_V2=READY")
    print("STATUS=LINKED")
    print("EXECUTION=NOT_RUN")
    print("SAFE_STOP=ACTIVE")
