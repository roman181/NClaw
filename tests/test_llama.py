import httpx

from models.llama import LlamaModel
from models.ollama import OllamaClient


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
        host="http://ollama.test",
        transport=httpx.MockTransport(handler),
    )
    model = LlamaModel(client=client, model="llama3.2")
    assert model.generate("Sag Hallo") == "Hallo aus Llama"
    assert seen["url"] == "http://ollama.test/api/chat"
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
