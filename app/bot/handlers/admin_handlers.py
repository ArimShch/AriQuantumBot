from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from fluentogram import TranslatorRunner

from ...infrastructure.database.repositories import activity_repository, user_repository, base_repository
from ..filters.is_admin import IsAdmin
from ..keyboards.admin_keyboards import (
    builder_admin_kb, builder_back_admin_menu
)
from ..states.states import States
from ..utils.broadcast import broadcast_to_all_users

import asyncio

admin_router = Router()


@admin_router.message(
    IsAdmin(), 
    Command(commands=['admin']), 
)
async def command_admin_func(
    message: Message, 
    session: AsyncSession, 
    i18n: TranslatorRunner, 
):
    await message.answer(
        text=i18n.command_admin(), 
        reply_markup=builder_admin_kb(i18n), 
    )


@admin_router.callback_query(
        IsAdmin(), 
        F.data == 'admin'
)
async def admin_menu_btn_func(
    callback: CallbackQuery, 
    i18n: TranslatorRunner, 
):
    await callback.message.edit_text(
        text=i18n.command_admin(), 
        reply_markup=builder_admin_kb(i18n), 
    )


@admin_router.callback_query(
    IsAdmin(), 
    F.data == 'admin:users', 
)
async def admin_users_btn_func(
    callback: CallbackQuery, 
    session: AsyncSession, 
    i18n: TranslatorRunner, 
):
    count_users = await activity_repository.get_count_users(session)
    stat_users20 = await activity_repository.get_user_activity_last_20_days(session)
    top5_days = await activity_repository.get_top_10_user_activity_days(session)
    top5_circuits = await activity_repository.get_top_10_user_activity_circuits(session)
    top5_simulations = await activity_repository.get_top_10_user_activity_simulations(session)

    # print(stat_users10)

    text_stat_users20 = "\n".join([
        f"• {date.strftime('%d.%m')}: {count}" 
        for date, count in stat_users20
    ])

    top5_days_text = "\n".join([
        f"{i}. @{user[0]} | ⏱️ {user[1]}" 
        for i, user in enumerate(top5_days, 1)
    ])

    top5_circuits_text = "\n".join([
        f"{i}. @{user[0]} | ⛓️ {user[1]}" 
        for i, user in enumerate(top5_circuits, 1)
    ])

    top5_simulations_text = "\n".join([
        f"{i}. @{user[0]} | 🚀 {user[1]}" 
        for i, user in enumerate(top5_simulations, 1)
    ])


    await callback.message.edit_text(
        text=i18n.admin_users(
                all_users=count_users, 
                stat_users20=text_stat_users20, 
                top5_days_text=top5_days_text, 
                top5_circuits_text=top5_circuits_text, 
                top5_simulations_text=top5_simulations_text,
        ),
        reply_markup=builder_back_admin_menu(i18n)
    )


@admin_router.callback_query(
    IsAdmin(), 
    F.data == 'admin:circuits', 
)
async def admin_circuits_btn_func(
    callback: CallbackQuery, 
    session: AsyncSession, 
    i18n: TranslatorRunner, 
):
    count_circuits_now = await activity_repository.get_count_circuits_now(
        session
    )
    count_circuits_all = await activity_repository.get_count_circuits_all(
        session
    )
    count_simulations_now = await activity_repository.get_count_simulations_now(
        session
    )
    count_simulations_all = await activity_repository.get_count_simulations_all(
        session 
    )
    stat_circuits20 = await activity_repository.get_circuits_activity_last_20_days(
        session
    )
    avg_qubits = await activity_repository.get_avg_count_qubits(session)
    avg_qubits = avg_qubits if avg_qubits else 0
    avg_time = await activity_repository.get_avg_time(session) 
    avg_time = avg_time if avg_time else 0

    text_stat_citcuits20 = "\n".join([
        f"• {date.strftime('%d.%m')}: ⛓️ {circuits} | 🚀 {simulations}" 
        for date, circuits, simulations in stat_circuits20
    ])
    # print(avg_time)

    await callback.message.edit_text(
        text=i18n.admin_circuits(
            circuits_now=count_circuits_now, 
            circuits_all=count_circuits_all, 
            simulations_now=count_simulations_now, 
            simulations_all=count_simulations_all, 
            stat_circuits20=text_stat_citcuits20, 
            avg_qubits=str(round(avg_qubits, 2)), 
            avg_time=str(round(avg_time, 5)), 
        ), 
        reply_markup=builder_back_admin_menu(i18n), 
    )


@admin_router.callback_query(
    IsAdmin(), 
    F.data == 'admin:backends', 
)
async def admin_backends_btn_func(
    callback: CallbackQuery, 
    session: AsyncSession, 
    i18n: TranslatorRunner, 
):
    backends_circuits = await activity_repository.get_circuits_by_backends(session)
    backends_simulations = await activity_repository.get_simulations_by_backends(session)
    backends_avg_qubits = await activity_repository.get_avg_qubits_by_backends(session)
    backend_avg_time = await activity_repository.get_avg_time_simulations_by_backends(session)

    backends_circuits_text = "\n".join([
        f"• {backend}: ⛓️ {circuits}" 
        for backend, circuits in backends_circuits
    ])

    backends_simulations_text = "\n".join([
        f"• {backend}: ⛓️ {simulations}" 
        for backend, simulations in backends_simulations
    ])

    backends_avg_qubits_text = "\n".join([
        f"• {backend}: ⛓️ {round(qubits, 2)}" 
        for backend, qubits in backends_avg_qubits
    ])

    backends_avg_time_text = "\n".join([
        f"• {backend}: ⛓️ {round(time, 5)} сек." 
        for backend, time in backend_avg_time
    ])

    await callback.message.edit_text(
        text=i18n.admin_backends(
            backends_circuits_text=backends_circuits_text, 
            backends_simulations_text=backends_simulations_text, 
            backends_avg_qubits_text=backends_avg_qubits_text, 
            backends_avg_time_text=backends_avg_time_text, 
        ), 
        reply_markup=builder_back_admin_menu(i18n)
    )


@admin_router.callback_query(F.data == "admin:stat", IsAdmin())
async def admin_statistics_handler(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
):
    from ...infrastructure.database.repositories import activity_repository

    # Получаем все статистики
    lang_stats = await activity_repository.get_users_by_language(session)
    complexity_stats = await activity_repository.get_users_by_complexity_level(session)
    backend_stats = await activity_repository.get_users_by_backend(session)
    auto_name_stats = await activity_repository.get_automatic_name_stats(session)
    qubit_input_stats = await activity_repository.get_qubit_input_text_stats(session)
    shots_stats = await activity_repository.get_simulation_shots_distribution(session)
    shots_avg = await activity_repository.get_avg_simulation_shots_distribution(session)
    ref_stats = await activity_repository.get_users_by_ref_source(session)
    tg_locale_stats = await activity_repository.get_users_by_tg_locale(session)

    # Форматируем данные
    def format_bool_stats(stats):
        enabled = next((count for value, count in stats if value), 0)
        disabled = next((count for value, count in stats if not value), 0)
        return f"Включено: {enabled}\nВыключено: {disabled}"

    lang_text = "\n".join([f"• {emoji} {name}: {count}" for emoji, name, count in lang_stats]) or "—"
    complexity_text = "\n".join([f"• {emoji} {name}: {count}" for emoji, name, count in complexity_stats]) or "—"
    backend_text = "\n".join([f"• {name}: {count}" for name, count in backend_stats]) or "—"
    auto_name_text = format_bool_stats(auto_name_stats)
    qubit_input_text = format_bool_stats(qubit_input_stats)
    shots_text = "\n".join([f"• {shots}: {count}" for shots, count in shots_stats]) or "—"
    ref_text = "\n".join([f"• {source}: {count}" for source, count in ref_stats]) or "—"
    tg_locale_text = "\n".join([f"• {locale.upper()}: {count}" for locale, count in tg_locale_stats]) or "—"

    text = i18n.admin_statistics(
        languages=lang_text,
        complexity_levels=complexity_text,
        backends=backend_text,
        automatic_name=auto_name_text,
        qubit_input=qubit_input_text,
        simulation_shots=shots_text,
        shots_avg=shots_avg, 
        ref_sources=ref_text,
        tg_locales=tg_locale_text,
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=builder_back_admin_menu(i18n)
    )
    await callback.answer()


@admin_router.callback_query(
        F.data == "admin:blocked", 
        IsAdmin()
)
async def admin_block_start(
    callback: CallbackQuery, 
    state: FSMContext, 
    i18n: TranslatorRunner
):
    """Начало процесса блокировки"""
    await callback.message.edit_text(i18n.admin_block_prompt(), reply_markup=builder_back_admin_menu(i18n))
    await state.set_state(States.waiting_for_block_input)
    await callback.answer()


@admin_router.message(
        StateFilter(States.waiting_for_block_input), 
        IsAdmin()
)
async def admin_block_process(
    message: Message, 
    state: FSMContext, 
    session: AsyncSession, 
    i18n: TranslatorRunner
):
    """Обработка ввода ID или username"""
    input_text = message.text.strip()
    
    success = False
    user_info = ""

    if input_text.isdigit():
        # Это ID
        user_id = int(input_text)
        success = await user_repository.block_user_by_id(session, user_id)
        user_info = f"ID: {user_id}"
    else:
        # Это username (удаляем @ если есть)
        username = input_text.lstrip('@')
        user = await user_repository.get_user_by_username(session, username)
        if user:
            success = await user_repository.block_user_by_username(session, username)
            user_info = f"@{username} (ID: {user.id})"
        else:
            success = False

    if success:
        response = i18n.admin_block_success(user=user_info)
        await state.clear()
    else:
        response = i18n.admin_block_not_found(user=input_text)

    await message.answer(response)
    


@admin_router.callback_query(F.data == "admin:message", IsAdmin())
async def admin_broadcast_start(
    callback: CallbackQuery, 
    state: FSMContext, 
    i18n: TranslatorRunner
):
    """Запрос текста для рассылки"""
    await state.set_state(States.waiting_for_broadcast_message)
    await callback.message.edit_text(i18n.admin_broadcast_prompt())
    await callback.answer()


@admin_router.message(
    States.waiting_for_broadcast_message, 
    IsAdmin()
)
async def admin_broadcast_process(
    message: Message, 
    state: FSMContext, 
    session: AsyncSession, 
    i18n: TranslatorRunner
):
    """Получение текста и запуск рассылки"""
    broadcast_text = message.text.strip()
    if not broadcast_text:
        await message.answer(i18n.admin_broadcast_empty())
        return

    await state.clear()
    await message.answer(i18n.admin_broadcast_started())

    users = await base_repository.get_all_users(session)

    # Запускаем фоновую рассылку (не блокирует бота)
    asyncio.create_task(
        broadcast_to_all_users(
            text=broadcast_text,
            users=users,
            admin_chat_id=message.from_user.id,
            bot=message.bot
        )
    )