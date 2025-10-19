from aiogram.fsm.state import State, StatesGroup

class SupportStates(StatesGroup):
    waiting_for_support_message = State()
    waiting_for_support_reply = State()
    waiting_for_ticket_action = State()

class CatalogStates(StatesGroup):
    browsing_categories = State()
    viewing_product = State()
    in_cart = State()

class OrderStates(StatesGroup):
    waiting_for_address = State()
    waiting_for_phone = State()
    confirming_order = State()