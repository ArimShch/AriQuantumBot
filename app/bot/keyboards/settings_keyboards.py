from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fluentogram import TranslatorRunner

from ...infrastructure.database.models.models import Language, ComplexityLevel, Backend


def builder_settings_menu(i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    """Главное меню настроек"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text=i18n.settings_language_button(),
        callback_data="settings:language"
    )
    builder.button(
        text=i18n.settings_backend_button(),
        callback_data="settings:backend"
    )
    builder.button(
        text=i18n.settings_complexity_button(),
        callback_data="settings:complexity"
    )
    builder.button(
        text=i18n.settings_automatic_name_button(),
        callback_data="settings:automatic_name"
    )
    builder.button(
        text=i18n.settings_qubit_input_text_button(),
        callback_data="settings:qubit_input_text"
    )
    builder.button(
        text=i18n.settings_simulation_shots_button(),
        callback_data="settings:simulation_shots"
    )
    builder.button(
        text=i18n.settings_output_mode_button(),
        callback_data="settings:output_mode"
    )
    builder.button(
        text=i18n.menu_button(),
        callback_data="menu"
    )
    
    builder.adjust(2, 1)  # как было: 1-й ряд — 2 кнопки, остальные по одной в ряд
    return builder.as_markup()


def builder_language_menu(
    languages: list[Language], 
    current_language: str, 
    i18n: TranslatorRunner
) -> InlineKeyboardMarkup:
    """Меню выбора языка"""
    builder = InlineKeyboardBuilder()

    for lang in languages:
        text = ("✅ " if lang.code == current_language else "") + f"{lang.emoji} {lang.name}"
        builder.button(
            text=text,
            callback_data=f"settings:language:{lang.code}"
        )
    
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text=i18n.back_button(), callback_data="back:settings"), 
                InlineKeyboardButton(text=i18n.menu_button(), callback_data="menu"))
    
    return builder.as_markup()


def builder_complexity_menu(
    complexity_levels: list[ComplexityLevel], 
    current_complexity: int, 
    i18n: TranslatorRunner, 
    locale: str, 
) -> InlineKeyboardMarkup:
    """Меню выбора уровня сложности"""
    builder = InlineKeyboardBuilder()
    
    sorted_levels = sorted(complexity_levels, key=lambda x: x.id)

    complexity_levels_en_ru = {
        'Novice': 'Новичок', 
        'Student': 'Студент', 
        'Researcher': 'Исследователь', 
    }
    
    for level in sorted_levels:
        if locale == 'en':
            text = ("✅ " if level.id == current_complexity else "") + f"{level.emoji} {level.name}"
        else:
            text = ("✅ " if level.id == current_complexity else "") + f"{level.emoji} {complexity_levels_en_ru[level.name]}"

        builder.button(
            text=text,
            callback_data=f"settings:complexity:{level.id}"
        )
    
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text=i18n.back_button(), callback_data="back:settings"), 
                InlineKeyboardButton(text=i18n.menu_button(), callback_data="menu"))
    
    return builder.as_markup()


def builder_simulation_shots(
        i18n: TranslatorRunner, 
        user_shots: int | None, 
) -> InlineKeyboardMarkup:
    """Меню выбора количества запусков (shots)"""
    builder = InlineKeyboardBuilder()
    shots_values = [1, 10, 50, 100, 200, 
                    300, 500, 600, 800, 1000]
    
    for shots in shots_values:
        builder.button(
            text=("✅ " if shots == user_shots else "") + f"{shots}",
            callback_data=f"settings:simulation_shots:{shots}"
        )
    
    # Кнопка "Спрашивать при запуске"
    builder.button(
        text=("✅ " if user_shots is None else "") + i18n.settings_ask_at_runtime(),
        callback_data="settings:simulation_shots:ask"
    )
    
    builder.adjust(4, 3, 3, 1)  # Последняя 1 для широкой кнопки выбора при запуске
    builder.row(InlineKeyboardButton(text=i18n.back_button(), callback_data="back:settings"), 
                InlineKeyboardButton(text=i18n.menu_button(), callback_data="menu"))

    return builder.as_markup()


def builder_backend_menu(
    backends: list[Backend], 
    current_backend: int | None, 
    i18n: TranslatorRunner
) -> InlineKeyboardMarkup:
    """Меню выбора бэкенда"""
    builder = InlineKeyboardBuilder()
    
    for backend in backends:
        text = ("✅ " if backend.id == current_backend else "") + f"{backend.name}" 
        builder.button(
            text=text,
            callback_data=f"settings:backend:{backend.id}"
        )
    
    # Кнопка "Спрашивать при запуске"
    builder.button(
        text=("✅ " if current_backend is None else "") + i18n.settings_ask_at_runtime(),
        callback_data="settings:backend:ask"
    )
    
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text=i18n.back_button(), callback_data="back:settings"), 
                InlineKeyboardButton(text=i18n.menu_button(), callback_data="menu"))
    
    return builder.as_markup()


def builder_output_mode_menu(
    current_mode: str,
    i18n: TranslatorRunner
) -> InlineKeyboardMarkup:
    """Меню выбора формата вывода графиков и схем"""
    builder = InlineKeyboardBuilder()

    builder.button(
        text=("✅ " if current_mode == 'widget' else "") + i18n.settings_output_mode_widget(),
        callback_data="settings:output_mode:widget"
    )
    builder.button(
        text=("✅ " if current_mode == 'ascii' else "") + i18n.settings_output_mode_ascii(),
        callback_data="settings:output_mode:ascii"
    )

    builder.adjust(1)
    builder.row(InlineKeyboardButton(text=i18n.back_button(), callback_data="back:settings"),
                InlineKeyboardButton(text=i18n.menu_button(), callback_data="menu"))

    return builder.as_markup()
