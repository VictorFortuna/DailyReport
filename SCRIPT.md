# Google Apps Script для веб-хука

## Код для Apps Script

```javascript
function doPost(e) {
  try {
    // Получаем данные из POST запроса
    const data = JSON.parse(e.postData.contents);

    // Проверяем секретный ключ (ЗАМЕНИТЕ НА СВОЙ!)
    const SECRET_KEY = "daily_report_bot_2025_secure_key";
    if (data.secret_key !== SECRET_KEY) {
      return ContentService.createTextOutput(JSON.stringify({
        status: 'error',
        message: 'Unauthorized access'
      })).setMimeType(ContentService.MimeType.JSON);
    }

    // Открываем активную таблицу
    const sheet = SpreadsheetApp.getActiveSheet();

    // Добавляем новую строку с данными согласно структуре таблицы
    sheet.appendRow([
      data.report_date, // A: Дата заполнения
      data.employee_name, // B: ФИО сотрудника
      "", // C: Направления (пустое, заполняется вручную)
      "", // D: Новые клиенты (пустое, заполняется вручную)
      data.calls_count, // E: Общее Кол-во звонков клиентам
      data.inadequate, // F: Пустые звонки
      data.rejections, // G: Звонки клиента
      data.kp_plus, // H: Договор КЦ+
      data.kp, // I: Договор КЦ
      "" // J: Договор подбора (пустое, заполняется вручную)
    ]);

    return ContentService.createTextOutput(JSON.stringify({status: 'success'}))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      status: 'error',
      message: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}
```

## Инструкция по настройке

1. Откройте вашу Google Таблицу
2. Нажмите `Расширения` → `Apps Script`
3. Замените весь код на код выше
4. Нажмите `Сохранить`
5. Нажмите `Развернуть` → `Новое развертывание`
6. Выберите тип `Веб-приложение`
7. В настройках доступа выберите `Любой пользователь`
8. Нажмите `Развернуть`
9. Скопируйте URL веб-приложения

## Структура данных

Скрипт ожидает данные в формате:
```json
{
  "employee_name": "Имя Фамилия",
  "report_date": "2024-01-26",
  "calls_count": 50,
  "kp_plus": 5,
  "kp": 10,
  "rejections": 20,
  "inadequate": 15
}
```