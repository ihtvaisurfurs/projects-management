from datetime import datetime
from typing import Dict, List, Optional

from core.constants import ROLES, STATUS_CHOICES


class ProjectService:
    def __init__(self, database):
        self._db = database

    async def create_project(
        self,
        title: str,
        description: str,
        status: str,
        owner_name: Optional[str],
        start_date: str,
    ) -> int:
        if status not in STATUS_CHOICES:
            raise ValueError("وضعیت انتخاب شده معتبر نیست")
        await self._db.execute(
            """
            INSERT INTO projects(title, description, status, owner_name, start_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (title, description, status, owner_name, start_date),
        )
        row = await self._db.fetchone(
            "SELECT id FROM projects WHERE title = ? ORDER BY id DESC LIMIT 1",
            (title,),
        )
        return row["id"] if row else 0

    async def grouped(self, role: str, owner_name: Optional[str]) -> Dict[str, List[dict]]:
        if role == "admin":
            rows = await self._db.fetchall("SELECT * FROM projects ORDER BY id DESC")
        else:
            rows = await self._db.fetchall(
                "SELECT * FROM projects WHERE owner_name = ? ORDER BY id DESC",
                (owner_name,),
            )
        result: Dict[str, List[dict]] = {status: [] for status in STATUS_CHOICES}
        for row in rows:
            result[row["status"]].append(row)
        return result

    async def list_for_updates(self, role: str, owner_name: Optional[str]) -> List[dict]:
        if role == "admin":
            return await self._db.fetchall("SELECT id, title FROM projects ORDER BY id DESC")
        return await self._db.fetchall(
            "SELECT id, title FROM projects WHERE owner_name = ? ORDER BY id DESC",
            (owner_name,),
        )

    async def get_project(self, project_id: int) -> Optional[dict]:
        return await self._db.fetchone("SELECT * FROM projects WHERE id = ?", (project_id,))

    async def update_status(self, project_id: int, status: str) -> None:
        if status not in STATUS_CHOICES:
            raise ValueError("وضعیت انتخاب شده معتبر نیست")
        end_date = datetime.utcnow().isoformat() if status == "done" else None
        if end_date:
            await self._db.execute(
                "UPDATE projects SET status = ?, end_date = ? WHERE id = ?",
                (status, end_date, project_id),
            )
        else:
            await self._db.execute(
                "UPDATE projects SET status = ?, end_date = NULL WHERE id = ?",
                (status, project_id),
            )

    async def update_owner(self, project_id: int, owner_name: Optional[str]) -> None:
        await self._db.execute(
            "UPDATE projects SET owner_name = ? WHERE id = ?",
            (owner_name, project_id),
        )

    async def update_title(self, project_id: int, title: str) -> None:
        await self._db.execute(
            "UPDATE projects SET title = ? WHERE id = ?",
            (title, project_id),
        )

    async def update_description(self, project_id: int, description: str) -> None:
        await self._db.execute(
            "UPDATE projects SET description = ? WHERE id = ?",
            (description, project_id),
        )
