"""Static guardrails for the explicitly allowlisted dashboard routes."""
from pathlib import Path

import dashboard.server as dashboard_server


def test_dashboard_controlled_agent_and_inference_apis_are_allowlisted():
    routes = (
        "/api/approvals",
        "/api/agent-executions",
        "/api/agent-actions/propose",
        "/api/inference",
    )
    source = (Path(dashboard_server.__file__)).read_text(encoding="utf-8")
    for route in routes:
        assert route in source
    assert "/api/execute" not in routes
