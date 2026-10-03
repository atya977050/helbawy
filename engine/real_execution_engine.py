from __future__ import annotations

import json
import os
import socket
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


class RealExecutionEngine:
    VERSION = 2

    def __init__(self, project_dir):
        self.project_dir = Path(project_dir)

        self.report = {
            "engine": "RealExecutionEngine",
            "version": self.VERSION,
            "status": "STARTED",
            "project_dir": str(self.project_dir),
            "started_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "checks": [],
            "failed_checks": [],
            "http": [],
        }

        self.process = None
        self.port = None

    def record(self, name, ok, details=None):
        item = {
            "name": name,
            "ok": bool(ok),
            "details": details or {},
        }

        self.report["checks"].append(item)

        if not ok:
            self.report["failed_checks"].append(item)

        return bool(ok)

    def inspect_files(self):
        required = [
            self.project_dir / "package.json",
            self.project_dir / "server.js",
            self.project_dir / "public" / "index.html",
        ]

        for path in required:
            self.record(
                "file:" + str(path.relative_to(self.project_dir)),
                path.exists(),
                {"path": str(path)},
            )

    def inspect_package(self):
        path = self.project_dir / "package.json"

        if not path.exists():
            return

        try:
            data = json.loads(
                path.read_text(encoding="utf-8")
            )

            self.record(
                "package_json",
                True,
                {
                    "name": data.get("name"),
                    "scripts": data.get("scripts", {}),
                },
            )

        except Exception as exc:
            self.record(
                "package_json",
                False,
                {"error": str(exc)},
            )

    def inspect_server_static(self):
        path = self.project_dir / "server.js"

        if not path.exists():
            return

        try:
            source = path.read_text(
                encoding="utf-8"
            )

            self.record(
                "server_static",
                "listen(" in source,
                {
                    "express": "express" in source,
                    "listen": "listen(" in source,
                },
            )

        except Exception as exc:
            self.record(
                "server_static",
                False,
                {"error": str(exc)},
            )

    def choose_port(self):
        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )

        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()

        return port

    def start_server(self):
        self.port = self.choose_port()

        env = os.environ.copy()
        env["PORT"] = str(self.port)

        try:
            self.process = subprocess.Popen(
                ["node", "server.js"],
                cwd=str(self.project_dir),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except Exception as exc:
            self.record(
                "server_start",
                False,
                {"error": str(exc)},
            )
            return False

        deadline = time.time() + 10

        while time.time() < deadline:
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()

                self.record(
                    "server_start",
                    False,
                    {
                        "returncode": self.process.returncode,
                        "stdout": stdout[-4000:],
                        "stderr": stderr[-4000:],
                    },
                )
                return False

            try:
                with socket.create_connection(
                    ("127.0.0.1", self.port),
                    timeout=0.5,
                ):
                    self.record(
                        "server_start",
                        True,
                        {"port": self.port},
                    )
                    return True
            except OSError:
                time.sleep(0.25)

        self.record(
            "server_start",
            False,
            {
                "error": "SERVER_START_TIMEOUT",
                "port": self.port,
            },
        )

        return False

    def http_get(self, path):
        url = f"http://127.0.0.1:{self.port}{path}"

        try:
            with urllib.request.urlopen(
                url,
                timeout=5,
            ) as response:
                body = response.read().decode(
                    "utf-8",
                    errors="replace",
                )

                return True, {
                    "url": url,
                    "status": response.status,
                    "body": body[:5000],
                }

        except urllib.error.HTTPError as exc:
            body = exc.read().decode(
                "utf-8",
                errors="replace",
            )

            return False, {
                "url": url,
                "status": exc.code,
                "body": body[:5000],
                "error": str(exc),
            }

        except Exception as exc:
            return False, {
                "url": url,
                "error": str(exc),
            }

    def run_http_checks(self):
        for path in (
            "/api/health",
            "/api/meta",
        ):
            ok, details = self.http_get(path)

            item = {
                "path": path,
                "ok": ok,
                "details": details,
            }

            self.report["http"].append(item)

            self.record(
                "http:" + path,
                ok,
                details,
            )

    def stop_server(self):
        if not self.process:
            return

        if self.process.poll() is None:
            self.process.terminate()

            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

        self.process = None

    def finish(self):
        self.report["finished_at"] = datetime.now(
            timezone.utc
        ).isoformat()

        self.report["summary"] = {
            "checks": len(self.report["checks"]),
            "failed_checks": len(
                self.report["failed_checks"]
            ),
            "http_checks": len(self.report["http"]),
            "http_passed": sum(
                1
                for item in self.report["http"]
                if item["ok"]
            ),
        }

        report_file = (
            self.project_dir
            / ".abqaryno-real-execution-report.json"
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

    def run(self, blueprint=None):
        try:
            self.inspect_files()
            self.inspect_package()
            self.inspect_server_static()

            if not self.report["failed_checks"]:
                if self.start_server():
                    self.run_http_checks()

            self.report["status"] = (
                "PASS"
                if not self.report["failed_checks"]
                else "FAILED"
            )

            return self.finish()

        finally:
            self.stop_server()
