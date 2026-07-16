from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from fluentogram import TranslatorRunner


def profile_menu_keyboard(i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    """Клавиатура для раздела профиля"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=i18n.menu_circuit_button(), 
        callback_data='circuits', 
    )
    builder.button(
        text=i18n.menu_button(),
        callback_data="menu"
    )

    builder.adjust(1, 1)
    
    return builder.as_markup()