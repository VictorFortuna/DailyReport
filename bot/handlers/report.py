"""
Обработчики отправки отчётов через Mini App
"""

import json
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, WebAppInfo

from bot.keyboards import (
    get_main_menu_keyboard,
    get_report_keyboard,
    get_user_status_keyboard,
    get_back_keyboard
)
from services.database import DatabaseService
from bot.config import Config
from utils.logger import get_logger

logger = get_logger(__name__)
router = Router()

@router.message(F.text == "📊 Отправить отчёт")
async def request_report(message: Message, db: DatabaseService):
    """Обработчик кнопки отправки отчёта"""

    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала необходимо зарегистрироваться. Используйте /start")
        return

    # Проверим, отправлен ли уже отчёт за сегодня
    today = datetime.now().strftime('%Y-%m-%d')
    existing_report = await db.get_report(user.id, today)

    if existing_report:
        await message.answer(
            f"✅ <b>Отчёт за сегодня уже отправлен!</b>\n\n"
            f"📊 <b>Ваши данные:</b>\n"
            f"📞 Звонков: {existing_report.calls_count}\n"
            f"✅ КП+: {existing_report.kp_plus}\n"
            f"🔄 КП: {existing_report.kp}\n"
            f"❌ Отказы: {existing_report.rejections}\n"
            f"⚠️ Неадекв: {existing_report.inadequate}\n\n"
            f"🕐 <b>Время отправки:</b> {existing_report.submitted_at.strftime('%H:%M')}\n\n"
            f"💡 <b>Хотите обновить данные?</b>\n"
            f"Просто отправьте отчёт заново - данные обновятся.",
            reply_markup=get_report_keyboard()
        )
    else:
        await message.answer(
            f"📊 <b>Отправка отчёта за {datetime.now().strftime('%d.%m.%Y')}</b>\n\n"
            f"👤 <b>Сотрудник:</b> {user.full_name}\n\n"
            f"📱 Нажмите кнопку ниже для открытия формы отчёта:",
            reply_markup=get_report_keyboard()
        )

@router.callback_query(F.data == "open_report_form")
async def open_report_form_callback(callback: CallbackQuery, db: DatabaseService):
    """Callback для открытия формы отчёта"""

    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.answer("❌ Необходима регистрация", show_alert=True)
        return

    await callback.message.edit_text(
        f"📊 <b>Форма отчёта</b>\n\n"
        f"👤 <b>Сотрудник:</b> {user.full_name}\n"
        f"📅 <b>Дата:</b> {datetime.now().strftime('%d.%m.%Y')}\n\n"
        f"📱 Нажмите кнопку для открытия формы:",
        reply_markup=get_report_keyboard()
    )
    await callback.answer()

@router.message(F.content_type == "web_app_data")
async def process_web_app_data(message: Message, db: DatabaseService):
    """Обработка данных от Mini App"""

    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Пользователь не найден. Используйте /start для регистрации.")
        return

    try:
        # Парсинг данных от Mini App
        data = json.loads(message.web_app_data.data)
        logger.info(f"Received web app data from {user.full_name}: {data}")

        # Валидация данных
        required_fields = ['calls_count', 'kp_plus', 'kp', 'rejections', 'inadequate']
        for field in required_fields:
            if field not in data:
                await message.answer(f"❌ Отсутствует поле: {field}")
                return

        # Проверка типов и значений
        try:
            calls_count = int(data['calls_count'])
            kp_plus = int(data['kp_plus'])
            kp = int(data['kp'])
            rejections = int(data['rejections'])
            inadequate = int(data['inadequate'])
        except (ValueError, TypeError):
            await message.answer("❌ Некорректные данные. Все поля должны содержать числа.")
            return

        # Валидация логики
        if calls_count < 0 or kp_plus < 0 or kp < 0 or rejections < 0 or inadequate < 0:
            await message.answer("❌ Все значения должны быть положительными числами.")
            return

        if calls_count == 0:
            await message.answer("❌ Количество звонков не может быть равно 0.")
            return

        if (kp_plus + kp) > calls_count:
            await message.answer("❌ Количество результативных звонков не может превышать общее количество.")
            return

        # Сохранение отчёта
        today = datetime.now().strftime('%Y-%m-%d')
        report = await db.create_report(
            user_id=user.id,
            report_date=today,
            calls_count=calls_count,
            kp_plus=kp_plus,
            kp=kp,
            rejections=rejections,
            inadequate=inadequate
        )

        if report:
            # Подсчёт статистики
            total_resultative = kp_plus + kp
            conversion = round((total_resultative / calls_count) * 100, 1) if calls_count > 0 else 0

            # Отправка подтверждения
            await message.answer(
                f"✅ <b>Отчёт успешно отправлен!</b>\n\n"
                f"📊 <b>Ваши результаты за {datetime.now().strftime('%d.%m.%Y')}:</b>\n\n"
                f"📞 <b>Звонков:</b> {calls_count}\n"
                f"✅ <b>КП+:</b> {kp_plus}\n"
                f"🔄 <b>КП:</b> {kp}\n"
                f"❌ <b>Отказы:</b> {rejections}\n"
                f"⚠️ <b>Неадекв:</b> {inadequate}\n\n"
                f"📈 <b>Статистика:</b>\n"
                f"🎯 <b>Результативных:</b> {total_resultative}\n"
                f"📊 <b>Конверсия:</b> {conversion}%\n\n"
                f"🕐 <b>Время отправки:</b> {report.submitted_at.strftime('%H:%M')}\n\n"
                f"🙏 Спасибо за работу!",
                reply_markup=get_main_menu_keyboard()
            )

            logger.info(f"Report saved for {user.full_name}: {calls_count} calls, {total_resultative} resultative")

            # Уведомление админа о новом отчёте
            try:
                await message.bot.send_message(
                    Config.ADMIN_TELEGRAM_ID,
                    f"📊 <b>Новый отчёт получен</b>\n\n"
                    f"👤 <b>Сотрудник:</b> {user.full_name}\n"
                    f"📅 <b>Дата:</b> {datetime.now().strftime('%d.%m.%Y')}\n"
                    f"🕐 <b>Время:</b> {report.submitted_at.strftime('%H:%M')}\n\n"
                    f"📞 <b>Звонков:</b> {calls_count}\n"
                    f"🎯 <b>Результативных:</b> {total_resultative} ({conversion}%)\n"
                    f"✅ <b>КП+:</b> {kp_plus} | 🔄 <b>КП:</b> {kp}\n"
                    f"❌ <b>Отказы:</b> {rejections} | ⚠️ <b>Неадекв:</b> {inadequate}"
                )
            except Exception as e:
                logger.warning(f"Failed to notify admin about new report: {e}")

        else:
            await message.answer(
                "❌ <b>Ошибка сохранения отчёта</b>\n\n"
                "Произошла ошибка при сохранении данных. "
                "Попробуйте ещё раз или обратитесь к администратору.",
                reply_markup=get_main_menu_keyboard()
            )
            logger.error(f"Failed to save report for {user.full_name}")

    except json.JSONDecodeError:
        await message.answer(
            "❌ <b>Ошибка обработки данных</b>\n\n"
            "Некорректный формат данных. Попробуйте отправить отчёт ещё раз.",
            reply_markup=get_main_menu_keyboard()
        )
        logger.error(f"Invalid JSON data from {user.full_name}: {message.web_app_data.data}")

    except Exception as e:
        await message.answer(
            "❌ <b>Техническая ошибка</b>\n\n"
            "Произошла ошибка при обработке отчёта. "
            "Попробуйте ещё раз через несколько минут.",
            reply_markup=get_main_menu_keyboard()
        )
        logger.error(f"Error processing web app data from {user.full_name}: {e}")

@router.message(F.text == "📈 Мой статус")
async def user_status(message: Message, db: DatabaseService):
    """Показать статус пользователя"""

    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала необходимо зарегистрироваться. Используйте /start")
        return

    # Проверяем отчёт за сегодня
    today = datetime.now().strftime('%Y-%m-%d')
    today_report = await db.get_report(user.id, today)

    # Получаем последние отчёты
    recent_reports = await db.get_user_reports(user.id, limit=7)

    # Формируем сообщение
    status_text = f"📈 <b>Статус отчётов</b>\n\n👤 <b>{user.full_name}</b>\n\n"

    # Статус сегодняшнего отчёта
    if today_report:
        total_resultative = today_report.kp_plus + today_report.kp
        conversion = round((total_resultative / today_report.calls_count) * 100, 1) if today_report.calls_count > 0 else 0

        status_text += (
            f"✅ <b>Отчёт за сегодня отправлен</b>\n"
            f"🕐 Время: {today_report.submitted_at.strftime('%H:%M')}\n"
            f"📞 Звонков: {today_report.calls_count}\n"
            f"🎯 Результативных: {total_resultative} ({conversion}%)\n\n"
        )
    else:
        status_text += f"❌ <b>Отчёт за сегодня не отправлен</b>\n\n"

    # Статистика за неделю
    if recent_reports:
        total_calls = sum(r.calls_count for r in recent_reports)
        total_resultative = sum(r.kp_plus + r.kp for r in recent_reports)
        avg_conversion = round((total_resultative / total_calls) * 100, 1) if total_calls > 0 else 0

        status_text += (
            f"📊 <b>Статистика за {len(recent_reports)} дней:</b>\n"
            f"📞 Всего звонков: {total_calls}\n"
            f"🎯 Результативных: {total_resultative}\n"
            f"📈 Средняя конверсия: {avg_conversion}%\n\n"
        )

        # Последние отчёты
        status_text += "📅 <b>Последние отчёты:</b>\n"
        for report in recent_reports[:5]:  # Показываем максимум 5
            report_date = datetime.strptime(report.report_date, '%Y-%m-%d').strftime('%d.%m')
            resultative = report.kp_plus + report.kp
            conversion = round((resultative / report.calls_count) * 100, 1) if report.calls_count > 0 else 0
            status_text += f"• {report_date}: {report.calls_count} звонков, {conversion}% конверсия\n"
    else:
        status_text += "📅 <b>История отчётов пуста</b>\n"

    await message.answer(status_text, reply_markup=get_user_status_keyboard())

@router.callback_query(F.data == "refresh_status")
async def refresh_status(callback: CallbackQuery, db: DatabaseService):
    """Обновить статус пользователя"""
    # Используем тот же код что и в user_status, но для callback
    await user_status(callback.message, db)
    await callback.answer("✅ Статус обновлён")

@router.callback_query(F.data == "cancel_report")
async def cancel_report(callback: CallbackQuery):
    """Отмена отправки отчёта"""
    await callback.message.edit_text(
        "❌ <b>Отправка отчёта отменена</b>\n\n"
        "Вы можете отправить отчёт в любое время, нажав кнопку \"📊 Отправить отчёт\".",
        reply_markup=get_back_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "check_status")
async def check_status_callback(callback: CallbackQuery, db: DatabaseService):
    """Проверка статуса через callback (из напоминаний)"""
    await user_status(callback.message, db)
    await callback.answer()