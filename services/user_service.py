from datetime import datetime
from typing import List, Optional

from core.constants import ROLES


class UserService:
    def __init__(self, database):
        self._db = database

    async def get_by_phone(self, phone: str) -> Optional[dict]:
        return await self._db.fetchone("SELECT * FROM users WHERE phone = ?", (phone,))

    async def create_user(self, phone: str, name: str, role: str) -> int:
        if role not in ROLES:
            raise ValueError("نقش انتخاب شده معتبر نیست")
        created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        await self._db.execute(
            "INSERT INTO users(phone, name, role, created_at) VALUES (?, ?, ?, ?)",
            (phone, name, role, created_at),
        )
        row = await self._db.fetchone("SELECT id FROM users WHERE phone = ?", (phone,))
        return row["id"] if row else 0

    async def list_users(self) -> List[dict]:
        return await self._db.fetchall("SELECT * FROM users ORDER BY name ASC")

    async def get_by_name(self, name: str) -> Optional[dict]:
        return await self._db.fetchone("SELECT * FROM users WHERE name = ?", (name,))

    async def get_by_id(self, user_id: int) -> Optional[dict]:
        return await self._db.fetchone("SELECT * FROM users WHERE id = ?", (user_id,))

    async def get_by_telegram(self, telegram_id: int) -> Optional[dict]:
        return await self._db.fetchone("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))

    async def update_telegram_id(self, user_id: int, telegram_id: int) -> None:
        await self._db.execute(
            "UPDATE users SET telegram_id = ? WHERE id = ?",
            (telegram_id, user_id),
        )
