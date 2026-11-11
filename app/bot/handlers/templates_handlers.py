import copy
import logging
from uuid import uuid4

from aiogram import Router, F
from aiogram.types import CallbackQuery, InputRichMessage
from aiogram.fsm.context import FSMContext
from fluentogram import TranslatorRunner
from sqlalchemy.ext.asyncio import AsyncSession

from ..utils.templates_data import TEMPLATES
from ..utils.draw_circuit import draw_history
from ..utils.circuit_screen import present
from ..keyboards.templates_keyboards import builder_templates_list, builder_template_details
from ..keyboards.circuit_manage_keyboards import builder_circuit_manage
from ...infrastructure.database.repositories import user_repository, circuit_repository, activity_repository
from ..states.states import States

logger = logging.getLogger(__name__)
templates_router = Router()

# 1. Открытие списка шаблонов
@templates_router.callback_query(F.data == "templates")
async def templates_list_handler(callback: CallbackQuery, i18n: TranslatorRunner, locale: str):
    await callback.message.edit_text(
        rich_message=InputRichMessage(html=i18n.templates_list_title()),
        reply_markup=builder_templates_list(i18n, locale)
    )
    await callback.answer()

# 2. Просмотр конкретного шаблона
@templates_router.callback_query(F.data.regexp(r"^templates:([^:]+)$"))
async def template_view_handler(callback: CallbackQuery, i18n: TranslatorRunner, locale: str):
    template_id = callback.data.split(":")[1]
    data = TEMPLATES.get(template_id)
    
    if not data:
        await callback.answer(i18n.template_not_found(), show_alert=True)
        return

    name = data["name_ru"] if locale == "ru" else data["name_en"]
    desc = data["desc_ru"] if locale == "ru" else data["desc_en"]
    diagram = draw_history(data["num_qubits"], data["history"])

    text = i18n.template_details(
        name=name,
        description=desc,
        circuit_diagram=diagram,
    )

    await callback.message.edit_text(
        rich_message=InputRichMessage(html=text),
        reply_markup=builder_template_details(template_id, i18n)
    )
    await callback.answer()

# 3. Создание схемы из шаблона
@templates_router.callback_query(F.data.regexp(r"^templates:([^:]+):create$"))
async def template_create_handler(
    callback: CallbackQuery, 
    session: AsyncSession, 
    state: FSMContext,
    i18n: TranslatorRunner, 
    locale: str, 
):
    template_id = callback.data.split(":")[1]
    data = TEMPLATES.get(template_id)

    if not data:
        await callback.answer(i18n.template_not_found(), show_alert=True)
        return

    # Проверка лимитов схем
    if await user_repository.has_reached_circuit_limit(session=session, tg_id=callback.from_user.id):
        await callback.answer(i18n.circuit_limit_reached(), show_alert=True)
        return

    # 1. Берем базовое название шаблона на языке пользователя
    template_name = data["name_ru"] if locale == "ru" else data["name_en"]
    
    # 2. Отсекаем текст в скобках (например, " (2 кубита)") для краткости
    clean_name = template_name.split('(')[0].strip()
    
    # 3. Генерируем короткую уникальную приписку (4 символа)
    unique_suffix = uuid4().hex[:6].upper()
    
    # 4. Формируем итоговое имя (и обрезаем до 50 символов, чтобы БД не выдала ошибку)
    circuit_name = f"{clean_name}-{unique_suffix}"
    if len(circuit_name) > 50:
        circuit_name = circuit_name[:50]
    
    # Создаем схему в БД
    created_circuit = await circuit_repository.create_circuit(
        tg_id=callback.from_user.id,
        circuit_name=circuit_name,
        num_qubits=data["num_qubits"],
        session=session
    )
    
    # Копируем историю гейтов
    created_circuit.circuit_history = copy.deepcopy(data["history"])
    await session.flush()
    await session.refresh(created_circuit)

    # Увеличиваем стату
    user_activity = await activity_repository.get_activity_today(session=session, tg_id=callback.from_user.id)
    user_activity.circuits_created += 1

    # Формируем сообщение о созданной схеме
    diagram = draw_history(created_circuit.num_qubits, created_circuit.circuit_history)
    text = i18n.circuit_details(
        circuit_name=created_circuit.circuit_name, 
        circuit_diagram=diagram,
        state_vector=f'|{"0" * created_circuit.num_qubits}⟩', # Симуляции еще не было
        has_simulation='False', 
    )

    await present(
        callback, session=session, i18n=i18n, circuit=created_circuit,
        html=text, reply_markup=builder_circuit_manage(i18n, created_circuit.id),
    )
    await state.set_state(States.circuit_manage)
    await callback.answer()