from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.build_execution_gate_v2 import BuildExecutionGateV2


class ExecutionCommandContractV2:
    VERSION = "2.0"
    CONTRACT = "EXECUTION_COMMAND_CONTRACT_V2"

    COMMAND = "EXECUTE_BUILD"
    MODE = "EXPLICIT_USER_COMMAND"

    DEFAULT_STATUS = "LOCKED"
    EXECUTION = "NOT_RUN"
    SAFE_STOP = True

    PRECHECKS = [
        "REQUIREMENTS_APPROVAL",
        "SCREEN_APPROVAL",
        "BUILD_APPROVAL",
        "GENERATION_GATE",
        "BUILD_EXECUTION_GATE",
    ]

    @classmethod
    def contract(cls):
        return {
            "contract": cls.CONTRACT,
            "version": cls.VERSION,
            "command": cls.COMMAND,
            "mode": cls.MODE,
            "status": cls.DEFAULT_STATUS,
            "execution": cls.EXECUTION,
            "safe_stop": cls.SAFE_STOP,
            "prechecks": cls.PRECHECKS,
            "project_execution": "NOT_RUN",
            "legal_project_execution": "NOT_RUN",
            "runtime": "BLOCKED",
            "deployment": "BLOCKED",
            "release": "BLOCKED",
        }

    @classmethod
    def preflight(cls):
        gate = BuildExecutionGateV2()
        result = gate.evaluate()

        return {
            "command": cls.COMMAND,
            "mode": cls.MODE,
            "execution": "NOT_RUN",
            "gate_status": result.get("status"),
            "execution_allowed": False,
            "prechecks": cls.PRECHECKS,
            "safe_stop": True,
        }

    @classmethod
    def authorize(cls):
        BuildExecutionGateV2.authorize()

        return {
            "authorized": True,
            "command": cls.COMMAND,
            "mode": cls.MODE,
            "execution": "NOT_RUN",
            "safe_stop": True,
            "next_action": "BEGIN_BUILD_PIPELINE_ONLY_AFTER_EXPLICIT_EXECUTION",
        }


if __name__ == "__main__":
    print("EXECUTION_COMMAND_CONTRACT_V2=READY")
    print("COMMAND=EXECUTE_BUILD")
    print("MODE=EXPLICIT_USER_COMMAND")
    print("STATUS=LOCKED")
    print("EXECUTION=NOT_RUN")
    print("SAFE_STOP=ACTIVE")
