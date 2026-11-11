import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InputRichMessage
from aiogram.filters import Command, StateFilter
from aiogram.utils.text_decorations import html_decoration as hd
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from fluentogram import TranslatorRunner

from ...infrastructure.database.repositories import (
    activity_repository, user_repository, base_repository, user_stat_repository
)
from ...infrastructure.database.models.models import UserActivityLog
from ..filters.is_admin import IsAdmin
from ..keyboards.admin_keyboards import (
    builder_admin_kb, 
    builder_admin_users_menu_kb,
    builder_admin_user_select_kb, 
    builder_back_admin_menu, 
    builder_back_to_users_menu,
    builder_user_profile_keyboard
)
from ..states.states import States
from ..utils.broadcast import broadcast_to_all_users
from ..utils.formatters_for_admin import format_user_link

admin_router = Router()


# === ГЛАВНОЕ АДМИН-МЕНЮ ===

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


# === ОБЩИЙ РАЗДЕЛ "ПОЛЬЗОВАТЕЛИ" ===

@admin_router.callback_query(
    IsAdmin(), 
    F.data == 'admin:users', 
)
async def admin_users_main_section(
    callback: CallbackQuery, 
    i18n: TranslatorRunner, 
):
    """Объединенное меню раздела «Пользователи»"""
    await callback.message.edit_text(
        text=i18n.admin_users_section_title(),
        reply_markup=builder_admin_users_menu_kb(i18n),
    )
    await callback.answer()


# === 1. ПОДРАЗДЕЛ: АКТИВНОСТЬ ПОЛЬЗОВАТЕЛЕЙ ===

@admin_router.callback_query(
    IsAdmin(), 
    F.data == 'admin:users:activity', 
)
async def admin_users_activity_btn_func(
    callback: CallbackQuery, 
    session: AsyncSession, 
    i18n: TranslatorRunner, 
):
    count_users = await activity_repository.get_count_users(session)
    stat_users20 = await activity_repository.get_user_activity_last_20_days(session)
    top5_days = await activity_repository.get_top_10_user_activity_days(session)
    top5_circuits = await activity_repository.get_top_10_user_activity_circuits(session)
    top5_simulations = await activity_repository.get_top_10_user_activity_simulations(session)

    text_stat_users20 = "\n".join([
        f"• {date.strftime('%d.%m')}: {count}" 
        for date, count in stat_users20
    ])

    top5_days_text = "\n".join([
        f"{i}. {format_user_link(user)} | ⏱️ {user[4] or 0}" 
        for i, user in enumerate(top5_days, 1)
    ])

    top5_circuits_text = "\n".join([
        f"{i}. {format_user_link(user)} | ⛓️ {user[4] or 0}" 
        for i, user in enumerate(top5_circuits, 1)
    ])

    top5_simulations_text = "\n".join([
        f"{i}. {format_user_link(user)} | 🚀 {user[4] or 0}" 
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
        reply_markup=builder_back_to_users_menu(i18n),
        disable_web_page_preview=True,
    )


# === 2. ПОДРАЗДЕЛ: НОВЫЕ РЕГИСТРАЦИИ ПО ДНЯМ ===

@admin_router.callback_query(
    IsAdmin(), 
    F.data == 'admin:users:new_stats', 
)
async def admin_users_new_stats_func(
    callback: CallbackQuery, 
    session: AsyncSession, 
    i18n: TranslatorRunner, 
):
    """Вывод регистраций по датам в формате 'дата: +N'"""
    # Предполагается, что в activity_repository есть соответствующий метод
    # Возвращающий список [(date_obj, count), ...]
    new_users_by_date = await activity_repository.get_new_users_by_date(session)

    lines = []
    for dt, count in new_users_by_date:
        lines.append(f"• <b>{dt.strftime('%d.%m.%Y')}</b>: +{count}")

    text = i18n.admin_users_new_stats_text(
        stats_list="\n".join(lines) if lines else i18n.admin_user_no_circuits()
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=builder_back_to_users_menu(i18n),
    )
    await callback.answer()


# === 3. ПОДРАЗДЕЛ: ПОИСК ПОЛЬЗОВАТЕЛЯ И ВЫВОД ПРОФИЛЯ ===

async def _build_profile_text(
    user, i18n: TranslatorRunner, session: AsyncSession
) -> str:
    """Собирает все данные и передаёт их в единый Fluent-шаблон"""
    setting = user.setting

    # === 1. Схемы (Убрали вывод бэкенда схемы) ===
    circuits_with_stats = await user_stat_repository.get_user_circuits_with_stats(session, user.id)
    circuits_count = len(circuits_with_stats)

    circuits_lines = []
    for circuit, sim_count in circuits_with_stats[:10]:
        gates_count = len(circuit.circuit_history or [])
        circuits_lines.append(
            f"• {circuit.circuit_name} — "
            f"{circuit.num_qubits}q — "
            f"{gates_count} gates — {sim_count} sim — "
            f"{circuit.created_at.strftime('%d.%m')}"
        )
    circuits_list = "<br>".join(circuits_lines) if circuits_lines else "—"
    circuits_more = max(0, circuits_count - 10)

    # === 2. Симуляции ===
    sim_stats = await user_stat_repository.get_user_simulation_stats(session, user.id)
    simulations_count = sum(s['total'] for s in sim_stats['by_backend'].values())

    backend_lines = []
    for backend_name, stats in sim_stats['by_backend'].items():
        backend_lines.append(
            f"• {backend_name}: {stats['total']} sim — "
            f"~{stats['avg_qubits']:.1f}q — "
            f"~{stats['avg_time']:.4f} сек — "
            f"max {stats['max_time']:.4f} сек"
        )
    backend_stats_list = "<br>".join(backend_lines) if backend_lines else "—"

    overall_avg_qubits = f"{sim_stats['overall']['avg_qubits']:.1f}"
    overall_avg_time = f"{sim_stats['overall']['avg_time']:.4f}"

    # === 3. Активность ===
    activity_logs = await user_stat_repository.get_user_activity_logs(session, user.id, limit=50)
    activity_count = await user_stat_repository.get_user_activity_count(session, user.id)

    activity_lines = []
    for log in activity_logs[:20]:
        activity_lines.append(
            f"• {log.activity_date.strftime('%d.%m.%Y')}: "
            f"{log.circuits_created} схем, {log.simulations_run} сим."
        )
    activity_list = "<br>".join(activity_lines) if activity_lines else "—"
    activity_more = max(0, len(activity_logs) - 20)

    # === 4. Суммарные значения из UserActivityLog ===
    from sqlalchemy import select, func
    res = await session.execute(
        select(
            func.sum(UserActivityLog.circuits_created).label('c'),
            func.sum(UserActivityLog.simulations_run).label('s'),
        ).where(UserActivityLog.user_id == user.id)
    )
    row = res.one()
    total_circuits_created = row.c or 0
    total_simulations_run = row.s or 0

    # === 5. Даты и флаги ===
    setting_auto = "✅" if setting.automatic_name else "❌"
    setting_qubit = "✅" if setting.qubit_input_text else "❌"
    role_emoji = "👑" if user.role.name == "admin" else "👤"

    # Обработка None для бэкенда и shots
    backend_val = setting.backend.name if setting.backend else "❓ Выбор при запуске"
    shots_val = str(setting.simulation_shots) if setting.simulation_shots else "❓ Выбор при запуске"

    return i18n.admin_user_profile(
        role_emoji=role_emoji,
        user_id=user.id,
        username=f"@{user.username}" if user.username else "—",
        first_name=user.first_name,
        last_name=user.last_name or '',
        is_blocked=user.is_blocked,
        date_joined=user.date_joined.strftime("%Y-%m-%d %H:%M"),
        last_activity=user.last_activity.strftime("%Y-%m-%d %H:%M"),
        ref_source=user.ref_source or 'direct', 
        tg_locate=user.tg_locate or '-',
        language=f"{setting.language.name} ({setting.language.emoji})",
        complexity=f"{setting.complexity_level.name} ({setting.complexity_level.emoji})",
        backend=backend_val,
        shots=shots_val,
        automatic_name=setting_auto,
        qubit_input_text=setting_qubit,
        total_circuits_created=total_circuits_created,
        circuits_count=circuits_count,
        circuits_list=circuits_list,
        circuits_more=circuits_more,
        total_simulations_run=total_simulations_run,
        simulations_count=simulations_count,
        backend_stats_list=backend_stats_list,
        overall_avg_qubits=overall_avg_qubits,
        overall_avg_time=overall_avg_time,
        activity_count=activity_count,
        activity_list=activity_list,
        activity_more=activity_more,
    )


@admin_router.callback_query(F.data == "admin:user", IsAdmin())
async def admin_user_search_start(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: TranslatorRunner,
):
    await state.set_state(States.waiting_for_user_search)
    await callback.message.edit_text(
        text=i18n.admin_user_search_prompt(),
        reply_markup=builder_back_to_users_menu(i18n),
    )
    await callback.answer()


@admin_router.message(States.waiting_for_user_search, IsAdmin())
async def admin_user_search_process(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    i18n: TranslatorRunner,
):
    query = (message.text or "").strip()
    if not query:
        await message.answer(i18n.admin_user_search_empty())
        return

    users = await user_stat_repository.search_users(session, query)
    
    if not users:
        await message.answer(
            text=i18n.admin_user_not_found(query=query),
            reply_markup=builder_back_to_users_menu(i18n),
        )
        await state.clear()
        return

    if len(users) == 1:
        user = users[0]
        text = await _build_profile_text(user, i18n, session)
        await message.answer_rich(
            rich_message=InputRichMessage(html=text),
            reply_markup=builder_user_profile_keyboard(user.id, user.is_blocked, i18n),
        )
        await state.clear()
        return

    users_lines = [
        "👥 <b>Найдено несколько пользователей. Выберите номер:</b>\n"
    ]
    for idx, user in enumerate(users, start=1):
        username_str = f" (@{user.username})" if user.username else ""
        full_name = " ".join(filter(None, [user.first_name, user.last_name])) or "Без имени"
        users_lines.append(
            f"<b>{idx}.</b> ID: <code>{user.id}</code>{username_str} — {hd.quote(full_name)}"
        )

    await message.answer(
        text="\n".join(users_lines),
        reply_markup=builder_admin_user_select_kb(users, i18n),
    )
    await state.clear()


@admin_router.callback_query(
    F.data.regexp(r"^admin:user:select:(\d+)$"),
    IsAdmin()
)
async def admin_user_select_from_list(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
):
    user_id = int(callback.data.split(":")[-1])
    user = await user_stat_repository.get_user_full(session, user_id)
    
    if not user:
        await callback.answer(i18n.admin_user_not_found(query=str(user_id)), show_alert=True)
        return

    text = await _build_profile_text(user, i18n, session)
    await callback.message.edit_text(
        rich_message=InputRichMessage(html=text),
        reply_markup=builder_user_profile_keyboard(user.id, user.is_blocked, i18n),
    )
    await callback.answer()


@admin_router.callback_query(
    F.data.regexp(r"^admin:user:toggle_block:(\d+)$"),
    IsAdmin()
)
async def admin_toggle_user_block(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
):
    user_id = int(callback.data.split(":")[-1])
    new_status = await user_stat_repository.toggle_user_block(session, user_id)

    status_word = (
        i18n.admin_user_status_blocked()
        if new_status
        else i18n.admin_user_status_active()
    )
    await callback.answer(
        text=i18n.admin_user_block_toggled(status=status_word),
        show_alert=True,
    )

    user = await user_stat_repository.get_user_full(session, user_id)
    if not user:
        return

    text = await _build_profile_text(user, i18n, session)
    await callback.message.edit_text(
        rich_message=InputRichMessage(html=text),
        reply_markup=builder_user_profile_keyboard(user.id, user.is_blocked, i18n),
    )


# === ОСТАЛЬНЫЕ РАЗДЕЛЫ АДМИНКИ ===

@admin_router.callback_query(
    IsAdmin(), 
    F.data == 'admin:circuits', 
)
async def admin_circuits_btn_func(
    callback: CallbackQuery, 
    session: AsyncSession, 
    i18n: TranslatorRunner, 
):
    count_circuits_now = await activity_repository.get_count_circuits_now(session)
    count_circuits_all = await activity_repository.get_count_circuits_all(session)
    count_simulations_now = await activity_repository.get_count_simulations_now(session)
    count_simulations_all = await activity_repository.get_count_simulations_all(session)
    stat_circuits20 = await activity_repository.get_circuits_activity_last_20_days(session)
    avg_qubits = await activity_repository.get_avg_count_qubits(session)
    avg_qubits = avg_qubits if avg_qubits else 0
    avg_time = await activity_repository.get_avg_time(session) 
    avg_time = avg_time if avg_time else 0

    text_stat_citcuits20 = "\n".join([
        f"• {date.strftime('%d.%m')}: ⛓️ {circuits} | 🚀 {simulations}" 
        for date, circuits, simulations in stat_circuits20
    ])

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
    backends_simulations = await activity_repository.get_simulations_by_backends(session)
    backends_avg_qubits = await activity_repository.get_avg_qubits_by_backends(session)
    backend_avg_time = await activity_repository.get_avg_time_simulations_by_backends(session)

    backends_simulations_text = "\n".join([
        f"• {backend}: 🚀 {simulations}" 
        for backend, simulations in backends_simulations
    ])

    backends_avg_qubits_text = "\n".join([
        f"• {backend}: 📉 {round(qubits, 2)}" 
        for backend, qubits in backends_avg_qubits
    ])

    backends_avg_time_text = "\n".join([
        f"• {backend}: ⏱ {round(time, 5)} сек." 
        for backend, time in backend_avg_time
    ])

    await callback.message.edit_text(
        text=i18n.admin_backends(
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
    lang_stats = await activity_repository.get_users_by_language(session)
    complexity_stats = await activity_repository.get_users_by_complexity_level(session)
    backend_stats = await activity_repository.get_users_by_backend(session)
    auto_name_stats = await activity_repository.get_automatic_name_stats(session)
    qubit_input_stats = await activity_repository.get_qubit_input_text_stats(session)
    shots_stats = await activity_repository.get_simulation_shots_distribution(session)
    shots_avg = await activity_repository.get_avg_simulation_shots_distribution(session)
    ref_stats = await activity_repository.get_users_by_ref_source(session)
    tg_locale_stats = await activity_repository.get_users_by_tg_locale(session)

    def format_bool_stats(stats):
        enabled = next((count for value, count in stats if value), 0)
        disabled = next((count for value, count in stats if not value), 0)
        return f"Включено: {enabled}\nВыключено: {disabled}"

    lang_text = "\n".join([f"• {emoji} {name}: {count}" for emoji, name, count in lang_stats]) or "—"
    complexity_text = "\n".join([f"• {emoji} {name}: {count}" for emoji, name, count in complexity_stats]) or "—"
    auto_name_text = format_bool_stats(auto_name_stats)
    qubit_input_text = format_bool_stats(qubit_input_stats)
    ref_text = "\n".join([f"• {source}: {count}" for source, count in ref_stats]) or "—"
    tg_locale_text = "\n".join([f"• {locale.upper()}: {count}" for locale, count in tg_locale_stats]) or "—"

    # Обработка None в статистике
    backend_text = "\n".join([f"• {name if name else '❓ При запуске'}: {count}" for name, count in backend_stats]) or "—"
    shots_text = "\n".join([f"• {shots if shots else '❓ При запуске'}: {count}" for shots, count in shots_stats]) or "—"

    text = i18n.admin_statistics(
        languages=lang_text,
        complexity_levels=complexity_text,
        backends=backend_text,
        automatic_name=auto_name_text,
        qubit_input=qubit_input_text,
        simulation_shots=shots_text,
        shots_avg=shots_avg if shots_avg else 0, 
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
    input_text = message.text.strip()
    
    success = False
    user_info = ""

    if input_text.isdigit():
        user_id = int(input_text)
        success = await user_repository.block_user_by_id(session, user_id)
        user_info = f"ID: {user_id}"
    else:
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
    

# ШАГ 1: Старт рассылки (Запрос русского текста)
@admin_router.callback_query(F.data == "admin:message", IsAdmin())
async def admin_broadcast_start(
    callback: CallbackQuery, 
    state: FSMContext, 
    i18n: TranslatorRunner
):
    await state.set_state(States.waiting_for_broadcast_ru) # Ожидаем русский текст
    await callback.message.edit_text(i18n.admin_broadcast_prompt(), reply_markup=builder_back_admin_menu(i18n))
    await callback.answer()


# ШАГ 2: Обработка русского текста и запрос английского
@admin_router.message(
    StateFilter(States.waiting_for_broadcast_ru), 
    IsAdmin()
)
async def admin_broadcast_process_ru(
    message: Message, 
    state: FSMContext, 
    i18n: TranslatorRunner
):
    broadcast_text_ru = message.text.strip()
    
    if not broadcast_text_ru:
        await message.answer(i18n.admin_broadcast_empty())
        return

    # Сохраняем русский текст в состояние
    await state.update_data(broadcast_text_ru=broadcast_text_ru)
    
    # Переходим к запросу английского текста
    await state.set_state(States.waiting_for_broadcast_en)
    await message.answer(i18n.admin_broadcast_prompt_en(), reply_markup=builder_back_admin_menu(i18n))


# ШАГ 3: Обработка английского текста и запуск рассылки
@admin_router.message(
    StateFilter(States.waiting_for_broadcast_en), 
    IsAdmin()
)
async def admin_broadcast_process_en(
    message: Message, 
    state: FSMContext, 
    session: AsyncSession, 
    i18n: TranslatorRunner
):
    broadcast_text_en = message.text.strip()
    
    if not broadcast_text_en:
        await message.answer(i18n.admin_broadcast_empty())
        return

    # Достаем русский текст из состояния
    data = await state.get_data()
    broadcast_text_ru = data.get('broadcast_text_ru')

    await state.clear()
    await message.answer(i18n.admin_broadcast_started())

    # Получаем полные объекты пользователей со связанными настройками (чтобы узнать их язык)
    users = await base_repository.get_all_users_with_settings(session)

    # Запускаем фоновую задачу
    asyncio.create_task(
        broadcast_to_all_users(
            text_ru=broadcast_text_ru,
            text_en=broadcast_text_en,
            users=users,
            admin_chat_id=message.from_user.id,
            bot=message.bot
        )
    )