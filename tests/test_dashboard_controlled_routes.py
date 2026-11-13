"""Unit tests for the explicit, installed-model inference allowlist."""
import pytest

import dashboard.server as dashboard_server


def test_run_model_inference_uses_only_an_installed_model(monkeypatch):
    monkeypatch.setattr(dashboard_server, "ollama_models", lambda: {
        "ok": True,
        "available": True,
        "models": [{"name": "llama3.2:latest"}],
    })
    captured = {}

    class FakeClient:
        def __init__(self, timeout):
            captured["timeout"] = timeout

    class FakeModel:
        def __init__(self, client, model):
            captured["client"] = client
            captured["model"] = model

        def generate(self, prompt):
            captured["prompt"] = prompt
            return "Antwort"

    monkeypatch.setattr(dashboard_server, "OllamaClient", FakeClient)
    monkeypatch.setattr(dashboard_server, "LlamaModel", FakeModel)

    assert dashboard_server.run_model_inference("llama3.2:latest", "Hallo") == "Antwort"
    assert captured["timeout"] == 60
    assert captured["model"] == "llama3.2:latest"
    assert captured["prompt"] == "Hallo"

    with pytest.raises(ValueError, match="not available"):
        dashboard_server.run_model_inference("unlisted-model", "Hallo")
