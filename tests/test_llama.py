import httpx
import pytest

from models.llama import LlamaModel
from models.ollama import OllamaClient, OllamaError


def test_llama_uses_single_configured_model():
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["payload"] = request.read().decode()
        return httpx.Response(
            200,
            json={"message": {"content": "Hallo aus Llama"}},
        )

    client = OllamaClient(
        host="http://ollama.local",
        transport=httpx.MockTransport(handler),
    )
    model = LlamaModel(client=client, model="llama3.2")
    assert model.generate("Sag Hallo") == "Hallo aus Llama"
    assert seen["url"] == "http://ollama.local/api/chat"
    assert '"model":"llama3.2"' in seen["payload"]


def test_llama_can_add_system_instruction():
    captured = {}

    def handler(request):
        captured["body"] = request.read().decode()
        return httpx.Response(200, json={"message": {"content": "OK"}})

    model = LlamaModel(
        client=OllamaClient(transport=httpx.MockTransport(handler))
    )
    assert model.generate("Test", system="Antworte kurz") == "OK"
    assert '"role":"system"' in captured["body"]


@pytest.mark.parametrize(
    "host",
    [
        "https://example.com",
        "http://user:password@127.0.0.1:11434",
        "http://127.0.0.1:11434/path",
        "http://127.0.0.1:11434?token=x",
    ],
)
def test_ollama_rejects_unsafe_hosts(host):
    with pytest.raises(ValueError):
        OllamaClient(host=host)


def test_ollama_rejects_unbounded_timeout_and_prompt():
    with pytest.raises(ValueError):
        OllamaClient(timeout=121)
    model = LlamaModel(client=OllamaClient(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json={"message": {"content": "OK"}})
    )))
    with pytest.raises(ValueError):
        model.generate("x" * 16_001)


def test_ollama_does_not_follow_redirects():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(307, headers={"Location": "https://example.com/api/chat"})

    client = OllamaClient(transport=httpx.MockTransport(handler))
    with pytest.raises(OllamaError):
        client.chat("llama3.2", "Hallo")
    assert len(seen) == 1


def test_ollama_rejects_oversized_response():
    client = OllamaClient(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, content=b"x" * 65_537)
    ))
    with pytest.raises(OllamaError, match="64 KiB"):
        client.chat("llama3.2", "Hallo")
