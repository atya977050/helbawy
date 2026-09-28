#!/usr/bin/env python3
import json
from pathlib import Path

class DeepRepairEngine:
    def __init__(self, project_path):
        self.project_path = Path(project_path).resolve()
        self.public_dir = self.project_path / "public"
        self.reports_dir = self.project_path / "reports"

    def execute_repairs(self):
        print(f"[+] Executing Deep Code Repair on: {self.project_path}")
        app_js = self.public_dir / "app.js"
        fixes = []
        if app_js.exists():
            content = app_js.read_text(encoding="utf-8")
            if "ontrack" not in content:
                patch = "\n peerConnection.ontrack = (e) => { remoteVideo.srcObject = e.streams[0]; };"
                app_js.write_text(content + patch, encoding="utf-8")
                fixes.append("Injected ontrack handler.")
        
        self.reports_dir.mkdir(exist_ok=True, parents=True)
        report = {"status": "Repairs completed", "fixes": fixes}
        (self.reports_dir / "deep-repair-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("[✓] Repairs completed.")
        return report
