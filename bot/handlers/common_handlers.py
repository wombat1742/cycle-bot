from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from keyboards import get_main_menu_keyboard

class CommonHandlers:
    def __init__(self):
        self.router = Router()
        
        self.router.message.register(self.start, Command("start"))
        self.router.message.register(self.help, Command("help"))
        self.router.message.register(self.cancel, Command("cancel"))
    
    async def start(self, message: Message, state: FSMContext):
        """Команда /start"""
        await state.clear()
        await message.answer(
            "🚴‍♂️ Добро пожаловать в BikeShop!\n\n"
            "Выберите действие:",
            reply_markup=get_main_menu_keyboard()
        )
    
    async def help(self, message: Message):
        """Команда /help"""
        await message.answer(
            "🤖 **Помощь по боту**\n\n"
            "🚴 /catalog - Просмотр каталога\n"
            "📞 /support - Связь с поддержкой\n"
            "🛒 Корзина - Просмотр корзины\n"
            "📋 Мои заказы - История заказов\n\n"
            "Для консультации используйте кнопку 'Поддержка'",
            parse_mode="Markdown"
        )
    
    async def cancel(self, message: Message, state: FSMContext):
        """Отмена текущего действия"""
        await state.clear()
        await message.answer(
            "❌ Действие отменено",
            reply_markup=get_main_menu_keyboard()
        )