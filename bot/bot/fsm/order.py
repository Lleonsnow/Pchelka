from aiogram.fsm.state import State, StatesGroup


class OrderFSM(StatesGroup):
    fio = State()
    address = State()
    confirm = State()
