from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from states.support_states import CatalogStates
from keyboards import get_catalog_keyboard, get_main_menu_keyboard
import logging

logger = logging.getLogger(__name__)

class CatalogHandlers:
    def __init__(self):
        self.router = Router()
        
        self.router.message.register(self.show_catalog, Command("catalog"))
        self.router.callback_query.register(self.handle_category_selection, F.data.startswith("cat_"))
        self.router.callback_query.register(self.handle_main_menu, F.data == "main_menu")
    
    async def show_catalog(self, message: Message, state: FSMContext):
        """Показ каталога"""
        await message.answer(
            "🚴‍♂️ **Каталог велосипедов**\n\n"
            "Выберите категорию:",
            reply_markup=get_catalog_keyboard(),
            parse_mode="Markdown"
        )
        await state.set_state(CatalogStates.browsing_categories)
    
    async def handle_category_selection(self, callback: CallbackQuery, state: FSMContext):
        """Обработка выбора категории"""
        category = callback.data.replace("cat_", "")
        
        category_names = {
            "mountain": "🏔️ Горные велосипеды",
            "road": "🏁 Шоссейные велосипеды", 
            "city": "🏙️ Городские велосипеды",
            "folding": "📦 Складные велосипеды",
            "hybrid": "🚴 Гибридные велосипеды",
            "accessories": "🎯 Аксессуары"
        }
        
        category_name = category_names.get(category, "Категория")
        
        await callback.message.edit_text(
            f"{category_name}\n\n"
            f"Здесь будут товары из категории {category_name}...",
            reply_markup=get_catalog_keyboard()
        )
        await callback.answer()
    
    async def handle_main_menu(self, callback: CallbackQuery, state: FSMContext):
        """Возврат в главное меню"""
        await callback.message.edit_text(
            "🏠 Главное меню",
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()
        await callback.answer()