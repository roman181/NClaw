import pytest

from core.approvals import ApprovalRequest, ApprovalRequired, require_approval
from core.orchestrator import Orchestrator


def test_orchestrator_registers_agents():
    nexus = Orchestrator()
    nexus.register("Nexus")
    assert nexus.snapshot() == [{"name": "Nexus", "state": "idle", "detail": ""}]


def test_orchestrator_rejects_duplicate_agent():
    nexus = Orchestrator()
    nexus.register("Nexus")
    with pytest.raises(ValueError):
        nexus.register("Nexus")


def test_approval_is_required_by_default():
    request = ApprovalRequest("publish", "Publish a release")
    with pytest.raises(ApprovalRequired):
        require_approval(request)


def test_explicit_approval_allows_guard():
    require_approval(ApprovalRequest("read", "Read local metadata"), approved=True)
