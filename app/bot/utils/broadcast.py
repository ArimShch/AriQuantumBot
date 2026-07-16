# utils/broadcast.py
import asyncio
import logging
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...infrastructure.database.models.models import User


logger = logging.getLogger(__name__)

async def broadcast_to_all_users(
    text: str,
    users: list,
    admin_chat_id: int,
    bot: Bot,
    max_concurrent: int = 20,  # Безопасный лимит Telegram: ~30 msg/sec
):
    """
    Рассылка одного и того же сообщения всем пользователям.
    Не зависит от языка пользователя.
    """
    if not users:
        await bot.send_message(admin_chat_id, "📭 Нет пользователей для рассылки.")
        return

    # 2. Семафор для контроля нагрузки (20 параллельных запросов)
    semaphore = asyncio.Semaphore(max_concurrent)
    success_count = 0
    fail_count = 0
    blocked_count = 0

    async def send_to_user(tg_id: int):
        nonlocal success_count, fail_count, blocked_count
        async with semaphore:
            try:
                # Отправляем ОДНО И ТО ЖЕ сообщение всем
                await bot.send_message(tg_id, text)
                success_count += 1
                
            except TelegramForbiddenError:
                blocked_count += 1  # Пользователь заблокировал бота
            except TelegramRetryAfter as e:
                # Telegram просит подождать — соблюдаем паузу
                logger.warning(f"Rate limit hit. Sleeping {e.retry_after}s")
                await asyncio.sleep(e.retry_after)
                # Повторная отправка
                try:
                    await bot.send_message(tg_id, text)
                    success_count += 1
                except Exception as retry_err:
                    fail_count += 1
                    logger.error(f"Retry failed for {tg_id}: {retry_err}")
            except Exception as e:
                fail_count += 1
                logger.error(f"Failed to send to {tg_id}: {e}")

    # 3. Запускаем все задачи
    tasks = [send_to_user(tg_id) for tg_id in users]
    await asyncio.gather(*tasks)

    # 4. Отчёт админу
    report = (
        f"✅ Рассылка завершена!\n"
        f"📤 Отправлено: {success_count}\n"
        f"🚫 Заблокировано: {blocked_count}\n"
        f"❌ Ошибки: {fail_count}"
    )
    await bot.send_message(admin_chat_id, report)