from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone


class ScreenContractEngine:
    """
    محرك العقود التنفيذية للشاشات.

    يحول تعريف الشاشة الموجود داخل Blueprint
    إلى عقد قابل للتنفيذ والاختبار.

    لا يستبدل الـBlueprint.
    بل يضيف طبقة تنفيذ موحدة فوقه.
    """

    VERSION = 1

    def __init__(self, blueprint):
        self.blueprint = blueprint or {}
        self.screens = self.blueprint.get("screens", [])
        self.modules = self.blueprint.get("modules", [])
        self.api = self.blueprint.get("api", [])
        self.database = self.blueprint.get("database", {})

    @staticmethod
    def _text(value):
        return str(value or "").strip()

    @staticmethod
    def _slug(value):
        text = str(value or "").strip().lower()
        result = []
        for char in text:
            if char.isalnum():
                result.append(char)
            elif char in " _-/":
                result.append("-")
        value = "".join(result).strip("-")
        return value or "screen"

    def _module_for_screen(self, screen):
        module_id = self._text(
            screen.get("module_id")
            or screen.get("moduleId")
            or screen.get("module")
        )

        if module_id:
            for module in self.modules:
                if self._text(module.get("id")) == module_id:
                    return module

        module_name = self._text(
            screen.get("module_name")
            or screen.get("moduleName")
            or screen.get("module")
        )

        if module_name:
            for module in self.modules:
                if self._text(module.get("name")) == module_name:
                    return module

        return self.modules[0] if self.modules else {}

    def _screen_profile(self, screen):
        screen_id = self._text(
            screen.get("id")
            or screen.get("key")
            or screen.get("name")
        ).lower()

        profiles = {
            "home": {
                "table": None,
                "api": [],
                "fields": [],
                "actions": [
                    {
                        "id": "open_consultation_choice",
                        "label": "اختيار نوع الاستشارة",
                        "method": "GET"
                    }
                ],
            },
            "login": {
                "table": "users",
                "api": ["/api/auth/login"],
                "fields": [
                    {"name": "phone", "type": "tel", "required": True},
                    {"name": "password", "type": "password", "required": True},
                ],
                "actions": [{
                    "id": "login",
                    "label": "تسجيل الدخول",
                    "method": "POST",
                    "api": "/api/auth/login",
                }],
            },
            "dashboard": {
                "table": None,
                "api": ["/api/meta"],
                "fields": [],
                "actions": [{
                    "id": "load_meta",
                    "label": "تحميل لوحة التحكم",
                    "method": "GET",
                    "api": "/api/meta",
                }],
            },
            "clients": {
                "table": "clients",
                "api": ["/api/clients"],
                "fields": [
                    {"name": "name", "type": "text", "required": True},
                    {"name": "phone", "type": "tel"},
                    {"name": "email", "type": "email"},
                    {"name": "status", "type": "text"},
                ],
                "actions": [
                    {"id": "list", "label": "عرض الموكلين", "method": "GET", "api": "/api/clients"},
                    {"id": "create", "label": "إضافة موكل", "method": "POST", "api": "/api/clients"},
                    {"id": "update", "label": "تعديل موكل", "method": "PUT", "api": "/api/clients/:id"},
                    {"id": "delete", "label": "حذف موكل", "method": "DELETE", "api": "/api/clients/:id"},
                ],
            },
            "lawyers": {
                "table": "lawyers",
                "api": ["/api/lawyers"],
                "fields": [
                    {"name": "name", "type": "text", "required": True},
                    {"name": "phone", "type": "tel"},
                    {"name": "email", "type": "email"},
                ],
                "actions": [
                    {"id": "list", "label": "عرض المحامين", "method": "GET", "api": "/api/lawyers"},
                    {"id": "create", "label": "إضافة محام", "method": "POST", "api": "/api/lawyers"},
                    {"id": "update", "label": "تعديل محام", "method": "PUT", "api": "/api/lawyers/:id"},
                    {"id": "delete", "label": "حذف محام", "method": "DELETE", "api": "/api/lawyers/:id"},
                ],
            },
            "cases": {
                "table": "cases",
                "api": ["/api/cases"],
                "fields": [
                    {"name": "case_number", "type": "text"},
                    {"name": "court", "type": "text"},
                    {"name": "chamber", "type": "text"},
                    {"name": "status", "type": "text"},
                    {"name": "notes", "type": "textarea"},
                    {"name": "client_id", "type": "number"},
                    {"name": "lawyer_id", "type": "number"},
                ],
                "actions": [
                    {"id": "list", "label": "عرض القضايا", "method": "GET", "api": "/api/cases"},
                    {"id": "create", "label": "إضافة قضية", "method": "POST", "api": "/api/cases"},
                    {"id": "update", "label": "تعديل قضية", "method": "PUT", "api": "/api/cases/:id"},
                    {"id": "delete", "label": "حذف قضية", "method": "DELETE", "api": "/api/cases/:id"},
                ],
            },
            "documents": {
                "table": "documents",
                "api": ["/api/documents"],
                "fields": [
                    {"name": "name", "type": "text", "required": True},
                    {"name": "file_path", "type": "text", "required": True},
                    {"name": "mime_type", "type": "text"},
                    {"name": "case_id", "type": "number"},
                    {"name": "uploaded_by", "type": "number"},
                ],
                "actions": [
                    {"id": "list", "label": "عرض المستندات", "method": "GET", "api": "/api/documents"},
                    {"id": "create", "label": "إضافة مستند", "method": "POST", "api": "/api/documents"},
                    {"id": "update", "label": "تعديل مستند", "method": "PUT", "api": "/api/documents/:id"},
                    {"id": "delete", "label": "حذف مستند", "method": "DELETE", "api": "/api/documents/:id"},
                ],
            },
            "consultations": {
                "table": "consultations",
                "api": ["/api/consultations"],
                "fields": [
                    {"name": "client_id", "type": "number"},
                    {"name": "lawyer_id", "type": "number"},
                    {"name": "case_id", "type": "number"},
                    {"name": "subject", "type": "text", "required": True},
                    {"name": "status", "type": "text"},
                    {"name": "notes", "type": "textarea"},
                ],
                "actions": [
                    {"id": "list", "label": "عرض الاستشارات", "method": "GET", "api": "/api/consultations"},
                    {"id": "create", "label": "إضافة استشارة", "method": "POST", "api": "/api/consultations"},
                    {"id": "update", "label": "تعديل استشارة", "method": "PUT", "api": "/api/consultations/:id"},
                    {"id": "delete", "label": "حذف استشارة", "method": "DELETE", "api": "/api/consultations/:id"},
                ],
            },
            "appointments": {
                "table": "appointments",
                "api": ["/api/appointments"],
                "fields": [
                    {"name": "title", "type": "text", "required": True},
                    {"name": "appointment_date", "type": "datetime-local", "required": True},
                    {"name": "status", "type": "text"},
                    {"name": "user_id", "type": "number"},
                ],
                "actions": [
                    {"id": "list", "label": "عرض المواعيد", "method": "GET", "api": "/api/appointments"},
                    {"id": "create", "label": "إضافة موعد", "method": "POST", "api": "/api/appointments"},
                    {"id": "update", "label": "تعديل موعد", "method": "PUT", "api": "/api/appointments/:id"},
                    {"id": "delete", "label": "حذف موعد", "method": "DELETE", "api": "/api/appointments/:id"},
                ],
            },
            "consultation_choice": {
                "table": None,
                "api": [
                    "/api/consultations"
                ],
                "fields": [],
                "actions": [
                    {
                        "id": "open_free_consultation",
                        "label": "الاستشارة المجانية",
                        "method": "GET"
                    },
                    {
                        "id": "open_private_consultation",
                        "label": "الاستشارة الخاصة",
                        "method": "GET"
                    }
                ],
            },
            "private_consultation": {
                "table": "messages",
                "api": [
                    "/api/consultations",
                    "/api/conversations",
                    "/api/messages",
                    "/api/documents"
                ],
                "fields": [
                    {
                        "name": "الرسالة",
                        "type": "textarea",
                        "required": False
                    },
                    {
                        "name": "الملف",
                        "type": "file",
                        "required": False
                    }
                ],
                "actions": [
                    {
                        "id": "send_message",
                        "label": "إرسال رسالة",
                        "method": "POST",
                        "api": "/api/messages"
                    },
                    {
                        "id": "receive_messages",
                        "label": "استقبال الرسائل",
                        "method": "GET",
                        "api": "/api/messages"
                    },
                    {
                        "id": "attach_document",
                        "label": "إرفاق مستند",
                        "method": "POST",
                        "api": "/api/documents"
                    },
                    {
                        "id": "attach_file",
                        "label": "إرفاق ملف",
                        "method": "POST",
                        "api": "/api/documents"
                    },
                    {
                        "id": "attach_video",
                        "label": "إرفاق فيديو",
                        "method": "POST",
                        "api": "/api/documents"
                    },
                    {
                        "id": "attach_audio",
                        "label": "إرفاق ملف صوتي",
                        "method": "POST",
                        "api": "/api/documents"
                    },
                    {
                        "id": "copy_reply",
                        "label": "نسخ رد المستشار",
                        "method": "POST"
                    },
                    {
                        "id": "print_reply",
                        "label": "طباعة رد المستشار",
                        "method": "POST"
                    },
                    {
                        "id": "export_reply",
                        "label": "تصدير رد المستشار",
                        "method": "POST"
                    }
                ],
            },
            "chat": {
                "table": "messages",
                "api": ["/api/conversations", "/api/messages"],
                "fields": [
                    {"name": "receiver_id", "type": "number"},
                    {"name": "message", "type": "textarea", "required": True},
                ],
                "actions": [
                    {"id": "conversations", "label": "عرض المحادثات", "method": "GET", "api": "/api/conversations"},
                    {"id": "send_message", "label": "إرسال رسالة", "method": "POST", "api": "/api/messages"},
                ],
            },
            "notifications": {
                "table": "notifications",
                "api": ["/api/notifications"],
                "fields": [
                    {"name": "user_id", "type": "number"},
                    {"name": "title", "type": "text", "required": True},
                    {"name": "message", "type": "textarea"},
                    {"name": "is_read", "type": "number"},
                ],
                "actions": [
                    {"id": "list", "label": "عرض الإشعارات", "method": "GET", "api": "/api/notifications"},
                    {"id": "create", "label": "إضافة إشعار", "method": "POST", "api": "/api/notifications"},
                ],
            },
            "reports": {
                "table": None,
                "api": ["/api/reports"],
                "fields": [],
                "actions": [{
                    "id": "load",
                    "label": "عرض التقارير",
                    "method": "GET",
                    "api": "/api/reports",
                }],
            },
        }

        return profiles.get(screen_id, {
            "table": None,
            "api": [],
            "fields": [],
            "actions": [],
        })

    def _apis_for_screen(self, screen):
        explicit = (
            screen.get("api")
            or screen.get("apis")
            or screen.get("endpoints")
            or []
        )
        if isinstance(explicit, str):
            explicit = [explicit]
        if explicit:
            return explicit
        return list(self._screen_profile(screen).get("api") or [])

    def _fields(self, screen):
        fields = (
            screen.get("fields")
            or screen.get("form_fields")
            or screen.get("inputs")
            or self._screen_profile(screen).get("fields")
            or []
        )

        if isinstance(fields, dict):
            fields = [
                {"name": key, "type": value}
                for key, value in fields.items()
            ]

        normalized = []

        for index, field in enumerate(fields):
            if isinstance(field, str):
                normalized.append({
                    "id": self._slug(field),
                    "name": field,
                    "type": "text",
                    "required": False,
                })
                continue

            if not isinstance(field, dict):
                continue

            name = (
                field.get("name")
                or field.get("label")
                or field.get("id")
                or f"field_{index + 1}"
            )

            normalized.append({
                "id": self._text(field.get("id")) or self._slug(name),
                "name": self._text(name),
                "type": self._text(field.get("type")) or "text",
                "required": bool(field.get("required", False)),
                "validation": field.get("validation", {}),
            })

        return normalized

    def _actions(self, screen):
        actions = (
            screen.get("actions")
            or []
        )

        if isinstance(actions, str):
            actions = [actions]

        normalized = []

        for action in actions:
            if isinstance(action, str):
                normalized.append({
                    "id": self._slug(action),
                    "label": action,
                    "method": "POST",
                })
                continue

            if not isinstance(action, dict):
                continue

            name = (
                action.get("name")
                or action.get("label")
                or action.get("id")
                or "action"
            )

            normalized.append({
                "id": self._text(action.get("id")) or self._slug(name),
                "label": self._text(name),
                "method": self._text(action.get("method")).upper() or "POST",
                "api": action.get("api"),
            })

        if not normalized:
            normalized = [{
                "id": "load",
                "label": "عرض البيانات",
                "method": "GET",
            }]

        return normalized

    def _contract(self, screen, index):
        if not isinstance(screen, dict):
            screen = {"name": str(screen)}

        title = (
            screen.get("title")
            or screen.get("name")
            or screen.get("label")
            or f"الشاشة {index + 1}"
        )

        module = self._module_for_screen(screen)

        contract = {
            "contract_version": self.VERSION,
            "id": (
                self._text(screen.get("id"))
                or f"screen-{index + 1}"
            ),
            "key": self._slug(title),
            "title": self._text(title),
            "purpose": self._text(
                screen.get("purpose")
                or screen.get("description")
                or title
            ),
            "module": {
                "id": self._text(module.get("id")),
                "name": self._text(module.get("name")),
            },
            "fields": self._fields(screen),
            "actions": self._actions(screen),
            "api": self._apis_for_screen(screen),
            "database": {
                "table": (
                    screen.get("table")
                    or screen.get("database_table")
                    or screen.get("entity")
                    or self._screen_profile(screen).get("table")
                ),
                "relations": self.database.get("relations", []),
            },
            "permissions": screen.get(
                "permissions",
                ["authenticated"],
            ),
            "validation": screen.get(
                "validation",
                {},
            ),
            "dependencies": screen.get(
                "dependencies",
                [],
            ),
            "tests": [
                "screen_contract_valid",
                "screen_data_source_valid",
                "screen_actions_defined",
            ],
            "status": "planned",
        }

        canonical = json.dumps(
            contract,
            ensure_ascii=False,
            sort_keys=True,
        )

        contract["contract_hash"] = hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

        return contract

    def build(self):
        contracts = [
            self._contract(screen, index)
            for index, screen in enumerate(self.screens)
        ]

        errors = []

        ids = set()

        for contract in contracts:
            if not contract["id"]:
                errors.append("missing_screen_id")

            if contract["id"] in ids:
                errors.append(
                    "duplicate_screen_id:" + contract["id"]
                )

            ids.add(contract["id"])

            if not contract["title"]:
                errors.append(
                    "missing_screen_title:" + contract["id"]
                )

            if not contract["actions"]:
                errors.append(
                    "missing_actions:" + contract["id"]
                )

        return {
            "version": self.VERSION,
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "status": "PASSED" if not errors else "FAILED",
            "total": len(contracts),
            "contracts": contracts,
            "errors": errors,
        }
