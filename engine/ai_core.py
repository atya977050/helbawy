# -*- coding: utf-8 -*-

from dataclasses import dataclass, asdict
from typing import Any
import json


@dataclass
class AssistantAction:
    action_id: str
    title: str
    description: str
    requires_confirmation: bool = True
    status: str = "proposed"


class AIProvider:
    """واجهة موحدة لأي مزود AI مستقبلي."""

    name = "abstract"

    def generate(self, prompt: str, context: dict) -> str:
        raise NotImplementedError


class LocalAIProvider(AIProvider):
    """
    مزود محلي آمن كبداية.
    لا ينفذ عمليات خارجية ولا يرسل البيانات إلى أي خدمة.
    """

    name = "local"

    def generate(self, prompt: str, context: dict) -> str:
        capabilities = context.get("capability_labels", {})
        screens = context.get("screens", [])

        if "ما الشاشات" in prompt or "الشاشات" in prompt:
            names = [
                s.get("title", s.get("id", "شاشة"))
                for s in screens
            ]
            return "الشاشات المتاحة: " + (
                "، ".join(names) if names else "لا توجد شاشات محددة بعد."
            )

        if "الوظائف" in prompt or "ماذا يمكنني" in prompt:
            labels = list(capabilities.values())
            return "الوظائف المتاحة: " + (
                "، ".join(labels) if labels
                else "لم يتم تحديد وظائف إضافية بعد."
            )

        if "المساعد" in prompt:
            return (
                "أنا المساعد الذكي للبرنامج. "
                "أفهم سياق البرنامج والشاشات والقدرات المتاحة، "
                "وأقترح الإجراءات قبل تنفيذها."
            )

        return (
            "فهمت طلبك. أستطيع تحليل سياق البرنامج "
            "واقتراح إجراء مناسب، لكن أي إجراء يغيّر "
            "البيانات يحتاج إلى تأكيدك أولًا."
        )


class ContextBuilder:

    def build(
        self,
        idea: str,
        requirements: dict | None = None,
        screen: dict | None = None,
        user: dict | None = None,
    ) -> dict:

        requirements = requirements or {}
        screen = screen or {}
        user = user or {}

        return {
            "idea": idea,
            "screen": screen,
            "user": user,
            "screens": requirements.get("screens", []),
            "roles": requirements.get("roles", []),
            "capabilities": requirements.get("capabilities", []),
            "capability_labels": requirements.get(
                "capability_labels", {}
            ),
            "app_types": requirements.get("app_types", []),
        }


class AgentActionEngine:

    READ_ONLY = {
        "inspect",
        "search",
        "explain",
        "summarize",
    }

    def propose(self, prompt: str, context: dict) -> list[AssistantAction]:
        text = (prompt or "").strip()

        if not text:
            return []

        lowered = text.lower()

        if (
            "ابحث" in text
            or "بحث" in text
            or "search" in lowered
        ):
            return [
                AssistantAction(
                    action_id="search",
                    title="البحث في بيانات البرنامج",
                    description="البحث في البيانات المتاحة داخل سياق البرنامج.",
                    requires_confirmation=False,
                )
            ]

        if (
            "اعرض" in text
            or "افتح" in text
            or "وضح" in text
        ):
            return [
                AssistantAction(
                    action_id="inspect",
                    title="استعراض المعلومات",
                    description="عرض المعلومات المرتبطة بطلب المستخدم.",
                    requires_confirmation=False,
                )
            ]

        if (
            "احذف" in text
            or "حذف" in text
            or "عدّل" in text
            or "تعديل" in text
            or "أنشئ" in text
            or "إضافة" in text
            or "أرسل" in text
        ):
            return [
                AssistantAction(
                    action_id="data_change",
                    title="تنفيذ إجراء على بيانات البرنامج",
                    description=(
                        "الإجراء قد يغيّر بيانات البرنامج "
                        "ويحتاج إلى تأكيد المستخدم."
                    ),
                    requires_confirmation=True,
                )
            ]

        return [
            AssistantAction(
                action_id="explain",
                title="تحليل الطلب",
                description="تحليل الطلب وفق سياق البرنامج الحالي.",
                requires_confirmation=False,
            )
        ]

    def confirm(
        self,
        action: AssistantAction,
        confirmed: bool = False,
    ) -> AssistantAction:
        if not confirmed:
            action.status = "cancelled"
            return action

        action.status = "confirmed"
        return action

    def approve(self, action: AssistantAction) -> AssistantAction:
        if action.requires_confirmation and action.status != "confirmed":
            raise PermissionError(
                "يجب تأكيد الإجراء من المستخدم قبل اعتماده."
            )

        action.status = "approved"
        return action


class AssistantEngine:

    def __init__(self, provider: AIProvider | None = None):
        self.provider = provider or LocalAIProvider()
        self.context_builder = ContextBuilder()
        self.actions = AgentActionEngine()

    def handle(
        self,
        prompt: str,
        idea: str,
        requirements: dict | None = None,
        screen: dict | None = None,
        user: dict | None = None,
    ) -> dict:

        context = self.context_builder.build(
            idea=idea,
            requirements=requirements,
            screen=screen,
            user=user,
        )

        answer = self.provider.generate(
            prompt,
            context,
        )

        proposed_actions = self.actions.propose(
            prompt,
            context,
        )

        return {
            "ok": True,
            "provider": self.provider.name,
            "answer": answer,
            "context": context,
            "actions": [
                asdict(action)
                for action in proposed_actions
            ],
        }
