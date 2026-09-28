
# -*- coding: utf-8 -*-

from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
import json
import re
import html


def now():
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ScreenProposal:
    screen_id: str
    title: str
    purpose: str
    variant: int
    layout: str
    components: list
    approved: bool = False


class ConversationState:

    def __init__(self, root):
        self.root = Path(root)
        self.path = self.root / ".abqaryno" / "creation-state.json"

    def save(self, data):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def load(self):
        if not self.path.exists():
            return {}

        try:
            return json.loads(
                self.path.read_text(encoding="utf-8")
            )
        except Exception:
            return {}


class RequirementsEngine:

    def analyze(self, idea):

        idea = idea.strip()

        screens = [
            {
                "id": "home",
                "title": "الشاشة الرئيسية",
                "purpose": "الشاشة الرئيسية والتنقل بين وظائف البرنامج"
            }
        ]

        text = idea.lower()

        chat_features = []

        if any(x in text for x in [
            "شات", "دردشة", "محادثة", "رسائل", "chat", "message", "messages"
        ]):
            screens.append({
                "id": "chat",
                "title": "غرفة الشات",
                "purpose": "إرسال واستقبال الرسائل وإدارة المحادثة"
            })
            chat_features.append("إرسال واستقبال الرسائل")

        if any(x in text for x in [
            "كاميرا", "camera", "فيديو", "video"
        ]):
            screens.append({
                "id": "camera",
                "title": "الكاميرا والفيديو",
                "purpose": "تشغيل الكاميرا ومعاينة وإرسال الفيديو"
            })
            chat_features.append("الكاميرا والفيديو")

        if any(x in text for x in [
            "مايك", "ميكروفون", "microphone", "mic", "صوت", "audio"
        ]):
            screens.append({
                "id": "microphone",
                "title": "المايك والصوت",
                "purpose": "تشغيل الميكروفون وإرسال الصوت"
            })
            chat_features.append("المايك والصوت")

        if any(x in text for x in [
            "إرفاق", "مرفق", "مرفقات", "ملف", "ملفات",
            "attachment", "attachments", "file", "files"
        ]):
            screens.append({
                "id": "attachments",
                "title": "المرفقات",
                "purpose": "اختيار وإرسال الملفات والمرفقات داخل المحادثة"
            })
            chat_features.append("إرفاق وإرسال الملفات")

        if any(x in text for x in [
            "to", "إلى", "المستلم", "مستلم"
        ]):
            chat_features.append("To — تحديد المستلم")

        if any(x in text for x in [
            "fetch", "جلب", "استدعاء البيانات"
        ]):
            chat_features.append("Fetch — جلب البيانات")

        if any(x in text for x in [
            "محام", "قانون", "قض", "مكتب"
        ]):
            screens.extend([
                {
                    "id": "cases",
                    "title": "القضايا",
                    "purpose": "إدارة القضايا ومتابعة حالتها"
                },
                {
                    "id": "clients",
                    "title": "الموكلون",
                    "purpose": "إدارة بيانات الموكلين"
                },
                {
                    "id": "sessions",
                    "title": "الجلسات",
                    "purpose": "متابعة الجلسات والمواعيد"
                },
                {
                    "id": "documents",
                    "title": "المستندات",
                    "purpose": "إدارة مستندات القضايا"
                }
            ])

        elif any(x in text for x in [
            "متجر", "بيع", "منتج"
        ]):
            screens.extend([
                {
                    "id": "products",
                    "title": "المنتجات",
                    "purpose": "عرض وإدارة المنتجات"
                },
                {
                    "id": "orders",
                    "title": "الطلبات",
                    "purpose": "متابعة الطلبات"
                }
            ])

        elif any(x in text for x in [
            "تعليم", "مدرس", "طلاب", "دورة"
        ]):
            screens.extend([
                {
                    "id": "courses",
                    "title": "الدورات",
                    "purpose": "إدارة الدورات"
                },
                {
                    "id": "students",
                    "title": "الطلاب",
                    "purpose": "إدارة الطلاب"
                }
            ])

        features = [
            "تسجيل المستخدم",
            "حفظ البيانات",
            "البحث"
        ]

        features.extend(chat_features)

        capability_engine = CapabilityEngine()
        capability_data = capability_engine.analyze(idea)

        return {
            "idea": idea,
            "created_at": now(),
            "screens": screens,
            "features": features,
            "app_types": capability_data["app_types"],
            "roles": capability_data["roles"],
            "capabilities": capability_data["capabilities"],
            "capability_labels": capability_data["capability_labels"]
        }


class CapabilityEngine:
    """
    محرك عام لفهم قدرات البرنامج المطلوبة من وصف المستخدم.
    لا يغيّر واجهة عبقرينو؛ يضيف فقط بيانات منظمة للمولد.
    """

    CAPABILITIES = {
        "auth": "تسجيل الدخول والحسابات",
        "users": "إدارة المستخدمين",
        "roles": "الأدوار والصلاحيات",
        "database": "قاعدة البيانات وحفظ السجلات",
        "crud": "الإضافة والتعديل والحذف والعرض",
        "search": "البحث والتصفية",
        "dashboard": "لوحة التحكم والإحصائيات",
        "chat": "المحادثات والرسائل",
        "files": "الملفات والمرفقات",
        "camera": "الكاميرا والفيديو",
        "microphone": "الميكروفون والصوت",
        "webrtc": "الاتصال المباشر WebRTC",
        "notifications": "الإشعارات والتنبيهات",
        "reports": "التقارير",
        "export": "التصدير",
        "print": "الطباعة",
        "scheduling": "المواعيد والحجوزات",
        "payments": "المدفوعات والفواتير",
        "location": "الموقع والخرائط",
        "settings": "الإعدادات",
        "audit": "سجل العمليات",
        "translation": "ترجمة المستندات والنصوص بين اللغات",
        "document_processing": "معالجة المستندات واستخراج النصوص",
        "ocr": "التعرف الضوئي على النصوص من الصور والمستندات الممسوحة",
        "speech_to_text": "تحويل الصوت إلى نص",
        "text_to_speech": "تحويل النص إلى صوت",
    }

    ROLE_WORDS = {
        "admin": ["مدير", "مشرف", "ادمن", "admin", "administrator"],
        "owner": ["صاحب الشركة", "صاحب المشروع", "مالك", "owner"],
        "employee": ["موظف", "عامل", "employee", "staff"],
        "lawyer": ["محامي", "محامية", "lawyer"],
        "client": ["موكل", "موكلة"],
        "student": ["طالب", "طالبة", "student"],
        "teacher": ["مدرس", "مدرسة", "معلم", "معلمة", "teacher"],
        "customer": ["زبون", "مشتري", "customer"],
        "doctor": ["طبيب", "طبيبة", "doctor"],
        "patient": ["مريض", "مريضة", "patient"],
        "driver": ["سائق", "driver"],
        "support": ["دعم", "موظف دعم", "support"],
    }

    DOMAIN_RULES = [
        ("legal", ["محام", "قانون", "قضية", "محكمة", "مكتب محاماة"]),
        ("commerce", ["متجر", "بيع", "مبيعات", "منتج", "مخزن", "مخزون"]),
        ("education", ["تعليم", "مدرس", "طلاب", "دورة", "مدرسة", "جامعة"]),
        ("media", ["بث", "بث مباشر", "لايف", "stream", "live"]),
        ("booking", ["حجز", "حجوزات", "موعد", "مواعيد", "reservation", "booking"]),
        ("finance", ["مصروف", "مصروفات", "حسابات", "فاتورة", "فواتير", "مالية"]),
        ("crm", ["عملاء", "موكلين", "crm", "علاقات العملاء"]),
        ("project_management", ["مشروع", "مهام", "فريق", "إدارة مشاريع"]),
        ("support", ["دعم فني", "تذاكر", "helpdesk", "support"]),
        ("logistics", ["توصيل", "شحن", "مندوب", "سائق", "طلبات"]),
    ]

    @staticmethod
    def _has(text, words):
        for word in words:
            word = word.lower()

            if re.search(r"[a-z]", word):
                if re.search(r"(?<![a-z0-9_])" + re.escape(word) + r"(?![a-z0-9_])", text):
                    return True
            elif word in text:
                return True

        return False

    def analyze(self, idea):
        text = idea.strip().lower()

        capabilities = {"database", "crud", "settings"}
        roles = []
        domains = []

        for role, words in self.ROLE_WORDS.items():
            if self._has(text, words):
                roles.append(role)

        for domain, words in self.DOMAIN_RULES:
            if self._has(text, words):
                domains.append(domain)

        rules = {
            "auth": [
                "تسجيل دخول", "تسجيل الدخول", "حساب", "حسابات",
                "login", "signin", "sign in", "تسجيل المستخدم"
            ],
            "users": ["مستخدم", "مستخدمين", "users", "user"],
            "roles": ["صلاحيات", "دور", "أدوار", "role", "roles", "مشرف", "مدير"],
            "chat": ["شات", "دردشة", "محادثة", "رسائل", "chat", "message", "messages"],
            "files": ["ملف", "ملفات", "مرفق", "مرفقات", "إرفاق", "attachment", "attachments", "file", "files"],
            "camera": ["كاميرا", "camera", "فيديو", "video"],
            "microphone": ["مايك", "ميكروفون", "microphone", "mic", "صوت", "audio", "تسجيل صوت"],
            "webrtc": ["webrtc", "مكالمة فيديو", "اتصال فيديو", "اتصال مباشر", "مكالمة صوتية"],
            "notifications": ["إشعار", "إشعارات", "تنبيه", "تنبيهات", "notification", "notifications"],
            "search": ["بحث", "ابحث", "تصفية", "فلترة", "search", "filter"],
            "dashboard": ["لوحة تحكم", "إحصائيات", "dashboard", "statistics", "stats"],
            "reports": ["تقرير", "تقارير", "report", "reports"],
            "export": ["تصدير", "excel", "csv", "pdf", "export"],
            "print": ["طباعة", "اطبع", "print"],
            "scheduling": ["حجز", "حجوزات", "موعد", "مواعيد", "جدول", "calendar", "booking"],
            "payments": ["دفع", "مدفوعات", "فاتورة", "فواتير", "سداد", "payment", "payments", "invoice"],
            "location": ["موقع", "خريطة", "خرائط", "موقع جغرافي", "map", "maps", "location", "gps"],
            "audit": ["سجل العمليات", "سجل النشاط", "audit", "activity log", "تتبع العمليات"],
            "translation": [
                "ترجمة", "ترجم", "مترجم", "translation",
                "translate", "translations", "multilingual"
            ],
            "document_processing": [
                "مستند", "مستندات", "وثيقة", "وثائق",
                "pdf", "word", "docx", "txt", "html",
                "document", "documents"
            ],
            "ocr": [
                "ocr", "مسح ضوئي", "صورة مستند",
                "صور ممسوحة", "مستند ممسوح", "مستندات ممسوحة",
                "استخراج النص من الصورة", "scanned", "scan"
            ],
            "speech_to_text": [
                "تحويل الصوت إلى نص", "تفريغ صوتي",
                "speech to text", "speech-to-text",
                "transcription", "audio transcription"
            ],
            "text_to_speech": [
                "نطق", "قراءة صوتية", "تحويل النص لصوت",
                "تحويل النص إلى صوت", "text to speech", "tts"
            ],
        }

        for capability, words in rules.items():
            if self._has(text, words):
                capabilities.add(capability)

        # بعض القدرات الأساسية تُستنتج من طبيعة النظام.
        if roles:
            capabilities.update({"auth", "users", "roles"})

        if any(x in domains for x in ["commerce", "finance", "crm", "legal", "project_management", "logistics"]):
            capabilities.update({"search", "reports"})

        if "booking" in domains:
            capabilities.update({"scheduling", "notifications"})

        if "media" in domains:
            capabilities.update({"camera", "microphone", "webrtc"})

        if "chat" in capabilities:
            capabilities.add("notifications")

        if "payments" in capabilities:
            capabilities.update({"audit", "reports"})

        return {
            "app_types": domains or ["general"],
            "roles": roles or ["user"],
            "capabilities": sorted(capabilities),
            "capability_labels": {
                key: self.CAPABILITIES[key]
                for key in sorted(capabilities)
                if key in self.CAPABILITIES
            }
        }


class ScreenIntelligenceEngine:

    SCREEN_RULES = {
        "home": {
            "layout": "لوحة تحكم",
            "components": ["العنوان", "ملخص البرنامج", "بطاقات الوظائف", "شريط التنقل"],
            "fields": [],
            "actions": ["فتح الوظيفة", "الانتقال للإعدادات"],
        },
        "chat": {
            "layout": "محادثة",
            "components": ["قائمة المحادثات", "منطقة الرسائل", "حقل كتابة", "زر إرسال"],
            "fields": ["الرسالة"],
            "actions": ["إرسال رسالة", "إرفاق ملف", "فتح الكاميرا", "تسجيل صوت"],
        },
        "camera": {
            "layout": "وسائط",
            "components": ["معاينة الكاميرا", "أزرار التحكم", "معاينة الوسائط"],
            "fields": [],
            "actions": ["تشغيل الكاميرا", "إيقاف الكاميرا", "التقاط", "إرسال"],
        },
        "microphone": {
            "layout": "وسائط",
            "components": ["مؤشر التسجيل", "أزرار التحكم", "مشغل الصوت"],
            "fields": [],
            "actions": ["بدء التسجيل", "إيقاف التسجيل", "تشغيل", "إرسال"],
        },
        "attachments": {
            "layout": "قائمة ملفات",
            "components": ["اختيار الملفات", "قائمة المرفقات", "حالة الرفع"],
            "fields": ["الملف"],
            "actions": ["اختيار ملف", "رفع", "حذف", "فتح"],
        },
        "cases": {
            "layout": "إدارة سجلات",
            "components": ["شريط بحث", "قائمة القضايا", "بيانات القضية", "حالة القضية"],
            "fields": ["رقم القضية", "المحكمة", "الدائرة", "الحالة", "ملاحظات"],
            "actions": ["إضافة", "تعديل", "عرض", "حذف", "بحث"],
        },
        "clients": {
            "layout": "إدارة سجلات",
            "components": ["شريط بحث", "قائمة الموكلين", "بطاقة الموكل"],
            "fields": ["الاسم", "رقم الهاتف", "البريد", "الحالة"],
            "actions": ["إضافة", "تعديل", "عرض", "حذف", "بحث"],
        },
        "sessions": {
            "layout": "جدول مواعيد",
            "components": ["التقويم", "قائمة المواعيد", "تفاصيل الموعد"],
            "fields": ["التاريخ", "الوقت", "الموضوع", "الحالة"],
            "actions": ["حجز", "تعديل", "إلغاء", "فتح"],
        },
        "documents": {
            "layout": "مكتبة ملفات",
            "components": ["شريط بحث", "قائمة المستندات", "رفع ملف", "تفاصيل المستند"],
            "fields": ["اسم المستند", "نوع الملف", "الوصف"],
            "actions": ["رفع", "فتح", "تحميل", "حذف", "بحث"],
        },
        "products": {
            "layout": "كتالوج",
            "components": ["بحث", "بطاقات المنتجات", "تفاصيل المنتج"],
            "fields": ["اسم المنتج", "السعر", "الكمية", "الوصف"],
            "actions": ["إضافة", "تعديل", "عرض", "حذف", "بحث"],
        },
        "students": {
            "layout": "إدارة سجلات",
            "components": ["بحث", "قائمة الطلاب", "بطاقة الطالب"],
            "fields": ["الاسم", "الصف", "رقم الطالب", "الحالة"],
            "actions": ["إضافة", "تعديل", "عرض", "حذف", "بحث"],
        },
        "courses": {
            "layout": "كتالوج تعليمي",
            "components": ["قائمة الدورات", "تفاصيل الدورة", "بحث"],
            "fields": ["اسم الدورة", "الوصف", "المدرس", "الحالة"],
            "actions": ["إضافة", "تعديل", "عرض", "بحث"],
        },
    }

    def analyze(self, screen, requirements=None):
        requirements = requirements or {}

        screen_id = screen.get("id", "screen")
        base = self.SCREEN_RULES.get(
            screen_id,
            {
                "layout": "واجهة قياسية متجاوبة",
                "components": ["العنوان", "المحتوى", "الإجراءات"],
                "fields": [],
                "actions": ["عرض", "إضافة", "تعديل"],
            }
        )

        capabilities = set(requirements.get("capabilities", []))
        roles = list(requirements.get("roles", ["user"]))

        if screen_id == "home":
            needed = {"dashboard"}
        elif screen_id in {"chat", "camera", "microphone", "attachments"}:
            needed = {screen_id}
        else:
            needed = {"database", "crud"}

        if "search" in capabilities and screen_id not in {"camera", "microphone"}:
            if "بحث" not in base["actions"]:
                base = dict(base)
                base["actions"] = list(base["actions"]) + ["بحث"]

        if "files" in capabilities and screen_id in {"chat", "cases", "documents"}:
            if "إرفاق ملف" not in base["actions"] and "رفع" not in base["actions"]:
                base = dict(base)
                base["actions"] = list(base["actions"]) + ["إرفاق ملف"]

        screen_capabilities = sorted(
            needed.intersection(capabilities)
            or needed
        )

        if screen_id == "home" and "dashboard" not in capabilities:
            screen_capabilities = ["database"]

        navigation = {
            "from": ["home"] if screen_id != "home" else [],
            "to": []
        }

        if screen_id != "home":
            navigation["to"].append("home")

        return {
            "screen_id": screen_id,
            "title": screen.get("title", "شاشة جديدة"),
            "purpose": screen.get("purpose", "واجهة البرنامج"),
            "layout": base["layout"],
            "components": list(base["components"]),
            "fields": list(base["fields"]),
            "actions": list(base["actions"]),
            "roles": roles,
            "capabilities": screen_capabilities,
            "navigation": navigation,
        }


class ScreenProposalEngine:

    def __init__(self, requirements=None):
        self.requirements = requirements or {}
        self.intelligence = ScreenIntelligenceEngine()

    def proposals(self, screen, offset=0):

        intelligent = self.intelligence.analyze(
            screen,
            self.requirements
        )

        layouts = [
            ("بطاقات", ["العنوان", "بطاقات الوظائف", "شريط التنقل"]),
            ("لوحة تحكم", ["العنوان", "إحصائيات", "أزرار رئيسية", "قائمة"]),
            ("قائمة مركزة", ["العنوان", "قائمة الوظائف", "زر إجراء رئيسي"]),
            ("واجهة جانبية", ["قائمة جانبية", "منطقة محتوى", "زر رئيسي"]),
            ("واجهة كبيرة", ["عنوان كبير", "إجراءات رئيسية", "محتوى"]),
            ("واجهة مختصرة", ["عنوان", "أزرار كبيرة", "معلومات مختصرة"]),
        ]

        result = []

        for i in range(3):
            index = (offset + i) % len(layouts)

            fallback_layout, fallback_components = layouts[index]

            layout = (
                intelligent["layout"]
                if i == 0
                else fallback_layout
            )

            components = (
                intelligent["components"]
                if i == 0
                else fallback_components
            )

            proposal = ScreenProposal(
                screen_id=screen["id"],
                title=screen["title"],
                purpose=screen["purpose"],
                variant=i + 1,
                layout=layout,
                components=components
            )

            data = asdict(proposal)
            data.update({
                "fields": intelligent["fields"],
                "actions": intelligent["actions"],
                "roles": intelligent["roles"],
                "capabilities": intelligent["capabilities"],
                "navigation": intelligent["navigation"],
            })

            result.append(data)

        return result


class ScreenApprovalWizard:

    def __init__(self):
        self.engine = ScreenProposalEngine()

    def display(self, proposal):

        print("\n" + "─" * 60)

        print(
            f"التصميم رقم {proposal.variant}"
        )

        print(
            f"الشاشة: {proposal.title}"
        )

        print(
            f"الغرض: {proposal.purpose}"
        )

        print(
            f"النمط: {proposal.layout}"
        )

        print(
            "العناصر: " +
            " • ".join(proposal.components)
        )

        print("─" * 60)

    def choose(self, screen):

        offset = 0

        while True:

            proposals = self.engine.proposals(
                screen,
                offset
            )

            print(
                "\n╔══════════════════════════════════════╗"
            )

            print(
                f"  اقتراحات شاشة: {screen['title']}"
            )

            print(
                "╚══════════════════════════════════════╝"
            )

            for proposal in proposals:
                self.display(proposal)

            print("""
1 - اختيار التصميم الأول
2 - اختيار التصميم الثاني
3 - اختيار التصميم الثالث
4 - عرض تصميمات أخرى
5 - تعديل الشاشة
6 - رفض الشاشة
""")

            choice = input("اختيارك: ").strip()

            if choice in ("1", "2", "3"):

                selected = proposals[
                    int(choice) - 1
                ]

                selected.approved = True

                return asdict(selected)

            if choice == "4":

                offset += 3

                continue

            if choice == "5":

                change = input(
                    "ما التعديل المطلوب؟ "
                ).strip()

                if change:

                    screen = dict(screen)

                    screen["purpose"] += (
                        " — تعديل المستخدم: "
                        + change
                    )

                continue

            if choice == "6":

                return None

            print("[-] اختيار غير صحيح.")



class DatabaseEngine:

    TABLE_RULES = {
        "users": {
            "columns": [
                ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                ("name", "TEXT NOT NULL"),
                ("email", "TEXT"),
                ("phone", "TEXT"),
                ("password_hash", "TEXT"),
                ("created_at", "TEXT NOT NULL")
            ]
        },
        "roles": {
            "columns": [
                ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                ("name", "TEXT NOT NULL UNIQUE")
            ]
        },
        "user_roles": {
            "columns": [
                ("user_id", "INTEGER NOT NULL"),
                ("role_id", "INTEGER NOT NULL")
            ]
        },
        "clients": {
            "columns": [
                ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                ("name", "TEXT NOT NULL"),
                ("phone", "TEXT"),
                ("email", "TEXT"),
                ("status", "TEXT"),
                ("created_at", "TEXT NOT NULL")
            ]
        },
        "lawyers": {
            "columns": [
                ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                ("name", "TEXT NOT NULL"),
                ("phone", "TEXT"),
                ("email", "TEXT"),
                ("created_at", "TEXT NOT NULL")
            ]
        },
        "cases": {
            "columns": [
                ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                ("case_number", "TEXT"),
                ("court", "TEXT"),
                ("chamber", "TEXT"),
                ("status", "TEXT"),
                ("notes", "TEXT"),
                ("client_id", "INTEGER"),
                ("lawyer_id", "INTEGER"),
                ("created_at", "TEXT NOT NULL")
            ]
        },
        "appointments": {
            "columns": [
                ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                ("title", "TEXT NOT NULL"),
                ("appointment_date", "TEXT NOT NULL"),
                ("status", "TEXT"),
                ("user_id", "INTEGER"),
                ("created_at", "TEXT NOT NULL")
            ]
        },
        "documents": {
            "columns": [
                ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                ("name", "TEXT NOT NULL"),
                ("file_path", "TEXT NOT NULL"),
                ("mime_type", "TEXT"),
                ("case_id", "INTEGER"),
                ("uploaded_by", "INTEGER"),
                ("created_at", "TEXT NOT NULL")
            ]
        },
        "messages": {
            "columns": [
                ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                ("sender_id", "INTEGER"),
                ("receiver_id", "INTEGER"),
                ("message", "TEXT"),
                ("created_at", "TEXT NOT NULL")
            ]
        },
        "translations": {
            "columns": [
                ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                ("document_id", "INTEGER"),
                ("source_text", "TEXT"),
                ("source_language", "TEXT"),
                ("target_language", "TEXT"),
                ("translated_text", "TEXT"),
                ("created_at", "TEXT NOT NULL")
            ]
        },
        "document_text": {
            "columns": [
                ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                ("document_id", "INTEGER NOT NULL"),
                ("extracted_text", "TEXT"),
                ("extraction_method", "TEXT"),
                ("detected_language", "TEXT"),
                ("created_at", "TEXT NOT NULL")
            ]
        },
        "audio_transcriptions": {
            "columns": [
                ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                ("file_path", "TEXT"),
                ("transcription_text", "TEXT"),
                ("detected_language", "TEXT"),
                ("created_at", "TEXT NOT NULL")
            ]
        },
        "audio_outputs": {
            "columns": [
                ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                ("source_text", "TEXT"),
                ("language", "TEXT"),
                ("audio_path", "TEXT"),
                ("created_at", "TEXT NOT NULL")
            ]
        },
        "notifications": {
            "columns": [
                ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                ("user_id", "INTEGER"),
                ("title", "TEXT NOT NULL"),
                ("message", "TEXT"),
                ("is_read", "INTEGER NOT NULL DEFAULT 0"),
                ("created_at", "TEXT NOT NULL")
            ]
        },
        "products": {
            "columns": [
                ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                ("name", "TEXT NOT NULL"),
                ("price", "REAL NOT NULL DEFAULT 0"),
                ("quantity", "INTEGER NOT NULL DEFAULT 0"),
                ("description", "TEXT"),
                ("created_at", "TEXT NOT NULL")
            ]
        },
        "orders": {
            "columns": [
                ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                ("user_id", "INTEGER"),
                ("total", "REAL NOT NULL DEFAULT 0"),
                ("status", "TEXT"),
                ("created_at", "TEXT NOT NULL")
            ]
        },
        "courses": {
            "columns": [
                ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                ("name", "TEXT NOT NULL"),
                ("description", "TEXT"),
                ("teacher_id", "INTEGER"),
                ("status", "TEXT"),
                ("created_at", "TEXT NOT NULL")
            ]
        },
        "students": {
            "columns": [
                ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                ("name", "TEXT NOT NULL"),
                ("student_number", "TEXT"),
                ("class_name", "TEXT"),
                ("status", "TEXT"),
                ("created_at", "TEXT NOT NULL")
            ]
        },
        "reports": {
            "columns": [
                ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                ("title", "TEXT NOT NULL"),
                ("report_type", "TEXT"),
                ("created_at", "TEXT NOT NULL")
            ]
        },
        "audit_logs": {
            "columns": [
                ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
                ("user_id", "INTEGER"),
                ("action", "TEXT NOT NULL"),
                ("target", "TEXT"),
                ("created_at", "TEXT NOT NULL")
            ]
        }
    }

    DOMAIN_TABLES = {
        "legal": ["clients", "lawyers", "cases", "documents"],
        "commerce": ["products", "orders"],
        "education": ["courses", "students"],
        "crm": ["clients"],
        "booking": ["appointments"],
        "finance": ["orders", "reports"],
        "project_management": ["reports"],
        "support": ["tickets"],
        "logistics": ["orders"],
    }

    CAPABILITY_TABLES = {
        "translation": ["translations"],
        "document_processing": ["documents"],
        "ocr": ["document_text"],
        "speech_to_text": ["audio_transcriptions"],
        "text_to_speech": ["audio_outputs"],
        "auth": ["users", "roles", "user_roles"],
        "users": ["users"],
        "roles": ["roles", "user_roles"],
        "chat": ["messages"],
        "files": ["documents"],
        "notifications": ["notifications"],
        "reports": ["reports"],
        "audit": ["audit_logs"],
        "scheduling": ["appointments"],
    }

    def analyze(self, requirements):
        tables = {"users"}

        for domain in requirements.get("app_types", []):
            tables.update(self.DOMAIN_TABLES.get(domain, []))

        for capability in requirements.get("capabilities", []):
            tables.update(self.CAPABILITY_TABLES.get(capability, []))

        roles = requirements.get("roles", [])

        if roles:
            tables.update({"roles", "user_roles"})

        # العلاقات المشتركة المطلوبة عند وجودها
        if "cases" in tables:
            tables.update({"clients", "lawyers"})

        if "documents" in tables and "cases" in tables:
            tables.add("documents")

        # خدمات المستندات والترجمة والصوت
        if "translation" in requirements.get("capabilities", []):
            tables.add("translations")

        if "document_processing" in requirements.get("capabilities", []):
            tables.add("documents")

        if "ocr" in requirements.get("capabilities", []):
            tables.add("document_text")

        if "speech_to_text" in requirements.get("capabilities", []):
            tables.add("audio_transcriptions")

        if "text_to_speech" in requirements.get("capabilities", []):
            tables.add("audio_outputs")

        return sorted(
            table for table in tables
            if table in self.TABLE_RULES
        )

    def schema(self, requirements):
        tables = self.analyze(requirements)
        statements = [
            "PRAGMA foreign_keys = ON;"
        ]

        for table in tables:
            columns = self.TABLE_RULES[table]["columns"]
            column_sql = ",\n    ".join(
                f"{name} {definition}"
                for name, definition in columns
            )

            statements.append(
                f"CREATE TABLE IF NOT EXISTS {table} (\n"
                f"    {column_sql}\n"
                f");"
            )

        if "user_roles" in tables:
            statements.append(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "idx_user_roles_unique "
                "ON user_roles(user_id, role_id);"
            )

        if "cases" in tables:
            statements.extend([
                "CREATE INDEX IF NOT EXISTS idx_cases_client "
                "ON cases(client_id);",
                "CREATE INDEX IF NOT EXISTS idx_cases_lawyer "
                "ON cases(lawyer_id);"
            ])

        if "messages" in tables:
            statements.append(
                "CREATE INDEX IF NOT EXISTS idx_messages_users "
                "ON messages(sender_id, receiver_id);"
            )

        return "\n\n".join(statements) + "\n"

class ProjectGenerator:

    def __init__(self, root):
        self.root = Path(root)

    @staticmethod
    def safe_name(text):

        text = re.sub(
            r"[^\w\u0600-\u06FF -]+",
            "",
            text,
            flags=re.UNICODE
        )

        text = re.sub(
            r"\s+",
            "-",
            text.strip()
        )

        return text[:80] or "abqaryno-project"

    def generate(
        self,
        idea,
        requirements,
        approved_screens,
        options=None
    ):

        name = self.safe_name(idea)

        options = options or []

        target = self.root / name

        public = target / "public"

        public.mkdir(
            parents=True,
            exist_ok=True
        )

        # إنشاء البنية الأساسية للمشروع الناتج
        project_dirs = [
            target / "server",
            target / "routes",
            target / "services",
            target / "database",
            target / "uploads",
            public / "css",
            public / "js",
        ]

        for directory in project_dirs:
            directory.mkdir(
                parents=True,
                exist_ok=True
            )

        cards = []

        for screen in approved_screens:

            cards.append(
                f"""
<section class="screen">
<h2>{html.escape(screen["title"])}</h2>
<p>{html.escape(screen["purpose"])}</p>
<strong>
التصميم: {html.escape(screen.get("layout", "واجهة قياسية متجاوبة"))}
</strong>
</section>
"""
            )

        page = f"""<!doctype html>
<html lang="ar" dir="rtl">

<head>

<meta charset="utf-8">

<meta name="viewport"
content="width=device-width,initial-scale=1">

<title>{html.escape(idea)}</title>

<style>

body {{
    margin: 0;
    background: #101010;
    color: #f5d76e;
    font-family: Tahoma, Arial;
}}

header {{
    padding: 30px;
    text-align: center;
    border-bottom: 1px solid #66551c;
}}

main {{
    max-width: 1100px;
    margin: auto;
    padding: 25px;
    display: grid;
    grid-template-columns:
        repeat(auto-fit,minmax(260px,1fr));
    gap: 20px;
}}

.screen {{
    background: #1d1d1d;
    border: 1px solid #806b24;
    border-radius: 18px;
    padding: 25px;
}}

</style>

<link rel="stylesheet" href="/css/style.css">\n</head>

<body>

<header>

<div class="brand-logo-wrap">
    <button
        id="logo-button"
        class="logo-button"
        type="button"
        title="تغيير اللوجو"
        aria-label="تغيير اللوجو"
    >
        <span id="logo-placeholder" class="logo-placeholder">👤</span>
        <img id="app-logo" class="logo-image" alt="لوجو البرنامج">
    </button>

    <input
        id="logo-input"
        type="file"
        accept="image/*"
        hidden
    >

    <div class="logo-actions">
        <button id="logo-change" type="button">تغيير اللوجو</button>
        <button id="logo-remove" type="button">حذف اللوجو</button>
    </div>
</div>

<h1>{html.escape(idea)}</h1>

<p>
تم تصميم المشروع واعتماد شاشاته بواسطة عبقرينو
</p>

</header>

<main>

{''.join(cards)}

</main>

</body>

</html>
"""

        # واجهة تشغيل الوظائف المعتمدة
        tools_ui = """
<section id="abqaryno-tools" class="tools-panel">

    <div class="tool-card" id="chat-tool">
        <h2>💬 المحادثة</h2>
        <div id="chat-messages" class="chat-messages"></div>
        <div class="chat-input-row">
            <input id="chat-input" type="text" placeholder="اكتب رسالتك...">
            <button id="chat-send">إرسال</button>
        </div>
    </div>

    <div class="tool-card" id="camera-tool">
        <h2>📷 الكاميرا</h2>
        <video id="camera-preview" autoplay playsinline muted></video>
        <div class="tool-actions">
            <button id="camera-start">تشغيل الكاميرا</button>
            <button id="camera-stop">إيقاف الكاميرا</button>
        </div>
    </div>

    <div class="tool-card" id="microphone-tool">
        <h2>🎙️ المايك والتسجيل</h2>
        <div class="tool-actions">
            <button id="mic-start">تشغيل المايك</button>
            <button id="mic-record">بدء التسجيل</button>
            <button id="mic-stop">إيقاف التسجيل</button>
        </div>
        <audio id="recorded-audio" controls hidden></audio>
    </div>

    <div class="tool-card" id="attachments-tool">
        <h2>📎 المرفقات</h2>
        <input id="attachment-input" type="file" multiple>
        <div id="attachment-list"></div>
    </div>

</section>
"""

        page = page.replace(
            "</main>",
            tools_ui + "\n</main>",
            1
        )

        # تشغيل الوظائف التفاعلية
        interactive_script = """
<script>
document.addEventListener("DOMContentLoaded", () => {

    // لوجو البرنامج: اختيار وتغيير وحذف وحفظ محلي
    const logoButton = document.getElementById("logo-button");
    const logoInput = document.getElementById("logo-input");
    const logoImage = document.getElementById("app-logo");
    const logoPlaceholder = document.getElementById("logo-placeholder");
    const logoChange = document.getElementById("logo-change");
    const logoRemove = document.getElementById("logo-remove");
    const logoStorageKey = "abqarynoLogo";

    function renderLogo(value) {
        if (value) {
            logoImage.src = value;
            logoImage.style.display = "block";
            logoPlaceholder.style.display = "none";
        } else {
            logoImage.removeAttribute("src");
            logoImage.style.display = "none";
            logoPlaceholder.style.display = "inline";
        }
    }

    function openLogoPicker() {
        if (logoInput) {
            logoInput.click();
        }
    }

    renderLogo(localStorage.getItem(logoStorageKey));

    if (logoButton) {
        logoButton.addEventListener("click", openLogoPicker);
    }

    if (logoChange) {
        logoChange.addEventListener("click", openLogoPicker);
    }

    if (logoInput) {
        logoInput.addEventListener("change", event => {
            const file = event.target.files && event.target.files[0];

            if (!file) return;

            if (!file.type.startsWith("image/")) {
                alert("من فضلك اختر صورة فقط.");
                return;
            }

            const reader = new FileReader();

            reader.onload = () => {
                const value = reader.result;
                localStorage.setItem(logoStorageKey, value);
                renderLogo(value);
            };

            reader.readAsDataURL(file);
        });
    }

    if (logoRemove) {
        logoRemove.addEventListener("click", () => {
            localStorage.removeItem(logoStorageKey);
            renderLogo(null);

            if (logoInput) {
                logoInput.value = "";
            }
        });
    }

    const chatInput = document.getElementById("chat-input");
    const chatSend = document.getElementById("chat-send");
    const chatMessages = document.getElementById("chat-messages");

    if (window.abqarynoChat && chatInput && chatSend) {
        chatSend.addEventListener("click", () => {
            const item = window.abqarynoChat.send(chatInput.value);

            if (!item) return;

            const message = document.createElement("div");
            message.className = "chat-message";
            message.textContent = item.text;

            chatMessages.appendChild(message);
            chatInput.value = "";
            chatInput.focus();
        });

        chatInput.addEventListener("keydown", event => {
            if (event.key === "Enter") {
                chatSend.click();
            }
        });
    }

    const video = document.getElementById("camera-preview");
    const cameraStart = document.getElementById("camera-start");
    const cameraStop = document.getElementById("camera-stop");

    const camera = window.AbqarynoCamera
        ? new window.AbqarynoCamera()
        : null;

    if (camera && cameraStart) {
        cameraStart.addEventListener("click", async () => {
            try {
                await camera.start(video);
            } catch (error) {
                alert("تعذر تشغيل الكاميرا: " + error.message);
            }
        });
    }

    if (camera && cameraStop) {
        cameraStop.addEventListener("click", () => camera.stop());
    }

    const micStart = document.getElementById("mic-start");
    const micRecord = document.getElementById("mic-record");
    const micStop = document.getElementById("mic-stop");
    const recordedAudio = document.getElementById("recorded-audio");

    const microphone = window.AbqarynoMicrophone
        ? new window.AbqarynoMicrophone()
        : null;

    if (microphone && micStart) {
        micStart.addEventListener("click", async () => {
            try {
                await microphone.start();
            } catch (error) {
                alert("تعذر تشغيل المايك: " + error.message);
            }
        });
    }

    if (microphone && micRecord) {
        micRecord.addEventListener("click", () => {
            try {
                microphone.record();
            } catch (error) {
                alert(error.message);
            }
        });
    }

    if (microphone && micStop) {
        micStop.addEventListener("click", async () => {
            const blob = await microphone.stopRecording();

            if (!blob || !recordedAudio) return;

            recordedAudio.src = URL.createObjectURL(blob);
            recordedAudio.hidden = false;
        });
    }

    const attachmentInput =
        document.getElementById("attachment-input");

    const attachmentList =
        document.getElementById("attachment-list");

    if (window.abqarynoAttachments && attachmentInput) {
        attachmentInput.addEventListener("change", event => {

            const files =
                window.abqarynoAttachments.add(
                    event.target.files
                );

            attachmentList.innerHTML = "";

            files.forEach(file => {
                const item = document.createElement("div");

                item.className = "attachment-item";
                item.textContent =
                    file.name +
                    " (" +
                    Math.round(file.size / 1024) +
                    " KB)";

                attachmentList.appendChild(item);
            });
        });
    }
});
</script>
"""

        # المساعد الذكي السياقي للبرنامج الناتج
        assistant_ui = """
<style>
#abqaryno-assistant .assistant-action-confirmation {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    margin: 10px 0;
    padding: 10px;
    border: 1px solid rgba(255, 193, 7, 0.35);
    border-radius: 10px;
}

#abqaryno-assistant .assistant-action-confirmation button {
    border: 0;
    border-radius: 8px;
    padding: 8px 14px;
    cursor: pointer;
    font: inherit;
}

#abqaryno-assistant .assistant-action-confirmation button:first-child {
    background: #198754;
    color: #fff;
}

#abqaryno-assistant .assistant-action-confirmation button:nth-child(2) {
    background: #6c757d;
    color: #fff;
}

#abqaryno-assistant .assistant-action-confirmation button:disabled {
    opacity: 0.55;
    cursor: not-allowed;
}

#abqaryno-assistant .assistant-action-status {
    font-size: 0.9em;
    opacity: 0.8;
}
</style>

<section id="abqaryno-assistant" class="assistant-panel">
    <div class="assistant-header">
        <div>
            <h2>🧠 المساعد الذكي</h2>
            <p id="assistant-context-label">
                يفهم البرنامج والشاشة الحالية ويساعدك أثناء الاستخدام.
            </p>
        </div>
        <button
            id="assistant-clear"
            type="button"
            aria-label="مسح محادثة المساعد"
        >
            مسح
        </button>
    </div>

    <div
        id="assistant-messages"
        class="assistant-messages"
        aria-live="polite"
    ></div>

    <div class="assistant-input-row">
        <input
            id="assistant-input"
            type="text"
            placeholder="اسأل المساعد عن البرنامج أو الشاشة الحالية..."
            autocomplete="off"
        >
        <button id="assistant-send" type="button">
            إرسال
        </button>
    </div>

    <div class="assistant-suggestions">
        <button type="button" data-assistant-question="ماذا يمكنني أن أفعل هنا؟">
            ماذا أفعل هنا؟
        </button>
        <button type="button" data-assistant-question="ما الشاشات الموجودة في البرنامج؟">
            الشاشات
        </button>
        <button type="button" data-assistant-question="ما الوظائف المتاحة؟">
            الوظائف
        </button>
    </div>
</section>

<script src="/js/assistant.js"></script>
"""

        page = page.replace(
            "</main>",
            assistant_ui + "\n</main>",
            1
        )

        page = page.replace(
            "</body>",
            interactive_script + "\n</body>",
            1
        )

        (public / "index.html").write_text(
            page,
            encoding="utf-8"
        )

        assistant_context = {
            "idea": idea,
            "screens": approved_screens,
            "roles": requirements.get("roles", []),
            "capabilities": requirements.get("capabilities", []),
            "capability_labels": requirements.get(
                "capability_labels",
                {}
            ),
            "app_types": requirements.get("app_types", []),
            "options": options
        }

        (public / "assistant-context.json").write_text(
            json.dumps(
                assistant_context,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

        assistant_js = r"""
(() => {
    "use strict";

    const state = {
        context: null,
        messages: []
    };

    const $ = id => document.getElementById(id);

    function addMessage(text, type) {
        const container = $("assistant-messages");
        if (!container) return;

        const item = document.createElement("div");
        item.className = "assistant-message " + type;
        item.textContent = text;
        container.appendChild(item);

        container.scrollTop = container.scrollHeight;
        state.messages.push({text, type});
    }

    function capabilityLabel(key) {
        const labels =
            state.context &&
            state.context.capability_labels;

        return (labels && labels[key]) || key;
    }

    function currentScreen() {
        const screens =
            state.context && state.context.screens;

        if (!Array.isArray(screens) || !screens.length) {
            return null;
        }

        const visible = Array.from(
            document.querySelectorAll(".screen")
        );

        if (visible.length) {
            const index = Math.min(
                Math.max(
                    window.scrollY > 20 ? 1 : 0,
                    0
                ),
                screens.length - 1
            );

            return screens[index] || screens[0];
        }

        return screens[0];
    }

    function answer(question) {
        const q = String(question || "").trim().toLowerCase();

        if (!state.context) {
            return "المساعد ما زال يحمّل معلومات البرنامج. حاول مرة أخرى.";
        }

        const screen = currentScreen();
        const screens = Array.isArray(state.context.screens)
            ? state.context.screens
            : [];

        const capabilities = Array.isArray(state.context.capabilities)
            ? state.context.capabilities
            : [];

        if (
            q.includes("ماذا") &&
            (q.includes("أفعل") || q.includes("هنا"))
        ) {
            if (screen) {
                return (
                    "أنت الآن في شاشة " +
                    (screen.title || "الحالية") +
                    ". " +
                    (screen.purpose || "يمكنك استخدام الوظائف المتاحة في هذه الشاشة.") +
                    (
                        Array.isArray(screen.actions) &&
                        screen.actions.length
                            ? " الإجراءات المتاحة: " +
                              screen.actions.join("، ") +
                              "."
                            : ""
                    )
                );
            }

            return "يمكنك استخدام الشاشات والوظائف التي أنشأها البرنامج حسب صلاحياتك.";
        }

        if (
            q.includes("الشاشات") ||
            q.includes("شاشة") ||
            q.includes("الصفحات")
        ) {
            if (!screens.length) {
                return "لم يتم اعتماد شاشات إضافية لهذا البرنامج.";
            }

            return (
                "الشاشات المعتمدة: " +
                screens
                    .map(item => item.title || item.id)
                    .filter(Boolean)
                    .join("، ") +
                "."
            );
        }

        if (
            q.includes("الوظائف") ||
            q.includes("القدرات") ||
            q.includes("ماذا يمكن")
        ) {
            if (!capabilities.length) {
                return "لم يتم تسجيل قدرات إضافية لهذا البرنامج.";
            }

            return (
                "الوظائف المتاحة تشمل: " +
                capabilities
                    .map(capabilityLabel)
                    .join("، ") +
                "."
            );
        }

        if (
            q.includes("ترجم") ||
            q.includes("ترجمة")
        ) {
            if (capabilities.includes("translation")) {
                return "البرنامج يدعم الترجمة. استخدم وظيفة المستندات أو الترجمة المتاحة في الشاشة المناسبة.";
            }

            return "ميزة الترجمة غير مفعلة في هذا البرنامج.";
        }

        if (
            q.includes("مستند") ||
            q.includes("pdf") ||
            q.includes("word")
        ) {
            if (
                capabilities.includes("document_processing") ||
                capabilities.includes("files")
            ) {
                return "البرنامج يحتوي على قدرات للتعامل مع المستندات والملفات. يمكنك اختيار الملف من وظيفة المرفقات أو المستندات.";
            }

            return "لا توجد قدرة مستندات مسجلة لهذا البرنامج.";
        }

        if (
            q.includes("صوت") ||
            q.includes("تسجيل")
        ) {
            if (
                capabilities.includes("microphone") ||
                capabilities.includes("speech_to_text") ||
                capabilities.includes("text_to_speech")
            ) {
                return "البرنامج يحتوي على وظائف صوتية مفعلة، ويمكن استخدامها حسب الأدوات الموجودة في الشاشة.";
            }

            return "الوظائف الصوتية غير مفعلة في هذا البرنامج.";
        }

        if (
            q.includes("من أنت") ||
            q.includes("المساعد")
        ) {
            return "أنا المساعد الذكي المدمج في هذا البرنامج. أقرأ سياق البرنامج والشاشات والقدرات لمساعدتك أثناء الاستخدام.";
        }

        return (
            "أفهم سؤالك. أستطيع مساعدتك في التنقل وفهم الشاشات والوظائف والمستندات والقدرات المتاحة. " +
            "جرّب السؤال عن الشاشة الحالية أو الوظائف المتاحة."
        );
    }

    async function send(question) {
        const input = $("assistant-input");
        const value = String(
            question !== undefined
                ? question
                : input && input.value
        ).trim();

        if (!value) return;

        addMessage(value, "user");

        if (input) {
            input.value = "";
        }

        try {
            const screen = currentScreen() || {};

            const response = await fetch("/api/assistant", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    prompt: value,
                    idea: state.context && state.context.idea
                        ? state.context.idea
                        : "",
                    requirements: state.context || {},
                    screen: screen,
                    user: {}
                })
            });

            if (!response.ok) {
                throw new Error("تعذر الاتصال بالمساعد الذكي");
            }

            const result = await response.json();

            if (!result.ok) {
                throw new Error(
                    result.error || "تعذر معالجة طلب المساعد"
                );
            }

            addMessage(
                result.answer || "تم تحليل طلبك.",
                "assistant"
            );

            if (Array.isArray(result.actions) && result.actions.length) {
                result.actions.forEach(action => {
                    const needsConfirmation =
                        Boolean(action.requires_confirmation);

                    const suffix = needsConfirmation
                        ? " — يحتاج إلى تأكيدك قبل التنفيذ."
                        : "";

                    addMessage(
                        "اقتراح: " +
                        (action.title || action.action_id || "إجراء") +
                        suffix,
                        "assistant"
                    );

                    if (needsConfirmation) {
                        addConfirmationControls(action);
                    }
                });
            }
        } catch (error) {
            addMessage(
                "تعذر الاتصال بالمساعد الذكي حاليًا. " +
                "جرّب مرة أخرى.",
                "assistant"
            );
        }
    }

    function addConfirmationControls(action) {
        const container = $("assistant-messages");
        if (!container) return;

        const wrapper = document.createElement("div");
        wrapper.className = "assistant-action-confirmation";

        const confirmButton = document.createElement("button");
        confirmButton.type = "button";
        confirmButton.textContent = "تأكيد التنفيذ";

        const cancelButton = document.createElement("button");
        cancelButton.type = "button";
        cancelButton.textContent = "إلغاء";

        const status = document.createElement("span");
        status.className = "assistant-action-status";
        status.textContent = "بانتظار تأكيدك";

        const setDisabled = () => {
            confirmButton.disabled = true;
            cancelButton.disabled = true;
        };

        const confirm = async confirmed => {
            setDisabled();
            status.textContent = "جارٍ معالجة التأكيد...";

            try {
                const response = await fetch(
                    "/api/assistant/confirm",
                    {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            confirmed,
                            action: {
                                action_id: action.action_id || "",
                                title: action.title || "",
                                description: action.description || "",
                                requires_confirmation:
                                    Boolean(action.requires_confirmation),
                                status: action.status || "proposed"
                            }
                        })
                    }
                );

                if (!response.ok) {
                    throw new Error("تعذر إرسال التأكيد");
                }

                const result = await response.json();

                if (!result.ok) {
                    throw new Error(
                        result.error || "تعذر معالجة التأكيد"
                    );
                }

                const finalStatus =
                    result.action && result.action.status
                        ? result.action.status
                        : (confirmed ? "approved" : "cancelled");

                status.textContent =
                    finalStatus === "approved"
                        ? "تم تأكيد الإجراء."
                        : "تم إلغاء الإجراء.";

                if (finalStatus === "approved") {
                    addMessage(
                        "تم اعتماد الإجراء بعد تأكيدك.",
                        "assistant"
                    );
                } else {
                    addMessage(
                        "تم إلغاء الإجراء.",
                        "assistant"
                    );
                }
            } catch (error) {
                confirmButton.disabled = false;
                cancelButton.disabled = false;
                status.textContent =
                    "تعذر معالجة التأكيد. حاول مرة أخرى.";
            }
        };

        confirmButton.addEventListener(
            "click",
            () => confirm(true)
        );

        cancelButton.addEventListener(
            "click",
            () => confirm(false)
        );

        wrapper.appendChild(confirmButton);
        wrapper.appendChild(cancelButton);
        wrapper.appendChild(status);

        container.appendChild(wrapper);
        container.scrollTop = container.scrollHeight;
    }

    function clearMessages() {
        const container = $("assistant-messages");
        if (container) {
            container.innerHTML = "";
        }

        state.messages = [];

        addMessage(
            "مرحبًا. أنا المساعد الذكي للبرنامج. كيف أساعدك؟",
            "assistant"
        );
    }

    async function initialize() {
        try {
            const response = await fetch(
                "/assistant-context.json",
                {cache: "no-store"}
            );

            if (!response.ok) {
                throw new Error("تعذر تحميل سياق البرنامج");
            }

            state.context = await response.json();

            const label = $("assistant-context-label");

            if (label && state.context.idea) {
                label.textContent =
                    "المساعد يفهم برنامج: " +
                    state.context.idea;
            }

            addMessage(
                "مرحبًا. أنا المساعد الذكي للبرنامج. اسألني عن الشاشة الحالية أو الوظائف المتاحة.",
                "assistant"
            );
        } catch (error) {
            addMessage(
                "تعذر تحميل سياق البرنامج حاليًا.",
                "assistant"
            );
        }

        const input = $("assistant-input");
        const sendButton = $("assistant-send");
        const clearButton = $("assistant-clear");

        if (sendButton) {
            sendButton.addEventListener(
                "click",
                () => send()
            );
        }

        if (input) {
            input.addEventListener(
                "keydown",
                event => {
                    if (event.key === "Enter") {
                        event.preventDefault();
                        send();
                    }
                }
            );
        }

        if (clearButton) {
            clearButton.addEventListener(
                "click",
                clearMessages
            );
        }

        document
            .querySelectorAll("[data-assistant-question]")
            .forEach(button => {
                button.addEventListener(
                    "click",
                    () => send(
                        button.getAttribute(
                            "data-assistant-question"
                        )
                    )
                );
            });
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initialize,
            {once: true}
        );
    } else {
        initialize();
    }
})();
"""

        (public / "js" / "assistant.js").write_text(
            assistant_js,
            encoding="utf-8"
        )

        manifest = {
            "idea": idea,
            "created_at": now(),
            "requirements": requirements,
            "approved_screens": approved_screens,
            "options": options
        }

        (target / ".abqaryno-requirements.json").write_text(
            json.dumps(
                manifest,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

        # ملفات البنية الأساسية للمشروع الناتج
        (public / "css" / "style.css").write_text(
            """
* {
    box-sizing: border-box;
}

:root {
    --bg: #0b1020;
    --panel: #121a2e;
    --panel-2: #18233d;
    --border: rgba(255,255,255,.10);
    --text: #f5f7ff;
    --muted: #aeb8d0;
    --gold: #d9b45b;
    --gold-2: #f0d58a;
}

body {
    margin: 0;
    min-height: 100vh;
    background:
        radial-gradient(circle at top right, rgba(217,180,91,.12), transparent 30%),
        linear-gradient(145deg, #080c18, var(--bg));
    color: var(--text);
    font-family: Arial, "Noto Sans Arabic", sans-serif;
    direction: rtl;
}

header {
    padding: 28px 20px;
    text-align: center;
    border-bottom: 1px solid var(--border);
    background: rgba(10,15,30,.88);
}

header h1 {
    margin: 0 0 8px;
    font-size: clamp(24px, 5vw, 38px);
}

header p {
    margin: 0;
    color: var(--muted);
}

.brand-logo-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    margin-bottom: 18px;
}

.logo-button {
    width: 92px;
    height: 92px;
    padding: 0;
    border: 2px solid rgba(217,180,91,.55);
    border-radius: 50%;
    overflow: hidden;
    background: linear-gradient(145deg,#18233d,#0d1424);
    color: var(--gold-2);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 12px 30px rgba(0,0,0,.28);
}

.logo-button:hover {
    transform: scale(1.04);
    border-color: var(--gold-2);
}

.logo-placeholder {
    font-size: 38px;
}

.logo-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: none;
}

.logo-actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    justify-content: center;
}

.logo-actions button {
    border: 1px solid rgba(217,180,91,.35);
    border-radius: 10px;
    padding: 7px 12px;
    background: rgba(217,180,91,.10);
    color: var(--gold-2);
    cursor: pointer;
}

.logo-actions button:hover {
    background: rgba(217,180,91,.18);
}

@media (max-width: 600px) {
    .logo-button {
        width: 82px;
        height: 82px;
    }
}

main {
    width: min(1100px, calc(100% - 28px));
    margin: 28px auto 50px;
}

.screen {
    padding: 20px;
    margin-bottom: 16px;
    border: 1px solid var(--border);
    border-radius: 18px;
    background: rgba(18,26,46,.82);
    box-shadow: 0 12px 35px rgba(0,0,0,.20);
}

.screen h2 {
    margin-top: 0;
    color: var(--gold-2);
}

.tools-panel {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 18px;
    margin-top: 24px;
}

.tool-card {
    padding: 20px;
    border: 1px solid var(--border);
    border-radius: 20px;
    background: linear-gradient(160deg, rgba(24,35,61,.96), rgba(15,22,40,.96));
    box-shadow: 0 15px 40px rgba(0,0,0,.24);
}

.tool-card h2 {
    margin: 0 0 16px;
    color: var(--gold-2);
    font-size: 21px;
}

.chat-messages {
    min-height: 150px;
    max-height: 300px;
    overflow-y: auto;
    padding: 12px;
    margin-bottom: 12px;
    border: 1px solid var(--border);
    border-radius: 14px;
    background: rgba(0,0,0,.16);
}

.chat-message {
    width: fit-content;
    max-width: 85%;
    margin: 7px 0;
    padding: 10px 14px;
    border-radius: 14px;
    background: var(--panel-2);
    border: 1px solid var(--border);
    word-break: break-word;
}

.chat-input-row {
    display: flex;
    gap: 8px;
}

input[type="text"],
input[type="file"] {
    width: 100%;
    min-height: 46px;
    padding: 10px 13px;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: rgba(0,0,0,.22);
    color: var(--text);
    outline: none;
}

button {
    min-height: 44px;
    padding: 10px 16px;
    border: 1px solid rgba(217,180,91,.45);
    border-radius: 12px;
    background: linear-gradient(135deg, var(--gold), var(--gold-2));
    color: #15110a;
    font-weight: 700;
    cursor: pointer;
}

button:hover {
    filter: brightness(1.08);
}

.tool-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

#camera-preview {
    display: block;
    width: 100%;
    min-height: 220px;
    max-height: 420px;
    margin-bottom: 14px;
    object-fit: cover;
    border-radius: 16px;
    background: #050811;
    border: 1px solid var(--border);
}

#recorded-audio {
    width: 100%;
    margin-top: 16px;
}

#attachment-list {
    display: grid;
    gap: 8px;
    margin-top: 14px;
}

.attachment-item {
    padding: 11px 13px;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: rgba(0,0,0,.16);
    color: var(--muted);
    word-break: break-word;
}

@media (max-width: 760px) {
    main {
        width: min(100% - 18px, 680px);
    }

    .tools-panel {
        grid-template-columns: 1fr;
    }

    .chat-input-row {
        flex-direction: column;
    }

    .chat-input-row button {
        width: 100%;
    }

    .tool-actions button {
        flex: 1 1 140px;
    }
}
""",
            encoding="utf-8"
        )

        # ملف مواصفات المشروع الناتج
        (public / "project.json").write_text(
            json.dumps(
                {
                    "name": name,
                    "idea": idea,
                    "created_at": manifest["created_at"],
                    "features": requirements.get("features", []),
                    "screens": approved_screens,
                    "options": options
                },
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

        # ربط واجهة المشروع بالمواصفات المعتمدة
        (public / "js" / "app.js").write_text(
            """const AbqarynoAPI = {
    async request(path, options = {}) {
        const response = await fetch(path, {
            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {})
            },
            ...options
        });

        let data = {};
        try {
            data = await response.json();
        } catch (error) {
            data = {
                ok: false,
                error: "استجابة API غير صالحة."
            };
        }

        if (!response.ok) {
            const error = new Error(
                data.error || `HTTP ${response.status}`
            );
            error.status = response.status;
            error.data = data;
            throw error;
        }

        return data;
    },

    health() {
        return this.request("/api/health");
    },

    search(query, items = []) {
        return this.request("/api/search", {
            method: "POST",
            body: JSON.stringify({
                query,
                items
            })
        });
    },

    report(title, data = {}) {
        return this.request("/api/advanced_reports", {
            method: "POST",
            body: JSON.stringify({
                title,
                data
            })
        });
    },

    ocr(data = {}) {
        return this.request("/api/ocr", {
            method: "POST",
            body: JSON.stringify(data)
        });
    },

    translation(data = {}) {
        return this.request("/api/translation", {
            method: "POST",
            body: JSON.stringify(data)
        });
    },

    voice(data = {}) {
        return this.request("/api/voice", {
            method: "POST",
            body: JSON.stringify(data)
        });
    }
};

window.abqarynoAPI = AbqarynoAPI;

function optionIds(project) {
    return (project.options || [])
        .map(option => {
            if (typeof option === "string") {
                return option;
            }
            return option && option.option_id;
        })
        .filter(Boolean);
}

function createServicePanel(project) {
    const ids = optionIds(project);

    if (!ids.length) {
        return;
    }

    const main = document.querySelector("main");

    if (!main) {
        return;
    }

    if (document.getElementById("abqaryno-api-tools")) {
        return;
    }

    const panel = document.createElement("section");
    panel.id = "abqaryno-api-tools";
    panel.className = "tools-panel";

    panel.innerHTML = `
        <div class="tool-card">
            <h3>🔌 خدمات البرنامج</h3>
            <p>الخدمات التي تم اختيارها أثناء إنشاء المشروع.</p>
            <div id="abqaryno-api-status">جاري فحص الاتصال...</div>
        </div>
    `;

    if (ids.includes("search")) {
        const card = document.createElement("div");
        card.className = "tool-card";
        card.innerHTML = `
            <h3>🔎 البحث</h3>
            <input id="abqaryno-api-search-input"
                   type="text"
                   placeholder="اكتب عبارة البحث...">
            <button id="abqaryno-api-search-button" type="button">
                بحث
            </button>
            <div id="abqaryno-api-search-results"></div>
        `;
        panel.appendChild(card);
    }

    if (ids.includes("advanced_reports")) {
        const card = document.createElement("div");
        card.className = "tool-card";
        card.innerHTML = `
            <h3>📊 التقارير</h3>
            <input id="abqaryno-api-report-title"
                   type="text"
                   placeholder="عنوان التقرير">
            <button id="abqaryno-api-report-button" type="button">
                إنشاء تقرير
            </button>
            <div id="abqaryno-api-report-result"></div>
        `;
        panel.appendChild(card);
    }

    for (const [id, label] of [
        ["ocr", "📄 OCR"],
        ["translation", "🌐 الترجمة"],
        ["voice", "🎙️ الصوت"]
    ]) {
        if (!ids.includes(id)) {
            continue;
        }

        const card = document.createElement("div");
        card.className = "tool-card";
        card.innerHTML = `
            <h3>${label}</h3>
            <p>الخدمة موجودة في المشروع، لكن محركها غير موصل بعد.</p>
        `;
        panel.appendChild(card);
    }

    main.appendChild(panel);

    const searchButton = document.getElementById(
        "abqaryno-api-search-button"
    );

    if (searchButton) {
        searchButton.addEventListener("click", async () => {
            const input = document.getElementById(
                "abqaryno-api-search-input"
            );
            const output = document.getElementById(
                "abqaryno-api-search-results"
            );

            const query = String(
                input ? input.value : ""
            ).trim();

            if (!query) {
                output.textContent = "اكتب عبارة البحث أولًا.";
                return;
            }

            output.textContent = "جاري البحث...";

            try {
                const result = await AbqarynoAPI.search(
                    query,
                    []
                );

                output.textContent = (
                    result.results || []
                ).join("، ") || "لا توجد نتائج.";
            } catch (error) {
                output.textContent =
                    error.data?.error ||
                    error.message ||
                    "تعذر تنفيذ البحث.";
            }
        });
    }

    const reportButton = document.getElementById(
        "abqaryno-api-report-button"
    );

    if (reportButton) {
        reportButton.addEventListener("click", async () => {
            const input = document.getElementById(
                "abqaryno-api-report-title"
            );
            const output = document.getElementById(
                "abqaryno-api-report-result"
            );

            const title = String(
                input ? input.value : ""
            ).trim();

            if (!title) {
                output.textContent = "اكتب عنوان التقرير أولًا.";
                return;
            }

            output.textContent = "جاري إنشاء التقرير...";

            try {
                const result = await AbqarynoAPI.report(
                    title,
                    {}
                );

                output.textContent =
                    result.title || "تم إنشاء التقرير.";
            } catch (error) {
                output.textContent =
                    error.data?.error ||
                    error.message ||
                    "تعذر إنشاء التقرير.";
            }
        });
    }
}

async function loadProject() {
    try {
        const response = await fetch("/project.json");
        const project = await response.json();

        const container = document.querySelector("main");

        if (!container) {
            return;
        }

        container.dataset.project = project.name || "";

        createServicePanel(project);

        try {
            const health = await AbqarynoAPI.health();
            const status = document.getElementById(
                "abqaryno-api-status"
            );

            if (status) {
                status.textContent = health.ok
                    ? "متصل بخدمات البرنامج."
                    : "الخدمة غير متاحة.";
            }
        } catch (error) {
            const status = document.getElementById(
                "abqaryno-api-status"
            );

            if (status) {
                status.textContent =
                    "تعذر الاتصال بخدمات البرنامج.";
            }
        }

        console.log(
            "تم تحميل مشروع عبقرينو:",
            project.name
        );
    } catch (error) {
        console.error(
            "تعذر تحميل مواصفات المشروع:",
            error
        );
    }
}

document.addEventListener(
    "DOMContentLoaded",
    loadProject
);
""",
            encoding="utf-8"
        )

        # ============================================================
        # الوظائف الفعلية للمشروع الناتج
        # ============================================================

        js_dir = public / "js"

        (js_dir / "chat.js").write_text(
            """class AbqarynoChat {
    constructor() {
        this.messages = [];
    }

    send(message) {
        const text = String(message || "").trim();

        if (!text) {
            return null;
        }

        const item = {
            id: Date.now(),
            text,
            created_at: new Date().toISOString()
        };

        this.messages.push(item);

        document.dispatchEvent(
            new CustomEvent("abqaryno:message", {
                detail: item
            })
        );

        return item;
    }

    getMessages() {
        return [...this.messages];
    }
}

window.AbqarynoChat = AbqarynoChat;
window.abqarynoChat = new AbqarynoChat();
""",
            encoding="utf-8"
        )

        (js_dir / "camera.js").write_text(
            """class AbqarynoCamera {
    constructor() {
        this.stream = null;
    }

    async start(videoElement) {
        if (!navigator.mediaDevices?.getUserMedia) {
            throw new Error("الكاميرا غير مدعومة في هذا المتصفح");
        }

        this.stream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: false
        });

        if (videoElement) {
            videoElement.srcObject = this.stream;
            videoElement.autoplay = true;
            videoElement.playsInline = true;
        }

        return this.stream;
    }

    stop() {
        if (!this.stream) {
            return;
        }

        this.stream.getTracks().forEach(
            track => track.stop()
        );

        this.stream = null;
    }
}

window.AbqarynoCamera = AbqarynoCamera;
""",
            encoding="utf-8"
        )

        (js_dir / "microphone.js").write_text(
            """class AbqarynoMicrophone {
    constructor() {
        this.stream = null;
        this.recorder = null;
        this.chunks = [];
    }

    async start() {
        if (!navigator.mediaDevices?.getUserMedia) {
            throw new Error("المايك غير مدعوم في هذا المتصفح");
        }

        this.stream = await navigator.mediaDevices.getUserMedia({
            audio: true
        });

        return this.stream;
    }

    record() {
        if (!this.stream) {
            throw new Error("شغّل المايك أولًا");
        }

        this.chunks = [];
        this.recorder = new MediaRecorder(this.stream);

        this.recorder.ondataavailable = event => {
            if (event.data.size > 0) {
                this.chunks.push(event.data);
            }
        };

        this.recorder.start();
    }

    stopRecording() {
        return new Promise(resolve => {
            if (!this.recorder) {
                resolve(null);
                return;
            }

            this.recorder.onstop = () => {
                const blob = new Blob(
                    this.chunks,
                    { type: "audio/webm" }
                );

                resolve(blob);
            };

            this.recorder.stop();
        });
    }

    stop() {
        if (this.stream) {
            this.stream.getTracks().forEach(
                track => track.stop()
            );
        }

        this.stream = null;
        this.recorder = null;
    }
}

window.AbqarynoMicrophone = AbqarynoMicrophone;
""",
            encoding="utf-8"
        )

        (js_dir / "attachments.js").write_text(
            """class AbqarynoAttachments {
    constructor() {
        this.files = [];
    }

    add(fileList) {
        const files = Array.from(fileList || []);

        this.files.push(...files);

        document.dispatchEvent(
            new CustomEvent("abqaryno:attachments", {
                detail: files
            })
        );

        return files;
    }

    clear() {
        this.files = [];
    }

    getFiles() {
        return [...this.files];
    }
}

window.AbqarynoAttachments = AbqarynoAttachments;
window.abqarynoAttachments = new AbqarynoAttachments();
""",
            encoding="utf-8"
        )

        # ربط الوظائف المعتمدة بواجهة المشروع
        scripts = []

        feature_text = " ".join(
            str(x)
            for x in requirements.get("features", [])
        )

        screen_text = " ".join(
            str(x)
            for x in approved_screens
        )

        combined = f"{feature_text} {screen_text}"

        if any(x in combined for x in ["الرسائل", "شات", "محادثة"]):
            scripts.append("chat.js")

        if any(x in combined for x in ["الكاميرا", "فيديو"]):
            scripts.append("camera.js")

        if any(x in combined for x in ["المايك", "الصوت", "تسجيل"]):
            scripts.append("microphone.js")

        if any(x in combined for x in ["الملفات", "مرفقات", "إرفاق"]):
            scripts.append("attachments.js")

        script_tags = "\n".join(
            f'<script src="/js/{name}"></script>'
            for name in scripts
        )

        page = page.replace(
            "</body>",
            f"{script_tags}\n</body>"
        )

        (public / "index.html").write_text(
            page,
            encoding="utf-8"
        )

        option_ids = {
            str(option.get("option_id", "")).strip()
            for option in options
            if isinstance(option, dict)
        }

        option_ids = {
            str(option.get("option_id", "")).strip()
            for option in options
            if isinstance(option, dict)
        }

        server_lines = [
            "from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler",
            "from pathlib import Path",
            "import json",
            "import os",
            "import sys",
            "",
            "ROOT = Path(__file__).resolve().parents[1]",
            "sys.path.insert(0, str(ROOT))",
            "PUBLIC = ROOT / \"public\"",
            "",
            "class GeneratedHandler(SimpleHTTPRequestHandler):",
            "",
            "    def send_json(self, payload, status=200):",
            "        body = json.dumps(payload, ensure_ascii=False).encode(\"utf-8\")",
            "        self.send_response(status)",
            "        self.send_header(\"Content-Type\", \"application/json; charset=utf-8\")",
            "        self.send_header(\"Content-Length\", str(len(body)))",
            "        self.end_headers()",
            "        self.wfile.write(body)",
            "",
            "    def read_json(self):",
            "        length = int(self.headers.get(\"Content-Length\", \"0\") or 0)",
            "        raw = self.rfile.read(length) if length else b\"{}\"",
            "        try:",
            "            return json.loads(raw.decode(\"utf-8\"))",
            "        except (json.JSONDecodeError, UnicodeDecodeError):",
            "            return {}",
            "",
            "    def do_GET(self):",
            "        if self.path == \"/api/health\":",
            "            return self.send_json({\"ok\": True, \"service\": \"abqaryno-generated-api\"})",
            "        return super().do_GET()",
            "",
            "    def do_POST(self):",
        ]

        if "search" in option_ids:
            server_lines.extend([
                "        if self.path == \"/api/search\":",
                "            from services.search import SearchService",
                "            data = self.read_json()",
                "            result = SearchService().search(data.get(\"query\", \"\"), data.get(\"items\", []))",
                "            return self.send_json({\"ok\": True, \"query\": result.query, \"results\": result.results})",
            ])

        if "advanced_reports" in option_ids:
            server_lines.extend([
                "        if self.path == \"/api/advanced_reports\":",
                "            from services.reports import ReportsService",
                "            data = self.read_json()",
                "            result = ReportsService().generate(data.get(\"title\", \"تقرير\"), data.get(\"data\", {}))",
                "            return self.send_json({\"ok\": True, \"title\": result.title, \"generated_at\": result.generated_at, \"data\": result.data})",
            ])

        if "ocr" in option_ids:
            server_lines.extend([
                "        if self.path == \"/api/ocr\":",
                "            return self.send_json({\"ok\": False, \"error\": \"OCR يحتاج ملف صورة\"}, 501)",
            ])

        if "translation" in option_ids:
            server_lines.extend([
                "        if self.path == \"/api/translation\":",
                "            return self.send_json({\"ok\": False, \"error\": \"محرك الترجمة غير موصل بعد\"}, 501)",
            ])

        if "voice" in option_ids:
            server_lines.extend([
                "        if self.path == \"/api/voice\":",
                "            return self.send_json({\"ok\": False, \"error\": \"محرك الصوت غير موصل بعد\"}, 501)",
            ])

        server_lines.extend([
            "        return self.send_json({",
            "            \"ok\": False,",
            "            \"error\": \"API not found\"",
            "        }, 404)",
            "",
            "os.chdir(PUBLIC)",
            "",
            "server = ThreadingHTTPServer(",
            "    (\"127.0.0.1\", 8080),",
            "    GeneratedHandler",
            ")",
            "",
            "print(\"Generated project: http://127.0.0.1:8080\")",
            "server.serve_forever()",
            "",
        ])

        server_template = "\n".join(server_lines)

        (target / "server" / "server.py").write_text(
            server_template,
            encoding="utf-8"
        )

        (target / "routes" / "__init__.py").write_text(
            "",
            encoding="utf-8"
        )

        (target / "services" / "__init__.py").write_text(
            "",
            encoding="utf-8"
        )

        database_dir = target / "database"

        schema_sql = '-- قاعدة بيانات المشروع التي أنشأها عبقرينو\nPRAGMA foreign_keys = ON;\n\nCREATE TABLE IF NOT EXISTS users (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    name TEXT NOT NULL,\n    email TEXT,\n    phone TEXT,\n    password_hash TEXT,\n    created_at TEXT NOT NULL\n);\n\nCREATE TABLE IF NOT EXISTS roles (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    name TEXT NOT NULL UNIQUE\n);\n\nCREATE TABLE IF NOT EXISTS user_roles (\n    user_id INTEGER NOT NULL,\n    role_id INTEGER NOT NULL\n);\n\nCREATE TABLE IF NOT EXISTS clients (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    name TEXT NOT NULL,\n    phone TEXT,\n    email TEXT,\n    status TEXT,\n    created_at TEXT NOT NULL\n);\n\nCREATE TABLE IF NOT EXISTS lawyers (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    name TEXT NOT NULL,\n    phone TEXT,\n    email TEXT,\n    created_at TEXT NOT NULL\n);\n\nCREATE TABLE IF NOT EXISTS cases (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    case_number TEXT,\n    court TEXT,\n    chamber TEXT,\n    status TEXT,\n    notes TEXT,\n    client_id INTEGER,\n    lawyer_id INTEGER,\n    created_at TEXT NOT NULL\n);\n\nCREATE TABLE IF NOT EXISTS documents (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    name TEXT NOT NULL,\n    file_path TEXT NOT NULL,\n    mime_type TEXT,\n    case_id INTEGER,\n    uploaded_by INTEGER,\n    created_at TEXT NOT NULL\n);\n\nCREATE TABLE IF NOT EXISTS translations (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    document_id INTEGER,\n    source_text TEXT,\n    source_language TEXT,\n    target_language TEXT,\n    translated_text TEXT,\n    created_at TEXT NOT NULL\n);\n\nCREATE TABLE IF NOT EXISTS document_text (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    document_id INTEGER NOT NULL,\n    extracted_text TEXT,\n    extraction_method TEXT,\n    detected_language TEXT,\n    created_at TEXT NOT NULL\n);\n\nCREATE TABLE IF NOT EXISTS audio_transcriptions (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    file_path TEXT,\n    transcription_text TEXT,\n    detected_language TEXT,\n    created_at TEXT NOT NULL\n);\n\nCREATE TABLE IF NOT EXISTS audio_outputs (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    source_text TEXT,\n    language TEXT,\n    audio_path TEXT,\n    created_at TEXT NOT NULL\n);\n\nCREATE TABLE IF NOT EXISTS messages (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    sender_id INTEGER,\n    receiver_id INTEGER,\n    message TEXT,\n    created_at TEXT NOT NULL\n);\n\nCREATE TABLE IF NOT EXISTS notifications (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    user_id INTEGER,\n    title TEXT NOT NULL,\n    message TEXT,\n    is_read INTEGER NOT NULL DEFAULT 0,\n    created_at TEXT NOT NULL\n);\n\nCREATE TABLE IF NOT EXISTS reports (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    title TEXT NOT NULL,\n    content TEXT,\n    created_at TEXT NOT NULL\n);\n\nCREATE TABLE IF NOT EXISTS audit_logs (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    user_id INTEGER,\n    action TEXT NOT NULL,\n    details TEXT,\n    created_at TEXT NOT NULL\n);\n\nCREATE TABLE IF NOT EXISTS appointments (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    title TEXT NOT NULL,\n    appointment_date TEXT NOT NULL,\n    status TEXT,\n    user_id INTEGER,\n    created_at TEXT NOT NULL\n);\n'

        (database_dir / "schema.sql").write_text(
            schema_sql,
            encoding="utf-8"
        )

        database_py = 'from pathlib import Path\nimport sqlite3\n\nDATABASE = Path(__file__).resolve().parent / "app.db"\nSCHEMA = Path(__file__).resolve().parent / "schema.sql"\n\n\ndef get_connection():\n    connection = sqlite3.connect(DATABASE)\n    connection.row_factory = sqlite3.Row\n    connection.execute("PRAGMA foreign_keys = ON")\n    return connection\n\n\ndef initialize():\n    schema = SCHEMA.read_text(encoding="utf-8")\n\n    with get_connection() as connection:\n        connection.executescript(schema)\n        connection.commit()\n\n    return DATABASE\n\n\nif __name__ == "__main__":\n    path = initialize()\n    print(f"Database initialized: {path}")\n'

        (database_dir / "database.py").write_text(
            database_py,
            encoding="utf-8"
        )

        (database_dir / "README.md").write_text(
            "# قاعدة بيانات المشروع\\n\\n"
            "- app.db — قاعدة SQLite الفعلية\\n"
            "- schema.sql — مخطط قاعدة البيانات\\n"
            "- database.py — تهيئة والاتصال بقاعدة البيانات\\n",
            encoding="utf-8"
        )

        import sqlite3

        database_file = database_dir / "app.db"

        with sqlite3.connect(database_file) as connection:
            connection.executescript(schema_sql)
            connection.commit()

        (target / "uploads" / ".gitkeep").write_text(
            "",
            encoding="utf-8"
        )

        option_ids = {
            str(option.get("option_id", "")).strip()
            for option in options
            if isinstance(option, dict)
        }

        if "ocr" in option_ids:
            (target / "services" / "ocr.py").write_text(
                'from pathlib import Path\nimport subprocess\n\n\nclass OCRService:\n    """خدمة OCR اختيارية للمشروع الناتج."""\n\n    def extract_text(self, image_path, language="eng"):\n        image_path = Path(image_path)\n\n        if not image_path.exists():\n            raise FileNotFoundError(f"ملف الصورة غير موجود: {image_path}")\n\n        try:\n            result = subprocess.run(\n                [\n                    "tesseract",\n                    str(image_path),\n                    "stdout",\n                    "-l",\n                    str(language or "eng"),\n                ],\n                capture_output=True,\n                text=True,\n                check=True,\n            )\n        except FileNotFoundError as exc:\n            raise RuntimeError("Tesseract OCR غير مثبت في بيئة التشغيل.") from exc\n        except subprocess.CalledProcessError as exc:\n            message = exc.stderr.strip() or "فشل استخراج النص من الصورة."\n            raise RuntimeError(message) from exc\n\n        return result.stdout.strip()\n\n\ndef extract_text(image_path, language="eng"):\n    return OCRService().extract_text(image_path, language)\n',
                encoding="utf-8"
            )

            (target / "routes" / "ocr.py").write_text(
                'from pathlib import Path\n\nfrom services.ocr import OCRService\n\n\ndef extract_uploaded_image(image_path, language="eng"):\n    return OCRService().extract_text(\n        Path(image_path),\n        language,\n    )\n',
                encoding="utf-8"
            )

            (target / "OCR.md").write_text(
                "# OCR\n\n"
                "تمت إضافة خدمة OCR لأن خيار OCR تم اختياره أثناء إنشاء المشروع.\n\n"
                "الخدمة موجودة في services/ocr.py.\n"
                "المسار المساعد موجود في routes/ocr.py.\n"
                "تحتاج بيئة التشغيل إلى Tesseract OCR.\n",
                encoding="utf-8"
            )

        if "translation" in option_ids:
            (target / "services" / "translation.py").write_text(
                'from dataclasses import dataclass\n\n\n@dataclass\nclass TranslationResult:\n    source_text: str\n    source_language: str\n    target_language: str\n    translated_text: str\n\n\nclass TranslationService:\n    """خدمة ترجمة اختيارية للمشروع الناتج."""\n\n    def translate(\n        self,\n        source_text,\n        source_language="auto",\n        target_language="ar",\n    ):\n        source_text = str(source_text or "").strip()\n        source_language = str(source_language or "auto").strip()\n        target_language = str(target_language or "ar").strip()\n\n        if not source_text:\n            raise ValueError("النص المطلوب ترجمته فارغ.")\n\n        raise RuntimeError(\n            "محرك الترجمة غير موصل بعد. الخدمة جاهزة للربط بمحرك ترجمة."\n        )\n\n\ndef translate(\n    source_text,\n    source_language="auto",\n    target_language="ar",\n):\n    return TranslationService().translate(\n        source_text,\n        source_language,\n        target_language,\n    )\n',
                encoding="utf-8"
            )

            (target / "routes" / "translation.py").write_text(
                'from services.translation import TranslationService\n\n\ndef translate_text(\n    source_text,\n    source_language="auto",\n    target_language="ar",\n):\n    return TranslationService().translate(\n        source_text,\n        source_language,\n        target_language,\n    )\n',
                encoding="utf-8"
            )

            (target / "TRANSLATION.md").write_text(
                "# Translation\n\n"
                "تمت إضافة خدمة الترجمة لأن خيار Translation تم اختياره أثناء إنشاء المشروع.\n\n"
                "الخدمة موجودة في services/translation.py.\n"
                "المسار المساعد موجود في routes/translation.py.\n"
                "محرك الترجمة يحتاج إلى الربط بمزود ترجمة عند تشغيله.\n",
                encoding="utf-8"
            )

        if "voice" in option_ids:
            (target / "services" / "voice.py").write_text(
                'from pathlib import Path\nimport subprocess\n\n\nclass VoiceService:\n    """خدمة الصوت الاختيارية للمشروع الناتج."""\n\n    def transcribe(self, audio_path, language="ar"):\n        audio_path = Path(audio_path)\n\n        if not audio_path.exists():\n            raise FileNotFoundError(\n                f"ملف الصوت غير موجود: {audio_path}"\n            )\n\n        raise RuntimeError(\n            "محرك تحويل الصوت إلى نص غير موصل بعد. "\n            "الخدمة جاهزة للربط بمحرك STT."\n        )\n\n    def synthesize(self, text, language="ar", output_path=None):\n        text = str(text or "").strip()\n\n        if not text:\n            raise ValueError("النص المطلوب تحويله إلى صوت فارغ.")\n\n        raise RuntimeError(\n            "محرك تحويل النص إلى صوت غير موصل بعد. "\n            "الخدمة جاهزة للربط بمحرك TTS."\n        )\n\n\ndef transcribe(audio_path, language="ar"):\n    return VoiceService().transcribe(audio_path, language)\n\n\ndef synthesize(text, language="ar", output_path=None):\n    return VoiceService().synthesize(\n        text,\n        language,\n        output_path,\n    )\n',
                encoding="utf-8"
            )

            (target / "routes" / "voice.py").write_text(
                'from services.voice import VoiceService\n\n\ndef transcribe_audio(audio_path, language="ar"):\n    return VoiceService().transcribe(\n        audio_path,\n        language,\n    )\n\n\ndef synthesize_text(\n    text,\n    language="ar",\n    output_path=None,\n):\n    return VoiceService().synthesize(\n        text,\n        language,\n        output_path,\n    )\n',
                encoding="utf-8"
            )

            (target / "VOICE.md").write_text(
                "# Voice\n\n"
                "تمت إضافة خدمة الصوت لأن خيار Voice تم اختياره أثناء إنشاء المشروع.\n\n"
                "الخدمة موجودة في services/voice.py.\n"
                "المسار المساعد موجود في routes/voice.py.\n"
                "الخدمة جاهزة للربط بمحركات STT وTTS.\n",
                encoding="utf-8"
            )

        if "search" in option_ids:
            (target / "services" / "search.py").write_text(
                '''from dataclasses import dataclass


@dataclass
class SearchResult:
    query: str
    results: list


class SearchService:
    """خدمة البحث الاختيارية للمشروع الناتج."""

    def search(self, query, items=None):
        query = str(query or "").strip()

        if not query:
            raise ValueError("عبارة البحث مطلوبة.")

        items = items or []
        query_lower = query.casefold()

        results = [
            item
            for item in items
            if query_lower in str(item).casefold()
        ]

        return SearchResult(
            query=query,
            results=results,
        )


def search(query, items=None):
    return SearchService().search(query, items)
''',
                encoding="utf-8"
            )

            (target / "routes" / "search.py").write_text(
                '''from services.search import SearchService


def search_items(query, items=None):
    return SearchService().search(
        query,
        items,
    )
''',
                encoding="utf-8"
            )

            (target / "SEARCH.md").write_text(
                "# Search\\n\\n"
                "تمت إضافة خدمة البحث لأن خيار البحث تم اختياره أثناء إنشاء المشروع.\\n\\n"
                "الخدمة موجودة في services/search.py.\\n"
                "المسار المساعد موجود في routes/search.py.\\n",
                encoding="utf-8"
            )

        if "advanced_reports" in option_ids:
            (target / "services" / "reports.py").write_text(
                'from dataclasses import dataclass\nfrom datetime import datetime\n\n\n@dataclass\nclass ReportResult:\n    title: str\n    generated_at: str\n    data: dict\n\n\nclass ReportsService:\n    """خدمة التقارير المتقدمة الاختيارية للمشروع الناتج."""\n\n    def generate(self, title, data=None):\n        title = str(title or "").strip()\n\n        if not title:\n            raise ValueError("عنوان التقرير مطلوب.")\n\n        return ReportResult(\n            title=title,\n            generated_at=datetime.now().isoformat(),\n            data=data or {},\n        )\n\n\ndef generate_report(title, data=None):\n    return ReportsService().generate(title, data)\n',
                encoding="utf-8"
            )

            (target / "routes" / "reports.py").write_text(
                'from services.reports import ReportsService\n\n\ndef generate_report(title, data=None):\n    return ReportsService().generate(\n        title,\n        data,\n    )\n',
                encoding="utf-8"
            )

            (target / "REPORTS.md").write_text(
                "# Advanced Reports\n\n"
                "تمت إضافة خدمة التقارير المتقدمة لأن الخيار تم اختياره أثناء إنشاء المشروع.\n\n"
                "الخدمة موجودة في services/reports.py.\n"
                "المسار المساعد موجود في routes/reports.py.\n",
                encoding="utf-8"
            )

        (target / "README.md").write_text(
            f"""# {idea}

تم إنشاء هذا المشروع بواسطة عبقرينو Studio.

## البنية

- public — واجهة البرنامج
- server — تشغيل المشروع
- routes — مسارات التطبيق
- services — الخدمات والمنطق
- database — طبقة البيانات
- uploads — الملفات المرفوعة
- .abqaryno-requirements.json — المتطلبات والشاشات المعتمدة

## التشغيل

python server/server.py
""",
            encoding="utf-8"
        )

        return target, manifest


class FinalReport:

    def write(
        self,
        root,
        target,
        manifest
    ):

        reports = Path(root) / "reports"

        reports.mkdir(
            parents=True,
            exist_ok=True
        )

        report = {

            "status": "COMPLETED",

            "time": now(),

            "target": str(target),

            "idea": manifest["idea"],

            "approved_screen_count":
                len(manifest["approved_screens"]),

            "approved_screens":
                manifest["approved_screens"]

        }

        path = (
            reports /
            "creation-final-report.json"
        )

        path.write_text(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

        return path
