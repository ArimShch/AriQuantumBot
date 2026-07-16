import logging
from fluentogram import TranslatorRunner
from uuid import uuid4

from aiogram import Bot, Router, F
from aiogram.types import CallbackQuery, Message, InputRichMessage
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State

from sqlalchemy.ext.asyncio import AsyncSession

from ..utils.draw_circuit import draw_history
from ..filters.is_unique_circuit_name import IsUniqueCircuitName
from ..states.states import States
from ...infrastructure.database.models.models import UserSetting, QuantumCircuit, User
from ...infrastructure.database.repositories import user_repository, circuit_repository, activity_repository
from ..keyboards.create_circuit_keyboards import (
    builder_num_qubits_keyboard, 
    builder_my_circuits_keyboard,
)
from ..keyboards.circuit_manage_keyboards import builder_circuit_manage


logger = logging.getLogger(__name__)

create_circuit_router = Router()


# Хэндлер, отвечающий за обработку команды /create_circuit
@create_circuit_router.message(Command(commands=['create_circuit']))
async def create_circuit_command_func(
    message: Message, 
    state: FSMContext,
    session: AsyncSession,
    i18n: TranslatorRunner, 
    user_complexity_level: str, 
):
    if await user_repository.has_reached_circuit_limit(
        session=session, 
        tg_id=message.from_user.id, 
    ):
        await message.answer(
            text=i18n.circuit_limit_reached(), 
            reply_markup=builder_my_circuits_keyboard(i18n),  
        )
        return


    user_settings: UserSetting = await user_repository.get_user_settings(
        session=session, 
        tg_id=message.from_user.id,
    )
    await state.update_data(user_settings=user_settings)

    if not user_settings.automatic_name:
        text = i18n.input_circuit_name(
            complexity_level=user_complexity_level, 
        )
        await message.answer(
            text=text, 
        )
        await state.set_state(States.input_circuit_name)
    else:
        await input_circuit_name_func(message, state, session, i18n, user_complexity_level)


# Хэндлер, отвечающий за обработку ввода имени схемы
@create_circuit_router.message(
    StateFilter(States.input_circuit_name),
    F.text, 
    IsUniqueCircuitName()
)

async def input_circuit_name_func(
    message: Message, 
    state: FSMContext, 
    session: AsyncSession, 
    i18n: TranslatorRunner, 
    user_complexity_level: str,
):
    if len(message.text.strip()) > 50:
        await message.answer(text=i18n.error_input_circuit_name())
        return    

    data = await state.get_data()
    user_settings: UserSetting = data['user_settings']

    if user_settings.automatic_name:
        await state.update_data(
            circuit_name=f'QC-{message.from_user.id}-{uuid4().hex[:8].upper()}'
        )
    else:
        await state.update_data(
            circuit_name=message.text
        )

    if user_settings.qubit_input_text:
        text = i18n.input_num_qubits_text(
            num_qubits=user_settings.backend.max_qubits,
            complexity_level=user_complexity_level,
        )
        await message.answer(
            text=text, 
        )
    else:
        text = i18n.input_num_qubits_keyboard(
            complexity_level=user_complexity_level, 
            num_qubits=user_settings.backend.max_qubits,
        )
        await message.answer(
            text=text, 
            reply_markup=builder_num_qubits_keyboard(user_settings.backend.max_qubits)
        )
    
    await state.set_state(States.input_num_qubits)


# Хэндлер, отвечающий за обработку ошибки ввода имени схемы
@create_circuit_router.message(
        StateFilter(States.input_circuit_name), 
)
async def input_circuit_name_func_error(
    message: Message, 
    i18n: TranslatorRunner, 
):
    await message.answer(
        text=i18n.error_input_circuit_name(),
    )


# Хэндлер, отвечающий за обработку выбора количества кубитов через кнопки
@create_circuit_router.callback_query(
        StateFilter(States.input_num_qubits), 
        F.data.startswith('create:num_qubits:'), 
)
async def input_num_qubits_keyboard_func(
    callback: CallbackQuery, 
    state: FSMContext, 
    session: AsyncSession, 
    i18n: TranslatorRunner, 
    user_complexity_level: str,
):
    data = await state.get_data()

    try:
        num_qubits = int(callback.data.split(':')[-1])

        data = await state.get_data()
        user_settings: UserSetting = data['user_settings']
        
        if user_settings.backend.max_qubits < num_qubits or num_qubits < 1:
            raise ValueError('Указанное количество кубитов больше или меньше доступного для бэкенда')
    except Exception as e:
        await callback.answer(
            text=i18n.error_num_qubits_invalid(max_qubits=user_settings.backend.max_qubits),
            show_alert=True
        )
        return 

    if await user_repository.has_reached_circuit_limit(
        session=session, 
        tg_id=callback.from_user.id, 
    ):
        await callback.message.edit_text(
            text=i18n.circuit_limit_reached(), 
            reply_markup=builder_my_circuits_keyboard(i18n),  
        )
        return

    created_circuit: QuantumCircuit = await circuit_repository.create_circuit(
        tg_id=callback.from_user.id, 
        circuit_name=data['circuit_name'], 
        num_qubits=num_qubits, 
        backend_id=user_settings.backend_id, 
        session=session
    )
    user_activity_today = await activity_repository.get_activity_today(
        session=session, 
        tg_id=callback.from_user.id, 
    )
    user_activity_today.circuits_created += 1

    last_simulation = await circuit_repository.get_last_simulation_circuit(
        session=session, 
        circuit_id=created_circuit.id, 
    )
    if not last_simulation:
        state_vector = f'|{"0" * created_circuit.num_qubits}⟩'
        has_simulation = 'False'
    else:
        state_vector = last_simulation.braket_state
        has_simulation = 'True'

    text = i18n.circuit_details(
        circuit_name=created_circuit.circuit_name, 
        circuit_diagram=draw_history(created_circuit.num_qubits, created_circuit.circuit_history),
        state_vector=state_vector,
        backend=created_circuit.backend.name, 
        has_simulation=has_simulation, 
    )

    await callback.message.edit_text(
        # text=text,  
        reply_markup=builder_circuit_manage(
            i18n, created_circuit.id,
        ),
        rich_message=InputRichMessage(html=text)
    )

    await state.set_state(
        States.circuit_manage
    )


# Хэндлер, отвечающий за обработку ввода количества кубитов текстовым сообщением
@create_circuit_router.message(
        StateFilter(States.input_num_qubits), 
        F.text.regexp(r'^\d+$')
)
async def input_num_qubits_text_func(
    message: Message, 
    state: FSMContext, 
    session: AsyncSession, 
    i18n: TranslatorRunner, 
    user_complexity_level: str,
):
    data = await state.get_data()

    try:
        num_qubits = int(message.text)

        user_settings: UserSetting = data['user_settings']
        
        if user_settings.backend.max_qubits < num_qubits or num_qubits < 1:
            raise ValueError('Указанное количество кубитов больше или меньше доступного для бэкенда')
        
    except Exception as e:
        await input_num_qubits_text_error_func(
            message, 
            state, 
            i18n, 
        )
        logger.error('Error in working input_num_qubits_text_func func.')
        return 

    if await user_repository.has_reached_circuit_limit(
        session=session, 
        tg_id=message.from_user.id, 
    ):
        await message.answer(
            text=i18n.circuit_limit_reached(), 
            reply_markup=builder_my_circuits_keyboard(i18n),  
        )
        return

    created_circuit: QuantumCircuit = await circuit_repository.create_circuit(
        tg_id=message.from_user.id, 
        circuit_name=data['circuit_name'], 
        num_qubits=num_qubits, 
        backend_id=user_settings.backend_id, 
        session=session, 
    )
    user_activity_today = await activity_repository.get_activity_today(
        session=session, 
        tg_id=message.from_user.id, 
    )
    user_activity_today.circuits_created += 1

    last_simulation = await circuit_repository.get_last_simulation_circuit(
        session=session, 
        circuit_id=created_circuit.id, 
    )
    if not last_simulation:
        state_vector = f'|{"0" * created_circuit.num_qubits}⟩'
        has_simulation = 'False'
    else:
        state_vector = last_simulation.braket_state
        has_simulation = 'True'

    text = i18n.circuit_details(
        circuit_name=created_circuit.circuit_name, 
        circuit_diagram=draw_history(created_circuit.num_qubits, created_circuit.circuit_history),
        state_vector=state_vector,        
        backend=created_circuit.backend.name, 
        has_simulation=has_simulation, 
    )

    await message.answer_rich(
        rich_message=InputRichMessage(html=text), 
        reply_markup=builder_circuit_manage(
            i18n, created_circuit.id,
        )
    )

    await state.set_state(
        States.circuit_manage
    )


# Хэндлер, отвечающий за обработку ошибки ввода количества кубитов текстом
@create_circuit_router.message(
    StateFilter(States.input_num_qubits),
)
async def input_num_qubits_text_error_func(
    message: Message, 
    state: FSMContext, 
    i18n: TranslatorRunner, 
):
    data = await state.get_data()
    user_settings: UserSetting = data['user_settings']

    await message.answer(
        text=i18n.error_input_num_qubits(max_qubits=user_settings.backend.max_qubits)
    )


