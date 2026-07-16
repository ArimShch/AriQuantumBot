from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fluentogram import TranslatorRunner


def builder_simulation_result(
    circuit_id: int,
    i18n: TranslatorRunner
) -> InlineKeyboardMarkup:
    """Клавиатура для результата симуляции"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text=i18n.simulation_back_to_circuit_button(),
        callback_data=f"simulation:back:{circuit_id}"
    )
    builder.button(
        text=i18n.menu_button(),
        callback_data="answer_menu"
    )
    
    builder.adjust(1)
    return builder.as_markup()