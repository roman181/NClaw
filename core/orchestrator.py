"""Small, safe orchestration entry point (no shell execution)."""
from dataclasses import dataclass


@dataclass
class AgentStatus:
    name: str
    state: str = "idle"
    detail: str = ""


class Orchestrator:
    """Tracks agent status; tool execution is deliberately not implicit."""

    def __init__(self) -> None:
        self.agents: dict[str, AgentStatus] = {}

    def register(self, name: str) -> AgentStatus:
        if not name or name.strip() != name:
            raise ValueError("Agent name must be non-empty and trimmed")
        if name in self.agents:
            raise ValueError(f"Agent already registered: {name}")
        status = AgentStatus(name=name)
        self.agents[name] = status
        return status

    def snapshot(self) -> list[dict[str, str]]:
        return [
            {"name": item.name, "state": item.state, "detail": item.detail}
            for item in self.agents.values()
        ]
