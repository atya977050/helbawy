from pathlib import Path
import json
from datetime import datetime, timezone

from engine.execution_evidence_contract_v2 import ExecutionEvidenceContractV2


class ExecutionEvidenceRecorderV2:
    VERSION = "2.0"
    STATUS = "READY"
    EXECUTION = "NOT_RUN"
    SAFE_STOP = True

    EVIDENCE_FILE = (
        Path(__file__).resolve().parents[1]
        / "reports"
        / "abqaryno-execution-evidence-v2.json"
    )

    @classmethod
    def _now(cls):
        return datetime.now(timezone.utc).isoformat()

    @classmethod
    def empty_record(cls, stage):
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
    def load(cls):
        if not cls.EVIDENCE_FILE.exists():
            return {
                "version": cls.VERSION,
                "status": cls.STATUS,
                "execution": cls.EXECUTION,
                "safe_stop": cls.SAFE_STOP,
                "records": [],
            }

        return json.loads(
            cls.EVIDENCE_FILE.read_text(encoding="utf-8")
        )

    @classmethod
    def save(cls, data):
        cls.EVIDENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
        cls.EVIDENCE_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def record(cls, stage, status, evidence=None, artifact=None, error=None):
        payload = cls.empty_record(stage)
        payload["status"] = status
        payload["evidence"] = evidence
        payload["artifact"] = artifact
        payload["error"] = error

        if status == "RUNNING":
            payload["started_at"] = cls._now()

        if status in {"PASSED", "FAILED", "BLOCKED"}:
            payload["finished_at"] = cls._now()

        ExecutionEvidenceContractV2.validate_record(payload)

        data = cls.load()
        records = [
            item for item in data.get("records", [])
            if item.get("stage") != stage
        ]
        records.append(payload)
        data["records"] = records
        data["updated_at"] = cls._now()
        data["execution"] = cls.EXECUTION
        data["safe_stop"] = cls.SAFE_STOP
        cls.save(data)

        return payload

    @classmethod
    def contract(cls):
        return {
            "recorder": "ExecutionEvidenceRecorderV2",
            "version": cls.VERSION,
            "status": "LINKED",
            "execution": cls.EXECUTION,
            "evidence_file": str(cls.EVIDENCE_FILE),
            "contract": "ExecutionEvidenceContractV2",
            "recording": "READY",
            "execution_allowed": False,
            "safe_stop": cls.SAFE_STOP,
        }
