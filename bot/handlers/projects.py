from aiogram import Router, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from bot.fsm.states import (
    ProjectDescriptionUpdate,
    ProjectOwnerUpdate,
    ProjectStatusUpdate,
    ProjectTitleUpdate,
)
from bot.keyboards.inline import (
    OwnerCallback,
    ProjectActionCallback,
    StatusCallback,
    owner_keyboard,
    project_profile_keyboard,
    status_keyboard,
)
from bot.keyboards.reply import back_keyboard, contact_request_keyboard
from bot.texts import fa
from services.logging_service import LogService
from services.project_formatter import project_profile_text
from services.project_service import ProjectService
from services.session_manager import SessionManager
from services.user_service import UserService

router = Router()


async def _send_profile(
    message: types.Message,
    project: dict,
    profile: dict,
    session_manager: SessionManager,
) -> None:
    sent = await message.answer(
        project_profile_text(project),
        reply_markup=project_profile_keyboard(project["id"], profile.get("role") == "admin"),
    )
    session_manager.add_inline_message(message.from_user.id, sent.message_id)


async def _load_project(
    project_id: int,
    user_id: int,
    project_service: ProjectService,
    session_manager: SessionManager,
    target: types.Message,
):
    profile = session_manager.get_profile(user_id)
    if not profile:
        await target.answer(fa.REQUEST_PHONE, reply_markup=contact_request_keyboard())
        return None, None
    project = await project_service.get_project(project_id)
    if not project:
        await target.answer(fa.PROJECT_NOT_FOUND)
        return None, profile
    if profile.get("role") != "admin" and project.get("owner_name") != profile.get("name"):
        await target.answer(fa.UNAUTHORIZED)
        return None, profile
    return project, profile


@router.callback_query(ProjectActionCallback.filter())
async def handle_project_action(
    callback: types.CallbackQuery,
    callback_data: ProjectActionCallback,
    state: FSMContext,
    project_service: ProjectService,
    session_manager: SessionManager,
    user_service: UserService,
):
    project, profile = await _load_project(
        callback_data.project_id,
        callback.from_user.id,
        project_service,
        session_manager,
        callback.message,
    )
    if not project:
        await callback.answer()
        return
    action = callback_data.action
    if action == "status":
        await state.set_state(ProjectStatusUpdate.waiting_status)
        await state.update_data(edit_project_id=project["id"])
        inline_message = await callback.message.answer(
            "لطفاً وضعیت جدید را انتخاب کنید:",
            reply_markup=status_keyboard(),
        )
        session_manager.add_inline_message(callback.from_user.id, inline_message.message_id)
    elif action == "title":
        await state.set_state(ProjectTitleUpdate.waiting_title)
        await state.update_data(edit_project_id=project["id"])
        await callback.message.answer(fa.ASK_NEW_TITLE, reply_markup=back_keyboard())
    elif action == "description":
        await state.set_state(ProjectDescriptionUpdate.waiting_description)
        await state.update_data(edit_project_id=project["id"])
        await callback.message.answer(fa.ASK_NEW_DESCRIPTION, reply_markup=back_keyboard())
    elif action == "owner":
        if profile.get("role") != "admin":
            await callback.answer(fa.UNAUTHORIZED, show_alert=True)
            return
        await state.set_state(ProjectOwnerUpdate.waiting_owner)
        await state.update_data(edit_project_id=project["id"])
        users = await user_service.list_users()
        if not users:
            await callback.message.answer("هیچ کاربری برای انتخاب وجود ندارد. ابتدا کاربر جدید تعریف کنید.")
            await state.clear()
            await _send_profile(callback.message, project, profile, session_manager)
            await callback.answer()
            return
        else:
            inline_message = await callback.message.answer(
                "مسئول جدید را انتخاب کنید:",
                reply_markup=owner_keyboard(users),
            )
            session_manager.add_inline_message(callback.from_user.id, inline_message.message_id)
    await callback.answer()


@router.callback_query(StatusCallback.filter(), StateFilter(ProjectStatusUpdate.waiting_status))
async def update_status(
    callback: types.CallbackQuery,
    callback_data: StatusCallback,
    state: FSMContext,
    project_service: ProjectService,
    session_manager: SessionManager,
    log_service: LogService,
):
    data = await state.get_data()
    project_id = data.get("edit_project_id")
    if not project_id:
        await callback.answer(fa.GENERIC_ERROR, show_alert=True)
        return
    project, profile = await _load_project(
        project_id,
        callback.from_user.id,
        project_service,
        session_manager,
        callback.message,
    )
    if not project:
        await callback.answer()
        return
    await project_service.update_status(project_id, callback_data.value)
    updated = await project_service.get_project(project_id)
    await log_service.info(f"{profile['name']} وضعیت پروژه {project_id} را به‌روزرسانی کرد")
    await state.clear()
    await callback.answer("✅ تغییر انجام شد")
    await callback.message.answer(fa.STATUS_UPDATED)
    await _send_profile(callback.message, updated, profile, session_manager)


@router.message(ProjectTitleUpdate.waiting_title)
async def apply_new_title(
    message: types.Message,
    state: FSMContext,
    project_service: ProjectService,
    session_manager: SessionManager,
    log_service: LogService,
):
    title = message.text.strip()
    if len(title) < 3:
        await message.answer("❗️ عنوان معتبر وارد کنید.")
        return
    data = await state.get_data()
    project_id = data.get("edit_project_id")
    project, profile = await _load_project(
        project_id,
        message.from_user.id,
        project_service,
        session_manager,
        message,
    )
    if not project:
        return
    await project_service.update_title(project_id, title)
    await log_service.info(f"{profile['name']} عنوان پروژه {project_id} را تغییر داد")
    await state.clear()
    updated = await project_service.get_project(project_id)
    await message.answer(fa.TITLE_UPDATED)
    await _send_profile(message, updated, profile, session_manager)


@router.message(ProjectDescriptionUpdate.waiting_description)
async def apply_new_description(
    message: types.Message,
    state: FSMContext,
    project_service: ProjectService,
    session_manager: SessionManager,
    log_service: LogService,
):
    description = message.text.strip()
    data = await state.get_data()
    project_id = data.get("edit_project_id")
    project, profile = await _load_project(
        project_id,
        message.from_user.id,
        project_service,
        session_manager,
        message,
    )
    if not project:
        return
    await project_service.update_description(project_id, description)
    await log_service.info(f"{profile['name']} توضیحات پروژه {project_id} را تغییر داد")
    await state.clear()
    updated = await project_service.get_project(project_id)
    await message.answer(fa.DESCRIPTION_UPDATED)
    await _send_profile(message, updated, profile, session_manager)


@router.callback_query(OwnerCallback.filter(), StateFilter(ProjectOwnerUpdate.waiting_owner))
async def update_owner(
    callback: types.CallbackQuery,
    callback_data: OwnerCallback,
    state: FSMContext,
    user_service: UserService,
    project_service: ProjectService,
    session_manager: SessionManager,
    log_service: LogService,
):
    profile = session_manager.get_profile(callback.from_user.id)
    if not profile or profile.get("role") != "admin":
        await callback.answer(fa.UNAUTHORIZED, show_alert=True)
        return
    user = await user_service.get_by_id(callback_data.user_id)
    if not user:
        await callback.answer(fa.GENERIC_ERROR, show_alert=True)
        return
    data = await state.get_data()
    project_id = data.get("edit_project_id")
    await project_service.update_owner(project_id, user["name"])
    await log_service.info(f"{profile['name']} مسئول پروژه {project_id} را به {user['name']} تغییر داد")
    await state.clear()
    updated = await project_service.get_project(project_id)
    await callback.answer("✅ مسئول تغییر کرد")
    await callback.message.answer(fa.OWNER_UPDATED)
    await _send_profile(callback.message, updated, profile, session_manager)
