"""
bot.py — локальний запуск через polling (для тестів): python bot.py
Уся логіка — в bot_core.py. На проді бот працює через webhook (api/telegram.py).
"""

import asyncio
import logging

from telegram import Update

from bot_core import build_application, sync_commands

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


async def main_async() -> None:
    logger.info("Запуск LexMind Bot (polling, локально)...")
    app = build_application()
    await app.initialize()
    await sync_commands(app)
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("Бот у polling-режимі. Зупинити: Ctrl+C")

    stop_event = asyncio.Event()
    try:
        await stop_event.wait()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        logger.info("Зупинка бота...")
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main_async())
