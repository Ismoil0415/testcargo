from aiogram import Bot, Dispatcher, types
from aiogram.types import ContentType
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage  # Import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
import asyncio
import handlers
from database import notify_users_about_arrivals
from dotenv import load_dotenv
from os import getenv
import logging
import sys

load_dotenv()

TOKEN = getenv("TOKEN")

bot = Bot(token=TOKEN)

storage = MemoryStorage()  # Initialize MemoryStorage
dp = Dispatcher(bot, storage=storage)

dp.middleware.setup(LoggingMiddleware())

dp.register_message_handler(handlers.start, commands="start")
dp.register_message_handler(handlers.admin, commands="admin_panel")

dp.register_message_handler(handlers.start, state=handlers.Form.start)
dp.register_message_handler(handlers.handle_phone_number, state=handlers.Form.phone_number)
dp.register_message_handler(handlers.admin, state=handlers.Form.admin)
dp.register_message_handler(handlers.handle_password, state=handlers.Form.password)
dp.register_message_handler(handlers.check_trackCode, state=handlers.Form.check_tracking)
dp.register_message_handler(handlers.changeStatusTrack, state=handlers.Form.changeStatus)
dp.register_message_handler(handlers.adminPage, state=handlers.Form.adminPage)

dp.register_message_handler(handlers.deleteList, content_types=[ContentType.DOCUMENT, ContentType.TEXT], state=handlers.Form.deleteList)
dp.register_message_handler(handlers.updateList, content_types=[ContentType.DOCUMENT, ContentType.TEXT], state=handlers.Form.updateList)

dp.register_callback_query_handler(handlers.link_track_yes, text="link_track_yes")
dp.register_callback_query_handler(handlers.link_track_no, text="link_track_no")

dp.register_message_handler(handlers.myOrders, Text(equals="📝 Мои трек-коды"))
dp.register_message_handler(handlers.prices, Text(equals="💵 Цены"))
dp.register_message_handler(handlers.notAllowed, Text(equals="🚫 Запрещённые товары"))
dp.register_message_handler(handlers.contactUs, Text(equals="💬 Связаться с нами"))
dp.register_message_handler(handlers.getAddress, Text(equals="📍 Получить адрес"))
dp.register_message_handler(handlers.subscribe, Text(equals="👤 Подписаться"))
dp.register_message_handler(handlers.freeStudy, Text(equals="🎓 Бесплатное обучение"))
dp.register_message_handler(handlers.exchange, Text(equals="💱 Курс обмена (RMB/TJS)"))
dp.register_message_handler(handlers.check_trackCodeMessage, Text(equals="📦 Отслеживать трек-коды"))

dp.register_message_handler(handlers.updatePage, Text(equals="📦 Обновить список трек-кодов"))
dp.register_message_handler(handlers.statistics, Text(equals="📈 Статистика"))
dp.register_message_handler(handlers.notify_users, text="🔔 Уведомить о прибытии трек-кодов")
dp.register_message_handler(handlers.changeStatus, Text(equals="♻️ Изменение статуса трек-кодов"))
dp.register_message_handler(handlers.deleteListMessage, Text(equals="🗑 Удалить завершенные треки"))
dp.register_message_handler(handlers.addManually, Text(equals="📝 Добавить трек-код вручную"))
dp.register_message_handler(handlers.exportUserData, Text(equals="📤 Экспорт данных"))

dp.register_message_handler(handlers.cancel_task, Text(equals="Отмена/Выход"))

if __name__ == "__main__":
    print("🚀 Bot is running...")  # Debugging message
    logging.basicConfig(level=logging.INFO,
                        format = '%(asctime)s - %(name)s  - %(levelname)s - %(message)s',
                        handlers = [
                            logging.FileHandler("bot.log"),
                            logging.StreamHandler(sys.stdout)
                        ]
                        
                        )
    executor.start_polling(dp, skip_updates=False)
