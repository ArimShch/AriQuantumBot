from aiogram import Router, F, Bot 
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


last_router = Router()

@last_router.message()
async def last_random_message(
    message: Message, 
):
    pass 