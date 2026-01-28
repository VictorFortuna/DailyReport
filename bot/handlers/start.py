"""
Обработчики команды /start и регистрации пользователей
"""

from aiogram import Router, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.keyboards import (
    get_main_menu_keyboard,
    get_registration_keyboard,
    get_help_keyboard
)
from services.database import DatabaseService
from utils.logger import get_logger

logger = get_logger(__name__)
router = Router()

class RegistrationStates(StatesGroup):
    waiting_for_name = State()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db: DatabaseService):
    """Обработчик команды /start"""

    user = await db.get_user(message.from_user.id)

    if user:
        # Пользователь уже зарегистрирован
        await message.answer(
            f"👋 С возвращением, <b>{user.full_name}</b>!\n\n"
            f"Вы можете отправить отчёт за сегодня или проверить свой статус.",
            reply_markup=get_main_menu_keyboard(user.full_name)
        )
        logger.info(f"Existing user {user.full_name} ({message.from_user.id}) used /start")
    else:
        # Новый пользователь - начинаем регистрацию
        await message.answer(
            "👋 <b>Добро пожаловать в Daily Report Bot!</b>\n\n"
            "🤖 Я помогу вам быстро отправлять ежедневные отчёты о работе.\n\n"
            "📋 <b>Что я умею:</b>\n"
            "• 📊 Принимать ежедневные отчёты через удобную форму\n"
            "• 📈 Показывать статистику ваших отчётов\n"
            "• ⏰ Напоминать о необходимости отправить отчёт\n"
            "• 📱 Работать прямо в Telegram без установки приложений\n\n"
            "📝 <b>Для начала работы нужна регистрация.</b>\n"
            "Давайте зарегистрируем вас в системе!",
            reply_markup=get_registration_keyboard()
        )
        logger.info(f"New user {message.from_user.id} started registration")

@router.message(F.text == "✅ Начать регистрацию")
async def start_registration(message: Message, state: FSMContext):
    """Начало процесса регистрации"""

    await state.set_state(RegistrationStates.waiting_for_name)
    await message.answer(
        "📝 <b>Регистрация сотрудника</b>\n\n"
        "Пожалуйста, введите ваше <b>полное имя</b> (Фамилия Имя Отчество):\n\n"
        "<i>Например: Иванов Иван Иванович</i>",
        reply_markup=None  # Убираем клавиатуру
    )

@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext, db: DatabaseService):
    """Обработка введённого имени"""

    full_name = message.text.strip()

    # Валидация имени
    if len(full_name) < 3:
        await message.answer(
            "❌ <b>Имя слишком короткое.</b>\n\n"
            "Пожалуйста, введите ваше полное имя (минимум 3 символа):"
        )
        return

    if len(full_name) > 100:
        await message.answer(
            "❌ <b>Имя слишком длинное.</b>\n\n"
            "Пожалуйста, введите имя покороче (до 100 символов):"
        )
        return

    # Проверка на наличие хотя бы двух слов
    name_parts = full_name.split()
    if len(name_parts) < 2:
        await message.answer(
            "❌ <b>Пожалуйста, введите фамилию и имя.</b>\n\n"
            "Например: <i>Иванов Иван</i> или <i>Иванов Иван Иванович</i>"
        )
        return

    # Создание пользователя
    try:
        user = await db.create_user(
            telegram_id=message.from_user.id,
            full_name=full_name,
            username=message.from_user.username
        )

        if user:
            await state.clear()
            await message.answer(
                f"✅ <b>Регистрация завершена!</b>\n\n"
                f"👤 <b>Ваше имя:</b> {user.full_name}\n"
                f"🆔 <b>Ваш ID:</b> <code>{user.telegram_id}</code>\n\n"
                f"🎉 <b>Добро пожаловать в команду!</b>\n\n"
                f"📊 Теперь вы можете отправлять ежедневные отчёты.\n"
                f"⏰ Напоминания будут приходить каждый день в 18:00.\n\n"
                f"💡 <b>Совет:</b> Используйте кнопку <b>\"📊 Отчёт\"</b> "
                f"для быстрого доступа к форме.",
                reply_markup=get_main_menu_keyboard(user.full_name)
            )

            logger.info(f"User registered: {full_name} ({message.from_user.id})")

            # Уведомление админа о новом пользователе
            from bot.config import Config
            try:
                bot = message.bot
                await bot.send_message(
                    Config.ADMIN_TELEGRAM_ID,
                    f"👤 <b>Новый сотрудник зарегистрирован!</b>\n\n"
                    f"📝 <b>Имя:</b> {full_name}\n"
                    f"🆔 <b>Telegram ID:</b> <code>{message.from_user.id}</code>\n"
                    f"📱 <b>Username:</b> @{message.from_user.username or 'отсутствует'}\n"
                    f"📅 <b>Дата:</b> {user.created_at.strftime('%d.%m.%Y %H:%M')}"
                )
            except Exception as e:
                logger.warning(f"Failed to notify admin about new user: {e}")
        else:
            await message.answer(
                "❌ <b>Ошибка регистрации</b>\n\n"
                "Произошла ошибка при создании аккаунта. "
                "Попробуйте ещё раз или обратитесь к администратору."
            )
            logger.error(f"Failed to create user: {full_name} ({message.from_user.id})")

    except Exception as e:
        await message.answer(
            "❌ <b>Ошибка регистрации</b>\n\n"
            "Произошла техническая ошибка. "
            "Попробуйте ещё раз через несколько минут."
        )
        logger.error(f"Registration error for {full_name}: {e}")
        await state.clear()

@router.message(F.text == "⚙️ Открыть админ-панель")
async def admin_panel_handler(message: Message, db: DatabaseService):
    """Обработчик кнопки админ-панели"""

    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала необходимо зарегистрироваться. Используйте /start")
        return

    # Проверяем, является ли пользователь администратором
    from bot.config import Config
    if message.from_user.id == Config.ADMIN_TELEGRAM_ID:
        # Для админа показываем админ-панель
        from bot.handlers.admin import admin_panel
        await admin_panel(message, db)
    else:
        # Для обычных пользователей - отказ в доступе
        await message.answer(
            "❌ <b>Админ-панель недоступна</b>\n\n"
            "У вас нет прав доступа к административным функциям."
        )

@router.message(F.text == "📈 Мой статус")
async def status_handler(message: Message, db: DatabaseService):
    """Обработчик кнопки статуса"""
    # Вызываем функцию статуса из report.py
    from bot.handlers.report import user_status
    await user_status(message, db)

@router.message(F.text == "Меню")
async def menu_handler(message: Message, db: DatabaseService):
    """Обработчик кнопки меню"""

    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала необходимо зарегистрироваться. Используйте /start")
        return

    await message.answer(
        f"👋 <b>{user.full_name}</b>\n\n"
        "Главное меню:",
        reply_markup=get_main_menu_keyboard(user.full_name)
    )

@router.message(F.text == "ℹ️ Помощь")
async def help_button_handler(message: Message, db: DatabaseService):
    """Обработчик кнопки помощи"""
    await help_handler(message, db)

async def help_handler(message: Message, db: DatabaseService):
    """Обработчик кнопки помощи"""

    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала необходимо зарегистрироваться. Используйте /start")
        return

    await message.answer(
        "ℹ️ <b>Справка по использованию бота</b>\n\n"
        "🤖 <b>Основные функции:</b>\n\n"
        "📊 <b>Отправить отчёт</b>\n"
        "• Нажмите кнопку \"📊 Отправить отчёт\"\n"
        "• Заполните форму с данными за день и нажмите кнопку \"Отправить\"\n\n"
        "📈 <b>Мой статус</b>\n"
        "• Показывает отправлен ли отчёт за сегодня\n"
        "• Отображает статистику за последние дни"
    )

@router.message(Command("help"))
async def cmd_help(message: Message, db: DatabaseService):
    """Обработчик команды /help"""
    await help_handler(message, db)

@router.message(Command("status"))
async def cmd_status(message: Message, db: DatabaseService):
    """Обработчик команды /status"""
    # Вызываем функцию статуса напрямую
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала необходимо зарегистрироваться. Используйте /start")
        return

    # Импортируем и вызываем функцию статуса
    from bot.handlers.report import user_status
    await user_status(message, db)

# Обработчики callback для помощи
@router.callback_query(F.data.startswith("help_"))
async def help_callbacks(callback: CallbackQuery):
    """Обработчики callback-ов для справки"""

    action = callback.data.split("_")[1]

    if action == "report":
        text = (
            "📊 <b>Как отправить отчёт</b>\n\n"
            "1️⃣ Нажмите кнопку <b>\"📊 Отправить отчёт\"</b>\n"
            "2️⃣ В открывшейся форме заполните поля:\n"
            "   • Количество звонков\n"
            "   • КП+ (закрытые сделки)\n"
            "   • КП (сделки в работе)\n"
            "   • Отказы\n"
            "   • Неадекватные звонки\n"
            "3️⃣ Нажмите <b>\"Отправить отчёт\"</b>\n\n"
            "✅ Форма автоматически проверит данные и отправит отчёт в Google Таблицу.\n\n"
            "📝 <b>Важно:</b> Один отчёт в день. При повторной отправке данные обновятся."
        )
    elif action == "status":
        text = (
            "📈 <b>Как посмотреть статус</b>\n\n"
            "1️⃣ Нажмите кнопку <b>\"📈 Мой статус\"</b>\n"
            "2️⃣ Вы увидите:\n"
            "   • Отправлен ли отчёт за сегодня\n"
            "   • Время последнего отчёта\n"
            "   • Статистику за неделю\n"
            "   • Общее количество отчётов\n\n"
            "🔄 Статус обновляется в реальном времени.\n"
            "📊 Также доступен быстрый доступ к форме отчёта."
        )
    elif action == "faq":
        text = (
            "❓ <b>Частые вопросы</b>\n\n"
            "<b>Q:</b> Можно ли исправить отправленный отчёт?\n"
            "<b>A:</b> Да, отправьте отчёт повторно - данные обновятся.\n\n"
            "<b>Q:</b> Что делать если форма не открывается?\n"
            "<b>A:</b> Убедитесь, что используете официальное приложение Telegram.\n\n"
            "<b>Q:</b> Когда приходят напоминания?\n"
            "<b>A:</b> Ежедневно в 18:00, если отчёт не отправлен.\n\n"
            "<b>Q:</b> Можно ли посмотреть отчёты коллег?\n"
            "<b>A:</b> Нет, доступны только ваши отчёты. Руководитель видит все отчёты в Google Таблице.\n\n"
            "<b>Q:</b> Бот не отвечает, что делать?\n"
            "<b>A:</b> Обратитесь к администратору или попробуйте /start."
        )
    elif action == "support":
        text = (
            "📞 <b>Техническая поддержка</b>\n\n"
            "При возникновении проблем:\n\n"
            "1️⃣ <b>Попробуйте перезапустить бота:</b>\n"
            "   • Используйте команду /start\n\n"
            "2️⃣ <b>Проверьте подключение:</b>\n"
            "   • Убедитесь что есть интернет\n"
            "   • Обновите приложение Telegram\n\n"
            "3️⃣ <b>Обратитесь к администратору:</b>\n"
            "   • Опишите проблему подробно\n"
            "   • Укажите время возникновения\n\n"
            "🆔 <b>Ваш ID для техподдержки:</b>\n"
            f"<code>{callback.from_user.id}</code>\n\n"
            "⚡ Обычно проблемы решаются в течение нескольких минут."
        )

    await callback.message.edit_text(text, reply_markup=get_help_keyboard())
    await callback.answer()

@router.callback_query(F.data == "open_report_form")
async def open_report_form(callback: CallbackQuery, db: DatabaseService):
    """Открыть форму отчёта с правильным именем пользователя"""

    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.answer("❌ Сначала необходимо зарегистрироваться. Используйте /start")
        return

    # Создаем URL с именем пользователя
    from bot.config import Config
    from urllib.parse import quote

    webapp_url = f"{Config.WEBAPP_URL}?user_name={quote(user.full_name)}"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

    webapp = WebAppInfo(url=webapp_url)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Открыть форму отчёта", web_app=webapp)]
    ])

    await callback.message.edit_text(
        "📊 <b>Отправка отчёта</b>\n\n"
        f"👤 <b>Сотрудник:</b> {user.full_name}\n\n"
        "Нажмите кнопку для открытия формы:",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data == "back")
async def back_to_main(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.delete()
    await callback.answer("Возвращаемся в главное меню")

# Обработчик неизвестных сообщений для незарегистрированных пользователей
@router.message(StateFilter(None))
async def unknown_command(message: Message, db: DatabaseService):
    """Обработка неизвестных команд"""

    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer(
            "❌ <b>Вы не зарегистрированы</b>\n\n"
            "Для начала работы используйте команду /start",
            reply_markup=get_registration_keyboard()
        )
        return

    # Для зарегистрированных пользователей - показываем меню
    await message.answer(
        "Используйте кнопки меню:",
        reply_markup=get_main_menu_keyboard(user.full_name)
    )