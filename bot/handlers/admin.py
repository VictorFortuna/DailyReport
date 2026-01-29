"""
Административные команды и панель управления
"""

from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.keyboards import (
    get_admin_keyboard,
    get_admin_users_keyboard,
    get_admin_user_actions_keyboard,
    get_admin_registrations_keyboard,
    get_registration_actions_keyboard,
    get_confirmation_keyboard,
    get_back_keyboard
)
from services.database import DatabaseService
from bot.config import Config
from utils.logger import get_logger
from utils.timezone import format_moscow_time

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

    current_time = format_moscow_time(datetime.now(), '%H:%M:%S')

    await message.answer(
        f"👨‍💼 <b>Административная панель</b>\n\n"
        f"📅 <b>Дата:</b> {today}\n"
        f"👥 <b>Активных сотрудников:</b> {len(all_users)}\n"
        f"📊 <b>Отчётов за сегодня:</b> {len(today_reports)}\n"
        f"📈 <b>Процент выполнения:</b> {round(len(today_reports) / len(all_users) * 100) if all_users else 0}%\n"
        f"🔄 <b>Открыто:</b> {current_time}\n\n"
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
            time_str = format_moscow_time(datetime.fromisoformat(report['submitted_at']))
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

        # Получаем пользователя
        users = await db.get_all_users(active_only=False)
        user = next((u for u in users if u.id == user_id), None)

        if not user:
            await callback.answer("❌ Пользователь не найден")
            return

        # Получаем статистику пользователя
        today = datetime.now().strftime('%Y-%m-%d')
        today_reports = await db.get_daily_reports(today)
        user_reports = [r for r in today_reports if r.get('telegram_id') == user.telegram_id]

        status_emoji = "✅" if user.is_active else "❌"
        reg_date = format_moscow_time(user.created_at, '%d.%m.%Y %H:%M') if user.created_at else 'Неизвестно'

        user_text = (
            f"👤 <b>Информация о сотруднике</b>\n\n"
            f"📝 <b>ФИО:</b> {user.full_name}\n"
            f"🆔 <b>Telegram ID:</b> <code>{user.telegram_id}</code>\n"
            f"📱 <b>Username:</b> @{user.username or 'отсутствует'}\n"
            f"{status_emoji} <b>Статус:</b> {'Активный' if user.is_active else 'Неактивный'}\n"
            f"📅 <b>Зарегистрирован:</b> {reg_date}\n\n"
            f"📊 <b>Отчёт за сегодня:</b> {'✅ Отправлен' if user_reports else '❌ Не отправлен'}\n\n"
            f"Выберите действие:"
        )

        await callback.message.edit_text(
            user_text,
            reply_markup=get_admin_user_actions_keyboard(user.id)
        )
        await callback.answer()

    except ValueError:
        await callback.answer("❌ Ошибка получения данных пользователя")

@router.callback_query(F.data.startswith("admin_delete_"))
async def admin_delete_user_confirm(callback: CallbackQuery, db: DatabaseService):
    """Подтверждение удаления пользователя"""

    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    try:
        user_id = int(callback.data.split("_")[-1])

        # Получаем пользователя
        users = await db.get_all_users(active_only=False)
        user = next((u for u in users if u.id == user_id), None)

        if not user:
            await callback.answer("❌ Пользователь не найден")
            return

        confirm_text = (
            f"⚠️ <b>Подтверждение удаления</b>\n\n"
            f"👤 <b>Пользователь:</b> {user.full_name}\n"
            f"🆔 <b>ID:</b> <code>{user.telegram_id}</code>\n\n"
            f"❗️ <b>Внимание!</b> Это действие:\n"
            f"• Удалит пользователя из базы данных\n"
            f"• Удалит все его отчёты\n"
            f"• Нельзя будет отменить\n\n"
            f"Вы уверены, что хотите удалить этого пользователя?"
        )

        # Используем confirmation keyboard с уникальным action
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑 Да, удалить", callback_data=f"confirm_delete_user_{user_id}"),
                InlineKeyboardButton(text="❌ Отмена", callback_data=f"admin_user_{user_id}")
            ]
        ])

        await callback.message.edit_text(confirm_text, reply_markup=keyboard)
        await callback.answer()

    except ValueError:
        await callback.answer("❌ Ошибка получения данных пользователя")

@router.callback_query(F.data.startswith("confirm_delete_user_"))
async def admin_delete_user_execute(callback: CallbackQuery, db: DatabaseService):
    """Выполнение удаления пользователя"""

    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    try:
        user_id = int(callback.data.split("_")[-1])

        # Получаем пользователя перед удалением
        users = await db.get_all_users(active_only=False)
        user = next((u for u in users if u.id == user_id), None)

        if not user:
            await callback.answer("❌ Пользователь не найден")
            return

        # Удаляем пользователя (с каскадным удалением отчётов)
        success = await db.delete_user(user_id)

        if success:
            # Уведомляем пользователя об удалении
            try:
                bot = callback.bot
                await bot.send_message(
                    user.telegram_id,
                    f"❌ <b>Аккаунт удален</b>\n\n"
                    f"Ваш аккаунт был удален администратором.\n"
                    f"Все ваши данные и отчёты были удалены из системы.\n\n"
                    f"Для повторного доступа к боту потребуется новая регистрация."
                )
            except Exception as e:
                logger.warning(f"Failed to notify deleted user {user.telegram_id}: {e}")

            result_text = (
                f"✅ <b>Пользователь удален</b>\n\n"
                f"👤 <b>Удалён:</b> {user.full_name}\n"
                f"🆔 <b>ID:</b> <code>{user.telegram_id}</code>\n\n"
                f"📝 Пользователь и все его отчёты удалены из системы.\n"
                f"📧 Отправлено уведомление пользователю."
            )

            await callback.message.edit_text(
                result_text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="👥 К списку сотрудников", callback_data="admin_users_list")],
                    [InlineKeyboardButton(text="🔙 В админ-панель", callback_data="admin_back")]
                ])
            )
            await callback.answer("✅ Пользователь удален")
            logger.info(f"Admin {callback.from_user.id} deleted user: {user.full_name} ({user.telegram_id})")
        else:
            await callback.answer("❌ Ошибка при удалении пользователя", show_alert=True)

    except ValueError:
        await callback.answer("❌ Ошибка получения данных пользователя")

@router.callback_query(F.data.in_(["admin_refresh", "admin_back"]))
async def admin_refresh(callback: CallbackQuery, db: DatabaseService):
    """Обновление админ-панели"""

    logger.info(f"Admin callback {callback.data} from user {callback.from_user.id}")

    if not is_admin(callback.from_user.id):
        logger.warning(f"Unauthorized admin callback {callback.data} attempt by {callback.from_user.id}")
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    # Генерируем админ-панель напрямую (без вызова admin_panel с callback.message)
    today = datetime.now().strftime('%d.%m.%Y')

    try:
        # Получаем базовую статистику
        all_users = await db.get_all_users(active_only=True)
        today_reports = await db.get_daily_reports(datetime.now().strftime('%Y-%m-%d'))
        logger.info(f"Admin stats: {len(all_users)} users, {len(today_reports)} reports")
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        await callback.message.edit_text("❌ Ошибка получения статистики. Проверьте логи.")
        await callback.answer()
        return

    # Добавляем временную метку чтобы избежать ошибки "message is not modified"
    current_time = format_moscow_time(datetime.now(), '%H:%M:%S')

    await callback.message.edit_text(
        f"👨‍💼 <b>Административная панель</b>\n\n"
        f"📅 <b>Дата:</b> {today}\n"
        f"👥 <b>Активных сотрудников:</b> {len(all_users)}\n"
        f"📊 <b>Отчётов за сегодня:</b> {len(today_reports)}\n"
        f"📈 <b>Процент выполнения:</b> {round(len(today_reports) / len(all_users) * 100) if all_users else 0}%\n"
        f"🔄 <b>Обновлено:</b> {current_time}\n\n"
        f"Выберите действие:",
        reply_markup=get_admin_keyboard()
    )
    await callback.answer("✅ Обновлено")

@router.callback_query(F.data == "admin_registrations")
async def admin_registrations_list(callback: CallbackQuery, db: DatabaseService):
    """Список заявок на регистрацию"""

    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    pending_registrations = await db.get_pending_registrations('pending')
    all_registrations = await db.get_pending_registrations()

    approved_count = len([r for r in all_registrations if r.status == 'approved'])
    rejected_count = len([r for r in all_registrations if r.status == 'rejected'])

    if not pending_registrations and not all_registrations:
        registrations_text = (
            "📋 <b>Заявки на регистрацию</b>\n\n"
            "📭 <b>Нет заявок</b>\n\n"
            "Заявки будут отображаться здесь после того, как новые пользователи "
            "попытаются зарегистрироваться через /start"
        )
        await callback.message.edit_text(registrations_text, reply_markup=get_admin_keyboard())
        await callback.answer()
        return

    registrations_text = f"📋 <b>Заявки на регистрацию</b>\n\n"
    registrations_text += f"⏳ <b>Ожидают рассмотрения:</b> {len(pending_registrations)}\n"
    registrations_text += f"✅ <b>Одобрено:</b> {approved_count}\n"
    registrations_text += f"❌ <b>Отклонено:</b> {rejected_count}\n\n"

    if pending_registrations:
        registrations_text += "📋 <b>Новые заявки:</b>\n"
        for reg in pending_registrations[:5]:  # Показываем максимум 5
            reg_time = format_moscow_time(reg.requested_at, '%d.%m %H:%M') if reg.requested_at else '—'
            registrations_text += f"• {reg.full_name} ({reg_time})\n"

        if len(pending_registrations) > 5:
            registrations_text += f"... и ещё {len(pending_registrations) - 5}\n\n"

        registrations_text += "Выберите заявку для просмотра:"
    else:
        registrations_text += "✅ Все заявки рассмотрены"

    # Показываем только pending заявки в кнопках
    keyboard = get_admin_registrations_keyboard(pending_registrations)

    await callback.message.edit_text(registrations_text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("admin_reg_"))
async def admin_registration_details(callback: CallbackQuery, db: DatabaseService):
    """Детали заявки на регистрацию"""

    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    try:
        registration_id = int(callback.data.split("_")[-1])
    except ValueError:
        await callback.answer("❌ Ошибка получения данных заявки")
        return

    # Получаем заявку из базы
    registrations = await db.get_pending_registrations()
    registration = next((r for r in registrations if r.id == registration_id), None)

    if not registration:
        await callback.message.edit_text(
            "❌ <b>Заявка не найдена</b>\n\n"
            "Возможно, заявка была удалена или обработана.",
            reply_markup=get_admin_registrations_keyboard([])
        )
        await callback.answer()
        return

    status_emoji = {
        'pending': '⏳',
        'approved': '✅',
        'rejected': '❌'
    }
    status_text = {
        'pending': 'Ожидает рассмотрения',
        'approved': 'Одобрена',
        'rejected': 'Отклонена'
    }

    reg_time = format_moscow_time(registration.requested_at, '%d.%m.%Y %H:%M') if registration.requested_at else 'Неизвестно'

    details_text = (
        f"📋 <b>Заявка на регистрацию #{registration.id}</b>\n\n"
        f"👤 <b>ФИО:</b> {registration.full_name}\n"
        f"🆔 <b>Telegram ID:</b> <code>{registration.telegram_id}</code>\n"
        f"📱 <b>Username:</b> @{registration.username or 'отсутствует'}\n"
        f"📅 <b>Подана:</b> {reg_time}\n"
        f"{status_emoji.get(registration.status, '❓')} <b>Статус:</b> {status_text.get(registration.status, 'Неизвестен')}\n\n"
    )

    if registration.status == 'pending':
        details_text += "Выберите действие:"

    await callback.message.edit_text(
        details_text,
        reply_markup=get_registration_actions_keyboard(registration.id, registration.status)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("approve_reg_"))
async def approve_registration(callback: CallbackQuery, db: DatabaseService):
    """Одобрить заявку на регистрацию"""

    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    try:
        registration_id = int(callback.data.split("_")[-1])
    except ValueError:
        await callback.answer("❌ Ошибка получения данных заявки")
        return

    # Получаем данные заявки перед одобрением
    registrations = await db.get_pending_registrations()
    registration = next((r for r in registrations if r.id == registration_id), None)

    if not registration or registration.status != 'pending':
        await callback.answer("❌ Заявка недоступна для одобрения")
        return

    # Одобряем заявку (создается пользователь)
    success = await db.approve_registration(registration_id)

    if success:
        # Уведомляем пользователя об одобрении
        try:
            bot = callback.bot
            await bot.send_message(
                registration.telegram_id,
                f"✅ <b>Заявка одобрена!</b>\n\n"
                f"🎉 Добро пожаловать в команду, {registration.full_name}!\n\n"
                f"📊 Теперь вы можете отправлять ежедневные отчёты.\n"
                f"⏰ Напоминания будут приходить каждый день в 22:00.\n\n"
                f"💡 Используйте команду /start для начала работы."
            )
        except Exception as e:
            logger.warning(f"Failed to notify user {registration.telegram_id} about approval: {e}")

        await callback.message.edit_text(
            f"✅ <b>Заявка одобрена</b>\n\n"
            f"👤 <b>Пользователь:</b> {registration.full_name}\n"
            f"📝 Создан аккаунт и отправлено уведомление пользователю.",
            reply_markup=get_registration_actions_keyboard(registration_id, 'approved')
        )
        await callback.answer("✅ Заявка одобрена")
    else:
        await callback.answer("❌ Ошибка при одобрении заявки", show_alert=True)

@router.callback_query(F.data.startswith("reject_reg_"))
async def reject_registration(callback: CallbackQuery, db: DatabaseService):
    """Отклонить заявку на регистрацию"""

    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    try:
        registration_id = int(callback.data.split("_")[-1])
    except ValueError:
        await callback.answer("❌ Ошибка получения данных заявки")
        return

    # Получаем данные заявки
    registrations = await db.get_pending_registrations()
    registration = next((r for r in registrations if r.id == registration_id), None)

    if not registration or registration.status != 'pending':
        await callback.answer("❌ Заявка недоступна для отклонения")
        return

    # Отклоняем заявку
    success = await db.reject_registration(registration_id)

    if success:
        # Уведомляем пользователя об отклонении
        try:
            bot = callback.bot
            await bot.send_message(
                registration.telegram_id,
                f"❌ <b>Заявка отклонена</b>\n\n"
                f"К сожалению, ваша заявка на регистрацию была отклонена администратором.\n\n"
                f"Для решения данного вопроса обратитесь к руководству."
            )
        except Exception as e:
            logger.warning(f"Failed to notify user {registration.telegram_id} about rejection: {e}")

        await callback.message.edit_text(
            f"❌ <b>Заявка отклонена</b>\n\n"
            f"👤 <b>Пользователь:</b> {registration.full_name}\n"
            f"📝 Отправлено уведомление об отклонении.",
            reply_markup=get_registration_actions_keyboard(registration_id, 'rejected')
        )
        await callback.answer("❌ Заявка отклонена")
    else:
        await callback.answer("❌ Ошибка при отклонении заявки", show_alert=True)

@router.callback_query(F.data.startswith("block_reg_"))
async def block_registration_user(callback: CallbackQuery, db: DatabaseService):
    """Заблокировать пользователя из заявки"""

    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    try:
        registration_id = int(callback.data.split("_")[-1])
    except ValueError:
        await callback.answer("❌ Ошибка получения данных заявки")
        return

    # Получаем данные заявки
    registrations = await db.get_pending_registrations()
    registration = next((r for r in registrations if r.id == registration_id), None)

    if not registration:
        await callback.answer("❌ Заявка не найдена")
        return

    # Получаем admin user_id
    admin_user = await db.get_user(callback.from_user.id)
    if not admin_user:
        await callback.answer("❌ Ошибка определения администратора")
        return

    # Блокируем пользователя
    blocked = await db.block_user(
        telegram_id=registration.telegram_id,
        reason="Заблокировано через заявку на регистрацию",
        blocked_by=admin_user.id,
        full_name=registration.full_name,
        username=registration.username
    )

    # Отклоняем заявку
    rejected = await db.reject_registration(registration_id)

    if blocked and rejected:
        # Уведомляем пользователя о блокировке
        try:
            bot = callback.bot
            await bot.send_message(
                registration.telegram_id,
                f"🚫 <b>Доступ заблокирован</b>\n\n"
                f"Ваш аккаунт был заблокирован администратором.\n"
                f"Для решения данного вопроса обратитесь к руководству."
            )
        except Exception as e:
            logger.warning(f"Failed to notify blocked user {registration.telegram_id}: {e}")

        await callback.message.edit_text(
            f"🚫 <b>Пользователь заблокирован</b>\n\n"
            f"👤 <b>Пользователь:</b> {registration.full_name}\n"
            f"📝 Заявка отклонена, пользователь добавлен в черный список.\n"
            f"📞 Отправлено уведомление о блокировке.",
            reply_markup=get_registration_actions_keyboard(registration_id, 'rejected')
        )
        await callback.answer("🚫 Пользователь заблокирован")
    else:
        await callback.answer("❌ Ошибка при блокировке пользователя", show_alert=True)

@router.callback_query(F.data.startswith("confirm_approve_reg_"))
async def approve_registration_confirm(callback: CallbackQuery, db: DatabaseService):
    """Обработчик старых кнопок подтверждения одобрения"""

    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    try:
        # Извлекаем ID заявки из callback_data
        registration_id = int(callback.data.split("_")[-1])

        # Перенаправляем на основной обработчик одобрения
        new_callback_data = f"approve_reg_{registration_id}"

        # Создаем новый CallbackQuery объект с правильными данными
        callback.data = new_callback_data
        await approve_registration(callback, db)

    except ValueError:
        await callback.answer("❌ Ошибка получения данных заявки")