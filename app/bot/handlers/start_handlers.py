import logging
from fluentogram import TranslatorRunner

from aiogram import Bot, Router, F
from aiogram.enums import BotCommandScopeType
from aiogram.types import CallbackQuery, InputRichMessage, Message, BotCommandScopeChat
from aiogram.filters import CommandStart, Command, StateFilter, CommandObject
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from ...infrastructure.database.repositories import circuit_repository, user_repository
from ..states.states import States
from ..keyboards.settings_keyboards import builder_settings_menu
from ..keyboards.start_keyboards import builder_menu_keyboard, builder_choose_language, builder_help_keyboard
from ..keyboards.circuit_manage_keyboards import (
    builder_circuits_keyboard, 
    builder_circuit_manage, 
    builder_circuit_apply_gates, 
)
from ..utils.draw_circuit import draw_history
from ..utils.menu_keyboard import get_main_menu_commands
from ...infrastructure.database.models.models import User


logger = logging.getLogger(__name__)

start_router = Router()

# Хэндел, отвечающий за выбор языка при старте бота
@start_router.message(
        StateFilter(States.choose_language), 
)
async def choose_language_ignore_msg(
    message: Message, 
    state: FSMContext, 
    i18n: TranslatorRunner, 
    bot: Bot, 
):
    await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id - 1)

    await message.answer(
        text=i18n.choose_language(), 
        reply_markup=builder_choose_language(), 
    )

# Хэндлер, отвечающий за команду /start
@start_router.message(Command(commands=['start']))
async def start_bot_handler(
    message: Message, 
    command: CommandObject, 
    state: FSMContext, 
    bot: Bot, 
    admin_ids: list[int], 
    i18n: TranslatorRunner, 
    user_complexity_level: str, 
    is_new_user: bool, 
    session: AsyncSession, 
):
    if is_new_user:
        await message.answer(
            text=i18n.choose_language(), 
            reply_markup=builder_choose_language(), 
        )

        ref_source = command.args
        await user_repository.update_user_ref_source(
            session=session, 
            tg_id=message.from_user.id, 
            ref_source=ref_source, 
        )
    else:
        text = i18n.menu(complexity_level=user_complexity_level)
        
        await message.answer(
            text=text, 
            reply_markup=builder_menu_keyboard(i18n)
        )

        await state.set_state(States.menu)

    role = 'user'
    if message.from_user.id in admin_ids:
        role = 'admin'

    await bot.set_my_commands(
        commands=get_main_menu_commands(role, i18n), 
        scope=BotCommandScopeChat(
            type=BotCommandScopeType.CHAT, 
            chat_id=message.from_user.id), 
    )


@start_router.callback_query(
        F.data.startswith('lang:'), 
        StateFilter(States.choose_language)
)
async def choose_language_btn(
    callback: CallbackQuery, 
    session: AsyncSession, 
    state: FSMContext, 
    i18n: TranslatorRunner, 
    user_complexity_level: str, 
):
    user: User = await user_repository.get_user(session=session, tg_id=callback.from_user.id)
    user.setting.language_code = callback.data.split(':')[1]

    text = i18n.menu(complexity_level=user_complexity_level)
    
    await callback.message.edit_text(
        text=text, 
        reply_markup=builder_menu_keyboard(i18n)
    )

    await callback.answer(text=i18n.set_language())

    await state.set_state(States.menu)


@start_router.callback_query(
        StateFilter(States.choose_language), 
)
async def choose_language_callback_ignore(
    callback: CallbackQuery, 
):
    await callback.answer()


# Хэндлер, отвечающий за кнопку "Меню"
@start_router.callback_query(
    F.data == 'menu'
)
async def menu_button_func(
    callback: CallbackQuery, 
    state: FSMContext, 
    i18n: TranslatorRunner, 
    user_complexity_level: str, 
):
    text = i18n.menu(complexity_level=user_complexity_level)
    
    await callback.message.edit_text(
        text=text, 
        reply_markup=builder_menu_keyboard(i18n)
    )

    await state.set_state(States.menu)


@start_router.callback_query(
        F.data == 'answer_menu'
)
async def answer_menu_button_func(
    callback: CallbackQuery, 
    state: FSMContext, 
    i18n: TranslatorRunner, 
    user_complexity_level: str, 
):
    text = i18n.menu(complexity_level=user_complexity_level)
    
    await callback.message.answer(
        text=text, 
        reply_markup=builder_menu_keyboard(i18n)
    )

    await state.set_state(States.menu)
    await callback.answer()


@start_router.callback_query(
    F.data.startswith('back:')
)
async def back_button(
    callback: CallbackQuery, 
    session: AsyncSession, 
    state: FSMContext, 
    i18n: TranslatorRunner, 
    user_complexity_level: str, 
    locale: str,
):
    val = callback.data.split(':')[1]

    if val == 'circuits':
        user_circuits = await user_repository.get_user_circuits(
            session=session, 
            tg_id=callback.from_user.id, 
        )

        if user_circuits == []:
            text = i18n.my_circuits(have_circuits=False)
        else:
            text = i18n.my_circuits(have_circuits=True)

        await callback.message.edit_text(
            text=text, 
            reply_markup=builder_circuits_keyboard(
                i18n, user_circuits
            )
        )
    elif val == 'circuit'  or val == 'circuit_edit':
        circuit = await circuit_repository.get_circuit(
            session=session, 
            tg_id=callback.from_user.id, 
            circuit_id=int(callback.data.split(':')[2])
        )

        last_simulation = await circuit_repository.get_last_simulation_circuit(
            session=session, 
            circuit_id=int(callback.data.split(':')[2]), 
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
            backend=circuit.backend.name,
            state_vector=state_vector,
            has_simulation=has_simulation, 
        )

        await callback.message.edit_text(
            # text=text, 
            reply_markup=builder_circuit_manage(
                i18n, int(callback.data.split(':')[2])
            ), 
            rich_message=InputRichMessage(html=text)
        )
        await state.set_state(
            States.circuit_manage, 
        )
    elif val == 'circuit_gates':
            circuit = await circuit_repository.get_circuit(
                session=session, 
                tg_id=callback.from_user.id,
                circuit_id=int(callback.data.split(':')[2]),
            )
            
            # Очищаем данные состояния перед новым выбором
            await state.clear()
            await state.update_data(circuit_id=int(callback.data.split(':')[2]))
            
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
    elif val == 'settings': 
        user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
        
        automatic_name = i18n.bool_yes() if user_settings.automatic_name else i18n.bool_no(),
        qubit_input_text = i18n.bool_yes() if user_settings.qubit_input_text else i18n.bool_no(),
        
        complexity_levels_en_ru = {
            'Novice': 'Новичок', 
            'Student': 'Студент', 
            'Researcher': 'Исследователь', 
        }
        user_level = complexity_levels_en_ru[user_settings.complexity_level.name] if locale == 'ru' else user_settings.complexity_level.name

        text = i18n.settings_menu(
            language=user_settings.language.emoji + ' ' + user_settings.language.name,
            complexity=user_settings.complexity_level.emoji + ' ' + user_level,
            backend=user_settings.backend.name,
            automatic_name=automatic_name[0],
            qubit_input_text=qubit_input_text[0],
            simulation_shots=user_settings.simulation_shots,
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=builder_settings_menu(i18n)
        )
        await callback.answer()


# Хэндлер, отвечающий за команду /help
@start_router.message(
    Command('help')
)
async def cmnd_help_func(
    message: Message, 
    i18n: TranslatorRunner, 
):
    await message.answer_rich(
        rich_message=InputRichMessage(html=i18n.help_message()), 
        reply_markup=builder_help_keyboard(i18n)
    )
