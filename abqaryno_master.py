#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
from pathlib import Path

from engine.scanner import ProjectScanner
from engine.contract_graph import ContractGraphEngine
from engine.root_cause import RootCauseEngine
from engine.planner import EngineeringPlanner
from engine.approval import ApprovalGate
from engine.snapshot import SnapshotEngine
from engine.repair import DeepRepairEngine
from engine.verification import VerificationEngine
from engine.execution_log import ExecutionLog

from engine.creation import (
    RequirementsEngine,
    ScreenApprovalWizard,
    ProjectGenerator,
    ConversationState,
    FinalReport
)


class AbqarynoOrchestrator:

    def __init__(self, project_path):

        self.project_path = Path(
            project_path
        ).resolve()

        self.scanner = ProjectScanner(
            str(self.project_path)
        )

        self.contract_graph = ContractGraphEngine(
            str(self.project_path)
        )

        self.root_cause = RootCauseEngine(
            str(self.project_path)
        )

        self.planner = EngineeringPlanner(
            str(self.project_path)
        )

        self.approval_gate = ApprovalGate(
            str(self.project_path)
        )

        self.snapshot_engine = SnapshotEngine(
            str(self.project_path)
        )

        self.repair_engine = DeepRepairEngine(
            str(self.project_path)
        )

        self.verification_engine = VerificationEngine(
            str(self.project_path)
        )

        self.logger = ExecutionLog(
            str(self.project_path)
        )


    def run_repair_lifecycle(self):

        print(
            "\n[*] عبقرينو: بدء الفحص والإصلاح..."
        )

        reports = (
            self.project_path /
            "reports"
        )

        reports.mkdir(
            parents=True,
            exist_ok=True
        )

        for cycle in range(1, 6):

            print(
                f"\n--- دورة الفحص #{cycle} ---"
            )

            scan = self.scanner.scan()

            (
                reports /
                "scan-report.json"
            ).write_text(
                json.dumps(
                    scan if isinstance(scan, dict)
                    else {"files": scan},
                    ensure_ascii=False,
                    indent=2
                ),
                encoding="utf-8"
            )

            try:
                self.contract_graph.build()
            except Exception as exc:
                print(
                    "[!] Contract Graph:",
                    exc
                )

            try:
                diagnostics = (
                    self.root_cause.build()
                )
            except Exception as exc:
                print(
                    "[!] Root Cause:",
                    exc
                )
                diagnostics = {}

            findings = []

            if isinstance(
                diagnostics,
                dict
            ):

                findings = diagnostics.get(
                    "findings",
                    []
                )

            if not findings:

                print(
                    "[+] لا توجد نتائج تتطلب إصلاحًا آليًا."
                )

                return {
                    "status": "CLEAN",
                    "cycles": cycle
                }

            try:

                plan = (
                    self.planner
                    .diagnose_and_plan()
                )

            except Exception as exc:

                print(
                    "[-] فشل بناء خطة الإصلاح:",
                    exc
                )

                self.logger.record(
                    "repair",
                    "planning",
                    "FAILED",
                    error=str(exc)
                )

                return {
                    "status":
                        "PLANNING_FAILED"
                }

            actions = []

            if isinstance(
                plan,
                dict
            ):

                actions = plan.get(
                    "actions",
                    []
                )

            if not actions:

                print(
                    "[+] لا توجد إجراءات إصلاح."
                )

                return {
                    "status":
                        "NO_ACTIONS"
                }

            print(
                f"[+] الإجراءات: {len(actions)}"
            )

            for action in actions:

                action_id = (
                    action.get("id")
                    or
                    action.get("action_id")
                    or
                    "unknown-action"
                )

                candidate_id = (
                    action.get(
                        "candidate_id"
                    )
                    or
                    action_id
                )

                try:

                    self.approval_gate.approve(
                        candidate_id
                    )

                except Exception as exc:

                    print(
                        f"[!] لم يعتمد {candidate_id}:",
                        exc
                    )

                    continue

                try:

                    self.snapshot_engine.create(
                        self.project_path
                    )

                    self.logger.record(
                        "repair",
                        action_id,
                        "SNAPSHOT_CREATED"
                    )

                except Exception as exc:

                    print(
                        "[!] Snapshot:",
                        exc
                    )

            try:

                result = (
                    self.repair_engine
                    .execute_repairs()
                )

                print(
                    "[+] نتيجة الإصلاح:",
                    result
                )

            except Exception as exc:

                print(
                    "[-] فشل التنفيذ:",
                    exc
                )

                self.logger.record(
                    "repair",
                    "execute_repairs",
                    "FAILED",
                    error=str(exc)
                )

                return {
                    "status":
                        "REPAIR_FAILED",
                    "error":
                        str(exc)
                }

            print(
                "[*] إعادة التحليل..."
            )

        return {
            "status":
                "MAX_CYCLES_REACHED"
        }


    def run_project_creation_lifecycle(
        self,
        user_idea
    ):

        print(
            "\n"
            + "=" * 64
        )

        print(
            "عبقرينو — إنشاء برنامج جديد"
        )

        print(
            "=" * 64
        )

        requirements = (
            RequirementsEngine()
            .analyze(user_idea)
        )

        state = ConversationState(
            self.project_path
        )

        state.save({
            "phase":
                "requirements",
            "requirements":
                requirements
        })

        print(
            "\nالشاشات التي يقترحها عبقرينو:"
        )

        for index, screen in enumerate(
            requirements["screens"],
            1
        ):

            print(
                f"{index}. "
                f"{screen['title']} — "
                f"{screen['purpose']}"
            )

        wizard = ScreenApprovalWizard()

        approved = []

        for screen in requirements["screens"]:

            print(
                f"\nهل تريد شاشة "
                f"{screen['title']}؟"
            )

            answer = input(
                "(y/n): "
            ).strip().lower()

            if answer != "y":

                print(
                    "[-] تم رفض الشاشة."
                )

                continue

            selected = wizard.choose(
                screen
            )

            if selected:

                approved.append(
                    selected
                )

                state.save({
                    "phase":
                        "screen_approved",
                    "requirements":
                        requirements,
                    "approved_screens":
                        approved
                })

        if not approved:

            print(
                "[-] لم تعتمد أي شاشة."
            )

            return {
                "status":
                    "CANCELLED"
            }

        generator = ProjectGenerator(
            self.project_path
        )

        target, manifest = (
            generator.generate(
                user_idea,
                requirements,
                approved
            )
        )

        report = FinalReport().write(
            self.project_path,
            target,
            manifest
        )

        print(
            "\n[+] تم إنشاء المشروع:"
        )

        print(
            target
        )

        print(
            "[+] التقرير:"
        )

        print(
            report
        )

        print(
            "\n[*] فحص المشروع المنشأ..."
        )

        repair_result = (
            AbqarynoOrchestrator(
                target
            ).run_repair_lifecycle()
        )

        return {
            "status":
                "CREATED_AND_VERIFIED",

            "path":
                str(target),

            "report":
                str(report),

            "repair":
                repair_result
        }


def interactive_menu():

    while True:

        print(
            "\n"
            + "=" * 64
        )

        print(
            "أهلاً بك في عبقرينو 🤖"
        )

        print(
            "=" * 64
        )

        print(
            "1. إنشاء برنامج جديد"
        )

        print(
            "2. فحص وإصلاح برنامج موجود"
        )

        print(
            "3. خروج"
        )

        choice = input(
            "\nاختيارك: "
        ).strip()

        if choice == "1":

            idea = input(
                "\nما فكرة البرنامج؟: "
            ).strip()

            if not idea:

                print(
                    "[-] يجب إدخال فكرة."
                )

                continue

            AbqarynoOrchestrator(
                "."
            ).run_project_creation_lifecycle(
                idea
            )

        elif choice == "2":

            path = input(
                "مسار البرنامج "
                "(Enter للمجلد الحالي): "
            ).strip()

            path = path or "."

            AbqarynoOrchestrator(
                path
            ).run_repair_lifecycle()

        elif choice == "3":

            print(
                "إلى اللقاء يا فندم."
            )

            return

        else:

            print(
                "[-] اختيار غير صحيح."
            )


if __name__ == "__main__":
    interactive_menu()
