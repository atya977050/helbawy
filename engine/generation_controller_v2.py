from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.generation_gate_v2 import GenerationGateV2


class GenerationControllerV2:
    VERSION = "2.0"
    STATUS = "LINKED"
    EXECUTION = "NOT_RUN"

    PIPELINE = [
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
        "DEPLOYMENT_FINAL_VERIFICATION",
    ]

    @classmethod
    def status(cls):
        gate = GenerationGateV2()
        result = gate.evaluate()

        return {
            "controller": "GenerationControllerV2",
            "version": cls.VERSION,
            "status": cls.STATUS,
            "execution": cls.EXECUTION,
            "gate": result,
            "current_stage": "PROJECT_BRAIN",
            "pipeline": cls.PIPELINE,
            "engine_execution": "NOT_RUN",
            "project_execution": "NOT_RUN",
            "legal_project_execution": "NOT_RUN",
            "runtime": "BLOCKED_UNTIL_GENERATION",
            "deployment": "BLOCKED",
            "release": "BLOCKED",
            "safe_stop": True,
        }

    @classmethod
    def authorize(cls):
        GenerationGateV2.assert_allowed()

        return {
            "authorized": True,
            "execution": "NOT_RUN",
            "current_stage": "PROJECT_BRAIN",
            "pipeline": cls.PIPELINE,
            "safe_stop": True,
            "project_execution": "NOT_RUN",
            "legal_project_execution": "NOT_RUN",
        }

    @classmethod
    def contract(cls):
        return {
            "status": "LINKED",
            "execution": "NOT_RUN",
            "controller": "GenerationControllerV2",
            "module": "engine.generation_controller_v2",
            "gate": "GenerationGateV2",
            "gate_rule": "ALL_REQUIRED_APPROVALS",
            "pipeline": cls.PIPELINE,
            "engine_execution": "NOT_RUN",
            "project_execution": "NOT_RUN",
            "legal_project_execution": "NOT_RUN",
            "runtime": "AFTER_GENERATION",
            "deployment": "AFTER_FINAL_VERIFICATION",
            "release": "AFTER_DEPLOYMENT",
            "safe_stop": True,
        }


if __name__ == "__main__":
    print("GENERATION_CONTROLLER_V2=READY")
    print("STATUS=LINKED")
    print("EXECUTION=NOT_RUN")
    print("SAFE_STOP=ACTIVE")
