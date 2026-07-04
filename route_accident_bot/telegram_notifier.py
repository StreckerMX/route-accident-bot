"""Notificaciones por Telegram Bot API."""

from __future__ import annotations

import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_MESSAGE_LENGTH = 4096


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token.strip()
        self.chat_id = chat_id.strip()
        self.enabled = bool(self.bot_token and self.chat_id)

    def send(self, message: str, parse_mode: str | None = "HTML") -> bool:
        if not self.enabled:
            return False

        text = message[:MAX_MESSAGE_LENGTH]
        url = TELEGRAM_API.format(token=self.bot_token)

        payload: dict = {
            "chat_id": self.chat_id,
            "text": text,
            "disable_web_page_preview": False,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode

        response = requests.post(url, json=payload, timeout=15)

        if response.status_code == 200:
            return True

        # Reintento sin HTML si el parseo falla
        if parse_mode == "HTML":
            response = requests.post(
                url,
                json={
                    "chat_id": self.chat_id,
                    "text": text.replace("<b>", "").replace("</b>", "")
                    .replace("<i>", "").replace("</i>", ""),
                    "disable_web_page_preview": False,
                },
                timeout=15,
            )
            return response.status_code == 200

        response.raise_for_status()
        return False