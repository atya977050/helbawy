#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
عبقرينو — إغلاق المرحلة الأولى بالكامل
PHASE 1: FOUNDATION / ARCHITECTURE / AUDIT / CREATION ENGINE BASELINE

الهدف:
1. تثبيت engine/creation.py كمحرك إنشاء أساسي.
2. منع اعتبار ملفات الترقيات القديمة محركات مستقلة.
3. توحيد مرجع المحرك في master/server.
4. فحص البنية والرموز الأساسية.
5. فحص مسار:
   Requirements
   -> Screen Proposal
   -> Approval
   -> Generator
   -> Final Report
6. فحص الاختبارات.
7. فحص syntax.
8. إنشاء سجل Phase 1.
9. إعادة الفحص بعد التثبيت.
10. عدم الانتقال إلى Phase 2 إذا لم تتحقق بوابة Phase 1.

هذا السكريبت لا ينفذ إصلاحات مشاريع خارج عبقرينو.
"""

from __future__ import annotations

import ast
import json
import re
import shutil
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "engine"
CREATION = ENGINE / "creation.py"
MASTER = ROOT / "abqaryno_master.py"
UPGRADE = ROOT / "abqaryno_complete_upgrade.py"
STUDIO_SERVER = ROOT / "studio" / "server.py"
REPORTS = ROOT / "reports"
PHASE_REPORT = REPORTS / "phase1-final-report.json"
PHASE_MD = REPORTS / "phase1-final-report.md"
PHASE_STATE = REPORTS / "phase1-state.json"


NOW = datetime.now(timezone.utc).isoformat()


@dataclass
class Check:
    id: str
    area: str
    status: str
    message: str
    evidence: str = ""
    action: str = ""


checks: list[Check] = []


def add(
    cid: str,
    area: str,
    status: str,
    message: str,
    evidence: str = "",
    action: str = "",
):
    checks.append(
        Check(
            id=cid,
            area=area,
            status=status,
            message=message,
            evidence=evidence,
            action=action,
        )
    )


def read(path: Path) -> str:
    try:
        return path.read_text(
            encoding="utf-8",
            errors="replace",
        )
    except Exception:
        return ""


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def syntax_ok(path: Path) -> bool:
    try:
        ast.parse(read(path), filename=str(path))
        return True
    except Exception:
        return False


def backup_file(path: Path):
    if not path.exists():
        return None

    backup_dir = ROOT / ".phase1_backups"
    backup_dir.mkdir(exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    destination = (
        backup_dir
        / f"{path.name}.{stamp}.bak"
    )

    shutil.copy2(path, destination)
    return destination


def replace_exact(
    path: Path,
    old: str,
    new: str,
    label: str,
):
    text = read(path)

    count = text.count(old)

    if count == 0:
        return False

    if count != 1:
        raise RuntimeError(
            f"{label}: expected one exact occurrence, found {count}"
        )

    backup_file(path)

    write(
        path,
        text.replace(old, new, 1),
    )

    return True


# ---------------------------------------------------------
# 1. BASIC STRUCTURE
# ---------------------------------------------------------

def check_structure():

    required_dirs = [
        ROOT / "engine",
        ROOT / "studio",
        ROOT / "tools",
        ROOT / "reports",
    ]

    for path in required_dirs:
        if path.exists():
            add(
                "STRUCT-" + path.name,
                "structure",
                "PASS",
                f"المجلد موجود: {path}",
            )
        else:
            path.mkdir(parents=True, exist_ok=True)

            add(
                "STRUCT-" + path.name,
                "structure",
                "FIXED",
                f"تم إنشاء المجلد: {path}",
            )


# ---------------------------------------------------------
# 2. AUTHORITATIVE CREATION ENGINE
# ---------------------------------------------------------

def check_authoritative_creation_engine():

    if not CREATION.exists():
        add(
            "ENGINE-001",
            "creation-engine",
            "BLOCKED",
            "engine/creation.py غير موجود.",
            action="لا يمكن إغلاق Phase 1.",
        )
        return False

    if not syntax_ok(CREATION):
        add(
            "ENGINE-002",
            "creation-engine",
            "BLOCKED",
            "engine/creation.py يحتوي خطأ syntax.",
            action="إصلاح syntax أولًا.",
        )
        return False

    text = read(CREATION)

    required = [
        "RequirementsEngine",
        "ScreenProposalEngine",
        "ScreenApprovalWizard",
        "ProjectGenerator",
        "FinalReport",
    ]

    missing = []

    for symbol in required:
        if not re.search(
            rf"\bclass\s+{re.escape(symbol)}\b",
            text,
        ):
            missing.append(symbol)

    if missing:
        add(
            "ENGINE-003",
            "creation-engine",
            "BLOCKED",
            "رموز أساسية ناقصة من محرك الإنشاء.",
            ", ".join(missing),
            "استكمال المحرك الأساسي.",
        )
        return False

    add(
        "ENGINE-004",
        "creation-engine",
        "PASS",
        "engine/creation.py مثبت كمحرك الإنشاء الأساسي.",
        ", ".join(required),
    )

    return True


# ---------------------------------------------------------
# 3. MASTER IMPORT
# ---------------------------------------------------------

def fix_master_import():

    if not MASTER.exists():
        add(
            "MASTER-001",
            "architecture",
            "BLOCKED",
            "abqaryno_master.py غير موجود.",
        )
        return

    text = read(MASTER)

    if "from engine.creation import" in text:
        add(
            "MASTER-002",
            "architecture",
            "PASS",
            "abqaryno_master.py يستخدم engine.creation.",
        )
        return

    add(
        "MASTER-003",
        "architecture",
        "REVIEW",
        "abqaryno_master.py لا يحتوي مرجع engine.creation واضح.",
        action="مراجعة الاستيراد.",
    )


# ---------------------------------------------------------
# 4. STUDIO SERVER
# ---------------------------------------------------------

def check_studio_server():

    if not STUDIO_SERVER.exists():
        add(
            "STUDIO-001",
            "studio",
            "BLOCKED",
            "studio/server.py غير موجود.",
        )
        return

    if not syntax_ok(STUDIO_SERVER):
        add(
            "STUDIO-002",
            "studio",
            "BLOCKED",
            "studio/server.py يحتوي خطأ syntax.",
        )
        return

    text = read(STUDIO_SERVER)

    if "engine.creation" in text:
        add(
            "STUDIO-003",
            "studio",
            "PASS",
            "Studio server مربوط بمحرك الإنشاء الأساسي.",
        )
    else:
        add(
            "STUDIO-004",
            "studio",
            "REVIEW",
            "Studio server لا يحتوي مرجعًا واضحًا لمحرك الإنشاء.",
        )


# ---------------------------------------------------------
# 5. OLD DUPLICATE ENGINE
# ---------------------------------------------------------

def retire_duplicate_upgrade():

    if not UPGRADE.exists():
        add(
            "ARCH-001",
            "architecture",
            "PASS",
            "لا يوجد ملف upgrade مكرر.",
        )
        return

    text = read(UPGRADE)

    duplicate_symbols = [
        "class RequirementsEngine",
        "class ScreenProposalEngine",
        "class ScreenApprovalWizard",
        "class ProjectGenerator",
        "class FinalReport",
    ]

    duplicates = [
        x for x in duplicate_symbols
        if x in text
    ]

    if not duplicates:
        add(
            "ARCH-002",
            "architecture",
            "PASS",
            "ملف upgrade لا يحتوي نسخة مستقلة من محرك الإنشاء.",
        )
        return

    # لا نحذف الملف.
    # فقط نثبت أنه ليس المرجع المعتمد.
    marker = (
        "\n\n"
        "# PHASE1 AUTHORITATIVE ENGINE NOTICE\n"
        "# engine/creation.py is the authoritative creation engine.\n"
        "# This legacy upgrade module is not an independent engine.\n"
    )

    if "PHASE1 AUTHORITATIVE ENGINE NOTICE" not in text:
        backup_file(UPGRADE)
        write(
            UPGRADE,
            text.rstrip() + marker,
        )

    add(
        "ARCH-003",
        "architecture",
        "PASS",
        "تم تثبيت engine/creation.py كمحرك معتمد وعدم اعتبار upgrade محركًا مستقلًا.",
        "\n".join(duplicates),
    )


# ---------------------------------------------------------
# 6. CREATION PIPELINE
# ---------------------------------------------------------

def check_creation_pipeline():

    text = read(CREATION)

    stages = {
        "REQUIREMENTS": [
            "RequirementsEngine",
            "requirements",
        ],
        "SCREEN_PROPOSAL": [
            "ScreenProposalEngine",
            "screen",
            "proposal",
        ],
        "APPROVAL": [
            "ScreenApprovalWizard",
            "approve",
            "approved",
        ],
        "GENERATOR": [
            "ProjectGenerator",
            "generate",
            "create_project",
        ],
        "REPORT": [
            "FinalReport",
            "report",
        ],
    }

    for stage, tokens in stages.items():

        hits = [
            token
            for token in tokens
            if token.lower() in text.lower()
        ]

        if hits:
            add(
                "PIPE-" + stage,
                "creation-pipeline",
                "PASS",
                f"مرحلة {stage} لها دليل داخل محرك الإنشاء.",
                ", ".join(hits),
            )
        else:
            add(
                "PIPE-" + stage,
                "creation-pipeline",
                "BLOCKED",
                f"لا يوجد دليل كافٍ لمرحلة {stage}.",
                action="استكمال المرحلة داخل engine/creation.py.",
            )


# ---------------------------------------------------------
# 7. APPROVAL CONTRACT
# ---------------------------------------------------------

def check_approval_contract():

    text = read(CREATION)

    contracts = {
        "YES": [
            "approve",
            "approved",
            "نعم",
            "اعتماد",
        ],
        "NO": [
            "reject",
            "delete",
            "حذف",
            "لا",
        ],
        "EDIT": [
            "edit",
            "modify",
            "تعديل",
        ],
    }

    for name, tokens in contracts.items():

        hits = [
            token
            for token in tokens
            if token.lower() in text.lower()
        ]

        if hits:
            add(
                "APPROVAL-" + name,
                "approval-contract",
                "PASS",
                f"مسار {name} موجود.",
                ", ".join(hits),
            )
        else:
            add(
                "APPROVAL-" + name,
                "approval-contract",
                "BLOCKED",
                f"مسار {name} غير مثبت.",
                action="استكمال عقد الاعتماد.",
            )


# ---------------------------------------------------------
# 8. TRACEABILITY
# ---------------------------------------------------------

def check_traceability():

    text = read(CREATION)

    required = [
        "requirement",
        "screen",
        "approval",
        "contract",
        "test",
        "report",
    ]

    missing = [
        x for x in required
        if x.lower() not in text.lower()
    ]

    if missing:
        add(
            "TRACE-001",
            "traceability",
            "REVIEW",
            "التتبع الكامل غير مثبت بالاسم.",
            ", ".join(missing),
            "إكمال traceability في المرحلة التالية إذا لم يكن مثبتًا فعليًا.",
        )
    else:
        add(
            "TRACE-002",
            "traceability",
            "PASS",
            "وجدت مؤشرات التتبع الأساسية.",
        )


# ---------------------------------------------------------
# 9. TESTS
# ---------------------------------------------------------

def check_tests():

    tests = []

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue

        if any(
            part in {
                ".git",
                "node_modules",
                "__pycache__",
                ".venv",
                "venv",
            }
            for part in path.parts
        ):
            continue

        name = path.name.lower()

        if (
            "test" in name
            or "tests" in {p.lower() for p in path.parts}
        ):
            tests.append(path)

    if tests:
        add(
            "TEST-001",
            "verification",
            "PASS",
            f"تم العثور على {len(tests)} ملفات اختبار محتملة.",
            "\n".join(
                str(x.relative_to(ROOT))
                for x in tests[:50]
            ),
        )
    else:
        add(
            "TEST-002",
            "verification",
            "BLOCKED",
            "لا توجد اختبارات مكتشفة.",
            action="إضافة اختبارات Phase 1.",
        )


# ---------------------------------------------------------
# 10. PYTHON SYNTAX
# ---------------------------------------------------------

def check_python():

    ignored = {
        ".git",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
    }

    failures = []

    for path in ROOT.rglob("*.py"):

        if any(
            part in ignored
            for part in path.parts
        ):
            continue

        if not syntax_ok(path):
            failures.append(
                str(path.relative_to(ROOT))
            )

    if failures:
        add(
            "PY-001",
            "syntax",
            "BLOCKED",
            "توجد ملفات Python بها أخطاء syntax.",
            "\n".join(failures),
            "إصلاح جميع أخطاء syntax.",
        )
    else:
        add(
            "PY-002",
            "syntax",
            "PASS",
            "جميع ملفات Python المكتشفة سليمة نحويًا.",
        )


# ---------------------------------------------------------
# 11. REQUIRED CREATION FILES
# ---------------------------------------------------------

def check_creation_files():

    required = [
        CREATION,
        MASTER,
        STUDIO_SERVER,
    ]

    missing = [
        str(x.relative_to(ROOT))
        for x in required
        if not x.exists()
    ]

    if missing:
        add(
            "FILES-001",
            "foundation",
            "BLOCKED",
            "ملفات تأسيسية ناقصة.",
            "\n".join(missing),
        )
    else:
        add(
            "FILES-002",
            "foundation",
            "PASS",
            "الملفات التأسيسية موجودة.",
        )


# ---------------------------------------------------------
# 12. PHASE GATE
# ---------------------------------------------------------

def phase_gate():

    blocked = [
        x for x in checks
        if x.status == "BLOCKED"
    ]

    review = [
        x for x in checks
        if x.status == "REVIEW"
    ]

    if blocked:
        return "BLOCKED"

    if review:
        return "REVIEW_REQUIRED"

    return "PHASE_1_COMPLETE"


# ---------------------------------------------------------
# 13. REPORT
# ---------------------------------------------------------

def build_report(gate):

    counts = {}

    for item in checks:
        counts[item.status] = (
            counts.get(item.status, 0) + 1
        )

    payload = {
        "tool": "Abqaryno Phase 1 Finalizer",
        "version": "1.0",
        "generated_at": NOW,
        "project_root": str(ROOT),
        "phase": 1,
        "gate": gate,
        "counts": counts,
        "checks": [
            asdict(x)
            for x in checks
        ],
    }

    write(
        PHASE_REPORT,
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
    )

    lines = [
        "# عبقرينو — تقرير إغلاق المرحلة الأولى",
        "",
        f"وقت التنفيذ: `{NOW}`",
        "",
        "## بوابة المرحلة",
        "",
        f"**{gate}**",
        "",
        "## الإحصائيات",
        "",
    ]

    for key, value in sorted(counts.items()):
        lines.append(
            f"- {key}: {value}"
        )

    lines += [
        "",
        "## النتائج",
        "",
    ]

    for item in checks:

        lines.append(
            f"### {item.id}"
        )

        lines.append(
            f"- المجال: `{item.area}`"
        )

        lines.append(
            f"- الحالة: `{item.status}`"
        )

        lines.append(
            f"- النتيجة: {item.message}"
        )

        if item.evidence:
            lines.append("")
            lines.append("الدليل:")
            lines.append("```text")
            lines.append(item.evidence[:5000])
            lines.append("```")

        if item.action:
            lines.append("")
            lines.append(
                f"الإجراء: {item.action}"
            )

        lines.append("")

    write(
        PHASE_MD,
        "\n".join(lines),
    )

    state = {
        "phase": 1,
        "status": gate,
        "generated_at": NOW,
        "next_phase_allowed": gate == "PHASE_1_COMPLETE",
    }

    write(
        PHASE_STATE,
        json.dumps(
            state,
            ensure_ascii=False,
            indent=2,
        ),
    )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    print("=" * 78)
    print(" عبقرينو — إغلاق PHASE 1")
    print("=" * 78)
    print(f"ROOT: {ROOT}")
    print()

    check_structure()
    check_creation_files()
    check_authoritative_creation_engine()
    fix_master_import()
    check_studio_server()
    retire_duplicate_upgrade()
    check_creation_pipeline()
    check_approval_contract()
    check_traceability()
    check_tests()
    check_python()

    gate = phase_gate()

    build_report(gate)

    print()
    print("=" * 78)
    print(" PHASE 1 GATE")
    print("=" * 78)
    print(gate)
    print()

    for status in [
        "BLOCKED",
        "REVIEW",
        "FIXED",
        "PASS",
    ]:
        items = [
            x for x in checks
            if x.status == status
        ]

        if items:
            print(
                f"{status:12} : {len(items)}"
            )

    print()
    print("REPORT:")
    print(PHASE_REPORT)

    print()
    print("MARKDOWN:")
    print(PHASE_MD)

    print()
    print("STATE:")
    print(PHASE_STATE)

    print("=" * 78)

    return (
        0
        if gate == "PHASE_1_COMPLETE"
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
