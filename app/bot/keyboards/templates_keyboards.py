from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fluentogram import TranslatorRunner

from ..utils.templates_data import TEMPLATES

def builder_templates_list(i18n: TranslatorRunner, locale: str) -> InlineKeyboardMarkup:
    """Выводит список всех шаблонов (каждый в новой строке)"""
    builder = InlineKeyboardBuilder()

    for template_id, data in TEMPLATES.items():
        name = data["name_ru"] if locale == "ru" else data["name_en"]
        builder.button(
            text=name,
            callback_data=f"templates:{template_id}"
        )
    
    builder.button(
        text=i18n.menu_button(),
        callback_data="menu"
    )

    # 1 кнопка в ряд
    builder.adjust(2, 1)
    return builder.as_markup()


def builder_template_details(template_id: int, i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    """Клавиатура внутри конкретного шаблона"""
    builder = InlineKeyboardBuilder()

    builder.button(
        text=i18n.template_create_btn(),
        callback_data=f"templates:{template_id}:create"
    )
    
    # Кнопки Назад и Меню в один ряд
    builder.button(text=i18n.back_button(), callback_data="back:templates")
    builder.button(text=i18n.menu_button(), callback_data="menu")
    
    builder.adjust(1, 2)
    return builder.as_markup()