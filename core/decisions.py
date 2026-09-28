from .errors import ConflictingInformation, MissingInformation
from .models import CoreContext, Decision
from .states import CoreState


def decide(context: CoreContext) -> Decision:
    if not context.goal.strip():
        raise MissingInformation("A goal is required before making a decision")

    if context.status == "BLOCKED":
        raise ConflictingInformation(
            "Core context is blocked and requires clarification"
        )

    if context.status == "COMPLETED":
        return Decision(
            action="complete",
            reason="Core process is already completed",
            target_state=CoreState.COMPLETED,
        )

    if context.status == "STOPPED":
        return Decision(
            action="stop",
            reason="Core process is already stopped",
            target_state=CoreState.STOPPED,
        )

    if context.state == CoreState.NEW:
        return Decision(
            action="begin_understanding",
            reason="A valid goal exists and understanding can begin",
            target_state=CoreState.UNDERSTANDING,
        )

    if context.state == CoreState.UNDERSTANDING:
        if not context.facts:
            return Decision(
                action="wait_for_information",
                reason="Understanding requires available facts",
                target_state=CoreState.WAITING,
            )
        return Decision(
            action="continue_to_requirements",
            reason="Facts are available for requirement analysis",
            target_state=CoreState.REQUIREMENTS,
        )

    if context.state == CoreState.REQUIREMENTS:
        if not context.requirements:
            return Decision(
                action="wait_for_requirements",
                reason="Requirements are not available yet",
                target_state=CoreState.WAITING,
            )
        return Decision(
            action="continue_to_planning",
            reason="Requirements are available for planning",
            target_state=CoreState.PLANNING,
        )

    if context.state == CoreState.PLANNING:
        if not context.plan:
            return Decision(
                action="wait_for_plan",
                reason="A plan is required before mapping",
                target_state=CoreState.WAITING,
            )
        return Decision(
            action="continue_to_mapping",
            reason="Plan is available for mapping",
            target_state=CoreState.MAPPING,
        )

    if context.state == CoreState.MAPPING:
        if not context.map_data:
            return Decision(
                action="wait_for_map",
                reason="A map is required before decision making",
                target_state=CoreState.WAITING,
            )
        return Decision(
            action="continue_to_decision",
            reason="The map is available for decision making",
            target_state=CoreState.DECISION,
        )

    if context.state == CoreState.DECISION:
        if context.next_step:
            return Decision(
                action="execute_next_step",
                reason="A valid next step has been identified",
                target_state=CoreState.NEXT_STEP,
            )
        return Decision(
            action="complete",
            reason="No further step is required",
            target_state=CoreState.COMPLETED,
        )

    if context.state == CoreState.NEXT_STEP:
        return Decision(
            action="continue",
            reason="The next step must be evaluated again after progress",
            target_state=CoreState.DECISION,
        )

    if context.state == CoreState.WAITING:
        raise MissingInformation(
            "WAITING is a pause state and requires new information before resuming"
        )

    raise ConflictingInformation(
        f"No decision rule exists for state: {context.state.value}"
    )
