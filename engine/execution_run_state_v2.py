from pathlib import Path
import json
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
STATE_FILE = REPORTS / "abqaryno-execution-run-state-v2.json"


class ExecutionRunStateV2:
    VERSION = "2.0"

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

    ALLOWED_STATES = {
        "PENDING",
        "RUNNING",
        "PASSED",
        "FAILED",
        "BLOCKED",
    }

    @classmethod
    def empty_state(cls):
        now = datetime.now(timezone.utc).isoformat()

        return {
            "version": cls.VERSION,
            "execution": "NOT_RUN",
            "safe_stop": True,
            "started_at": None,
            "finished_at": None,
            "current_stage": None,
            "completed_stages": [],
            "failed_stage": None,
            "stages": {
                stage: {
                    "status": "PENDING",
                    "started_at": None,
                    "finished_at": None,
                    "error": None,
                    "evidence": None,
                }
                for stage in cls.STAGES
            },
            "project_execution": "NOT_RUN",
            "legal_project_execution": "NOT_RUN",
            "runtime": "BLOCKED",
            "deployment": "BLOCKED",
            "release": "BLOCKED",
            "created_at": now,
        }

    @classmethod
    def save(cls, state):
        REPORTS.mkdir(exist_ok=True)
        STATE_FILE.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls):
        if not STATE_FILE.exists():
            return cls.empty_state()

        return json.loads(
            STATE_FILE.read_text(encoding="utf-8")
        )

    @classmethod
    def contract(cls):
        return {
            "status": "LINKED",
            "execution": "NOT_RUN",
            "module": "engine.execution_run_state_v2",
            "state_file": str(STATE_FILE.relative_to(ROOT)),
            "states": sorted(cls.ALLOWED_STATES),
            "stage_count": len(cls.STAGES),
            "stop_on_failure": True,
            "safe_stop": True,
        }


if __name__ == "__main__":
    state = ExecutionRunStateV2.empty_state()
    ExecutionRunStateV2.save(state)

    print("EXECUTION_RUN_STATE_V2=READY")
    print("STATE_FILE_CREATED=TRUE")
    print("STAGES=12")
    print("EXECUTION=NOT_RUN")
    print("SAFE_STOP=ACTIVE")
