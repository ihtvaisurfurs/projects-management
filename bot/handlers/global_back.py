from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from bot.texts import fa
from core.constants import BACK_TO_MENU
from bot.utils.ui import cleanup_inline_messages
from services.menu_service import MenuService
from services.session_manager import SessionManager
from bot.keyboards.reply import contact_request_keyboard

router = Router(name="global_back_router")


@router.message(F.text == BACK_TO_MENU)
async def global_back_handler(
    message: types.Message,
    state: FSMContext,
    session_manager: SessionManager,
    menu_service: MenuService,
):
    await state.clear()
    await cleanup_inline_messages(message, session_manager)
    profile = session_manager.get_profile(message.from_user.id)
    if profile:
        await menu_service.show_main_menu(message, profile)
    else:
        await message.answer(fa.REQUEST_PHONE, reply_markup=contact_request_keyboard())
