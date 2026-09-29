#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

CREATION = ROOT / "engine" / "creation.py"
SERVER = ROOT / "studio" / "server.py"
UI = ROOT / "studio" / "ui"


@dataclass
class Finding:
    id: str
    severity: str
    area: str
    title: str
    evidence: str
    expected: str = ""
    recommendation: str = ""
    file: str = ""
    line: int | None = None


findings: list[Finding] = []


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def add(
    fid,
    severity,
    area,
    title,
    evidence,
    expected="",
    recommendation="",
    file=None,
    line=None,
):
    # حماية سكريبت الفحص من تمرير Path كوسيط موضعي بالخطأ.
    # هذا لا يغيّر البرنامج الذي يتم فحصه.
    if isinstance(recommendation, Path) and file is None:
        file = recommendation
        recommendation = ""

    if isinstance(expected, Path) and file is None:
        file = expected
        expected = ""

    if isinstance(file, Path):
        file = rel(file)

    findings.append(
        Finding(
            fid,
            severity,
            area,
            title,
            str(evidence),
            str(expected),
            str(recommendation),
            file or "",
            line,
        )
    )


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        return f"__READ_ERROR__: {exc}"


def line_of(text: str, needle: str):
    pos = text.find(needle)
    if pos < 0:
        return None
    return text.count("\n", 0, pos) + 1


def parse(path: Path):
    text = read(path)

    if text.startswith("__READ_ERROR__"):
        add(
            "SRC-001",
            "FAIL",
            "source",
            "تعذر قراءة الملف",
            text,
            file=path,
        )
        return None, text

    try:
        return ast.parse(text, filename=str(path)), text
    except SyntaxError as exc:
        add(
            "SRC-002",
            "FAIL",
            "syntax",
            "خطأ Python syntax",
            f"{exc.msg} — line {exc.lineno}",
            "Python files must compile.",
            "إصلاح syntax قبل أي اختبار سلوكي.",
            path,
            exc.lineno,
        )
        return None, text


def classes(tree):
    result = {}

    if tree is None:
        return result

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            result[node.name] = {}

            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    result[node.name][item.name] = item.lineno

    return result


def functions(tree):
    if tree is None:
        return {}

    return {
        node.name: node.lineno
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def check_python_sources():
    trees = {}

    for path in [CREATION, SERVER]:
        if not path.exists():
            add(
                "SRC-MISSING-" + rel(path),
                "FAIL",
                "source",
                "ملف أساسي مفقود",
                rel(path),
                file=path,
            )
            continue

        tree, text = parse(path)

        if tree is not None:
            trees[path] = tree

        if tree is not None:
            add(
                "SYNTAX-" + rel(path),
                "PASS",
                "syntax",
                "Python syntax سليم",
                rel(path),
                file=path,
            )

    return trees


def check_creation_engine(trees):
    tree = trees.get(CREATION)

    if tree is None:
        return

    cls = classes(tree)

    required = {
        "RequirementsEngine": "analyze",
        "ScreenProposalEngine": "proposals",
        "ScreenApprovalWizard": "choose",
        "ProjectGenerator": "generate",
    }

    for name, method in required.items():

        if name not in cls:
            add(
                f"ENG-{name}",
                "FAIL",
                "engine",
                f"{name} غير موجود",
                "class غير موجود.",
                "وجود المحرك المطلوب.",
                "لا تكتب اختبارًا لهذا المحرك قبل تحديد API الحقيقي.",
                CREATION,
            )
            continue

        if method not in cls[name]:
            add(
                f"ENG-{name}-{method}",
                "FAIL",
                "engine",
                f"{name}.{method} غير موجودة",
                f"class موجود لكن {method} غير موجودة.",
                "API حقيقي قابل للتنفيذ.",
                "مراجعة engine قبل الاختبار.",
                CREATION,
            )
            continue

        add(
            f"ENG-{name}-OK",
            "PASS",
            "engine",
            f"{name}.{method} موجودة",
            f"line={cls[name][method]}",
            file=CREATION,
            line=cls[name][method],
        )

    wizard = next(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
            and node.name == "ScreenApprovalWizard"
        ),
        None,
    )

    if wizard:

        init = next(
            (
                node
                for node in wizard.body
                if isinstance(node, ast.FunctionDef)
                and node.name == "__init__"
            ),
            None,
        )

        choose = next(
            (
                node
                for node in wizard.body
                if isinstance(node, ast.FunctionDef)
                and node.name == "choose"
            ),
            None,
        )

        if init:
            args = [a.arg for a in init.args.args]

            add(
                "WIZARD-INIT",
                "INFO",
                "engine",
                "توقيع ScreenApprovalWizard.__init__",
                str(args),
                "الاختبارات يجب أن تستخدم التوقيع الحقيقي.",
                file=CREATION,
                line=init.lineno,
            )

        if choose:
            args = [a.arg for a in choose.args.args]

            add(
                "WIZARD-CHOOSE",
                "INFO",
                "engine",
                "توقيع ScreenApprovalWizard.choose",
                str(args),
                "لا نفترض arguments غير الموجودة.",
                "اختبار choose يجب أن يستخدم API الحقيقي.",
                CREATION,
                choose.lineno,
            )

            source = read(CREATION)

            body_start = source.find("def choose(", choose.lineno)
            if body_start >= 0:
                choose_text = source[body_start:]

                for term in [
                    "choice in (\"1\", \"2\", \"3\")",
                    "choice == \"4\"",
                    "choice == \"5\"",
                    "choice == \"6\"",
                ]:
                    if term in choose_text:
                        add(
                            "WIZARD-BEHAVIOR-" + str(abs(hash(term))),
                            "INFO",
                            "engine",
                            "Wizard يحتوي مسار تفاعلي",
                            term,
                            "السلوك يجب اختباره عبر التنفيذ الحقيقي.",
                            "لا تستخدم مجرد وجود النص كإثبات نجاح.",
                            CREATION,
                        )

    generator = next(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
            and node.name == "ProjectGenerator"
        ),
        None,
    )

    if generator:

        generate = next(
            (
                node
                for node in generator.body
                if isinstance(node, ast.FunctionDef)
                and node.name == "generate"
            ),
            None,
        )

        if generate:
            args = [a.arg for a in generate.args.args]

            add(
                "GENERATOR-SIGNATURE",
                "INFO",
                "engine",
                "توقيع ProjectGenerator.generate",
                str(args),
                "مطابقته مع /api/create.",
                file=CREATION,
                line=generate.lineno,
            )


def check_server(trees):
    if not SERVER.exists():
        return

    source = read(SERVER)

    create_line = line_of(
        source,
        'if self.path == "/api/create":',
    )

    if create_line:
        add(
            "SERVER-CREATE",
            "PASS",
            "server",
            "/api/create موجود",
            f"line={create_line}",
            file=SERVER,
            line=create_line,
        )
    else:
        add(
            "SERVER-CREATE",
            "FAIL",
            "server",
            "/api/create غير موجود",
            "لم يتم العثور على route.",
            "وجود endpoint حقيقي للإنشاء.",
            file=SERVER,
        )

    if re.search(r"generator\.generate\s*\(", source):
        add(
            "SERVER-GENERATOR",
            "PASS",
            "server",
            "/api/create يستدعي generator.generate",
            "generator.generate(...) موجود.",
            file=SERVER,
        )
    else:
        add(
            "SERVER-GENERATOR",
            "FAIL",
            "server",
            "ProjectGenerator غير مربوط بـ /api/create",
            "لم يظهر generator.generate.",
            "ربط المسار بالمولد.",
            file=SERVER,
        )

    for symbol in [
        "RequirementsEngine",
        "ScreenProposalEngine",
        "ScreenApprovalWizard",
        "ProjectGenerator",
    ]:

        count = len(
            re.findall(
                rf"\b{re.escape(symbol)}\b",
                source,
            )
        )

        if count:
            add(
                "SERVER-SYMBOL-" + symbol,
                "INFO",
                "server",
                f"{symbol} مستخدم/مذكور في server",
                f"occurrences={count}",
                "وجود الاسم لا يثبت التنفيذ.",
                "فحص call-site الحقيقي.",
                SERVER,
            )
        else:
            add(
                "SERVER-SYMBOL-" + symbol,
                "REVIEW",
                "server",
                f"{symbol} غير ظاهر في server",
                "لا يوجد occurrence.",
                "إذا كان جزءًا من المسار، يجب إثبات الربط.",
                SERVER,
            )

    create_match = re.search(
        r'if self\.path == "/api/create":(?P<body>.*?)(?=\n\s*if self\.path == |\Z)',
        source,
        re.S,
    )

    if create_match:

        body = create_match.group("body")

        if "approved" in body:
            add(
                "CREATE-APPROVED",
                "PASS",
                "binding",
                "approved يدخل مسار /api/create",
                "approved موجود داخل create route.",
                "الاعتماد يجب أن يكون نتيجة فعلية.",
                "فحص مصدر approved.",
                SERVER,
            )
        else:
            add(
                "CREATE-APPROVED",
                "REVIEW",
                "binding",
                "لم يثبت approved داخل create route",
                "لا يوجد approved داخل block.",
                "تحديد مصدر الاعتماد.",
                file=SERVER,
            )

        if "RequirementsEngine" in body:
            add(
                "CREATE-REANALYZE",
                "REVIEW",
                "architecture",
                "السيرفر يعيد تحليل الفكرة أثناء الإنشاء",
                "RequirementsEngine.analyze(idea) داخل /api/create.",
                "التعديلات المعتمدة يجب ألا تضيع.",
                "مراجعة هل إعادة التحليل مقصودة أم تتجاوز تعديلات المستخدم.",
                SERVER,
            )


def check_ui():
    pages = [
        "create-idea.html",
        "create-understanding.html",
        "create-requirements.html",
        "create-plan.html",
        "create-build.html",
    ]

    ui_text = {}

    for name in pages:

        path = UI / name

        if not path.exists():
            add(
                "UI-MISSING-" + name,
                "FAIL",
                "ui",
                f"{name} مفقودة",
                rel(path),
                file=path,
            )
            continue

        text = read(path)
        ui_text[name] = text

        add(
            "UI-PRESENT-" + name,
            "PASS",
            "ui",
            f"{name} موجودة",
            rel(path),
            file=path,
        )

    # Requirements
    req = ui_text.get("create-requirements.html", "")

    if re.search(r"(اعتماد|مستبعد|choices|approved|rejected)", req):
        add(
            "UI-REQ-DECISION",
            "PASS",
            "ui",
            "واجهة المتطلبات تحتوي قرار اعتماد/استبعاد",
            "decision markers موجودة.",
            file=UI / "create-requirements.html",
        )
    else:
        add(
            "UI-REQ-DECISION",
            "REVIEW",
            "ui",
            "تعذر إثبات قرار المتطلبات",
            "لا توجد markers واضحة.",
            file=UI / "create-requirements.html",
        )

    # Plan
    plan = ui_text.get("create-plan.html", "")

    if "abqarynoSelectedScreens" in plan:
        add(
            "UI-PLAN-SELECTED",
            "PASS",
            "dataflow",
            "الخطة تقرأ الشاشات المختارة",
            "abqarynoSelectedScreens موجود.",
            file=UI / "create-plan.html",
        )
    else:
        add(
            "UI-PLAN-SELECTED",
            "FAIL",
            "dataflow",
            "الخطة لا تقرأ الشاشات المختارة",
            "key غير موجود.",
            file=UI / "create-plan.html",
        )

    if re.search(r"approved\s*:\s*true", plan):
        add(
            "UI-PLAN-FIXED-APPROVED",
            "REVIEW",
            "dataflow",
            "الخطة تضع approved=true مباشرة",
            "approved:true موجود.",
            "هذا لا يثبت اعتماد تصميم حقيقي.",
            "يجب تتبع مصدر approved قبل كتابة اختبار Phase 3.",
            UI / "create-plan.html",
        )

    # Build
    build = ui_text.get("create-build.html", "")

    if "/api/create" in build:
        add(
            "UI-BUILD-API",
            "PASS",
            "dataflow",
            "واجهة Build تستدعي /api/create",
            "/api/create موجود.",
            file=UI / "create-build.html",
        )
    else:
        add(
            "UI-BUILD-API",
            "FAIL",
            "dataflow",
            "واجهة Build لا تستدعي /api/create",
            "endpoint غير موجود.",
            file=UI / "create-build.html",
        )

    if "approved" in build:
        add(
            "UI-BUILD-APPROVED",
            "PASS",
            "dataflow",
            "Build يستخدم approved",
            "approved موجود.",
            "فحص مصدره مطلوب.",
            file=UI / "create-build.html",
        )

    # Actual proposal UI.
    combined = "\n".join(ui_text.values())

    proposal_terms = [
        "ScreenProposalEngine",
        "ScreenApprovalWizard",
        "variant",
        "proposal",
        "اعتماد التصميم",
        "رفض التصميم",
        "تصميمات أخرى",
        "تعديل الشاشة",
    ]

    hits = {
        term: len(re.findall(re.escape(term), combined, re.I))
        for term in proposal_terms
    }

    if not any(hits.values()):
        add(
            "UI-PROPOSAL-MISSING",
            "REVIEW",
            "ui",
            "لا توجد واجهة واضحة لاعتماد تصميمات الشاشة",
            json.dumps(hits, ensure_ascii=False),
            "عرض تصميمات فعلية ثم اعتماد/رفض/تعديل.",
            "لا نكتب اختبار Phase 3 قبل حسم هذا المسار.",
        )
    else:
        add(
            "UI-PROPOSAL-PRESENT",
            "INFO",
            "ui",
            "وجدت مؤشرات Proposal/Approval في الواجهات",
            json.dumps(hits, ensure_ascii=False),
        )

    # sessionStorage map
    writers = {}
    readers = {}

    for name, text in ui_text.items():

        for key in re.findall(
            r'sessionStorage\.setItem\(\s*["\']([^"\']+)',
            text,
        ):
            writers.setdefault(key, []).append(name)

        for key in re.findall(
            r'sessionStorage\.getItem\(\s*["\']([^"\']+)',
            text,
        ):
            readers.setdefault(key, []).append(name)

    for key in sorted(set(writers) | set(readers)):

        w = writers.get(key, [])
        r = readers.get(key, [])

        if w and r:
            severity = "PASS"
            title = f"sessionStorage flow: {key}"
            evidence = f"writers={w}; readers={r}"
        elif w:
            severity = "WARN"
            title = f"key مكتوب بلا قارئ واضح: {key}"
            evidence = f"writers={w}"
        else:
            severity = "WARN"
            title = f"key مقروء بلا كاتب واضح: {key}"
            evidence = f"readers={r}"

        add(
            "DATA-" + key,
            severity,
            "dataflow",
            title,
            evidence,
        )


def check_architecture():
    legacy = ROOT / "abqaryno_complete_upgrade.py"
    master = ROOT / "abqaryno_master.py"

    if legacy.exists():
        add(
            "ARCH-LEGACY",
            "REVIEW",
            "architecture",
            "ملف creation legacy محتمل موجود",
            rel(legacy),
            "مصدر authoritative واضح.",
            "لا تحذف قبل فحص consumers/imports.",
            legacy,
        )

    if master.exists():
        add(
            "ARCH-MASTER",
            "INFO",
            "architecture",
            "abqaryno_master.py موجود",
            rel(master),
            file=master,
        )

    if CREATION.exists():
        add(
            "ARCH-CREATION",
            "PASS",
            "architecture",
            "engine/creation.py موجود",
            rel(CREATION),
            file=CREATION,
        )


def check_traceability():
    creation = read(CREATION)

    if "traceability" in creation:
        add(
            "TRACE-001",
            "PASS",
            "traceability",
            "traceability موجود في creation engine",
            "marker موجود.",
            file=CREATION,
        )
    else:
        add(
            "TRACE-001",
            "WARN",
            "traceability",
            "لم يثبت traceability في creation engine",
            "marker غير موجود.",
            "فحص manifest الفعلي.",
            file=CREATION,
        )


def write_report():
    counts = {}

    for item in findings:
        counts[item.severity] = counts.get(item.severity, 0) + 1

    if counts.get("FAIL", 0):
        gate = "BLOCKED"
    elif counts.get("REVIEW", 0) or counts.get("WARN", 0):
        gate = "REVIEW_REQUIRED"
    else:
        gate = "AUDIT_COMPLETE"

    data = {
        "tool": "abqaryno_comprehensive_audit",
        "version": 1,
        "root": str(ROOT),
        "gate": gate,
        "counts": counts,
        "rule": [
            "inspect source before tests",
            "inspect actual API signatures",
            "inspect actual UI flow",
            "inspect server binding",
            "inspect data flow",
            "distinguish engine existence from execution",
            "distinguish flags from real approval",
        ],
        "findings": [asdict(x) for x in findings],
    }

    json_path = REPORTS / "abqaryno-comprehensive-audit.json"
    md_path = REPORTS / "abqaryno-comprehensive-audit.md"

    json_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    md = [
        "# عبقرينو — الفحص الشامل",
        "",
        f"## Gate: {gate}",
        "",
    ]

    for key in [
        "FAIL",
        "WARN",
        "REVIEW",
        "PASS",
        "INFO",
    ]:
        md.append(
            f"- {key}: {counts.get(key, 0)}"
        )

    md += [
        "",
        "## النتائج",
        "",
    ]

    order = {
        "FAIL": 0,
        "WARN": 1,
        "REVIEW": 2,
        "PASS": 3,
        "INFO": 4,
    }

    for item in sorted(
        findings,
        key=lambda x: (order.get(x.severity, 9), x.id),
    ):
        md += [
            f"### [{item.severity}] {item.id} — {item.title}",
            f"- Area: `{item.area}`",
            f"- Evidence: {item.evidence}",
        ]

        if item.file:
            location = (
                f"{item.file}:{item.line}"
                if item.line
                else item.file
            )
            md.append(f"- File: `{location}`")

        if item.expected:
            md.append(
                f"- Expected: {item.expected}"
            )

        if item.recommendation:
            md.append(
                f"- Recommendation: {item.recommendation}"
            )

        md.append("")

    md_path.write_text(
        "\n".join(md),
        encoding="utf-8",
    )

    return gate, counts, json_path, md_path


def main():
    print("=" * 72)
    print("عبقرينو — الفحص الشامل قبل كتابة الاختبارات")
    print("=" * 72)
    print(f"ROOT: {ROOT}")
    print()

    trees = check_python_sources()

    check_creation_engine(trees)
    check_server(trees)
    check_ui()
    check_architecture()
    check_traceability()

    gate, counts, json_path, md_path = write_report()

    print("=" * 72)
    print("RESULT")
    print("=" * 72)

    for key in [
        "FAIL",
        "WARN",
        "REVIEW",
        "PASS",
        "INFO",
    ]:
        print(
            f"{key:<7}: {counts.get(key, 0)}"
        )

    print()
    print(f"GATE   : {gate}")
    print()
    print(f"JSON   : {json_path}")
    print(f"REPORT : {md_path}")
    print()
    print("الفحص انتهى — لم يتم تعديل ملفات البرنامج.")


if __name__ == "__main__":
    main()
