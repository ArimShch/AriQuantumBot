from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fluentogram import TranslatorRunner


def builder_admin_kb(
        i18n: TranslatorRunner, 
):
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text=i18n.admin_users_btn(), 
        callback_data='admin:users', 
    )
    builder.button(
        text=i18n.admin_circuits_btn(), 
        callback_data='admin:circuits', 
    )
    builder.button(
        text=i18n.admin_backends_btn(), 
        callback_data='admin:backends', 
    )
    builder.button(
        text=i18n.admin_stat_btn(), 
        callback_data='admin:stat', 
    )
    builder.button(
        text=i18n.admin_blocked_btn(), 
        callback_data='admin:blocked', 
    )
    builder.button(
        text=i18n.admin_message_btn(), 
        callback_data='admin:message', 
    )
    
    builder.adjust(1)

    return builder.as_markup()


def builder_back_admin_menu(
        i18n: TranslatorRunner, 
):
    builder = InlineKeyboardBuilder()

    builder.button(
        text=i18n.admin_menu_btn(),
        callback_data='admin'
    )
    builder.adjust(1)

    return builder.as_markup()



