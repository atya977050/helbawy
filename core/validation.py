from .errors import (
    ConflictingInformation,
    InvalidDecision,
    MissingInformation,
)
from .models import CoreContext, Decision
from .states import CoreState


def validate_context(context: CoreContext) -> None:
    if not context.goal.strip():
        raise MissingInformation("Core goal is required")

    if context.status not in {"ACTIVE", "WAITING", "BLOCKED", "STOPPED", "COMPLETED"}:
        raise ConflictingInformation(
            f"Unknown context status: {context.status}"
        )


def validate_decision(context: CoreContext, decision: Decision) -> None:
    if not decision.action.strip():
        raise InvalidDecision("Decision action is required")

    if not decision.reason.strip():
        raise InvalidDecision("Decision reason is required")

    if not isinstance(decision.target_state, CoreState):
        raise InvalidDecision("Decision target_state must be CoreState")

    if context.state in {CoreState.STOPPED, CoreState.COMPLETED}:
        raise InvalidDecision(
            f"No decision is allowed from terminal state: {context.state.value}"
        )


def validate_required_information(
    context: CoreContext,
    required: list[str],
) -> None:
    missing = [
        item for item in required
        if item not in context.facts or context.facts[item] in (None, "")
    ]

    if missing:
        raise MissingInformation(
            "Missing required information: " + ", ".join(missing)
        )
