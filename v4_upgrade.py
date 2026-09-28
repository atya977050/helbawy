#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from datetime import datetime
import ast
import hashlib
import json
import re
import subprocess
import sys

APP_NAME = "🛠️ مستودع الإصلاح V4.2"
VERSION = "V4.2"

PROJECT = Path.home() / "downloads" / "بلبل" / "helbawy-chat-extracted"
REPORT_DIR = PROJECT / ".repair-repository"

DEFAULT_PLAN = REPORT_DIR / "default-execution-plan-v4.2.json"
APPROVED_PLAN = REPORT_DIR / "approved-execution-plan-v4.2.json"
REPORT = REPORT_DIR / "v4.2-truth-intelligence-report.json"
EXECUTION_LOG = REPORT_DIR / "v4.2-execution-log.json"

IGNORE_DIRS = {
    ".git",
    ".svn",
    ".hg",
    "node_modules",
    ".next",
    ".nuxt",
    "dist",
    "build",
    "coverage",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    "env",
    ".idea",
    ".vscode",
    ".repair-repository",
    ".repair-trash",
}

SUPPORTED = {
    ".js", ".mjs", ".cjs",
    ".jsx", ".ts", ".tsx",
    ".py",
    ".json",
    ".html", ".htm",
    ".css",
}

LIFECYCLE_EVENTS = {
    "connect",
    "disconnect",
    "connect_error",
    "disconnecting",
    "newListener",
    "removeListener",
}

CLIENT_EVENT_RE = re.compile(
    r'\bsocket\s*\.\s*emit\s*\(\s*["\']([^"\']+)["\']'
)

CLIENT_LISTENER_RE = re.compile(
    r'\bsocket\s*\.\s*on\s*\(\s*["\']([^"\']+)["\']'
)

SERVER_HANDLER_RE = re.compile(
    r'\bsocket\s*\.\s*on\s*\(\s*["\']([^"\']+)["\']'
)

SERVER_EMIT_RE = re.compile(
    r'(?:socket|io)\s*\.\s*emit\s*\(\s*["\']([^"\']+)["\']'
)

SERVER_TO_RE = re.compile(
    r'io\s*\.\s*to\s*\([^)]*\)\s*\.emit\s*\(\s*["\']([^"\']+)["\']'
)

API_CLIENT_RE = re.compile(
    r'(?:fetch|axios\.(?:get|post|put|patch|delete|request))'
    r'\s*\(\s*[`"\']([^`"\']+)'
)

API_SERVER_RE = re.compile(
    r'@(?:app|bp|api)\.(?:route|get|post|put|patch|delete|options|head)'
    r'\s*\(\s*[\'"]([^\'"]+)[\'"]'
)

EXPRESS_ROUTE_RE = re.compile(
    r'\b(?:app|router)\.(?:get|post|put|patch|delete|put|options|head)'
    r'\s*\(\s*[\'"]([^\'"]+)[\'"]'
)


def now():
    return datetime.now().isoformat(timespec="seconds")


def safe_read(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return f"__READ_ERROR__: {exc}"


def rel(path):
    try:
        return str(path.relative_to(PROJECT))
    except ValueError:
        return str(path)


def line_no(text, pos):
    return text.count("\n", 0, pos) + 1


def sha(text):
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def normalize_code(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r'^\s*//.*$', '', text, flags=re.M)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def collect_files():
    files = []

    if not PROJECT.exists():
        return files

    for p in PROJECT.rglob("*"):
        if not p.is_file():
            continue

        try:
            relative_parts = p.relative_to(PROJECT).parts
        except ValueError:
            continue

        if any(part in IGNORE_DIRS for part in relative_parts):
            continue

        if p.suffix.lower() in SUPPORTED:
            files.append(p)

    return sorted(files)


def classify(path, text=None):
    r = rel(path).lower()
    name = path.name.lower()

    if path.suffix.lower() in {".html", ".htm", ".css"}:
        return "CLIENT"

    if any(x in r for x in [
        "public/",
        "frontend/",
        "client/",
        "static/",
    ]):
        return "CLIENT"

    if name in {
        "server.js",
        "server.mjs",
        "server.cjs",
        "app.js",
        "app.mjs",
        "app.cjs",
        "server.py",
    }:
        return "SERVER"

    if r.startswith("server/"):
        if path.suffix.lower() in {".js", ".mjs", ".cjs", ".py"}:
            return "SERVER"

    if text is None:
        text = safe_read(path)

    if path.suffix.lower() in {".js", ".mjs", ".cjs", ".ts", ".tsx"}:
        server_signatures = [
            "express(",
            "createServer(",
            "socket.io",
            "Server(",
            "io.on(",
            "app.listen(",
            "server.listen(",
            "require('express')",
            'require("express")',
        ]

        if any(sig in text for sig in server_signatures):
            return "SERVER"

        return "CLIENT"

    if path.suffix.lower() == ".py":
        server_signatures = [
            "from flask import",
            "import flask",
            "Flask(",
            "@app.route",
            "socketio",
            "SocketIO(",
        ]

        if any(sig in text for sig in server_signatures):
            return "SERVER"

        return "UNKNOWN"

    return "UNKNOWN"


def extract_context(text, pos, radius=220):
    start = max(0, pos - radius)
    end = min(len(text), pos + radius)
    snippet = text[start:end].strip()

    return {
        "line_start": line_no(text, start),
        "line_event": line_no(text, pos),
        "line_end": line_no(text, end),
        "snippet": snippet,
    }


def extract_block_after(text, pos):
    """
    محاولة بسيطة لاستخراج كتلة callback بعد socket.emit/on.
    لا تعتمد على parser كامل، لكنها مفيدة لإظهار السياق الحقيقي.
    """
    start = text.find("(", pos)
    if start < 0:
        return ""

    depth = 0
    quote = None
    escaped = False

    for i in range(start, min(len(text), start + 5000)):
        ch = text[i]

        if quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
            continue

        if ch in "'\"`":
            quote = ch
            continue

        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]

    return text[start:start + 1000]


def extract_emit_payload(text, pos):
    call = extract_block_after(text, pos)

    if not call:
        return {
            "raw_call": "",
            "payload_fields": [],
        }

    fields = set()

    # object literal keys
    for m in re.finditer(r'([A-Za-z_$][\w$]*)\s*:', call):
        fields.add(m.group(1))

    # payload.foo
    for m in re.finditer(r'\b(?:payload|data|message|body|offer|answer|candidate)\.([A-Za-z_$][\w$]*)', call):
        fields.add(m.group(1))

    return {
        "raw_call": call[:1500],
        "payload_fields": sorted(fields),
    }


def collect_client_socket(files):
    events = {}

    for p in files:
        if classify(p) != "CLIENT":
            continue

        if p.suffix.lower() not in {".js", ".mjs", ".cjs", ".ts", ".tsx"}:
            continue

        text = safe_read(p)

        for m in CLIENT_EVENT_RE.finditer(text):
            event = m.group(1)

            item = events.setdefault(event, {
                "event": event,
                "emits": [],
                "listeners": [],
            })

            ctx = extract_context(text, m.start())
            payload = extract_emit_payload(text, m.start())

            item["emits"].append({
                "file": rel(p),
                "line": ctx["line_event"],
                "context": ctx["snippet"],
                "payload": payload,
            })

        for m in CLIENT_LISTENER_RE.finditer(text):
            event = m.group(1)

            item = events.setdefault(event, {
                "event": event,
                "emits": [],
                "listeners": [],
            })

            ctx = extract_context(text, m.start())

            item["listeners"].append({
                "file": rel(p),
                "line": ctx["line_event"],
                "context": ctx["snippet"],
            })

    return events


def collect_server_socket(files):
    events = {}

    for p in files:
        if classify(p) != "SERVER":
            continue

        if p.suffix.lower() not in {".js", ".mjs", ".cjs", ".ts", ".tsx", ".py"}:
            continue

        text = safe_read(p)

        # JavaScript socket handlers
        if p.suffix.lower() in {".js", ".mjs", ".cjs", ".ts", ".tsx"}:
            for m in SERVER_HANDLER_RE.finditer(text):
                event = m.group(1)

                item = events.setdefault(event, {
                    "event": event,
                    "handlers": [],
                    "emits": [],
                })

                ctx = extract_context(text, m.start())
                item["handlers"].append({
                    "file": rel(p),
                    "line": ctx["line_event"],
                    "context": ctx["snippet"],
                })

            for m in SERVER_TO_RE.finditer(text):
                event = m.group(1)

                item = events.setdefault(event, {
                    "event": event,
                    "handlers": [],
                    "emits": [],
                })

                ctx = extract_context(text, m.start())
                item["emits"].append({
                    "file": rel(p),
                    "line": ctx["line_event"],
                    "context": ctx["snippet"],
                    "kind": "io.to(...).emit",
                })

            for m in SERVER_EMIT_RE.finditer(text):
                event = m.group(1)

                item = events.setdefault(event, {
                    "event": event,
                    "handlers": [],
                    "emits": [],
                })

                ctx = extract_context(text, m.start())
                item["emits"].append({
                    "file": rel(p),
                    "line": ctx["line_event"],
                    "context": ctx["snippet"],
                    "kind": "emit",
                })

        # Python Flask-SocketIO
        if p.suffix.lower() == ".py":
            decorator_re = re.compile(
                r'@socketio\.(?:on|on_event)\s*\(\s*[\'"]([^\'"]+)[\'"]'
            )

            for m in decorator_re.finditer(text):
                event = m.group(1)

                item = events.setdefault(event, {
                    "event": event,
                    "handlers": [],
                    "emits": [],
                })

                ctx = extract_context(text, m.start())

                item["handlers"].append({
                    "file": rel(p),
                    "line": ctx["line_event"],
                    "context": ctx["snippet"],
                })

            for m in re.finditer(
                r'\bsocketio\s*\.\s*emit\s*\(\s*[\'"]([^\'"]+)[\'"]',
                text
            ):
                event = m.group(1)

                item = events.setdefault(event, {
                    "event": event,
                    "handlers": [],
                    "emits": [],
                })

                ctx = extract_context(text, m.start())

                item["emits"].append({
                    "file": rel(p),
                    "line": ctx["line_event"],
                    "context": ctx["snippet"],
                    "kind": "socketio.emit",
                })

    return events


def normalize_api_path(path):
    path = path.split("?")[0]
    path = path.replace("`", "")
    path = re.sub(r'\$\{[^}]+\}', ':param', path)

    if not path.startswith("/"):
        if path.startswith("http://") or path.startswith("https://"):
            path = "/" + path.split("/", 3)[-1] if "/" in path[8:] else "/"
        else:
            path = "/" + path

    path = re.sub(r'/+', '/', path)

    return path.rstrip("/") or "/"


def collect_client_api(files):
    result = {}

    for p in files:
        if classify(p) != "CLIENT":
            continue

        if p.suffix.lower() not in {".js", ".mjs", ".cjs", ".ts", ".tsx"}:
            continue

        text = safe_read(p)

        for m in API_CLIENT_RE.finditer(text):
            raw = m.group(1)

            if not raw.startswith("/"):
                continue

            path = normalize_api_path(raw)

            item = result.setdefault(path, [])

            ctx = extract_context(text, m.start())

            item.append({
                "file": rel(p),
                "line": ctx["line_event"],
                "raw": raw,
                "context": ctx["snippet"],
            })

    return result


def collect_server_api(files):
    result = {}

    for p in files:
        if classify(p) != "SERVER":
            continue

        text = safe_read(p)

        patterns = []

        if p.suffix.lower() in {".js", ".mjs", ".cjs", ".ts", ".tsx"}:
            patterns.append(EXPRESS_ROUTE_RE)

        if p.suffix.lower() == ".py":
            patterns.append(API_SERVER_RE)

        for pattern in patterns:
            for m in pattern.finditer(text):
                path = normalize_api_path(m.group(1))

                item = result.setdefault(path, [])

                ctx = extract_context(text, m.start())

                item.append({
                    "file": rel(p),
                    "line": ctx["line_event"],
                    "context": ctx["snippet"],
                })

    return result


def architecture_summary(files):
    result = []

    for p in files:
        text = safe_read(p)
        c = classify(p, text)

        if c != "SERVER":
            continue

        if p.suffix.lower() in {".js", ".mjs", ".cjs", ".ts", ".tsx"}:
            if any(x in text for x in [
                "socket.io",
                "io.on(",
                "Server(",
                "express(",
            ]):
                result.append({
                    "file": rel(p),
                    "role": "NODE_SOCKET_BACKEND",
                    "evidence": [
                        x for x in [
                            "socket.io",
                            "io.on(",
                            "Server(",
                            "express(",
                        ] if x in text
                    ],
                })

        if p.suffix.lower() == ".py":
            if any(x in text for x in [
                "Flask(",
                "@app.route",
            ]):
                result.append({
                    "file": rel(p),
                    "role": "FLASK_HTTP_BACKEND",
                    "evidence": [
                        x for x in [
                            "Flask(",
                            "@app.route",
                        ] if x in text
                    ],
                })

    return result


def infer_socket_intent(event, client_item, server_item):
    emits = client_item.get("emits", [])
    listeners = client_item.get("listeners", [])
    handlers = server_item.get("handlers", [])
    server_emits = server_item.get("emits", [])

    fields = set()

    for e in emits:
        fields.update(e.get("payload", {}).get("payload_fields", []))

    intent = []

    if handlers:
        intent.append("يوجد معالج خادمي فعلي للحدث.")

    if server_emits:
        intent.append("يوجد إرسال خادمي مرتبط بالحدث.")

    if emits:
        intent.append("العميل يرسل هذا الحدث إلى الخادم.")

    if listeners:
        intent.append("العميل يستمع إلى هذا الحدث.")

    if fields:
        intent.append(
            "حقول payload المستدل عليها: " +
            ", ".join(sorted(fields))
        )

    if event in {"webrtc:offer", "webrtc:answer", "webrtc:ice"}:
        intent.append(
            "الوظيفة المتوقعة: تمرير إشارة WebRTC بين أطراف المكالمة، "
            "مع الحفاظ على معلومات الهدف/المرسل الموجودة في payload."
        )

    elif event == "call:join":
        intent.append(
            "الوظيفة المتوقعة: تسجيل انضمام طرف إلى مكالمة "
            "ثم إخطار الطرف/الأطراف ذات الصلة."
        )

    elif event == "call:end":
        intent.append(
            "الوظيفة المتوقعة: إنهاء المكالمة وإخطار الأطراف "
            "بالحدث المقابل الموجود في العميل."
        )

    elif event == "chat:send":
        intent.append(
            "الوظيفة المتوقعة: استقبال رسالة الدردشة "
            "ثم تخزينها/تمريرها وفق آلية الدردشة الموجودة."
        )

    elif event == "chat:history":
        intent.append(
            "الوظيفة المتوقعة: إعادة سجل الرسائل إلى العميل."
        )

    elif event == "user:join":
        intent.append(
            "الوظيفة المتوقعة: تسجيل دخول المستخدم/حضوره "
            "وتحديث حالة الحضور."
        )

    elif event in {"chat:message", "presence:update", "call:peer-joined", "call:ended"}:
        intent.append(
            "هذا الحدث يبدو كحدث صادر من الخادم يستقبله العميل؛ "
            "يجب تحديد مصدره الخادمي قبل التنفيذ."
        )

    return intent


def compare_socket_contract(client_events, server_events):
    findings = []

    all_events = sorted(
        set(client_events) |
        set(server_events)
    )

    for event in all_events:
        if event in LIFECYCLE_EVENTS:
            findings.append({
                "type": "SOCKET_EVENT",
                "event": event,
                "status": "LIFECYCLE",
                "severity": "INFO",
                "reason": "Socket.IO lifecycle event; not treated as application repair contract.",
            })
            continue

        c = client_events.get(event, {})
        s = server_events.get(event, {})

        client_emits = c.get("emits", [])
        client_listeners = c.get("listeners", [])
        server_handlers = s.get("handlers", [])
        server_emits = s.get("emits", [])

        if client_emits and server_handlers:
            status = "MATCHED"
            severity = "INFO"
        elif client_emits and not server_handlers:
            status = "MISSING_IMPLEMENTATION"
            severity = "HIGH"
        elif client_listeners and not server_emits:
            status = "MISSING_IMPLEMENTATION"
            severity = "MEDIUM"
        elif server_handlers and not client_emits and not client_listeners:
            status = "EXTRA_CANDIDATE"
            severity = "MEDIUM"
        else:
            status = "DIFFERENT_IMPLEMENTATION"
            severity = "MEDIUM"

        evidence = {
            "client_emit_sites": client_emits,
            "client_listener_sites": client_listeners,
            "server_handler_sites": server_handlers,
            "server_emit_sites": server_emits,
        }

        intent = infer_socket_intent(event, c, s)

        findings.append({
            "type": "SOCKET_EVENT",
            "event": event,
            "status": status,
            "severity": severity,
            "evidence": evidence,
            "implementation_intent": intent,
        })

    return findings


def compare_api_contract(client_api, server_api):
    findings = []

    all_paths = sorted(
        set(client_api) |
        set(server_api)
    )

    for path in all_paths:
        c = client_api.get(path, [])
        s = server_api.get(path, [])

        if c and s:
            status = "MATCHED"
            severity = "INFO"
        elif c and not s:
            status = "MISSING_IMPLEMENTATION"
            severity = "HIGH"
        else:
            status = "EXTRA_CANDIDATE"
            severity = "MEDIUM"

        intent = []

        if c:
            intent.append("يوجد استخدام فعلي للمسار من العميل.")

        if s:
            intent.append("يوجد endpoint خادمي فعلي للمسار.")

        if path == "/api/upload" and c and not s:
            intent.append(
                "العميل يستخدم /api/upload؛ يجب فحص FormData/الملف "
                "واستجابة الطلب قبل إنشاء route."
            )

        findings.append({
            "type": "API_ENDPOINT",
            "path": path,
            "status": status,
            "severity": severity,
            "client_sites": c,
            "server_sites": s,
            "implementation_intent": intent,
        })

    return findings


def dependency_candidates():
    package = PROJECT / "package.json"

    if not package.exists():
        return []

    try:
        data = json.loads(package.read_text(encoding="utf-8"))
    except Exception:
        return []

    deps = {}
    deps.update(data.get("dependencies", {}))
    deps.update(data.get("devDependencies", {}))

    source_files = collect_files()
    source_text = "\n".join(
        safe_read(p)
        for p in source_files
        if p.suffix.lower() in {
            ".js", ".mjs", ".cjs", ".jsx",
            ".ts", ".tsx", ".py"
        }
    )

    result = []

    for name, version in sorted(deps.items()):
        base = name.split("/")[-1]

        patterns = [
            rf"require\s*\(\s*['\"]{re.escape(name)}['\"]",
            rf"from\s+['\"]{re.escape(name)}['\"]",
            rf"import .*?['\"]{re.escape(name)}['\"]",
            rf"from\s+{re.escape(name)}\s+import",
            rf"import\s+{re.escape(name)}",
        ]

        used = any(
            re.search(pattern, source_text)
            for pattern in patterns
        )

        if not used and base in source_text:
            used = True

        if not used:
            result.append({
                "dependency": name,
                "declared_version": version,
                "status": "UNUSED_CANDIDATE",
                "requires_manual_confirmation": True,
            })

    return result


def build_default_plan(files):
    client_events = collect_client_socket(files)
    server_events = collect_server_socket(files)

    client_api = collect_client_api(files)
    server_api = collect_server_api(files)

    socket_findings = compare_socket_contract(
        client_events,
        server_events
    )

    api_findings = compare_api_contract(
        client_api,
        server_api
    )

    architecture = architecture_summary(files)

    plan_items = []

    for item in socket_findings:
        plan_items.append({
            "category": "SOCKET_EVENT",
            **item,
        })

    for item in api_findings:
        plan_items.append({
            "category": "API_ENDPOINT",
            **item,
        })

    for dep in dependency_candidates():
        plan_items.append({
            "category": "DEPENDENCY",
            "type": "DEPENDENCY",
            "name": dep["dependency"],
            "status": dep["status"],
            "severity": "LOW",
            "evidence": dep,
        })

    summary = {}

    for item in plan_items:
        key = item["status"]
        summary[key] = summary.get(key, 0) + 1

    return {
        "metadata": {
            "app": APP_NAME,
            "version": VERSION,
            "created_at": now(),
            "project": str(PROJECT),
            "source": "PROJECT_CONTRACT_INFERENCE_V4.2",
            "mode": "READ_ONLY_UNTIL_APPROVAL",
        },
        "architecture": architecture,
        "contract": {
            "client_socket_events": client_events,
            "server_socket_events": server_events,
            "client_api": client_api,
            "server_api": server_api,
        },
        "items": plan_items,
        "summary": summary,
        "approval": {
            "approved": False,
            "approved_at": None,
        },
    }


def save_json(path, data):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


def print_architecture(plan):
    print()
    print("=" * 72)
    print("🏗️ البنية التي استنتجها مستودع الإصلاح")
    print("=" * 72)

    architecture = plan.get("architecture", [])

    if not architecture:
        print("⚪ لم يتم تحديد خادم واضح.")
        return

    for item in architecture:
        print(
            f"🔹 {item['file']} → {item['role']}"
        )
        print(
            f"   دليل: {', '.join(item.get('evidence', []))}"
        )


def print_findings(plan):
    items = plan.get("items", [])

    print()
    print("=" * 72)
    print("🧠 خطة V4.2 المستنتجة من الواقع")
    print("=" * 72)

    if not items:
        print("⚪ لا توجد عناصر مكتشفة.")
        return

    for i, item in enumerate(items, 1):
        status = item.get("status", "?")
        severity = item.get("severity", "INFO")

        if status == "MATCHED":
            icon = "✅"
        elif status == "MISSING_IMPLEMENTATION":
            icon = "❌"
        elif status == "DIFFERENT_IMPLEMENTATION":
            icon = "⚠️"
        elif status == "EXTRA_CANDIDATE":
            icon = "🗑️"
        elif status == "LIFECYCLE":
            icon = "🔄"
        elif status == "UNUSED_CANDIDATE":
            icon = "📦"
        else:
            icon = "❓"

        label = item.get("event") or item.get("path") or item.get("name")

        print()
        print(
            f"{i}. {icon} {item.get('category')} | {label}"
        )
        print(
            f"   الحالة: {status} | الخطورة: {severity}"
        )

        if item.get("category") == "SOCKET_EVENT":
            evidence = item.get("evidence", {})

            for x in evidence.get("client_emit_sites", [])[:4]:
                print(
                    f"   ← CLIENT emit {x['file']}:{x['line']}"
                )

                payload = x.get("payload", {})
                fields = payload.get("payload_fields", [])

                if fields:
                    print(
                        f"      payload: {', '.join(fields)}"
                    )

            for x in evidence.get("client_listener_sites", [])[:4]:
                print(
                    f"   ← CLIENT listener {x['file']}:{x['line']}"
                )

            for x in evidence.get("server_handler_sites", [])[:4]:
                print(
                    f"   → SERVER handler {x['file']}:{x['line']}"
                )

            for x in evidence.get("server_emit_sites", [])[:4]:
                print(
                    f"   → SERVER emit {x['file']}:{x['line']}"
                )

        elif item.get("category") == "API_ENDPOINT":
            for x in item.get("client_sites", [])[:4]:
                print(
                    f"   ← CLIENT {x['file']}:{x['line']}"
                )

            for x in item.get("server_sites", [])[:4]:
                print(
                    f"   → SERVER {x['file']}:{x['line']}"
                )

        for intent in item.get("implementation_intent", [])[:5]:
            print(f"   🧩 {intent}")


def print_summary(plan):
    print()
    print("=" * 72)
    print("📊 ملخص V4.2")
    print("=" * 72)

    summary = plan.get("summary", {})

    order = [
        "MATCHED",
        "MISSING_IMPLEMENTATION",
        "DIFFERENT_IMPLEMENTATION",
        "EXTRA_CANDIDATE",
        "LIFECYCLE",
        "UNUSED_CANDIDATE",
    ]

    for key in order:
        if key in summary:
            print(f"   {key:<28} {summary[key]}")

    print()
    print("🔒 لم يتم تعديل أو حذف أي ملف.")


def run_tests(files):
    tests = []

    for p in files:
        suffix = p.suffix.lower()

        if suffix in {".js", ".mjs", ".cjs"}:
            try:
                r = subprocess.run(
                    ["node", "--check", str(p)],
                    capture_output=True,
                    text=True,
                    timeout=20,
                )

                tests.append({
                    "file": rel(p),
                    "command": "node --check",
                    "status": "PASS" if r.returncode == 0 else "FAIL",
                    "stderr": r.stderr[:2000],
                })
            except Exception as exc:
                tests.append({
                    "file": rel(p),
                    "command": "node --check",
                    "status": "ERROR",
                    "stderr": str(exc),
                })

        elif suffix == ".py":
            try:
                r = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(p)],
                    capture_output=True,
                    text=True,
                    timeout=20,
                )

                tests.append({
                    "file": rel(p),
                    "command": "python -m py_compile",
                    "status": "PASS" if r.returncode == 0 else "FAIL",
                    "stderr": r.stderr[:2000],
                })
            except Exception as exc:
                tests.append({
                    "file": rel(p),
                    "command": "python -m py_compile",
                    "status": "ERROR",
                    "stderr": str(exc),
                })

        elif suffix == ".json":
            try:
                json.loads(safe_read(p))

                tests.append({
                    "file": rel(p),
                    "command": "json parse",
                    "status": "PASS",
                    "stderr": "",
                })
            except Exception as exc:
                tests.append({
                    "file": rel(p),
                    "command": "json parse",
                    "status": "FAIL",
                    "stderr": str(exc),
                })

    return tests


def approve():
    if not DEFAULT_PLAN.exists():
        print("❌ لا توجد خطة V4.2 لاعتمادها.")
        print("شغّل البرنامج أولًا بدون --approve.")
        return 1

    try:
        plan = json.loads(
            DEFAULT_PLAN.read_text(
                encoding="utf-8"
            )
        )
    except Exception as exc:
        print(f"❌ تعذر قراءة الخطة: {exc}")
        return 1

    plan["approval"] = {
        "approved": True,
        "approved_at": now(),
        "mode": "FULL_REPAIR_AUTHORIZED",
        "warning": (
            "هذه الموافقة تمنح محرك الإصلاح صلاحية تنفيذ "
            "التغييرات المحددة في الخطة فقط."
        ),
    }

    save_json(APPROVED_PLAN, plan)

    log = {
        "timestamp": now(),
        "action": "APPROVE_PLAN",
        "plan": str(DEFAULT_PLAN),
        "approved_plan": str(APPROVED_PLAN),
        "authorized": True,
    }

    save_json(EXECUTION_LOG, log)

    print()
    print("=" * 72)
    print("🔐 تم اعتماد الخطة التنفيذية V4.2")
    print("=" * 72)
    print(f"📄 الخطة: {APPROVED_PLAN}")
    print()
    print("⚠️ الاعتماد وحده لا يعني أن V4.2 سيخترع كودًا غير موثوق.")
    print("🧠 التنفيذ يجب أن يلتزم بالأدلة والعقود التي استنتجتها الخطة.")
    print()
    print("➡️ الخطوة التالية: مرحلة التنفيذ الفعلي للإصلاح.")
    return 0


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    if "--approve" in sys.argv:
        return approve()

    print()
    print(APP_NAME)
    print("🧠 Plan Intelligence + Truth Trace")
    print(f"📁 المشروع: {PROJECT}")
    print("🔒 المرحلة الحالية: تحليل فقط")
    print("🛡️ لا تعديل ولا حذف قبل الاعتماد")

    if not PROJECT.exists():
        print("❌ مجلد المشروع غير موجود.")
        return 1

    files = collect_files()

    print(f"📄 الملفات البرمجية المدعومة: {len(files)}")

    plan = build_default_plan(files)

    save_json(DEFAULT_PLAN, plan)

    print_architecture(plan)
    print_findings(plan)

    tests = run_tests(files)

    failed = [
        t for t in tests
        if t["status"] != "PASS"
    ]

    report = {
        "metadata": {
            "app": APP_NAME,
            "version": VERSION,
            "generated_at": now(),
            "project": str(PROJECT),
            "mode": "READ_ONLY",
        },
        "files_count": len(files),
        "plan": plan,
        "tests": tests,
        "test_summary": {
            "total": len(tests),
            "failed": len(failed),
        },
        "authorization": {
            "approved": False,
            "full_repair_enabled": False,
        },
    }

    save_json(REPORT, report)

    print()
    print("=" * 72)
    print("🧪 الاختبارات")
    print("=" * 72)

    for test in tests:
        icon = "✅" if test["status"] == "PASS" else "❌"

        print(
            f"{icon} {test['file']} → "
            f"{test['command']} → {test['status']}"
        )

    print_summary(plan)

    print()
    print("=" * 72)
    print("📁 التقارير")
    print("=" * 72)
    print(f"📋 الخطة الافتراضية : {DEFAULT_PLAN}")
    print(f"📊 التقرير          : {REPORT}")

    print()
    print("👁️ راجع الخطة أولًا.")
    print("🔐 عند اعتمادها صراحة:")
    print("   python v4_upgrade.py --approve")
    print()
    print("🚫 لم يتم تعديل أو حذف أي ملف من بلبل.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
