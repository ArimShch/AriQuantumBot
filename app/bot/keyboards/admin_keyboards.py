from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fluentogram import TranslatorRunner


def builder_admin_kb(
        i18n: TranslatorRunner, 
) -> InlineKeyboardMarkup:
    """Главное меню админки (кнопки пользователя объединены в одну)."""
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
    
    builder.adjust(2, 2, 1, 1)

    return builder.as_markup()


def builder_admin_users_menu_kb(
        i18n: TranslatorRunner,
) -> InlineKeyboardMarkup:
    """Общий раздел 'Пользователи': 3 функциональные кнопки + 'Админ меню'."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text=i18n.admin_users_activity_btn(),
        callback_data='admin:users:activity'
    )
    builder.button(
        text=i18n.admin_user_search_btn(),
        callback_data='admin:user'
    )
    builder.button(
        text=i18n.admin_users_new_stats_btn(),
        callback_data='admin:users:new_stats'
    )
    builder.button(
        text=i18n.admin_menu_btn(),
        callback_data='admin'
    )

    builder.adjust(1)
    return builder.as_markup()


def builder_back_admin_menu(
        i18n: TranslatorRunner, 
) -> InlineKeyboardMarkup:
    """Одиночная кнопка 'Админ меню'."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text=i18n.admin_menu_btn(),
        callback_data='admin'
    )
    builder.adjust(1)

    return builder.as_markup()


def builder_back_to_users_menu(
        i18n: TranslatorRunner,
) -> InlineKeyboardMarkup:
    """Две кнопки: 'Назад' (в 'Пользователи') и 'Админ меню'."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text=i18n.back_button(),
        callback_data='admin:users'
    )
    builder.button(
        text=i18n.admin_menu_btn(),
        callback_data='admin'
    )
    builder.adjust(2)

    return builder.as_markup()


def builder_admin_user_select_kb(
    users: list,
    i18n: TranslatorRunner,
) -> InlineKeyboardMarkup:
    """Клавиатура с цифрами при выборе из нескольких найденных юзеров."""
    builder = InlineKeyboardBuilder()

    for idx, user in enumerate(users, start=1):
        builder.button(
            text=str(idx),
            callback_data=f"admin:user:select:{user.id}"
        )
    
    builder.adjust(5)

    builder.row(
        InlineKeyboardButton(
            text=i18n.back_button(),
            callback_data="admin:users"
        ),
        InlineKeyboardButton(
            text=i18n.admin_menu_btn(),
            callback_data="admin"
        )
    )

    return builder.as_markup()


def builder_user_profile_keyboard(
    user_id: int, 
    is_blocked: bool, 
    i18n: TranslatorRunner
) -> InlineKeyboardMarkup:
    """Клавиатура профиля конкретного юзера (Блокировка/Разблокировка + Назад в 'Пользователи')."""
    builder = InlineKeyboardBuilder()
    if is_blocked:
        builder.button(
            text=i18n.admin_user_unblock_btn(),
            callback_data=f"admin:user:toggle_block:{user_id}"
        )
    else:
        builder.button(
            text=i18n.admin_user_block_btn(),
            callback_data=f"admin:user:toggle_block:{user_id}"
        )
    builder.button(text=i18n.back_button(), callback_data="admin:users")
    builder.button(text=i18n.admin_menu_btn(), callback_data="admin")
    builder.adjust(1, 2)
    return builder.as_markup()