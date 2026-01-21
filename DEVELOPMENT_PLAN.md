# 📋 DEVELOPMENT PLAN: Telegram Daily Report Bot

## 🎯 Project Overview

**Project Name:** Telegram Daily Report Bot  
**Type:** Telegram Bot + Mini App для автоматизации ежедневной отчётности  
**Target Users:** 4-5 сотрудников call-центра + 1 руководитель  
**Development Time:** 2-4 недели  
**Budget:** 0₽ (полностью бесплатное решение)

---

## 📊 Business Requirements

### Problem Statement
Сотрудники call-центра должны ежедневно отправлять отчёт о своей работе руководителю. Текущий процесс неавтоматизирован и требует ручного ввода данных.

### Solution
Telegram бот с Mini App формой, которая:
- Позволяет сотрудникам быстро заполнить отчёт через удобный интерфейс
- Автоматически отправляет данные в Google Таблицу руководителя
- Напоминает о необходимости отправить отчёт
- Не требует установки дополнительных приложений (работает в Telegram)

### Key Features
1. **Регистрация сотрудников** - автоматическое определение пользователя по Telegram
2. **Форма отчёта** - простая таблица с полями для ввода
3. **Автоотправка в Google Sheets** - данные сразу попадают в таблицу
4. **Напоминания** - автоматическое уведомление о необходимости отправить отчёт
5. **Админ-панель** - руководитель видит статус отправки отчётов

---

## 🏗️ Technical Architecture

### Technology Stack

#### Backend
- **Language:** Python 3.11+
- **Framework:** aiogram 3.x (асинхронная библиотека для Telegram Bot API)
- **Database:** SQLite (встроенная, без необходимости отдельного сервера)
- **Scheduler:** APScheduler (для напоминаний)
- **Google API:** gspread + oauth2client (работа с Google Sheets)

#### Frontend (Mini App)
- **HTML5** - структура формы
- **CSS3** - стилизация (адаптивный дизайн)
- **Vanilla JavaScript** - логика и валидация
- **Telegram Web App API** - интеграция с Telegram

#### Hosting & Deployment
- **Code Repository:** GitHub (version control)
- **Hosting:** Render.com (бесплатный план, 750 часов/месяц)
- **CI/CD:** Auto-deploy from GitHub (настроим в Render)
- **Environment Variables:** Render.com dashboard (безопасное хранение токенов)

#### External Services
- **Telegram Bot API** - основной интерфейс
- **Google Sheets API** - хранение отчётов
- **Google Cloud Console** - управление API доступом

---

## 📁 Project Structure

```
telegram-report-bot/
│
├── README.md                      # Описание проекта и инструкции
├── DEVELOPMENT_PLAN.md            # Этот документ
├── requirements.txt               # Python зависимости
├── .env.example                   # Пример файла с переменными окружения
├── .gitignore                     # Исключения для Git
├── runtime.txt                    # Версия Python для Render.com
│
├── bot/
│   ├── __init__.py
│   ├── main.py                    # Точка входа приложения
│   ├── config.py                  # Конфигурация (токены, настройки)
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start.py               # Обработчик команды /start
│   │   ├── report.py              # Обработчик отправки отчётов
│   │   └── admin.py               # Админские команды
│   ├── keyboards.py               # Клавиатуры и кнопки бота
│   ├── middlewares.py             # Middleware для проверки доступа
│   └── states.py                  # FSM состояния (если понадобятся)
│
├── services/
│   ├── __init__.py
│   ├── database.py                # Работа с SQLite
│   ├── google_sheets.py           # Интеграция с Google Sheets
│   └── scheduler.py               # Планировщик напоминаний
│
├── webapp/
│   ├── index.html                 # Форма отчёта (Mini App)
│   ├── css/
│   │   └── style.css              # Стили формы
│   └── js/
│       └── app.js                 # Логика формы и отправка данных
│
├── database/
│   ├── __init__.py
│   ├── models.py                  # Модели данных (Users, Reports)
│   └── database.db                # SQLite файл (создастся автоматически)
│
├── utils/
│   ├── __init__.py
│   ├── validators.py              # Валидация данных
│   └── logger.py                  # Настройка логирования
│
└── credentials/
    └── google_credentials.json    # Google Service Account ключи (НЕ коммитить в Git!)
```

---

## 🗄️ Database Schema (SQLite)

### Table: users
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    username TEXT,
    is_admin BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Table: reports
```sql
CREATE TABLE reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    report_date DATE NOT NULL,
    calls_count INTEGER NOT NULL,
    kp_plus INTEGER NOT NULL,
    kp INTEGER NOT NULL,
    rejections INTEGER NOT NULL,
    inadequate INTEGER NOT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, report_date)  -- Один отчёт в день от пользователя
);
```

### Table: settings
```sql
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 📊 Google Sheets Structure

### Sheet Name: "Ежедневные отчёты"

| Column | Header | Type | Description |
|--------|--------|------|-------------|
| A | Дата | Date | Дата отчёта (формат: ДД.ММ.ГГГГ) |
| B | Сотрудник | Text | ФИО сотрудника |
| C | Кол-во звонков | Number | Общее количество звонков |
| D | КП+ | Number | Закрытые сделки |
| E | КП | Number | В работе |
| F | Отказы | Number | Отказы клиентов |
| G | Неадекв | Number | Нецелевые звонки |
| H | Время отправки | Time | Время отправки отчёта (формат: ЧЧ:ММ) |

**Example:**
```
| Дата       | Сотрудник      | Кол-во звонков | КП+ | КП | Отказы | Неадекв | Время отправки |
|------------|----------------|----------------|-----|----|---------|---------|-----------------
| 18.01.2026 | Иванов Иван    | 45             | 3   | 5  | 30      | 7       | 18:45          |
| 18.01.2026 | Петров Пётр    | 52             | 5   | 8  | 35      | 4       | 18:50          |
```

---

## 🔐 Environment Variables

### Required Variables (хранятся в Render.com или .env локально)

```env
# Telegram Bot
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
ADMIN_TELEGRAM_ID=123456789

# Google Sheets
GOOGLE_SPREADSHEET_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
GOOGLE_CREDENTIALS_PATH=credentials/google_credentials.json

# Application Settings
TIMEZONE=Europe/Moscow
REMINDER_TIME=18:00
DATABASE_PATH=database/database.db

# Logging
LOG_LEVEL=INFO
```

---

## 🎨 User Flow & Features

### 1. Employee Registration Flow

```
User: /start
  ↓
Bot: "Добро пожаловать! Давайте зарегистрируем вас в системе."
  ↓
Bot: "Введите ваше ФИО (Например: Иванов Иван Иванович)"
  ↓
User: Вводит ФИО
  ↓
Bot: "Отлично! Вы зарегистрированы. Используйте кнопку '📊 Отправить отчёт' для отправки ежедневного отчёта."
  ↓
Bot показывает главное меню:
  [📊 Отправить отчёт]
  [📈 Мой статус]
  [ℹ️ Помощь]
```

### 2. Daily Report Submission Flow

```
User: Нажимает "📊 Отправить отчёт"
  ↓
Bot: Открывает Telegram Mini App с формой
  ↓
Mini App показывает:
  - ФИО (автоматически, нельзя изменить)
  - Таблицу с полями:
    * Кол-во звонков: [____]
    * КП+: [____]
    * КП: [____]
    * Отказы: [____]
    * Неадекв: [____]
  - Кнопка [Отправить отчёт]
  ↓
User: Заполняет поля и нажимает "Отправить"
  ↓
Mini App: Валидация данных (все поля заполнены, только цифры)
  ↓
Mini App: Отправляет данные боту через Telegram.WebApp.sendData()
  ↓
Bot: Получает данные, сохраняет в БД
  ↓
Bot: Отправляет данные в Google Sheets
  ↓
Bot: Отправляет подтверждение пользователю
  "✅ Отчёт успешно отправлен! Спасибо за работу."
  ↓
Bot: Уведомляет руководителя (опционально)
  "📊 Новый отчёт от [ФИО] получен"
```

### 3. Reminder System Flow

```
Планировщик: Каждый день в 18:00
  ↓
Система: Проверяет, кто не отправил отчёт сегодня
  ↓
Для каждого сотрудника без отчёта:
  ↓
Bot: "⏰ Напоминаем! Не забудьте отправить отчёт за сегодня."
  [📊 Отправить отчёт сейчас]
  ↓
Если через 30 минут отчёт не отправлен:
  ↓
Bot: "⚠️ Последнее напоминание! Пожалуйста, отправьте отчёт."
  [📊 Отправить отчёт]
```

### 4. Admin Panel Flow

```
Admin: /admin
  ↓
Bot: "👨‍💼 Админ-панель"
  [📊 Статус отчётов сегодня]
  [👥 Список сотрудников]
  [⚙️ Настройки]
  ↓
Admin: Нажимает "📊 Статус отчётов сегодня"
  ↓
Bot: Показывает таблицу:
  "📋 Отчёты за 18.01.2026:
  
  ✅ Иванов Иван - отправлен в 18:45
  ✅ Петров Пётр - отправлен в 18:50
  ❌ Сидоров Сидор - НЕ отправлен
  ❌ Кузнецова Анна - НЕ отправлен
  
  Отправлено: 2/4"
```

---

## 🚀 Development Phases

### Phase 1: Project Setup & Infrastructure (Week 1)

#### Tasks:
1. **Initialize Project**
   - [ ] Create GitHub repository
   - [ ] Set up project structure
   - [ ] Create requirements.txt
   - [ ] Configure .gitignore
   - [ ] Write initial README.md

2. **Set Up Development Environment**
   - [ ] Install Python 3.11+
   - [ ] Create virtual environment
   - [ ] Install dependencies
   - [ ] Set up .env file

3. **Create Telegram Bot**
   - [ ] Talk to @BotFather in Telegram
   - [ ] Create new bot
   - [ ] Get BOT_TOKEN
   - [ ] Configure bot settings (commands, description)

4. **Set Up Google Sheets API**
   - [ ] Create Google Cloud Project
   - [ ] Enable Google Sheets API
   - [ ] Create Service Account
   - [ ] Download credentials JSON
   - [ ] Create Google Sheet for reports
   - [ ] Share sheet with service account email

5. **Database Setup**
   - [ ] Create database models (models.py)
   - [ ] Implement database service (database.py)
   - [ ] Create initialization script
   - [ ] Test database operations

#### Deliverables:
- ✅ Working project structure
- ✅ Telegram bot created and configured
- ✅ Google Sheets API connected
- ✅ Database initialized

#### Success Criteria:
- Bot responds to /start command
- Can connect to Google Sheets
- Database creates tables successfully

---

### Phase 2: Core Bot Functionality (Week 2)

#### Tasks:
1. **User Registration System**
   - [ ] Implement /start handler
   - [ ] Create user registration flow
   - [ ] Store user data in database
   - [ ] Implement user validation

2. **Main Menu & Keyboards**
   - [ ] Create main menu keyboard
   - [ ] Implement menu handlers
   - [ ] Add help command (/help)
   - [ ] Add status command (/status)

3. **Mini App Form (Frontend)**
   - [ ] Create HTML structure (index.html)
   - [ ] Design CSS styles (style.css)
   - [ ] Implement form validation (app.js)
   - [ ] Integrate Telegram Web App API
   - [ ] Test form on mobile devices

4. **Report Submission Backend**
   - [ ] Implement data receiver from Mini App
   - [ ] Validate incoming data
   - [ ] Save report to database
   - [ ] Send report to Google Sheets
   - [ ] Send confirmation to user

5. **Google Sheets Integration**
   - [ ] Implement google_sheets.py service
   - [ ] Create append_report() method
   - [ ] Format data for sheets
   - [ ] Handle API errors
   - [ ] Test with real data

#### Deliverables:
- ✅ Users can register
- ✅ Mini App form working
- ✅ Reports saved to database
- ✅ Reports appear in Google Sheets

#### Success Criteria:
- User can open Mini App from bot
- Form validates data correctly
- Reports successfully saved
- Data appears in Google Sheets

---

### Phase 3: Advanced Features (Week 3)

#### Tasks:
1. **Reminder System**
   - [ ] Implement scheduler.py
   - [ ] Set up APScheduler
   - [ ] Create daily check function
   - [ ] Send reminders to users without reports
   - [ ] Implement repeat reminders

2. **Admin Panel**
   - [ ] Create /admin command
   - [ ] Implement admin middleware
   - [ ] Show daily report status
   - [ ] Display employee list
   - [ ] Add settings management

3. **User Status Feature**
   - [ ] Implement /status command
   - [ ] Show user's today report status
   - [ ] Display recent reports history
   - [ ] Show statistics

4. **Error Handling & Logging**
   - [ ] Set up logging system (logger.py)
   - [ ] Add try-catch blocks
   - [ ] Implement error notifications
   - [ ] Create error recovery mechanisms

5. **Data Validation**
   - [ ] Implement validators.py
   - [ ] Validate report data
   - [ ] Validate user inputs
   - [ ] Handle edge cases

#### Deliverables:
- ✅ Automatic reminders working
- ✅ Admin can see all reports status
- ✅ Users can check their status
- ✅ Proper error handling

#### Success Criteria:
- Reminders sent at 18:00 daily
- Admin panel shows correct data
- No crashes on invalid input
- All errors logged properly

---

### Phase 4: Testing & Deployment (Week 4)

#### Tasks:
1. **Local Testing**
   - [ ] Test all user flows
   - [ ] Test admin features
   - [ ] Test edge cases
   - [ ] Test error scenarios
   - [ ] Performance testing

2. **Documentation**
   - [ ] Update README.md
   - [ ] Write deployment guide
   - [ ] Create user manual
   - [ ] Document API endpoints
   - [ ] Add code comments

3. **Deploy to Render.com**
   - [ ] Create Render.com account
   - [ ] Connect GitHub repository
   - [ ] Configure environment variables
   - [ ] Set up auto-deploy
   - [ ] Configure web service settings

4. **Post-Deployment Testing**
   - [ ] Test bot in production
   - [ ] Verify Google Sheets integration
   - [ ] Test reminders in production
   - [ ] Monitor logs
   - [ ] Fix any production issues

5. **User Onboarding**
   - [ ] Create user guide
   - [ ] Train employees
   - [ ] Set up admin account
   - [ ] Conduct first week monitoring

#### Deliverables:
- ✅ Bot deployed and running 24/7
- ✅ All features working in production
- ✅ Documentation complete
- ✅ Users trained

#### Success Criteria:
- Bot responds within 1 second
- No downtime in 24 hours
- All employees successfully registered
- Reports flowing to Google Sheets

---

## 📦 Dependencies (requirements.txt)

```txt
# Telegram Bot Framework
aiogram==3.4.1
aiohttp==3.9.1

# Google Sheets Integration
gspread==6.0.0
oauth2client==4.1.3

# Scheduling
APScheduler==3.10.4

# Database
aiosqlite==0.19.0

# Environment Variables
python-dotenv==1.0.0

# Utilities
python-dateutil==2.8.2
pytz==2023.3

# Logging
colorlog==6.8.0
```

---

## 🔧 Configuration Files

### .env.example
```env
# Telegram Bot Configuration
BOT_TOKEN=your_bot_token_here
ADMIN_TELEGRAM_ID=your_telegram_id_here

# Google Sheets Configuration
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id_here
GOOGLE_CREDENTIALS_PATH=credentials/google_credentials.json

# Application Settings
TIMEZONE=Europe/Moscow
REMINDER_TIME=18:00
REMINDER_REPEAT_AFTER_MINUTES=30
DATABASE_PATH=database/database.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log

# Development
DEBUG=False
```

### .gitignore
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment
.env
.env.local

# Database
*.db
*.sqlite3

# Logs
*.log
logs/

# Credentials
credentials/
*.json

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Render
.render/
```

### runtime.txt (для Render.com)
```
python-3.11.7
```

---

## 🎯 Key Implementation Details

### 1. Bot Configuration (bot/config.py)

```python
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Telegram
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_TELEGRAM_ID = int(os.getenv('ADMIN_TELEGRAM_ID', 0))
    
    # Google Sheets
    GOOGLE_SPREADSHEET_ID = os.getenv('GOOGLE_SPREADSHEET_ID')
    GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials/google_credentials.json')
    
    # Application
    TIMEZONE = os.getenv('TIMEZONE', 'Europe/Moscow')
    REMINDER_TIME = os.getenv('REMINDER_TIME', '18:00')
    REMINDER_REPEAT_AFTER_MINUTES = int(os.getenv('REMINDER_REPEAT_AFTER_MINUTES', 30))
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'database/database.db')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/bot.log')
    
    # Development
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Mini App URL (будет на Render.com после деплоя)
    WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://your-app.onrender.com/webapp')
```

### 2. Database Service Interface

```python
class DatabaseService:
    async def create_user(telegram_id, full_name, username=None)
    async def get_user(telegram_id)
    async def get_all_users()
    async def update_user(telegram_id, **kwargs)
    async def delete_user(telegram_id)
    
    async def create_report(user_id, report_date, calls_count, kp_plus, kp, rejections, inadequate)
    async def get_report(user_id, report_date)
    async def get_user_reports(user_id, limit=10)
    async def get_daily_reports(report_date)
    async def check_report_exists(user_id, report_date)
```

### 3. Google Sheets Service Interface

```python
class GoogleSheetsService:
    async def append_report(report_data: dict)
    async def get_all_reports()
    async def get_report_by_date(date)
    async def update_report(row_number, report_data)
    async def delete_report(row_number)
```

### 4. Scheduler Service Interface

```python
class SchedulerService:
    async def start()
    async def stop()
    async def send_daily_reminders()
    async def send_repeat_reminders()
    async def check_and_notify_admin()
```

---

## 🧪 Testing Strategy

### Manual Testing Checklist

#### User Registration
- [ ] New user can start bot with /start
- [ ] User provides full name
- [ ] User data saved to database
- [ ] User receives welcome message
- [ ] Main menu keyboard displayed

#### Report Submission
- [ ] User clicks "📊 Отправить отчёт"
- [ ] Mini App opens correctly
- [ ] User's name auto-filled
- [ ] All fields accept only numbers
- [ ] Submit button disabled if fields empty
- [ ] Form validates data before sending
- [ ] Report saved to database
- [ ] Report appears in Google Sheets
- [ ] User receives confirmation

#### Reminders
- [ ] Reminder sent at configured time
- [ ] Only users without today's report receive reminder
- [ ] Repeat reminder sent after 30 minutes
- [ ] No reminders after report submitted

#### Admin Panel
- [ ] Admin can access /admin
- [ ] Non-admin users cannot access /admin
- [ ] Status shows correct report count
- [ ] Employee list is complete
- [ ] Settings can be changed

#### Error Handling
- [ ] Invalid input handled gracefully
- [ ] Network errors don't crash bot
- [ ] Google Sheets API errors logged
- [ ] User receives helpful error messages

---

## 🚀 Deployment Guide

### Step 1: Prepare for Deployment

1. **Commit all code to GitHub:**
```bash
git add .
git commit -m "Initial bot implementation"
git push origin main
```

2. **Verify .env variables are in .gitignore**

3. **Test locally one more time**

### Step 2: Create Render.com Service

1. Go to https://render.com
2. Sign up / Log in (можно через GitHub)
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Configure service:
   - **Name:** telegram-report-bot
   - **Region:** Frankfurt (EU Central)
   - **Branch:** main
   - **Root Directory:** (leave empty)
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot/main.py`
   - **Plan:** Free

### Step 3: Configure Environment Variables

In Render.com dashboard, add all variables from .env:
- BOT_TOKEN
- ADMIN_TELEGRAM_ID
- GOOGLE_SPREADSHEET_ID
- GOOGLE_CREDENTIALS_PATH
- And all others...

**Important:** For GOOGLE_CREDENTIALS_PATH, you'll need to:
1. Copy content of google_credentials.json
2. Create environment variable GOOGLE_CREDENTIALS_JSON with JSON content
3. Modify code to load from environment variable instead of file

### Step 4: Deploy

1. Click "Create Web Service"
2. Wait for deployment (5-10 minutes)
3. Check logs for errors
4. Test bot in Telegram

### Step 5: Configure Webhook (если используется webhook вместо polling)

```python
# В main.py добавить после инициализации бота:
WEBHOOK_URL = f"https://your-app.onrender.com/webhook"
await bot.set_webhook(WEBHOOK_URL)
```

---

## 📚 Resources & Documentation

### Official Documentation
- **aiogram:** https://docs.aiogram.dev/en/latest/
- **Telegram Bot API:** https://core.telegram.org/bots/api
- **Telegram Mini Apps:** https://core.telegram.org/bots/webapps
- **Google Sheets API:** https://developers.google.com/sheets/api
- **Render.com Docs:** https://render.com/docs

### Tutorials
- Creating Telegram Bot with aiogram 3.x
- Google Sheets API Python Quickstart
- Deploying Python app to Render.com

### Code Examples
- aiogram examples: https://github.com/aiogram/aiogram/tree/dev-3.x/examples
- gspread examples: https://docs.gspread.org/en/latest/user-guide.html

---

## 🎓 For Claude Code: Development Navigation

### When user asks "What's next?" or "What should I do now?"

**Check current project state and respond with:**

1. **If project not initialized:**
   - "Let's start by setting up the project structure. I'll create all necessary folders and files."
   - Then create project structure

2. **If structure exists but no code:**
   - "Now let's implement [next component from Phase]. I'll start with [specific file]."
   - Implement next logical component

3. **If basic bot works:**
   - "Great! Basic bot is working. Let's add [next feature]."
   - Implement next feature from development plan

4. **If bot complete but not deployed:**
   - "Bot is ready for deployment! Let's prepare it for Render.com."
   - Guide through deployment steps

5. **If deployed:**
   - "Bot is live! Let's test all features and fix any issues."
   - Test and debug

### Progress Tracking

Always check:
- [ ] Phase 1: Infrastructure ✓ / ✗
- [ ] Phase 2: Core Features ✓ / ✗
- [ ] Phase 3: Advanced Features ✓ / ✗
- [ ] Phase 4: Deployment ✓ / ✗

### Quick Commands for User

Suggest these commands based on context:
- `python bot/main.py` - Run bot locally
- `git status` - Check what changed
- `git add . && git commit -m "message"` - Commit changes
- `pip install -r requirements.txt` - Install dependencies
- `pytest` - Run tests (if we add them)

---

## 🆘 Troubleshooting Guide

### Common Issues & Solutions

#### Bot doesn't respond
1. Check if BOT_TOKEN is correct
2. Verify bot is running (`python bot/main.py`)
3. Check internet connection
4. Look at console logs for errors

#### Google Sheets not updating
1. Verify GOOGLE_SPREADSHEET_ID is correct
2. Check if service account has access to sheet
3. Verify credentials JSON file exists
4. Check Google API quotas

#### Mini App doesn't open
1. Verify WEBAPP_URL is correct
2. Check if webapp files are accessible
3. Test in Telegram mobile app (desktop may not support)
4. Check browser console for errors

#### Database errors
1. Check if database file exists
2. Verify file permissions
3. Check if tables were created
4. Try deleting database.db and recreating

#### Reminders not working
1. Verify timezone is correct
2. Check if scheduler is started
3. Verify REMINDER_TIME format
4. Check logs for scheduler errors

---

## 📈 Future Enhancements (Post-MVP)

### Phase 2 Features (если потребуется)
- [ ] Статистика по сотрудникам (графики)
- [ ] Экспорт отчётов в Excel
- [ ] Редактирование отправленных отчётов
- [ ] Комментарии к отчётам
- [ ] Уведомления руководителю в реальном времени
- [ ] Интеграция с CRM системами
- [ ] Мобильное приложение (вместо Mini App)
- [ ] Голосовой ввод данных
- [ ] AI-анализ эффективности сотрудников

---

## ✅ Success Metrics

### Technical Metrics
- Bot uptime: >99%
- Response time: <1 second
- Error rate: <1%
- Reports processed: 100%

### Business Metrics
- Time to submit report: <2 minutes (vs 10+ minutes manually)
- Report completion rate: >95%
- User satisfaction: >4/5
- Adoption rate: 100% of employees

---

## 📞 Support & Maintenance

### Daily Monitoring
- Check bot is running
- Review error logs
- Verify reports in Google Sheets
- Monitor user complaints

### Weekly Tasks
- Review all logs
- Check database size
- Update dependencies if needed
- Backup database and sheets

### Monthly Tasks
- Review and optimize code
- Update documentation
- Plan new features
- User feedback collection

---

## 🎉 Project Completion Checklist

- [ ] All features implemented
- [ ] All tests passed
- [ ] Documentation complete
- [ ] Deployed to production
- [ ] Users trained
- [ ] Monitoring set up
- [ ] Backup strategy in place
- [ ] Support process defined
- [ ] Success metrics achieved
- [ ] User feedback collected

---

**Document Version:** 1.0  
**Last Updated:** 18.01.2026  
**Author:** Claude (Anthropic)  
**Project Owner:** [Your Name]  
**Status:** Ready for Development 🚀

---

## 🔄 Next Steps for Development

1. **Initialize project structure** (you can ask me: "Create project structure")
2. **Set up Telegram Bot** (you can ask me: "Help me create Telegram bot")
3. **Configure Google Sheets** (you can ask me: "Guide me through Google Sheets setup")
4. **Start coding!** (you can ask me: "Let's implement user registration")

**Ready to start? Just tell me what you want to do next!** 🎯
