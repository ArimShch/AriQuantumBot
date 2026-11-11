from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from fluentogram import TranslatorRunner


# Клавиатура для выбора кол-ва кубитов в схеме (универсальный лимит 10)
def builder_num_qubits_keyboard(max_qubits: int = 10):
    builder = InlineKeyboardBuilder()

    for i in range(1, max_qubits + 1):
        builder.button(
            text=f'{i}', 
            callback_data=f'create:num_qubits:{i}'
        )
    
    # По 5 кнопок в ряд для 10 кубитов
    builder.adjust(5)

    return builder.as_markup()


# Клавиатура для возврата в раздел "Мои схемы"
def builder_my_circuits_keyboard(i18n: TranslatorRunner):
    builder = InlineKeyboardBuilder()

    builder.button(
        text=i18n.menu_circuit_button(), 
        callback_data='circuits', 
    )
    builder.button(
        text=i18n.menu_button(), 
        callback_data='menu', 
    )

    builder.adjust(1)

    return builder.as_markup()