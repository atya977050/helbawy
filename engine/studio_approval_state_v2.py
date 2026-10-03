
import json
from datetime import datetime, timezone
from pathlib import Path


class StudioApprovalStateV2:
    VERSION = "2.0"

    ROOT = Path(__file__).resolve().parents[1]
    REPORTS = ROOT / "reports"
    STATE_FILE = REPORTS / "abqaryno-studio-approval-state-v2.json"

    APPROVALS = (
        "requirements",
        "screens",
        "build",
    )

    @classmethod
    def now(cls):
        return datetime.now(timezone.utc).isoformat()

    @classmethod
    def initial_state(cls):
        return {
            "status": "LOCKED",
            "execution": "NOT_RUN",
            "safe_stop": True,
            "project_status": "NOT_STARTED",
            "approvals": {
                "requirements": {
                    "status": "PENDING",
                    "approved": False,
                    "timestamp": None,
                },
                "screens": {
                    "status": "PENDING",
                    "approved": False,
                    "timestamp": None,
                    "selected_variant": None,
                },
                "build": {
                    "status": "PENDING",
                    "approved": False,
                    "timestamp": None,
                },
            },
            "generation_allowed": False,
            "runtime_allowed": False,
            "deployment_allowed": False,
            "release_allowed": False,
        }

    @classmethod
    def load(cls):
        if not cls.STATE_FILE.exists():
            return cls.initial_state()

        try:
            return json.loads(cls.STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return cls.initial_state()

    @classmethod
    def save(cls, state):
        cls.REPORTS.mkdir(parents=True, exist_ok=True)
        cls.STATE_FILE.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return state

    @classmethod
    def evaluate(cls, state):
        approvals = state["approvals"]

        requirements = approvals["requirements"]["approved"] is True
        screens = approvals["screens"]["approved"] is True
        build = approvals["build"]["approved"] is True

        all_approved = requirements and screens and build

        state["generation_allowed"] = all_approved
        state["runtime_allowed"] = False
        state["deployment_allowed"] = False
        state["release_allowed"] = False

        state["status"] = "READY_FOR_GENERATION" if all_approved else "LOCKED"
        state["safe_stop"] = not all_approved

        return {
            "requirements_approved": requirements,
            "screens_approved": screens,
            "build_approved": build,
            "all_approved": all_approved,
            "generation_allowed": all_approved,
            "runtime_allowed": False,
            "deployment_allowed": False,
            "release_allowed": False,
            "safe_stop": not all_approved,
        }

    @classmethod
    def set_requirements(cls, approved):
        state = cls.load()

        state["approvals"]["requirements"] = {
            "status": "APPROVED" if approved else "REJECTED",
            "approved": bool(approved),
            "timestamp": cls.now(),
        }

        cls.evaluate(state)
        return cls.save(state)

    @classmethod
    def set_screens(cls, approved, selected_variant=None):
        state = cls.load()

        state["approvals"]["screens"] = {
            "status": "APPROVED" if approved else "REJECTED",
            "approved": bool(approved),
            "timestamp": cls.now(),
            "selected_variant": selected_variant,
        }

        cls.evaluate(state)
        return cls.save(state)

    @classmethod
    def set_build(cls, approved):
        state = cls.load()

        state["approvals"]["build"] = {
            "status": "APPROVED" if approved else "REJECTED",
            "approved": bool(approved),
            "timestamp": cls.now(),
        }

        cls.evaluate(state)
        return cls.save(state)

    @classmethod
    def contract(cls):
        state = cls.load()
        evaluation = cls.evaluate(state)

        return {
            "controller": "StudioApprovalStateV2",
            "version": cls.VERSION,
            "status": state["status"],
            "execution": "NOT_RUN",
            "state_file": str(cls.STATE_FILE),
            "approvals": state["approvals"],
            "evaluation": evaluation,
            "generation_allowed": state["generation_allowed"],
            "runtime_allowed": state["runtime_allowed"],
            "deployment_allowed": state["deployment_allowed"],
            "release_allowed": state["release_allowed"],
            "safe_stop": state["safe_stop"],
        }
