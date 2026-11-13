"""Approval-gated execution for explicitly registered in-process agent actions.

This runtime never accepts shell commands, module names, or dynamic code. A
trusted application must register each callable before it can be proposed.
Approval is bound to the exact JSON payload and consumed once before dispatch.
"""
from __future__ import annotations

import hashlib
import json
import secrets
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from core.approval_manager import ApprovalManager, ApprovalRecord

MAX_PAYLOAD_BYTES = 16_384


class AgentExecutionError(RuntimeError):
    """Raised when a registered agent action cannot complete safely."""


@dataclass
class ExecutionRecord:
    execution_id: str
    agent: str
    approval_id: str
    status: str
    created_at: float
    finished_at: float | None = None
    error: str | None = None


AgentHandler = Callable[[dict[str, Any]], Any]


class AgentRuntime:
    """Dispatch only trusted, registered Python handlers after explicit approval."""

    def __init__(self, approvals: ApprovalManager | None = None) -> None:
        self.approvals = approvals or ApprovalManager()
        self._handlers: dict[str, AgentHandler] = {}
        self._payloads: dict[str, dict[str, Any]] = {}
        self.executions: dict[str, ExecutionRecord] = {}

    def register(self, name: str, handler: AgentHandler) -> None:
        if not isinstance(name, str) or not name or name.strip() != name:
            raise ValueError("Agent name must be non-empty and trimmed")
        if name in self._handlers:
            raise ValueError(f"Agent already registered: {name}")
        if not callable(handler):
            raise TypeError("Agent handler must be callable")
        self._handlers[name] = handler

    @staticmethod
    def _serialize_payload(payload: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
        if not isinstance(payload, Mapping):
            raise TypeError("Agent payload must be a JSON object")
        try:
            encoded = json.dumps(
                dict(payload), ensure_ascii=False, sort_keys=True,
                separators=(",", ":"), allow_nan=False,
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("Agent payload must contain only finite JSON values") from exc
        if len(encoded.encode("utf-8")) > MAX_PAYLOAD_BYTES:
            raise ValueError("Agent payload exceeds the 16 KiB limit")
        digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        return json.loads(encoded), digest

    def propose(self, agent: str, payload: Mapping[str, Any]) -> ApprovalRecord:
        if agent not in self._handlers:
            raise KeyError("Agent is not registered")
        safe_payload, digest = self._serialize_payload(payload)
        record = self.approvals.create(
            action=f"agent.run:{agent}",
            description=f"Agentenausführung freigeben: {agent}",
            binding=digest,
            payload=safe_payload,
        )
        return record

    def payload_for(self, approval_id: str) -> dict[str, Any]:
        return self.approvals.payload_for(approval_id)

    def execute(
        self,
        approval_id: str,
        agent: str,
        payload: Mapping[str, Any] | None = None,
    ) -> tuple[ExecutionRecord, Any]:
        handler = self._handlers.get(agent)
        if handler is None:
            raise KeyError("Agent is not registered")
        if payload is None:
            approval_state = self.approvals.get(approval_id)
            if approval_state.status != "approved":
                raise PermissionError("Request has not been approved or was already consumed")
            payload = self.payload_for(approval_id)
        safe_payload, digest = self._serialize_payload(payload)
        approval = self.approvals.consume(
            approval_id, f"agent.run:{agent}", expected_binding=digest
        )
        execution_id = secrets.token_urlsafe(9)
        while execution_id in self.executions:
            execution_id = secrets.token_urlsafe(9)
        record = ExecutionRecord(
            execution_id=execution_id,
            agent=agent,
            approval_id=approval.request_id,
            status="running",
            created_at=time.time(),
        )
        self.executions[execution_id] = record
        self.approvals.save_execution(record)
        try:
            result = handler(safe_payload)
            result_json = json.dumps(
                result, ensure_ascii=False, allow_nan=False, separators=(",", ":")
            )
            if len(result_json.encode("utf-8")) > MAX_PAYLOAD_BYTES:
                raise ValueError("Agent result exceeds the 16 KiB limit")
            safe_result = json.loads(result_json)
        except Exception as exc:
            record.status = "failed"
            record.error = type(exc).__name__
            record.finished_at = time.time()
            self.approvals.save_execution(record)
            raise AgentExecutionError(
                f"Agent action failed ({record.error}); approval was consumed"
            ) from exc
        record.status = "completed"
        record.finished_at = time.time()
        self.approvals.save_execution(record)
        return record, safe_result
