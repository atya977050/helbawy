from pathlib import Path
import json
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
EVIDENCE_FILE = REPORTS / "abqaryno-execution-evidence-v2.json"


class ExecutionEvidenceContractV2:
    VERSION = "2.0"

    REQUIRED_FIELDS = [
        "stage",
        "status",
        "started_at",
        "finished_at",
        "evidence",
        "artifact",
        "error",
    ]

    VALID_STATUSES = [
        "PENDING",
        "RUNNING",
        "PASSED",
        "FAILED",
        "BLOCKED",
    ]

    @classmethod
    def create_record(cls, stage):
        return {
            "stage": stage,
            "status": "PENDING",
            "started_at": None,
            "finished_at": None,
            "evidence": None,
            "artifact": None,
            "error": None,
        }

    @classmethod
    def validate_record(cls, record):
        missing = [
            field
            for field in cls.REQUIRED_FIELDS
            if field not in record
        ]

        if missing:
            raise ValueError(
                "EVIDENCE_FIELDS_MISSING: "
                + ",".join(missing)
            )

        if record["status"] not in cls.VALID_STATUSES:
            raise ValueError(
                "INVALID_EVIDENCE_STATUS: "
                + str(record["status"])
            )

        if record["status"] == "PASSED":
            if not record.get("evidence"):
                raise ValueError(
                    "PASSED_REQUIRES_EVIDENCE"
                )

        return True

    @classmethod
    def contract(cls):
        return {
            "status": "LINKED",
            "execution": "NOT_RUN",
            "module": "engine.execution_evidence_contract_v2",
            "evidence_file": str(
                EVIDENCE_FILE.relative_to(ROOT)
            ),
            "required_fields": cls.REQUIRED_FIELDS,
            "valid_statuses": cls.VALID_STATUSES,
            "passed_requires_evidence": True,
            "safe_stop": True,
        }


if __name__ == "__main__":
    print("EXECUTION_EVIDENCE_CONTRACT_V2=READY")
    print("STATUS=LINKED")
    print("PASSED_REQUIRES_EVIDENCE=TRUE")
    print("EXECUTION=NOT_RUN")
    print("SAFE_STOP=ACTIVE")
