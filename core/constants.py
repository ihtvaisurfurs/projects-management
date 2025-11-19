from dataclasses import dataclass

BACK_TO_MENU = "↩️ برگشت به منوی اصلی"
REQUEST_PHONE_BUTTON = "📱 ارسال شماره همراه من"
ADMIN_MENU_BUTTONS = [
    "📊 وضعیت پروژه ها",
    "👥 کاربرها",
    "➕ تعریف پروژه",
    BACK_TO_MENU,
]
USER_MENU_BUTTONS = [
    "📄 لیست کاربران",
    "👤 تعریف کاربر جدید",
    BACK_TO_MENU,
]
PROGRAMMER_MENU_BUTTONS = [
    "📊 وضعیت پروژه ها",
    BACK_TO_MENU,
]
ROLES = ("admin", "programmer")
STATUS_CHOICES = ["pending", "in_progress", "MVP", "support_update", "done", "failed", "deleted"]
VISIBLE_STATUSES = ["pending", "in_progress", "MVP", "support_update", "done", "failed"]
STATUS_LABELS = {
    "pending": "🟡 در انتظار",
    "in_progress": "🚧 درحال انجام",
    "MVP": "🟢 نسخه MVP",
    "support_update": "🔧 پشتیبانی و ارتقا",
    "done": "✅ تکمیل شده",
    "failed": "❌ شکست خورده",
    "deleted": "🗑 حذف شده",
}
PROJECT_GROUP_LABELS = {
    "pending": "پروژه‌های تعریف شده",
    "in_progress": "پروژه‌های درحال انجام",
    "MVP": "پروژه‌های MVP",
    "support_update": "پروژه‌های درحال پشتیبانی و ارتقای عملکرد",
    "done": "پروژه‌های تکمیل شده",
    "failed": "پروژه‌های شکست خورده",
}
SKIP_OWNER_BUTTON = "🚫 عدم انتخاب مسئول"
SKIP_DESCRIPTION_BUTTON = "⏭️ بدون توضیحات"
DATE_FORMATS = ("%Y/%m/%d", "%Y-%m-%d")

@dataclass(frozen=True)
class AppPaths:
    logs_root: str = "logs"
    migrations_dir: str = "data/migrations"
    default_db: str = "data/app.db"
