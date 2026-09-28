#!/usr/bin/env python3
"""
P45 Engineering Contracts

Central vocabulary for evidence, repair plans, snapshots,
execution states, and verification results.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


EXECUTION_STATES = {
    "DISCOVERED",
    "EVIDENCED",
    "PLANNED",
    "APPROVED",
    "SNAPSHOTTED",
    "APPLIED",
    "VERIFIED",
    "FAILED",
    "NOT_APPLIED",
    "REJECTED",
}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Evidence:
    source: str
    finding: str
    status: str = "EVIDENCED"
    file: str | None = None
    line: int | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class RepairAction:
    action_id: str
    target: str
    reason: str
    evidence: list[Evidence] = field(default_factory=list)
    status: str = "PLANNED"
    before_sha256: str | None = None
    after_sha256: str | None = None
    snapshot: str | None = None
    verification: list[str] = field(default_factory=list)


@dataclass
class RepairPlan:
    project: str
    goal: str
    actions: list[RepairAction] = field(default_factory=list)
    status: str = "PLANNED"
    created_at: str = field(default_factory=utc_now)


def validate_state(state: str):
    if state not in EXECUTION_STATES:
        raise ValueError(f"Invalid P45 execution state: {state}")
    return state
