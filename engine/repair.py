#!/usr/bin/env python3
"""
P45 Repair Engine

Evidence-based repair execution:
Evidence -> Approval -> Snapshot -> Exact Change -> SHA -> Log
"""

import hashlib
from pathlib import Path

from engine.contracts import RepairAction, validate_state
from engine.execution_log import ExecutionLog
from engine.snapshot import SnapshotEngine, SnapshotError


class RepairError(RuntimeError):
    pass


class DeepRepairEngine:
    def __init__(self, project_path):
        self.project_path = Path(project_path).resolve()
        self.reports_dir = self.project_path / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self.snapshot_engine = SnapshotEngine(self.project_path)
        self.execution_log = ExecutionLog(self.project_path)

    @staticmethod
    def sha256_file(path):
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _target(self, target):
        path = (self.project_path / target).resolve()

        try:
            path.relative_to(self.project_path)
        except ValueError as exc:
            raise RepairError(
                f"Repair target is outside project: {target}"
            ) from exc

        if not path.exists():
            raise RepairError(f"Repair target does not exist: {target}")

        if not path.is_file():
            raise RepairError(f"Repair target is not a file: {target}")

        return path

    def inspect(self, target):
        path = self._target(target)
        sha = self.sha256_file(path)

        result = {
            "target": str(path.relative_to(self.project_path)),
            "sha256": sha,
            "size": path.stat().st_size,
            "status": "EVIDENCED",
        }

        self.execution_log.record(
            "EVIDENCE",
            "target_inspected",
            "EVIDENCED",
            target=result["target"],
            sha256=sha,
            size=result["size"],
        )

        return result

    def apply_exact_change(
        self,
        action_id,
        target,
        reason,
        old_text,
        new_text,
        approved=False,
    ):
        if not approved:
            self.execution_log.record(
                "REPAIR",
                action_id,
                "REJECTED",
                target=target,
                reason=reason,
            )
            raise RepairError("Repair requires explicit approval.")

        path = self._target(target)
        relative = str(path.relative_to(self.project_path))
        before = path.read_text(encoding="utf-8")

        if old_text not in before:
            self.execution_log.record(
                "REPAIR",
                action_id,
                "FAILED",
                target=relative,
                reason=reason,
                failure="Exact old_text was not found.",
            )
            raise RepairError(
                f"Exact repair target was not found in {relative}"
            )

        if before.count(old_text) != 1:
            self.execution_log.record(
                "REPAIR",
                action_id,
                "FAILED",
                target=relative,
                reason=reason,
                failure="old_text matched more than once.",
                matches=before.count(old_text),
            )
            raise RepairError(
                f"Repair is ambiguous in {relative}: "
                f"{before.count(old_text)} matches"
            )

        before_sha256 = self.sha256_file(path)

        try:
            snapshot = self.snapshot_engine.create(path)
        except SnapshotError as exc:
            self.execution_log.record(
                "SNAPSHOT",
                action_id,
                "FAILED",
                target=relative,
                reason=reason,
                error=str(exc),
            )
            raise

        self.execution_log.record(
            "SNAPSHOT",
            action_id,
            "SNAPSHOTTED",
            target=relative,
            snapshot=snapshot["snapshot"],
            before_sha256=before_sha256,
        )

        updated = before.replace(old_text, new_text, 1)
        path.write_text(updated, encoding="utf-8")

        after_sha256 = self.sha256_file(path)

        if after_sha256 == before_sha256:
            self.execution_log.record(
                "REPAIR",
                action_id,
                "FAILED",
                target=relative,
                reason=reason,
                failure="File hash did not change.",
            )
            raise RepairError(
                f"Repair produced no byte-level change: {relative}"
            )

        self.execution_log.record(
            "REPAIR",
            action_id,
            "APPLIED",
            target=relative,
            reason=reason,
            before_sha256=before_sha256,
            after_sha256=after_sha256,
            snapshot=snapshot["snapshot"],
        )

        return RepairAction(
            action_id=action_id,
            target=relative,
            reason=reason,
            status="APPLIED",
            before_sha256=before_sha256,
            after_sha256=after_sha256,
            snapshot=snapshot["snapshot"],
        )

    def execute_repairs(self):
        self.execution_log.record(
            "REPAIR",
            "repair_engine_requested",
            "NOT_APPLIED",
            reason="No approved repair action supplied.",
        )

        print("[!] P45 Repair Engine is ready.")
        print("[!] No repair action was supplied.")
        print("[!] No project files were modified.")
        print("[!] Status: NOT_APPLIED")

        return {
            "status": "NOT_APPLIED",
            "reason": "No approved repair action supplied.",
        }


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "."
    engine = DeepRepairEngine(path)
    engine.execute_repairs()
