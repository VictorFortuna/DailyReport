# Деплой на PythonAnywhere

## Шаги развертывания

### 1. Регистрация
- Зайти на [www.pythonanywhere.com](https://www.pythonanywhere.com)
- Создать бесплатный аккаунт (3 месяца полный доступ)

### 2. Клонирование проекта
Открыть Bash консоль на PythonAnywhere:
```bash
cd ~
git clone https://github.com/VictorFortuna/DailyReport.git
cd DailyReport
```

### 3. Установка зависимостей
```bash
pip3.11 install --user -r requirements.txt
```

### 4. Настройка переменных окружения
Создать файл `.env`:
```bash
nano .env
```

Добавить:
```
BOT_TOKEN=ваш_токен_бота
ADMIN_TELEGRAM_ID=325463089
WEBAPP_URL=https://ваш_домен.pythonanywhere.com
DATABASE_PATH=./data/reports.db
REMINDER_TIME=17:45
TIMEZONE=Europe/Moscow
```

### 5. Создание Always-On Task
- Зайти в Dashboard → Tasks
- Создать новую Always-On Task
- Command: `/home/ваш_username/DailyReport/start_bot.sh`
- Нажать Create

### 6. Настройка веб-приложения (для Mini App)
- Зайти в Web → Add a new web app
- Manual configuration → Python 3.11
- Source code: `/home/ваш_username/DailyReport/webapp`

### 7. Проверка работы
- Проверить логи в Tasks
- Отправить `/start` боту в Telegram
- Проверить админ-панель `/admin`

## Ограничения бесплатного плана
- 1 Always-On Task (достаточно для бота)
- CPU seconds ограничены (но для бота хватает)
- 512MB дискового пространства
- Outbound интернет только к whitelist доменам (включая Telegram API)

## Мониторинг
- Логи Always-On Task в Dashboard
- Если бот "засыпает" - перезапустить Task
- Проверять статистику использования CPU

## Преимущества для разработки
- SSH доступ для отладки
- Jupyter notebooks для экспериментов
- MySQL база данных (если захочешь upgrade с SQLite)
- Простая интеграция с GitHub