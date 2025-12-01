from aiogram.fsm.state import State, StatesGroup

class BotStates(StatesGroup):
    in_support = State()      # пользователь в поддержке
    lead_name   = State()     # ждём имя
    lead_phone  = State()     # ждём телефон
    lead_email  = State()     # ждём email
