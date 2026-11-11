import logging
from fluentogram import TranslatorRunner

from aiogram import Bot, Router, F
from aiogram.enums import BotCommandScopeType
from aiogram.types import CallbackQuery, InputRichMessage, Message, BotCommandScopeChat
from aiogram.filters import CommandStart, Command, StateFilter, CommandObject
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from ..handlers.settings_handlers import get_settings_display_values

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
from ..utils.circuit_view import render_circuit_details
from ..utils.circuit_screen import present, edit_screen
from ..utils.menu_keyboard import get_main_menu_commands
from ..utils.formatters_for_admin import format_user_link
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
    locale: str,
):
    if is_new_user:
        ref_source = command.args

        await message.answer(
            text=i18n.choose_language(), 
            reply_markup=builder_choose_language(), 
        )

        try:
            await _notify_admin_about_new_user(
                bot=bot,
                admin_id=admin_ids[0],
                message=message,
                ref_source=ref_source,
                locale=locale,
                i18n=i18n,
            )
        except Exception as e:
            # Логируем ошибку уведомления, но НЕ прерываем основной flow
            logger.warning(f"Failed to notify admin about new user: {e}")

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

        # Схема не менялась: в режиме виджета обновится только текст под ним
        text = await render_circuit_details(session, i18n, circuit)

        await present(
            callback, session=session, i18n=i18n, circuit=circuit,
            html=text, reply_markup=builder_circuit_manage(
                i18n, int(callback.data.split(':')[2])
            ),
            circuit_changed=False,
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

            await edit_screen(
                callback,
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
        values = get_settings_display_values(user_settings, i18n, locale)
    
        text = i18n.settings_menu(**values)
    
        await callback.message.edit_text(
            text=text,
            reply_markup=builder_settings_menu(i18n), 
        )
        await callback.answer()
    elif val == 'templates':
        from ..keyboards.templates_keyboards import builder_templates_list
        await callback.message.edit_text(
            rich_message=InputRichMessage(html=i18n.templates_list_title()),
            reply_markup=builder_templates_list(i18n, locale)
        ) 


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


async def _notify_admin_about_new_user(
    bot: Bot,
    admin_id: int,
    message: Message,
    ref_source: str | None,
    locale: str,
    i18n: TranslatorRunner,
) -> None:
    """Отправляет админу уведомление о новом пользователе."""
    user = message.from_user
    
    # Собираем всю информацию
    user_link = format_user_link((user.id, user.username, user.first_name, user.last_name))  # твоя функция
    user_id = str(user.id)
    username = f"@{user.username}" if user.username else "—"
    full_name = user.full_name or "—"
    source_display = ref_source if ref_source else 'direct'
    
    # Флаги языков (опционально, для красоты)
    lang_flag = {
        'ru': '🇷🇺',
        'en': '🇬🇧', 
        'uk': '🇺🇦',
        'by': '🇧🇾',
        'de': '🇩🇪',
        'fr': '🇫🇷',
        'es': '🇪🇸',
        'it': '🇮🇹',
        'cn': '🇨🇳',
        'jp': '🇯🇵',
    }.get(locale.lower(), '🌍')
    
    text = i18n.admin_new_user_notification(
        user_link=user_link,
        user_id=user_id,
        username=username,
        full_name=full_name,
        source=source_display,
        locale_flag=lang_flag,
        locale_code=locale or "—",
    )

    try:
        await bot.send_message(
            chat_id=admin_id,
            text=text,
            disable_web_page_preview=True,
        )
    except Exception:
        # Админ заблокировал бота или бот не может писать админу
        logger.warning(f"Cannot notify admin {admin_id}: bot is blocked or not started")
