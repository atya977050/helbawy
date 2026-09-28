from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class AppOption:
    option_id: str
    title: str
    description: str
    category: str
    enabled: bool = False
    requires_confirmation: bool = False
    config: dict[str, Any] | None = None

    def to_dict(self):
        data = asdict(self)
        data["config"] = self.config or {}
        return data


class OptionsEngine:
    """
    نظام الإضافات العامة لعبقرينو.

    الـ Option لا يصبح جزءًا من عبقرينو نفسه؛
    بل يتم اختياره أثناء إنشاء البرنامج ثم يُضاف
    إلى مواصفات المشروع الناتج.
    """

    CATALOG = [
        AppOption(
            option_id="legal_assistant",
            title="⚖️ المساعد القانوني الخاص بالمحامي",
            description=(
                "مساعد خاص بالمحامي يضاف إلى البرامج القانونية "
                "عند اختياره فقط."
            ),
            category="legal",
            requires_confirmation=True,
            config={
                "private": True,
                "lawyer_only": True,
                "client_access": False,
            },
        ),
        AppOption(
            option_id="ocr",
            title="📄 OCR واستخراج النص",
            description="استخراج النص من الصور والمستندات الممسوحة.",
            category="documents",
        ),
        AppOption(
            option_id="translation",
            title="🌐 الترجمة",
            description="إضافة إمكانيات الترجمة إلى البرنامج.",
            category="language",
        ),
        AppOption(
            option_id="voice",
            title="🎙️ الصوت",
            description="إضافة إمكانيات التسجيل وتحويل الصوت والنص.",
            category="voice",
        ),
        AppOption(
            option_id="advanced_reports",
            title="📊 التقارير المتقدمة",
            description="إضافة تقارير وتحليلات متقدمة للبرنامج.",
            category="reports",
        ),
        AppOption(
            option_id="search",
            title="🔎 البحث المتقدم",
            description="إضافة خدمة بحث عامة داخل بيانات المشروع الناتج.",
            category="search",
        ),
    ]

    def catalog(self) -> list[dict]:
        return [
            option.to_dict()
            for option in self.CATALOG
        ]

    def get(self, option_id: str) -> AppOption | None:
        option_id = str(option_id or "").strip()

        for option in self.CATALOG:
            if option.option_id == option_id:
                return option

        return None

    def validate(self, selected: list[Any]) -> list[dict]:
        if not isinstance(selected, list):
            raise ValueError("الخيارات يجب أن تكون قائمة")

        result = []

        for item in selected:
            option_id = (
                item.get("option_id")
                if isinstance(item, dict)
                else item
            )

            option = self.get(option_id)

            if option is None:
                raise ValueError(
                    f"Option غير معروف: {option_id}"
                )

            result.append(option.to_dict())

        return result

    def selected_ids(self, selected: list[Any]) -> list[str]:
        return [
            option["option_id"]
            for option in self.validate(selected)
        ]
