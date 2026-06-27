"""
api/telegram.py — Vercel serverless webhook endpoint (Flask / WSGI).

Vercel виявляє `app` (Flask WSGI callable) як entrypoint.

POST /api/telegram — приймає Update від Telegram і передає боту.
GET  /api/ping     — warm-up (Vercel cron / зовнішній пінгер).
GET  /api/telegram — health-check.

Application тримається в пам'яті теплого контейнера; на холодному старті
ConversationHandler-стан скидається — нормально для serverless.
"""

import asyncio
import logging
import os
import sys

# api/ треба прибрати з sys.path ДО імпортів: файл api/telegram.py має те саме
# ім'я, що й пакет python-telegram-bot → інакше circular import.
_api_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_api_dir)
if _api_dir in sys.path:
    sys.path.remove(_api_dir)
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

from flask import Flask, request
from telegram import Update
from bot_core import build_application

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

_tg_app = None
_loop = None


def _get_loop() -> asyncio.AbstractEventLoop:
    global _loop, _tg_app
    if _loop is None or _loop.is_closed():
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
        _tg_app = None
    return _loop


def _get_tg_app():
    global _tg_app
    loop = _get_loop()
    if _tg_app is None:
        logger.info("Cold start: ініціалізація Application")
        _tg_app = build_application()
        loop.run_until_complete(_tg_app.initialize())
    return _tg_app


@app.route("/api/telegram", methods=["GET"])
@app.route("/api/ping", methods=["GET"])
@app.route("/", methods=["GET"])
def health():
    try:
        _get_tg_app()  # прогрів, щоб cold start не вдарив по webhook
    except Exception:
        pass
    return "LexMind bot webhook is alive", 200


@app.route("/api/telegram", methods=["POST"])
@app.route("/", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return "Bad Request: empty body", 400
        tg_app = _get_tg_app()
        loop = _get_loop()
        update = Update.de_json(data, tg_app.bot)
        loop.run_until_complete(tg_app.process_update(update))
        return "OK", 200
    except Exception as e:
        logger.error("Помилка обробки update: %s", e)
        return "Internal Server Error", 500
