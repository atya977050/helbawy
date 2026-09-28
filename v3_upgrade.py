#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import difflib
import hashlib
import json
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

APP_NAME = "🛠️ مستودع الإصلاح V3"
VERSION = "V3.0"

PROJECT = Path.home() / "downloads" / "بلبل" / "helbawy-chat-extracted"
REPORT_DIR = PROJECT / ".repair-repository"

IGNORE_DIRS = {
    ".git", ".svn", ".hg",
    "node_modules", ".next", ".nuxt",
    "dist", "build", "coverage",
    "__pycache__", ".pytest_cache",
    ".venv", "venv", "env",
    ".idea", ".vscode",
    ".repair-trash",
}

SUPPORTED_EXTENSIONS = {
    ".js", ".mjs", ".cjs",
    ".jsx", ".ts", ".tsx",
    ".py",
    ".json",
    ".html", ".htm",
    ".css",
}

TEXT_EXTENSIONS = SUPPORTED_EXTENSIONS


# ============================================================
# BASIC
# ============================================================

def safe_read(path):
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return ""


def rel(path):
    try:
        return str(path.relative_to(PROJECT))
    except ValueError:
        return str(path)


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize(text):
    if text is None:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def line_no(text, pos):
    return text.count("\n", 0, pos) + 1


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ============================================================
# PROJECT DISCOVERY
# ============================================================

def collect_files():
    result = []

    if not PROJECT.exists():
        return result

    for path in PROJECT.rglob("*"):
        if not path.is_file():
            continue

        try:
            relative_parts = path.relative_to(PROJECT).parts
        except ValueError:
            continue

        if any(part in IGNORE_DIRS for part in relative_parts):
            continue

        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            result.append(path)

    return sorted(result)


def classify_file(path):
    name = path.name.lower()
    p = rel(path).lower()

    if p.startswith(".repair-repository/"):
        return "REPAIR_DATA"

    if path.suffix.lower() in {".html", ".htm", ".css"}:
        return "CLIENT"

    server_patterns = [
        r"\bexpress\s*\(",
        r"\bapp\s*=\s*express",
        r"\bio\.on\s*\(\s*['\"]connection",
        r"\bsocket\.on\s*\(\s*['\"]connection",
        r"\bnew\s+Server\s*\(",
        r"\bFlask\s*\(",
        r"@app\.route",
        r"@socketio\.(on|event)",
        r"\bsocketio\.on_event\s*\(",
    ]

    client_patterns = [
        r"\bdocument\.",
        r"\bwindow\.",
        r"\bfetch\s*\(",
        r"\bsocket\s*\.\s*emit\s*\(",
        r"\bsocket\s*\.\s*on\s*\(",
        r"\bio\s*\.\s*emit\s*\(",
        r"\baxios\.",
    ]

    try:
        text = safe_read(path)
    except Exception:
        text = ""

    if any(re.search(x, text) for x in server_patterns):
        return "SERVER"

    if any(re.search(x, text) for x in client_patterns):
        return "CLIENT"

    if name.startswith(("test_", "test.", "tests")) or \
       name.endswith((".test.js", ".spec.js", ".test.ts", ".spec.ts")):
        return "TEST"

    if name in {
        "package.json",
        "package-lock.json",
        "requirements.txt",
        "pyproject.toml",
    }:
        return "CONFIG"

    if path.suffix.lower() == ".json":
        return "DATA"

    return "UNKNOWN"


# ============================================================
# EXECUTION PLAN
# ============================================================

PLAN_CANDIDATES = [
    PROJECT / "execution-plan.json",
    REPORT_DIR / "execution-plan.json",
]


def read_execution_plan():
    for candidate in PLAN_CANDIDATES:
        if candidate.exists():
            try:
                return json.loads(
                    candidate.read_text(encoding="utf-8")
                ), candidate
            except Exception as exc:
                return {
                    "_error": f"Invalid execution plan: {exc}"
                }, candidate

    return None, None


def plan_items(plan):
    if not plan:
        return []

    items = []

    files = plan.get("files", [])

    if isinstance(files, dict):
        for path, value in files.items():
            if isinstance(value, str):
                items.append({
                    "path": path,
                    "code": value,
                    "anchor": None,
                    "description": "",
                    "kind": "file",
                })

            elif isinstance(value, dict):
                item = dict(value)
                item["path"] = path
                items.append(item)

    elif isinstance(files, list):
        for entry in files:
            if not isinstance(entry, dict):
                continue

            path = entry.get("path", "")

            blocks = entry.get("blocks")

            if isinstance(blocks, list):
                for block in blocks:
                    if not isinstance(block, dict):
                        continue

                    item = dict(block)
                    item["path"] = path
                    items.append(item)
            else:
                items.append(dict(entry))

    # Also support direct "items"
    direct = plan.get("items", [])
    if isinstance(direct, list):
        for entry in direct:
            if isinstance(entry, dict):
                items.append(dict(entry))

    return items


def find_anchor(text, anchor):
    if not anchor:
        return []

    try:
        pattern = re.compile(anchor, re.MULTILINE)
        return [
            line_no(text, m.start())
            for m in pattern.finditer(text)
        ]
    except re.error:
        return [
            line_no(text, m.start())
            for m in re.finditer(
                re.escape(anchor),
                text
            )
        ]


def compare_plan(project_files, plan):
    items = plan_items(plan)

    findings = []

    for item in items:
        path_text = str(item.get("path", "")).strip()
        reference = item.get("code", "")
        anchor = item.get("anchor")
        kind = item.get("kind", "code")
        description = item.get("description", "")

        if not path_text:
            findings.append({
                "status": "INVALID_PATH",
                "path": path_text,
                "kind": kind,
                "description": description,
            })
            continue

        actual_path = PROJECT / path_text

        if not actual_path.exists():
            findings.append({
                "status": "MISSING",
                "path": path_text,
                "kind": kind,
                "description": description,
                "reference_code": reference,
                "anchor": anchor,
                "message": "الملف المطلوب غير موجود.",
            })
            continue

        actual = safe_read(actual_path)

        if not reference:
            findings.append({
                "status": "EMPTY_REFERENCE",
                "path": path_text,
                "kind": kind,
                "description": description,
                "anchor": anchor,
                "message": "الخطة لا تحتوي كودًا مرجعيًا لهذا العنصر.",
            })
            continue

        nref = normalize(reference)
        nactual = normalize(actual)

        if nref == nactual or nref in nactual:
            status = "MATCHED"
            actual_lines = find_anchor(actual, anchor)
            if not actual_lines:
                actual_lines = [
                    i + 1
                    for i, line in enumerate(actual.splitlines())
                    if normalize(line) and
                    normalize(line) in nref
                ][:5]

            findings.append({
                "status": status,
                "path": path_text,
                "kind": kind,
                "description": description,
                "reference_code": reference,
                "actual_code": actual,
                "actual_lines": actual_lines,
                "anchor": anchor,
                "message": "التنفيذ مطابق للمرجع.",
            })
            continue

        anchor_lines = find_anchor(actual, anchor)

        if anchor_lines:
            status = "DIFFERENT_IMPLEMENTATION"
            message = "المرجع موجود له موضع/مرساة في المشروع لكن الكود مختلف."
        else:
            status = "MISSING_IMPLEMENTATION"
            message = "الملف موجود لكن التنفيذ المرجعي غير موجود."

        diff = list(
            difflib.unified_diff(
                reference.splitlines(),
                actual.splitlines(),
                fromfile=f"REFERENCE:{path_text}",
                tofile=f"ACTUAL:{path_text}",
                lineterm="",
            )
        )

        findings.append({
            "status": status,
            "path": path_text,
            "kind": kind,
            "description": description,
            "reference_code": reference,
            "actual_code": actual,
            "actual_lines": anchor_lines,
            "anchor": anchor,
            "diff": diff[:1000],
            "message": message,
        })

    return findings


# ============================================================
# EXTRA FILES
# ============================================================

def planned_paths(plan):
    result = set()

    for item in plan_items(plan):
        path = str(item.get("path", "")).strip()
        if path:
            result.add(path.replace("\\", "/"))

    return result


def detect_extra_files(project_files, plan):
    planned = planned_paths(plan)
    findings = []

    if not plan:
        return findings

    for path in project_files:
        rp = rel(path).replace("\\", "/")

        if rp in planned:
            continue

        role = classify_file(path)

        if role == "TEST":
            status = "TEST_ARTIFACT"
            message = "ملف يبدو كملف اختبار وليس ضمن الخطة."
        elif path.name.lower() in {
            "debug.js",
            "debug.py",
            "temp.js",
            "temp.py",
            "old.js",
            "old.py",
        }:
            status = "LEGACY"
            message = "ملف يحمل مؤشرات قوية على كونه بقايا/نسخة قديمة."
        else:
            status = "EXTRA"
            message = "الملف موجود في المشروع وغير موجود في الخطة المرجعية."

        findings.append({
            "status": status,
            "path": rp,
            "role": role,
            "message": message,
            "authorized_for_delete": False,
        })

    return findings


# ============================================================
# DUPLICATES
# ============================================================

def normalize_for_duplicate(text):
    text = re.sub(r"//.*", "", text)
    text = re.sub(r"#.*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return normalize(text)


def detect_duplicates(project_files):
    fingerprints = defaultdict(list)

    for path in project_files:
        text = safe_read(path)
        normalized = normalize_for_duplicate(text)

        if len(normalized) < 80:
            continue

        fingerprint = sha256_text(normalized)
        fingerprints[fingerprint].append(path)

    findings = []

    for fingerprint, paths in fingerprints.items():
        if len(paths) < 2:
            continue

        paths = sorted(paths, key=lambda p: len(rel(p)))

        canonical = paths[0]

        for duplicate in paths[1:]:
            findings.append({
                "status": "DUPLICATE",
                "canonical": rel(canonical),
                "duplicate": rel(duplicate),
                "similarity": 1.0,
                "fingerprint": fingerprint,
                "message": "تطابق نصي كامل بعد إزالة التعليقات والمسافات.",
                "authorized_for_delete": False,
            })

    return findings


# ============================================================
# UNUSED DEPENDENCIES
# ============================================================

def detect_unused_dependencies():
    findings = []

    package = PROJECT / "package.json"

    if not package.exists():
        return findings

    try:
        data = json.loads(
            package.read_text(encoding="utf-8")
        )
    except Exception:
        return findings

    dependencies = {}
    dependencies.update(data.get("dependencies", {}))
    dependencies.update(data.get("devDependencies", {}))

    files = [
        p for p in collect_files()
        if p.suffix.lower() in {
            ".js", ".mjs", ".cjs",
            ".jsx", ".ts", ".tsx",
        }
    ]

    combined = "\n".join(
        safe_read(p) for p in files
    )

    for dep in sorted(dependencies):
        name = dep

        # Handle scoped packages reasonably.
        if name.startswith("@"):
            token = name
        else:
            token = name.split("-")[0]

        patterns = [
            rf"require\s*\(\s*['\"]{re.escape(name)}",
            rf"from\s+['\"]{re.escape(name)}",
            rf"import\s+.*['\"]{re.escape(name)}",
        ]

        used = any(
            re.search(pattern, combined)
            for pattern in patterns
        )

        if not used:
            findings.append({
                "status": "UNUSED_DEPENDENCY",
                "package": name,
                "message": "لم يجد المحرك استخدامًا واضحًا للاعتماد.",
                "authorized_for_delete": False,
            })

    return findings


# ============================================================
# SOURCE QUALITY
# ============================================================

def detect_artifacts(project_files):
    findings = []

    artifact_patterns = [
        r"(^|/)(backup|backups|old|temp|tmp|debug|test|tests)(/|$)",
        r"\.(bak|backup|old|tmp)$",
    ]

    for path in project_files:
        rp = rel(path)

        if any(re.search(p, rp, re.I) for p in artifact_patterns):
            findings.append({
                "status": "ARTIFACT",
                "path": rp,
                "message": "مسار/اسم الملف يحتوي مؤشرًا على كونه artifact.",
                "authorized_for_delete": False,
            })

    return findings


# ============================================================
# SYNTAX TESTS
# ============================================================

def syntax_tests(project_files):
    tests = []

    for path in project_files:
        suffix = path.suffix.lower()

        if suffix in {".js", ".mjs", ".cjs"}:
            result = subprocess.run(
                ["node", "--check", str(path)],
                capture_output=True,
                text=True,
            )

            tests.append({
                "file": rel(path),
                "test": "node --check",
                "status": "PASS" if result.returncode == 0 else "FAIL",
                "stderr": result.stderr[:2000],
            })

        elif suffix == ".py":
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(path)],
                capture_output=True,
                text=True,
            )

            tests.append({
                "file": rel(path),
                "test": "python -m py_compile",
                "status": "PASS" if result.returncode == 0 else "FAIL",
                "stderr": result.stderr[:2000],
            })

        elif suffix == ".json":
            try:
                json.loads(
                    path.read_text(encoding="utf-8")
                )
                tests.append({
                    "file": rel(path),
                    "test": "JSON parse",
                    "status": "PASS",
                    "stderr": "",
                })
            except Exception as exc:
                tests.append({
                    "file": rel(path),
                    "test": "JSON parse",
                    "status": "FAIL",
                    "stderr": str(exc),
                })

    return tests


# ============================================================
# AUTHORIZED CLEANUP
# ============================================================

def is_delete_authorized(item):
    """
    الحذف لا يعتمد على الاسم وحده.
    يجب أن يكون العنصر:
      - خارج الخطة
      - أو duplicate واضح
    """
    status = item.get("status")

    if status in {
        "EXTRA",
        "TEST_ARTIFACT",
        "LEGACY",
        "ARTIFACT",
    }:
        return bool(item.get("delete_authorized", False))

    if status == "DUPLICATE":
        return bool(item.get("delete_authorized", False))

    return False


def apply_cleanup(findings, authorized=False):
    results = []

    if not authorized:
        return results

    trash = REPORT_DIR / "repair-trash"
    trash.mkdir(parents=True, exist_ok=True)

    for item in findings:
        if not item.get("delete_authorized"):
            continue

        target_text = item.get("duplicate") or item.get("path")

        if not target_text:
            continue

        target = PROJECT / target_text

        if not target.exists() or not target.is_file():
            continue

        timestamp = int(time.time())
        destination = trash / f"{timestamp}_{target.name}"

        try:
            target.rename(destination)

            results.append({
                "action": "QUARANTINE",
                "source": target_text,
                "destination": rel(destination),
                "status": "APPLIED",
            })
        except Exception as exc:
            results.append({
                "action": "QUARANTINE",
                "source": target_text,
                "status": "FAILED",
                "error": str(exc),
            })

    return results


# ============================================================
# REPAIR RECOMMENDATIONS
# ============================================================

def build_repair_actions(plan_findings):
    actions = []

    for item in plan_findings:
        status = item.get("status")

        if status == "MISSING":
            actions.append({
                "action": "CREATE",
                "path": item.get("path"),
                "reason": "الملف موجود في الخطة وغير موجود في المشروع.",
                "reference_code": item.get("reference_code", ""),
                "authorized": False,
            })

        elif status in {
            "MISSING_IMPLEMENTATION",
            "DIFFERENT_IMPLEMENTATION",
        }:
            actions.append({
                "action": "REPAIR",
                "path": item.get("path"),
                "reason": item.get("message"),
                "reference_code": item.get("reference_code", ""),
                "actual_lines": item.get("actual_lines", []),
                "authorized": False,
            })

    return actions


# ============================================================
# PRINT
# ============================================================

def print_section(title):
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(title)
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


def print_report(
    plan_path,
    plan_findings,
    extra_findings,
    duplicate_findings,
    dependency_findings,
    artifact_findings,
    tests,
):
    print_section("📋 مقارنة الخطة التنفيذية")

    if not plan_path:
        print("⚪ لا توجد خطة تنفيذية مرجعية.")
        print("📌 ضع execution-plan.json داخل بلبل لبدء المطابقة.")
    else:
        print(f"📋 الخطة: {rel(plan_path)}")

        for item in plan_findings:
            icon = {
                "MATCHED": "✅",
                "DIFFERENT_IMPLEMENTATION": "⚠️",
                "MISSING_IMPLEMENTATION": "❌",
                "MISSING": "❌",
                "EMPTY_REFERENCE": "⚪",
                "INVALID_PATH": "⛔",
            }.get(item["status"], "•")

            print(
                f"{icon} {item['status']:26} "
                f"{item.get('path', '')}"
            )

            if item.get("actual_lines"):
                print(
                    f"   📍 الأسطر الفعلية: "
                    f"{item['actual_lines']}"
                )

    print_section("🧹 العناصر الزائدة")

    for item in extra_findings:
        print(
            f"⚠️ {item['status']:18} "
            f"{item.get('path', '')}"
        )
        print(
            f"   {item.get('message', '')}"
        )

    if not extra_findings:
        print("✅ لا توجد عناصر زائدة مثبتة.")

    print_section("♻️ التكرار")

    for item in duplicate_findings:
        print(
            f"♻️ DUPLICATE: "
            f"{item['duplicate']}"
        )
        print(
            f"   ↳ المرجع: {item['canonical']}"
        )
        print(
            f"   ↳ التطابق: "
            f"{item['similarity'] * 100:.0f}%"
        )

    if not duplicate_findings:
        print("✅ لم يثبت وجود ملفات مكررة بالكامل.")

    print_section("📦 الاعتمادات غير المستخدمة")

    for item in dependency_findings:
        print(
            f"⚠️ {item['package']}"
        )

    if not dependency_findings:
        print("✅ لم يثبت وجود اعتماد غير مستخدم.")

    print_section("🧪 الاختبارات")

    failed = 0

    for test in tests:
        icon = "✅" if test["status"] == "PASS" else "❌"

        if test["status"] != "PASS":
            failed += 1

        print(
            f"{icon} {test['file']} → "
            f"{test['test']} → "
            f"{test['status']}"
        )

    print_section("📊 النتيجة")

    matched = sum(
        1 for x in plan_findings
        if x["status"] == "MATCHED"
    )

    different = sum(
        1 for x in plan_findings
        if x["status"] == "DIFFERENT_IMPLEMENTATION"
    )

    missing = sum(
        1 for x in plan_findings
        if x["status"] in {
            "MISSING",
            "MISSING_IMPLEMENTATION",
        }
    )

    print(f"📋 عناصر الخطة       : {len(plan_findings)}")
    print(f"✅ مطابق             : {matched}")
    print(f"⚠️ مختلف             : {different}")
    print(f"❌ ناقص              : {missing}")
    print(f"🗑️ زائد              : {len(extra_findings)}")
    print(f"♻️ مكرر              : {len(duplicate_findings)}")
    print(f"📦 اعتماد غير مستخدم : {len(dependency_findings)}")
    print(f"🧪 اختبارات فاشلة    : {failed}")


# ============================================================
# MAIN
# ============================================================

def main():
    started = time.time()

    print("🛠️ مستودع الإصلاح V3.0")
    print("🧠 Execution Plan + Truth + Clean Engine")
    print(f"📁 المشروع: {PROJECT}")
    print("🔒 الوضع الافتراضي: تشخيص فقط")
    print("🛡️ لا حذف ولا تعديل بدون صلاحية صريحة")

    if not PROJECT.exists():
        print("❌ المشروع غير موجود.")
        raise SystemExit(1)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    files = collect_files()

    print(f"📄 الملفات المفحوصة: {len(files)}")

    print_section("🧭 تصنيف الملفات")

    classifications = {}

    for path in files:
        role = classify_file(path)
        classifications[rel(path)] = role
        print(f"{role:14} {rel(path)}")

    plan, plan_path = read_execution_plan()

    if isinstance(plan, dict) and "_error" in plan:
        print_section("❌ خطأ في الخطة التنفيذية")
        print(plan["_error"])
        return

    plan_findings = compare_plan(files, plan)
    extra_findings = detect_extra_files(files, plan)
    duplicate_findings = detect_duplicates(files)
    dependency_findings = detect_unused_dependencies()
    artifact_findings = detect_artifacts(files)
    tests = syntax_tests(files)

    repair_actions = build_repair_actions(plan_findings)

    all_findings = (
        plan_findings
        + extra_findings
        + duplicate_findings
        + dependency_findings
        + artifact_findings
    )

    report = {
        "app": APP_NAME,
        "version": VERSION,
        "project": str(PROJECT),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "mode": "diagnostic-only",
        "plan": {
            "path": rel(plan_path) if plan_path else None,
            "exists": bool(plan_path),
            "items": len(plan_items(plan)),
        },
        "files": [
            {
                "path": rel(path),
                "role": classify_file(path),
            }
            for path in files
        ],
        "plan_comparison": plan_findings,
        "extra_files": extra_findings,
        "duplicates": duplicate_findings,
        "unused_dependencies": dependency_findings,
        "artifacts": artifact_findings,
        "repair_actions": repair_actions,
        "tests": tests,
        "cleanup": [],
        "elapsed_seconds": round(
            time.time() - started,
            3,
        ),
    }

    report_path = REPORT_DIR / "v3-truth-clean-report.json"

    write_json(report_path, report)

    print_report(
        plan_path,
        plan_findings,
        extra_findings,
        duplicate_findings,
        dependency_findings,
        artifact_findings,
        tests,
    )

    print_section("📄 التقرير")

    print(report_path)

    print()
    print("🎯 V3 أنهى التشخيص.")
    print("🔒 لم يتم تعديل أو حذف أي ملف من بلبل.")


if __name__ == "__main__":
    main()
