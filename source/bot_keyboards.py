from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_now_8_5_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="Сейчас")
    kb.button(text="08:00")
    kb.button(text="17:00")
    kb.adjust(3)
    return kb.as_markup(resize_keyboard=True)