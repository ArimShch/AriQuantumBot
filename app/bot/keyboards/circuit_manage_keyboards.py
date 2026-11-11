from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from fluentogram import TranslatorRunner
import math


# Клавиатура для раздела "Мои схемы"
def builder_circuits_keyboard(i18n: TranslatorRunner, 
                              circuits):
    builder = InlineKeyboardBuilder()

    for i, circuit in enumerate(circuits, 1):
        builder.button(
            text=f'{i}. {circuit.circuit_name}', 
            callback_data=f'circuits:{circuit.id}'
        )

    builder.button(
        text=i18n.menu_button(), 
        callback_data='menu', 
    )

    builder.adjust(1)

    return builder.as_markup()


# Клавиатура для раздела управленияя каждой схемой
def builder_circuit_manage(
        i18n: TranslatorRunner, 
        circuit_id: int, 
):
    builder = InlineKeyboardBuilder()

    builder.button(
        text=i18n.circuit_apply_gate_button(), 
        callback_data=f'circuits:{circuit_id}:gate', 
    )
    # print(f'circuits:{circuit_id}:gate')
    builder.button(
        text=i18n.circuit_edit_button(), 
        callback_data=f'circuits:{circuit_id}:edit', 
    )
    builder.button(
        text=i18n.circuit_simulate_button(), 
        callback_data=f'circuits:{circuit_id}:simulate'
    )
    builder.button(
        text=i18n.back_button(), 
        callback_data=f'back:circuits'
    )
    builder.button(
        text=i18n.menu_button(), 
        callback_data=f'menu'
    )

    builder.adjust(1, 1, 1, 2)

    return builder.as_markup()


# # Клавиатура дла раздела применения гейта. Меняется в зависимости от колчисетва кубитов
# def builder_circuit_apply_gates(
#         num_qubits: int,
#         circuit_id: int,
#         i18n: TranslatorRunner,
# ):
#     builder = InlineKeyboardBuilder()

#     lst_gates = [
#         'I', 'X', 'Y', 'Z', 'H', 'S', 'T', 'P', 'Rx', 'Ry', 'Rz', 
#         'CX', 'CY', 'CZ', 'CH', 'CS', 'CP', 'CRx', 'CRy', 'CRz', 
#         'CCX', 'CCZ',   
#     ]

#     if num_qubits == 1:
#         for i in range(11):
#             builder.button(
#                 text=lst_gates[i], 
#                 callback_data=f'circuits:{circuit_id}:gate:{lst_gates[i]}',
#             )
#     elif num_qubits == 2:
#         for i in range(20):
#             builder.button(
#                 text=lst_gates[i], 
#                 callback_data=f'circuits:{circuit_id}:gate:{lst_gates[i]}',
#             )
#     else:
#         for gate in lst_gates:
#             builder.button(
#                 text=gate, 
#                 callback_data=f'circuits:{circuit_id}:gate:{gate}',
#             )
    
#     builder.button(
#         text=i18n.back_button(),
#         callback_data=f'back:circuit:{circuit_id}'
#     )
#     builder.button(
#         text=i18n.menu_button(), 
#         callback_data=f'menu'
#     )

#     if num_qubits == 1:
#         builder.adjust(6, 5, 2) # 11
#     elif num_qubits == 2:
#         builder.adjust(5, 5, 5, 5, 2) # 20
#     else:
#         builder.adjust(6, 5, 6, 5, 2) # 22

#     return builder.as_markup()


# # Клавиатура для выбора угла поворота 
# def builder_apply_gate_select_angle(
#     circuit_id: int, 
#     gate_name: str, 
#     i18n: TranslatorRunner, 
# ):
#     builder = InlineKeyboardBuilder()

#     angles = ['0', 'π/6', 'π/4', 'π/3', 'π/2', '2π/3', 
#               '3π/4', '5π/6', 'π', '7π/6', '3π/2', '2π']
    
#     for angle in angles: 
#         builder.button(
#             text=angle, 
#             callback_data=f'circuits:{circuit_id}:gate:{gate_name}:{angle}', 
#         )
#     builder.adjust(6, 6)
    
#     button_back = InlineKeyboardButton(
#         text=i18n.back_button(), 
#         callback_data=f'back:circuit_gates:{circuit_id}'
#     )
#     button_menu = InlineKeyboardButton(
#         text=i18n.menu_button(), 
#         callback_data='menu', 
#     )
#     builder.row(button_back, button_menu)

#     return builder.as_markup()



# # Клавиатура для выбора целевого кубита
# def builder_apply_gate_target_qubit(
#     num_qubits: int,
#     controls: list,  
#     circuit_id: int, 
#     gate_name: str, 
#     i18n: TranslatorRunner, 
# ): 
#     builder = InlineKeyboardBuilder()

#     for i in range(num_qubits):
#         if i in controls:
#             builder.button(
#                 text=f'⚫️ {i}', 
#                 callback_data=f'control_qubit', 
#             )
#         else:
#             builder.button(
#                 text=f'{i}', 
#                 callback_data=f'circuits:{circuit_id}:gate:{gate_name}:{i}', 
#             )
    
#     if num_qubits <= 6:
#         builder.adjust(6)
#     else:
#         builder.adjust(4)

#     button_reset = InlineKeyboardButton(
#         text=i18n.reset_qubit_selection(), 
#         callback_data=f'circuits:{circuit_id}:gate:{gate_name}:reset', 
#     )
#     button_back = InlineKeyboardButton(
#         text=i18n.back_button(), 
#         callback_data=f'back:circuit_gates:{circuit_id}'
#     )
#     button_menu = InlineKeyboardButton(
#         text=i18n.menu_button(), 
#         callback_data='menu', 
#     )

#     builder.row(button_reset)
#     builder.row(button_back, button_menu)

#     return builder.as_markup()


# ====================================================================
# Клавиатура выбора гейта (зависит от кол-ва кубитов)
# ====================================================================
def builder_circuit_apply_gates(
    num_qubits: int,
    circuit_id: int,
    i18n: TranslatorRunner,
) -> InlineKeyboardMarkup:
    """Показывает доступные гейты в зависимости от кол-ва кубитов"""
    builder = InlineKeyboardBuilder()

    lst_gates = [
        'I', 'X', 'Y', 'Z', 'H', 'S', 'T', 'P', 'Rx', 'Ry', 'Rz', 
        'CX', 'CY', 'CZ', 'CH', 'CS', 'CP', 'CRx', 'CRy', 'CRz', 
        'CCX', 'CCZ',   
    ]

    if num_qubits == 1:
        for i in range(11):  # Только однокубитные
            builder.button(
                text=lst_gates[i], 
                callback_data=f'circuits:{circuit_id}:gate:{lst_gates[i]}',
            )
    elif num_qubits == 2:
        for i in range(20):  # Одно- и двухкубитные
            builder.button(
                text=lst_gates[i], 
                callback_data=f'circuits:{circuit_id}:gate:{lst_gates[i]}',
            )
    else:
        for gate in lst_gates:  # Все гейты
            builder.button(
                text=gate, 
                callback_data=f'circuits:{circuit_id}:gate:{gate}',
            )
    builder.button(
        text=i18n.gate_measure_btn(), 
        callback_data=f'circuits:{circuit_id}:gate:M'
    )
    
    builder.button(
        text=i18n.back_button(),
        callback_data=f'back:circuit:{circuit_id}'
    )
    builder.button(
        text=i18n.menu_button(), 
        callback_data=f'menu'
    )

    # Настройка сетки кнопок
    if num_qubits == 1:
        builder.adjust(6, 5, 1, 2)  # 12 гейтов + 2 кнопки
    elif num_qubits == 2:
        builder.adjust(6, 5, 5, 4, 1, 2)  # 21 гейтов + 2 кнопки
    else:
        builder.adjust(6, 6, 5, 5, 1, 2)  # 23 гейта + 2 кнопки

    return builder.as_markup()


# ====================================================================
# Клавиатура выбора угла поворота
# ====================================================================
def builder_apply_gate_select_angle(
    circuit_id: int, 
    gate_name: str, 
    i18n: TranslatorRunner,
) -> InlineKeyboardMarkup:
    """Показывает доступные углы для параметрических гейтов"""
    builder = InlineKeyboardBuilder()

    angles = ['0', 'π/6', 'π/4', 'π/3', 'π/2', '2π/3', 
              '3π/4', '5π/6', 'π', '7π/6', '3π/2', '2π']
    
    for angle in angles: 
        builder.button(
            text=angle, 
            callback_data=f'circuits:{circuit_id}:gate:{gate_name}:{angle}', 
        )
    builder.adjust(6, 6)
    
    button_back = InlineKeyboardButton(
        text=i18n.back_button(), 
        callback_data=f'back:circuit_gates:{circuit_id}'
    )
    button_menu = InlineKeyboardButton(
        text=i18n.menu_button(), 
        callback_data='menu', 
    )
    builder.row(button_back, button_menu)

    return builder.as_markup()


# ====================================================================
# Клавиатура выбора первого контролирующего кубита
# ====================================================================
def builder_apply_gate_first_control(
    num_qubits: int,
    controls: list,
    circuit_id: int, 
    gate_name: str, 
    i18n: TranslatorRunner,
) -> InlineKeyboardMarkup:
    """Показывает выбор первого контролирующего кубита"""
    builder = InlineKeyboardBuilder()

    for i in range(num_qubits):
        builder.button(
            text=f'{i}', 
            callback_data=f'circuits:{circuit_id}:gate:{gate_name}:{i}', 
        )
    
    if num_qubits <= 6:
        builder.adjust(6)
    else:
        builder.adjust(5)

    button_reset = InlineKeyboardButton(
        text=i18n.reset_qubit_selection(), 
        callback_data=f'circuits:{circuit_id}:gate:{gate_name}:reset', 
    )
    button_back = InlineKeyboardButton(
        text=i18n.back_button(), 
        callback_data=f'back:circuit_gates:{circuit_id}'
    )
    button_menu = InlineKeyboardButton(
        text=i18n.menu_button(), 
        callback_data='menu', 
    )

    builder.row(button_reset)
    builder.row(button_back, button_menu)

    return builder.as_markup()


# ====================================================================
# Клавиатура выбора второго контролирующего кубита
# ====================================================================
def builder_apply_gate_second_control(
    num_qubits: int,
    first_control: int,
    circuit_id: int, 
    gate_name: str, 
    i18n: TranslatorRunner,
) -> InlineKeyboardMarkup:
    """Показывает выбор второго контролирующего кубита (первый уже выбран)"""
    builder = InlineKeyboardBuilder()

    for i in range(num_qubits):
        if i == first_control:
            builder.button(
                text=f'⚪️ {i}', 
                callback_data='control_qubit_already_selected', 
            )
        else:
            builder.button(
                text=f'{i}', 
                callback_data=f'circuits:{circuit_id}:gate:{gate_name}:{first_control}:{i}', 
            )
    
    if num_qubits <= 6:
        builder.adjust(6)
    else:
        builder.adjust(5)

    button_reset = InlineKeyboardButton(
        text=i18n.reset_qubit_selection(), 
        callback_data=f'circuits:{circuit_id}:gate:{gate_name}:reset', 
    )
    button_back = InlineKeyboardButton(
        text=i18n.back_button(), 
        callback_data=f'back:circuit_gates:{circuit_id}'
    )
    button_menu = InlineKeyboardButton(
        text=i18n.menu_button(), 
        callback_data='menu', 
    )

    builder.row(button_reset)
    builder.row(button_back, button_menu)

    return builder.as_markup()


# ====================================================================
# Клавиатура выбора целевого кубита
# ====================================================================
def builder_apply_gate_target_qubit(
    num_qubits: int,
    controls: list,  
    circuit_id: int, 
    gate_name: str, 
    i18n: TranslatorRunner,
) -> InlineKeyboardMarkup:
    """Показывает выбор целевого кубита (контроли уже выбраны)"""
    builder = InlineKeyboardBuilder()

    for i in range(num_qubits):
        if i in controls:
            builder.button(
                text=f'⚪️ {i}', 
                callback_data='control_qubit_already_selected', 
            )
        else:
            builder.button(
                text=f'{i}', 
                callback_data=f'circuits:{circuit_id}:gate:{gate_name}:{i}', 
            )
    
    if num_qubits <= 6:
        builder.adjust(6)
    else:
        builder.adjust(5)

    button_reset = InlineKeyboardButton(
        text=i18n.reset_qubit_selection(), 
        callback_data=f'circuits:{circuit_id}:gate:{gate_name}:reset', 
    )
    button_back = InlineKeyboardButton(
        text=i18n.back_button(), 
        callback_data=f'back:circuit_gates:{circuit_id}'
    )
    button_menu = InlineKeyboardButton(
        text=i18n.menu_button(), 
        callback_data='menu', 
    )

    builder.row(button_reset)
    builder.row(button_back, button_menu)

    return builder.as_markup()


# Клавиатура если был выбран измерительный прибор
def builder_apply_gate_target_qubit_measurement(
    num_qubits: int,
    circuit_id: int,
    i18n: TranslatorRunner,
) -> InlineKeyboardMarkup:
    """Показывает выбор кубитов для измерения (с опцией 'Все кубиты')"""
    builder = InlineKeyboardBuilder()

    # Кнопка "Все кубиты"
    builder.button(
        text=i18n.measure_all_qubits_button(),
        callback_data=f'circuits:{circuit_id}:gate:M:all',
    )

    # Кнопки для отдельных кубитов
    for i in range(num_qubits):
        builder.button(
            text=f'{i}', 
            callback_data=f'circuits:{circuit_id}:gate:M:{i}', 
        )
    
    if num_qubits <= 6:
        builder.adjust(1, 6)
    else:
        builder.adjust(1, 5)

    button_reset = InlineKeyboardButton(
        text=i18n.reset_qubit_selection(), 
        callback_data=f'circuits:{circuit_id}:gate:M:reset', 
    )
    button_back = InlineKeyboardButton(
        text=i18n.back_button(), 
        callback_data=f'back:circuit_gates:{circuit_id}'
    )
    button_menu = InlineKeyboardButton(
        text=i18n.menu_button(), 
        callback_data='menu', 
    )

    builder.row(button_reset)
    builder.row(button_back, button_menu)

    return builder.as_markup()


# Клавиатура для раздела управления схемой
def builder_circuit_edit_menu(
    circuit_id: int,
    i18n: TranslatorRunner,
) -> InlineKeyboardMarkup:
    """Меню управления схемой"""
    builder = InlineKeyboardBuilder()

    builder.button(
        text=i18n.circuit_edit_delete_gate_button(),
        callback_data=f'circuits:{circuit_id}:edit:delete_gate'
    )
    builder.button(
        text=i18n.circuit_edit_delete_button(),
        callback_data=f'circuits:{circuit_id}:edit:delete'
    )
    builder.button(
        text=i18n.circuit_edit_clear_button(),
        callback_data=f'circuits:{circuit_id}:edit:clear'
    )
    builder.button(
        text=i18n.circuit_edit_rename_button(),
        callback_data=f'circuits:{circuit_id}:edit:rename'
    )
    builder.button(
        text=i18n.circuit_edit_export_button(),
        callback_data=f'circuits:{circuit_id}:edit:export'
    )
    builder.button(
        text=i18n.back_button(),
        callback_data=f'back:circuit_edit:{circuit_id}'
    )
    builder.button(
        text=i18n.menu_button(),
        callback_data='menu'
    )

    builder.adjust(2, 2, 1, 2)
    return builder.as_markup()



# Клавиатура, отвечающая за отрисовку клавиатуры для удаления гейта
def builder_delete_gate_keyboard(
    circuit_id: int, 
    total_gates: int, 
    current_page: int, 
    i18n,
    has_measurements: bool = False,
    per_page: int = 10
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    total_pages = math.ceil(total_gates / per_page) if total_gates > 0 else 1
    
    # Защита от выхода за пределы страниц
    if current_page > total_pages:
        current_page = total_pages
    if current_page < 1:
        current_page = 1
        
    start_idx = (current_page - 1) * per_page
    end_idx = min(start_idx + per_page, total_gates)
    
    # 1. Кнопки с номерами гейтов
    for i in range(start_idx, end_idx):
        builder.add(InlineKeyboardButton(
            text=str(i + 1), 
            callback_data=f"circuits:{circuit_id}:edit:delete_gate:confirm:{i}"
        ))
    builder.adjust(5) # Делает сетку: максимум 6 кнопок в ряд (получится 2 ряда по 6)
    
    # НОВАЯ КНОПКА: Удалить все измерения (только если они есть)
    if has_measurements:
        builder.row(
            InlineKeyboardButton(
                text=i18n.delete_all_measurements_button(),
                callback_data=f"circuits:{circuit_id}:edit:delete_gate:all_measurements"
            )
        )

    # 2. Пагинация (только если страниц больше 1)
    if total_pages > 1:
        prev_cb = f"circuits:{circuit_id}:edit:delete_gate:page:{current_page - 1}" if current_page > 1 else "ignore_prev"
        next_cb = f"circuits:{circuit_id}:edit:delete_gate:page:{current_page + 1}" if current_page < total_pages else "ignore_next"
        
        builder.row(
            InlineKeyboardButton(text="◀️", callback_data=prev_cb),
            InlineKeyboardButton(text=f"{current_page}/{total_pages}", callback_data="ignore"),
            InlineKeyboardButton(text="▶️", callback_data=next_cb)
        )
        
    # 3. Кнопки Назад и Меню
    builder.row(
        InlineKeyboardButton(text=i18n.back_button(), callback_data=f"circuits:{circuit_id}:edit"),
        InlineKeyboardButton(text=i18n.menu_button(), callback_data="menu")
    )
    
    return builder.as_markup()


# Клавиатура для вариантов экспорта
def builder_export_format_keyboard(circuit_id: int, i18n) -> InlineKeyboardMarkup:
    """Клавиатура выбора формата экспорта"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="OpenQASM 2.0",
        callback_data=f"circuits:{circuit_id}:edit:export:qasm2"
    )
    builder.button(
        text="OpenQASM 3.0",
        callback_data=f"circuits:{circuit_id}:edit:export:qasm3"
    )
    builder.button(
        text="AriQuantum",
        callback_data=f"circuits:{circuit_id}:edit:export:ariquantum"
    )
    builder.button(
        text="Qiskit",
        callback_data=f"circuits:{circuit_id}:edit:export:qiskit"
    )
    
    builder.button(
        text=i18n.back_button(),
        callback_data=f"circuits:{circuit_id}:edit"
    )
    builder.button(
        text=i18n.menu_button(),
        callback_data="menu"
    )
    
    builder.adjust(2)
    return builder.as_markup()

# Клавиатура, которая будет отправляться вместе с файлом экспорта
def builder_export_result_keyboard(
        circuit_id: int, i18n,
) -> InlineKeyboardMarkup:
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