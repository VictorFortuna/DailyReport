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

    # Mini App URL (GitHub Pages)
    WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://victorfortuna.github.io/DailyReport')

    # Google Sheets Webhook
    GOOGLE_SHEETS_WEBHOOK_URL = os.getenv('GOOGLE_SHEETS_WEBHOOK_URL', 'https://script.google.com/macros/s/AKfycbyopLLgXsfJQzBN81HWeuTr-2PWXZVV52Vdkvw3LJbHpgwq7k9ioLfMWtsnvpWoRcqD2w/exec')
    GOOGLE_SHEETS_SECRET_KEY = os.getenv('GOOGLE_SHEETS_SECRET_KEY', 'daily_report_bot_2025_secure_key')

    @classmethod
    def validate(cls):
        """Validate required environment variables"""
        errors = []

        if not cls.BOT_TOKEN:
            errors.append("BOT_TOKEN is required")

        if not cls.ADMIN_TELEGRAM_ID:
            errors.append("ADMIN_TELEGRAM_ID is required")

        if not cls.GOOGLE_SPREADSHEET_ID:
            errors.append("GOOGLE_SPREADSHEET_ID is required")

        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")

        return True