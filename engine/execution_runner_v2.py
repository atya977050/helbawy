from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.execution_command_contract_v2 import ExecutionCommandContractV2
from engine.execution_run_state_v2 import ExecutionRunStateV2
from engine.execution_evidence_contract_v2 import ExecutionEvidenceContractV2


class ExecutionRunnerV2:
    VERSION = "2.0"
    RUNNER = "EXECUTION_RUNNER_V2"

    EXECUTION = "NOT_RUN"
    SAFE_STOP = True

    STAGES = [
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

    @classmethod
    def run_state_contract(cls):
        return ExecutionRunStateV2.contract()

    @classmethod
    def initial_run_state(cls):
        return ExecutionRunStateV2.empty_state()

    @classmethod
    def evidence_contract(cls):
        return ExecutionEvidenceContractV2.contract()

    @classmethod
    def validate_stage_evidence(cls, stage, record):
        payload = dict(record)
        payload["stage"] = stage
        return ExecutionEvidenceContractV2.validate_record(payload)

    @classmethod
    def contract(cls):
        return {
            "runner": cls.RUNNER,
            "version": cls.VERSION,
            "status": "LINKED",
            "execution": cls.EXECUTION,
            "safe_stop": cls.SAFE_STOP,
            "command_contract": "ExecutionCommandContractV2",
            "command": "EXECUTE_BUILD",
            "stages": cls.STAGES,
            "stop_on_failure": True,
            "runtime_after_generation": True,
            "deployment": "BLOCKED_UNTIL_FINAL_VERIFICATION",
            "release": "BLOCKED_UNTIL_DEPLOYMENT",
        }

    @classmethod
    def preflight(cls):
        result = ExecutionCommandContractV2.preflight()

        return {
            "runner": cls.RUNNER,
            "execution": "NOT_RUN",
            "preflight": result,
            "stage_count": len(cls.STAGES),
            "execution_allowed": False,
            "safe_stop": True,
        }

    @classmethod
    def authorize(cls):
        result = ExecutionCommandContractV2.authorize()

        return {
            "authorized": result["authorized"],
            "runner": cls.RUNNER,
            "command": "EXECUTE_BUILD",
            "execution": "NOT_RUN",
            "next_stage": cls.STAGES[0],
            "stage_count": len(cls.STAGES),
            "safe_stop": True,
        }

    @classmethod
    def execution_record(cls):
        return {
            "runner": cls.RUNNER,
            "execution": "NOT_RUN",
            "started_at": None,
            "finished_at": None,
            "current_stage": None,
            "completed_stages": [],
            "failed_stage": None,
            "project_execution": "NOT_RUN",
            "legal_project_execution": "NOT_RUN",
            "deployment": "BLOCKED",
            "release": "BLOCKED",
            "safe_stop": True,
        }


if __name__ == "__main__":
    print("EXECUTION_RUNNER_V2=READY")
    print("STATUS=LINKED")
    print("COMMAND=EXECUTE_BUILD")
    print("STAGES=12")
    print("EXECUTION=NOT_RUN")
    print("SAFE_STOP=ACTIVE")
