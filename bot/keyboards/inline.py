from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.constants import ROLES, VISIBLE_STATUSES, STATUS_LABELS


class RoleCallback(CallbackData, prefix="role"):
    value: str


class StatusCallback(CallbackData, prefix="status"):
    value: str


class OwnerCallback(CallbackData, prefix="owner"):
    user_id: int


class ProjectActionCallback(CallbackData, prefix="project"):
    project_id: int
    action: str


class UserActionCallback(CallbackData, prefix="user"):
    user_id: int
    action: str


class GroupProjectCallback(CallbackData, prefix="gproj"):
    project_id: int


class StatusFilterCallback(CallbackData, prefix="statusfilter"):
    status: str


def role_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for role in ROLES:
        label = "👑 ادمین" if role == "admin" else "👨‍💻 برنامه‌نویس"
        builder.button(text=label, callback_data=RoleCallback(value=role))
        
    builder.adjust(2)
    return builder.as_markup()


def status_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for status in VISIBLE_STATUSES:
        builder.button(
            text=STATUS_LABELS.get(status, status),
            callback_data=StatusCallback(value=status),
        )
    builder.adjust(2)
    return builder.as_markup()


def owner_keyboard(users) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for user in users:
        builder.button(
            text=f"👤 {user['name']}",
            callback_data=OwnerCallback(user_id=user["id"]),
        )
    builder.adjust(2)
    return builder.as_markup()


def project_profile_keyboard(project_id: int, is_admin: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔄 تغییر وضعیت",
        callback_data=ProjectActionCallback(project_id=project_id, action="status"),
    )
    builder.button(
        text="✏️ تغییر نام پروژه",
        callback_data=ProjectActionCallback(project_id=project_id, action="title"),
    )
    builder.button(
        text="📝 تغییر توضیحات پروژه",
        callback_data=ProjectActionCallback(project_id=project_id, action="description"),
    )
    if is_admin:
        builder.button(
            text="👥 تغییر مسئول پروژه",
            callback_data=ProjectActionCallback(project_id=project_id, action="owner"),
        )
        builder.button(
            text="🗑 حذف پروژه",
            callback_data=ProjectActionCallback(project_id=project_id, action="delete"),
        )
    builder.adjust(1)
    return builder.as_markup()


def delete_confirmation_keyboard(project_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ تأیید حذف",
        callback_data=ProjectActionCallback(project_id=project_id, action="delete_confirm"),
    )
    builder.button(
        text="❌ انصراف",
        callback_data=ProjectActionCallback(project_id=project_id, action="delete_cancel"),
    )
    builder.adjust(1)
    return builder.as_markup()


def user_list_keyboard(users) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for user in users:
        status = "✅" if user.get("active", 1) else "🚫"
        builder.button(
            text=f"{status} {user['name']}",
            callback_data=UserActionCallback(user_id=user["id"], action="view"),
        )
    builder.adjust(1)
    return builder.as_markup()


def user_profile_keyboard(user_id: int, is_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    action = "deactivate" if is_active else "activate"
    label = "🚫 غیرفعال کردن" if is_active else "✅ فعال کردن"
    builder.button(
        text=label,
        callback_data=UserActionCallback(user_id=user_id, action=action),
    )
    return builder.as_markup()


def group_projects_keyboard(projects) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for project in projects:
        builder.button(
            text=project["title"],
            callback_data=GroupProjectCallback(project_id=project["id"]),
        )
    builder.adjust(1)
    return builder.as_markup()


def status_filter_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for status in VISIBLE_STATUSES:
        builder.button(
            text=STATUS_LABELS.get(status, status),
            callback_data=StatusFilterCallback(status=status),
        )
    builder.adjust(2)
    return builder.as_markup()
