import logging
from fluentogram import TranslatorRunner

from aiogram import Bot, Router, F
from aiogram.types import CallbackQuery, InputRichMessage, Message
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State

from sqlalchemy.ext.asyncio import AsyncSession

from ..utils.draw_circuit import draw_history
from ..utils.check_measured import validate_gate_on_measured_qubits
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

    last_simulation = await circuit_repository.get_last_simulation_circuit(
        session=session, 
        circuit_id=circuit_id, 
    )
    if not last_simulation:
        state_vector = f'|{"0" * circuit.num_qubits}⟩'
        has_simulation = 'False'
    else:
        state_vector = last_simulation.braket_state
        has_simulation = 'True'

    text = i18n.circuit_details(
        circuit_name=circuit.circuit_name, 
        circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
        state_vector=state_vector,
        backend=circuit.backend.name, 
        has_simulation=has_simulation, 
    )

    await callback.message.edit_text(
        # text=text, 
        reply_markup=builder_circuit_manage(
            i18n, circuit_id
        ), 
        rich_message=InputRichMessage(html=text)
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

    await callback.message.edit_text(
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

    await callback.message.edit_text(
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

    await callback.message.edit_text(
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

    await callback.message.edit_text(
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

    await callback.message.edit_text(
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

    await callback.message.edit_text(
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

    await callback.message.edit_text(
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

    await callback.message.edit_text(
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

    await callback.message.edit_text(
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

    await callback.message.edit_text(
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

    await callback.message.edit_text(
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
    last_simulation = await circuit_repository.get_last_simulation_circuit(
        session=session, 
        circuit_id=circuit_id, 
    )
    
    if last_simulation:
        state_vector = last_simulation.braket_state
        has_simulation = 'True'
    else:
        state_vector = f'|{"0" * circuit.num_qubits}⟩'
        has_simulation = 'False'

    # Возвращаемся в управление схемой
    text = i18n.circuit_details(
        circuit_name=circuit.circuit_name, 
        circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
        backend=circuit.backend.name, 
        state_vector=state_vector,
        has_simulation=has_simulation, 
    )

    await callback.message.edit_text(
        # text=text, 
        reply_markup=builder_circuit_manage(i18n, circuit_id), 
        rich_message=InputRichMessage(html=text), 
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
    last_simulation = await circuit_repository.get_last_simulation_circuit(
        session=session, 
        circuit_id=circuit_id, 
    )
    
    if last_simulation:
        state_vector = last_simulation.braket_state
        has_simulation = 'True'
    else:
        state_vector = f'|{"0" * circuit.num_qubits}⟩'
        has_simulation = 'False'

    # Возвращаемся в управление схемой
    text = i18n.circuit_details(
        circuit_name=circuit.circuit_name, 
        circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
        backend=circuit.backend.name, 
        state_vector=state_vector,
        has_simulation=has_simulation, 
    )

    await callback.message.edit_text(
        # text=text, 
        reply_markup=builder_circuit_manage(i18n, circuit_id), 
        rich_message=InputRichMessage(html=text), 
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
            await callback.message.edit_text(
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
            await callback.message.edit_text(
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
            await callback.message.edit_text(
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
        await callback.message.edit_text(
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
        await callback.message.edit_text(
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

    await callback.message.edit_text(
        # text=text, 
        reply_markup=builder_circuit_edit_menu(circuit_id, i18n), 
        rich_message=InputRichMessage(html=text),
    )
    await callback.answer()


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
    last_simulation = await circuit_repository.get_last_simulation_circuit(
        session=session, 
        circuit_id=circuit_id, 
    )
    
    if last_simulation:
        state_vector = last_simulation.braket_state
        has_simulation = 'True'
    else:
        state_vector = f'|{"0" * circuit.num_qubits}⟩'
        has_simulation = 'False'

    # Возвращаемся в управление схемой
    text = i18n.circuit_details(
        circuit_name=circuit.circuit_name, 
        circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
        backend=circuit.backend.name, 
        state_vector=state_vector,
        has_simulation=has_simulation, 
    )

    await callback.message.edit_text(
        # text=text, 
        reply_markup=builder_circuit_manage(i18n, circuit_id),
        rich_message=InputRichMessage(html=text), 
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
    """Обрабатывает новое имя схемы"""
    new_name = message.text.strip()
    
    if not new_name or len(new_name) > 50:
        await message.answer(i18n.circuit_name_invalid())
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
    last_simulation = await circuit_repository.get_last_simulation_circuit(
        session=session, 
        circuit_id=circuit_id, 
    )
    
    if last_simulation:
        state_vector = last_simulation.braket_state
        has_simulation = 'True'
    else:
        state_vector = f'|{"0" * circuit.num_qubits}⟩'
        has_simulation = 'False'

    # Возвращаемся в управление схемой
    text = i18n.circuit_details(
        circuit_name=circuit.circuit_name, 
        circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
        backend=circuit.backend.name, 
        state_vector=state_vector,
        has_simulation=has_simulation, 
    )

    await message.answer_rich(
        rich_message=InputRichMessage(html=text), 
        reply_markup=builder_circuit_manage(i18n, circuit_id)
    )
    await state.set_state(States.circuit_manage)


