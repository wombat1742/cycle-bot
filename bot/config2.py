import os
from dotenv import load_dotenv

load_dotenv()

# Конфигурация бота
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
ADMIN_IDS = [123456789]  # ID администраторов

# Настройки магазина
SHOP_NAME = "BikeShop"
SHOP_PHONE = "+7 (999) 123-45-67"
SHOP_ADDRESS = "г. Москва, ул. Велосипедная, 1"
