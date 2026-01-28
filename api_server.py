"""
Простой API сервер для приема отчетов от Mini App
"""

import json
import asyncio
from datetime import datetime
from aiohttp import web
from services.database import DatabaseService
from bot.config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

async def submit_report_handler(request):
    """Обработка отправки отчета через API"""
    try:
        data = await request.json()
        logger.info(f"API: Received report data: {data}")

        # Валидация данных
        required_fields = ['calls_count', 'kp_plus', 'kp', 'rejections', 'inadequate', 'telegram_user_id']
        for field in required_fields:
            if field not in data:
                return web.json_response({'error': f'Missing field: {field}'}, status=400)

        # Инициализация базы данных
        db = DatabaseService()

        # Получение пользователя
        user = await db.get_user(data['telegram_user_id'])
        if not user:
            return web.json_response({'error': 'User not found'}, status=404)

        # Валидация данных
        try:
            calls_count = int(data['calls_count'])
            kp_plus = int(data['kp_plus'])
            kp = int(data['kp'])
            rejections = int(data['rejections'])
            inadequate = int(data['inadequate'])
        except (ValueError, TypeError):
            return web.json_response({'error': 'Invalid data types'}, status=400)

        if calls_count < 0 or kp_plus < 0 or kp < 0 or rejections < 0 or inadequate < 0:
            return web.json_response({'error': 'All values must be positive'}, status=400)

        if calls_count == 0:
            return web.json_response({'error': 'Call count cannot be zero'}, status=400)

        if (kp_plus + kp) > calls_count:
            return web.json_response({'error': 'Resultative calls exceed total calls'}, status=400)

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
            # Отправка в Google Sheets (если нужно)
            from bot.handlers.report import send_to_google_sheets
            google_sheets_data = {
                "employee_name": user.full_name,
                "report_date": today,
                "calls_count": calls_count,
                "kp_plus": kp_plus,
                "kp": kp,
                "rejections": rejections,
                "inadequate": inadequate
            }

            await send_to_google_sheets(google_sheets_data)

            return web.json_response({
                'status': 'success',
                'message': 'Вы успешно передали данные'
            })
        else:
            return web.json_response({'error': 'Failed to save report'}, status=500)

    except Exception as e:
        logger.error(f"API error: {e}")
        return web.json_response({'error': 'Internal server error'}, status=500)

async def init_api_app():
    """Инициализация API приложения"""
    app = web.Application()
    app.router.add_post('/api/submit_report', submit_report_handler)
    return app

if __name__ == '__main__':
    app = init_api_app()
    web.run_app(app, host='localhost', port=8080)