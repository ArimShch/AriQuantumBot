import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
from aiohttp import ClientTimeout

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from fluentogram import TranslatorHub

from .handlers.start_handlers import start_router
from .handlers.create_circuit_handlers import create_circuit_router
from .handlers.circuit_manage_handlers import circuit_manage_router
from .handlers.settings_handlers import settings_router 
from .handlers.simulation_handlers import simulation_router
from .handlers.profile_handlers import profile_router
from .handlers.admin_handlers import admin_router
from .handlers.last_handlers import last_router
from .middlewares.throttling import ThrottlingMiddleware
from .middlewares.database import DBSessionMiddleware
from .middlewares.last_activity import LastActivityMiddleware
from .middlewares.blocked import BlockMiddleware
from .middlewares.i18n import I18nMiddleware
from config.config import Config
from app.infrastructure.database.init_db import init_db
from app.infrastructure.database.connection import engine, get_session_factory
from config.i18n import create_translator_hub

logger = logging.getLogger(__name__)

async def main(config: Config) -> None:
    logger.info('Starting bot...')

    session_factory: async_sessionmaker[AsyncSession] = get_session_factory()

    if not await init_db(engine, session_factory):
        logger.info("Bot can't work without bd")

    PROXY_URL = "http://127.0.0.1:7890"
    session = AiohttpSession(
        proxy=PROXY_URL,
        timeout=30.0
    )

    bot = Bot(
        token=config.bot.token, 
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        ),
        session=session,
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    hub: TranslatorHub = create_translator_hub()

    logger.info('Including routers...')
    dp.include_routers(
        start_router, create_circuit_router, circuit_manage_router, 
        settings_router, simulation_router, profile_router, admin_router, 
        last_router, 
    )

    logger.info('Including middlewares...')
    dp.update.middleware(ThrottlingMiddleware())
    dp.update.middleware(DBSessionMiddleware())
    dp.update.middleware(LastActivityMiddleware())
    dp.update.middleware(BlockMiddleware())
    dp.update.middleware(I18nMiddleware(hub))

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(
            bot, admin_ids=config.bot.admin_ids, 
            session_factory=session_factory, 
            
        )
    except Exception as e:
        logger.exception('Error in start polling: %s', e)


