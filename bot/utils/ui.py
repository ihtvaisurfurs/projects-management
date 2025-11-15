from aiogram import types
from aiogram.exceptions import TelegramBadRequest

from services.session_manager import SessionManager


async def cleanup_inline_messages(message: types.Message, session_manager: SessionManager) -> None:
    message_ids = session_manager.consume_inline_messages(message.from_user.id)
    if not message_ids:
        return
    for msg_id in message_ids:
        try:
            await message.bot.edit_message_reply_markup(
                chat_id=message.chat.id,
                message_id=msg_id,
                reply_markup=None,
            )
        except TelegramBadRequest:
            continue