from dataclasses import dataclass, field
from datetime import datetime, timezone

from .models import Transition


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class HistoryLog:
    entries: list[Transition] = field(default_factory=list)

    def record(self, transition: Transition) -> None:
        self.entries.append(transition)

    def last(self) -> Transition | None:
        if not self.entries:
            return None
        return self.entries[-1]

    def count(self) -> int:
        return len(self.entries)

    def states(self) -> list[str]:
        result = []

        for entry in self.entries:
            if not result:
                result.append(entry.before.value)
            result.append(entry.after.value)

        return result
