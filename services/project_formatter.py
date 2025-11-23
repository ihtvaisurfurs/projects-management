from typing import Dict

from core.utils import human_status


def project_profile_text(project: Dict) -> str:
    end_date = project.get("end_date") or "—"
    owner = project.get("owner_name") or "—"
    description = project.get("description") or "—"
    version = project.get("version", "0")
    version_date = project.get("version_updated_at") or "—"
    return (
        f"🗂 عنوان: {project['title']}\n"
        f"📝 توضیحات: {description}\n"
        f"📌 وضعیت: {human_status(project['status'])}\n"
        f"👤 مسئول: {owner}\n"
        f"🗓 شروع: {project['start_date']}\n"
        f"✅ پایان: {end_date}\n"
        f"🧩 ورژن: {version}\n"
        f"📅 آخرین تاریخ ورژن: {version_date}"
    )
