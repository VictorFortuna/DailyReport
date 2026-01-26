"""
Клавиатуры и кнопки для Telegram бота
"""

from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
    WebAppInfo
)
from bot.config import Config

def get_main_menu_keyboard(user_full_name: str = None) -> ReplyKeyboardMarkup:
    """Главное меню для сотрудников"""

    # Создаем кнопку для отчёта с прямым WebApp
    report_button = KeyboardButton(text="📊 Отправить отчёт")
    if user_full_name:
        from urllib.parse import quote
        webapp_url = f"{Config.WEBAPP_URL}?user_name={quote(user_full_name)}"
        report_button = KeyboardButton(
            text="📊 Отправить отчёт",
            web_app=WebAppInfo(url=webapp_url)
        )

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📈 Мой статус"),
                KeyboardButton(text="ℹ️ Помощь")
            ],
            [report_button]
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите действие..."
    )
    return keyboard

def get_report_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для отправки отчёта через Mini App"""
    webapp = WebAppInfo(url=Config.WEBAPP_URL)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Открыть форму отчёта", web_app=webapp)],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_report")]
    ])
    return keyboard

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Административная клавиатура"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статус отчётов сегодня", callback_data="admin_today_status")],
        [InlineKeyboardButton(text="👥 Список сотрудников", callback_data="admin_users_list")],
        [
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings"),
            InlineKeyboardButton(text="📈 Статистика", callback_data="admin_stats")
        ],
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_refresh")]
    ])
    return keyboard

def get_admin_users_keyboard(users: list) -> InlineKeyboardMarkup:
    """Клавиатура со списком пользователей для админа"""
    keyboard = []

    for user in users:
        status_emoji = "✅" if user.is_active else "❌"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{status_emoji} {user.full_name}",
                callback_data=f"admin_user_{user.id}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_user_status_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для просмотра статуса пользователя"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Отправить отчёт", callback_data="open_report_form")]
    ])
    return keyboard

def get_confirmation_keyboard(action: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action}"),
            InlineKeyboardButton(text="❌ Нет", callback_data=f"cancel_{action}")
        ]
    ])
    return keyboard

def get_back_keyboard() -> InlineKeyboardMarkup:
    """Простая клавиатура с кнопкой "Назад" """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ])
    return keyboard

def get_help_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для справки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Как отправить отчёт?", callback_data="help_report")],
        [InlineKeyboardButton(text="📈 Как посмотреть статус?", callback_data="help_status")],
        [InlineKeyboardButton(text="❓ Частые вопросы", callback_data="help_faq")],
        [InlineKeyboardButton(text="📞 Связаться с поддержкой", callback_data="help_support")]
    ])
    return keyboard

def get_registration_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для начала регистрации"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Начать регистрацию")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

def get_admin_user_actions_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Действия с конкретным пользователем для админа"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Информация", callback_data=f"admin_user_info_{user_id}")],
        [InlineKeyboardButton(text="📊 Отчёты пользователя", callback_data=f"admin_user_reports_{user_id}")],
        [
            InlineKeyboardButton(text="✅ Активировать", callback_data=f"admin_activate_{user_id}"),
            InlineKeyboardButton(text="❌ Деактивировать", callback_data=f"admin_deactivate_{user_id}")
        ],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_delete_{user_id}")],
        [InlineKeyboardButton(text="🔙 Назад к списку", callback_data="admin_users_list")]
    ])
    return keyboard