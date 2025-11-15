from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.constants import ROLES, SKIP_OWNER_BUTTON, STATUS_CHOICES, STATUS_LABELS


class RoleCallback(CallbackData, prefix="role"):
    value: str


class StatusCallback(CallbackData, prefix="status"):
    value: str


class OwnerCallback(CallbackData, prefix="owner"):
    user_id: int


class ProjectActionCallback(CallbackData, prefix="project"):
    project_id: int
    action: str


def role_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for role in ROLES:
        label = "👑 ادمین" if role == "admin" else "👨‍💻 برنامه‌نویس"
        builder.button(text=label, callback_data=RoleCallback(value=role))
    builder.adjust(2)
    return builder.as_markup()


def status_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for status in STATUS_CHOICES:
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
    builder.adjust(1)
    return builder.as_markup()
