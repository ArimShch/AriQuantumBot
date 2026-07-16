from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from fluentogram import TranslatorRunner


# Клавиатура для выбора кол-ва кубитов в схеме
def builder_num_qubits_keyboard(max_qubits: int):
    builder = InlineKeyboardBuilder()

    for i in range(1, max_qubits + 1):
        builder.button(
            text=f'{i}', 
            callback_data=f'create:num_qubits:{i}'
        )
    
    if max_qubits <= 8:
        builder.adjust(4)
    else:
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