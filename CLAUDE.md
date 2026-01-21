# Telegram Report Bot - Development Rules

## 📚 START HERE: DEVELOPMENT_PLAN.md
**IMPORTANT:** All project architecture, technology stack, and development phases are in `/DEVELOPMENT_PLAN.md`

**When you need to:**
- Understand project structure and file locations
- Find technology stack decisions (Python, aiogram, SQLite)
- Check development phases and current progress
- Review database schema or API integrations
- Understand user flows and features

**→ FIRST OPEN `/DEVELOPMENT_PLAN.md` and find the needed section**

This saves time and ensures you understand the project context correctly.

---

## 📖 Project Quick Reference

**Project Type:** Telegram Bot + Mini App for daily reporting automation

**Key Files:**
- **[DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md)** - Complete project documentation, architecture, phases
- **[README.md](README.md)** - Quick start, installation, usage (to be created)
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes (to be created)
- **[CURRENT_TASK.md](CURRENT_TASK.md)** - Current work in progress state (when needed)

**Technology Stack:**
- **Backend:** Python 3.11+, aiogram 3.x, SQLite, APScheduler
- **Frontend:** HTML5, CSS3, Vanilla JavaScript, Telegram Web App API
- **Integration:** Google Sheets API (gspread)
- **Hosting:** GitHub + Render.com (free tier)

---

## 💎 CRITICAL PATTERNS

### 1. AIOGRAM 3.X ASYNC PATTERNS

**✅ CORRECT - async/await everywhere:**
```python
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Добро пожаловать!")
```

**❌ WRONG:**
```python
@dp.message_handler(commands=['start'])  # aiogram 2.x syntax!
def cmd_start(message: types.Message):  # Not async!
    bot.send_message(message.chat.id, "Привет")  # Blocking call!
```

---

### 2. DATABASE ASYNC OPERATIONS

**✅ CORRECT - aiosqlite for async:**
```python
import aiosqlite

async def create_user(telegram_id: int, full_name: str):
    async with aiosqlite.connect(Config.DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO users (telegram_id, full_name) VALUES (?, ?)",
            (telegram_id, full_name)
        )
        await db.commit()
```

**❌ WRONG:**
```python
import sqlite3
conn = sqlite3.connect('database.db')  # Blocking I/O!
cursor.execute(...)  # Blocks async loop!
```

---

### 3. ENVIRONMENT VARIABLES

**✅ CORRECT - python-dotenv with defaults:**
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_ID = int(os.getenv('ADMIN_TELEGRAM_ID', 0))
    TIMEZONE = os.getenv('TIMEZONE', 'Europe/Moscow')
```

**❌ WRONG:**
```python
BOT_TOKEN = "123456:ABC-DEF..."  # Hardcoded! Security risk!
ADMIN_ID = os.getenv('ADMIN_ID')  # No default → TypeError if missing
```

---

### 4. GOOGLE SHEETS API AUTHENTICATION

**✅ CORRECT - Service Account with error handling:**
```python
import gspread
from oauth2client.service_account import ServiceAccountCredentials

async def init_sheets():
    try:
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            Config.GOOGLE_CREDENTIALS_PATH, scope)
        client = gspread.authorize(creds)
        return client.open_by_key(Config.GOOGLE_SPREADSHEET_ID)
    except Exception as e:
        logger.error(f"Google Sheets init failed: {e}")
        raise
```

**❌ WRONG:**
```python
client = gspread.authorize(creds)  # No error handling!
sheet = client.open("Sheet name")  # Uses name, not ID (unreliable)
```

---

### 5. TELEGRAM MINI APP DATA RECEIVING

**✅ CORRECT - validate web_app_data:**
```python
from aiogram.types import Message

@router.message(F.web_app_data)
async def handle_web_app_data(message: Message):
    data = message.web_app_data.data  # JSON string
    report_data = json.loads(data)
    
    # Validate data
    if not all(k in report_data for k in ['calls_count', 'kp_plus', ...]):
        await message.answer("❌ Неверный формат данных")
        return
    
    # Process report
    await save_report(message.from_user.id, report_data)
    await message.answer("✅ Отчёт принят!")
```

**❌ WRONG:**
```python
data = json.loads(message.text)  # Wrong! web_app_data is separate field
await save_report(data)  # No validation!
```

---

### 6. TELEGRAM KEYBOARDS

**✅ CORRECT - use builders:**
```python
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(
        text="📊 Отправить отчёт",
        web_app=WebAppInfo(url=Config.WEBAPP_URL)
    )
    builder.button(text="📈 Мой статус")
    builder.button(text="ℹ️ Помощь")
    builder.adjust(1)  # 1 button per row
    return builder.as_markup(resize_keyboard=True)
```

**❌ WRONG:**
```python
keyboard = [[KeyboardButton("Отчёт", web_app=url)]]  # Manual array building
markup = ReplyKeyboardMarkup(keyboard)  # Verbose and error-prone
```

---

### 7. APSCHEDULER ASYNC INTEGRATION

**✅ CORRECT - AsyncIOScheduler with aiogram:**
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler(timezone=Config.TIMEZONE)

async def send_reminders():
    users = await get_users_without_report_today()
    for user in users:
        await bot.send_message(
            user.telegram_id,
            "⏰ Не забудьте отправить отчёт!"
        )

# Schedule daily at 18:00
scheduler.add_job(
    send_reminders,
    trigger=CronTrigger(hour=18, minute=0),
    id='daily_reminders'
)
```

**❌ WRONG:**
```python
from apscheduler.schedulers.blocking import BlockingScheduler
scheduler = BlockingScheduler()  # Blocks async loop!

def send_reminders():  # Not async!
    bot.send_message(...)  # Blocking call!
```

---

### 8. ERROR HANDLING & LOGGING

**✅ CORRECT - structured logging with context:**
```python
import logging

logger = logging.getLogger(__name__)

async def save_report(user_id: int, data: dict):
    try:
        # Validate data
        validated = validate_report_data(data)
        
        # Save to database
        report = await db.create_report(user_id, validated)
        
        # Send to Google Sheets
        await sheets.append_report(report)
        
        logger.info(f"Report saved: user={user_id}, date={report.date}")
        return report
        
    except ValidationError as e:
        logger.warning(f"Invalid report data: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to save report: {e}", exc_info=True)
        raise
```

**❌ WRONG:**
```python
try:
    save_report(data)
    print("Success")  # Don't use print for logging!
except:  # Too broad!
    pass  # Silently fails!
```

---

### 9. RENDER.COM DEPLOYMENT

**✅ CORRECT - proper startup script:**
```python
# bot/main.py
async def main():
    # Initialize database
    await init_database()
    
    # Start scheduler
    scheduler.start()
    
    # Start polling
    logger.info("Bot starting...")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
```

**Render.com Start Command:**
```bash
python bot/main.py
```

**❌ WRONG:**
```python
# No cleanup, no initialization order
dp.start_polling(bot)
```

---

### 10. TELEGRAM WEB APP SECURITY

**✅ CORRECT - validate initData:**
```python
import hmac
import hashlib
from urllib.parse import parse_qs

def validate_telegram_web_app_data(init_data: str, bot_token: str) -> bool:
    """Validate data received from Telegram Mini App"""
    try:
        parsed = parse_qs(init_data)
        hash_value = parsed.get('hash', [''])[0]
        
        # Remove hash from data
        data_check_string = '\n'.join(
            f"{k}={v[0]}" for k, v in sorted(parsed.items()) if k != 'hash'
        )
        
        # Calculate hash
        secret_key = hmac.new(
            "WebAppData".encode(),
            bot_token.encode(),
            hashlib.sha256
        ).digest()
        
        expected_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_hash, hash_value)
    except Exception:
        return False
```

**❌ WRONG:**
```python
# Trust all data from Mini App without validation
data = request.json  # Anyone can send this!
```

---

### 11. DATABASE SCHEMA VERIFICATION

**✅ CORRECT - verify columns before using:**
```python
import aiosqlite

async def check_schema():
    async with aiosqlite.connect(Config.DATABASE_PATH) as db:
        async with db.execute("PRAGMA table_info(users)") as cursor:
            columns = [row[1] async for row in cursor]
            print(f"Users table columns: {columns}")
            # ['id', 'telegram_id', 'full_name', 'username', ...]
```

**❌ WRONG:**
```python
# Assume column exists without verification
await db.execute("SELECT non_existent_column FROM users")  # Error!
```

---

### 12. GOOGLE SHEETS ROW FORMATTING

**✅ CORRECT - format dates and times consistently:**
```python
from datetime import datetime
import pytz

async def append_report(report_data: dict):
    tz = pytz.timezone(Config.TIMEZONE)
    now = datetime.now(tz)
    
    row = [
        now.strftime("%d.%m.%Y"),  # Дата: 18.01.2026
        report_data['full_name'],   # Сотрудник
        report_data['calls_count'], # Кол-во звонков
        report_data['kp_plus'],     # КП+
        report_data['kp'],          # КП
        report_data['rejections'],  # Отказы
        report_data['inadequate'],  # Неадекв
        now.strftime("%H:%M")       # Время: 18:45
    ]
    
    worksheet.append_row(row)
```

**❌ WRONG:**
```python
row = [str(datetime.now()), ...]  # Wrong format: 2026-01-18 18:45:32.123
worksheet.append_row(report_data)  # Wrong order!
```

---

### 13. USER STATE MANAGEMENT

**✅ CORRECT - FSM for multi-step dialogs:**
```python
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

class Registration(StatesGroup):
    waiting_for_name = State()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.set_state(Registration.waiting_for_name)
    await message.answer("Введите ваше ФИО:")

@router.message(Registration.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    full_name = message.text.strip()
    await save_user(message.from_user.id, full_name)
    await state.clear()
    await message.answer("✅ Регистрация завершена!")
```

**❌ WRONG:**
```python
# Using global variables for state
user_states = {}  # Not safe with async!

def cmd_start(message):
    user_states[message.from_user.id] = 'waiting_name'  # Race conditions!
```

---

### 14. MINI APP JAVASCRIPT

**✅ CORRECT - use Telegram Web App API properly:**
```javascript
// webapp/js/app.js

// Initialize Telegram Web App
const tg = window.Telegram.WebApp;
tg.expand();  // Expand to full height

// Get user data safely
const user = tg.initDataUnsafe?.user;
const fullName = user ? `${user.first_name} ${user.last_name}` : 'Unknown';

// Validate form data
function validateForm(formData) {
    const required = ['calls_count', 'kp_plus', 'kp', 'rejections', 'inadequate'];
    for (const field of required) {
        const value = formData[field];
        if (!value || isNaN(value) || value < 0) {
            return false;
        }
    }
    return true;
}

// Send data back to bot
function submitReport(formData) {
    if (!validateForm(formData)) {
        alert('Пожалуйста, заполните все поля корректно');
        return;
    }
    
    tg.sendData(JSON.stringify(formData));
    tg.close();
}
```

**❌ WRONG:**
```javascript
// Direct access without safety checks
const user = Telegram.WebApp.initDataUnsafe.user;  // May be undefined!

// No validation
function submitReport(data) {
    Telegram.WebApp.sendData(data);  // Send unvalidated data!
}
```

---

### 15. ADMIN MIDDLEWARE

**✅ CORRECT - check admin before handler:**
```python
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

class AdminMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        user_id = event.from_user.id if hasattr(event, 'from_user') else None
        
        if user_id and user_id == Config.ADMIN_TELEGRAM_ID:
            return await handler(event, data)
        
        if hasattr(event, 'answer'):
            await event.answer("⛔ Доступ запрещён")
        return

# Apply to admin router
admin_router = Router()
admin_router.message.middleware(AdminMiddleware())
```

**❌ WRONG:**
```python
@router.message(Command("admin"))
async def admin_panel(message: Message):
    # No check! Anyone can access
    await show_admin_panel(message)
```

---

## 🔄 AUTO-COMMIT ON APPROVAL

**Rule:** When user approves changes with positive responses ("Хорошо", "Отлично", "Ок", "Давай", "👍", etc.), immediately commit the changes without asking.

**Commit message format:**
- Brief description in English for code changes
- In Russian if changes relate to Russian UI/UX messages

**Example flow:**
1. User: "Добавь валидацию в форму"
2. Claude: *makes change* "Добавил валидацию полей формы"
3. User: "Отлично"
4. Claude: *immediately commits* "Закоммитил: Add form validation"

---

## 📁 PROJECT STRUCTURE

**Project Root:** `telegram-report-bot/`

**Key Directories:**
- `bot/` - Main bot code (handlers, config, keyboards)
- `services/` - Business logic (database, Google Sheets, scheduler)
- `webapp/` - Mini App frontend (HTML, CSS, JS)
- `database/` - SQLite database and models
- `utils/` - Helper functions (validators, logger)
- `credentials/` - Google API credentials (NOT in Git!)

**Configuration Files:**
- `.env` - Environment variables (NOT in Git!)
- `.env.example` - Template for environment variables
- `requirements.txt` - Python dependencies
- `runtime.txt` - Python version for Render.com
- `.gitignore` - Git exclusions

---

## 📝 CURRENT_TASK.md - ФОРМАТ ДОКУМЕНТАЦИИ НЕЗАВЕРШЕННОЙ РАБОТЫ

**НАЗНАЧЕНИЕ:** Сохранение состояния процесса работы для быстрого восстановления контекста при обрыве сессии.

**ПРИНЦИПЫ:**
- Только ПРОЦЕСС, не результаты
- Максимально сжато, без воды
- Все файлы с номерами строк
- Один конкретный следующий шаг

**ОБЯЗАТЕЛЬНАЯ СТРУКТУРА:**

```markdown
# ЧТО ПРОИСХОДИТ
[Одно предложение - суть проблемы/задачи]

# ГДЕ Я ОСТАНОВИЛСЯ
[Точно где сейчас нахожусь в процессе]

# ЧТО СДЕЛАНО
[Список изменений с файлами и строками]

# ЧТО НЕ РАБОТАЕТ
[Конкретная ошибка/проблема прямо сейчас]

# СЛЕДУЮЩИЙ ШАГ
[Одно конкретное действие]

# ТЕХНИЧЕСКАЯ КАРТА
- Файлы: [пути:строки]
- Команды: [для проверки состояния]
- Логи: [где смотреть ошибки]
```

**ПРАВИЛА ЗАПИСИ:**

1. **Без Результатов**: НИКАКИХ "Успешно", "Реализовано", "Работает", "Проблема решена"
2. **Файлы с Номерами**: `bot/main.py:23-45` (всегда точные строки)
3. **Состояние Системы**: работает/сломано/неизвестно (без эмоций)
4. **Один Шаг**: следующий шаг = одно конкретное действие
5. **Способ Проверки**: команда/лог для подтверждения состояния

**КРИТИЧЕСКОЕ ПРАВИЛО:** ЗАПРЕЩЕНО писать "решена", "исправлена", "работает". "Готово к тестированию" - РАЗРЕШЕНО (код изменен, но результат неизвестен). CURRENT_TASK.md содержит только НЕЗАВЕРШЕННЫЕ процессы.

**СТАТУСЫ ЗАВЕРШЕНИЯ:**
- "Закоммичено" - можно удалить запись и писать новую задачу
- "Требует тестирования" - ждем проверки пользователем

**КОГДА СОЗДАВАТЬ:**
- При значительном прогрессе без финального результата
- Перед сложными изменениями
- По запросу пользователя "запиши текущее состояние"

**ПРИМЕР КАЧЕСТВЕННОЙ ЗАПИСИ:**
```markdown
# ЧТО ПРОИСХОДИТ
Google Sheets API возвращает 403 при попытке записать отчёт

# ГДЕ Я ОСТАНОВИЛСЯ
Проверяю права доступа service account к таблице

# ЧТО СДЕЛАНО
- Создан service account: credentials/google_credentials.json
- Реализована интеграция: services/google_sheets.py:15-67
- Добавлена обработка ошибок: services/google_sheets.py:45-52

# ЧТО НЕ РАБОТАЕТ
worksheet.append_row() падает с 403 Forbidden

# СЛЕДУЮЩИЙ ШАГ
Проверить email service account и права доступа в Google Sheets

# ТЕХНИЧЕСКАЯ КАРТА
- Файлы: services/google_sheets.py:45-52 (error handling)
- Команды: python -c "from services.google_sheets import test_connection; test_connection()"
- Логи: bot/main.py console output
```

---

## 🧪 TESTING GUIDELINES

### Manual Testing Checklist

**Before Committing:**
- [ ] Bot responds to `/start`
- [ ] Main menu keyboard displayed
- [ ] Mini App opens from button
- [ ] Form validates data correctly
- [ ] Report saved to database
- [ ] Report appears in Google Sheets
- [ ] Admin panel accessible (for admin only)
- [ ] Reminders sent at configured time

**Test Commands:**
```bash
# Run bot locally
python bot/main.py

# Check database
sqlite3 database/database.db "SELECT * FROM users;"

# Test Google Sheets connection
python -c "from services.google_sheets import GoogleSheetsService; import asyncio; asyncio.run(GoogleSheetsService().test_connection())"
```

---

## 🚀 DEPLOYMENT CHECKLIST

**Before Deploying to Render.com:**

1. **Environment Variables Set:**
   - [ ] BOT_TOKEN
   - [ ] ADMIN_TELEGRAM_ID
   - [ ] GOOGLE_SPREADSHEET_ID
   - [ ] GOOGLE_CREDENTIALS_JSON (content, not path!)
   - [ ] TIMEZONE
   - [ ] REMINDER_TIME

2. **Files Ready:**
   - [ ] requirements.txt up to date
   - [ ] runtime.txt has Python version
   - [ ] .env not in Git (.gitignore verified)
   - [ ] credentials/ not in Git

3. **Code Ready:**
   - [ ] All imports correct
   - [ ] No hardcoded tokens/secrets
   - [ ] Proper error handling everywhere
   - [ ] Logging configured

4. **GitHub:**
   - [ ] All changes committed
   - [ ] Pushed to main branch
   - [ ] No sensitive data in history

---

## 🎯 DEVELOPMENT PHASES TRACKING

**Current Phase:** [Update as you progress]

- [ ] **Phase 1: Infrastructure** (Week 1)
  - [ ] Project structure created
  - [ ] Telegram bot created
  - [ ] Google Sheets API configured
  - [ ] Database initialized

- [ ] **Phase 2: Core Features** (Week 2)
  - [ ] User registration implemented
  - [ ] Mini App form created
  - [ ] Report submission working
  - [ ] Google Sheets integration tested

- [ ] **Phase 3: Advanced Features** (Week 3)
  - [ ] Reminder system implemented
  - [ ] Admin panel created
  - [ ] User status feature added
  - [ ] Error handling complete

- [ ] **Phase 4: Deployment** (Week 4)
  - [ ] Local testing passed
  - [ ] Deployed to Render.com
  - [ ] Production testing passed
  - [ ] Users trained

---

## 📚 QUICK REFERENCE COMMANDS

**Development:**
```bash
# Start virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run bot
python bot/main.py

# Check database
sqlite3 database/database.db
```

**Git:**
```bash
# Check status
git status

# Commit changes
git add .
git commit -m "Description"

# Push to GitHub
git push origin main
```

**Debugging:**
```bash
# Check bot token
echo $BOT_TOKEN

# Test database connection
python -c "import sqlite3; print(sqlite3.connect('database/database.db').execute('SELECT * FROM users').fetchall())"

# View logs
tail -f logs/bot.log
```

---

## 🔐 SECURITY NOTES

**Never Commit:**
- ❌ `.env` file
- ❌ `credentials/google_credentials.json`
- ❌ `database/database.db` (contains user data)
- ❌ API tokens or secrets in code

**Always:**
- ✅ Use `.env.example` for templates
- ✅ Use environment variables
- ✅ Add sensitive files to `.gitignore`
- ✅ Validate all user inputs
- ✅ Verify Telegram Mini App data

---

## 📖 DOCUMENTATION PRIORITIES

**Always Update When Changing:**
1. **DEVELOPMENT_PLAN.md** - If architecture/phases change
2. **CURRENT_TASK.md** - During active development (if interrupted)
3. **CHANGELOG.md** - After completing features (to be created)
4. **README.md** - When setup instructions change (to be created)

**Format for Updates:**
- Be concise and specific
- Include file paths and line numbers
- Use examples when explaining patterns
- Keep checklists up to date

---

**Document Version:** 1.0  
**Created:** 18.01.2026  
**Last Updated:** 18.01.2026  
**Project:** Telegram Report Bot  
**Owner:** [Your Name]

---

## 🎯 REMEMBER

1. **Always check DEVELOPMENT_PLAN.md first** for project context
2. **Use async/await everywhere** (aiogram 3.x requirement)
3. **Validate all inputs** (security first)
4. **Log everything important** (debugging future issues)
5. **Test before committing** (broken code wastes time)
6. **Auto-commit on user approval** (keep momentum)
7. **Write CURRENT_TASK.md** when interrupted (save context)

---

**Ready to start development!** 🚀
