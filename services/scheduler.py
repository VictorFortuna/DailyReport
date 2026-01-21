"""
Планировщик напоминаний и автоматических задач
"""

import asyncio
from datetime import datetime, time
from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from bot.config import Config
from utils.logger import get_logger

if TYPE_CHECKING:
    from aiogram import Bot
    from services.database import DatabaseService

logger = get_logger(__name__)

class SchedulerService:
    """Сервис планировщика для напоминаний"""

    def __init__(self, bot: "Bot", db: "DatabaseService"):
        self.bot = bot
        self.db = db
        self.scheduler = AsyncIOScheduler(timezone=Config.TIMEZONE)
        self.is_running = False

    async def start(self):
        """Запустить планировщик"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return

        try:
            # Парсинг времени напоминания
            reminder_time = time.fromisoformat(Config.REMINDER_TIME)

            # Добавляем задачу ежедневных напоминаний
            self.scheduler.add_job(
                func=self.send_daily_reminders,
                trigger=CronTrigger(
                    hour=reminder_time.hour,
                    minute=reminder_time.minute,
                    timezone=Config.TIMEZONE
                ),
                id='daily_reminders',
                name='Daily Report Reminders',
                replace_existing=True
            )

            # Добавляем задачу повторных напоминаний
            self.scheduler.add_job(
                func=self.send_repeat_reminders,
                trigger=CronTrigger(
                    hour=(reminder_time.hour +
                          Config.REMINDER_REPEAT_AFTER_MINUTES // 60) % 24,
                    minute=(reminder_time.minute +
                           Config.REMINDER_REPEAT_AFTER_MINUTES % 60) % 60,
                    timezone=Config.TIMEZONE
                ),
                id='repeat_reminders',
                name='Repeat Report Reminders',
                replace_existing=True
            )

            # Запускаем планировщик
            self.scheduler.start()
            self.is_running = True

            logger.info(f"Scheduler started successfully")
            logger.info(f"Daily reminders at: {Config.REMINDER_TIME}")
            logger.info(f"Repeat reminders after: {Config.REMINDER_REPEAT_AFTER_MINUTES} minutes")

        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise

    async def stop(self):
        """Остановить планировщик"""
        if not self.is_running:
            return

        try:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("Scheduler stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")

    async def send_daily_reminders(self):
        """Отправить ежедневные напоминания"""
        try:
            # Получаем текущую дату
            today = datetime.now().strftime('%Y-%m-%d')

            # Получаем пользователей без отчёта за сегодня
            users_without_report = await self.db.get_users_without_report(today)

            if not users_without_report:
                logger.info("All users have submitted reports for today")
                return

            logger.info(f"Sending daily reminders to {len(users_without_report)} users")

            # Отправляем напоминания
            for user in users_without_report:
                try:
                    await self.bot.send_message(
                        user.telegram_id,
                        "⏰ <b>Напоминание о отчёте</b>\n\n"
                        f"👋 {user.full_name.split()[0]}, не забудьте отправить отчёт за сегодня!\n\n"
                        "📊 Нажмите кнопку ниже, чтобы заполнить форму:",
                        reply_markup=self._get_reminder_keyboard()
                    )
                    logger.debug(f"Daily reminder sent to {user.full_name}")

                    # Небольшая пауза между сообщениями
                    await asyncio.sleep(0.1)

                except Exception as e:
                    logger.error(f"Failed to send daily reminder to {user.full_name}: {e}")

        except Exception as e:
            logger.error(f"Error in send_daily_reminders: {e}")

    async def send_repeat_reminders(self):
        """Отправить повторные напоминания"""
        try:
            # Получаем текущую дату
            today = datetime.now().strftime('%Y-%m-%d')

            # Получаем пользователей без отчёта за сегодня
            users_without_report = await self.db.get_users_without_report(today)

            if not users_without_report:
                logger.info("All users have submitted reports - no repeat reminders needed")
                return

            logger.info(f"Sending repeat reminders to {len(users_without_report)} users")

            # Отправляем повторные напоминания
            for user in users_without_report:
                try:
                    await self.bot.send_message(
                        user.telegram_id,
                        "⚠️ <b>Последнее напоминание!</b>\n\n"
                        f"🔔 {user.full_name.split()[0]}, вы ещё не отправили отчёт за сегодня.\n\n"
                        "📋 Пожалуйста, заполните форму отчёта сейчас:\n\n"
                        "⏱️ Отчёты принимаются до конца рабочего дня.",
                        reply_markup=self._get_reminder_keyboard()
                    )
                    logger.debug(f"Repeat reminder sent to {user.full_name}")

                    # Небольшая пауза между сообщениями
                    await asyncio.sleep(0.1)

                except Exception as e:
                    logger.error(f"Failed to send repeat reminder to {user.full_name}: {e}")

        except Exception as e:
            logger.error(f"Error in send_repeat_reminders: {e}")

    async def send_admin_daily_summary(self):
        """Отправить админу ежедневную сводку"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            today_display = datetime.now().strftime('%d.%m.%Y')

            # Получаем отчёты за сегодня
            daily_reports = await self.db.get_daily_reports(today)
            all_users = await self.db.get_all_users(active_only=True)
            users_without_report = await self.db.get_users_without_report(today)

            # Формируем сообщение
            total_users = len(all_users)
            reports_count = len(daily_reports)
            missing_count = len(users_without_report)

            summary_text = (
                f"📊 <b>Ежедневная сводка за {today_display}</b>\n\n"
                f"👥 <b>Всего сотрудников:</b> {total_users}\n"
                f"✅ <b>Отчёты отправлены:</b> {reports_count}\n"
                f"❌ <b>Отчёты не отправлены:</b> {missing_count}\n\n"
            )

            if reports_count > 0:
                summary_text += "📋 <b>Отправили отчёт:</b>\n"
                for report in daily_reports:
                    time_str = datetime.fromisoformat(report['submitted_at']).strftime('%H:%M')
                    summary_text += f"• {report['full_name']} - {time_str}\n"
                summary_text += "\n"

            if missing_count > 0:
                summary_text += "⚠️ <b>Не отправили отчёт:</b>\n"
                for user in users_without_report:
                    summary_text += f"• {user.full_name}\n"

            # Отправляем админу
            await self.bot.send_message(
                Config.ADMIN_TELEGRAM_ID,
                summary_text
            )

            logger.info(f"Daily summary sent to admin: {reports_count}/{total_users} reports")

        except Exception as e:
            logger.error(f"Error sending admin daily summary: {e}")

    def _get_reminder_keyboard(self):
        """Получить клавиатуру для напоминания"""
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        from aiogram.types.web_app_info import WebAppInfo

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="📊 Отправить отчёт",
                web_app=WebAppInfo(url=Config.WEBAPP_URL)
            )],
            [InlineKeyboardButton(
                text="📈 Мой статус",
                callback_data="check_status"
            )]
        ])
        return keyboard

    def get_status(self) -> dict:
        """Получить статус планировщика"""
        return {
            'is_running': self.is_running,
            'jobs': [
                {
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in self.scheduler.get_jobs()
            ] if self.is_running else []
        }