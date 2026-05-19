import threading
import os
from app import app  # импортируем Flask-приложение
from bot import run_bot  # функция запуска бота

if __name__ == '__main__':
    # Запускаем Flask в отдельном потоке
    port = int(os.environ.get("PORT", 5000))
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False), daemon=True).start()
    # Запускаем бота
    run_bot()
