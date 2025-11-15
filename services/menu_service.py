from aiogram import types

from bot.keyboards.reply import admin_menu_keyboard, programmer_menu_keyboard
from bot.texts import fa


class MenuService:
    async def show_main_menu(self, message: types.Message, profile: dict) -> None:
        role = profile.get("role")
        keyboard = (
            admin_menu_keyboard()
            if role == "admin"
            else programmer_menu_keyboard()
        )
        greeting = fa.MAIN_MENU_ADMIN if role == "admin" else fa.MAIN_MENU_PROGRAMMER
        await message.answer(
            greeting.format(name=profile.get("name", "")),
            reply_markup=keyboard,
        )