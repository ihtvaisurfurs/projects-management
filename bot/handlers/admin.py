from datetime import datetime

from aiogram import F, Router, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from bot.fsm.states import AdminCreateProject, AdminCreateUser
from bot.keyboards.inline import (
    OwnerCallback,
    RoleCallback,
    StatusCallback,
    UserActionCallback,
    owner_keyboard,
    role_keyboard,
    status_keyboard,
    user_list_keyboard,
    user_profile_keyboard,
)
from bot.keyboards.reply import (
    back_keyboard,
    contact_request_keyboard,
    description_keyboard,
    owner_skip_keyboard,
    user_menu_keyboard,
)
from bot.texts import fa
from services.project_formatter import project_profile_text
from core.constants import BACK_TO_MENU, SKIP_DESCRIPTION_BUTTON, SKIP_OWNER_BUTTON
from services.logging_service import LogService
from services.menu_service import MenuService
from services.project_service import ProjectService
from services.session_manager import SessionManager
from services.user_service import UserService
from services.validators import is_valid_phone, parse_date

router = Router()


async def _ensure_admin(message: types.Message, session_manager: SessionManager, user_service: UserService):
    profile = await session_manager.ensure_profile(message.from_user.id, user_service)
    if not profile:
        await message.answer(fa.REQUEST_PHONE, reply_markup=contact_request_keyboard())
        return None
    if not profile.get("active", 1):
        session_manager.clear_profile(message.from_user.id)
        await message.answer(fa.USER_INACTIVE)
        return None
    if profile.get("role") != "admin":
        await message.answer(fa.UNAUTHORIZED)
        return None
    return profile


async def _ensure_admin_callback(callback: types.CallbackQuery, session_manager: SessionManager, user_service: UserService):
    profile = await session_manager.ensure_profile(callback.from_user.id, user_service)
    if not profile:
        await callback.answer(fa.UNAUTHORIZED, show_alert=True)
        return None
    if not profile.get("active", 1):
        session_manager.clear_profile(callback.from_user.id)
        await callback.answer(fa.USER_INACTIVE, show_alert=True)
        return None
    if profile.get("role") != "admin":
        await callback.answer(fa.UNAUTHORIZED, show_alert=True)
        return None
    return profile


async def _notify_group(bot, updates_group_id, project: dict, prefix: str) -> None:
    if not updates_group_id:
        return
    text = f"{prefix}\n{project_profile_text(project)}"
    await bot.send_message(chat_id=updates_group_id, text=text)


@router.message(F.text == "👥 کاربرها")
async def user_menu(
    message: types.Message,
    state: FSMContext,
    session_manager: SessionManager,
    user_service: UserService,
):
    profile = await _ensure_admin(message, session_manager, user_service)
    if not profile:
        return
    await state.clear()
    await message.answer("یکی از گزینه‌های کاربری را انتخاب کنید:", reply_markup=user_menu_keyboard())


@router.message(F.text == "📄 لیست کاربران")
async def list_users(
    message: types.Message,
    session_manager: SessionManager,
    user_service: UserService,
    log_service: LogService,
):
    profile = await _ensure_admin(message, session_manager, user_service)
    if not profile:
        return
    users = await user_service.list_users()
    if not users:
        await message.answer(fa.USER_LIST_EMPTY)
        return
    await message.answer(
        fa.USER_LIST_TITLE,
        reply_markup=user_list_keyboard(users),
    )
    await log_service.info(f"{profile['name']} لیست کاربران را مشاهده کرد")


@router.callback_query(UserActionCallback.filter())
async def handle_user_actions(
    callback: types.CallbackQuery,
    callback_data: UserActionCallback,
    user_service: UserService,
    session_manager: SessionManager,
    log_service: LogService,
):
    profile = await _ensure_admin_callback(callback, session_manager, user_service)
    if not profile:
        return
    user = await user_service.get_by_id(callback_data.user_id)
    if not user:
        await callback.answer(fa.GENERIC_ERROR, show_alert=True)
        return
    action = callback_data.action
    if action == "view":
        status = "فعال" if user.get("active", 1) else "غیرفعال"
        details = (
            f"👤 نام: {user['name']}\n"
            f"📞 تلفن: {user['phone']}\n"
            f"🎯 نقش: {user['role']}\n"
            f"📅 ثبت: {user.get('created_at','—')}\n"
            f"وضعیت: {status}"
        )
        await callback.message.answer(
            details,
            reply_markup=user_profile_keyboard(user["id"], bool(user.get("active", 1))),
        )
        await callback.answer()
        return
    if action in {"deactivate", "activate"}:
        new_state = action == "activate"
        await user_service.set_active(user["id"], new_state)
        updated_user = await user_service.get_by_id(callback_data.user_id)
        telegram_id = updated_user.get("telegram_id") if updated_user else None
        if telegram_id:
            if new_state:
                session_manager.set_profile(telegram_id, updated_user)
            else:
                session_manager.clear_profile(telegram_id)
        await log_service.info(
            f"{profile['name']} وضعیت کاربر {user['name']} را به {'فعال' if new_state else 'غیرفعال'} تغییر داد"
        )
        await callback.answer(
            fa.USER_ACTIVATED if new_state else fa.USER_DEACTIVATED,
            show_alert=True,
        )
        return
    await callback.answer()

@router.message(F.text == "👤 تعریف کاربر جدید")
async def new_user_entry(
    message: types.Message,
    state: FSMContext,
    session_manager: SessionManager,
    user_service: UserService,
):
    profile = await _ensure_admin(message, session_manager, user_service)
    if not profile:
        return
    await state.set_state(AdminCreateUser.waiting_phone)
    await message.answer(fa.ASK_NEW_USER_PHONE, reply_markup=back_keyboard())


@router.message(AdminCreateUser.waiting_phone)
async def capture_user_phone(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    if not is_valid_phone(phone):
        await message.answer(fa.INVALID_PHONE)
        return
    await state.update_data(new_user_phone=phone)
    await state.set_state(AdminCreateUser.waiting_name)
    await message.answer(fa.ASK_NEW_USER_NAME)


@router.message(AdminCreateUser.waiting_name)
async def capture_user_name(
    message: types.Message,
    state: FSMContext,
    session_manager: SessionManager,
    user_service: UserService,
):
    name = message.text.strip()
    if len(name) < 3:
        await message.answer("❗️ لطفاً نام معتبر وارد کنید.")
        return
    await state.update_data(new_user_name=name)
    await state.set_state(AdminCreateUser.waiting_role)
    await message.answer(fa.ASK_NEW_USER_ROLE)
    inline_message = await message.answer(
        "نقش را از بین گزینه‌ها انتخاب کنید:",
        reply_markup=role_keyboard(),
    )
    session_manager.add_inline_message(message.from_user.id, inline_message.message_id)


@router.callback_query(RoleCallback.filter(), StateFilter(AdminCreateUser.waiting_role))
async def select_user_role(
    callback: types.CallbackQuery,
    callback_data: RoleCallback,
    state: FSMContext,
    user_service: UserService,
    session_manager: SessionManager,
    menu_service: MenuService,
    log_service: LogService,
):
    profile = await _ensure_admin_callback(callback, session_manager, user_service)
    if not profile:
        return
    data = await state.get_data()
    phone = data.get("new_user_phone")
    name = data.get("new_user_name")
    if not phone or not name:
        await callback.answer(fa.GENERIC_ERROR, show_alert=True)
        return
    existing = await user_service.get_by_phone(phone)
    if existing:
        await callback.answer(fa.USER_EXISTS, show_alert=True)
        return
    await user_service.create_user(phone, name, callback_data.value)
    await state.clear()
    await callback.answer("ذخیره شد ✅")
    await callback.message.answer(fa.USER_CREATED)
    await log_service.info(f"ادمین {profile['name']} کاربر جدیدی ایجاد کرد ({name})")
    await menu_service.show_main_menu(callback.message, profile)


@router.message(F.text == "➕ تعریف پروژه")
async def create_project_entry(
    message: types.Message,
    state: FSMContext,
    session_manager: SessionManager,
    user_service: UserService,
):
    profile = await _ensure_admin(message, session_manager, user_service)
    if not profile:
        return
    await state.set_state(AdminCreateProject.waiting_title)
    await message.answer(fa.ASK_PROJECT_TITLE, reply_markup=back_keyboard())


@router.message(AdminCreateProject.waiting_title)
async def capture_project_title(message: types.Message, state: FSMContext):
    title = message.text.strip()
    if len(title) < 3:
        await message.answer("❗️ عنوان پروژه باید حداقل ۳ کاراکتر باشد.")
        return
    await state.update_data(project_title=title)
    await state.set_state(AdminCreateProject.waiting_description)
    await message.answer(fa.ASK_PROJECT_DESCRIPTION, reply_markup=description_keyboard())


@router.message(AdminCreateProject.waiting_description)
async def capture_project_description(
    message: types.Message,
    state: FSMContext,
    session_manager: SessionManager,
):
    description = message.text.strip()
    if description == "-":
        await message.answer("⚠️ برای رد کردن توضیحات از دکمه مخصوص استفاده کنید.")
        return
    if description == SKIP_DESCRIPTION_BUTTON:
        description = ""
    await state.update_data(project_description=description)
    await state.set_state(AdminCreateProject.waiting_status)
    await message.answer(fa.ASK_PROJECT_STATUS, reply_markup=None)
    inline_message = await message.answer(
        "یکی از وضعیت‌ها را انتخاب کنید:",
        reply_markup=status_keyboard(),
    )
    session_manager.add_inline_message(message.from_user.id, inline_message.message_id)


@router.callback_query(StatusCallback.filter(), StateFilter(AdminCreateProject.waiting_status))
async def select_project_status(
    callback: types.CallbackQuery,
    callback_data: StatusCallback,
    state: FSMContext,
    session_manager: SessionManager,
    user_service: UserService,
):
    profile = await _ensure_admin_callback(callback, session_manager, user_service)
    if not profile:
        return
    await state.update_data(project_status=callback_data.value)
    await state.set_state(AdminCreateProject.waiting_owner)
    users = await user_service.list_users()
    if users:
        await callback.message.answer(fa.ASK_PROJECT_OWNER, reply_markup=owner_skip_keyboard())
        inline_message = await callback.message.answer(
            "لیست کاربران:",
            reply_markup=owner_keyboard(users),
        )
        session_manager.add_inline_message(callback.from_user.id, inline_message.message_id)
    else:
        await callback.message.answer(
            "هیچ کاربری برای تخصیص وجود ندارد. از دکمه عدم انتخاب مسئول استفاده کنید.",
            reply_markup=owner_skip_keyboard(),
        )
    await callback.answer()


@router.callback_query(OwnerCallback.filter(), StateFilter(AdminCreateProject.waiting_owner))
async def select_project_owner(
    callback: types.CallbackQuery,
    callback_data: OwnerCallback,
    state: FSMContext,
    user_service: UserService,
    session_manager: SessionManager,
):
    profile = await _ensure_admin_callback(callback, session_manager, user_service)
    if not profile:
        return
    user = await user_service.get_by_id(callback_data.user_id)
    owner_name = user["name"] if user else None
    await state.update_data(project_owner=owner_name)
    await state.set_state(AdminCreateProject.waiting_start_date)
    await callback.message.answer(fa.ASK_PROJECT_START_DATE)
    await callback.answer("✅ مسئول انتخاب شد")


@router.message(StateFilter(AdminCreateProject.waiting_owner), F.text == SKIP_OWNER_BUTTON)
async def skip_owner(message: types.Message, state: FSMContext):
    await state.update_data(project_owner=None)
    await state.set_state(AdminCreateProject.waiting_start_date)
    await message.answer(fa.ASK_PROJECT_START_DATE)


@router.message(AdminCreateProject.waiting_start_date)
async def capture_start_date(
    message: types.Message,
    state: FSMContext,
    project_service: ProjectService,
    session_manager: SessionManager,
    log_service: LogService,
    menu_service: MenuService,
    user_service: UserService,
    updates_group_id: int | None,
):
    if message.text == BACK_TO_MENU:
        await state.clear()
        profile = await session_manager.ensure_profile(message.from_user.id, user_service)
        if profile:
            await menu_service.show_main_menu(message, profile)
        else:
            from bot.keyboards.reply import contact_request_keyboard
            await message.answer(fa.REQUEST_PHONE, reply_markup=contact_request_keyboard())
        return
    formatted = parse_date(message.text)
    if not formatted:
        await message.answer(fa.INVALID_DATE)
        return
    await state.update_data(project_start_date=formatted)
    data = await state.get_data()
    if data.get("project_status") == "done":
        await state.set_state(AdminCreateProject.waiting_end_date)
        await message.answer(fa.ASK_PROJECT_END_DATE)
        return
    profile = await session_manager.ensure_profile(message.from_user.id, user_service)
    project_id = await project_service.create_project(
        title=data.get("project_title"),
        description=data.get("project_description", ""),
        status=data.get("project_status"),
        owner_name=data.get("project_owner"),
        start_date=formatted,
    )
    await log_service.info(f"ادمین {profile['name']} پروژه‌ای جدید ایجاد کرد ({data.get('project_title')})")
    new_project = await project_service.get_project(project_id)
    if new_project:
        await _notify_group(message.bot, updates_group_id, new_project, "پروژه جدید ایجاد شد")
    await state.clear()
    await message.answer(fa.PROJECT_CREATED)
    await menu_service.show_main_menu(message, profile)


@router.message(AdminCreateProject.waiting_end_date)
async def capture_end_date(
    message: types.Message,
    state: FSMContext,
    project_service: ProjectService,
    session_manager: SessionManager,
    log_service: LogService,
    menu_service: MenuService,
    user_service: UserService,
    updates_group_id: int | None,
):
    formatted = parse_date(message.text)
    if not formatted:
        await message.answer(fa.INVALID_DATE)
        return
    data = await state.get_data()
    start_date = data.get("project_start_date")
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(formatted, "%Y-%m-%d")
        if end_dt < start_dt:
            await message.answer(fa.INVALID_END_BEFORE_START)
            return
    profile = await session_manager.ensure_profile(message.from_user.id, user_service)
    project_id = await project_service.create_project(
        title=data.get("project_title"),
        description=data.get("project_description", ""),
        status=data.get("project_status"),
        owner_name=data.get("project_owner"),
        start_date=start_date or formatted,
        end_date=formatted,
    )
    await log_service.info(f"ادمین {profile['name']} پروژه‌ای جدید ایجاد کرد ({data.get('project_title')})")
    new_project = await project_service.get_project(project_id)
    if new_project:
        await _notify_group(message.bot, updates_group_id, new_project, "پروژه جدید ایجاد شد")
    await state.clear()
    await message.answer(fa.PROJECT_CREATED)
    await menu_service.show_main_menu(message, profile)


