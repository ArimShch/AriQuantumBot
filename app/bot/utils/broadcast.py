import asyncio
import logging
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...infrastructure.database.models.models import User

logger = logging.getLogger(__name__)

async def broadcast_to_all_users(
    text_ru: str,
    text_en: str,
    users: list[User],
    admin_chat_id: int,
    bot: Bot,
    max_concurrent: int = 20,  # Безопасный лимит Telegram: ~30 msg/sec
):
    """
    Рассылка сообщения. Пользователям с русским языком в настройках
    отправляется text_ru, всем остальным — text_en.
    """
    if not users:
        await bot.send_message(admin_chat_id, "📭 Нет пользователей для рассылки.")
        return

    # Семафор для контроля нагрузки
    semaphore = asyncio.Semaphore(max_concurrent)
    success_count = 0
    fail_count = 0
    blocked_count = 0

    async def send_to_user(user: User):
        nonlocal success_count, fail_count, blocked_count
        async with semaphore:
            try:
                # Определяем язык пользователя на основе его настроек
                # Если настройки не подгрузились, используем 'en' как фоллбэк
                lang_code = user.setting.language_code if user.setting else 'en'
                
                # Выбираем нужный текст
                text_to_send = text_ru if lang_code == 'ru' else text_en

                await bot.send_message(user.id, text_to_send)
                success_count += 1
                
            except TelegramForbiddenError:
                blocked_count += 1  # Пользователь заблокировал бота
            except TelegramRetryAfter as e:
                # Telegram просит подождать — соблюдаем паузу
                logger.warning(f"Rate limit hit. Sleeping {e.retry_after}s")
                await asyncio.sleep(e.retry_after)
                # Повторная отправка
                try:
                    await bot.send_message(user.id, text_to_send)
                    success_count += 1
                except Exception as retry_err:
                    fail_count += 1
                    logger.error(f"Retry failed for {user.id}: {retry_err}")
            except Exception as e:
                fail_count += 1
                logger.error(f"Failed to send to {user.id}: {e}")

    # Запускаем все задачи
    tasks = [send_to_user(user) for user in users]
    await asyncio.gather(*tasks)

    # Отчёт админу
    report = (
        f"✅ Рассылка завершена!\n"
        f"📤 Успешно отправлено: {success_count}\n"
        f"🚫 Заблокировали бота: {blocked_count}\n"
        f"❌ Ошибок отправки: {fail_count}"
    )
    await bot.send_message(admin_chat_id, report)