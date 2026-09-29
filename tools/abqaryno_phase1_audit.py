#!/usr/bin/env python3

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

NOW = time.strftime("%Y-%m-%dT%H:%M:%S")


@dataclass
class Finding:
    id: str
    category: str
    severity: str
    status: str
    target: str
    message: str
    evidence: str = ""
    recommendation: str = ""


findings: list[Finding] = []


def add(
    fid: str,
    category: str,
    severity: str,
    status: str,
    target: str,
    message: str,
    evidence: str = "",
    recommendation: str = "",
):
    findings.append(
        Finding(
            id=fid,
            category=category,
            severity=severity,
            status=status,
            target=target,
            message=message,
            evidence=evidence,
            recommendation=recommendation,
        )
    )


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except Exception:
        return str(path)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def all_files():
    ignored = {
        ".git",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        ".pytest_cache",
        ".mypy_cache",
    }

    result = []

    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue

        if any(part in ignored for part in p.parts):
            continue

        result.append(p)

    return sorted(result)


def classify_files(files):
    groups = {
        "python": [],
        "javascript": [],
        "typescript": [],
        "html": [],
        "css": [],
        "json": [],
        "markdown": [],
        "tests": [],
        "other": [],
    }

    for p in files:
        suffix = p.suffix.lower()

        if suffix == ".py":
            groups["python"].append(p)
        elif suffix in {".js", ".mjs", ".cjs"}:
            groups["javascript"].append(p)
        elif suffix in {".ts", ".tsx"}:
            groups["typescript"].append(p)
        elif suffix in {".html", ".htm"}:
            groups["html"].append(p)
        elif suffix == ".css":
            groups["css"].append(p)
        elif suffix == ".json":
            groups["json"].append(p)
        elif suffix in {".md", ".markdown"}:
            groups["markdown"].append(p)
        elif (
            "test" in p.name.lower()
            or "tests" in {x.lower() for x in p.parts}
        ):
            groups["tests"].append(p)
        else:
            groups["other"].append(p)

    return groups


def run_compile_checks(groups):
    for path in groups["python"]:
        try:
            source = read_text(path)
            ast.parse(source, filename=str(path))

            add(
                "PY-SYNTAX-" + path.name,
                "syntax",
                "INFO",
                "PASS",
                rel(path),
                "Python syntax is valid.",
            )
        except Exception as exc:
            add(
                "PY-SYNTAX-" + path.name,
                "syntax",
                "CRITICAL",
                "FAIL",
                rel(path),
                "Python syntax error.",
                str(exc),
                "Fix syntax before proceeding.",
            )


def find_routes(server_path: Path):
    text = read_text(server_path)

    routes = []

    patterns = [
        r'self\.path\s*==\s*["\']([^"\']+)["\']',
        r'self\.path\.startswith\(\s*["\']([^"\']+)["\']',
        r'@(?:app|router)\.(?:get|post|put|delete|patch)\(\s*["\']([^"\']+)',
    ]

    for pattern in patterns:
        routes.extend(re.findall(pattern, text))

    return sorted(set(routes))


def audit_server(groups):
    servers = [
        p for p in groups["python"]
        if p.name in {"server.py", "app.py"}
    ]

    if not servers:
        add(
            "SERVER-001",
            "runtime",
            "CRITICAL",
            "FAIL",
            "server",
            "No server.py/app.py was discovered.",
            "",
            "Verify the actual runtime entrypoint.",
        )
        return

    for server in servers:
        routes = find_routes(server)

        if not routes:
            add(
                "SERVER-ROUTES-" + server.name,
                "runtime",
                "WARNING",
                "FAIL",
                rel(server),
                "No recognizable HTTP routes were detected.",
                "",
                "Review the server routing layer.",
            )
        else:
            add(
                "SERVER-ROUTES-" + server.name,
                "runtime",
                "INFO",
                "PASS",
                rel(server),
                f"Detected {len(routes)} HTTP route patterns.",
                "\n".join(routes),
            )

        text = read_text(server)

        important_routes = [
            "/api/analyze",
            "/api/state",
            "/api/create",
            "/api/project/zip",
            "/api/project/download",
            "/api/owner/login",
        ]

        for route in important_routes:
            if route in text:
                add(
                    "ROUTE-" + route.replace("/", "_"),
                    "api",
                    "INFO",
                    "FOUND",
                    rel(server),
                    f"Route detected: {route}",
                )
            else:
                add(
                    "ROUTE-" + route.replace("/", "_"),
                    "api",
                    "WARNING",
                    "MISSING",
                    rel(server),
                    f"Expected route was not detected: {route}",
                    "",
                    "Determine whether this route is required by the current architecture.",
                )


def audit_creation_engine(groups):
    candidates = [
        p for p in groups["python"]
        if p.name in {"creation.py", "abqaryno_complete_upgrade.py", "abqaryno_master.py"}
    ]

    if not candidates:
        add(
            "ENGINE-001",
            "creation-engine",
            "CRITICAL",
            "MISSING",
            "engine",
            "No known creation engine file was found.",
            "",
            "Locate the authoritative creation engine.",
        )
        return

    required_symbols = [
        "RequirementsEngine",
        "ScreenProposalEngine",
        "ScreenApprovalWizard",
        "ProjectGenerator",
        "FinalReport",
    ]

    for symbol in required_symbols:
        found = False

        for path in candidates:
            text = read_text(path)

            if re.search(
                rf"\b(class|def)\s+{re.escape(symbol)}\b",
                text,
            ):
                found = True
                add(
                    f"ENGINE-{symbol}",
                    "creation-engine",
                    "INFO",
                    "FOUND",
                    rel(path),
                    f"Detected {symbol}.",
                )
                break

        if not found:
            add(
                f"ENGINE-{symbol}",
                "creation-engine",
                "WARNING",
                "MISSING",
                "engine",
                f"{symbol} was not detected.",
                "",
                f"Implement or locate the authoritative {symbol}.",
            )


def audit_approval_contract(groups):
    text_pool = ""

    for path in groups["python"]:
        if path.name in {
            "creation.py",
            "server.py",
            "abqaryno_complete_upgrade.py",
            "abqaryno_master.py",
        }:
            text_pool += "\n" + read_text(path)

    checks = {
        "YES_APPROVAL": [
            "approve",
            "approved",
            "اعتماد",
            "نعم",
        ],
        "NO_REJECTION": [
            "reject",
            "rejected",
            "delete",
            "حذف",
            "لا",
        ],
        "EDIT_FLOW": [
            "edit",
            "modify",
            "تعديل",
        ],
        "SCREEN_PROPOSAL": [
            "ScreenProposal",
            "screen_proposal",
            "اقتراح",
        ],
        "SCREEN_APPROVAL": [
            "ScreenApproval",
            "screen_approval",
            "اعتماد الشاشة",
        ],
    }

    for key, tokens in checks.items():
        hits = [
            token
            for token in tokens
            if token.lower() in text_pool.lower()
        ]

        if hits:
            add(
                "APPROVAL-" + key,
                "screen-approval",
                "INFO",
                "FOUND",
                "creation/server",
                f"Detected approval-flow evidence: {', '.join(hits)}",
            )
        else:
            add(
                "APPROVAL-" + key,
                "screen-approval",
                "WARNING",
                "MISSING",
                "creation/server",
                f"No evidence found for {key}.",
                "",
                "Implement and test this decision path.",
            )


def audit_traceability(groups):
    names = [
        "requirement",
        "requirements",
        "screen",
        "function",
        "contract",
        "acceptance",
        "test",
        "report",
        "trace",
    ]

    combined = ""

    for path in groups["python"]:
        combined += "\n" + read_text(path)

    for name in names:
        if name.lower() in combined.lower():
            add(
                "TRACE-" + name,
                "traceability",
                "INFO",
                "FOUND",
                "engine",
                f"Evidence for '{name}' exists in source.",
            )
        else:
            add(
                "TRACE-" + name,
                "traceability",
                "WARNING",
                "MISSING",
                "engine",
                f"No obvious evidence for '{name}'.",
                "",
                "Add explicit traceability instead of relying on naming conventions.",
            )


def audit_tests(groups):
    test_files = groups["tests"]

    if not test_files:
        add(
            "TEST-001",
            "verification",
            "CRITICAL",
            "MISSING",
            "tests",
            "No test files were discovered.",
            "",
            "Create automated tests before declaring behavioral completion.",
        )
    else:
        add(
            "TEST-001",
            "verification",
            "INFO",
            "FOUND",
            "tests",
            f"Detected {len(test_files)} possible test files.",
            "\n".join(rel(p) for p in test_files[:50]),
        )


def audit_generated_project_pipeline(groups):
    combined = ""

    for path in groups["python"]:
        combined += "\n" + read_text(path)

    required = {
        "GENERATOR": [
            "ProjectGenerator",
            "create_project",
            "generate_project",
        ],
        "ZIP": [
            "create_zip",
            "make_archive",
            "/api/project/zip",
        ],
        "REPORT": [
            "FinalReport",
            "final_report",
            "report",
        ],
        "REPAIR": [
            "repair",
            "fix",
            "root_cause",
        ],
        "VERIFY": [
            "verify",
            "verification",
            "test",
        ],
    }

    for key, tokens in required.items():
        hits = [x for x in tokens if x.lower() in combined.lower()]

        if hits:
            add(
                "PIPELINE-" + key,
                "pipeline",
                "INFO",
                "FOUND",
                "engine",
                f"{key} evidence detected.",
                ", ".join(hits),
            )
        else:
            add(
                "PIPELINE-" + key,
                "pipeline",
                "WARNING",
                "MISSING",
                "engine",
                f"No reliable {key} implementation evidence detected.",
                "",
                f"Implement and connect the {key} stage.",
            )


def audit_ui(groups):
    html_files = groups["html"]

    if not html_files:
        add(
            "UI-001",
            "ui",
            "WARNING",
            "MISSING",
            "public",
            "No HTML interface files were discovered.",
        )
        return

    buttons = 0
    forms = 0
    scripts = 0

    for path in html_files:
        text = read_text(path)

        buttons += len(
            re.findall(r"<button\b", text, re.I)
        )

        forms += len(
            re.findall(r"<form\b", text, re.I)
        )

        scripts += len(
            re.findall(r"<script\b", text, re.I)
        )

    add(
        "UI-002",
        "ui",
        "INFO",
        "FOUND",
        "html",
        f"HTML={len(html_files)}, buttons={buttons}, forms={forms}, scripts={scripts}",
    )

    for path in html_files:
        text = read_text(path)

        if "نعم" in text or "اعتماد" in text:
            add(
                "UI-APPROVE-" + path.name,
                "ui-approval",
                "INFO",
                "FOUND",
                rel(path),
                "Approval UI text detected.",
            )

        if "لا" in text or "حذف" in text:
            add(
                "UI-REJECT-" + path.name,
                "ui-approval",
                "INFO",
                "FOUND",
                rel(path),
                "Reject/delete UI text detected.",
            )

        if "تعديل" in text:
            add(
                "UI-EDIT-" + path.name,
                "ui-approval",
                "INFO",
                "FOUND",
                rel(path),
                "Edit UI text detected.",
            )


def audit_duplicate_engines(groups):
    known = [
        p for p in groups["python"]
        if p.name in {
            "creation.py",
            "abqaryno_complete_upgrade.py",
            "abqaryno_master.py",
        }
    ]

    if len(known) > 1:
        add(
            "ARCH-001",
            "architecture",
            "WARNING",
            "REVIEW",
            "engine",
            "Multiple possible authoritative creation-engine files detected.",
            "\n".join(rel(p) for p in known),
            "Choose one authoritative implementation and remove/retire duplicate logic.",
        )


def audit_procfile():
    procfile = ROOT / "Procfile"

    if not procfile.exists():
        add(
            "DEPLOY-001",
            "deployment",
            "WARNING",
            "MISSING",
            "Procfile",
            "Procfile not found.",
        )
        return

    text = read_text(procfile)

    add(
        "DEPLOY-002",
        "deployment",
        "INFO",
        "FOUND",
        "Procfile",
        text.strip(),
    )


def audit_requirements():
    path = ROOT / "requirements.txt"

    if not path.exists():
        add(
            "DEPLOY-003",
            "deployment",
            "WARNING",
            "MISSING",
            "requirements.txt",
            "requirements.txt not found.",
        )
    else:
        add(
            "DEPLOY-004",
            "deployment",
            "INFO",
            "FOUND",
            "requirements.txt",
            f"{len(read_text(path).splitlines())} requirement lines detected.",
        )


def build_summary(files, groups):
    counts = {}

    for item in findings:
        counts[item.status] = counts.get(item.status, 0) + 1

    critical = [
        asdict(x)
        for x in findings
        if x.severity == "CRITICAL"
        and x.status in {"FAIL", "MISSING"}
    ]

    warnings = [
        asdict(x)
        for x in findings
        if x.severity == "WARNING"
        and x.status in {"FAIL", "MISSING", "REVIEW"}
    ]

    return {
        "generated_at": NOW,
        "root": str(ROOT),
        "total_files": len(files),
        "file_counts": {
            k: len(v)
            for k, v in groups.items()
        },
        "finding_counts": counts,
        "critical_blockers": critical,
        "warnings": warnings,
        "completion_gate": (
            "BLOCKED"
            if critical
            else "REVIEW_REQUIRED"
            if warnings
            else "READY_FOR_NEXT_PHASE"
        ),
    }


def write_reports(files, groups):
    summary = build_summary(files, groups)

    payload = {
        "tool": "Abqaryno Phase 1 Audit",
        "version": "1.0",
        "generated_at": NOW,
        "project_root": str(ROOT),
        "summary": summary,
        "findings": [asdict(x) for x in findings],
        "files": [rel(p) for p in files],
    }

    json_path = REPORT_DIR / "abqaryno-phase1-audit.json"
    md_path = REPORT_DIR / "abqaryno-phase1-audit.md"

    json_path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    lines = []

    lines.append("# عبقرينو — تقرير المرحلة الأولى")
    lines.append("")
    lines.append(f"وقت الفحص: `{NOW}`")
    lines.append(f"الجذر: `{ROOT}`")
    lines.append("")
    lines.append("## البوابة")
    lines.append("")
    lines.append(
        f"**{summary['completion_gate']}**"
    )
    lines.append("")

    lines.append("## إحصائيات الملفات")
    lines.append("")

    for key, value in summary["file_counts"].items():
        lines.append(f"- {key}: {value}")

    lines.append("")
    lines.append("## نتائج الفحص")
    lines.append("")

    for status, count in sorted(
        summary["finding_counts"].items()
    ):
        lines.append(f"- {status}: {count}")

    lines.append("")
    lines.append("## العوائق الحرجة")
    lines.append("")

    if not summary["critical_blockers"]:
        lines.append("- لا توجد عوائق حرجة مكتشفة آليًا.")
    else:
        for item in summary["critical_blockers"]:
            lines.append(
                f"- **{item['id']}** — {item['target']} — "
                f"{item['message']}"
            )

    lines.append("")
    lines.append("## التحذيرات")
    lines.append("")

    if not summary["warnings"]:
        lines.append("- لا توجد تحذيرات.")
    else:
        for item in summary["warnings"]:
            lines.append(
                f"- **{item['id']}** — {item['target']} — "
                f"{item['message']}"
            )

    lines.append("")
    lines.append("## جميع النتائج")
    lines.append("")

    for item in findings:
        lines.append(
            f"### {item.id}"
        )
        lines.append(
            f"- التصنيف: `{item.category}`"
        )
        lines.append(
            f"- الخطورة: `{item.severity}`"
        )
        lines.append(
            f"- الحالة: `{item.status}`"
        )
        lines.append(
            f"- الهدف: `{item.target}`"
        )
        lines.append(
            f"- الرسالة: {item.message}"
        )

        if item.evidence:
            lines.append("")
            lines.append("الدليل:")
            lines.append("```text")
            lines.append(item.evidence[:6000])
            lines.append("```")

        if item.recommendation:
            lines.append("")
            lines.append(
                f"التوصية: {item.recommendation}"
            )

        lines.append("")

    md_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    return json_path, md_path


def main():
    print("=" * 78)
    print(" عبقرينو — PHASE 1 ARCHITECTURE / FUNCTION AUDIT")
    print("=" * 78)
    print(f"ROOT: {ROOT}")
    print()

    files = all_files()

    if not files:
        print("ERROR: لم يتم العثور على ملفات المشروع.")
        return 2

    groups = classify_files(files)

    print(f"FILES: {len(files)}")
    print()

    run_compile_checks(groups)
    audit_server(groups)
    audit_creation_engine(groups)
    audit_approval_contract(groups)
    audit_traceability(groups)
    audit_tests(groups)
    audit_generated_project_pipeline(groups)
    audit_ui(groups)
    audit_duplicate_engines(groups)
    audit_procfile()
    audit_requirements()

    summary = build_summary(files, groups)

    json_path, md_path = write_reports(
        files,
        groups,
    )

    print("=" * 78)
    print(" SUMMARY")
    print("=" * 78)

    for key, value in summary["file_counts"].items():
        print(f"{key:15} {value}")

    print()
    print("FINDINGS")

    for key, value in sorted(
        summary["finding_counts"].items()
    ):
        print(f"{key:15} {value}")

    print()
    print(
        "COMPLETION GATE:",
        summary["completion_gate"],
    )

    print()
    print("REPORT JSON:")
    print(json_path)

    print()
    print("REPORT MARKDOWN:")
    print(md_path)

    print()
    print("=" * 78)

    if summary["critical_blockers"]:
        print("CRITICAL BLOCKERS:")
        for item in summary["critical_blockers"]:
            print(
                f"- {item['id']}: "
                f"{item['message']}"
            )

    print("=" * 78)

    return (
        2
        if summary["critical_blockers"]
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
