"""
Административные команды и панель управления
"""

from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from bot.keyboards import (
    get_admin_keyboard,
    get_admin_users_keyboard,
    get_admin_user_actions_keyboard,
    get_confirmation_keyboard,
    get_back_keyboard
)
from services.database import DatabaseService
from bot.config import Config
from utils.logger import get_logger

logger = get_logger(__name__)
router = Router()

def is_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    return user_id == Config.ADMIN_TELEGRAM_ID

@router.message(Command("admin"))
async def admin_panel(message: Message, db: DatabaseService):
    """Главная админ-панель"""

    logger.info(f"Admin command called by user {message.from_user.id}")

    if not is_admin(message.from_user.id):
        logger.warning(f"Unauthorized admin access attempt by {message.from_user.id}")
        await message.answer("❌ Доступ запрещён. Только для администраторов.")
        return

    today = datetime.now().strftime('%d.%m.%Y')

    try:
        # Получаем базовую статистику
        all_users = await db.get_all_users(active_only=True)
        today_reports = await db.get_daily_reports(datetime.now().strftime('%Y-%m-%d'))
        logger.info(f"Admin stats: {len(all_users)} users, {len(today_reports)} reports")
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        await message.answer("❌ Ошибка получения статистики. Проверьте логи.")
        return

    await message.answer(
        f"👨‍💼 <b>Административная панель</b>\n\n"
        f"📅 <b>Дата:</b> {today}\n"
        f"👥 <b>Активных сотрудников:</b> {len(all_users)}\n"
        f"📊 <b>Отчётов за сегодня:</b> {len(today_reports)}\n"
        f"📈 <b>Процент выполнения:</b> {round(len(today_reports) / len(all_users) * 100) if all_users else 0}%\n\n"
        f"Выберите действие:",
        reply_markup=get_admin_keyboard()
    )

@router.callback_query(F.data == "admin_today_status")
async def admin_today_status(callback: CallbackQuery, db: DatabaseService):
    """Статус отчётов за сегодня"""

    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    today = datetime.now().strftime('%Y-%m-%d')
    today_display = datetime.now().strftime('%d.%m.%Y')

    # Получаем данные
    all_users = await db.get_all_users(active_only=True)
    daily_reports = await db.get_daily_reports(today)
    users_without_report = await db.get_users_without_report(today)

    # Формируем сообщение
    status_text = f"📊 <b>Отчёты за {today_display}</b>\n\n"

    if daily_reports:
        status_text += f"✅ <b>Отправили отчёт ({len(daily_reports)}):</b>\n"
        for report in daily_reports:
            time_str = datetime.fromisoformat(report['submitted_at']).strftime('%H:%M')
            calls = report['calls_count']
            resultative = report['kp_plus'] + report['kp']
            conversion = round((resultative / calls) * 100, 1) if calls > 0 else 0
            status_text += f"• {report['full_name']} - {time_str} ({calls} звонков, {conversion}%)\n"
        status_text += "\n"

    if users_without_report:
        status_text += f"❌ <b>Не отправили отчёт ({len(users_without_report)}):</b>\n"
        for user in users_without_report:
            status_text += f"• {user.full_name}\n"
        status_text += "\n"

    status_text += f"📈 <b>Общая статистика:</b>\n"
    status_text += f"👥 Всего сотрудников: {len(all_users)}\n"
    status_text += f"✅ Отправлено: {len(daily_reports)}\n"
    status_text += f"❌ Не отправлено: {len(users_without_report)}\n"
    status_text += f"📊 Процент выполнения: {round(len(daily_reports) / len(all_users) * 100) if all_users else 0}%"

    await callback.message.edit_text(status_text, reply_markup=get_admin_keyboard())
    await callback.answer()

@router.callback_query(F.data == "admin_users_list")
async def admin_users_list(callback: CallbackQuery, db: DatabaseService):
    """Список всех пользователей"""

    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    users = await db.get_all_users(active_only=False)

    if not users:
        await callback.message.edit_text(
            "👥 <b>Список сотрудников пуст</b>\n\n"
            "Пользователи появятся здесь после регистрации через /start",
            reply_markup=get_admin_keyboard()
        )
        await callback.answer()
        return

    active_users = [u for u in users if u.is_active]
    inactive_users = [u for u in users if not u.is_active]

    users_text = f"👥 <b>Список сотрудников ({len(users)})</b>\n\n"
    users_text += f"✅ <b>Активные ({len(active_users)}):</b>\n"

    for user in active_users[:10]:  # Показываем максимум 10
        reg_date = user.created_at.strftime('%d.%m.%Y') if user.created_at else "—"
        users_text += f"• {user.full_name} (с {reg_date})\n"

    if len(active_users) > 10:
        users_text += f"... и ещё {len(active_users) - 10}\n"

    if inactive_users:
        users_text += f"\n❌ <b>Неактивные ({len(inactive_users)}):</b>\n"
        for user in inactive_users[:5]:
            users_text += f"• {user.full_name}\n"

    await callback.message.edit_text(
        users_text,
        reply_markup=get_admin_users_keyboard(users[:20])  # Показываем кнопки для первых 20
    )
    await callback.answer()

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery, db: DatabaseService):
    """Общая статистика"""

    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    # Получаем данные за последние 7 дней
    stats_text = "📈 <b>Статистика системы</b>\n\n"

    all_users = await db.get_all_users(active_only=False)
    active_users = [u for u in all_users if u.is_active]

    stats_text += f"👥 <b>Пользователи:</b>\n"
    stats_text += f"• Всего зарегистрировано: {len(all_users)}\n"
    stats_text += f"• Активных: {len(active_users)}\n"
    stats_text += f"• Неактивных: {len(all_users) - len(active_users)}\n\n"

    # Статистика по дням
    today = datetime.now().strftime('%Y-%m-%d')
    today_reports = await db.get_daily_reports(today)

    stats_text += f"📊 <b>Отчёты за сегодня:</b>\n"
    stats_text += f"• Отправлено: {len(today_reports)}\n"
    stats_text += f"• Ожидается: {len(active_users) - len(today_reports)}\n"
    stats_text += f"• Выполнение: {round(len(today_reports) / len(active_users) * 100) if active_users else 0}%\n\n"

    if today_reports:
        total_calls = sum(r['calls_count'] for r in today_reports)
        total_resultative = sum(r['kp_plus'] + r['kp'] for r in today_reports)
        avg_conversion = round((total_resultative / total_calls) * 100, 1) if total_calls > 0 else 0

        stats_text += f"📞 <b>Показатели за сегодня:</b>\n"
        stats_text += f"• Всего звонков: {total_calls}\n"
        stats_text += f"• Результативных: {total_resultative}\n"
        stats_text += f"• Средняя конверсия: {avg_conversion}%\n"

    await callback.message.edit_text(stats_text, reply_markup=get_admin_keyboard())
    await callback.answer()

@router.callback_query(F.data == "admin_settings")
async def admin_settings(callback: CallbackQuery):
    """Настройки системы"""

    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    settings_text = (
        f"⚙️ <b>Настройки системы</b>\n\n"
        f"🕐 <b>Время напоминаний:</b> {Config.REMINDER_TIME}\n"
        f"🔄 <b>Повтор через:</b> {Config.REMINDER_REPEAT_AFTER_MINUTES} мин\n"
        f"🌍 <b>Часовой пояс:</b> {Config.TIMEZONE}\n"
        f"📱 <b>Mini App URL:</b> {Config.WEBAPP_URL}\n"
        f"🗄️ <b>База данных:</b> {Config.DATABASE_PATH}\n"
        f"📊 <b>Google Sheets:</b> {'✅ Настроено' if Config.GOOGLE_SPREADSHEET_ID != 'YOUR_SPREADSHEET_ID_HERE' else '❌ Не настроено'}\n\n"
        f"💡 <i>Настройки изменяются в файле .env</i>"
    )

    await callback.message.edit_text(settings_text, reply_markup=get_admin_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("admin_user_"))
async def admin_user_details(callback: CallbackQuery, db: DatabaseService):
    """Детали пользователя"""

    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    try:
        user_id = int(callback.data.split("_")[-1])
        # Здесь можно добавить детальную информацию о пользователе
        await callback.answer("🚧 Функция в разработке")
    except ValueError:
        await callback.answer("❌ Ошибка получения данных пользователя")

@router.callback_query(F.data.in_(["admin_refresh", "admin_back"]))
async def admin_refresh(callback: CallbackQuery, db: DatabaseService):
    """Обновление админ-панели"""

    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    await admin_panel(callback.message, db)
    await callback.answer("✅ Обновлено")