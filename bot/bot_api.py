from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import logging
import asyncio

from handlers.support_api_handlers import SupportAPIHandlers
from handlers.common_handlers import CommonHandlers
from handlers.catalog_handlers import CatalogHandlers
from config import BOT_TOKEN, get_api_url

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Инициализация бота
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Инициализация обработчиков с API
    support_handlers = SupportAPIHandlers(api_base_url=get_api_url())
    common_handlers = CommonHandlers()
    catalog_handlers = CatalogHandlers()
    
    # Регистрация роутеров
    dp.include_router(support_handlers.router)
    dp.include_router(common_handlers.router)
    dp.include_router(catalog_handlers.router)
    
    # Запуск бота
    logger.info("Бот с API запущен")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка бота: {e}")

if __name__ == "__main__":
    asyncio.run(main())