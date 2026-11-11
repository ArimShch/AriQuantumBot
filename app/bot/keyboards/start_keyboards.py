from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from fluentogram import TranslatorRunner

# Клавиатура для выбора языка 
def builder_choose_language():
    builder = InlineKeyboardBuilder()

    builder.button(
        text='🇷🇺 Русский', 
        callback_data='lang:ru', 
    )
    builder.button(
        text='🇬🇧 English', 
        callback_data='lang:en',
    )
    builder.adjust(1)

    return builder.as_markup()


# Клавиатура для главного раздела /start
def builder_menu_keyboard(i18n: TranslatorRunner):
    builder = InlineKeyboardBuilder()

    builder.button(
        text=i18n.get('menu_profile_button'), 
        callback_data='profile', 
    )
    builder.button(
        text=i18n.get('menu_circuit_button'), 
        callback_data='circuits',
    ) 
    builder.button(
        text=i18n.get('menu_settings_button'), 
        callback_data='settings', 
    )
    builder.button(
        text=i18n.get('menu_template_button'), 
        callback_data='templates',
    ) 
    builder.adjust(2)

    return builder.as_markup()


# Клавиатура для текста /help
def builder_help_keyboard(i18n: TranslatorRunner):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=i18n.menu_button(),
        callback_data="menu"
    )
    builder.adjust(1)

    return builder.as_markup()

