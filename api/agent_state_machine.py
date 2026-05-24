# MD-OS Agent Run State Machine
#
# States: queued → running → waiting_approval → done
#                         ↘ (on error) → failed
#
# State transitions are validated in code + enforced in DB ( CHECK constraint)

from typing import Any

AGENT_RUN_STATES = [
    "queued",
    "running",
    "waiting_approval",
    "done",
    "failed",
]

VALID_TRANSITIONS = {
    "queued": ["running"],
    "running": ["waiting_approval", "done", "failed"],
    "waiting_approval": ["running", "failed"],  # resume after approval
    "done": [],           # terminal
    "failed": [],        # terminal
}


def is_valid_transition(from_state: str, to_state: str) -> bool:
    """Check if transition is allowed by state machine rules."""
    valid_next = VALID_TRANSITIONS.get(from_state, [])
    return to_state in valid_next


def can_transition(agent_run: dict[str, Any], to_state: str) -> bool:
    """Check if agent run can transition to given state."""
    current = agent_run.get("status", "queued")
    return is_valid_transition(current, to_state)


def next_states(current: list[str]) -> list[str]:
    """Get valid next states from current state(s)."""
    states: set[str] = set()
    for s in current:
        states.update(VALID_TRANSITIONS.get(s, []))
    return list(states)