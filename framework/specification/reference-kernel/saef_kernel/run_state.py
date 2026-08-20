from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


class InvalidTransition(ValueError):
    pass


TERMINAL={"completed","partial","refused","failed"}
TRANSITIONS={
    "created":{"preflighted","refused","failed"},
    "preflighted":{"input_validated","refused","failed"},
    "input_validated":{"planned","refused","failed"},
    "planned":{"context_ready","checkpointed","refused","failed"},
    "context_ready":{"evidence_gathering","checkpointed","refused","failed"},
    "evidence_gathering":{"evidence_ready","checkpointed","partial","refused","failed"},
    "evidence_ready":{"diagnosing","checkpointed","partial","refused","failed"},
    "diagnosing":{"draft_ready","checkpointed","partial","failed"},
    "draft_ready":{"reviewing","checkpointed","partial","failed"},
    "reviewing":{"completed","partial","refused","failed","checkpointed"},
    "checkpointed":{"planned","context_ready","evidence_gathering","evidence_ready","diagnosing","draft_ready","reviewing","refused","failed"},
}


@dataclass
class RunStateMachine:
    run_id: str
    state: str="created"
    history: list[dict]=field(default_factory=list)

    def transition(self, new_state: str, actor: str, reason: str, at: datetime | None=None) -> None:
        if self.state in TERMINAL:
            raise InvalidTransition(f"terminal state {self.state} cannot transition")
        allowed=TRANSITIONS.get(self.state,set())
        if new_state not in allowed:
            raise InvalidTransition(f"{self.state} -> {new_state} is not allowed")
        at=at or datetime.now(timezone.utc)
        self.history.append({"from":self.state,"to":new_state,"actor":actor,"reason":reason,"at":at.isoformat()})
        self.state=new_state

    @property
    def terminal(self) -> bool:
        return self.state in TERMINAL
