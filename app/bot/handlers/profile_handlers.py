from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from fluentogram import TranslatorRunner

from ...infrastructure.database.repositories import user_repository
from ..keyboards.profile_keyboards import profile_menu_keyboard


profile_router = Router()


@profile_router.callback_query(F.data == "profile")
async def show_profile(
    callback: CallbackQuery,
    session: AsyncSession,
    i18n: TranslatorRunner,
):
    """Показывает профиль пользователя"""
    user = callback.from_user
    
    # Получаем статистику
    circuits_count = await user_repository.get_user_circuits_count(session, user.id)
    simulations_count = await user_repository.get_user_simulations_count(session, user.id)
    
    # Максимальное количество схем (из настроек или константы)
    max_circuits = 5
    
    text = i18n.profile(
        first_name=user.first_name or "",
        username=f"@{user.username}" if user.username else "—",
        circuits_count=circuits_count,
        max_circuits=max_circuits,
        simulations_count=simulations_count,
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=profile_menu_keyboard(i18n)
    )
    await callback.answer()