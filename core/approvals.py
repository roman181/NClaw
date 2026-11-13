"""Explicit approval primitives for actions with side effects."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ApprovalRequest:
    action: str
    description: str


class ApprovalRequired(PermissionError):
    """Raised when an action has not been explicitly approved."""


def require_approval(request: ApprovalRequest, approved: bool = False) -> None:
    """Reject side-effecting actions unless approval was explicitly supplied."""
    if not approved:
        raise ApprovalRequired(
            f"Approval required for '{request.action}': {request.description}"
        )
