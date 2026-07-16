import logging
from fluentogram import TranslatorRunner

from aiogram import Router, F
from aiogram.types import CallbackQuery, InputRichMessage
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

import asyncio
from functools import partial
from sqlalchemy.ext.asyncio import AsyncSession

from ..filters.is_owner_circuit import IsCircuitOwner
from ..states.states import States
from ...infrastructure.database.repositories import circuit_repository, user_repository, activity_repository
from ..keyboards.simulation_keyboards import builder_simulation_result
from ..keyboards.circuit_manage_keyboards import builder_circuit_manage
from ..utils.simulation import simulate_circuit
from ..utils.draw_circuit import draw_history


logger = logging.getLogger(__name__)
simulation_router = Router()


@simulation_router.callback_query(
    F.data.regexp(r"^circuits:\d+:simulate$"),
    StateFilter(States.circuit_manage),
    IsCircuitOwner(),
)
async def simulate_circuit_handler(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
    circuit_id: int,
):
    """Обрабатывает запрос на симуляцию схемы"""
    # Получаем схему
    circuit = await circuit_repository.get_circuit(
        session=session,
        tg_id=callback.from_user.id,
        circuit_id=circuit_id,
    )
    
    # Получаем настройки пользователя для shots
    user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
    shots = user_settings.simulation_shots
    backend_name = circuit.backend.name
    
    # Выполняем симуляцию
    try:
        loop = asyncio.get_event_loop()

        sim_func = partial(
            simulate_circuit,
            history=circuit.circuit_history,
            num_qubits=circuit.num_qubits,
            backend_name=backend_name,
            shots=shots
        )

        # Выполняем в отдельном потоке с таймаутом
        braket_state, counts, execution_time = await asyncio.wait_for(
            loop.run_in_executor(None, sim_func),
            timeout=10.0
        )
    except asyncio.TimeoutError as e:
        logger.error(f'Simulation timeout error: {e}')
        await callback.answer(i18n.simulation_timeout_error(), show_alert=True)
        return

    except Exception as e:
        logger.error(f"Simulation error: {e}")
        await callback.answer(i18n.simulation_error(), show_alert=True)
        return
    
    # Сохраняем результат в БД
    await circuit_repository.create_simulation_result(
        session=session,
        tg_id=callback.from_user.id,
        circuit_id=circuit_id,
        braket_state=braket_state,
        counts=counts,
        execution_time=execution_time,
        shots=shots
    )
    user_activity_today = await activity_repository.get_activity_today(
        session=session, 
        tg_id=callback.from_user.id, 
    )
    user_activity_today.simulations_run += 1

    
    # Формируем текст результата
    if counts is not None:
        # Есть измерения - показываем состояние до измерения + статистику
        counts_text = "\n".join([f"• |{state}⟩: {count}" for state, count in sorted(counts.items())])
        text = i18n.simulation_result_with_measurements(
            circuit_name=circuit.circuit_name,
            circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
            backend=backend_name,
            execution_time=f"{execution_time:.4f}",
            braket_state=braket_state,
            counts=counts_text,
            shots=str(shots)
        )
    else:
        # Нет измерений - только вектор состояния
        text = i18n.simulation_result_without_measurements(
            circuit_name=circuit.circuit_name,
            circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
            backend=backend_name,
            execution_time=f"{execution_time:.4f}",
            braket_state=braket_state
        )

    try:
        await callback.message.delete()
    except Exception:
        pass
    
    # Отправляем новое сообщение (не редактируем)
    await callback.message.answer_rich(
        rich_message=InputRichMessage(html=text),
        reply_markup=builder_simulation_result(circuit_id, i18n), 
    )
    await callback.answer()


@simulation_router.callback_query(F.data.regexp(r"^simulation:back:(\d+)$"))
async def simulation_back_to_circuit(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
    state: FSMContext
):
    """Возвращает к управлению схемой"""
    circuit_id = int(callback.data.split(":")[2])
    
    circuit = await circuit_repository.get_circuit(
        session=session,
        tg_id=callback.from_user.id,
        circuit_id=circuit_id,
    )
    
    # Получаем последнюю симуляцию для отображения состояния
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
    
    text = i18n.circuit_details(
        circuit_name=circuit.circuit_name,
        circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
        backend=circuit.backend.name, 
        state_vector=state_vector,
        has_simulation=has_simulation,
    )
    
    await callback.message.answer_rich(
        rich_message=InputRichMessage(html=text),
        reply_markup=builder_circuit_manage(i18n, circuit_id), 
    )
    await state.set_state(
        States.circuit_manage
    )
    await callback.answer()