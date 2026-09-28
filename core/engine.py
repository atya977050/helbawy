from .decisions import decide
from .errors import CoreCompleted, CoreStopped
from .history import HistoryLog
from .models import CoreContext, Transition
from .transitions import validate_transition
from .validation import validate_context, validate_decision


class CoreEngine:
    def __init__(self, context: CoreContext):
        self.context = context
        self.history = HistoryLog()

    def step(self):
        validate_context(self.context)

        if self.context.state == self.context.state.COMPLETED:
            raise CoreCompleted("Core process is already completed")

        if self.context.state == self.context.state.STOPPED:
            raise CoreStopped("Core process is already stopped")

        decision = decide(self.context)
        validate_decision(self.context, decision)
        validate_transition(self.context.state, decision.target_state)

        transition = Transition(
            before=self.context.state,
            after=decision.target_state,
            reason=decision.reason,
            decision=decision,
        )

        if any(
            entry.before == transition.after
            and entry.after == transition.before
            for entry in self.history.entries
        ):
            self.context.status = "STOPPED"
            raise RuntimeError(
                f"Core cycle detected: {transition.before.value} -> {transition.after.value}"
            )

        self.history.record(transition)
        self.context.history.append(transition)
        self.context.state = decision.target_state

        return transition
