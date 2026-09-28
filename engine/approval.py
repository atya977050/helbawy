#!/usr/bin/env python3
"""
P45 Approval Gate

Candidate -> Approval -> Authorized Repair
"""

from datetime import datetime, timezone
import json
from pathlib import Path


class ApprovalError(Exception):
    pass


class ApprovalGate:
    REQUIRED_STATUS = "PROPOSED"
    REQUIRED_APPROVAL = "APPROVAL"

    def __init__(self, project_path):
        self.project_path = Path(project_path).resolve()
        self.plan_path = self.project_path / "plans" / "execution-plan.json"

    def _load_plan(self):
        if not self.plan_path.exists():
            raise ApprovalError(
                f"Execution plan is missing: {self.plan_path}"
            )

        try:
            data = json.loads(
                self.plan_path.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError as exc:
            raise ApprovalError(
                f"Execution plan is invalid JSON: {self.plan_path}"
            ) from exc

        if not isinstance(data, dict):
            raise ApprovalError(
                "Execution plan must be a JSON object."
            )

        return data

    def _find_candidate(self, plan, candidate_id):
        candidates = plan.get("repair_candidates", [])

        for candidate in candidates:
            if candidate.get("candidate_id") == candidate_id:
                return candidate

        raise ApprovalError(
            f"Repair candidate not found: {candidate_id}"
        )

    def approve(self, candidate_id):
        plan = self._load_plan()
        candidate = self._find_candidate(plan, candidate_id)

        if candidate.get("requires") != self.REQUIRED_APPROVAL:
            raise ApprovalError(
                f"Candidate does not require approval: {candidate_id}"
            )

        status = str(candidate.get("status", "")).upper()

        if status != self.REQUIRED_STATUS:
            raise ApprovalError(
                f"Candidate is not awaiting approval: "
                f"{candidate_id} status={status}"
            )

        now = datetime.now(timezone.utc).isoformat()

        candidate["status"] = "APPROVED"
        candidate["approved"] = True
        candidate["approved_at"] = now

        self.plan_path.write_text(
            json.dumps(plan, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return {
            "candidate_id": candidate_id,
            "status": "APPROVED",
            "approved": True,
            "approved_at": now,
            "target": candidate.get("target"),
            "reason": candidate.get("reason"),
        }

    def require_approved(self, candidate_id):
        plan = self._load_plan()
        candidate = self._find_candidate(plan, candidate_id)

        if (
            str(candidate.get("status", "")).upper() != "APPROVED"
            or candidate.get("approved") is not True
        ):
            raise ApprovalError(
                f"Candidate is not approved: {candidate_id}"
            )

        return candidate
