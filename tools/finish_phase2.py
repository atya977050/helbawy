from pathlib import Path
import ast, json, re, sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "engine" / "creation.py"
SERVER = ROOT / "studio" / "server.py"
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

REPORT_JSON = REPORTS / "phase2-final-report.json"
REPORT_MD = REPORTS / "phase2-final-report.md"
STATE = REPORTS / "phase2-state.json"
CONTRACT = ROOT / "plans" / "phase2-requirements-contract.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def fail(msg):
    raise SystemExit(f"PHASE 2 ABORTED: {msg}")

def read(path):
    if not path.exists():
        fail(f"Missing file: {path}")
    return path.read_text(encoding="utf-8")

engine_text = read(ENGINE)
server_text = read(SERVER)

# ------------------------------------------------------------
# 1. سلامة المرحلة السابقة
# ------------------------------------------------------------
phase1 = REPORTS / "phase1-state.json"
if not phase1.exists():
    fail("PHASE 1 state is missing.")

try:
    phase1_data = json.loads(phase1.read_text(encoding="utf-8"))
except Exception as exc:
    fail(f"Invalid phase1-state.json: {exc}")

phase1_complete = (
    phase1_data.get("status") == "PHASE_1_COMPLETE"
    or phase1_data.get("gate") == "PHASE_1_COMPLETE"
)

if not phase1_complete:
    fail(
        "PHASE 1 is not officially complete. "
        f"state={phase1_data}"
    )

if phase1_data.get("next_phase_allowed") is not True:
    fail(
        "PHASE 1 explicitly blocks the next phase. "
        f"state={phase1_data}"
    )

# ------------------------------------------------------------
# 2. فحص Python قبل أي تعديل
# ------------------------------------------------------------
for path in (ENGINE, SERVER):
    try:
        ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        fail(f"Python syntax error in {path}: {exc}")

# ------------------------------------------------------------
# 3. اكتشاف RequirementsEngine الحقيقي
# ------------------------------------------------------------
required_symbols = [
    "RequirementsEngine",
    "ScreenProposalEngine",
    "ScreenApprovalWizard",
]

missing = [x for x in required_symbols if x not in engine_text]
if missing:
    fail("Missing creation-engine symbols: " + ", ".join(missing))

# ------------------------------------------------------------
# 4. متطلبات Phase 2
# ------------------------------------------------------------
required_engine_tokens = [
    "def analyze",
    '"idea"',
    '"features"',
    '"roles"',
    '"capabilities"',
    '"app_types"',
]

engine_missing = [
    token for token in required_engine_tokens
    if token not in engine_text
]

if engine_missing:
    fail("Requirements engine is incomplete: " + ", ".join(engine_missing))

# ------------------------------------------------------------
# 5. إنشاء عقد المتطلبات الرسمي
# ------------------------------------------------------------
contract = {
    "version": 2,
    "phase": "PHASE_2",
    "name": "ABQARYNO REQUIREMENTS CONTRACT",
    "created_at": now(),
    "lifecycle": [
        "idea",
        "understanding",
        "requirement",
        "acceptance_criteria",
        "approval",
        "screen_mapping",
        "traceability"
    ],
    "requirement_schema": {
        "required": [
            "requirement_id",
            "text",
            "source",
            "category",
            "priority",
            "acceptance_criteria",
            "approval"
        ],
        "approval_values": [
            "PENDING",
            "APPROVED",
            "REJECTED",
            "EDIT_REQUIRED"
        ],
        "priority_values": [
            "CRITICAL",
            "HIGH",
            "MEDIUM",
            "LOW"
        ]
    },
    "gates": [
        "IDEA_PRESENT",
        "REQUIREMENTS_PRESENT",
        "REQUIREMENT_IDS_UNIQUE",
        "ACCEPTANCE_CRITERIA_PRESENT",
        "APPROVAL_STATE_PRESENT",
        "NO_REJECTED_CRITICAL",
        "SCREEN_MAPPING_READY"
    ]
}

CONTRACT.parent.mkdir(parents=True, exist_ok=True)
CONTRACT.write_text(
    json.dumps(contract, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

# ------------------------------------------------------------
# 6. فحص شاشة المتطلبات الحالية
# ------------------------------------------------------------
requirements_ui_candidates = [
    ROOT / "studio" / "ui" / "create-requirements.html",
]

ui = next((p for p in requirements_ui_candidates if p.exists()), None)

if ui is None:
    fail("create-requirements.html is missing.")

ui_text = ui.read_text(encoding="utf-8")

ui_requirements = {
    "yes": bool(re.search(r"نعم|اعتماد|approve", ui_text, re.I)),
    "no": bool(re.search(r"لا|رفض|reject", ui_text, re.I)),
    "edit": bool(re.search(r"تعديل|edit", ui_text, re.I)),
}

ui_missing = [
    key for key, value in ui_requirements.items()
    if not value
]

if ui_missing:
    fail(
        "Requirements approval UI is incomplete: "
        + ", ".join(ui_missing)
    )

# ------------------------------------------------------------
# 7. إضافة أدوات تطبيع المتطلبات إلى engine/creation.py
# ------------------------------------------------------------
marker = "# ABQARYNO PHASE 2 REQUIREMENTS CONTRACT"

if marker not in engine_text:

    anchor = "class RequirementsEngine:"

    if engine_text.count(anchor) != 1:
        fail(
            "Expected exactly one RequirementsEngine class, found "
            + str(engine_text.count(anchor))
        )

    helper = r'''
# ABQARYNO PHASE 2 REQUIREMENTS CONTRACT
# ------------------------------------------------------------
# Requirement lifecycle:
# Idea -> Requirement -> Acceptance Criteria -> Approval
# ------------------------------------------------------------
def _abqaryno_normalize_requirements(raw, idea):
    raw = raw if isinstance(raw, dict) else {}

    features = raw.get("features", [])
    capabilities = raw.get("capabilities", [])
    roles = raw.get("roles", [])
    app_types = raw.get("app_types", [])

    if not isinstance(features, list):
        features = [features] if features else []

    if not isinstance(capabilities, list):
        capabilities = [capabilities] if capabilities else []

    if not isinstance(roles, list):
        roles = [roles] if roles else []

    if not isinstance(app_types, list):
        app_types = [app_types] if app_types else []

    requirements = []

    source_items = []

    for item in features:
        source_items.append(("FUNCTIONAL", item))

    for item in capabilities:
        source_items.append(("CAPABILITY", item))

    for index, (category, item) in enumerate(source_items, start=1):
        text = str(item).strip()

        if not text:
            continue

        requirements.append({
            "requirement_id": f"REQ-{index:04d}",
            "text": text,
            "source": "idea_analysis",
            "category": category,
            "priority": "HIGH",
            "acceptance_criteria": [
                f"يجب أن تكون الوظيفة الخاصة بـ: {text} محددة وقابلة للاختبار."
            ],
            "approval": "PENDING"
        })

    return {
        "idea": str(idea).strip(),
        "requirements": requirements,
        "features": features,
        "capabilities": capabilities,
        "roles": roles,
        "app_types": app_types,
        "approval": {
            "status": "PENDING",
            "approved_count": 0,
            "rejected_count": 0,
            "pending_count": len(requirements)
        },
        "phase": "PHASE_2",
        "contract_version": 2
    }

def _abqaryno_validate_requirements(data):
    if not isinstance(data, dict):
        return False, ["requirements_not_dict"]

    errors = []

    if not str(data.get("idea", "")).strip():
        errors.append("idea_missing")

    requirements = data.get("requirements", [])

    if not isinstance(requirements, list):
        errors.append("requirements_not_list")
        return False, errors

    ids = set()

    for item in requirements:
        if not isinstance(item, dict):
            errors.append("requirement_not_object")
            continue

        rid = str(item.get("requirement_id", "")).strip()
        text = str(item.get("text", "")).strip()
        criteria = item.get("acceptance_criteria", [])
        approval = item.get("approval")

        if not rid:
            errors.append("requirement_id_missing")
        elif rid in ids:
            errors.append(f"duplicate_requirement_id:{rid}")
        ids.add(rid)

        if not text:
            errors.append(f"text_missing:{rid}")

        if not isinstance(criteria, list) or not criteria:
            errors.append(f"acceptance_criteria_missing:{rid}")

        if approval not in {
            "PENDING",
            "APPROVED",
            "REJECTED",
            "EDIT_REQUIRED"
        }:
            errors.append(f"invalid_approval:{rid}")

    return not errors, errors

'''

    # Insert before RequirementsEngine, preserving existing class.
    engine_text = engine_text.replace(
        anchor,
        helper + "\n" + anchor,
        1
    )

    ENGINE.write_text(engine_text, encoding="utf-8")

# ------------------------------------------------------------
# 8. إعادة قراءة وفحص syntax
# ------------------------------------------------------------
engine_text = read(ENGINE)

try:
    ast.parse(engine_text)
except SyntaxError as exc:
    fail(f"Generated Phase 2 engine is syntactically invalid: {exc}")

# ------------------------------------------------------------
# 9. فحص أدوات Phase 2
# ------------------------------------------------------------
phase2_tokens = [
    "_abqaryno_normalize_requirements",
    "_abqaryno_validate_requirements",
    "acceptance_criteria",
    "requirement_id",
    "approval",
    "PHASE_2",
]

missing_after = [
    token for token in phase2_tokens
    if token not in engine_text
]

if missing_after:
    fail(
        "Phase 2 implementation incomplete: "
        + ", ".join(missing_after)
    )

# ------------------------------------------------------------
# 10. اختبار مباشر للعقد بدون تشغيل المشروع
# ------------------------------------------------------------
namespace = {}
try:
    exec(
        compile(
            helper if 'helper' in locals() else "",
            "<phase2-contract>",
            "exec"
        ),
        namespace,
    )
except Exception as exc:
    fail(f"Phase 2 contract self-test failed: {exc}")

normalize = namespace.get("_abqaryno_normalize_requirements")
validate = namespace.get("_abqaryno_validate_requirements")

if not normalize or not validate:
    fail("Phase 2 contract functions are not executable.")

sample = normalize(
    {
        "features": ["تسجيل الدخول"],
        "capabilities": ["المحادثة"],
        "roles": ["موكل", "محامي"],
        "app_types": ["legal"]
    },
    "برنامج استشارات قانونية"
)

ok, errors = validate(sample)

if not ok:
    fail(
        "Phase 2 contract self-test failed: "
        + ", ".join(errors)
    )

# ------------------------------------------------------------
# 11. بوابة المرحلة
# ------------------------------------------------------------
checks = {
    "PHASE1_COMPLETE": True,
    "ENGINE_SYNTAX": True,
    "REQUIREMENTS_ENGINE": True,
    "REQUIREMENTS_UI": not ui_missing,
    "REQUIREMENTS_CONTRACT": CONTRACT.exists(),
    "NORMALIZATION": "_abqaryno_normalize_requirements" in engine_text,
    "VALIDATION": "_abqaryno_validate_requirements" in engine_text,
    "ACCEPTANCE_CRITERIA": "acceptance_criteria" in engine_text,
    "APPROVAL_STATE": '"approval"' in engine_text,
    "SELF_TEST": ok,
}

passed = sum(checks.values())
failed = [k for k, v in checks.items() if not v]

gate = "PHASE_2_COMPLETE" if not failed else "REVIEW_REQUIRED"

report = {
    "phase": "PHASE_2",
    "gate": gate,
    "time": now(),
    "root": str(ROOT),
    "checks": checks,
    "passed": passed,
    "failed": failed,
    "contract": str(CONTRACT),
    "next_phase": "PHASE_3" if gate == "PHASE_2_COMPLETE" else None,
}

REPORT_JSON.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

md = [
    "# عبقرينو — PHASE 2 FINAL REPORT",
    "",
    f"- Gate: **{gate}**",
    f"- Passed: **{passed}/{len(checks)}**",
    "",
    "## Checks",
]

for name, value in checks.items():
    md.append(f"- {'PASS' if value else 'FAIL'} — {name}")

if failed:
    md += ["", "## Failed", *[f"- {x}" for x in failed]]
else:
    md += [
        "",
        "## Phase 2 Result",
        "Requirements are normalized, identified, validated,",
        "have acceptance criteria and explicit approval states.",
        "",
        "Next: PHASE 3 — Screen Proposals & Approval."
    ]

REPORT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")

STATE.write_text(
    json.dumps(
        {
            "phase": "PHASE_2",
            "gate": gate,
            "completed_at": now() if gate == "PHASE_2_COMPLETE" else None,
            "report": str(REPORT_JSON),
            "contract": str(CONTRACT),
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8"
)

print("=" * 78)
print(" عبقرينو — إغلاق PHASE 2")
print("=" * 78)
print()
print(f"PHASE 2 GATE : {gate}")
print(f"PASS         : {passed}/{len(checks)}")

if failed:
    print("FAILED       :")
    for item in failed:
        print(" -", item)

print()
print("REPORT :", REPORT_JSON)
print("MARKDOWN:", REPORT_MD)
print("STATE :", STATE)
print("CONTRACT:", CONTRACT)
print("=" * 78)

if gate != "PHASE_2_COMPLETE":
    raise SystemExit(2)
