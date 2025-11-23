from __future__ import annotations
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from core.constants import PROJECT_GROUP_LABELS, STATUS_LABELS


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def log_directory(root: str) -> Path:
    now = datetime.utcnow()
    target = Path(root) / str(now.year) / f"{now.month:02d}"
    ensure_directory(target)
    return target


def human_status(status: str) -> str:
    return STATUS_LABELS.get(status, status)


def format_project_block(title: str, projects: List[Dict]) -> str:
    if not projects:
        return f"\n🔸 {title}:\n   └ هیچ موردی ثبت نشده است."
    lines = [f"\n🔸 {title}:"]
    for project in projects:
        owner = project.get("owner_name") or "—"
        version = project.get("version", "0")
        version_date = project.get("version_updated_at") or "—"
        end_date = project.get("end_date")
        base = (
            f"• {project['title']}\n"
            f"  🧑‍💻 مسئول: {owner}\n"
            f"  📌 وضعیت: {human_status(project['status'])}\n"
            f"  🗓 شروع: {project['start_date']}\n"
            f"  🧩 ورژن: {version} (تاریخ: {version_date})"
        )
        if end_date:
            base += f"\n  ✅ پایان: {end_date}"
        if project.get("description"):
            base += f"\n  📝 توضیح: {project['description']}"
        lines.append(base)
    return "\n".join(lines)


def grouped_projects_text(grouped: Dict[str, List[Dict]]) -> str:
    sections = ["📁 فهرست پروژه‌ها:"]
    for status, label in PROJECT_GROUP_LABELS.items():
        sections.append(format_project_block(label, grouped.get(status, [])))
    return "\n".join(sections)


def chunk_list(items: List, size: int) -> List[List]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def normalize_phone(phone: str) -> str:
    phone = phone.strip()
    if not phone.startswith("+") and phone.startswith("00"):
        phone = "+" + phone[2:]
    return phone


def ensure_async(func):
    if asyncio.iscoroutinefunction(func):
        return func

    async def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper
