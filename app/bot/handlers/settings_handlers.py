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
)


logger = logging.getLogger(__name__)
settings_router = Router()


# Главное меню настроек
@settings_router.callback_query(F.data == "settings")
async def settings_menu(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
    locale: str, 
):
    """Показывает главное меню настроек"""
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
        simulation_shots=str(user_settings.simulation_shots),
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=builder_settings_menu(i18n), 
        # rich_message=InputRichMessage(html=text)
    )
    await callback.answer()


# Меню выбора языка
@settings_router.callback_query(F.data == "settings:language")
async def settings_language_menu(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
):
    """Показывает меню выбора языка"""
    user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
    
    languages = await base_repository.get_languages(session)
    
    text = i18n.settings_language_menu(
        current=user_settings.language.emoji + ' ' + user_settings.language.name
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=builder_language_menu(
            languages, 
            user_settings.language_code, 
            i18n,
        )
    )
    await callback.answer()


# Выбор языка
@settings_router.callback_query(F.data.startswith("settings:language:"))
async def settings_language_select(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
):
    """Обрабатывает выбор языка"""
    language_code = callback.data.split(":")[2]
    
    # Обновляем настройки пользователя
    user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
    user_settings.language_code = language_code
    await session.flush()
    await session.refresh(user_settings)
    
    automatic_name = i18n.bool_yes() if user_settings.automatic_name else i18n.bool_no(),
    qubit_input_text = i18n.bool_yes() if user_settings.qubit_input_text else i18n.bool_no(),
    
    text = i18n.settings_menu(
        language=user_settings.language.emoji + ' ' + user_settings.language.name,
        complexity=user_settings.complexity_level.emoji + ' ' + user_settings.complexity_level.name,
        backend=user_settings.backend.name,
        automatic_name=automatic_name[0],
        qubit_input_text=qubit_input_text[0],
        simulation_shots=str(user_settings.simulation_shots),
    )

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
    """Показывает меню выбора уровня сложности"""
    user_settings = await user_repository.get_user_settings(session, callback.from_user.id)

    complexity_levels = await base_repository.get_complexity_level(session)
    
    complexity_levels_en_ru = {
        'Novice': 'Новичок', 
        'Student': 'Студент', 
        'Researcher': 'Исследователь', 
    }

    user_level = complexity_levels_en_ru[user_settings.complexity_level.name] if locale == 'ru' else user_settings.complexity_level.name

    text = i18n.settings_complexity_menu(current=user_settings.complexity_level.emoji + ' ' + user_level)
    
    await callback.message.edit_text(
        # text=text,
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
    """Обрабатывает выбор уровня сложности"""
    complexity_id = int(callback.data.split(":")[2])
    
    user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
    user_settings.complexity_level_id = complexity_id
    await session.flush()
    await session.refresh(user_settings)

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
        simulation_shots=str(user_settings.simulation_shots),
    )

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
    """Показывает меню выбора бэкенда"""
    user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
    
    backends = await base_repository.get_backends(session)
    
    text = i18n.settings_backend_menu(
        current=user_settings.backend.name,
        complexity_level=user_settings.complexity_level.name 
    )
    
    await callback.message.edit_text(
        # text=text,
        reply_markup=builder_backend_menu(backends, user_settings.backend_id, i18n), 
        rich_message=InputRichMessage(html=text)
    )
    await callback.answer()


# Выбор бэкенда
@settings_router.callback_query(F.data.startswith("settings:backend:"))
async def settings_backend_select(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
):
    """Обрабатывает выбор бэкенда"""
    backend_id = int(callback.data.split(":")[2])
    
    user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
    user_settings.backend_id = backend_id
    await session.flush()
    await session.refresh(user_settings)
    
    automatic_name = i18n.bool_yes() if user_settings.automatic_name else i18n.bool_no(),
    qubit_input_text = i18n.bool_yes() if user_settings.qubit_input_text else i18n.bool_no(),

    text = i18n.settings_menu(
        language=user_settings.language.emoji + ' ' + user_settings.language.name,
        complexity=user_settings.complexity_level.emoji + ' ' + user_settings.complexity_level.name,
        backend=user_settings.backend.name,
        automatic_name=automatic_name[0],
        qubit_input_text=qubit_input_text[0],
        simulation_shots=str(user_settings.simulation_shots),
    )

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
):
    """Переключает автоматическое имя схемы"""
    user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
    user_settings.automatic_name = not user_settings.automatic_name
    await session.flush()
    await session.refresh(user_settings)
    
    automatic_name = i18n.bool_yes() if user_settings.automatic_name else i18n.bool_no(),
    qubit_input_text = i18n.bool_yes() if user_settings.qubit_input_text else i18n.bool_no(),

    text = i18n.settings_menu(
        language=user_settings.language.emoji + ' ' + user_settings.language.name,
        complexity=user_settings.complexity_level.emoji + ' ' + user_settings.complexity_level.name,
        backend=user_settings.backend.name,
        automatic_name=automatic_name[0],
        qubit_input_text=qubit_input_text[0],
        simulation_shots=str(user_settings.simulation_shots),
    )

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
):
    """Переключает ввод количества кубитов текстом"""
    user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
    user_settings.qubit_input_text = not user_settings.qubit_input_text
    await session.flush()
    await session.refresh(user_settings)
    
    automatic_name = i18n.bool_yes() if user_settings.automatic_name else i18n.bool_no(),
    qubit_input_text = i18n.bool_yes() if user_settings.qubit_input_text else i18n.bool_no(),

    text = i18n.settings_menu(
        language=user_settings.language.emoji + ' ' + user_settings.language.name,
        complexity=user_settings.complexity_level.emoji + ' ' + user_settings.complexity_level.name,
        backend=user_settings.backend.name,
        automatic_name=automatic_name[0],
        qubit_input_text=qubit_input_text[0],
        simulation_shots=str(user_settings.simulation_shots),
    )

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
    """Показывает меню настройки количества запусков"""
    user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
    
    text = i18n.settings_simulation_shots_menu(current=str(user_settings.simulation_shots))
    
    await callback.message.edit_text(
        text=text,
        reply_markup=builder_simulation_shots(
            i18n=i18n, 
            user_shots=user_settings.simulation_shots, 
        )
    )
    await callback.answer()


# Выбор количества запусков
@settings_router.callback_query(F.data.startswith("settings:simulation_shots:"))
async def settings_simulation_shots_select(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
):
    """Обрабатывает выбор количества запусков"""
    shots = int(callback.data.split(":")[2])
    
    user_settings = await user_repository.get_user_settings(session, callback.from_user.id)
    user_settings.simulation_shots = shots
    await session.flush()
    await session.refresh(user_settings)
    
    automatic_name = i18n.bool_yes() if user_settings.automatic_name else i18n.bool_no(),
    qubit_input_text = i18n.bool_yes() if user_settings.qubit_input_text else i18n.bool_no(),

    text = i18n.settings_menu(
        language=user_settings.language.emoji + ' ' + user_settings.language.name,
        complexity=user_settings.complexity_level.emoji + ' ' + user_settings.complexity_level.name,
        backend=user_settings.backend.name,
        automatic_name=automatic_name[0],
        qubit_input_text=qubit_input_text[0],
        simulation_shots=str(user_settings.simulation_shots),
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=builder_settings_menu(i18n)
    )
    await callback.answer(i18n.settings_simulation_shots_updated())


