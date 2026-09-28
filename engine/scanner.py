#!/usr/bin/env python3
"""
🔍 Scanner Engine for Repair Repository
Responsible for project structure discovery, file classification, and type detection.
"""

from pathlib import Path
import json

class ProjectScanner:
    def __init__(self, project_path):
        self.project_path = Path(project_path).resolve()
        self.ignored_dirs = {'.git', 'node_modules', '__pycache__', '.repair-repository', 'venv', 'env', 'plans', 'reports', 'snapshots', 'logs'}

    def scan(self):
        print(f"[*] Scanning directory: {self.project_path}")
        structure = {
            "status": "EVIDENCED",
            "root": str(self.project_path),
            "files": [],
            "directories": [],
            "classification": {
                "client": [],
                "server": [],
                "config": [],
                "tests": [],
                "assets": [],
                "other": []
            }
        }

        for path in self.project_path.rglob("*"):
            # تجاهل المجلدات غير المرغوبة
            if any(part in self.ignored_dirs for part in path.parts):
                continue

            relative_path = str(path.relative_to(self.project_path))

            if path.is_dir():
                structure["directories"].append(relative_path)
            elif path.is_file():
                structure["files"].append(relative_path)
                self._classify_file(relative_path, structure["classification"])

        return structure

    def _classify_file(self, rel_path, classification):
        lower_path = rel_path.lower()
        
        # تصنيف مبني على الامتداد والموقع والاسم الفعلي
        if any(ext in lower_path for ext in ['.html', '.css']) or 'public' in lower_path or 'client' in lower_path:
            classification["client"].append(rel_path)
        elif any(ext in lower_path for ext in ['server.py', 'app.py', 'server.js', 'index.js']) or 'backend' in lower_path:
            classification["server"].append(rel_path)
        elif any(name in lower_path for name in ['package.json', 'requirements.txt', 'config', '.env', 'pyproject.toml']):
            classification["config"].append(rel_path)
        elif 'test' in lower_path or 'spec' in lower_path:
            classification["tests"].append(rel_path)
        elif any(ext in lower_path for ext in ['.png', '.jpg', '.ico', '.svg', '.mp3', '.mp4']):
            classification["assets"].append(rel_path)
        else:
            classification["other"].append(rel_path)

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    scanner = ProjectScanner(path)
    result = scanner.scan()
    print(json.dumps(result["classification"], indent=2))
