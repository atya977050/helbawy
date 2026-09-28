#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🛠️ مستودع الإصلاح V2.5
Truth-Trace Diagnostic Engine

الهدف:
- تتبع API من العميل إلى الخادم.
- تتبع Socket.IO من emit إلى listener.
- تتبع ردود الخادم إلى العميل.
- عدم اعتبار اختلاف الأسماء وحده خطأ مؤكدًا.
- إعطاء حكم:
    ✅ مسار مكتمل
    ⚠️ يحتاج تحققًا يدويًا
    🔴 خلل مرجح
- عدم تعديل ملفات المشروع المستهدف تلقائيًا.
"""

from pathlib import Path
import ast
import json
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request

APP_NAME = "🛠️ مستودع الإصلاح"
VERSION = "V2.5"

ROOT = Path.home() / "downloads" / "بلبل" / "helbawy-chat-extracted"
REPORT_DIR = ROOT / ".repair-repository"

IGNORE_DIRS = {
    ".git", ".svn", ".hg",
    "node_modules",
    ".next", ".nuxt",
    "dist", "build", "coverage",
    "__pycache__", ".pytest_cache",
    ".venv", "venv", "env",
    ".idea", ".vscode",
}

CLIENT_EXTS = {".html", ".htm", ".css"}
CODE_EXTS = {
    ".js", ".mjs", ".cjs", ".jsx",
    ".ts", ".tsx",
    ".py",
    ".json",
    ".html", ".htm", ".css",
}


def safe_read(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def rel(path):
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)


def classify_file(path):
    """
    تصنيف أدق من V2.1:
    الملفات الثنائية/الصور/DB ليست CLIENT أو SERVER.
    """

    name = path.name.lower()
    suffix = path.suffix.lower()
    rp = str(path.relative_to(ROOT)).replace("\\", "/").lower()

    # ملفات تقارير مستودع الإصلاح ليست جزءًا من كود المشروع
    if ".repair-repository" in path.parts:
        return "DATA"

    if suffix not in CODE_EXTS:
        return "DATA"

    if (
        name in {
            "server.js", "server.mjs", "server.cjs",
            "app.py", "server.py", "main.py",
            "backend.py"
        }
        or rp.startswith("server/")
        or "/server/" in rp
        or rp.startswith("backend/")
        or "/backend/" in rp
        or rp.startswith("api/")
        or "/api/" in rp
    ):
        return "SERVER"

    if (
        rp.startswith("public/")
        or rp.startswith("frontend/")
        or rp.startswith("client/")
        or rp.startswith("static/")
        or suffix in CLIENT_EXTS
    ):
        return "CLIENT"

    text = safe_read(path)

    server_signatures = [
        r"\bexpress\s*\(",
        r"\bapp\.(get|post|put|patch|delete)\s*\(",
        r"\bserver\.listen\s*\(",
        r"\bhttp\.createServer\s*\(",
        r"\bio\.on\s*\(\s*['\"]connection",
        r"\bsocket\.on\s*\(\s*['\"]connection",
        r"\bnew\s+Server\s*\(",
        r"\bFlask\s*\(",
        r"@app\.route",
        r"@socketio\.(on|event)",
        r"\bsocketio\.on_event\s*\(",
    ]

    for sig in server_signatures:
        if re.search(sig, text):
            return "SERVER"

    if suffix in {".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx"}:
        client_signatures = [
            r"\bdocument\.",
            r"\bwindow\.",
            r"\bfetch\s*\(",
            r"\bsocket\.emit\s*\(",
            r"\bsocket\.on\s*\(",
            r"\baxios\.",
        ]
        for sig in client_signatures:
            if re.search(sig, text):
                return "CLIENT"

    return "UNKNOWN"


def collect_files():
    files = []

    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue

        if any(part in IGNORE_DIRS for part in p.parts):
            continue

        if p.suffix.lower() in CODE_EXTS:
            files.append(p)

    return sorted(files)


def line_no(text, position):
    return text.count("\n", 0, position) + 1


def add_event(mapping, event, path, line, kind):
    if not event:
        return

    mapping.setdefault(event, []).append({
        "file": rel(path),
        "line": line,
        "kind": kind,
    })


def extract_js_block(text, start_pos):
    """
    استخراج جسم JavaScript block بعد موضع محدد.
    ليست parser كاملة، لكنها تتعامل مع الأقواس والاقتباسات الأساسية.
    """
    brace = text.find("{", start_pos)

    if brace == -1:
        return ""

    depth = 0
    quote = None
    escape = False

    for i in range(brace, len(text)):
        ch = text[i]

        if quote:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
            continue

        if ch in "\"'`":
            quote = ch
            continue

        if ch == "{":
            depth += 1

        elif ch == "}":
            depth -= 1

            if depth == 0:
                return text[brace:i + 1]

    return text[brace:]


def collect_socket(project_files):
    """
    V2.4 Socket Truth Graph.

    يجمع:
      CLIENT emit
      CLIENT listener
      SERVER listener
      SERVER emit
      handler body
    """

    client_emit = {}
    client_on = {}
    server_on = {}
    server_emit = {}

    server_handlers = []
    client_handlers = []

    def add_handler(collection, event, path, line, kind, body):
        collection.append({
            "event": event,
            "file": rel(path),
            "line": line,
            "kind": kind,
            "body": body[:20000],
        })

    for path in project_files:

        role = classify_file(path)

        if role not in {"CLIENT", "SERVER"}:
            continue

        text = safe_read(path)

        # ====================================================
        # JavaScript / TypeScript
        # ====================================================

        # socket.emit / io.emit
        for m in re.finditer(
            r"\b(?:socket|io)\s*\.\s*emit\s*\(\s*['\"]([^'\"]+)['\"]",
            text
        ):
            event = m.group(1)
            line = line_no(text, m.start())

            if role == "CLIENT":
                add_event(
                    client_emit,
                    event,
                    path,
                    line,
                    "client emit"
                )
            else:
                add_event(
                    server_emit,
                    event,
                    path,
                    line,
                    "server emit"
                )

        # socket.on / io.on
        for m in re.finditer(
            r"\b(?:socket|io)\s*\.\s*on\s*\(\s*['\"]([^'\"]+)['\"]",
            text
        ):
            event = m.group(1)
            line = line_no(text, m.start())

            body = extract_js_block(text, m.end())

            if role == "CLIENT":

                add_event(
                    client_on,
                    event,
                    path,
                    line,
                    "client listener"
                )

                client_handlers.append({
                    "event": event,
                    "file": rel(path),
                    "line": line,
                    "kind": "javascript client listener",
                    "body": body[:20000],
                })

            else:

                add_event(
                    server_on,
                    event,
                    path,
                    line,
                    "server listener"
                )

                server_handlers.append({
                    "event": event,
                    "file": rel(path),
                    "line": line,
                    "kind": "javascript server listener",
                    "body": body[:20000],
                })

        # ====================================================
        # Python Flask-SocketIO
        # ====================================================

        for m in re.finditer(
            r"@socketio\.on\s*\(\s*['\"]([^'\"]+)['\"]",
            text
        ):
            event = m.group(1)
            line = line_no(text, m.start())

            body_start = m.end()

            next_def = re.search(
                r"\n\s*(?:async\s+)?def\s+",
                text[body_start:]
            )

            if next_def:
                body = text[
                    body_start:
                    body_start + next_def.start()
                ]
            else:
                body = text[body_start:]

            add_event(
                server_on,
                event,
                path,
                line,
                "python socket listener"
            )

            server_handlers.append({
                "event": event,
                "file": rel(path),
                "line": line,
                "kind": "python socket listener",
                "body": body[:20000],
            })

        # socketio.on_event(...)
        for m in re.finditer(
            r"socketio\.on_event\s*\(\s*['\"]([^'\"]+)['\"]",
            text
        ):
            event = m.group(1)
            line = line_no(text, m.start())

            add_event(
                server_on,
                event,
                path,
                line,
                "python socket listener"
            )

            server_handlers.append({
                "event": event,
                "file": rel(path),
                "line": line,
                "kind": "python socket listener",
                "body": "",
            })

        # Python server emit
        for m in re.finditer(
            r"socketio\.emit\s*\(\s*['\"]([^'\"]+)['\"]",
            text
        ):
            event = m.group(1)
            line = line_no(text, m.start())

            add_event(
                server_emit,
                event,
                path,
                line,
                "python socket emit"
            )

    return {
        "client_emit": client_emit,
        "client_on": client_on,
        "server_on": server_on,
        "server_emit": server_emit,
        "server_handlers": server_handlers,
        "client_handlers": client_handlers,
    }

def normalize_api_path(path):
    if not path:
        return None

    path = path.strip()
    path = path.replace("\\", "/")

    path = re.sub(r"\$\{[^}]+\}", "{param}", path)
    path = re.sub(r":[A-Za-z_][A-Za-z0-9_-]*", "{param}", path)

    if not path.startswith("/"):
        return None

    path = re.sub(r"/+", "/", path)

    if len(path) > 1:
        path = path.rstrip("/")

    return path


def collect_api(project_files):
    """
    استخراج API الحقيقي حسب دور الملف:

    CLIENT:
        fetch(...)
        axios.get/post/put/patch/delete(...)

    SERVER:
        Express app/router routes
        Flask @app.route

    مهم:
    لا يجوز اعتبار fetch داخل server/app.py
    API خاصًا بالعميل.
    """

    client = {}
    server = {}

    for path in project_files:
        role = classify_file(path)

        if role not in {"CLIENT", "SERVER"}:
            continue

        text = safe_read(path)

        # ========================================================
        # CLIENT API
        # ========================================================
        if role == "CLIENT":

            # fetch("...")
            for m in re.finditer(
                r'\bfetch\s*\(\s*[`\'"]([^`\'"]+)[`\'"]',
                text
            ):
                raw = m.group(1)

                parsed = urllib.parse.urlparse(raw)

                # تجاهل الروابط الخارجية
                if parsed.scheme or raw.startswith("//"):
                    continue

                api = normalize_api_path(
                    parsed.path or raw.split("?")[0]
                )

                if api and api.startswith("/api"):
                    client.setdefault(api, []).append({
                        "file": rel(path),
                        "line": line_no(text, m.start()),
                        "kind": "fetch",
                    })

            # axios.get/post/put/patch/delete(...)
            for m in re.finditer(
                r'\baxios\s*\.\s*'
                r'(?:get|post|put|patch|delete)'
                r'\s*\(\s*[`\'"]([^`\'"]+)[`\'"]',
                text
            ):
                api = normalize_api_path(m.group(1))

                if api and api.startswith("/api"):
                    client.setdefault(api, []).append({
                        "file": rel(path),
                        "line": line_no(text, m.start()),
                        "kind": "axios",
                    })

        # ========================================================
        # SERVER API
        # ========================================================
        elif role == "SERVER":

            # Express:
            # app.get("/api/x", ...)
            # app.post("/api/x", ...)
            # router.get("/api/x", ...)
            for m in re.finditer(
                r'\b(?:app|router)\s*\.\s*'
                r'(?:get|post|put|patch|delete)'
                r'\s*\(\s*[\'"]([^\'"]+)[\'"]',
                text
            ):
                api = normalize_api_path(m.group(1))

                if api and api.startswith("/api"):
                    server.setdefault(api, []).append({
                        "file": rel(path),
                        "line": line_no(text, m.start()),
                        "kind": "express route",
                    })

            # Flask:
            # @app.route("/api/x")
            for m in re.finditer(
                r'@app\.route\s*\(\s*[\'"]([^\'"]+)[\'"]',
                text
            ):
                api = normalize_api_path(m.group(1))

                if api and api.startswith("/api"):
                    server.setdefault(api, []).append({
                        "file": rel(path),
                        "line": line_no(text, m.start()),
                        "kind": "flask route",
                    })

    return {
        "client": client,
        "server": server,
    }

def api_match(client_path, server_path):
    if client_path == server_path:
        return True

    def parts(x):
        return [p for p in x.split("/") if p]

    a = parts(client_path)
    b = parts(server_path)

    if len(a) != len(b):
        return False

    for x, y in zip(a, b):
        if x == y:
            continue

        if x == "{param}" or y == "{param}":
            continue

        return False

    return True


def trace_api(api_data):
    findings = []

    client = api_data["client"]
    server = api_data["server"]

    for api, client_refs in sorted(client.items()):
        matches = [
            server_api
            for server_api in server
            if api_match(api, server_api)
        ]

        if matches:
            findings.append({
                "type": "API",
                "name": api,
                "status": "MATCHED",
                "confidence": "HIGH",
                "client": client_refs,
                "server": [
                    ref
                    for matched in matches
                    for ref in server[matched]
                ],
                "message": "مسار API العميل مرتبط بمسار خادم مطابق فعليًا."
            })
        else:
            findings.append({
                "type": "API",
                "name": api,
                "status": "UNRESOLVED",
                "confidence": "MEDIUM",
                "client": client_refs,
                "server": [],
                "message": "لم يجد المحرك مسار خادم مطابقًا؛ يحتاج تحققًا يدويًا قبل اعتباره خللًا."
            })

    return findings


def trace_socket(socket_data):
    """
    V2.4 Socket Truth Graph.

    لا يعتبر مجرد غياب listener خللاً.
    يحاول تتبع سلسلة الحدث داخل الخادم ثم عودته للعميل.
    """

    findings = []

    client_emit = socket_data["client_emit"]
    client_on = socket_data["client_on"]
    server_on = socket_data["server_on"]
    server_emit = socket_data["server_emit"]

    server_handlers = socket_data.get(
        "server_handlers",
        []
    )

    # ========================================================
    # CLIENT → SERVER
    # ========================================================

    for event, refs in sorted(client_emit.items()):

        if event in server_on:

            handlers = [
                h for h in server_handlers
                if h["event"] == event
            ]

            findings.append({
                "type": "SOCKET",
                "direction": "CLIENT → SERVER",
                "event": event,
                "status": "MATCHED",
                "confidence": "HIGH",
                "source": refs,
                "target": server_on[event],
                "handler": handlers,
                "message": (
                    "العميل يرسل الحدث والخادم لديه listener مطابق."
                ),
            })

        else:

            findings.append({
                "type": "SOCKET",
                "direction": "CLIENT → SERVER",
                "event": event,
                "status": "UNRESOLVED",
                "confidence": "MEDIUM",
                "source": refs,
                "target": [],
                "handler": [],
                "message": (
                    "لم يجد المحرك listener مطابقًا في الخادم؛ "
                    "الحدث غير محسوم وليس خللًا مؤكدًا."
                ),
            })

    # ========================================================
    # SERVER → CLIENT
    # ========================================================

    for event, refs in sorted(server_emit.items()):

        if event in client_on:

            findings.append({
                "type": "SOCKET",
                "direction": "SERVER → CLIENT",
                "event": event,
                "status": "MATCHED",
                "confidence": "HIGH",
                "source": refs,
                "target": client_on[event],
                "message": (
                    "الخادم يرسل الحدث والعميل لديه listener مطابق."
                ),
            })

        else:

            findings.append({
                "type": "SOCKET",
                "direction": "SERVER → CLIENT",
                "event": event,
                "status": "UNRESOLVED",
                "confidence": "MEDIUM",
                "source": refs,
                "target": [],
                "message": (
                    "الخادم يرسل حدثًا لم يجد له العميل listener مطابقًا؛ "
                    "قد يكون موجهًا لطرف آخر أو مسجلًا بطريقة غير مكتشفة."
                ),
            })

    # ========================================================
    # DEEP SERVER HANDLER TRACE
    # ========================================================

    for item in findings:

        if item["direction"] != "CLIENT → SERVER":
            continue

        if item["status"] != "MATCHED":
            continue

        event = item["event"]

        handlers = [
            h for h in server_handlers
            if h["event"] == event
        ]

        downstream = set()

        for handler in handlers:

            body = handler.get("body", "")

            # JavaScript:
            # socket.emit(...)
            # io.emit(...)
            for m in re.finditer(
                r"\b(?:socket|io)\s*\.\s*emit\s*\(\s*['\"]([^'\"]+)['\"]",
                body
            ):
                downstream.add(m.group(1))

            # Python:
            # socketio.emit(...)
            for m in re.finditer(
                r"\bsocketio\.emit\s*\(\s*['\"]([^'\"]+)['\"]",
                body
            ):
                downstream.add(m.group(1))

        item["downstream_events"] = sorted(downstream)

        chains = []

        for downstream_event in sorted(downstream):

            if downstream_event in client_on:

                chains.append({
                    "event": downstream_event,
                    "status": "CONFIRMED",
                    "target": client_on[downstream_event],
                    "message": (
                        "الـhandler يرسل حدثًا ولدى العميل listener مطابق."
                    ),
                })

            else:

                chains.append({
                    "event": downstream_event,
                    "status": "UNRESOLVED",
                    "target": [],
                    "message": (
                        "الـhandler يرسل حدثًا لكن لم يجد المحرك "
                        "listener مطابقًا في العميل."
                    ),
                })

        item["downstream_trace"] = chains

        if downstream and chains and all(
            c["status"] == "CONFIRMED"
            for c in chains
        ):
            item["graph_status"] = "CONFIRMED"

        elif downstream:
            item["graph_status"] = "PARTIAL"

        else:
            item["graph_status"] = "SERVER_HANDLER_ONLY"

    return findings

# ============================================================
# V2.5 — Execution Plan vs Actual Code
# ============================================================

PLAN_CANDIDATES = [
    PROJECT / "execution-plan.json",
    PROJECT / ".repair-repository" / "execution-plan.json",
]


def normalize_source_code(value):
    """
    تطبيع محافظ للمقارنة:
    - توحيد نهايات الأسطر
    - إزالة BOM
    - إزالة الفراغات الطرفية
    - تجاهل الأسطر الفارغة
    """
    if value is None:
        return ""

    value = str(value)
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = value.replace("\ufeff", "")

    lines = []

    for line in value.splitlines():
        line = line.rstrip()

        if line.strip():
            lines.append(line.strip())

    return "\n".join(lines)


def source_line(text, position):
    return text.count("\n", 0, position) + 1


def read_execution_plan():
    for candidate in PLAN_CANDIDATES:

        if not candidate.exists():
            continue

        try:
            data = json.loads(
                candidate.read_text(
                    encoding="utf-8",
                    errors="replace"
                )
            )

            return {
                "path": candidate,
                "data": data
            }

        except Exception as exc:

            return {
                "path": candidate,
                "data": None,
                "error": str(exc)
            }

    return None


def plan_items(plan):
    """
    الصيغ المدعومة:

    1)
    {
      "files": {
        "public/app.js": "الكود المرجعي"
      }
    }

    2)
    {
      "files": [
        {
          "path": "public/app.js",
          "blocks": [
            {
              "id": "send-offer",
              "description": "إرسال WebRTC offer",
              "code": "..."
            }
          ]
        }
      ]
    }

    3)
    {
      "files": [
        {
          "path": "public/app.js",
          "id": "send-offer",
          "code": "..."
        }
      ]
    }
    """

    if not isinstance(plan, dict):
        return []

    files = plan.get("files", [])
    result = []

    # --------------------------------------------------------
    # files كـ dictionary
    # --------------------------------------------------------

    if isinstance(files, dict):

        for file_path, code in files.items():

            result.append({
                "path": file_path,
                "id": "full-file",
                "description": "مقارنة الملف الكامل",
                "code": code,
                "anchor": None,
            })

        return result

    if not isinstance(files, list):
        return []

    # --------------------------------------------------------
    # files كـ list
    # --------------------------------------------------------

    for item in files:

        if not isinstance(item, dict):
            continue

        file_path = item.get("path")

        if not file_path:
            continue

        blocks = item.get("blocks")

        # ----------------------------------------------------
        # blocks
        # ----------------------------------------------------

        if isinstance(blocks, list):

            for index, block in enumerate(blocks, 1):

                if not isinstance(block, dict):
                    continue

                code = block.get("code")

                if code is None:
                    continue

                result.append({
                    "path": file_path,
                    "id": block.get(
                        "id",
                        f"block-{index}"
                    ),
                    "description": block.get(
                        "description",
                        ""
                    ),
                    "code": code,
                    "anchor": block.get("anchor"),
                })

        # ----------------------------------------------------
        # ملف/بند مباشر
        # ----------------------------------------------------

        elif "code" in item:

            result.append({
                "path": file_path,
                "id": item.get(
                    "id",
                    "full-file"
                ),
                "description": item.get(
                    "description",
                    "مقارنة الكود المرجعي"
                ),
                "code": item.get(
                    "code",
                    ""
                ),
                "anchor": item.get("anchor"),
            })

    return result


def extract_plan_anchor(code, explicit_anchor=None):
    """
    استخراج نقطة ارتكاز قوية من الكود المرجعي.
    """

    if explicit_anchor:
        return str(explicit_anchor)

    patterns = [

        r'socket\.emit\s*\(\s*["\']([^"\']+)["\']',

        r'socket\.on\s*\(\s*["\']([^"\']+)["\']',

        r'io\.emit\s*\(\s*["\']([^"\']+)["\']',

        r'io\.on\s*\(\s*["\']([^"\']+)["\']',

        r'@socketio\.on\s*\(\s*["\']([^"\']+)["\']',

        r'@app\.route\s*\(\s*["\']([^"\']+)["\']',

        r'function\s+([A-Za-z_$][\w$]*)',

        r'def\s+([A-Za-z_]\w*)',

        r'(?:const|let|var)\s+([A-Za-z_$][\w$]*)',

        r'class\s+([A-Za-z_$][\w$]*)',
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            str(code)
        )

        if match:
            return match.group(1)

    return None


def find_anchor_occurrences(actual, anchor):

    if not anchor:
        return []

    positions = []

    for match in re.finditer(
        re.escape(anchor),
        actual,
        flags=re.IGNORECASE
    ):

        positions.append(
            source_line(
                actual,
                match.start()
            )
        )

    return positions


def compare_code_block(reference_code, actual_code):

    ref = normalize_source_code(
        reference_code
    )

    actual = normalize_source_code(
        actual_code
    )

    if not ref:

        return {
            "status": "EMPTY_REFERENCE",
            "message": "الكود المرجعي فارغ."
        }

    if ref == actual:

        return {
            "status": "MATCHED",
            "message": "الكود الفعلي مطابق للكود المرجعي."
        }

    if ref in actual:

        return {
            "status": "MATCHED",
            "message": "الكود المرجعي موجود داخل الكود الفعلي."
        }

    return {
        "status": "DIFFERENT",
        "message": (
            "الكود الفعلي موجود لكنه لا يطابق "
            "الكود المرجعي."
        )
    }


def compare_execution_plan(project):

    loaded = read_execution_plan()

    result = {
        "enabled": False,
        "plan_path": None,
        "status": "NO_PLAN",
        "items": [],
        "summary": {
            "total": 0,
            "matched": 0,
            "different": 0,
            "missing": 0,
            "empty_reference": 0,
            "invalid_path": 0,
            "read_error": 0,
        }
    }

    if loaded is None:

        result["message"] = (
            "لا توجد خطة تنفيذية مرجعية."
        )

        return result

    result["enabled"] = True
    result["plan_path"] = str(
        loaded["path"]
    )

    if loaded.get("data") is None:

        result["status"] = "PLAN_READ_ERROR"

        result["message"] = loaded.get(
            "error",
            "تعذر قراءة الخطة."
        )

        return result

    items = plan_items(
        loaded["data"]
    )

    result["summary"]["total"] = len(
        items
    )

    project_root = project.resolve()

    for item in items:

        relative = Path(
            str(item["path"])
        )

        # ----------------------------------------------------
        # منع الخروج خارج المشروع
        # ----------------------------------------------------

        try:

            actual_path = (
                project / relative
            ).resolve()

            if (
                actual_path != project_root
                and project_root not in actual_path.parents
            ):

                result["summary"][
                    "invalid_path"
                ] += 1

                result["items"].append({
                    "id": item["id"],
                    "path": item["path"],
                    "status": "INVALID_PATH",
                    "message": (
                        "مسار الخطة خارج المشروع."
                    )
                })

                continue

        except Exception as exc:

            result["summary"][
                "invalid_path"
            ] += 1

            result["items"].append({
                "id": item["id"],
                "path": item["path"],
                "status": "INVALID_PATH",
                "message": str(exc)
            })

            continue

        # ----------------------------------------------------
        # الملف غير موجود
        # ----------------------------------------------------

        if not actual_path.exists():

            result["summary"]["missing"] += 1

            result["items"].append({
                "id": item["id"],
                "path": item["path"],
                "description": item.get(
                    "description",
                    ""
                ),
                "status": "MISSING",
                "reference_code": item.get(
                    "code",
                    ""
                ),
                "message": (
                    "الخطة تتطلب هذا الكود/الملف "
                    "لكن الملف غير موجود فعليًا."
                )
            })

            continue

        # ----------------------------------------------------
        # قراءة الملف
        # ----------------------------------------------------

        try:

            actual_code = actual_path.read_text(
                encoding="utf-8",
                errors="replace"
            )

        except Exception as exc:

            result["summary"][
                "read_error"
            ] += 1

            result["items"].append({
                "id": item["id"],
                "path": item["path"],
                "status": "READ_ERROR",
                "message": str(exc)
            })

            continue

        # ----------------------------------------------------
        # المقارنة
        # ----------------------------------------------------

        comparison = compare_code_block(
            item.get("code", ""),
            actual_code
        )

        status = comparison["status"]

        if status == "MATCHED":

            result["summary"]["matched"] += 1

            result["items"].append({
                "id": item["id"],
                "path": item["path"],
                "description": item.get(
                    "description",
                    ""
                ),
                "status": "MATCHED",
                "message": comparison["message"]
            })

            continue

        if status == "EMPTY_REFERENCE":

            result["summary"][
                "empty_reference"
            ] += 1

            result["items"].append({
                "id": item["id"],
                "path": item["path"],
                "status": status,
                "message": comparison["message"]
            })

            continue

        # ----------------------------------------------------
        # DIFFERENT أو MISSING
        # ----------------------------------------------------

        anchor = extract_plan_anchor(
            item.get("code", ""),
            item.get("anchor")
        )

        locations = find_anchor_occurrences(
            actual_code,
            anchor
        )

        base_item = {
            "id": item["id"],
            "path": item["path"],
            "description": item.get(
                "description",
                ""
            ),
            "anchor": anchor,
            "actual_lines": locations,
            "reference_code": item.get(
                "code",
                ""
            ),
        }

        if locations:

            result["summary"][
                "different"
            ] += 1

            base_item.update({
                "status": "DIFFERENT",
                "message": (
                    "تم العثور على موضع التنفيذ، "
                    "لكن الكود الفعلي يختلف عن "
                    "الكود المرجعي."
                )
            })

        else:

            result["summary"][
                "missing"
            ] += 1

            base_item.update({
                "status": "MISSING",
                "message": (
                    "لم يجد المحرك التنفيذ المرجعي "
                    "ولا نقطة الارتكاز الخاصة به."
                )
            })

        result["items"].append(
            base_item
        )

    summary = result["summary"]

    if (
        summary["different"] > 0
        or summary["missing"] > 0
        or summary["invalid_path"] > 0
    ):

        result["status"] = (
            "MISMATCHES_FOUND"
        )

    elif (
        summary["empty_reference"] > 0
        or summary["read_error"] > 0
    ):

        result["status"] = (
            "PLAN_HAS_ISSUES"
        )

    else:

        result["status"] = (
            "PLAN_MATCHED"
        )

    return result


def print_execution_plan_report(comparison):

    print()
    print("=" * 80)
    print(
        "🧭 V2.5 — مقارنة الخطة التنفيذية "
        "مع الكود الفعلي"
    )
    print("=" * 80)

    if not comparison.get("enabled"):

        print(
            "⚪ لا توجد خطة تنفيذية مرجعية."
        )

        print(
            "📌 أنشئ execution-plan.json "
            "ليبدأ المحرك المقارنة."
        )

        return

    print(
        f"📋 الخطة: "
        f"{comparison.get('plan_path')}"
    )

    print(
        f"📊 الحالة: "
        f"{comparison.get('status')}"
    )

    print()

    summary = comparison["summary"]

    print(
        f"📦 إجمالي البنود       : "
        f"{summary['total']}"
    )

    print(
        f"🟢 مطابق               : "
        f"{summary['matched']}"
    )

    print(
        f"🟠 مختلف               : "
        f"{summary['different']}"
    )

    print(
        f"🔴 مفقود               : "
        f"{summary['missing']}"
    )

    if summary["empty_reference"]:

        print(
            f"⚪ مرجع فارغ           : "
            f"{summary['empty_reference']}"
        )

    if summary["invalid_path"]:

        print(
            f"⛔ مسار غير صالح       : "
            f"{summary['invalid_path']}"
        )

    if summary["read_error"]:

        print(
            f"❌ أخطاء قراءة         : "
            f"{summary['read_error']}"
        )

    print()

    for item in comparison["items"]:

        status = item.get(
            "status"
        )

        if status == "MATCHED":
            icon = "🟢"

        elif status == "DIFFERENT":
            icon = "🟠"

        elif status == "MISSING":
            icon = "🔴"

        elif status == "EMPTY_REFERENCE":
            icon = "⚪"

        elif status == "INVALID_PATH":
            icon = "⛔"

        else:
            icon = "❔"

        print(
            f"{icon} {item.get('path')} "
            f"[{item.get('id')}]"
        )

        print(
            f"   الحالة : {status}"
        )

        if item.get("description"):

            print(
                f"   الوصف  : "
                f"{item['description']}"
            )

        if item.get("anchor"):

            print(
                f"   نقطة التتبع : "
                f"{item['anchor']}"
            )

        if item.get("actual_lines"):

            print(
                f"   المواضع الفعلية : "
                f"{item['actual_lines']}"
            )

        print(
            f"   النتيجة: "
            f"{item.get('message', '')}"
        )

        print()


def write_execution_plan_report(comparison):

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    report_path = (
        REPORT_DIR
        / "v2.5-execution-plan-comparison.json"
    )

    report_path.write_text(
        json.dumps(
            comparison,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    return report_path


def syntax_tests(project_files):
    tests = []

    for path in project_files:
        suffix = path.suffix.lower()

        if suffix == ".js":
            try:
                r = subprocess.run(
                    ["node", "--check", str(path)],
                    capture_output=True,
                    text=True,
                    timeout=20
                )

                tests.append({
                    "file": rel(path),
                    "test": "node --check",
                    "status": "PASS" if r.returncode == 0 else "FAIL",
                    "stderr": r.stderr[:2000],
                })
            except Exception as e:
                tests.append({
                    "file": rel(path),
                    "test": "node --check",
                    "status": "ERROR",
                    "stderr": str(e),
                })

        elif suffix == ".py":
            try:
                r = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(path)],
                    capture_output=True,
                    text=True,
                    timeout=20
                )

                tests.append({
                    "file": rel(path),
                    "test": "python -m py_compile",
                    "status": "PASS" if r.returncode == 0 else "FAIL",
                    "stderr": r.stderr[:2000],
                })
            except Exception as e:
                tests.append({
                    "file": rel(path),
                    "test": "python -m py_compile",
                    "status": "ERROR",
                    "stderr": str(e),
                })

    return tests


def research(query):
    """
    V2.3 لا يدّعي أن جلب صفحة بحث = حل.
    نحتفظ بالبحث كدليل خارجي فقط.
    """
    result = {
        "query": query,
        "status": "NOT_RUN",
        "bytes": 0,
        "url": None,
    }

    try:
        url = (
            "https://www.google.com/search?q="
            + urllib.parse.quote(query)
        )

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read(200000)

        result["status"] = "REACHABLE"
        result["bytes"] = len(data)
        result["url"] = url

    except Exception as e:
        result["status"] = "ERROR"
        result["error"] = str(e)

    return result


def print_trace(findings):
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🔎 تتبع الحقيقة")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if not findings:
        print("ℹ️ لم يتم اكتشاف مسارات قابلة للتتبع.")
        return

    for item in findings:
        print()

        if item["status"] == "MATCHED":
            icon = "✅"
        else:
            icon = "⚠️"

        print(
            f"{icon} {item['type']} | "
            f"{item.get('direction', '')} | "
            f"{item.get('name', item.get('event', ''))}"
        )

        print(f"   الحالة       : {item['status']}")
        print(f"   الثقة        : {item['confidence']}")
        print(f"   النتيجة      : {item['message']}")

        for src in item.get("source", item.get("client", [])):
            print(
                f"   ← المصدر     : "
                f"{src['file']}:{src['line']}"
            )

        for dst in item.get("target", item.get("server", [])):
            print(
                f"   → الهدف      : "
                f"{dst['file']}:{dst['line']}"
            )


def main():
    started = time.time()

    print("🛠️ مستودع الإصلاح V2.5")
    print("🔬 Truth-Trace Diagnostic Engine")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"📁 المشروع: {ROOT}")
    print("🔒 الوضع: تشخيص وتتبع فقط — لا تعديل على بلبل")
    print()

    if not ROOT.exists():
        print("❌ المشروع غير موجود:")
        print(ROOT)
        sys.exit(1)

    REPORT_DIR.mkdir(exist_ok=True)

    files = collect_files()

    print(f"📄 الملفات البرمجية: {len(files)}")

    classifications = {}

    for p in files:
        classifications[rel(p)] = classify_file(p)

    print()
    print("🧭 تصنيف الملفات")

    for name, role in classifications.items():
        print(f"{role:7} {name}")

    socket_data = collect_socket(files)
    api_data = collect_api(files)

    socket_findings = trace_socket(socket_data)
    api_findings = trace_api(api_data)

    findings = api_findings + socket_findings

    # --------------------------------------------------------
    # V2.5 — مقارنة الخطة التنفيذية بالكود الفعلي
    # --------------------------------------------------------

    execution_plan = compare_execution_plan(PROJECT)

    print_execution_plan_report(
        execution_plan
    )

    execution_plan_report = (
        write_execution_plan_report(
            execution_plan
        )
    )


    tests = syntax_tests(files)

    # بحث خارجي محدود، فقط للمسارات غير المحسومة.
    research_results = []

    for item in findings:
        if item["status"] != "UNRESOLVED":
            continue

        name = item.get("name") or item.get("event")

        if item["type"] == "API":
            query = f"API endpoint {name} Express Flask frontend"
        else:
            query = f"Socket.IO event {name} client server"

        research_results.append(research(query))

        if len(research_results) >= 10:
            break

    report = {
        "app": APP_NAME,
        "version": VERSION,
        "project": str(ROOT),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "mode": "diagnostic-only",
        "files": [
            {
                "path": rel(p),
                "role": classify_file(p),
            }
            for p in files
        ],
        "api": api_data,
        "socket": socket_data,
        "api_trace": api_findings,
        "socket_trace": socket_findings,
        "findings": findings,
        "tests": tests,
        "research": research_results,
        "execution_plan_comparison": execution_plan,
        "repairs_applied": [],
        "elapsed_seconds": round(time.time() - started, 3),
    }

    report_path = REPORT_DIR / "v2.5-truth-trace.json"

    report_path.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print_trace(findings)

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🧪 الاختبارات")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    for test in tests:
        icon = "✅" if test["status"] == "PASS" else "❌"
        print(
            f"{icon} {test['file']} "
            f"→ {test['test']} "
            f"→ {test['status']}"
        )

    matched = sum(
        1 for x in findings
        if x["status"] == "MATCHED"
    )

    unresolved = sum(
        1 for x in findings
        if x["status"] == "UNRESOLVED"
    )

    failed_tests = sum(
        1 for x in tests
        if x["status"] != "PASS"
    )

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📊 النتيجة النهائية")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"📄 الملفات                : {len(files)}")
    print(f"🔗 المسارات المكتملة      : {matched}")
    print(f"⚠️ المسارات غير المحسومة : {unresolved}")
    print(f"❌ اختبارات فاشلة         : {failed_tests}")
    print(f"🌐 عمليات البحث           : {len(research_results)}")
    print(f"🔧 إصلاحات مطبقة          : 0")
    print()
    print("📄 التقرير:")
    print(report_path)


if __name__ == "__main__":
    main()
