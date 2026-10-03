from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLANS = ROOT / "plans"
REPORTS = ROOT / "reports"

PLANS.mkdir(exist_ok=True)
REPORTS.mkdir(exist_ok=True)

CAPABILITIES = [
    {
        "id": "requirements",
        "name": "تحليل المتطلبات",
        "required": True,
        "verification": "requirements_report"
    },
    {
        "id": "screen_design",
        "name": "تصميم الشاشات واعتمادها",
        "required": True,
        "verification": "approved_screen_plan"
    },
    {
        "id": "project_architecture",
        "name": "تصميم معمارية المشروع",
        "required": True,
        "verification": "architecture_manifest"
    },
    {
        "id": "database",
        "name": "قاعدة البيانات والعلاقات",
        "required": True,
        "verification": "database_schema_test"
    },
    {
        "id": "authentication",
        "name": "تسجيل الدخول والصلاحيات",
        "required": True,
        "verification": "auth_test"
    },
    {
        "id": "api",
        "name": "REST/API",
        "required": True,
        "verification": "api_test"
    },
    {
        "id": "realtime",
        "name": "الاتصال اللحظي",
        "required": False,
        "verification": "realtime_test"
    },
    {
        "id": "file_uploads",
        "name": "رفع وإدارة الملفات",
        "required": False,
        "verification": "upload_test"
    },
    {
        "id": "notifications",
        "name": "الإشعارات",
        "required": False,
        "verification": "notification_test"
    },
    {
        "id": "payments",
        "name": "الدفع الإلكتروني",
        "required": False,
        "verification": "payment_test"
    },
    {
        "id": "search",
        "name": "البحث والتصفية",
        "required": False,
        "verification": "search_test"
    },
    {
        "id": "responsive_ui",
        "name": "واجهة متجاوبة للموبايل والويب",
        "required": True,
        "verification": "ui_render_test"
    },
    {
        "id": "security",
        "name": "الأمان والتحقق من المدخلات",
        "required": True,
        "verification": "security_test"
    },
    {
        "id": "runtime",
        "name": "تشغيل حقيقي للمشروع",
        "required": True,
        "verification": "runtime_test"
    },
    {
        "id": "verification",
        "name": "التحقق النهائي",
        "required": True,
        "verification": "final_verification"
    },
    {
        "id": "evidence",
        "name": "سجل الأدلة والتنفيذ",
        "required": True,
        "verification": "evidence_report"
    },
]

def main() -> int:
    manifest = {
        "name": "ABQARYNO_PLATFORM_CAPABILITY_MATRIX",
        "version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "capabilities": CAPABILITIES,
        "rules": {
            "required_capability_must_be_verified": True,
            "optional_capability_must_not_be_claimed_without_evidence": True,
            "build_pass_requires_runtime_verification": True,
            "final_pass_requires_all_required_capabilities": True,
        },
    }

    plan_path = PLANS / "abqaryno-platform-capabilities.json"
    report_path = REPORTS / "abqaryno-platform-capabilities-report.json"

    plan_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    required = [x for x in CAPABILITIES if x["required"]]

    report = {
        "report": "ABQARYNO_PLATFORM_CAPABILITY_REPORT",
        "version": "1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "VERIFICATION_PENDING",
        "total_capabilities": len(CAPABILITIES),
        "required_capabilities": len(required),
        "optional_capabilities": len(CAPABILITIES) - len(required),
        "verified_capabilities": 0,
        "unverified_required": [x["id"] for x in required],
        "manifest": str(plan_path.relative_to(ROOT)),
    }

    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("=== ABQARYNO PLATFORM CAPABILITY MATRIX ===")
    print(f"Total      : {len(CAPABILITIES)}")
    print(f"Required   : {len(required)}")
    print(f"Optional   : {len(CAPABILITIES) - len(required)}")
    print("STATUS     : VERIFICATION_PENDING")
    print(f"PLAN       : {plan_path}")
    print(f"REPORT     : {report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
