from __future__ import annotations

import ast
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


class ExecutionRecoveryEngine:
    VERSION = 2
    MAX_ATTEMPTS = 3

    def __init__(self, project_dir):
        self.project_dir = Path(project_dir)
        self.reports_dir = Path.home() / "عبقرينو" / "reports"
        self.snapshots_dir = self.project_dir / "snapshots"

        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self.report = {
            "engine": "ExecutionRecoveryEngine",
            "version": self.VERSION,
            "status": "STARTED",
            "project_dir": str(self.project_dir),
            "checks": [],
            "repairs": [],
            "attempts": [],
        }

    def record(self, name, ok, details=None):
        item = {
            "name": name,
            "ok": bool(ok),
            "details": details or {},
        }
        self.report["checks"].append(item)
        return bool(ok)

    def snapshot(self, path):
        path = Path(path)
        if not path.exists():
            return None

        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup = self.snapshots_dir / f"{path.name}.{stamp}.bak"
        shutil.copy2(path, backup)
        return backup

    def check_json(self, path):
        try:
            json.loads(path.read_text(encoding="utf-8"))
            return True, {"file": str(path)}
        except Exception as exc:
            return False, {
                "file": str(path),
                "error": str(exc),
            }

    def check_node(self, path):
        try:
            result = subprocess.run(
                ["node", "--check", str(path)],
                cwd=str(path.parent),
                text=True,
                capture_output=True,
                timeout=15,
            )

            return (
                result.returncode == 0,
                {
                    "file": str(path),
                    "stdout": result.stdout[-3000:],
                    "stderr": result.stderr[-3000:],
                    "returncode": result.returncode,
                },
            )
        except Exception as exc:
            return False, {
                "file": str(path),
                "error": str(exc),
            }

    def inspect_execution_area(self):
        current = []

        required = [
            self.project_dir / "package.json",
            self.project_dir / "server.js",
            self.project_dir / "public" / "index.html",
        ]

        for path in required:
            ok = path.exists()
            current.append(
                self.record(
                    "required:" + str(path.relative_to(self.project_dir)),
                    ok,
                    {"path": str(path)},
                )
            )

        package = self.project_dir / "package.json"
        if package.exists():
            ok, details = self.check_json(package)
            current.append(
                self.record("package_json_valid", ok, details)
            )

        server = self.project_dir / "server.js"
        if server.exists():
            ok, details = self.check_node(server)
            current.append(
                self.record("server_js_syntax", ok, details)
            )

        return all(current)

    def safe_repair(self, details):
        error = details.get("error", "")

        package = self.project_dir / "package.json"

        if package.exists() and (
            "JSONDecodeError" in error
            or "Unexpected UTF" in error
            or "Unexpected BOM" in error
        ):
            raw = package.read_bytes()

            if raw.startswith(b"\xef\xbb\xbf"):
                backup = self.snapshot(package)
                package.write_bytes(raw[3:])

                self.report["repairs"].append({
                    "type": "AUTO-FIXED",
                    "target": str(package),
                    "reason": "remove_utf8_bom",
                    "backup": str(backup) if backup else None,
                })

                return True

        return False

    def execute_with_recovery(self):
        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            self.report["attempts"].append({
                "attempt": attempt,
                "started_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            })

            self.report["checks"] = []

            ok = self.inspect_execution_area()

            if ok:
                self.report["status"] = (
                    "COMPLETED_CLEAN"
                    if not self.report["repairs"]
                    else "COMPLETED_WITH_REPAIRS"
                )
                return self.finish()

            failed = [
                item
                for item in self.report["checks"]
                if not item["ok"]
            ]

            repaired = False

            for item in failed:
                if self.safe_repair(item["details"]):
                    repaired = True
                    break

            if not repaired:
                self.report["status"] = "BLOCKED"
                self.report["blocked_reason"] = (
                    "No safe deterministic repair matched "
                    "the detected execution error."
                )
                return self.finish()

        self.report["status"] = "FAILED"
        self.report["blocked_reason"] = "MAX_ATTEMPTS_REACHED"
        return self.finish()

    def finish(self):
        self.report["finished_at"] = datetime.now(
            timezone.utc
        ).isoformat()

        self.report["summary"] = {
            "checks": len(self.report["checks"]),
            "failed_checks": sum(
                1
                for item in self.report["checks"]
                if not item["ok"]
            ),
            "repairs": len(self.report["repairs"]),
            "attempts": len(self.report["attempts"]),
        }

        report_file = (
            self.reports_dir
            / "execution-recovery-latest.json"
        )

        report_file.write_text(
            json.dumps(
                self.report,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        self.report["report_file"] = str(report_file)

        return self.report


def run_execution_recovery(project_dir):
    return ExecutionRecoveryEngine(
        project_dir
    ).execute_with_recovery()
