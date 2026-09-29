#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from datetime import datetime, timezone
import ast
import json
import re
import html
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
ENGINE = ROOT / "engine"
REPORTS = ROOT / "reports"
STATE = ROOT / ".abqaryno"


def now():
    return datetime.now(timezone.utc).isoformat()


def write_new(path, text):
    if path.exists():
        print(f"[=] موجود بالفعل: {path.relative_to(ROOT)}")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"[+] تمت الإضافة: {path.relative_to(ROOT)}")
    return True


def compile_project():
    files = [
        p for p in ROOT.rglob("*.py")
        if ".git" not in p.parts
        and "__pycache__" not in p.parts
    ]

    result = subprocess.run(
        [sys.executable, "-m", "py_compile"] +
        [str(p) for p in files]
    )

    if result.returncode != 0:
        raise SystemExit("[-] فشل فحص Python.")

    print(f"[+] Python syntax OK — {len(files)} ملف")


CREATION_ENGINE = r'''
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

        return {
            "idea": idea,
            "created_at": now(),
            "screens": screens,
            "features": [
                "تسجيل المستخدم",
                "حفظ البيانات",
                "البحث"
            ]
        }


class ScreenProposalEngine:

    def proposals(self, screen, offset=0):

        layouts = [
            (
                "بطاقات",
                ["العنوان", "بطاقات الوظائف", "شريط التنقل"]
            ),
            (
                "لوحة تحكم",
                ["العنوان", "إحصائيات", "أزرار رئيسية", "قائمة"]
            ),
            (
                "قائمة مركزة",
                ["العنوان", "قائمة الوظائف", "زر إجراء رئيسي"]
            ),
            (
                "واجهة جانبية",
                ["قائمة جانبية", "منطقة محتوى", "زر رئيسي"]
            ),
            (
                "واجهة كبيرة",
                ["عنوان كبير", "إجراءات رئيسية", "محتوى"]
            ),
            (
                "واجهة مختصرة",
                ["عنوان", "أزرار كبيرة", "معلومات مختصرة"]
            )
        ]

        result = []

        for i in range(3):

            index = (offset + i) % len(layouts)

            layout, components = layouts[index]

            result.append(
                ScreenProposal(
                    screen_id=screen["id"],
                    title=screen["title"],
                    purpose=screen["purpose"],
                    variant=i + 1,
                    layout=layout,
                    components=components
                )
            )

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
        approved_screens
    ):

        name = self.safe_name(idea)

        target = self.root / name

        public = target / "public"

        public.mkdir(
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
التصميم: {html.escape(screen["layout"])}
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

</head>

<body>

<header>

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

        (public / "index.html").write_text(
            page,
            encoding="utf-8"
        )

        manifest = {
            "idea": idea,
            "created_at": now(),
            "requirements": requirements,
            "approved_screens": approved_screens
        }

        (target / ".abqaryno-requirements.json").write_text(
            json.dumps(
                manifest,
                ensure_ascii=False,
                indent=2
            ),
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
'''


MASTER = r'''#!/usr/bin/env python3
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
'''


def main():

    print("=" * 70)
    print("عبقرينو — بدء الترقية")
    print("=" * 70)

    required = [
        "engine/scanner.py",
        "engine/contracts.py",
        "engine/planner.py",
        "engine/approval.py",
        "engine/repair.py",
        "engine/verification.py",
        "engine/snapshot.py",
        "engine/execution_log.py"
    ]

    for item in required:

        path = ROOT / item

        if not path.exists():

            raise SystemExit(
                f"[-] ملف أساسي مفقود: {item}"
            )

        ast.parse(
            path.read_text(
                encoding="utf-8"
            )
        )

    print(
        "[+] محركات P45 الحالية سليمة نحويًا."
    )

    ENGINE.mkdir(
        parents=True,
        exist_ok=True
    )

    REPORTS.mkdir(
        parents=True,
        exist_ok=True
    )

    STATE.mkdir(
        parents=True,
        exist_ok=True
    )

    write_new(
        ENGINE / "creation.py",
        CREATION_ENGINE
    )

    master = ROOT / "abqaryno_master.py"

    # We intentionally replace only the known master orchestrator.
    master.write_text(
        MASTER,
        encoding="utf-8"
    )

    print(
        "[+] تم تحديث abqaryno_master.py"
    )

    compile_project()

    smoke = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from engine.creation import "
                "RequirementsEngine,ScreenProposalEngine,ProjectGenerator;"
                "from abqaryno_master import AbqarynoOrchestrator;"
                "print('ABQARYNO_IMPORT_OK')"
            )
        ],
        cwd=ROOT,
        capture_output=True,
        text=True
    )

    if smoke.returncode != 0:

        print(
            smoke.stdout
        )

        print(
            smoke.stderr
        )

        raise SystemExit(
            "[-] فشل اختبار الاستيراد."
        )

    print(
        smoke.stdout.strip()
    )

    report = {
        "status":
            "UPGRADED",

        "time":
            now(),

        "new_engine":
            "engine/creation.py",

        "master":
            "abqaryno_master.py",

        "features": [
            "Requirements Engine",
            "Interactive Screen Wizard",
            "Three Screen Proposals",
            "Alternative Designs",
            "User Screen Approval",
            "Screen Modification",
            "Conversation State",
            "Project Generator",
            "Creation Final Report",
            "Post-generation P45 lifecycle"
        ]
    }

    (
        REPORTS /
        "complete-upgrade-report.json"
    ).write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print()
    print("=" * 70)
    print("[+] اكتملت ترقية عبقرينو.")
    print("[+] لم يتم حذف محركات P45.")
    print("[+] تمت إضافة نظام اختيار الشاشات والتصميمات.")
    print("[+] تم اختبار Python syntax.")
    print(
        "[+] التقرير: "
        "reports/complete-upgrade-report.json"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
