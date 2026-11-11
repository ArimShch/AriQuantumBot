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
from ...infrastructure.database.repositories import circuit_repository, user_repository, activity_repository, base_repository
from ..keyboards.simulation_keyboards import (
    builder_simulation_result,
    builder_simulation_select_backend,
    builder_simulation_select_shots
)
from ..keyboards.circuit_manage_keyboards import builder_circuit_manage
from ..utils.simulation import simulate_circuit
from ..utils.histogram import build_histogram_widget, format_counts_ascii
from ..utils.widgets import SendWidget
from ..utils.draw_circuit import draw_history
from ..utils.circuit_view import render_circuit_details
from ..utils.circuit_screen import present


logger = logging.getLogger(__name__)

simulation_router = Router()


async def _run_simulation_and_send_result(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
    circuit,
    backend_id: int,
    shots: int,
    forced_qiskit: bool,
    backends: list
):
    """Единая функция исполнения симуляции и отправки результата"""
    backend_name = next(b.name for b in backends if b.id == backend_id)
    
    try:
        loop = asyncio.get_event_loop()
        sim_func = partial(
            simulate_circuit,
            history=circuit.circuit_history,
            num_qubits=circuit.num_qubits,
            backend_name=backend_name,
            shots=shots
        )
        
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
    
    # Сохраняем результат
    await circuit_repository.create_simulation_result(
        session=session,
        tg_id=callback.from_user.id,
        circuit_id=circuit.id,
        backend_id=backend_id,
        braket_state=braket_state,
        counts=counts,
        execution_time=execution_time,
        shots=shots
    )
    user_activity = await activity_repository.get_activity_today(session=session, tg_id=callback.from_user.id)
    user_activity.simulations_run += 1
    
    forced_warning = i18n.simulation_forced_qiskit() if forced_qiskit else ""

    has_counts = counts is not None and len(counts) > 0

    if has_counts:
        # ASCII-гистограмма (формат «ascii» и запасной вариант для виджета)
        counts_text = format_counts_ascii(counts)

        text = i18n.simulation_result_with_measurements(
            circuit_name=circuit.circuit_name,
            circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
            backend=backend_name,
            execution_time=f"{execution_time:.4f}",
            braket_state=braket_state,
            counts=counts_text,
            shots=str(shots),
            forced_warning=forced_warning
        )
    else:
        text = i18n.simulation_result_without_measurements(
            circuit_name=circuit.circuit_name,
            circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
            backend=backend_name,
            execution_time=f"{execution_time:.4f}",
            braket_state=braket_state,
            forced_warning=forced_warning
        )

    # Виджет: только если выбран в настройках, есть измерения и это личный чат
    widget = None
    if has_counts and callback.message.chat.type == 'private':
        user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
        if user_settings.output_mode == 'widget':
            # Как и в ASCII-режиме, показываем состояния всех кубитов схемы
            html, height, hidden = build_histogram_widget(
                counts,
                texts={
                    'count': i18n.simulation_widget_detail_count(),
                    'of': i18n.simulation_widget_detail_of(),
                    'share': i18n.simulation_widget_detail_share(),
                    'qubits': i18n.simulation_widget_detail_qubits(),
                },
            )

            caption = i18n.simulation_widget_title(shots=str(shots))
            if hidden:
                caption += '\n' + i18n.simulation_widget_hidden_note(
                    shown=len(counts) - hidden,
                    total=len(counts),
                )

            # Остальной результат (RTF) — без гистограммы, отправляется после виджета
            widget_text = i18n.simulation_result_with_measurements_widget(
                circuit_name=circuit.circuit_name,
                circuit_diagram=draw_history(circuit.num_qubits, circuit.circuit_history),
                backend=backend_name,
                execution_time=f"{execution_time:.4f}",
                braket_state=braket_state,
                forced_warning=forced_warning
            )
            widget = {'html': html, 'height': height, 'caption': caption, 'text': widget_text}

    try:
        await callback.message.delete()
    except Exception:
        pass

    widget_sent = False
    if widget is not None:
        # 1) гистограмма: сначала виджет, затем подпись
        try:
            await callback.bot(SendWidget(
                chat_id=callback.message.chat.id,
                html=widget['html'],
                height=widget['height'],
                caption=widget['caption'],
            ))
            widget_sent = True
        except Exception as e:
            # Виджеты недоступны (старый клиент, ошибка API) — откат на ASCII
            logger.warning(f'Widget send failed, falling back to ASCII: {e}')

    # 2) текст результата в RTF (с кнопками) — после гистограммы
    await callback.message.answer_rich(
        rich_message=InputRichMessage(html=widget['text'] if widget_sent else text),
        reply_markup=builder_simulation_result(circuit.id, i18n),
    )
    await callback.answer()


# ШАГ 1: Старт симуляции (проверка лимитов и настроек)
@simulation_router.callback_query(
    F.data.regexp(r"^circuits:\d+:simulate$"),
    StateFilter(States.circuit_manage),
    IsCircuitOwner(),
)
async def simulate_circuit_start(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
    circuit_id: int,
):
    circuit = await circuit_repository.get_circuit(session=session, tg_id=callback.from_user.id, circuit_id=circuit_id)
    user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
    backends = await base_repository.get_backends(session)
    
    # Проверяем, есть ли измерения в схеме
    measured_qubits = await circuit_repository.get_measured_qubits(
        session=session, tg_id=callback.from_user.id, circuit_id=circuit_id
    )
    has_measurements = len(measured_qubits) > 0

    forced_qiskit = False
    backend_id = user_settings.backend_id

    # 1. Проверка кубитов (> 6 кубитов = принудительно Qiskit)
    if circuit.num_qubits > 6:
        qiskit_backend = next(b for b in backends if b.name == "Qiskit")
        backend_id = qiskit_backend.id
        forced_qiskit = True
    
    # 2. Проверка бэкенда (если None и не принудительно Qiskit -> просим выбрать)
    if backend_id is None:
        await callback.message.edit_text(
            text=i18n.simulation_select_backend(),
            reply_markup=builder_simulation_select_backend(circuit_id, backends, i18n)
        )
        return

    # 3. Проверка Shots (только если есть измерения и настройка shots = None)
    shots = user_settings.simulation_shots
    if shots is None:
        if has_measurements:
            await callback.message.edit_text(
                text=i18n.simulation_select_shots(),
                reply_markup=builder_simulation_select_shots(circuit_id, backend_id, i18n)
            )
            return
        else:
            # Если нет измерений, кол-во shots не влияет на state vector
            shots = 10 

    # 4. Если всё известно - запускаем
    await _run_simulation_and_send_result(callback, session, i18n, circuit, backend_id, shots, forced_qiskit, backends)


# ШАГ 2: Бэкенд выбран вручную (проверяем Shots)
@simulation_router.callback_query(
    F.data.regexp(r"^simulate:\d+:backend:\d+$"),
    IsCircuitOwner(),
)
async def simulate_backend_selected(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
    circuit_id: int,
):
    parts = callback.data.split(":")
    backend_id = int(parts[3])
    
    circuit = await circuit_repository.get_circuit(session=session, tg_id=callback.from_user.id, circuit_id=circuit_id)
    user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
    backends = await base_repository.get_backends(session)

    # Проверяем, есть ли измерения в схеме
    measured_qubits = await circuit_repository.get_measured_qubits(
        session=session, tg_id=callback.from_user.id, circuit_id=circuit_id
    )
    has_measurements = len(measured_qubits) > 0

    shots = user_settings.simulation_shots
    if shots is None:
        if has_measurements:
            await callback.message.edit_text(
                text=i18n.simulation_select_shots(),
                reply_markup=builder_simulation_select_shots(circuit_id, backend_id, i18n)
            )
            return
        else:
            shots = 10

    await _run_simulation_and_send_result(callback, session, i18n, circuit, backend_id, shots, False, backends)


# ШАГ 3: Shots выбраны вручную (Финальный запуск)
@simulation_router.callback_query(
    F.data.regexp(r"^simulate:\d+:backend:\d+:shots:\d+$"),
    IsCircuitOwner(),
)
async def simulate_shots_selected(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
    circuit_id: int,
):
    parts = callback.data.split(":")
    backend_id = int(parts[3])
    shots = int(parts[5])
    
    circuit = await circuit_repository.get_circuit(session=session, tg_id=callback.from_user.id, circuit_id=circuit_id)
    backends = await base_repository.get_backends(session)

    forced_qiskit = circuit.num_qubits > 6

    await _run_simulation_and_send_result(callback, session, i18n, circuit, backend_id, shots, forced_qiskit, backends)


# Возврат к схеме
@simulation_router.callback_query(F.data.regexp(r"^simulation:back:(\d+)$"))
async def simulation_back_to_circuit(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
    state: FSMContext
):
    circuit_id = int(callback.data.split(":")[2])
    circuit = await circuit_repository.get_circuit(session=session, tg_id=callback.from_user.id, circuit_id=circuit_id)
    if circuit is None:
        await callback.answer()
        return
    
    text = await render_circuit_details(session, i18n, circuit)
    
    # Как и раньше — новым сообщением (результат симуляции остаётся в чате)
    await present(
        callback.message, session=session, i18n=i18n, circuit=circuit,
        html=text, reply_markup=builder_circuit_manage(i18n, circuit_id),
        user_id=callback.from_user.id,
    )
    await state.set_state(States.circuit_manage)
    await callback.answer()