// Telegram Mini App для отправки отчётов

class ReportApp {
    constructor() {
        this.tg = window.Telegram.WebApp;
        this.isFormValid = false;

        this.initTelegramApp();
        this.initElements();
        this.initEventListeners();
        this.setupForm();
    }

    initTelegramApp() {
        // Инициализация Telegram Web App
        this.tg.ready();
        this.tg.expand();

        // Установить цвета темы
        if (this.tg.themeParams) {
            document.documentElement.style.setProperty('--tg-theme-bg-color', this.tg.themeParams.bg_color || '#ffffff');
            document.documentElement.style.setProperty('--tg-theme-text-color', this.tg.themeParams.text_color || '#000000');
            document.documentElement.style.setProperty('--tg-theme-hint-color', this.tg.themeParams.hint_color || '#999999');
            document.documentElement.style.setProperty('--tg-theme-button-color', this.tg.themeParams.button_color || '#007aff');
            document.documentElement.style.setProperty('--tg-theme-button-text-color', this.tg.themeParams.button_text_color || '#ffffff');
            document.documentElement.style.setProperty('--tg-theme-secondary-bg-color', this.tg.themeParams.secondary_bg_color || '#f8f8f8');
        }

        console.log('Telegram Web App initialized:', this.tg);
    }

    initElements() {
        // Основные элементы
        this.form = document.getElementById('reportForm');
        this.submitButton = document.getElementById('submitButton');
        this.loadingDiv = document.getElementById('loading');
        this.successDiv = document.getElementById('success');
        this.errorDiv = document.getElementById('error');
        this.errorMessage = document.getElementById('errorMessage');
        this.retryButton = document.getElementById('retryButton');

        // Поля формы
        this.employeeName = document.getElementById('employeeName');
        this.callsCount = document.getElementById('callsCount');
        this.kpPlus = document.getElementById('kpPlus');
        this.kp = document.getElementById('kp');
        this.rejections = document.getElementById('rejections');
        this.inadequate = document.getElementById('inadequate');

        // Элементы сводки
        this.totalCalls = document.getElementById('totalCalls');
        this.resultativeCalls = document.getElementById('resultativeCalls');
        this.conversion = document.getElementById('conversion');

        // Дата
        this.currentDate = document.getElementById('currentDate');
    }

    initEventListeners() {
        // Отправка формы
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));

        // Валидация полей в реальном времени
        const inputs = [this.callsCount, this.kpPlus, this.kp, this.rejections, this.inadequate];
        inputs.forEach(input => {
            input.addEventListener('input', () => this.updateSummaryAndValidation());
            input.addEventListener('blur', () => this.validateField(input));
        });

        // Кнопка повтора
        this.retryButton.addEventListener('click', () => this.resetToForm());
    }

    setupForm() {
        // Установить дату
        const today = new Date().toLocaleDateString('ru-RU', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
        this.currentDate.textContent = today;

        // Установить имя пользователя из Telegram
        const user = this.tg.initDataUnsafe?.user;
        if (user) {
            const fullName = `${user.first_name} ${user.last_name || ''}`.trim();
            this.employeeName.value = fullName;
            console.log('User info:', user);
        } else {
            this.employeeName.value = 'Пользователь';
            console.warn('No user info available');
        }

        // Инициализировать валидацию
        this.updateSummaryAndValidation();
    }

    updateSummaryAndValidation() {
        const calls = parseInt(this.callsCount.value) || 0;
        const kpPlus = parseInt(this.kpPlus.value) || 0;
        const kp = parseInt(this.kp.value) || 0;
        const rejections = parseInt(this.rejections.value) || 0;
        const inadequate = parseInt(this.inadequate.value) || 0;

        // Обновить сводку
        this.totalCalls.textContent = calls;

        const resultative = kpPlus + kp;
        this.resultativeCalls.textContent = resultative;

        const conversionPercent = calls > 0 ? Math.round((resultative / calls) * 100) : 0;
        this.conversion.textContent = `${conversionPercent}%`;

        // Проверить валидность формы
        this.isFormValid = this.validateForm();
        this.submitButton.disabled = !this.isFormValid;

        // Обновить цвет конверсии
        const conversionElement = this.conversion;
        if (conversionPercent >= 20) {
            conversionElement.style.color = '#34c759'; // Зеленый
        } else if (conversionPercent >= 10) {
            conversionElement.style.color = '#ff9500'; // Оранжевый
        } else {
            conversionElement.style.color = '#ff3b30'; // Красный
        }
    }

    validateField(input) {
        const value = parseInt(input.value);

        // Проверить базовые правила
        if (isNaN(value) || value < 0) {
            input.style.borderColor = '#ff3b30';
            return false;
        }

        // Проверить логические правила
        if (input === this.callsCount && value === 0) {
            input.style.borderColor = '#ff9500';
            return false;
        }

        // Проверить, что результативные не больше общего количества
        const calls = parseInt(this.callsCount.value) || 0;
        const kpPlus = parseInt(this.kpPlus.value) || 0;
        const kp = parseInt(this.kp.value) || 0;

        if (calls > 0 && (kpPlus + kp) > calls) {
            if (input === this.kpPlus || input === this.kp) {
                input.style.borderColor = '#ff9500';
                return false;
            }
        }

        input.style.borderColor = 'var(--tg-theme-hint-color, #e0e0e0)';
        return true;
    }

    validateForm() {
        const calls = parseInt(this.callsCount.value);
        const kpPlus = parseInt(this.kpPlus.value);
        const kp = parseInt(this.kp.value);
        const rejections = parseInt(this.rejections.value);
        const inadequate = parseInt(this.inadequate.value);

        // Все поля должны быть заполнены и >= 0
        if (isNaN(calls) || isNaN(kpPlus) || isNaN(kp) ||
            isNaN(rejections) || isNaN(inadequate)) {
            return false;
        }

        if (calls < 0 || kpPlus < 0 || kp < 0 || rejections < 0 || inadequate < 0) {
            return false;
        }

        // Количество звонков должно быть > 0
        if (calls === 0) {
            return false;
        }

        // Результативные не могут быть больше общего количества
        if ((kpPlus + kp) > calls) {
            return false;
        }

        return true;
    }

    async handleSubmit(event) {
        event.preventDefault();

        if (!this.isFormValid) {
            this.showError('Пожалуйста, заполните все поля корректно');
            return;
        }

        this.showLoading();

        const reportData = {
            calls_count: parseInt(this.callsCount.value),
            kp_plus: parseInt(this.kpPlus.value),
            kp: parseInt(this.kp.value),
            rejections: parseInt(this.rejections.value),
            inadequate: parseInt(this.inadequate.value),
            report_date: new Date().toISOString().split('T')[0],
            employee_name: this.employeeName.value
        };

        try {
            console.log('Sending report data:', reportData);

            // Отправить данные через Telegram Web App
            this.tg.sendData(JSON.stringify(reportData));

            // Показать успех (это сработает, если sendData не закроет приложение)
            setTimeout(() => {
                this.showSuccess();
            }, 1000);

        } catch (error) {
            console.error('Error submitting report:', error);
            this.showError('Ошибка отправки отчёта. Попробуйте ещё раз.');
        }
    }

    showLoading() {
        this.form.classList.add('hidden');
        this.successDiv.classList.add('hidden');
        this.errorDiv.classList.add('hidden');
        this.loadingDiv.classList.remove('hidden');
    }

    showSuccess() {
        this.form.classList.add('hidden');
        this.loadingDiv.classList.add('hidden');
        this.errorDiv.classList.add('hidden');
        this.successDiv.classList.remove('hidden');

        // Уведомить Telegram, что приложение готово к закрытию
        setTimeout(() => {
            this.tg.close();
        }, 2000);
    }

    showError(message) {
        this.errorMessage.textContent = message;
        this.form.classList.add('hidden');
        this.loadingDiv.classList.add('hidden');
        this.successDiv.classList.add('hidden');
        this.errorDiv.classList.remove('hidden');
    }

    resetToForm() {
        this.form.classList.remove('hidden');
        this.loadingDiv.classList.add('hidden');
        this.successDiv.classList.add('hidden');
        this.errorDiv.classList.add('hidden');
    }
}

// Инициализация приложения после загрузки DOM
document.addEventListener('DOMContentLoaded', () => {
    new ReportApp();
});

// Обработка ошибок
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
});

// Обработка необработанных промисов
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    event.preventDefault();
});