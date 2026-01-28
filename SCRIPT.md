function doGet(e) {
  return ContentService.createTextOutput(JSON.stringify({
    status: 'ready',
    message: 'Daily Report Google Apps Script is ready',
    timestamp: new Date().toISOString()
  })).setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const SECRET_KEY = "daily_report_bot_2025_secure_key";
    if (data.secret_key !== SECRET_KEY) {
      return ContentService.createTextOutput(JSON.stringify({
        status: 'error',
        message: 'Unauthorized access'
      })).setMimeType(ContentService.MimeType.JSON);
    }
    const sheet = SpreadsheetApp.getActiveSheet();
    sheet.appendRow([
      data.report_date,
      data.employee_name,
      "",
      "",
      data.calls_count,
      data.inadequate,
      "",
      data.rejections,
      data.kp_plus,
      data.kp
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