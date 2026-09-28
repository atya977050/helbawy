#!/usr/bin/env python3
"""
P45 Snapshot Engine

Creates immutable file snapshots and SHA-256 fingerprints
before an approved repair is applied.
"""

import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path


class SnapshotError(RuntimeError):
    pass


class SnapshotEngine:
    def __init__(self, project_path):
        self.project_path = Path(project_path).resolve()
        self.snapshots_dir = self.project_path / "snapshots"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def sha256_file(path):
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def timestamp():
        return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    def create(self, target):
        target = Path(target).resolve()

        if not target.exists():
            raise SnapshotError(f"Snapshot target does not exist: {target}")

        if not target.is_file():
            raise SnapshotError(f"Snapshot target is not a file: {target}")

        try:
            relative = target.relative_to(self.project_path)
        except ValueError as exc:
            raise SnapshotError(
                f"Snapshot target is outside project: {target}"
            ) from exc

        before_sha256 = self.sha256_file(target)

        stamp = self.timestamp()
        safe_name = "__".join(relative.parts)
        snapshot = self.snapshots_dir / f"{stamp}__{safe_name}"

        shutil.copy2(target, snapshot)

        after_snapshot_sha256 = self.sha256_file(snapshot)

        if before_sha256 != after_snapshot_sha256:
            snapshot.unlink(missing_ok=True)
            raise SnapshotError(
                f"Snapshot hash mismatch for {relative}"
            )

        return {
            "target": str(relative),
            "snapshot": str(snapshot),
            "before_sha256": before_sha256,
            "snapshot_sha256": after_snapshot_sha256,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "SNAPSHOTTED",
        }
