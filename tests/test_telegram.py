"""Tests for the allowlisted Telegram agent."""
from __future__ import annotations

import httpx

from agents.telegram.bot import TelegramAgent, TelegramClient


class FakeLlama:
    def __init__(self) -> None:
        self.prompt = ""
        self.system = ""

    def generate(self, prompt: str, system: str | None = None) -> str:
        self.prompt = prompt
        self.system = system or ""
        return "Hallo aus Llama."


class FakeTelegram:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    def send_message(self, chat_id: str, text: str) -> None:
        self.sent.append((chat_id, text))


def make_update(chat_id: int, text: str) -> dict:
    return {
        "update_id": 12,
        "message": {"chat": {"id": chat_id}, "text": text},
    }


def test_rejects_unapproved_chat() -> None:
    telegram = FakeTelegram()
    agent = TelegramAgent(telegram, "123", llama=FakeLlama())  # type: ignore[arg-type]
    agent.handle_update(make_update(999, "/help"))
    assert telegram.sent == []


def test_help_command() -> None:
    telegram = FakeTelegram()
    agent = TelegramAgent(telegram, "123", llama=FakeLlama())  # type: ignore[arg-type]
    agent.handle_update(make_update(123, "/help"))
    assert telegram.sent[0][0] == "123"
    assert "/ask" in telegram.sent[0][1]


def test_ask_uses_llama() -> None:
    telegram = FakeTelegram()
    llama = FakeLlama()
    agent = TelegramAgent(telegram, "123", llama=llama)  # type: ignore[arg-type]
    agent.handle_update(make_update(123, "/ask Erkläre NClaw"))
    assert llama.prompt == "Erkläre NClaw"
    assert "Telegram-Agent" in llama.system
    assert telegram.sent[-1][1] == "Hallo aus Llama."


def test_unknown_command_does_not_execute_anything() -> None:
    telegram = FakeTelegram()
    agent = TelegramAgent(telegram, "123", llama=FakeLlama())  # type: ignore[arg-type]
    agent.handle_update(make_update(123, "/shell rm -rf /"))
    assert "Unbekannter Befehl" in telegram.sent[-1][1]


def test_telegram_client_sends_bot_api_request() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"ok": True, "result": True})

    http = httpx.Client(transport=httpx.MockTransport(handler))
    client = TelegramClient("test-token", http_client=http)
    client.send_message("123", "Test")
    assert requests[0].url.path.endswith("/sendMessage")
    assert requests[0].read() == b'{"chat_id":"123","text":"Test"}'
    http.close()
