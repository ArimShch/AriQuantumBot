"""
Экран схемы в режиме «HTML-виджет».

Вид экрана в режиме виджета (две отдельных сообщения):
    1) виджет со схемой; подпись — имя схемы;
    2) текст (результат последней симуляции / шаг мастера) + кнопки.

В режиме ASCII всё работает как раньше: одно сообщение, схема в <pre>.

Id сообщения-виджета хранится в памяти (по chat_id): виджет должен исчезать, когда
пользователь уходит с экрана схемы, и обновляться, когда схема меняется.
"""
import logging
import re
from html import escape
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot
from aiogram.types import CallbackQuery, InputRichMessage, Message
from fluentogram import TranslatorRunner
from sqlalchemy.ext.asyncio import AsyncSession

from .circuit_widget import build_circuit_widget
from .widgets import SendWidget
from ...infrastructure.database.models.models import QuantumCircuit
from ...infrastructure.database.repositories import user_repository


logger = logging.getLogger(__name__)

# chat_id -> message_id виджета схемы, который сейчас показан в чате
_widgets: dict[int, int] = {}

# <b>Имя</b> + <pre>диаграмма</pre> в начале шаблона — в режиме виджета их показывает сам виджет
_HEADER_RE = re.compile(
    r'\A\s*<b>.*?</b>\s*(?:<br>\s*)?<pre>.*?</pre>\s*(?:<br>\s*)?',
    re.DOTALL,
)


def strip_circuit_header(html: str) -> str:
    """Убирает из текста имя схемы и ASCII-диаграмму (они уже есть в виджете)."""
    return _HEADER_RE.sub('', html, count=1)


def has_circuit_widget(chat_id: int) -> bool:
    return chat_id in _widgets


async def _safe_delete(bot: Bot, chat_id: int, message_id: int | None) -> None:
    if message_id is None:
        return
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logger.debug('Cannot delete message %s in chat %s: %s', message_id, chat_id, e)


async def clear_circuit_widget(bot: Bot, chat_id: int) -> None:
    """Удаляет виджет схемы из чата (если он был)."""
    await _safe_delete(bot, chat_id, _widgets.pop(chat_id, None))


async def present(
    target: CallbackQuery | Message,
    *,
    session: AsyncSession,
    i18n: TranslatorRunner,
    circuit: QuantumCircuit,
    html: str,
    reply_markup: Any,
    circuit_changed: bool = True,
    user_id: int | None = None,
) -> None:
    """
    Показывает экран схемы.

    html — полный текст в формате ASCII-режима (с именем и диаграммой).
    circuit_changed=False — схема не менялась с момента показа виджета, достаточно
    отредактировать текстовое сообщение.
    user_id — id пользователя, если target — сообщение бота (например, callback.message).
    """
    is_callback = isinstance(target, CallbackQuery)
    message: Message = target.message if is_callback else target
    chat_id = message.chat.id
    bot = message.bot

    use_widget = False
    if message.chat.type == 'private':
        settings = await user_repository.get_user_settings(session, user_id or target.from_user.id)
        use_widget = settings is not None and settings.output_mode == 'widget'

    if use_widget:
        # Схема не менялась, виджет на месте — меняем только текст
        if is_callback and not circuit_changed and has_circuit_widget(chat_id):
            await message.edit_text(
                reply_markup=reply_markup,
                rich_message=InputRichMessage(html=strip_circuit_header(html)),
            )
            return

        built = build_circuit_widget(circuit.num_qubits, circuit.circuit_history)
        sent = None
        if built is not None:
            try:
                sent = await bot(SendWidget(
                    chat_id=chat_id,
                    html=built[0],
                    height=built[1],
                    caption=f'<b>{escape(circuit.circuit_name)}</b>',
                ))
            except Exception as e:
                # Виджеты недоступны (старый клиент, ошибка API) — откат на ASCII
                logger.warning(f'Circuit widget send failed, falling back to ASCII: {e}')

        if sent is not None:
            await message.answer_rich(
                rich_message=InputRichMessage(html=strip_circuit_header(html)),
                reply_markup=reply_markup,
            )
            old_widget = _widgets.get(chat_id)
            _widgets[chat_id] = sent.message_id
            await _safe_delete(bot, chat_id, old_widget)
            if is_callback:
                await _safe_delete(bot, chat_id, message.message_id)
            return

    # ASCII-режим (или откат): как раньше, одним сообщением
    await clear_circuit_widget(bot, chat_id)
    if is_callback:
        await message.edit_text(
            reply_markup=reply_markup,
            rich_message=InputRichMessage(html=html),
        )
    else:
        await message.answer_rich(
            rich_message=InputRichMessage(html=html),
            reply_markup=reply_markup,
        )


async def edit_screen(
    callback: CallbackQuery,
    *,
    reply_markup: Any = None,
    rich_message: InputRichMessage | None = None,
    text: str | None = None,
) -> None:
    """
    Редактирует текстовое сообщение экрана схемы (шаги мастера, меню и т. п.),
    когда схема не менялась. Если над сообщением показан виджет, имя и диаграмму
    из текста убираем — они уже есть в виджете.
    """
    if rich_message is not None and has_circuit_widget(callback.message.chat.id):
        rich_message = InputRichMessage(html=strip_circuit_header(rich_message.html))

    kwargs: dict[str, Any] = {}
    if text is not None:
        kwargs['text'] = text
    if reply_markup is not None:
        kwargs['reply_markup'] = reply_markup
    if rich_message is not None:
        kwargs['rich_message'] = rich_message
    await callback.message.edit_text(**kwargs)


_CIRCUIT_CALLBACK_RE = re.compile(r'^circuits:\d+(?::(.*))?$')
_KEEP_EXACT = {'ignore', 'ignore_prev', 'ignore_next', 'control_qubit_already_selected'}
_BACK_RE = re.compile(r'^back:circuit(?:_edit|_gates)?:\d+$')


def keeps_widget(data: str | None) -> bool:
    """True, если нажатие остаётся внутри экрана схемы и виджет нужно сохранить."""
    if not data:
        return False
    if data in _KEEP_EXACT or _BACK_RE.match(data):
        return True
    match = _CIRCUIT_CALLBACK_RE.match(data)
    if match:
        tail = match.group(1) or ''
        # запуск симуляции, удаление схемы и экспорт уводят с экрана схемы
        leaves = tail == 'simulate' or tail == 'edit:delete' or tail.startswith('edit:export:')
        return not leaves
    return False


class CircuitWidgetCleanupMiddleware(BaseMiddleware):
    """Удаляет виджет схемы, когда пользователь нажимает кнопку, уводящую с экрана схемы."""

    async def __call__(
        self,
        handler: Callable[[CallbackQuery, dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        message = event.message
        if message is not None and has_circuit_widget(message.chat.id) and not keeps_widget(event.data):
            try:
                await clear_circuit_widget(data['bot'], message.chat.id)
            except Exception as e:
                logger.warning(f'Circuit widget cleanup failed: {e}')
        return await handler(event, data)
