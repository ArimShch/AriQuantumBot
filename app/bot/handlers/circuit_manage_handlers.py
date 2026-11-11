import logging
from fluentogram import TranslatorRunner
import math

from aiogram import Bot, Router, F
from aiogram.types import CallbackQuery, InputRichMessage, Message, BufferedInputFile
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State

from sqlalchemy.ext.asyncio import AsyncSession

from ..utils.draw_circuit import draw_history
from ..utils.circuit_view import render_circuit_details
from ..utils.circuit_screen import present, edit_screen
from ..utils.check_measured import validate_gate_on_measured_qubits
from ..utils.delete_gate_table import generate_gates_table_html 
from ..utils.exporters import (
    export_to_ariquantum, 
    export_to_qasm2,
    export_to_qasm3,
    export_to_qiskit,
)
from ..utils.en_to_ru import slugify_filename
from ..filters.is_owner_circuit import IsCircuitOwner
from ..states.states import States
from ...infrastructure.database.models.models import UserSetting, QuantumCircuit, User
from ...infrastructure.database.repositories import user_repository, circuit_repository
from ..keyboards.circuit_manage_keyboards import (
    builder_circuits_keyboard, 
    builder_circuit_manage, 
    builder_circuit_apply_gates,
    builder_apply_gate_target_qubit, 
    builder_apply_gate_select_angle, 
    builder_apply_gate_first_control,  
    builder_apply_gate_second_control, 
    builder_circuit_edit_menu, 
    builder_apply_gate_target_qubit_measurement, 
    builder_delete_gate_keyboard,
    builder_export_format_keyboard,
    builder_export_result_keyboard,
)


circuit_manage_router = Router()

# Хэндлер, отвечающий за кнопку "Мои Схемы"
@circuit_manage_router.callback_query(
    F.data == 'circuits'
)
async def menu_circuits_button_func(
    callback: CallbackQuery, 
    state: FSMContext, 
    session: AsyncSession, 
    i18n: TranslatorRunner, 
):
    
    user_circuits = await user_repository.get_user_circuits(
        session=session, 
        tg_id=callback.from_user.id, 
    )

    if user_circuits == []:
        text = i18n.my_circuits(have_circuits='False')
    else:
        text = i18n.my_circuits(have_circuits='True')

    await callback.message.edit_text(
        text=text, 
        reply_markup=builder_circuits_keyboard(
            i18n=i18n, 
            circuits=user_circuits, 
        )
    )


# Хэндлер, отвечающий за кнопку каждой схемы
@circuit_manage_router.callback_query(
    F.data.regexp(r"^circuits:\d+$"),
    IsCircuitOwner(), 
)
async def menu_circuit_id_button_func(
    callback: CallbackQuery, 
    state: FSMContext, 
    session: AsyncSession, 
    i18n: TranslatorRunner, 
    circuit_id: int, 
):
    circuit = await circuit_repository.get_circuit(
        session=session, 
        tg_id=callback.from_user.id,
        circuit_id=circuit_id,
    )
    # print(circuit.circuit_history)

    text = await render_circuit_details(session, i18n, circuit)

    await present(
        callback, session=session, i18n=i18n, circuit=circuit,
        html=text, reply_markup=builder_circuit_manage(i18n, circuit_id), circuit_changed=True,
    )

    await state.set_state(
        States.circuit_manage
    )

@circuit_manage_router.callback_query(
        F.data.regexp(r'^circuits:\d+$'),
)
async def menu_circuit_func(
    callback: CallbackQuery, 
):
    await callback.answer()


# ШАГ 1: Нажатие на кнопку "Применить гейт"
@circuit_manage_router.callback_query(
    F.data.regexp(r"^circuits:\d+:gate$"),
    StateFilter(States.circuit_manage),
    IsCircuitOwner(),
)
async def circuit_apply_gate_button_func(
    callback: CallbackQuery,
    state: FSMContext, 
    session: AsyncSession, 
    i18n: TranslatorRunner,
    circuit_id: int, 
):
    """Показывает список доступных гейтов для схемы"""
    circuit = await circuit_repository.get_circuit(
        session=session, 
        tg_id=callback.from_user.id,
        circuit_id=circuit_id,
    )
    
    # Очищаем данные состояния перед новым выбором
    await state.clear()
    await state.update_data(circuit_id=circuit_id)
    
    text = i18n.apply_gate_prompt(
        circuit_name=circuit.circuit_name, 
        circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
    )

    await edit_screen(
        callback,
        # text=text, 
        reply_markup=builder_circuit_apply_gates(
            num_qubits=circuit.num_qubits, 
            circuit_id=circuit.id, 
            i18n=i18n,
        ), 
        rich_message=InputRichMessage(html=text), 
    )
    await state.set_state(States.circuit_manage)


# ШАГ 2: Выбор однокубитного гейта (без параметров)
@circuit_manage_router.callback_query(
    F.data.regexp(r'^circuits:\d+:gate:(I|X|Y|Z|H|S|T|M)$'), 
    StateFilter(States.circuit_manage), 
    IsCircuitOwner(), 
)
async def input_single_qubit_gate(
    callback: CallbackQuery, 
    state: FSMContext, 
    session: AsyncSession, 
    i18n: TranslatorRunner, 
    circuit_id: int, 
):
    """Обработка выбора однокубитного гейта без параметров"""
    gate_name = callback.data.split(':')[3]

    circuit = await circuit_repository.get_circuit(
        session=session, 
        tg_id=callback.from_user.id,
        circuit_id=circuit_id,
    )

    await state.update_data(
        gate_name=gate_name,
        controls=[],
    )

    # Специальная обработка для измерения
    if gate_name == 'M':
        text = i18n.apply_gate_select_target_qubit_measurement(
            circuit_name=circuit.circuit_name, 
            circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
        )
        reply_markup = builder_apply_gate_target_qubit_measurement(
            num_qubits=circuit.num_qubits,
            circuit_id=circuit_id,
            i18n=i18n,
        )
    else:
        text = i18n.apply_gate_select_target_qubit(
            circuit_name=circuit.circuit_name, 
            circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
            gate_name=gate_name, 
        )
        reply_markup = builder_apply_gate_target_qubit(
            num_qubits=circuit.num_qubits, 
            controls=[], 
            circuit_id=circuit_id, 
            gate_name=gate_name, 
            i18n=i18n, 
        )

    await edit_screen(
        callback,
        text=text,
        reply_markup=reply_markup, 
        rich_message=InputRichMessage(html=text)
    )
    await state.set_state(States.input_target_qubit)
    await callback.answer()


# ШАГ 3: Выбор параметрического гейта (с углом)
@circuit_manage_router.callback_query(
    F.data.regexp(r'^circuits:\d+:gate:(P|Rx|Ry|Rz)$'), 
    StateFilter(States.circuit_manage), 
    IsCircuitOwner(), 
)
async def input_parametric_gate_select_angle(
    callback: CallbackQuery, 
    state: FSMContext, 
    session: AsyncSession, 
    i18n: TranslatorRunner, 
    circuit_id: int, 
):
    """Обработка выбора параметрического гейта - показ выбора угла"""
    gate_name = callback.data.split(':')[3]

    circuit = await circuit_repository.get_circuit(
        session=session, 
        tg_id=callback.from_user.id,
        circuit_id=circuit_id,
    )

    await state.update_data(
        gate_name=gate_name,
        controls=[],
    )

    await edit_screen(
        callback,
        # text=i18n.apply_gate_select_angle(
        #     circuit_name=circuit.circuit_name, 
        #     circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
        #     gate_name=gate_name, 
        # ), 
        reply_markup=builder_apply_gate_select_angle(
            circuit_id=circuit.id, 
            gate_name=gate_name, 
            i18n=i18n, 
        ), 
        rich_message=InputRichMessage(html=i18n.apply_gate_select_angle(
            circuit_name=circuit.circuit_name, 
            circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
            gate_name=gate_name, 
        )),
    )
    await state.set_state(States.input_theta_qubit)
    await callback.answer()


# ШАГ 4: Выбор угла для параметрического гейта
@circuit_manage_router.callback_query(
    F.data.regexp(r'^circuits:\d+:gate:(P|Rx|Ry|Rz):[^:]+$'), 
    StateFilter(States.input_theta_qubit), 
    IsCircuitOwner(), 
)
async def input_parametric_gate_angle_selected(
    callback: CallbackQuery, 
    state: FSMContext, 
    session: AsyncSession, 
    i18n: TranslatorRunner, 
    circuit_id: int, 
):
    """Обработка выбора угла - переход к выбору целевого кубита"""
    gate_name, angle = callback.data.split(':')[3:5]

    circuit = await circuit_repository.get_circuit(
        session=session, 
        tg_id=callback.from_user.id,
        circuit_id=circuit_id,
    )

    await state.update_data(
        angle=angle,
        gate_name=f'{gate_name}({angle})',
    )

    await edit_screen(
        callback,
        # text=i18n.apply_gate_select_target_qubit(
        #     circuit_name=circuit.circuit_name, 
        #     circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
        #     gate_name=f'{gate_name}({angle})', 
        # ), 
        reply_markup=builder_apply_gate_target_qubit(
            num_qubits=circuit.num_qubits, 
            controls=[], 
            circuit_id=circuit_id, 
            gate_name=gate_name, 
            i18n=i18n, 
        ), 
        rich_message=InputRichMessage(html=i18n.apply_gate_select_target_qubit(
            circuit_name=circuit.circuit_name, 
            circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
            gate_name=f'{gate_name}({angle})', 
        )),
    )
    await state.set_state(States.input_target_qubit)
    await callback.answer()


# ШАГ 5: Выбор двухкубитного гейта (1 контроль + 1 цель)
@circuit_manage_router.callback_query(
    F.data.regexp(r'^circuits:\d+:gate:(CX|CY|CZ|CH|CS)$'), 
    StateFilter(States.circuit_manage), 
    IsCircuitOwner(), 
)
async def input_two_qubit_gate_select_first_control(
    callback: CallbackQuery, 
    state: FSMContext, 
    session: AsyncSession, 
    i18n: TranslatorRunner, 
    circuit_id: int, 
):
    """Обработка выбора двухкубитного гейта БЕЗ параметров - показ выбора контролирующего кубита"""
    gate_name = callback.data.split(':')[3]

    circuit = await circuit_repository.get_circuit(
        session=session, 
        tg_id=callback.from_user.id,
        circuit_id=circuit_id,
    )

    await state.update_data(
        gate_name=gate_name,
        controls=[],
    )

    await edit_screen(
        callback,
        # text=i18n.apply_gate_select_first_control(
        #     circuit_name=circuit.circuit_name, 
        #     circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
        #     gate_name=gate_name, 
        # ), 
        reply_markup=builder_apply_gate_first_control(
            num_qubits=circuit.num_qubits, 
            controls=[], 
            circuit_id=circuit_id, 
            gate_name=gate_name, 
            i18n=i18n, 
        ), 
        rich_message=InputRichMessage(html=i18n.apply_gate_select_first_control(
            circuit_name=circuit.circuit_name, 
            circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
            gate_name=gate_name, 
        )),
    )
    await state.set_state(States.input_first_control_qubit)
    await callback.answer()


# ШАГ 5b: Выбор параметрического двухкубитного гейта (с углом)
@circuit_manage_router.callback_query(
    F.data.regexp(r'^circuits:\d+:gate:(CP|CRx|CRy|CRz)$'), 
    StateFilter(States.circuit_manage), 
    IsCircuitOwner(), 
)
async def input_two_qubit_parametric_gate_select_angle(
    callback: CallbackQuery, 
    state: FSMContext, 
    session: AsyncSession, 
    i18n: TranslatorRunner, 
    circuit_id: int, 
):
    """Обработка выбора параметрического двухкубитного гейта - показ выбора угла"""
    gate_name = callback.data.split(':')[3]

    circuit = await circuit_repository.get_circuit(
        session=session, 
        tg_id=callback.from_user.id,
        circuit_id=circuit_id,
    )

    await state.update_data(
        gate_name=gate_name,
        controls=[],
    )

    await edit_screen(
        callback,
        # text=i18n.apply_gate_select_angle(
        #     circuit_name=circuit.circuit_name, 
        #     circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
        #     gate_name=gate_name, 
        # ), 
        reply_markup=builder_apply_gate_select_angle(
            circuit_id=circuit.id, 
            gate_name=gate_name, 
            i18n=i18n, 
        ), 
        rich_message=InputRichMessage(html=i18n.apply_gate_select_angle(
            circuit_name=circuit.circuit_name, 
            circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
            gate_name=gate_name, 
        ),)
    )
    await state.set_state(States.input_theta_qubit)
    await callback.answer()


# ШАГ 6: Выбор угла для параметрического ДВУХКУБИТНОГО гейта
@circuit_manage_router.callback_query(
    F.data.regexp(r'^circuits:\d+:gate:(CP|CRx|CRy|CRz):[^:]+$'), 
    StateFilter(States.input_theta_qubit), 
    IsCircuitOwner(), 
)
async def input_two_qubit_parametric_gate_angle_selected(
    callback: CallbackQuery, 
    state: FSMContext, 
    session: AsyncSession, 
    i18n: TranslatorRunner, 
    circuit_id: int, 
):
    """Обработка выбора угла для двухкубитного параметрического гейта - переход к выбору контролирующего кубита"""
    gate_name, angle = callback.data.split(':')[3:5]

    circuit = await circuit_repository.get_circuit(
        session=session, 
        tg_id=callback.from_user.id,
        circuit_id=circuit_id,
    )

    await state.update_data(
        angle=angle,
        gate_name=f'{gate_name}({angle})',
    )

    await edit_screen(
        callback,
        # text=i18n.apply_gate_select_first_control(
        #     circuit_name=circuit.circuit_name, 
        #     circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
        #     gate_name=f'{gate_name}({angle})', 
        # ), 
        reply_markup=builder_apply_gate_first_control(
            num_qubits=circuit.num_qubits, 
            controls=[], 
            circuit_id=circuit_id, 
            gate_name=gate_name, 
            i18n=i18n, 
        ), 
        rich_message=InputRichMessage(html=i18n.apply_gate_select_first_control(
            circuit_name=circuit.circuit_name, 
            circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
            gate_name=f'{gate_name}({angle})', 
        )),
    )
    await state.set_state(States.input_first_control_qubit)
    await callback.answer()


# ШАГ 6b: Выбор первого контролирующего кубита (для 2-кубитных)
@circuit_manage_router.callback_query(
    F.data.regexp(r'^circuits:\d+:gate:(CX|CY|CZ|CH|CS|CP|CRx|CRy|CRz):\d+$'), 
    StateFilter(States.input_first_control_qubit), 
    IsCircuitOwner(), 
)
async def input_two_qubit_gate_first_control_selected(
    callback: CallbackQuery, 
    state: FSMContext, 
    session: AsyncSession, 
    i18n: TranslatorRunner, 
    circuit_id: int, 
):
    """Обработка выбора контролирующего кубита для двухкубитного гейта"""
    parts = callback.data.split(':')
    gate_name = parts[3]
    control_qubit = int(parts[4])

    circuit = await circuit_repository.get_circuit(
        session=session, 
        tg_id=callback.from_user.id,
        circuit_id=circuit_id,
    )

    # Получаем данные из состояния (может быть угол)
    data = await state.get_data()
    gate_full_name = data.get('gate_name', gate_name)

    await state.update_data(
        controls=[control_qubit],
    )

    await edit_screen(
        callback,
        # text=i18n.apply_gate_select_target_qubit(
        #     circuit_name=circuit.circuit_name, 
        #     circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
        #     gate_name=gate_full_name, 
        # ), 
        reply_markup=builder_apply_gate_target_qubit(
            num_qubits=circuit.num_qubits, 
            controls=[control_qubit], 
            circuit_id=circuit_id, 
            gate_name=gate_name, 
            i18n=i18n, 
        ), 
        rich_message=InputRichMessage(html=i18n.apply_gate_select_target_qubit(
            circuit_name=circuit.circuit_name, 
            circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
            gate_name=gate_full_name, 
        )),
    )
    await state.set_state(States.input_target_qubit)
    await callback.answer()
    

# ШАГ 7: Выбор трёхкубитного гейта (2 контроля + 1 цель)
@circuit_manage_router.callback_query(
    F.data.regexp(r'^circuits:\d+:gate:(CCX|CCZ)$'), 
    StateFilter(States.circuit_manage), 
    IsCircuitOwner(), 
)
async def input_three_qubit_gate_select_first_control(
    callback: CallbackQuery, 
    state: FSMContext, 
    session: AsyncSession, 
    i18n: TranslatorRunner, 
    circuit_id: int, 
):
    """Обработка выбора трёхкубитного гейта - показ выбора первого контролирующего"""
    gate_name = callback.data.split(':')[3]

    circuit = await circuit_repository.get_circuit(
        session=session, 
        tg_id=callback.from_user.id,
        circuit_id=circuit_id,
    )

    await state.update_data(
        gate_name=gate_name,
        controls=[],
    )

    await edit_screen(
        callback,
        # text=i18n.apply_gate_select_first_control(
        #     circuit_name=circuit.circuit_name, 
        #     circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
        #     gate_name=gate_name, 
        # ), 
        reply_markup=builder_apply_gate_first_control(
            num_qubits=circuit.num_qubits, 
            controls=[], 
            circuit_id=circuit_id, 
            gate_name=gate_name, 
            i18n=i18n, 
        ), 
        rich_message=InputRichMessage(html=i18n.apply_gate_select_first_control(
            circuit_name=circuit.circuit_name, 
            circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
            gate_name=gate_name, 
        )),
    )
    await state.set_state(States.input_first_control_qubit)
    await callback.answer()


# ШАГ 8: Выбор первого контролирующего кубита (для 3-кубитных)
@circuit_manage_router.callback_query(
    F.data.regexp(r'^circuits:\d+:gate:(CCX|CCZ):\d+$'), 
    StateFilter(States.input_first_control_qubit), 
    IsCircuitOwner(), 
)
async def input_three_qubit_gate_first_control_selected(
    callback: CallbackQuery, 
    state: FSMContext, 
    session: AsyncSession, 
    i18n: TranslatorRunner, 
    circuit_id: int, 
):
    """Обработка выбора первого контролирующего кубита для 3-кубитного гейта"""
    gate_name, first_control = callback.data.split(':')[3:5]
    first_control = int(first_control)

    circuit = await circuit_repository.get_circuit(
        session=session, 
        tg_id=callback.from_user.id,
        circuit_id=circuit_id,
    )

    await state.update_data(
        controls=[first_control],
    )

    await edit_screen(
        callback,
        # text=i18n.apply_gate_select_second_control(
        #     circuit_name=circuit.circuit_name, 
        #     circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
        #     gate_name=gate_name, 
        # ), 
        reply_markup=builder_apply_gate_second_control(
            num_qubits=circuit.num_qubits, 
            first_control=first_control, 
            circuit_id=circuit_id, 
            gate_name=gate_name, 
            i18n=i18n, 
        ), 
        rich_message=InputRichMessage(html=i18n.apply_gate_select_second_control(
            circuit_name=circuit.circuit_name, 
            circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
            gate_name=gate_name, 
        )),
    )
    await state.set_state(States.input_second_control_qubit)
    await callback.answer()


# ШАГ 9: Выбор второго контролирующего кубита (для 3-кубитных)
@circuit_manage_router.callback_query(
    F.data.regexp(r'^circuits:\d+:gate:(CCX|CCZ):\d+:\d+$'), 
    StateFilter(States.input_second_control_qubit), 
    IsCircuitOwner(), 
)
async def input_three_qubit_gate_second_control_selected(
    callback: CallbackQuery, 
    state: FSMContext, 
    session: AsyncSession, 
    i18n: TranslatorRunner, 
    circuit_id: int, 
):
    """Обработка выбора второго контролирующего кубита"""
    gate_name, first_control, second_control = callback.data.split(':')[3:6]
    first_control = int(first_control)
    second_control = int(second_control)

    circuit = await circuit_repository.get_circuit(
        session=session, 
        tg_id=callback.from_user.id,
        circuit_id=circuit_id,
    )

    await state.update_data(
        controls=[first_control, second_control],
    )

    await edit_screen(
        callback,
        # text=i18n.apply_gate_select_target_qubit(
        #     circuit_name=circuit.circuit_name, 
        #     circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
        #     gate_name=gate_name, 
        # ), 
        reply_markup=builder_apply_gate_target_qubit(
            num_qubits=circuit.num_qubits, 
            controls=[first_control, second_control], 
            circuit_id=circuit_id, 
            gate_name=gate_name, 
            i18n=i18n, 
        ), 
        rich_message=InputRichMessage(html=i18n.apply_gate_select_target_qubit(
            circuit_name=circuit.circuit_name, 
            circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
            gate_name=gate_name, 
        )),
    )
    await state.set_state(States.input_target_qubit)
    await callback.answer()


# ====================================================================
# ШАГ 10b: Выбор кубитов для измерения (один или все)
# ====================================================================
@circuit_manage_router.callback_query(
    F.data.regexp(r'^circuits:\d+:gate:M:(\d+|all)$'), 
    StateFilter(States.input_target_qubit), 
    IsCircuitOwner(),
)
async def input_measurement_target_qubit(
    callback: CallbackQuery, 
    state: FSMContext, 
    session: AsyncSession, 
    i18n: TranslatorRunner, 
    circuit_id: int, 
):
    """Обработка выбора кубитов для измерения"""
    parts = callback.data.split(':')
    target_spec = parts[4]  # может быть число или 'all'

    circuit = await circuit_repository.get_circuit(
        session=session, 
        tg_id=callback.from_user.id,
        circuit_id=circuit_id,
    )

    # Определяем целевые кубиты
    if target_spec == 'all':
        targets = list(range(circuit.num_qubits))
    else:
        targets = [int(target_spec)]

    # Добавляем измерение в историю (отдельно для каждого кубита)
    for target in targets:
        circuit.circuit_history.append(['M', [], [target]])
    
    await session.flush()
    await session.refresh(circuit)

    # Получаем результат последней симуляции (если есть)
    text = await render_circuit_details(session, i18n, circuit)

    await present(
        callback, session=session, i18n=i18n, circuit=circuit,
        html=text, reply_markup=builder_circuit_manage(i18n, circuit_id), circuit_changed=True,
    )
    await state.set_state(States.circuit_manage)
    
    # Уведомление о количестве измеренных кубитов
    if len(targets) == 1:
        await callback.answer(i18n.measurement_applied_single())
    else:
        await callback.answer(i18n.measurement_applied_multiple(count=len(targets)))


# ШАГ 10: Выбор целевого кубита (финальный шаг)
@circuit_manage_router.callback_query(
    F.data.regexp(r'^circuits:\d+:gate:[^:]+:\d+$'), 
    StateFilter(States.input_target_qubit), 
    IsCircuitOwner(),
)
async def input_target_qubit_selected(
    callback: CallbackQuery, 
    state: FSMContext, 
    session: AsyncSession, 
    i18n: TranslatorRunner, 
    circuit_id: int, 
):
    """Обработка выбора целевого кубита - применение гейта к схеме"""
    data = await state.get_data()
    
    # Извлекаем данные
    gate_name = callback.data.split(':')[3]
    gate_full_name = data.get('gate_name')  # Может быть 'X' или 'Rx(π/2)'
    if gate_name in ['I', 'X', 'Y', 'Z', 'H', 'S', 'T', 'P', 'Rx', 'Ry', 'Rz']:
        pass
    elif gate_name in ['CX', 'CY', 'CZ', 'CH', 'CS', 'CP', 'CRx', 'CRy', 'CRz']:
        gate_full_name = data.get('gate_name')[1:]
    else:
        gate_full_name = data.get('gate_name')[2:]

    controls = data.get('controls', [])
    
    # Парсим целевой кубит из callback_data
    parts = callback.data.split(':')
    target_qubit = int(parts[-1])
    targets = [target_qubit]

    measured_qubits = await circuit_repository.get_measured_qubits(
        session=session, 
        tg_id=callback.from_user.id, 
        circuit_id=circuit_id, 
    )
    base_gate_name = gate_full_name.split('(')[0]
    
    try:
        validate_gate_on_measured_qubits(
            gate_name=base_gate_name,
            controls=controls,
            targets=targets,
            measured_qubits=measured_qubits
        )
    except ValueError:
        await callback.answer(
            i18n.gate_cannot_be_applied_to_measured_qubits(gate_name=gate_name), 
            show_alert=True
        )
        return

    # Получаем схему
    circuit = await circuit_repository.get_circuit(
        session=session, 
        tg_id=callback.from_user.id,
        circuit_id=circuit_id,
    )

    # Добавляем гейт в историю
    circuit.circuit_history.append([gate_full_name, controls, targets])
    await session.flush()
    await session.refresh(circuit)

    # Получаем результат последней симуляции (если есть)
    text = await render_circuit_details(session, i18n, circuit)

    await present(
        callback, session=session, i18n=i18n, circuit=circuit,
        html=text, reply_markup=builder_circuit_manage(i18n, circuit_id), circuit_changed=True,
    )
    await state.set_state(States.circuit_manage)
    await callback.answer(i18n.gate_applied_successfully())


# ОБРАБОТКА НАЖАТИЯ НА УЖЕ ВЫБРАННЫЙ КУБИТ
@circuit_manage_router.callback_query(
    F.data == 'control_qubit_already_selected',
)
async def control_qubit_already_selected(
    callback: CallbackQuery,
    i18n: TranslatorRunner,
):
    """Показывает уведомление, что кубит уже выбран"""
    await callback.answer(i18n.control_qubit_already_selected())


# ОБРАБОТКА КНОПКИ "ОТМЕНИТЬ ВЫБОР" (🔄)
@circuit_manage_router.callback_query(
    F.data.regexp(r'^circuits:\d+:gate:[^:]+:reset$'),
    IsCircuitOwner(),
)
async def reset_qubit_selection(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    i18n: TranslatorRunner,
    circuit_id: int,
):
    """Сбрасывает выбранные кубиты и возвращает к предыдущему шагу"""
    current_state = await state.get_state()
    data = await state.get_data()
    
    gate_name = data.get('gate_name', '')
    controls = data.get('controls', [])
    angle = data.get('angle')

    circuit = await circuit_repository.get_circuit(
        session=session,
        tg_id=callback.from_user.id,
        circuit_id=circuit_id,
    )

    # Возвращаемся в зависимости от текущего состояния
    if current_state == States.input_target_qubit:
        # Были выбраны контроли, сбрасываем их
        if len(controls) == 0:
            # Однокубитный гейт - возвращаемся к выбору гейта
            await state.clear()
            await state.update_data(circuit_id=circuit_id)
            await edit_screen(
                callback,
                # text=i18n.apply_gate_prompt(
                #     circuit_name=circuit.circuit_name,
                #     circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
                # ),
                reply_markup=builder_circuit_apply_gates(
                    num_qubits=circuit.num_qubits,
                    circuit_id=circuit_id,
                    i18n=i18n,
                ), 
                rich_message=InputRichMessage(html=i18n.apply_gate_prompt(
                    circuit_name=circuit.circuit_name,
                    circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
                ))
            )
            await state.set_state(States.circuit_manage)
        elif len(controls) == 1:
            # Двухкубитный гейт - возвращаемся к выбору контролирующего
            gate_base = gate_name.split('(')[0]
            await edit_screen(
                callback,
                # text=i18n.apply_gate_select_first_control(
                #     circuit_name=circuit.circuit_name,
                #     circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
                #     gate_name=gate_base,
                # ),
                reply_markup=builder_apply_gate_first_control(
                    num_qubits=circuit.num_qubits,
                    controls=[],
                    circuit_id=circuit_id,
                    gate_name=gate_base,
                    i18n=i18n,
                ), 
                rich_message=InputRichMessage(html=i18n.apply_gate_select_first_control(
                    circuit_name=circuit.circuit_name,
                    circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
                    gate_name=gate_base,
                )),
            )
            await state.set_state(States.input_first_control_qubit)
        else:
            # Трёхкубитный гейт - возвращаемся к выбору второго контролирующего
            gate_base = gate_name.split('(')[0]
            await edit_screen(
                callback,
                # text=i18n.apply_gate_select_second_control(
                #     circuit_name=circuit.circuit_name,
                #     circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
                #     gate_name=gate_base,
                # ),
                reply_markup=builder_apply_gate_second_control(
                    num_qubits=circuit.num_qubits,
                    first_control=controls[0],
                    circuit_id=circuit_id,
                    gate_name=gate_base,
                    i18n=i18n,
                ), 
                rich_message=InputRichMessage(html=i18n.apply_gate_select_second_control(
                    circuit_name=circuit.circuit_name,
                    circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
                    gate_name=gate_base,
                ))
            )
            await state.set_state(States.input_second_control_qubit)
    
    elif current_state == States.input_second_control_qubit:
        # Возвращаемся к выбору первого контролирующего
        gate_base = gate_name.split('(')[0]
        await edit_screen(
            callback,
            # text=i18n.apply_gate_select_first_control(
            #     circuit_name=circuit.circuit_name,
            #     circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
            #     gate_name=gate_base,
            # ),
            reply_markup=builder_apply_gate_first_control(
                num_qubits=circuit.num_qubits,
                controls=[],
                circuit_id=circuit_id,
                gate_name=gate_base,
                i18n=i18n,
            ), 
            rich_message=InputRichMessage(html=i18n.apply_gate_select_first_control(
                circuit_name=circuit.circuit_name,
                circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
                gate_name=gate_base,
            )),
        )
        await state.set_state(States.input_first_control_qubit)
    
    elif current_state == States.input_theta_qubit:
        # Возвращаемся к выбору гейта
        await state.clear()
        await state.update_data(circuit_id=circuit_id)
        await edit_screen(
            callback,
            # text=i18n.apply_gate_prompt(
            #     circuit_name=circuit.circuit_name,
            #     circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
            # ),
            reply_markup=builder_circuit_apply_gates(
                num_qubits=circuit.num_qubits,
                circuit_id=circuit_id,
                i18n=i18n,
            ), 
            rich_message=InputRichMessage(html=i18n.apply_gate_prompt(
                circuit_name=circuit.circuit_name,
                circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
            ))
        )
        await state.set_state(States.circuit_manage)

    await callback.answer(i18n.selection_reset())

    

# ====================================================================
# ШАГ 1: Открытие меню управления схемой
# ====================================================================
@circuit_manage_router.callback_query(
    F.data.regexp(r"^circuits:\d+:edit$"),
    StateFilter(States.circuit_manage),
    IsCircuitOwner(),
)
async def circuit_edit_menu(
    callback: CallbackQuery,
    state: FSMContext, 
    session: AsyncSession, 
    i18n: TranslatorRunner,
    circuit_id: int, 
):
    """Показывает меню управления схемой"""
    circuit = await circuit_repository.get_circuit(
        session=session, 
        tg_id=callback.from_user.id,
        circuit_id=circuit_id,
    )
    
    text = i18n.circuit_edit_menu(
        circuit_name=circuit.circuit_name,
        circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
    )

    await edit_screen(
        callback,
        # text=text, 
        reply_markup=builder_circuit_edit_menu(circuit_id, i18n), 
        rich_message=InputRichMessage(html=text),
    )
    await callback.answer()


# ====================================================================
# ШАГ 1.5: Удаление конкретного гейта
# ====================================================================

@circuit_manage_router.callback_query(F.data == 'ignore')
@circuit_manage_router.callback_query(F.data == 'ignore_prev')
@circuit_manage_router.callback_query(F.data == 'ignore_next')
async def ignore_buttons_func(
    callback: CallbackQuery
):
    await callback.answer()


# 1. Открытие меню удаления
@circuit_manage_router.callback_query(
    F.data.regexp(r"^circuits:\d+:edit:delete_gate$"),
    IsCircuitOwner()
)
async def circuit_delete_gate_menu(
    callback: CallbackQuery,
    session: AsyncSession, 
    i18n: TranslatorRunner,
    circuit_id: int,
):
    circuit = await circuit_repository.get_circuit(
        session=session, tg_id=callback.from_user.id, circuit_id=circuit_id
    )
    has_measurement_gates = any(gate[0] == 'M' for gate in circuit.circuit_history)
    
    table_html = generate_gates_table_html(circuit.circuit_history, page=1)
    text = i18n.delete_gate_message(
        circuit_name=circuit.circuit_name,
        circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
        gates_table=table_html,
        has_gates='True' if table_html else 'False'
    )
    keyboard = builder_delete_gate_keyboard(
        circuit_id=circuit_id,
        total_gates=len(circuit.circuit_history),
        current_page=1,
        i18n=i18n,
        has_measurements=has_measurement_gates
    )

    await edit_screen(
        callback,
        rich_message=InputRichMessage(html=text),
        reply_markup=keyboard
    )
    await callback.answer()


# 2. Пагинация
@circuit_manage_router.callback_query(
    F.data.regexp(r"^circuits:\d+:edit:delete_gate:page:\d+$"),
    IsCircuitOwner()
)
async def circuit_delete_gate_pagination(
    callback: CallbackQuery,
    session: AsyncSession, 
    i18n: TranslatorRunner,
    circuit_id: int,
):
    page = int(callback.data.split(":")[-1])
    
    circuit = await circuit_repository.get_circuit(
        session=session, tg_id=callback.from_user.id, circuit_id=circuit_id
    )
    has_measurement_gates = any(gate[0] == 'M' for gate in circuit.circuit_history)
    
    table_html = generate_gates_table_html(circuit.circuit_history, page=page)
    text = i18n.delete_gate_message(
        circuit_name=circuit.circuit_name,
        circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
        gates_table=table_html,
        has_gates='True' if table_html else 'False'
    )
    keyboard = builder_delete_gate_keyboard(
        circuit_id=circuit_id,
        total_gates=len(circuit.circuit_history),
        current_page=page,
        i18n=i18n,
        has_measurements=has_measurement_gates
    )

    await edit_screen(
        callback,
        rich_message=InputRichMessage(html=text),
        reply_markup=keyboard
    )
    await callback.answer()


# 3. Удаление конкретного гейта
@circuit_manage_router.callback_query(
    F.data.regexp(r"^circuits:\d+:edit:delete_gate:confirm:\d+$"),
    IsCircuitOwner()
)
async def circuit_delete_gate_action(
    callback: CallbackQuery,
    session: AsyncSession, 
    i18n: TranslatorRunner,
    circuit_id: int,
):
    gate_idx = int(callback.data.split(":")[-1])
    
    circuit = await circuit_repository.get_circuit(
        session=session, tg_id=callback.from_user.id, circuit_id=circuit_id
    )
    
    # Удаляем гейт из истории
    if 0 <= gate_idx < len(circuit.circuit_history):
        circuit.circuit_history.pop(gate_idx)
        # Сохраняем изменения в БД (используй свой метод обновления или commit)
        await session.flush()
        await session.refresh(circuit)
        
    # Пересчитываем текущую страницу, чтобы не остаться на пустой странице
    total_pages = math.ceil(len(circuit.circuit_history) / 10) if circuit.circuit_history else 1
    current_page = (gate_idx // 10) + 1
    if current_page > total_pages:
        current_page = total_pages if total_pages > 0 else 1
    has_measurement_gates = any(gate[0] == 'M' for gate in circuit.circuit_history)
    
    table_html = generate_gates_table_html(circuit.circuit_history, page=current_page)
    text = i18n.delete_gate_message(
        circuit_name=circuit.circuit_name,
        circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
        gates_table=table_html,
        has_gates='True' if table_html else 'False'
    )
    keyboard = builder_delete_gate_keyboard(
        circuit_id=circuit_id,
        total_gates=len(circuit.circuit_history),
        current_page=current_page,
        i18n=i18n,
        has_measurements=has_measurement_gates
    )

    await present(
        callback, session=session, i18n=i18n, circuit=circuit,
        html=text, reply_markup=keyboard, circuit_changed=True,
    )
    await callback.answer(i18n.delete_gate_success(), show_alert=False)


# Хэндлер для удаления всех измерений
@circuit_manage_router.callback_query(
    F.data.regexp(r"^circuits:\d+:edit:delete_gate:all_measurements$"),
    IsCircuitOwner()
)
async def circuit_delete_all_measurements(
    callback: CallbackQuery,
    session: AsyncSession, 
    i18n: TranslatorRunner,
    circuit_id: int,
):
    circuit = await circuit_repository.get_circuit(
        session=session, tg_id=callback.from_user.id, circuit_id=circuit_id
    )
    
    # Удаляем ВСЕ измерения из истории
    original_len = len(circuit.circuit_history)
    circuit.circuit_history = [
        gate for gate in circuit.circuit_history 
        if gate[0] != 'M'
    ]
    removed_count = original_len - len(circuit.circuit_history)
    
    # Сохраняем изменения
    await session.flush()
    await session.refresh(circuit)
    
    # Пересчитываем страницу (теперь гейтов меньше)
    total_pages = math.ceil(len(circuit.circuit_history) / 10) if circuit.circuit_history else 1
    current_page = min(1, total_pages) if total_pages > 0 else 1
    has_measurement_gates = any(gate[0] == 'M' for gate in circuit.circuit_history)

    table_html = generate_gates_table_html(circuit.circuit_history, page=current_page)
    text = i18n.delete_gate_message(
        circuit_name=circuit.circuit_name,
        circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
        gates_table=table_html,
        has_gates='True' if table_html else 'False'
    )
    keyboard = builder_delete_gate_keyboard(
        circuit_id=circuit_id,
        total_gates=len(circuit.circuit_history),
        current_page=current_page,
        i18n=i18n,
        has_measurements=has_measurement_gates
    )

    await present(
        callback, session=session, i18n=i18n, circuit=circuit,
        html=text, reply_markup=keyboard, circuit_changed=True,
    )
    await callback.answer(
        i18n.delete_measurements_success(count=removed_count),
    )


# ====================================================================
# ШАГ 2: Очистка схемы (удаление всех гейтов)
# ====================================================================
@circuit_manage_router.callback_query(
    F.data.regexp(r"^circuits:\d+:edit:clear$"),
    IsCircuitOwner(),
)
async def circuit_clear_confirm(
    callback: CallbackQuery,
    session: AsyncSession, 
    i18n: TranslatorRunner,
    circuit_id: int, 
):
    """Подтверждение очистки схемы"""
    circuit = await circuit_repository.get_circuit(
        session=session, 
        tg_id=callback.from_user.id,
        circuit_id=circuit_id,
    )
    
    # Очищаем историю гейтов
    circuit.circuit_history = []
    await session.flush()
    await session.refresh(circuit)
    
    # Получаем результат последней симуляции (если есть)
    text = await render_circuit_details(session, i18n, circuit)

    await present(
        callback, session=session, i18n=i18n, circuit=circuit,
        html=text, reply_markup=builder_circuit_manage(i18n, circuit_id), circuit_changed=True,
    )
    await callback.answer(i18n.circuit_cleared())


# ====================================================================
# ШАГ 3: Удаление схемы
# ====================================================================
@circuit_manage_router.callback_query(
    F.data.regexp(r"^circuits:\d+:edit:delete$"),
    IsCircuitOwner(),
)
async def circuit_delete_confirm(
    callback: CallbackQuery,
    session: AsyncSession, 
    i18n: TranslatorRunner,
    circuit_id: int, 
):
    """Подтверждение удаления схемы"""
    # Удаляем схему из БД
    await circuit_repository.delete_circuit(session, circuit_id)
    
    # Получаем обновлённый список схем
    user_circuits = await user_repository.get_user_circuits(
        session=session, 
        tg_id=callback.from_user.id, 
    )

    if not user_circuits:
        text = i18n.my_circuits(have_circuits='False')
    else:
        text = i18n.my_circuits(have_circuits='True')

    await callback.message.edit_text(
        text=text, 
        reply_markup=builder_circuits_keyboard(i18n=i18n, circuits=user_circuits)
    )
    await callback.answer(i18n.circuit_deleted())


# ====================================================================
# ШАГ 4: Начало переименования схемы
# ====================================================================
@circuit_manage_router.callback_query(
    F.data.regexp(r"^circuits:\d+:edit:rename$"),
    IsCircuitOwner(),
)
async def circuit_rename_start(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: TranslatorRunner,
    circuit_id: int, 
):
    """Запрашивает новое имя для схемы"""
    await state.update_data(circuit_id=circuit_id)
    await state.set_state(States.rename_circuit_name)
    
    await callback.message.edit_text(
        text=i18n.circuit_rename_prompt()
    )
    await callback.answer()


# ====================================================================
# ШАГ 5: Обработка нового имени схемы
# ====================================================================
@circuit_manage_router.message(
    StateFilter(States.rename_circuit_name),
)
async def circuit_rename_process(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    i18n: TranslatorRunner,
):
    """Обрабатывает новое имя схемы с проверкой на уникальность"""
    new_name = message.text.strip()
    
    # Проверка длины и пустоты
    if not new_name or len(new_name) > 50:
        await message.answer(i18n.circuit_name_invalid())
        return
    
    # Проверка уникальности имени в БД
    is_unique = await circuit_repository.is_unique_circuit_name(
        session=session,
        tg_id=message.from_user.id,
        name=new_name
    )
    if not is_unique:
        await message.answer(i18n.circuit_name_not_unique())
        return
    
    data = await state.get_data()
    circuit_id = data['circuit_id']
    
    # Обновляем имя схемы
    circuit = await circuit_repository.get_circuit(
        session=session,
        tg_id=message.from_user.id,
        circuit_id=circuit_id,
    )
    circuit.circuit_name = new_name
    await session.flush()
    await session.refresh(circuit)
    
    # Получаем результат последней симуляции (если есть)
    text = await render_circuit_details(session, i18n, circuit)

    await present(
        message, session=session, i18n=i18n, circuit=circuit,
        html=text, reply_markup=builder_circuit_manage(i18n, circuit_id), circuit_changed=True,
    )
    await state.set_state(States.circuit_manage)

# ====================================================================
# ШАГ 6: Экспортирование схемы
# ====================================================================
# Хэндлер отвечает за нажатие на кнопку "Экспортировать схему" в Edit-меню 
@circuit_manage_router.callback_query(
    F.data.regexp(r"^circuits:\d+:edit:export$"),
    IsCircuitOwner()
)
async def circuit_export_menu(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
    circuit_id: int,
    user_complexity_level: str,
):
    """Показывает меню выбора формата экспорта"""
    circuit = await circuit_repository.get_circuit(
        session=session,
        tg_id=callback.from_user.id,
        circuit_id=circuit_id
    )
    
    text = i18n.export_menu_text(
        complexity_level=user_complexity_level, 
        circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
        circuit_name=circuit.circuit_name,
    )
    
    await edit_screen(
        callback,
        rich_message=InputRichMessage(html=text),
        reply_markup=builder_export_format_keyboard(circuit_id, i18n)
    )
    await callback.answer()


# Хэндлер, отвечает за каждый из вариантов экспорта.
@circuit_manage_router.callback_query(
    F.data.regexp(r"^circuits:\d+:edit:export:(qasm2|qasm3|ariquantum|qiskit)$"),
    IsCircuitOwner()
)
async def circuit_export_action(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
    circuit_id: int,
    user_complexity_level: str,
):
    """Выполняет экспорт и отправляет файл + код в сообщении"""
    # Извлекаем формат из callback_data
    export_format = callback.data.split(":")[-1]
    
    circuit = await circuit_repository.get_circuit(
        session=session,
        tg_id=callback.from_user.id,
        circuit_id=circuit_id
    )
    user = await user_repository.get_user(session, callback.from_user.id)
    shots = user.setting.simulation_shots or 100
    
    # Выбираем функцию экспорта
    if export_format == 'qasm2':
        code = export_to_qasm2(circuit)
        filename = f"{slugify_filename(circuit.circuit_name)}.qasm"
        format_name = 'OpenQASM 2.0'
    elif export_format == 'qasm3':
        code = export_to_qasm3(circuit)
        filename = f"{slugify_filename(circuit.circuit_name)}.qasm"
        format_name = 'OpenQASM 3.0'
    elif export_format == 'ariquantum':
        code = export_to_ariquantum(circuit, shots)
        filename = f"{slugify_filename(circuit.circuit_name)}.py"
        format_name = 'AriQuantum'
    elif export_format == 'qiskit':
        code = export_to_qiskit(circuit, shots)
        filename = f"{slugify_filename(circuit.circuit_name)}.py"
        format_name = 'Qiskit'
    
    # Формируем сообщение с обрезанным кодом
    text = i18n.export_success_text(
        circuit_name=circuit.circuit_name,
        format_name=format_name,
        code=code, 
    )
    
    # Создаем файл
    file = BufferedInputFile(
        code.encode('utf-8'),
        filename=filename
    )
    
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Отправляем файл и текст
    await callback.message.answer_document(
        document=file,
    )
    await callback.message.answer(
        text=text,
        reply_markup=builder_export_result_keyboard(circuit_id, i18n),
    )
    
    await callback.answer(i18n.export_success_alert(), show_alert=False)


