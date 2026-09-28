from pathlib import Path
import json

from engine.scanner import ProjectScanner
from engine.root_cause import RootCauseEngine
from engine.planner import EngineeringPlanner
from engine.approval import ApprovalGate
from engine.snapshot import SnapshotEngine
from engine.repair import DeepRepairEngine
from engine.verification import VerificationEngine
from engine.repair_generator import RepairGenerator, RepairGenerationError


def _project(project_path):
    return str(Path(project_path).expanduser().resolve())


def scan(project_path):
    project_path = _project(project_path)

    result = ProjectScanner(project_path).scan()

    return {
        "status": "scanned",
        "project_path": project_path,
        "scan": result,
    }


def root_cause(project_path, scan_data=None):
    project_path = _project(project_path)

    result = RootCauseEngine(project_path).build()

    return {
        "status": "analyzed",
        "project_path": project_path,
        "cause": result,
    }


def plan(project_path, scan_data=None, cause=None):
    project_path = _project(project_path)

    result = EngineeringPlanner(
        project_path,
        goal="general_repair",
    ).diagnose_and_plan()

    return {
        "status": "planned",
        "project_path": project_path,
        "plan": result,
        "actions": result.get("actions", []),
        "repair_candidates": result.get(
            "repair_candidates",
            [],
        ),
    }


def generate(project_path, candidate):
    project_path = _project(project_path)

    if not candidate:
        return {
            "status": "generation_blocked",
            "project_path": project_path,
            "message": "لا يوجد مرشح إصلاح.",
        }

    candidate = dict(candidate)

    candidate_id = candidate.get("candidate_id")
    if not candidate_id:
        return {
            "status": "generation_blocked",
            "project_path": project_path,
            "message": "مرشح الإصلاح لا يحتوي على candidate_id.",
        }

    candidate["action_id"] = candidate_id

    design = candidate.get("design") or {}
    anchor = design.get("anchor")

    if not anchor:
        return {
            "status": "generation_blocked",
            "project_path": project_path,
            "candidate_id": candidate_id,
            "message": "تصميم الإصلاح لا يحتوي على anchor.",
        }

    try:
        generated = RepairGenerator(project_path).generate(
            action=candidate,
            anchor=anchor,
        )
    except RepairGenerationError as exc:
        return {
            "status": "generation_blocked",
            "project_path": project_path,
            "candidate_id": candidate_id,
            "target": candidate.get("target"),
            "reason": candidate.get("reason"),
            "message": str(exc),
        }

    result = RepairGenerator.to_dict(generated)

    return {
        "status": "GENERATED",
        "project_path": project_path,
        "candidate_id": candidate_id,
        "generation": result,
    }


def approve(project_path, candidate_id):
    project_path = _project(project_path)

    result = ApprovalGate(project_path).approve(
        candidate_id
    )

    return {
        "status": "approved",
        "project_path": project_path,
        "approval": result,
    }


def execute(
    project_path,
    scan_data,
    cause,
    plan_data,
    candidate_id=None,
    target=None,
    reason=None,
    old_text=None,
    new_text=None,
):
    project_path = _project(project_path)

    if not candidate_id:
        return {
            "status": "approval_required",
            "project_path": project_path,
            "message": "يجب تحديد candidate_id قبل التنفيذ.",
        }

    candidate = ApprovalGate(
        project_path
    ).require_approved(candidate_id)

    target = target or candidate.get("target", "")
    reason = reason or candidate.get("reason", candidate_id)

    if not target:
        return {
            "status": "execution_blocked",
            "project_path": project_path,
            "candidate_id": candidate_id,
            "message": "مرشح الإصلاح لا يحتوي على target صالح.",
        }

    if old_text is None or new_text is None:
        return {
            "status": "repair_input_required",
            "project_path": project_path,
            "candidate_id": candidate_id,
            "target": target,
            "reason": reason,
            "message": (
                "تمت الموافقة على المرشح، لكن التنفيذ الآمن "
                "يتطلب old_text وnew_text المطابقين للتغيير المقترح."
            ),
        }

    engine = DeepRepairEngine(project_path)

    evidence = engine.inspect(target)

    applied = engine.apply_exact_change(
        action_id=candidate_id,
        target=target,
        reason=reason,
        old_text=old_text,
        new_text=new_text,
        approved=True,
    )

    return {
        "status": "APPLIED",
        "project_path": project_path,
        "candidate_id": candidate_id,
        "evidence": evidence,
        "repair": applied.__dict__,
    }


def verify(
    project_path,
    previous_scan,
    repair,
    old_text=None,
    new_text=None,
):
    project_path = _project(project_path)

    if not repair:
        return {
            "status": "verification_blocked",
            "project_path": project_path,
            "message": "لا يوجد إصلاح للتحقق منه.",
        }

    action_id = repair.get(
        "candidate_id",
        repair.get("action_id", "UNKNOWN"),
    )

    target = repair.get("target")

    if not target:
        return {
            "status": "verification_blocked",
            "project_path": project_path,
            "message": "الإصلاح لا يحتوي على target.",
        }

    if old_text is None or new_text is None:
        return {
            "status": "verification_input_required",
            "project_path": project_path,
            "action_id": action_id,
            "target": target,
            "message": (
                "التحقق الدقيق يحتاج old_text وnew_text "
                "المستخدمين في الإصلاح."
            ),
        }

    result = VerificationEngine(
        project_path
    ).verify_exact_change(
        action_id=action_id,
        target=target,
        old_text=old_text,
        new_text=new_text,
    )

    # إعادة الفحص بعد الإصلاح.
    rescanned = ProjectScanner(
        project_path
    ).scan()

    # إعادة التحليل بعد الإصلاح.
    reanalysis = RootCauseEngine(
        project_path
    ).build()

    return {
        "status": "VERIFIED_AND_REANALYZED",
        "project_path": project_path,
        "verification": result,
        "post_repair_scan": rescanned,
        "post_repair_root_cause": reanalysis,
    }
