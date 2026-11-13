"""Thread-safe, in-memory, one-time approval registry.

Approvals authorize a named action and optional exact payload digest. They do
not execute actions. Pending approvals are intentionally cleared on restart.
"""
from __future__ import annotations

import secrets
import threading
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
    binding: str | None = None


class ApprovalManager:
    def __init__(self, ttl_seconds: int = 600) -> None:
        if not isinstance(ttl_seconds, int) or isinstance(ttl_seconds, bool) or ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be a positive integer")
        self.ttl_seconds = ttl_seconds
        self._records: dict[str, ApprovalRecord] = {}
        self._lock = threading.RLock()

    def create(
        self, action: str, description: str, binding: str | None = None
    ) -> ApprovalRecord:
        if not isinstance(action, str) or not isinstance(description, str):
            raise TypeError("Action and description must be text")
        action = action.strip()
        description = description.strip()
        if not action or not description:
            raise ValueError("Action and description are required")
        if binding is not None and (not isinstance(binding, str) or not binding):
            raise ValueError("Binding must be a non-empty string")
        now = time.time()
        with self._lock:
            request_id = secrets.token_urlsafe(9)
            while request_id in self._records:
                request_id = secrets.token_urlsafe(9)
            record = ApprovalRecord(
                request_id=request_id,
                action=action[:100],
                description=description[:3500],
                status="pending",
                created_at=now,
                expires_at=now + self.ttl_seconds,
                binding=binding,
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
        with self._lock:
            record = self._get_pending(request_id)
            record.status = "approved"
            return record

    def reject(self, request_id: str) -> ApprovalRecord:
        with self._lock:
            record = self._get_pending(request_id)
            record.status = "rejected"
            return record

    def consume(
        self,
        request_id: str,
        expected_action: str,
        expected_binding: str | None = None,
    ) -> ApprovalRecord:
        """Consume a matching approved request exactly once before an action."""
        with self._lock:
            record = self._records.get(request_id)
            if record is None:
                raise KeyError("Approval request not found")
            if record.status != "approved":
                raise PermissionError("Request has not been approved")
            if time.time() >= record.expires_at:
                record.status = "expired"
                raise TimeoutError("Approval request expired")
            if record.action != expected_action:
                raise PermissionError("Approval does not match the requested action")
            if record.binding != expected_binding:
                raise PermissionError("Approval does not match the exact action payload")
            record.status = "consumed"
            return record

    def get(self, request_id: str) -> ApprovalRecord:
        with self._lock:
            record = self._records.get(request_id)
            if record is None:
                raise KeyError("Approval request not found")
            if record.status in {"pending", "approved"} and time.time() >= record.expires_at:
                record.status = "expired"
            return record

    def pending(self) -> list[ApprovalRecord]:
        return [record for record in self.list() if record.status == "pending"]

    def list(self, limit: int = 50) -> list[ApprovalRecord]:
        if not isinstance(limit, int) or not 1 <= limit <= 200:
            raise ValueError("limit must be between 1 and 200")
        now = time.time()
        with self._lock:
            for record in self._records.values():
                if record.status == "pending" and now >= record.expires_at:
                    record.status = "expired"
            return sorted(
                self._records.values(),
                key=lambda record: record.created_at,
                reverse=True,
            )[:limit]
