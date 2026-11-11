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
from ..utils.circuit_view import render_circuit_details
from ..utils.circuit_screen import present
from ..utils.formatters_for_admin import format_user_link
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

UNIVERSAL_MAX_QUBITS = 10


# Хэндлер, отвечающий за старт процесса создания схемы (/create_circuit)
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
    # В FSM кладём только простые значения, а не ORM-объект
    await state.update_data(
        automatic_name=user_settings.automatic_name,
        qubit_input_text=user_settings.qubit_input_text,
    )

    if not user_settings.automatic_name:
        text = i18n.input_circuit_name(
            complexity_level=user_complexity_level, 
        )
        await message.answer(text=text)
        await state.set_state(States.input_circuit_name)
    else:
        await input_circuit_name_func(message, state, session, i18n, user_complexity_level)


# Хэндлер, отвечающий за обработку введенного имени схемы
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

    if data['automatic_name']:
        await state.update_data(
            circuit_name=f'QC-{message.from_user.id}-{uuid4().hex[:8].upper()}'
        )
    else:
        await state.update_data(
            circuit_name=message.text
        )

    if data['qubit_input_text']:
        text = i18n.input_num_qubits_text(
            num_qubits=UNIVERSAL_MAX_QUBITS,
            complexity_level=user_complexity_level,
        )
        await message.answer(text=text)
    else:
        text = i18n.input_num_qubits_keyboard(
            complexity_level=user_complexity_level, 
            num_qubits=UNIVERSAL_MAX_QUBITS,
        )
        await message.answer(
            text=text, 
            reply_markup=builder_num_qubits_keyboard(UNIVERSAL_MAX_QUBITS)
        )
    
    await state.set_state(States.input_num_qubits)


# Хэндлер, отвечающий за обработку ошибки ввода имени схемы (если прислали не текст)
@create_circuit_router.message(
        StateFilter(States.input_circuit_name), 
)
async def input_circuit_name_func_error(
    message: Message, 
    i18n: TranslatorRunner, 
):
    await message.answer(text=i18n.error_input_circuit_name())


# Хэндлер, отвечающий за обработку выбора количества кубитов через инлайн-кнопки
@create_circuit_router.callback_query(
        StateFilter(States.input_num_qubits), 
        F.data.startswith('create:num_qubits:'), 
)
async def input_num_qubits_keyboard_func(
    callback: CallbackQuery, 
    state: FSMContext, 
    session: AsyncSession, 
    i18n: TranslatorRunner, 
    admin_ids: list,
    bot: Bot, 
):
    data = await state.get_data()
    user = await user_repository.get_user(session, callback.from_user.id)

    try:
        num_qubits = int(callback.data.split(':')[-1])
        if num_qubits < 1 or num_qubits > UNIVERSAL_MAX_QUBITS:
            raise ValueError('Указанное количество кубитов вне диапазона 1-10')
    except Exception:
        await callback.answer(
            text=i18n.error_num_qubits_invalid(max_qubits=UNIVERSAL_MAX_QUBITS),
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

    # Создание схемы (backend_id больше не передается)
    created_circuit: QuantumCircuit = await circuit_repository.create_circuit(
        tg_id=callback.from_user.id, 
        circuit_name=data['circuit_name'], 
        num_qubits=num_qubits, 
        session=session
    )
    
    user_activity_today = await activity_repository.get_activity_today(
        session=session, 
        tg_id=callback.from_user.id, 
    )
    user_activity_today.circuits_created += 1

    text = await render_circuit_details(session, i18n, created_circuit)

    await present(
        callback, session=session, i18n=i18n, circuit=created_circuit,
        html=text, reply_markup=builder_circuit_manage(i18n, created_circuit.id),
    )
    await state.set_state(States.circuit_manage)

    if callback.from_user.id not in admin_ids:
        await bot.send_message(
            chat_id=admin_ids[0],
            text=i18n.admin_new_circuit_notification(
                user=format_user_link((user.id, user.username, user.first_name, user.last_name)),
                circuit_name=data['circuit_name'],
                num_qubits=num_qubits
            ),
            disable_web_page_preview=True,
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
    admin_ids: list,
    bot: Bot,
):
    data = await state.get_data()
    user = await user_repository.get_user(session, message.from_user.id)

    try:
        num_qubits = int(message.text)
        if num_qubits < 1 or num_qubits > UNIVERSAL_MAX_QUBITS:
            raise ValueError('Указанное количество кубитов вне диапазона 1-10')
    except Exception:
        await input_num_qubits_text_error_func(message, state, i18n)
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

    # Создание схемы (backend_id больше не передается)
    created_circuit: QuantumCircuit = await circuit_repository.create_circuit(
        tg_id=message.from_user.id, 
        circuit_name=data['circuit_name'], 
        num_qubits=num_qubits, 
        session=session, 
    )
    
    user_activity_today = await activity_repository.get_activity_today(
        session=session, 
        tg_id=message.from_user.id, 
    )
    user_activity_today.circuits_created += 1

    text = await render_circuit_details(session, i18n, created_circuit)

    await present(
        message, session=session, i18n=i18n, circuit=created_circuit,
        html=text, reply_markup=builder_circuit_manage(i18n, created_circuit.id),
    )
    await state.set_state(States.circuit_manage)

    if message.from_user.id not in admin_ids:
        await bot.send_message(
            chat_id=admin_ids[0],
            text=i18n.admin_new_circuit_notification(
                user=format_user_link((user.id, user.username, user.first_name, user.last_name)),
                circuit_name=data['circuit_name'],
                num_qubits=num_qubits
            ),
            disable_web_page_preview=True,
        )


# Хэндлер, отвечающий за обработку ошибки ввода количества кубитов текстом (вне лимитов)
@create_circuit_router.message(
    StateFilter(States.input_num_qubits),
)
async def input_num_qubits_text_error_func(
    message: Message, 
    state: FSMContext, 
    i18n: TranslatorRunner, 
):
    await message.answer(
        text=i18n.error_input_num_qubits(max_qubits=UNIVERSAL_MAX_QUBITS)
    )