from aiogram.fsm.state import State, StatesGroup


class CheckoutStates(StatesGroup):
    """Состояния FSM для оформления заказа."""
    waiting_address = State()    # ожидание ввода адреса доставки
    waiting_payment = State()    # ожидание подтверждения оплаты
    confirmation = State()       # финальное подтверждение заказа
