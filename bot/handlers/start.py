from aiogram import F, Router, types
from aiogram.filters import CommandStart
from aiogram.filters.command import CommandObject
from aiogram.fsm.context import FSMContext

from bot.fsm.states import AuthState
from bot.keyboards.inline import project_profile_keyboard
from bot.keyboards.reply import contact_request_keyboard
from bot.texts import fa
from core.constants import BACK_TO_MENU
from core.utils import normalize_phone
from services.deep_link import parse_start_param
from services.logging_service import LogService
from services.menu_service import MenuService
from services.project_formatter import project_profile_text
from services.project_service import ProjectService
from services.session_manager import SessionManager
from services.user_service import UserService
from services.validators import is_valid_phone

router = Router()


async def _show_project_profile(
    message: types.Message,
    project: dict,
    profile: dict,
    session_manager: SessionManager,
) -> None:
    is_admin = profile.get("role") == "admin"
    sent = await message.answer(
        project_profile_text(project),
        reply_markup=project_profile_keyboard(project["id"], is_admin=is_admin),
    )
    session_manager.add_inline_message(message.from_user.id, sent.message_id)


@router.message(CommandStart())
async def command_start(
    message: types.Message,
    command: CommandObject,
    state: FSMContext,
    session_manager: SessionManager,
    menu_service: MenuService,
    project_service: ProjectService,
    log_service: LogService,
    user_service: UserService,
):
    await state.clear()
    user_id = message.from_user.id
    deep_link = parse_start_param(command.args)
    profile = session_manager.get_profile(user_id)
    if not profile:
        db_user = await user_service.get_by_telegram(user_id)
        if db_user:
            session_manager.set_profile(user_id, db_user)
            profile = db_user
    if deep_link and deep_link.type == "project":
        if profile:
            project = await project_service.get_project(deep_link.entity_id)
            if not project:
                await message.answer(fa.PROJECT_NOT_FOUND)
                return
            if profile.get("role") != "admin" and project.get("owner_name") != profile.get("name"):
                await message.answer(fa.UNAUTHORIZED)
                return
            await _show_project_profile(message, project, profile, session_manager)
            return
        await state.set_state(AuthState.waiting_phone)
        await state.update_data(pending_project=deep_link.entity_id)
        await message.answer(fa.REQUEST_PHONE, reply_markup=contact_request_keyboard())
        await message.answer(fa.PENDING_PROJECT_NOTICE)
        return

    if profile:
        await menu_service.show_main_menu(message, profile)
        return

    await state.set_state(AuthState.waiting_phone)
    await message.answer(fa.REQUEST_PHONE, reply_markup=contact_request_keyboard())


@router.message(AuthState.waiting_phone, F.contact)
async def handle_contact(
    message: types.Message,
    state: FSMContext,
    user_service: UserService,
    menu_service: MenuService,
    session_manager: SessionManager,
    log_service: LogService,
    project_service: ProjectService,
):
    contact = message.contact
    if contact.user_id != message.from_user.id:
        await message.answer(fa.INVALID_PHONE)
        return
    phone = normalize_phone(contact.phone_number)
    if not is_valid_phone(phone):
        await message.answer(fa.INVALID_PHONE)
        return
    user = await user_service.get_by_phone(phone)
    if not user:
        await message.answer(fa.PHONE_NOT_FOUND)
        return
    await user_service.update_telegram_id(user["id"], message.from_user.id)
    session_manager.set_profile(message.from_user.id, user)
    await log_service.info(f"کاربر {user['name']} وارد شد")
    data = await state.get_data()
    await state.clear()
    await message.answer(fa.PHONE_SHARED_CONFIRM.format(name=user["name"]))
    await menu_service.show_main_menu(message, user)
    pending_project = data.get("pending_project")
    if pending_project:
        project = await project_service.get_project(pending_project)
        if project:
            await _show_project_profile(message, project, user, session_manager)


@router.message(AuthState.waiting_phone)
async def handle_plain_phone(message: types.Message):
    await message.answer(fa.REQUEST_PHONE, reply_markup=contact_request_keyboard())
