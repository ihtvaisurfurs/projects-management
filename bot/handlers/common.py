from aiogram import Router, types
from aiogram.filters import Command

from bot.texts import fa

router = Router(name="common_router")


@router.message(Command("id"))
async def send_chat_id(
    message: types.Message,
    enable_group_id_command: bool,
) -> None:
    if not enable_group_id_command:
        await message.answer(fa.GROUP_ID_COMMAND_DISABLED)
        return
    if message.chat.type not in {"group", "supergroup"}:
        await message.answer(fa.GROUP_ID_GROUP_ONLY)
        return
    await message.answer(fa.GROUP_ID_RESPONSE.format(chat_id=message.chat.id))
