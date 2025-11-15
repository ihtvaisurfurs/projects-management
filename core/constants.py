from dataclasses import dataclass

BACK_TO_MENU = "↩️ برگشت به منوی اصلی"
REQUEST_PHONE_BUTTON = "📱 ارسال شماره همراه من"
ADMIN_MENU_BUTTONS = [
    "📊 وضعیت پروژه ها",
    "👤 تعریف کاربر جدید",
    "➕ تعریف پروژه",
    "🛠 آپدیت پروژه",
    BACK_TO_MENU,
]
PROGRAMMER_MENU_BUTTONS = [
    "📊 وضعیت پروژه ها",
    "🛠 آپدیت پروژه",
    BACK_TO_MENU,
]
ROLES = ("admin", "programmer")
STATUS_CHOICES = ["pending", "MVP", "support_update", "done"]
STATUS_LABELS = {
    "pending": "🟡 در انتظار",
    "MVP": "🟢 نسخه MVP",
    "support_update": "🔧 پشتیبانی و ارتقا",
    "done": "✅ تکمیل شده",
}
PROJECT_GROUP_LABELS = {
    "pending": "پروژه‌های تعریف شده",
    "MVP": "پروژه‌های MVP",
    "support_update": "پروژه‌های درحال پشتیبانی و ارتقای عملکرد",
    "done": "پروژه‌های تکمیل شده",
}
SKIP_OWNER_BUTTON = "🚫 عدم انتخاب مسئول"
SKIP_DESCRIPTION_BUTTON = "⏭️ بدون توضیحات"
DATE_FORMATS = ("%Y/%m/%d", "%Y-%m-%d")

@dataclass(frozen=True)
class AppPaths:
    logs_root: str = "logs"
    migrations_dir: str = "data/migrations"
    default_db: str = "data/app.db"
