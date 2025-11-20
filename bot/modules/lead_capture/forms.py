from aiogram.fsm.state import State, StatesGroup
class LeadForm(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_email = State()
