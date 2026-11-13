"""In-memory, one-time approval registry.

Approvals authorize a named action for a short time. They do not execute it.
A future side-effecting tool must call consume() immediately before acting.
Pending approvals are intentionally cleared when the process restarts.
"""
from __future__ import annotations

import secrets
import time
from dataclasses import dataclass


@dataclass
class ApprovalRecord:
    request_id: str
    action: str
    description: str
    status: str
    created_at: float
    expires_at: float


class ApprovalManager:
    def __init__(self, ttl_seconds: int = 600) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self.ttl_seconds = ttl_seconds
        self._records: dict[str, ApprovalRecord] = {}

    def create(self, action: str, description: str) -> ApprovalRecord:
        action = action.strip()
        description = description.strip()
        if not action or not description:
            raise ValueError("Action and description are required")
        now = time.time()
        request_id = secrets.token_urlsafe(6)
        while request_id in self._records:
            request_id = secrets.token_urlsafe(6)
        record = ApprovalRecord(
            request_id=request_id,
            action=action[:100],
            description=description[:1000],
            status="pending",
            created_at=now,
            expires_at=now + self.ttl_seconds,
        )
        self._records[request_id] = record
        return record

    def _get_pending(self, request_id: str) -> ApprovalRecord:
        record = self._records.get(request_id)
        if record is None:
            raise KeyError("Approval request not found")
        if record.status != "pending":
            raise ValueError(f"Request is already {record.status}")
        if time.time() >= record.expires_at:
            record.status = "expired"
            raise TimeoutError("Approval request expired")
        return record

    def approve(self, request_id: str) -> ApprovalRecord:
        record = self._get_pending(request_id)
        record.status = "approved"
        return record

    def reject(self, request_id: str) -> ApprovalRecord:
        record = self._get_pending(request_id)
        record.status = "rejected"
        return record

    def consume(self, request_id: str, expected_action: str) -> ApprovalRecord:
        """Consume a matching approval once, immediately before an action."""
        record = self._get_pending(request_id)
        if record.action != expected_action:
            raise PermissionError("Approval does not match the requested action")
        record.status = "consumed"
        return record

    def pending(self) -> list[ApprovalRecord]:
        now = time.time()
        for record in self._records.values():
            if record.status == "pending" and now >= record.expires_at:
                record.status = "expired"
        return [r for r in self._records.values() if r.status == "pending"]
