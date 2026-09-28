from dataclasses import dataclass, field
from typing import Any

from .states import CoreState


@dataclass(frozen=True)
class Evidence:
    source: str
    fact: str
    confidence: float = 1.0

    def __post_init__(self):
        if not self.source.strip():
            raise ValueError("Evidence source is required")
        if not self.fact.strip():
            raise ValueError("Evidence fact is required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Evidence confidence must be between 0 and 1")


@dataclass(frozen=True)
class Decision:
    action: str
    reason: str
    target_state: CoreState
    evidence: tuple[Evidence, ...] = ()

    def __post_init__(self):
        if not self.action.strip():
            raise ValueError("Decision action is required")
        if not self.reason.strip():
            raise ValueError("Decision reason is required")


@dataclass(frozen=True)
class Transition:
    before: CoreState
    after: CoreState
    reason: str
    decision: Decision | None = None

    def __post_init__(self):
        if not self.reason.strip():
            raise ValueError("Transition reason is required")


@dataclass
class CoreContext:
    state: CoreState = CoreState.NEW
    goal: str = ""
    facts: dict[str, Any] = field(default_factory=dict)
    requirements: list[str] = field(default_factory=list)
    plan: list[str] = field(default_factory=list)
    map_data: dict[str, Any] = field(default_factory=dict)
    next_step: str | None = None
    history: list[Transition] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    status: str = "ACTIVE"
