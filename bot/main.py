#!/usr/bin/env python3
"""
Telegram Daily Report Bot
Основная точка входа приложения
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import Config
from bot.handlers import start, report, admin
from services.database import DatabaseService
from services.scheduler import SchedulerService
from utils.logger import get_logger

# Настройка логирования
logger = get_logger(__name__)

async def main():
    """Основная функция запуска бота"""

    # Валидация конфигурации
    try:
        Config.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please check your .env file and set all required variables")
        return

    # Инициализация бота
    bot = Bot(
        token=Config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Инициализация диспетчера
    dp = Dispatcher()

    # Инициализация базы данных
    db_service = DatabaseService(Config.DATABASE_PATH)
    try:
        await db_service.initialize()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return

    # Добавление сервисов в диспетчер
    dp["db"] = db_service

    # Регистрация роутеров (порядок важен!)
    dp.include_router(report.router)  # WebApp данные должны обрабатываться первыми
    dp.include_router(admin.router)   # Админ команды должны быть выше универсального обработчика
    dp.include_router(start.router)

    # Инициализация и запуск планировщика
    scheduler = SchedulerService(bot, db_service)
    await scheduler.start()
    logger.info("Scheduler started successfully")

    try:
        # Получение информации о боте
        bot_info = await bot.get_me()
        logger.info(f"Bot started: @{bot_info.username}")
        logger.info(f"Bot ID: {bot_info.id}")

        # Установка команд бота
        from aiogram.types import BotCommand, BotCommandScopeDefault

        commands = [
            BotCommand(command="admin", description="⚙️ Открыть админ-панель"),
        ]

        await bot.set_my_commands(commands, BotCommandScopeDefault())
        logger.info("Bot commands set successfully")

        # Уведомление админа о запуске
        try:
            await bot.send_message(
                Config.ADMIN_TELEGRAM_ID,
                "🚀 Daily Report Bot запущен!"
            )
        except Exception as e:
            logger.warning(f"Failed to notify admin: {e}")

        # Запуск polling
        logger.info("Starting polling...")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"Error during bot execution: {e}")
    finally:
        # Остановка планировщика
        await scheduler.stop()
        logger.info("Scheduler stopped")

        # Закрытие сессии бота
        await bot.session.close()
        logger.info("Bot session closed")

if __name__ == "__main__":
    try:
        # Запуск бота
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise