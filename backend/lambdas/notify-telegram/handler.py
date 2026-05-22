import json
import logging
import os
import traceback

import requests

logger = logging.getLogger(__name__)


def send_telegram(token: str, chat_id: str, message: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"}, timeout=10)


def handler(event, context):
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        logger.warning("Telegram credentials not configured")
        return {"sent": False, "reason": "missing_credentials"}

    msg_type = event.get("type", "unknown")
    pipeline = event.get("pipeline", "ETL")
    ts = event.get("timestamp", "")

    if msg_type == "success":
        counts = event.get("counts", {})
        message = (
            f"\u2705 <b>{pipeline} Success</b>\n"
            f"Time: <code>{ts}</code>\n"
            f"Extracted: {counts.get('extracted', '?')}\n"
            f"Transformed: {counts.get('transformed', '?')}\n"
            f"Loaded: {counts.get('loaded', '?')}"
        )
    elif msg_type == "failure":
        error = event.get("error", "Unknown error")
        state = event.get("state", "?")
        cause = event.get("cause", "")
        message = (
            f"\u274c <b>{pipeline} Failed</b>\n"
            f"State: <code>{state}</code>\n"
            f"Time: <code>{ts}</code>\n"
            f"Error: <pre>{error[:300]}</pre>"
        )
        if cause:
            message += f"\nCause: <pre>{cause[:300]}</pre>"
    else:
        message = f"\u2139 Pipeline update: {json.dumps(event)}"

    try:
        send_telegram(token, chat_id, message)
        logger.info("Telegram notification sent: %s", msg_type)
        return {"sent": True}
    except Exception as e:
        logger.error("Failed to send Telegram: %s", e)
        return {"sent": False, "error": str(e)}
