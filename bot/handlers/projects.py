from datetime import datetime
from html import escape

from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from bot.fsm.states import (
    ProjectDescriptionUpdate,
    ProjectOwnerUpdate,
    ProjectStatusUpdate,
    ProjectTitleUpdate,
)
from bot.keyboards.inline import (
    GroupProjectCallback,
    GroupStatusCallback,
    OwnerCallback,
    ProjectActionCallback,
    StatusCallback,
    delete_confirmation_keyboard,
    group_projects_keyboard,
    group_status_filter_keyboard,
    owner_keyboard,
    project_profile_keyboard,
    status_keyboard,
)
from bot.keyboards.reply import back_keyboard, contact_request_keyboard
from bot.texts import fa
from core.constants import STATUS_LABELS
from services.logging_service import LogService
from services.project_formatter import project_profile_text
from services.project_service import ProjectService
from services.session_manager import SessionManager
from services.user_service import UserService
from services.validators import parse_date

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

async def _notify_group(bot, updates_group_id, project: dict, prefix: str) -> None:
    if not updates_group_id:
        return
    text = f"{prefix}\n{project_profile_text(project)}"
    await bot.send_message(chat_id=updates_group_id, text=text)


async def _load_project(
    project_id: int,
    user_id: int,
    project_service: ProjectService,
    session_manager: SessionManager,
    user_service: UserService,
    target: types.Message,
):
    profile = await session_manager.ensure_profile(user_id, user_service)
    if not profile:
        await target.answer(fa.REQUEST_PHONE, reply_markup=contact_request_keyboard())
        return None, None
    if not profile.get("active", 1):
        session_manager.clear_profile(user_id)
        await target.answer(fa.USER_INACTIVE)
        return None, None
    project = await project_service.get_project(project_id)
    if not project:
        await target.answer(fa.PROJECT_NOT_FOUND)
        return None, profile
    if profile.get("role") != "admin" and project.get("owner_name") != profile.get("name"):
        await target.answer(fa.UNAUTHORIZED)
        return None, profile
    return project, profile


@router.message(F.text == "📊 وضعیت پروژه ها")
async def show_project_links(
    message: types.Message,
    session_manager: SessionManager,
    project_service: ProjectService,
    log_service: LogService,
    bot_username: str,
    user_service: UserService,
):
    if message.chat.type != "private":
        return
    profile = await session_manager.ensure_profile(message.from_user.id, user_service)
    if not profile:
        await message.answer(fa.REQUEST_PHONE, reply_markup=contact_request_keyboard())
        return
    if not profile.get("active", 1):
        session_manager.clear_profile(message.from_user.id)
        await message.answer(fa.USER_INACTIVE)
        return
    projects = await project_service.list_for_updates(profile.get("role"), profile.get("name"))
    if not projects:
        if profile.get("role") == "admin":
            await message.answer(fa.NO_PROJECTS_AVAILABLE)
        else:
            await message.answer(fa.NO_PROJECT_ASSIGNED)
        return
    items = [
        f"• <a href=\"https://t.me/{bot_username}?start=project_{project['id']}\">{escape(project['title'])}</a>"
        for project in projects
    ]
    response = "\n".join([fa.UPDATE_SELECT_PROJECT, *items])
    await message.answer(response, disable_web_page_preview=True)
    await log_service.info(f"{profile['name']} فهرست پروژه‌ها را مشاهده کرد")


@router.message(Command("status"))
async def group_status(
    message: types.Message,
    session_manager: SessionManager,
    project_service: ProjectService,
    log_service: LogService,
    bot_username: str,
    user_service: UserService,
    updates_group_id: int | None,
):
    if message.chat.type not in {"group", "supergroup"}:
        return
    profile = await session_manager.ensure_profile(message.from_user.id, user_service)
    if not profile or profile.get("role") != "admin":
        return
    projects = await project_service.list_for_updates("admin", None)
    if not projects:
        await message.answer(fa.NO_PROJECTS_AVAILABLE)
        return
    await message.answer(
        fa.UPDATE_SELECT_PROJECT,
        reply_markup=group_projects_keyboard(projects),
    )
    await message.answer(
        "فیلتر بر اساس وضعیت:",
        reply_markup=group_status_filter_keyboard(),
    )
    await log_service.info(f"{profile['name']} فهرست پروژه‌ها را در گروه {message.chat.id} ارسال کرد")


@router.callback_query(ProjectActionCallback.filter())
async def handle_project_action(
    callback: types.CallbackQuery,
    callback_data: ProjectActionCallback,
    state: FSMContext,
    project_service: ProjectService,
    session_manager: SessionManager,
    user_service: UserService,
    log_service: LogService,
):
    project, profile = await _load_project(
        callback_data.project_id,
        callback.from_user.id,
        project_service,
        session_manager,
        user_service,
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
    elif action == "delete":
        if profile.get("role") != "admin":
            await callback.answer(fa.UNAUTHORIZED, show_alert=True)
            return
        await callback.message.answer(fa.DELETE_CONFIRMATION, reply_markup=delete_confirmation_keyboard(project["id"]))

    elif action == "delete_confirm":
        if profile.get("role") != "admin":
            await callback.answer(fa.UNAUTHORIZED, show_alert=True)
            return
        await project_service.soft_delete_project(project["id"])
        await log_service.info(f"{profile['name']} پروژه {project['id']} را حذف کرد")
        await callback.answer(fa.PROJECT_DELETED, show_alert=True)
        await callback.message.answer(fa.PROJECT_DELETED)
        await state.clear()
        return
    elif action == "delete_cancel":
        if profile.get("role") != "admin":
            await callback.answer(fa.UNAUTHORIZED, show_alert=True)
            return
        await callback.answer(fa.DELETE_CANCELLED, show_alert=True)
        return
    await callback.answer()


@router.callback_query(StatusCallback.filter(), StateFilter(ProjectStatusUpdate.waiting_status))
async def update_status(
    callback: types.CallbackQuery,
    callback_data: StatusCallback,
    state: FSMContext,
    project_service: ProjectService,
    session_manager: SessionManager,
    log_service: LogService,
    user_service: UserService,
    updates_group_id: int | None,
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
        user_service,
        callback.message,
    )
    if not project:
        await callback.answer()
        return
    if callback_data.value == "done":
        await state.update_data(edit_project_id=project_id, new_status="done")
        await state.set_state(ProjectStatusUpdate.waiting_end_date)
        await callback.message.answer(fa.ASK_PROJECT_END_DATE)
        await callback.answer()
        return
    await project_service.update_status(project_id, callback_data.value)
    updated = await project_service.get_project(project_id)
    await log_service.info(f"{profile['name']} وضعیت پروژه {project_id} را به‌روزرسانی کرد")
    await _notify_group(callback.message.bot, updates_group_id, updated, "پروژه آپدیت شد")
    await state.clear()
    await callback.answer("✅ تغییر انجام شد")
    await callback.message.answer(fa.STATUS_UPDATED)
    await _send_profile(callback.message, updated, profile, session_manager)


@router.message(ProjectStatusUpdate.waiting_end_date)
async def capture_status_end_date(
    message: types.Message,
    state: FSMContext,
    project_service: ProjectService,
    session_manager: SessionManager,
    log_service: LogService,
    user_service: UserService,
    updates_group_id: int | None,
):
    formatted = parse_date(message.text)
    if not formatted:
        await message.answer(fa.INVALID_DATE)
        return
    data = await state.get_data()
    project_id = data.get("edit_project_id")
    project, profile = await _load_project(
        project_id,
        message.from_user.id,
        project_service,
        session_manager,
        user_service,
        message,
    )
    if not project:
        return
    start_date = project.get("start_date")
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(formatted, "%Y-%m-%d")
        if end_dt < start_dt:
            await message.answer(fa.INVALID_END_BEFORE_START)
            return
    await project_service.update_status(project_id, "done", end_date=formatted)
    updated = await project_service.get_project(project_id)
    await log_service.info(f"{profile['name']} وضعیت پروژه {project_id} را به‌روزرسانی کرد")
    await _notify_group(message.bot, updates_group_id, updated, "پروژه آپدیت شد")
    await state.clear()
    await message.answer(fa.STATUS_UPDATED)
    await _send_profile(message, updated, profile, session_manager)


@router.message(ProjectTitleUpdate.waiting_title)
async def apply_new_title(
    message: types.Message,
    state: FSMContext,
    project_service: ProjectService,
    session_manager: SessionManager,
    log_service: LogService,
    user_service: UserService,
    updates_group_id: int | None,
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
        user_service,
        message,
    )
    if not project:
        return
    await project_service.update_title(project_id, title)
    await log_service.info(f"{profile['name']} عنوان پروژه {project_id} را تغییر داد")
    updated = await project_service.get_project(project_id)
    await _notify_group(message.bot, updates_group_id, updated, "پروژه آپدیت شد")
    await state.clear()
    await message.answer(fa.TITLE_UPDATED)
    await _send_profile(message, updated, profile, session_manager)


@router.message(ProjectDescriptionUpdate.waiting_description)
async def apply_new_description(
    message: types.Message,
    state: FSMContext,
    project_service: ProjectService,
    session_manager: SessionManager,
    log_service: LogService,
    user_service: UserService,
    updates_group_id: int | None,
):
    description = message.text.strip()
    data = await state.get_data()
    project_id = data.get("edit_project_id")
    project, profile = await _load_project(
        project_id,
        message.from_user.id,
        project_service,
        session_manager,
        user_service,
        message,
    )
    if not project:
        return
    await project_service.update_description(project_id, description)
    await log_service.info(f"{profile['name']} توضیحات پروژه {project_id} را تغییر داد")
    updated = await project_service.get_project(project_id)
    await _notify_group(message.bot, updates_group_id, updated, "پروژه آپدیت شد")
    await state.clear()
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
    updates_group_id: int | None,
):
    profile = await session_manager.ensure_profile(callback.from_user.id, user_service)
    if not profile:
        await callback.answer(fa.UNAUTHORIZED, show_alert=True)
        return
    if not profile.get("active", 1):
        session_manager.clear_profile(callback.from_user.id)
        await callback.answer(fa.USER_INACTIVE, show_alert=True)
        return
    if profile.get("role") != "admin":
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
    updated = await project_service.get_project(project_id)
    await _notify_group(callback.message.bot, updates_group_id, updated, "پروژه آپدیت شد")
    await state.clear()
    await callback.answer("✅ مسئول تغییر کرد")
    await callback.message.answer(fa.OWNER_UPDATED)
    await _send_profile(callback.message, updated, profile, session_manager)


@router.callback_query(GroupProjectCallback.filter())
async def show_group_project(
    callback: types.CallbackQuery,
    callback_data: GroupProjectCallback,
    project_service: ProjectService,
):
    # Only respond in the same group/supergroup context
    chat = callback.message.chat if callback.message else None
    if not chat or chat.type not in {"group", "supergroup"}:
        await callback.answer()
        return
    project = await project_service.get_project(callback_data.project_id)
    if not project:
        await callback.answer(fa.PROJECT_NOT_FOUND, show_alert=True)
        return
    await callback.answer()
    await callback.message.answer(project_profile_text(project))


@router.callback_query(GroupStatusCallback.filter())
async def show_projects_by_status(
    callback: types.CallbackQuery,
    callback_data: GroupStatusCallback,
    project_service: ProjectService,
):
    chat = callback.message.chat if callback.message else None
    if not chat or chat.type not in {"group", "supergroup"}:
        await callback.answer()
        return
    projects = await project_service.list_for_updates("admin", None)
    filtered = [p for p in projects if p.get("status") == callback_data.status]
    if not filtered:
        await callback.answer(fa.NO_PROJECTS_IN_STATUS, show_alert=True)
        return
    lines = [f"📌 پروژه‌های {STATUS_LABELS.get(callback_data.status, callback_data.status)}:"]
    for proj in filtered:
        lines.append(f"• {proj['title']}")
    await callback.answer()
    await callback.message.answer("\n".join(lines))


