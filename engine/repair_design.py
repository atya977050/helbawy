from dataclasses import dataclass, asdict
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc).isoformat()


@dataclass
class CompiledRepairDesign:
    design_id: str
    candidate_id: str
    action_id: str
    target: str | None
    targets: list[str]
    repair_type: str
    intent: str
    depends_on: list[str]
    requires_exact_source_anchor: bool
    status: str = "COMPILED"
    execution_allowed: bool = False
    compiled_at: str = ""


class RepairDesignCompiler:
    """
    Converts an approved/design-only repair description into a
    deterministic intermediate representation.

    This component does NOT modify target files and does NOT
    generate executable source by itself.
    """

    def compile(self, action):
        design = action.get("design") or {}

        if not action.get("candidate_id"):
            raise ValueError("candidate_id is required")

        if not design.get("design_id"):
            raise ValueError("design_id is required")

        targets = []

        if design.get("target"):
            targets.append(design["target"])

        for target in design.get("targets", []):
            if target not in targets:
                targets.append(target)

        if not targets:
            raise ValueError("No repair target declared")

        return CompiledRepairDesign(
            design_id=design["design_id"],
            candidate_id=action["candidate_id"],
            action_id=action["action_id"],
            target=design.get("target"),
            targets=targets,
            repair_type=design.get("type", ""),
            intent=design.get("intent", ""),
            depends_on=list(design.get("depends_on", [])),
            requires_exact_source_anchor=bool(
                design.get("requires_exact_source_anchor", True)
            ),
            compiled_at=utc_now(),
        )

    def to_dict(self, compiled):
        return asdict(compiled)
