import json
import sys
from pathlib import Path
from datetime import datetime

class MasterAbqarynoFactory:
    def __init__(self, project_name, specification, root_dir=None):
        self.project_name = project_name
        self.specification = specification

        self.root_dir = (
            Path(root_dir).resolve()
            if root_dir
            else Path(__file__).resolve().parent.parent
        )

        safe_name = (
            str(project_name)
            .strip()
            .lower()
            .replace(" ", "-")
        )

        self.target_dir = self.root_dir / safe_name
        self.target_dir.mkdir(parents=True, exist_ok=True)
        self.brain = {
            "project": project_name,
            "specification": specification,
            "requirements": {},
            "architecture": {},
            "security": {},
            "database": {},
            "frontend": {},
            "implementation": {},
            "tests": [],
            "evidence": {}
        }

    def run_requirements_agent(self):
        print("📋 [Requirements Agent] Analyzing specs and extracting entities...")
        spec = self.specification.lower()
        if any(w in spec for w in ["قانون", "محام", "قضاي", "legal", "lawyer"]):
            domain = "Legal-Tech"
            entities = ["cases", "clients", "lawyers", "documents", "consultations"]
        elif any(w in spec for w in ["متجر", "بيع", "commerce", "shop"]):
            domain = "E-Commerce"
            entities = ["products", "orders", "customers", "payments"]
        else:
            domain = "Standard-Web"
            entities = ["users", "items", "logs"]

        self.brain["requirements"] = {"domain": domain, "entities": entities}
        print(f"✅ Domain: {domain} | Entities: {entities}")

    def run_architect_agent(self):
        print("🧠 [Architect Agent] Designing system architecture...")
        self.brain["architecture"] = {
            "stack": "Node.js + Express + SQLite + Vanilla JS UI",
            "realtime": "socket.io",
            "auth": "JWT + bcrypt"
        }
        print("✅ Architecture designed successfully.")

    def run_database_agent(self):
        print("🗄️ [Database Agent] Generating SQL schema...")
        db_dir = self.target_dir / "database"
        db_dir.mkdir(parents=True, exist_ok=True)
        
        domain = self.brain["requirements"]["domain"]
        if domain == "Legal-Tech":
            schema = """PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, password TEXT, role TEXT);
CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT);
CREATE TABLE IF NOT EXISTS cases (id INTEGER PRIMARY KEY AUTOINCREMENT, case_number TEXT UNIQUE, title TEXT, client_id INTEGER, status TEXT DEFAULT 'open', FOREIGN KEY(client_id) REFERENCES clients(id));
"""
        else:
            schema = """PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, price REAL);
"""
        (db_dir / "schema.sql").write_text(schema, encoding="utf-8")
        self.brain["database"] = {"status": "Schema generated", "path": "database/schema.sql"}
        print("✅ Database schema created.")

    def run_frontend_agent(self):
        print("🎨 [Frontend Agent] Generating UI interface (HTML/CSS/JS)...")
        public_dir = self.target_dir / "public"
        public_dir.mkdir(parents=True, exist_ok=True)

        html_content = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>{self.project_name}</title>
    <style>
        body {{ font-family: Tahoma, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
        .container {{ max-width: 900px; margin: auto; background: #1e293b; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }}
        h1 {{ color: #fbbf24; text-align: center; }}
        .card {{ background: #334155; padding: 15px; margin-bottom: 15px; border-radius: 8px; }}
        button {{ background: #fbbf24; color: #0f172a; border: none; padding: 10px 20px; font-weight: bold; border-radius: 5px; cursor: pointer; }}
        button:hover {{ background: #f59e0b; }}
        input, select {{ width: 100%; padding: 10px; margin: 8px 0; background: #0f172a; border: 1px solid #475569; color: white; border-radius: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ border: 1px solid #475569; padding: 10px; text-align: right; }}
        th {{ background: #1e293b; color: #fbbf24; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>⚖️ {self.project_name}</h1>
        <p style="text-align: center; color: #94a3b8;">تم الإنشاء آلياً بواسطة عبقرينو AI Software Factory</p>
        
        <div class="card">
            <h3>إدارة القضايا والعملاء</h3>
            <div id="status" style="color: #4ade80; margin-bottom: 10px;">🟢 النظام متصل وجاهز</div>
            <div id="data-container">
                <button onclick="loadCases()">تحميل قائمة القضايا</button>
                <table id="casesTable">
                    <thead><tr><th>رقم القضية</th><th>عنوان القضية</th><th>الحالة</th></tr></thead>
                    <tbody><tr><td colspan="3" style="text-align:center;">اضغط التحميل لعرض البيانات</td></tr></tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        async function loadCases() {{
            try {{
                const res = await fetch('/api/cases');
                const data = await res.json();
                const tbody = document.querySelector('#casesTable tbody');
                tbody.innerHTML = '';
                if(data.cases && data.cases.length > 0) {{
                    data.cases.forEach(c => {{
                        tbody.innerHTML += `<tr><td>${{c.case_number}}</td><td>${{c.title}}</td><td>${{c.status}}</td></tr>`;
                    }});
                }} else {{
                    tbody.innerHTML = '<tr><td colspan="3" style="text-align:center;">لا توجد قضايا مسجلة بعد</td></tr>';
                }}
            }} catch(e) {{
                alert('خطأ في الاتصال بالخادم');
            }}
        }}
    </script>
</body>
</html>
"""
        (public_dir / "index.html").write_text(html_content, encoding="utf-8")
        self.brain["frontend"] = {"status": "UI generated", "path": "public/index.html"}
        print("✅ Frontend interface generated successfully.")

    def run_backend_agent(self):
        print("⚙️ [Backend Agent] Generating server and API routes...")
        server_code = """const express = require("express");
const { DatabaseSync } = require("node:sqlite");
const path = require("path");
const fs = require("fs");

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

const dbPath = path.join(__dirname, "database", "app.db");
const db = new DatabaseSync(dbPath);
const schema = fs.readFileSync(path.join(__dirname, "database", "schema.sql"), "utf8");
db.exec(schema);

app.get("/api/health", (req, res) => res.json({ ok: true, status: "PASS", factory: "Abqaryno Master" }));

app.get("/api/cases", (req, res) => {
    try {
        const cases = db.prepare("SELECT * FROM cases").all();
        res.json({ ok: true, cases });
    } catch(e) {
        res.json({ ok: true, cases: [] });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`🚀 Abqaryno App running on port ${PORT}`));
"""
        (self.target_dir / "server.js").write_text(server_code, encoding="utf-8")
        
        package_json = json.dumps({
            "name": self.target_dir.name,
            "version": "1.0.0",
            "main": "server.js",
            "dependencies": { "express": "^4.19.2" }
        }, indent=2)
        (self.target_dir / "package.json").write_text(package_json, encoding="utf-8")
        self.brain["implementation"] = {"files": ["server.js", "package.json", "database/schema.sql", "public/index.html"]}
        print("✅ Backend files and static routing generated.")

    def run_test_and_evidence_agent(self):
        import json
        import shutil
        import subprocess
        from datetime import datetime

        tests = []
        root = self.target_dir

        def add_test(name, command, passed, stdout="", stderr="", exit_code=None):
            tests.append({
                "test": name,
                "command": command,
                "passed": bool(passed),
                "exit_code": exit_code,
                "stdout": stdout[-4000:],
                "stderr": stderr[-4000:],
                "timestamp": datetime.utcnow().isoformat() + "Z",
            })

        required = [
            "server.js",
            "package.json",
            "database/schema.sql",
            "public/index.html",
        ]

        missing = [x for x in required if not (root / x).exists()]

        add_test(
            "Required Files Test",
            "filesystem-check",
            not missing,
            stdout="required files present" if not missing else "",
            stderr="missing: " + ", ".join(missing) if missing else "",
            exit_code=0 if not missing else 1,
        )

        node = shutil.which("node")

        if not node:
            add_test(
                "Node Availability Test",
                "node --version",
                False,
                stderr="node executable not found",
                exit_code=127,
            )
        else:
            proc = subprocess.run(
                [node, "--check", "server.js"],
                cwd=root,
                text=True,
                capture_output=True,
            )

            add_test(
                "Server Syntax Test",
                "node --check server.js",
                proc.returncode == 0,
                proc.stdout,
                proc.stderr,
                proc.returncode,
            )

            sqlite_check = subprocess.run(
                [
                    node,
                    "-e",
                    "const { DatabaseSync } = require('node:sqlite'); "
                    "const db = new DatabaseSync(':memory:'); "
                    "db.exec('CREATE TABLE t(id INTEGER);'); "
                    "console.log('NODE_SQLITE_RUNTIME_OK');",
                ],
                cwd=root,
                text=True,
                capture_output=True,
            )

            add_test(
                "SQLite Runtime Test",
                "node:sqlite in-memory database",
                sqlite_check.returncode == 0
                and "NODE_SQLITE_RUNTIME_OK" in sqlite_check.stdout,
                sqlite_check.stdout,
                sqlite_check.stderr,
                sqlite_check.returncode,
            )

        # عبقرينو V2: تحقق مستقل من المشروع المولد
        creation_verification = None

        try:
            from engine.creation import CreationVerificationEngine

            creation_verification = (
                CreationVerificationEngine().verify(root)
            )

            for check in creation_verification.get("checks", []):
                add_test(
                    "Creation V2 | " + str(check.get("name", "unknown")),
                    "CreationVerificationEngine V2",
                    check.get("status") == "PASSED",
                    json.dumps(
                        check,
                        ensure_ascii=False,
                    ),
                    "",
                    0 if check.get("status") == "PASSED" else 1,
                )

        except Exception as exc:
            add_test(
                "Creation V2 Verification",
                "CreationVerificationEngine V2",
                False,
                "",
                repr(exc),
                1,
            )

            creation_verification = {
                "version": 2,
                "status": "FAILED",
                "error": repr(exc),
                "checks": [],
                "failed_checks": ["Creation V2 Verification"],
            }

        verified = bool(tests) and all(
            t["passed"] for t in tests
        )

        evidence = {
            "version": 2,
            "verified": verified,
            "status": "PASS" if verified else "FAILED",
            "tests": tests,
            "creation_verification": creation_verification,
            "runtime": {
                "node": subprocess.run(
                    ["node", "--version"],
                    text=True,
                    capture_output=True,
                ).stdout.strip()
                if shutil.which("node") else None
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        (root / ".abqaryno-evidence.json").write_text(
            json.dumps(
                evidence,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        self.brain["tests"] = tests
        self.brain["evidence"] = evidence

        print("\n=== ABQARYNO REAL VERIFICATION V2 ===")

        for test in tests:
            state = "PASS" if test["passed"] else "FAIL"
            print(f"{state} | {test['test']}")

        print(
            f"VERIFICATION_STATUS={evidence['status']}"
        )

    def build(self):
        self.run_requirements_agent()
        self.run_architect_agent()
        self.run_database_agent()
        self.run_frontend_agent()
        self.run_backend_agent()
        self.run_test_and_evidence_agent()

        evidence = self.brain.get("evidence", {})
        verification = evidence.get(
            "creation_verification",
            {},
        )

        gate_passed = (
            evidence.get("status") == "PASS"
            and evidence.get("verified") is True
            and verification.get("status") == "PASSED"
            and not verification.get("failed_checks")
        )

        self.brain["creation_gate"] = {
            "version": 1,
            "status": "PASSED" if gate_passed else "BLOCKED",
            "required": [
                "generation",
                "syntax",
                "dependencies",
                "runtime_process",
                "http_runtime",
                "evidence",
            ],
        }

        if not gate_passed:
            self.brain["creation_status"] = "VERIFICATION_BLOCKED"

            evidence["creation_gate"] = self.brain["creation_gate"]

            (self.target_dir / ".abqaryno-evidence.json").write_text(
                __import__("json").dumps(
                    evidence,
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            raise RuntimeError(
                "ABQARYNO_CREATION_GATE_BLOCKED"
            )

        self.brain["creation_status"] = "VERIFIED"

        evidence["creation_gate"] = self.brain["creation_gate"]
        evidence["creation_status"] = "VERIFIED"

        (self.target_dir / ".abqaryno-evidence.json").write_text(
            __import__("json").dumps(
                evidence,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        print(
            f"CREATION_GATE=PASSED | "
            f"PROJECT={self.project_name}"
        )
        print(
            "🌟 ABQARYNO BUILD VERIFIED"
        )

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print(
            "USAGE: python engine/abqaryno_master_factory.py "
            "<project_name> <specification>"
        )
        raise SystemExit(2)

    project_name = sys.argv[1]
    specification = sys.argv[2]

    factory = MasterAbqarynoFactory(
        project_name,
        specification,
    )

    factory.build()

