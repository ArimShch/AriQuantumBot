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


def builder_simulation_select_backend(
    circuit_id: int,
    backends: list,
    i18n: TranslatorRunner
) -> InlineKeyboardMarkup:
    """Клавиатура динамического выбора бэкенда"""
    builder = InlineKeyboardBuilder()
    
    for backend in backends:
        builder.button(
            text=f"{backend.name}",
            callback_data=f"simulate:{circuit_id}:backend:{backend.id}"
        )
        
    builder.button(
        text=i18n.simulation_back_to_circuit_button(),
        callback_data=f"circuits:{circuit_id}"
    )
    
    builder.adjust(1)
    return builder.as_markup()


def builder_simulation_select_shots(
    circuit_id: int,
    backend_id: int,
    i18n: TranslatorRunner
) -> InlineKeyboardMarkup:
    """Клавиатура динамического выбора количества запусков"""
    builder = InlineKeyboardBuilder()
    shots_values = [1, 10, 50, 100, 200, 300, 500, 600, 800, 1000]
    
    for shots in shots_values:
        builder.button(
            text=str(shots),
            callback_data=f"simulate:{circuit_id}:backend:{backend_id}:shots:{shots}"
        )
    
    builder.button(
        text=i18n.simulation_back_to_circuit_button(),
        callback_data=f"circuits:{circuit_id}"
    )
    
    builder.adjust(5, 5, 1)
    return builder.as_markup()