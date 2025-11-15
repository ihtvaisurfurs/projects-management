from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from bot.keyboards.reply import contact_request_keyboard
from bot.texts import fa
from core.constants import BACK_TO_MENU
from core.utils import grouped_projects_text
from bot.utils.ui import cleanup_inline_messages
from services.logging_service import LogService
from services.menu_service import MenuService
from services.project_service import ProjectService
from services.session_manager import SessionManager

router = Router()


async def _require_profile(message: types.Message, session_manager: SessionManager):
    profile = session_manager.get_profile(message.from_user.id)
    if not profile:
        await message.answer(fa.REQUEST_PHONE, reply_markup=contact_request_keyboard())
    return profile


@router.message(F.text == "📊 وضعیت پروژه ها")
async def show_statuses(
    message: types.Message,
    session_manager: SessionManager,
    project_service: ProjectService,
    log_service: LogService,
):
    profile = await _require_profile(message, session_manager)
    if not profile:
        return
    grouped = await project_service.grouped(profile["role"], profile.get("name"))
    if profile["role"] != "admin" and all(len(items) == 0 for items in grouped.values()):
        await message.answer(fa.NO_PROJECT_ASSIGNED)
        return
    await message.answer(grouped_projects_text(grouped))
    await log_service.info(f"{profile['name']} وضعیت پروژه‌ها را مشاهده کرد")


@router.message(F.text == "🛠 آپدیت پروژه")
async def update_project_entry(
    message: types.Message,
    session_manager: SessionManager,
    project_service: ProjectService,
    log_service: LogService,
    bot_username: str,
):
    profile = await _require_profile(message, session_manager)
    if not profile:
        return
    projects = await project_service.list_for_updates(profile["role"], profile.get("name"))
    if not projects:
        await message.answer(fa.NO_PROJECT_ASSIGNED)
        return
    lines = [fa.UPDATE_SELECT_PROJECT]
    for project in projects:
        link = f"https://t.me/{bot_username}?start=project_{project['id']}"
        lines.append(f"• 🔗 <a href=\"{link}\">{project['title']}</a>")
    await message.answer("\n".join(lines))
    await log_service.info(f"{profile['name']} لیست پروژه‌های قابل ویرایش را دریافت کرد")
