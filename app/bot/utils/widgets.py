"""Прямой вызов методов Bot API 10.4 (HTML-виджеты), которых ещё нет в aiogram 3.31."""
from typing import Optional

from aiogram.client.default import Default
from aiogram.methods import TelegramMethod
from aiogram.types import (
    ForceReply,
    InlineKeyboardMarkup,
    Message,
    MessageEntity,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    ReplyParameters,
)


class SendWidget(TelegramMethod[Message]):
    """
    Отправляет сообщение с HTML-виджетом (Bot API 10.4).

    Источник: https://core.telegram.org/bots/api#sendwidget
    В продакшене виджеты работают только в личных чатах.
    """

    __returning__ = Message
    __api_method__ = "sendWidget"

    chat_id: int | str
    html: str
    """HTML-код виджета, 1-32768 байт"""
    message_thread_id: Optional[int] = None
    width: Optional[int] = None
    """Ширина в логических пикселях (от 200 до максимума пузыря)"""
    height: Optional[int] = None
    """Высота в логических пикселях (50-600)"""
    public_data: Optional[str] = None
    chat_data: Optional[str] = None
    caption: Optional[str] = None
    parse_mode: Optional[str | Default] = Default("parse_mode")
    caption_entities: Optional[list[MessageEntity]] = None
    show_caption_above_media: Optional[bool | Default] = Default("show_caption_above_media")
    allow_queries: Optional[bool] = None
    is_shared: Optional[bool] = None
    disable_notification: Optional[bool] = None
    protect_content: Optional[bool | Default] = Default("protect_content")
    allow_paid_broadcast: Optional[bool] = None
    message_effect_id: Optional[str] = None
    reply_parameters: Optional[ReplyParameters] = None
    reply_markup: Optional[
        InlineKeyboardMarkup | ReplyKeyboardMarkup | ReplyKeyboardRemove | ForceReply
    ] = None
