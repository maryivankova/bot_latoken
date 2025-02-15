# main.py
from telegram.ext import ApplicationBuilder
from handlers import register_handlers
from config import TOKEN
from pytz import timezone

def main() -> None:
    # Создаем приложение
    application = ApplicationBuilder().token(TOKEN).build()

    # Настраиваем временную зону для JobQueue
    tz = timezone('Europe/Istanbul')
    application.job_queue.scheduler.timezone = tz

    # Регистрируем обработчики
    register_handlers(application)

    # Запускаем бота в режиме polling
    application.run_polling()

if __name__ == '__main__':
    main()