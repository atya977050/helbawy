from core.states import CoreState
from core.transitions import can_transition


def test_terminal_states_have_no_outgoing_transitions():
    for state in (CoreState.STOPPED, CoreState.COMPLETED):
        for target in CoreState:
            assert not can_transition(state, target)


def test_new_has_one_start_transition():
    allowed = [
        target
        for target in CoreState
        if can_transition(CoreState.NEW, target)
    ]
    assert allowed == [CoreState.UNDERSTANDING]


def test_waiting_cannot_loop_into_waiting():
    assert not can_transition(CoreState.WAITING, CoreState.WAITING)


def test_blocked_requires_resolution():
    assert can_transition(CoreState.BLOCKED, CoreState.WAITING)
    assert can_transition(CoreState.BLOCKED, CoreState.STOPPED)
    assert not can_transition(CoreState.BLOCKED, CoreState.BLOCKED)
