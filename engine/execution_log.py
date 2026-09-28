#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path


class ExecutionLog:
    def __init__(self, project_path):
        self.project_path = Path(project_path).resolve()
        self.log_dir = self.project_path / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.log_dir / "execution-log.json"

    def _load(self):
        if not self.path.exists():
            return {
                "project": str(self.project_path),
                "created_at": self.now(),
                "events": []
            }
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {
                "project": str(self.project_path),
                "created_at": self.now(),
                "events": []
            }

    @staticmethod
    def now():
        return datetime.now(timezone.utc).isoformat()

    def record(self, phase, action, status, **details):
        data = self._load()
        event = {
            "timestamp": self.now(),
            "phase": phase,
            "action": action,
            "status": status,
            **details
        }
        data["events"].append(event)
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return event
