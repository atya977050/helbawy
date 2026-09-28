from .states import CoreState


ALLOWED_TRANSITIONS = {
    CoreState.NEW: {
        CoreState.UNDERSTANDING,
    },
    CoreState.UNDERSTANDING: {
        CoreState.REQUIREMENTS,
        CoreState.WAITING,
        CoreState.BLOCKED,
        CoreState.STOPPED,
    },
    CoreState.REQUIREMENTS: {
        CoreState.PLANNING,
        CoreState.WAITING,
        CoreState.BLOCKED,
        CoreState.STOPPED,
    },
    CoreState.PLANNING: {
        CoreState.MAPPING,
        CoreState.WAITING,
        CoreState.BLOCKED,
        CoreState.STOPPED,
    },
    CoreState.MAPPING: {
        CoreState.DECISION,
        CoreState.WAITING,
        CoreState.BLOCKED,
        CoreState.STOPPED,
    },
    CoreState.DECISION: {
        CoreState.NEXT_STEP,
        CoreState.WAITING,
        CoreState.BLOCKED,
        CoreState.STOPPED,
        CoreState.COMPLETED,
    },
    CoreState.NEXT_STEP: {
        CoreState.UNDERSTANDING,
        CoreState.REQUIREMENTS,
        CoreState.PLANNING,
        CoreState.MAPPING,
        CoreState.DECISION,
        CoreState.WAITING,
        CoreState.BLOCKED,
        CoreState.STOPPED,
        CoreState.COMPLETED,
    },
    CoreState.WAITING: {
        CoreState.UNDERSTANDING,
        CoreState.REQUIREMENTS,
        CoreState.PLANNING,
        CoreState.MAPPING,
        CoreState.DECISION,
        CoreState.NEXT_STEP,
        CoreState.BLOCKED,
        CoreState.STOPPED,
    },
    CoreState.BLOCKED: {
        CoreState.WAITING,
        CoreState.STOPPED,
    },
    CoreState.STOPPED: set(),
    CoreState.COMPLETED: set(),
}


def can_transition(current: CoreState, target: CoreState) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())


def validate_transition(current: CoreState, target: CoreState) -> None:
    if not can_transition(current, target):
        raise ValueError(
            f"Invalid core transition: {current.value} -> {target.value}"
        )
