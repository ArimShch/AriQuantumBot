import logging
from fluentogram import TranslatorRunner

from aiogram import Router, F
from aiogram.types import CallbackQuery, InputRichMessage
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from ..filters.is_owner_circuit import IsCircuitOwner
from ..states.states import States
from ...infrastructure.database.repositories import user_repository, base_repository
from ..keyboards.settings_keyboards import (
    builder_settings_menu,
    builder_language_menu,
    builder_complexity_menu,
    builder_backend_menu,
    builder_simulation_shots, 
    builder_output_mode_menu,
)

logger = logging.getLogger(__name__)
settings_router = Router()


def get_settings_display_values(user_settings, i18n: TranslatorRunner, locale: str):
    """Вспомогательная функция для формирования отображаемых значений настроек"""
    automatic_name = i18n.bool_yes() if user_settings.automatic_name else i18n.bool_no()
    qubit_input_text = i18n.bool_yes() if user_settings.qubit_input_text else i18n.bool_no()
    
    complexity_levels_en_ru = {
        'Novice': 'Новичок', 
        'Student': 'Студент', 
        'Researcher': 'Исследователь', 
    }
    user_level = complexity_levels_en_ru[user_settings.complexity_level.name] if locale == 'ru' else user_settings.complexity_level.name

    backend_display = user_settings.backend.name if user_settings.backend else i18n.settings_ask_at_runtime()
    shots_display = str(user_settings.simulation_shots) if user_settings.simulation_shots else i18n.settings_ask_at_runtime()

    return {
        'language': f"{user_settings.language.emoji} {user_settings.language.name}",
        'complexity': f"{user_settings.complexity_level.emoji} {user_level}",
        'backend': backend_display,
        'automatic_name': automatic_name,
        'qubit_input_text': qubit_input_text,
        'simulation_shots': shots_display,
        'output_mode': (
            i18n.settings_output_mode_widget()
            if user_settings.output_mode == 'widget'
            else i18n.settings_output_mode_ascii()
        ),
    }


# Главное меню настроек
@settings_router.callback_query(F.data == "settings")
async def settings_menu(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
    locale: str, 
):
    user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
    values = get_settings_display_values(user_settings, i18n, locale)

    text = i18n.settings_menu(**values)

    await callback.message.edit_text(
        text=text,
        reply_markup=builder_settings_menu(i18n), 
    )
    await callback.answer()


# Меню выбора языка
@settings_router.callback_query(F.data == "settings:language")
async def settings_language_menu(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
):
    user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
    languages = await base_repository.get_languages(session)
    
    text = i18n.settings_language_menu(
        current=f"{user_settings.language.emoji} {user_settings.language.name}"
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=builder_language_menu(languages, user_settings.language_code, i18n)
    )
    await callback.answer()


# Выбор языка
@settings_router.callback_query(F.data.startswith("settings:language:"))
async def settings_language_select(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
    locale: str,
):
    language_code = callback.data.split(":")[2]
    
    user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
    user_settings.language_code = language_code
    await session.flush()
    await session.refresh(user_settings)
    
    values = get_settings_display_values(user_settings, i18n, locale)
    text = i18n.settings_menu(**values)

    await callback.message.edit_text(
        text=text,
        reply_markup=builder_settings_menu(i18n), 
    )
    await callback.answer(i18n.settings_language_updated())


# Меню выбора уровня сложности
@settings_router.callback_query(F.data == "settings:complexity")
async def settings_complexity_menu(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
    locale: str, 
):
    user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
    complexity_levels = await base_repository.get_complexity_level(session)
    
    values = get_settings_display_values(user_settings, i18n, locale)
    
    text = i18n.settings_complexity_menu(current=values['complexity'])
    
    await callback.message.edit_text(
        reply_markup=builder_complexity_menu(complexity_levels, user_settings.complexity_level_id, i18n, locale),
        rich_message=InputRichMessage(html=text),
    )
    await callback.answer()


# Выбор уровня сложности
@settings_router.callback_query(F.data.startswith("settings:complexity:"))
async def settings_complexity_select(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
    locale: str,
):
    complexity_id = int(callback.data.split(":")[2])
    
    user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
    user_settings.complexity_level_id = complexity_id
    await session.flush()
    await session.refresh(user_settings)

    values = get_settings_display_values(user_settings, i18n, locale)
    text = i18n.settings_menu(**values)

    await callback.message.edit_text(
        text=text,
        reply_markup=builder_settings_menu(i18n)
    )
    await callback.answer(i18n.settings_complexity_updated())


# Меню выбора бэкенда
@settings_router.callback_query(F.data == "settings:backend")
async def settings_backend_menu(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
):
    user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
    backends = await base_repository.get_backends(session)
    
    backend_display = user_settings.backend.name if user_settings.backend else i18n.settings_ask_at_runtime()
    
    text = i18n.settings_backend_menu(
        current=backend_display,
        complexity_level=user_settings.complexity_level.name 
    )
    
    await callback.message.edit_text(
        reply_markup=builder_backend_menu(backends, user_settings.backend_id, i18n), 
        rich_message=InputRichMessage(html=text)
    )
    await callback.answer()


# Выбор бэкенда (конкретный или 'ask')
@settings_router.callback_query(F.data.startswith("settings:backend:"))
async def settings_backend_select(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
    locale: str,
):
    backend_val = callback.data.split(":")[2]
    backend_id = None if backend_val == 'ask' else int(backend_val)
    
    user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
    user_settings.backend_id = backend_id
    await session.flush()
    await session.refresh(user_settings)
    
    values = get_settings_display_values(user_settings, i18n, locale)
    text = i18n.settings_menu(**values)

    await callback.message.edit_text(
        text=text,
        reply_markup=builder_settings_menu(i18n)
    )
    await callback.answer(i18n.settings_backend_updated())


# Переключение автоматического имени схемы
@settings_router.callback_query(F.data == "settings:automatic_name")
async def settings_toggle_automatic_name(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
    locale: str,
):
    user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
    user_settings.automatic_name = not user_settings.automatic_name
    await session.flush()
    await session.refresh(user_settings)
    
    values = get_settings_display_values(user_settings, i18n, locale)
    text = i18n.settings_menu(**values)

    await callback.message.edit_text(
        text=text,
        reply_markup=builder_settings_menu(i18n)
    )
    await callback.answer(i18n.settings_automatic_name_updated())


# Переключение ввода кубитов текстом
@settings_router.callback_query(F.data == "settings:qubit_input_text")
async def settings_toggle_qubit_input_text(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
    locale: str,
):
    user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
    user_settings.qubit_input_text = not user_settings.qubit_input_text
    await session.flush()
    await session.refresh(user_settings)
    
    values = get_settings_display_values(user_settings, i18n, locale)
    text = i18n.settings_menu(**values)

    await callback.message.edit_text(
        text=text,
        reply_markup=builder_settings_menu(i18n)
    )
    await callback.answer(i18n.settings_qubit_input_text_updated())


# Настройка количества запусков симуляции
@settings_router.callback_query(F.data == "settings:simulation_shots")
async def settings_simulation_shots_menu(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
):
    user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
    shots_display = str(user_settings.simulation_shots) if user_settings.simulation_shots else i18n.settings_ask_at_runtime()
    
    text = i18n.settings_simulation_shots_menu(current=shots_display)
    
    await callback.message.edit_text(
        text=text,
        reply_markup=builder_simulation_shots(
            i18n=i18n, 
            user_shots=user_settings.simulation_shots, 
        )
    )
    await callback.answer()


# Выбор количества запусков (число или 'ask')
@settings_router.callback_query(F.data.startswith("settings:simulation_shots:"))
async def settings_simulation_shots_select(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
    locale: str,
):
    shots_val = callback.data.split(":")[2]
    shots = None if shots_val == 'ask' else int(shots_val)
    
    user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
    user_settings.simulation_shots = shots
    await session.flush()
    await session.refresh(user_settings)
    
    values = get_settings_display_values(user_settings, i18n, locale)
    text = i18n.settings_menu(**values)

    await callback.message.edit_text(
        text=text,
        reply_markup=builder_settings_menu(i18n)
    )
    await callback.answer(i18n.settings_simulation_shots_updated())


# Меню выбора формата вывода графиков и схем
@settings_router.callback_query(F.data == "settings:output_mode")
async def settings_output_mode_menu(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
    locale: str,
):
    user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
    values = get_settings_display_values(user_settings, i18n, locale)

    await callback.message.edit_text(
        text=i18n.settings_output_mode_menu(current=values['output_mode']),
        reply_markup=builder_output_mode_menu(user_settings.output_mode, i18n),
    )
    await callback.answer()


# Выбор формата вывода ('widget' или 'ascii')
@settings_router.callback_query(F.data.regexp(r"^settings:output_mode:(widget|ascii)$"))
async def settings_output_mode_select(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
    locale: str,
):
    output_mode = callback.data.split(":")[2]

    user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
    user_settings.output_mode = output_mode
    await session.flush()
    await session.refresh(user_settings)

    values = get_settings_display_values(user_settings, i18n, locale)
    text = i18n.settings_menu(**values)

    await callback.message.edit_text(
        text=text,
        reply_markup=builder_settings_menu(i18n)
    )
    await callback.answer(i18n.settings_output_mode_updated())
