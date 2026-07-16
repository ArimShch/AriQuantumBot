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
        text=i18n.menu_button(),
        callback_data="menu"
    )
    
    builder.adjust(2, 1)
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
    
    # Сортируем по ID для правильного порядка
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
        user_shots: int, 
):
    builder = InlineKeyboardBuilder()
    shots_values = [1, 10, 50, 100, 200, 
                    300, 500, 600, 800, 1000]
    
    for shots in shots_values:
        builder.button(
            text=("✅ " if shots == user_shots else "") + f"{shots}",
            callback_data=f"settings:simulation_shots:{shots}"
        )
    
    builder.adjust(3, 4, 3)
    builder.row(InlineKeyboardButton(text=i18n.back_button(), callback_data="back:settings"), 
                InlineKeyboardButton(text=i18n.menu_button(), callback_data="menu"))

    return builder.as_markup()

def builder_backend_menu(
    backends: list[Backend], 
    current_backend: int, 
    i18n: TranslatorRunner
) -> InlineKeyboardMarkup:
    """Меню выбора бэкенда"""
    builder = InlineKeyboardBuilder()
    
    for backend in backends:
        text = ("✅ " if backend.id == current_backend else "") + f"{backend.name} ({backend.max_qubits} {i18n.qubits()})" 
        builder.button(
            text=text,
            callback_data=f"settings:backend:{backend.id}"
        )
    
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text=i18n.back_button(), callback_data="back:settings"), 
                InlineKeyboardButton(text=i18n.menu_button(), callback_data="menu"))
    
    return builder.as_markup()