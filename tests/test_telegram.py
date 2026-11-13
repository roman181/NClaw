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
    return {"update_id": 12, "message": {"chat": {"id": chat_id}, "text": text}}


def test_rejects_unapproved_chat(tmp_path) -> None:
    telegram = FakeTelegram()
    agent = TelegramAgent(telegram, "123", llama=FakeLlama(), workspace=tmp_path)  # type: ignore[arg-type]
    agent.handle_update(make_update(999, "/help"))
    assert telegram.sent == []


def test_help_command(tmp_path) -> None:
    telegram = FakeTelegram()
    agent = TelegramAgent(telegram, "123", llama=FakeLlama(), workspace=tmp_path)  # type: ignore[arg-type]
    agent.handle_update(make_update(123, "/help"))
    assert agent_help_has(telegram, "/ask")
    assert "/propose_file" in telegram.sent[0][1]


def agent_help_has(telegram: FakeTelegram, command: str) -> bool:
    return command in telegram.sent[0][1]


def test_ask_uses_llama(tmp_path) -> None:
    telegram = FakeTelegram()
    llama = FakeLlama()
    agent = TelegramAgent(telegram, "123", llama=llama, workspace=tmp_path)  # type: ignore[arg-type]
    agent.handle_update(make_update(123, "/ask Erkläre NClaw"))
    assert llama.prompt == "Erkläre NClaw"
    assert "Telegram-Agent" in llama.system
    assert telegram.sent[-1][1] == "Hallo aus Llama."


def test_unknown_command_does_not_execute_anything(tmp_path) -> None:
    telegram = FakeTelegram()
    agent = TelegramAgent(telegram, "123", llama=FakeLlama(), workspace=tmp_path)  # type: ignore[arg-type]
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


def test_request_creates_pending_approval(tmp_path) -> None:
    telegram = FakeTelegram()
    agent = TelegramAgent(telegram, "123", llama=FakeLlama(), workspace=tmp_path)  # type: ignore[arg-type]
    agent.handle_update(make_update(123, "/request publish | Release v0.1"))
    assert "Freigabe angelegt" in telegram.sent[-1][1]
    assert "führt selbst noch nichts aus" in telegram.sent[-1][1]
    assert len(agent.approvals.pending()) == 1


def test_approve_and_deny_commands_are_allowlisted(tmp_path) -> None:
    telegram = FakeTelegram()
    agent = TelegramAgent(telegram, "123", llama=FakeLlama(), workspace=tmp_path)  # type: ignore[arg-type]
    request = agent.approvals.create("publish", "Release v0.1")
    agent.handle_update(make_update(999, f"/approve {request.request_id}"))
    assert request.status == "pending"
    agent.handle_update(make_update(123, f"/approve {request.request_id}"))
    assert request.status == "approved"
    assert "Freigabe allein führt noch keine Aktion aus" in telegram.sent[-1][1]


def test_file_requires_approval_then_separate_execute(tmp_path) -> None:
    telegram = FakeTelegram()
    agent = TelegramAgent(telegram, "123", llama=FakeLlama(), workspace=tmp_path)  # type: ignore[arg-type]
    agent.handle_update(make_update(123, "/propose_file notes.txt | Hallo NClaw"))
    request_id = next(iter(agent._file_proposals))
    assert not (tmp_path / "notes.txt").exists()
    assert "Exakter Inhalt:" in telegram.sent[-1][1]

    agent.handle_update(make_update(123, f"/execute {request_id}"))
    assert not (tmp_path / "notes.txt").exists()

    agent.handle_update(make_update(123, f"/approve {request_id}"))
    assert not (tmp_path / "notes.txt").exists()

    agent.handle_update(make_update(123, f"/execute {request_id}"))
    assert (tmp_path / "notes.txt").read_text(encoding="utf-8") == "Hallo NClaw"
    assert "Datei erstellt" in telegram.sent[-1][1]


def test_file_action_cannot_overwrite_existing_file(tmp_path) -> None:
    (tmp_path / "notes.txt").write_text("original", encoding="utf-8")
    telegram = FakeTelegram()
    agent = TelegramAgent(telegram, "123", llama=FakeLlama(), workspace=tmp_path)  # type: ignore[arg-type]
    agent.handle_update(make_update(123, "/propose_file notes.txt | changed"))
    assert "Dateivorschlag abgelehnt" in telegram.sent[-1][1]
    assert (tmp_path / "notes.txt").read_text(encoding="utf-8") == "original"


def test_unauthorized_chat_cannot_execute_file_proposal(tmp_path) -> None:
    telegram = FakeTelegram()
    agent = TelegramAgent(telegram, "123", llama=FakeLlama(), workspace=tmp_path)  # type: ignore[arg-type]
    agent.handle_update(make_update(123, "/propose_file notes.txt | safe"))
    request_id = next(iter(agent._file_proposals))
    agent.handle_update(make_update(999, f"/approve {request_id}"))
    agent.handle_update(make_update(999, f"/execute {request_id}"))
    assert not (tmp_path / "notes.txt").exists()
