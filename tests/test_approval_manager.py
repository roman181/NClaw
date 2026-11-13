"""Tests for expiring one-time approval records."""
import pytest

from core.approval_manager import ApprovalManager


def test_request_starts_pending_and_can_be_approved() -> None:
    manager = ApprovalManager()
    request = manager.create("publish", "Publish release v0.1")
    assert request.status == "pending"
    assert manager.approve(request.request_id).status == "approved"


def test_rejected_request_cannot_be_consumed() -> None:
    manager = ApprovalManager()
    request = manager.create("delete", "Delete temporary file")
    manager.reject(request.request_id)
    with pytest.raises(PermissionError):
        manager.consume(request.request_id, "delete")


def test_approved_request_is_one_time_and_action_bound() -> None:
    manager = ApprovalManager()
    request = manager.create("publish", "Publish release")
    manager.approve(request.request_id)
    with pytest.raises(PermissionError):
        manager.consume(request.request_id, "delete")
    assert manager.consume(request.request_id, "publish").status == "consumed"
    with pytest.raises(PermissionError):
        manager.consume(request.request_id, "publish")


def test_expired_request_cannot_be_approved() -> None:
    manager = ApprovalManager(ttl_seconds=1)
    request = manager.create("install", "Install package")
    request.expires_at = 0
    with pytest.raises(TimeoutError):
        manager.approve(request.request_id)
