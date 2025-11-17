from datetime import datetime
from typing import Dict, List, Optional

from core.constants import STATUS_CHOICES, VISIBLE_STATUSES


class ProjectService:
    def __init__(self, database):
        self._db = database

    def _today(self) -> str:
        return datetime.utcnow().strftime("%Y-%m-%d")

    async def create_project(
        self,
        title: str,
        description: str,
        status: str,
        owner_name: Optional[str],
        start_date: str,
        end_date: Optional[str] = None,
    ) -> int:
        if status not in STATUS_CHOICES:
            raise ValueError("وضعیت انتخاب شده معتبر نیست")
        if status == "done" and not end_date:
            raise ValueError("تاریخ پایان برای وضعیت تکمیل شده الزامی است")
        await self._db.execute(
            """
            INSERT INTO projects(title, description, status, owner_name, start_date, end_date, deleted_at)
            VALUES (?, ?, ?, ?, ?, ?, NULL)
            """,
            (title, description, status, owner_name, start_date, end_date),
        )
        row = await self._db.fetchone(
            "SELECT id FROM projects WHERE title = ? ORDER BY id DESC LIMIT 1",
            (title,),
        )
        project_id = row["id"] if row else 0
        if owner_name:
            await self._add_owner_history(project_id, owner_name, start_date)
        return project_id

    async def grouped(self, role: str, owner_name: Optional[str]) -> Dict[str, List[dict]]:
        params = []
        base_query = "SELECT * FROM projects WHERE status != 'deleted'"
        if role != "admin":
            base_query += " AND owner_name = ?"
            params.append(owner_name)
        base_query += " ORDER BY id DESC"
        rows = await self._db.fetchall(base_query, tuple(params))
        result: Dict[str, List[dict]] = {status: [] for status in VISIBLE_STATUSES}
        for row in rows:
            if row["status"] in result:
                result[row["status"]].append(row)
        return result

    async def list_for_updates(self, role: str, owner_name: Optional[str]) -> List[dict]:
        params = []
        base_query = "SELECT id, title, status FROM projects WHERE status != 'deleted'"
        if role != "admin":
            base_query += " AND owner_name = ?"
            params.append(owner_name)
        base_query += " ORDER BY id DESC"
        return await self._db.fetchall(base_query, tuple(params))

    async def get_project(self, project_id: int, include_deleted: bool = False) -> Optional[dict]:
        if include_deleted:
            return await self._db.fetchone("SELECT * FROM projects WHERE id = ?", (project_id,))
        return await self._db.fetchone(
            "SELECT * FROM projects WHERE id = ? AND status != 'deleted'",
            (project_id,),
        )

    async def update_status(self, project_id: int, status: str, end_date: Optional[str] = None) -> None:
        if status == "deleted":
            raise ValueError("برای حذف از soft_delete_project استفاده کنید")
        if status not in STATUS_CHOICES:
            raise ValueError("وضعیت انتخاب شده معتبر نیست")
        if status == "done" and not end_date:
            raise ValueError("تاریخ پایان برای وضعیت تکمیل شده الزامی است")
        end_value = end_date if status == "done" else None
        await self._db.execute(
            "UPDATE projects SET status = ?, end_date = ?, deleted_at = NULL WHERE id = ?",
            (status, end_value, project_id),
        )

    async def update_owner(self, project_id: int, owner_name: Optional[str]) -> None:
        project = await self.get_project(project_id, include_deleted=True)
        if not project:
            return
        if project.get("owner_name") == owner_name:
            return
        now = self._today()
        await self._close_open_owner_history(project_id, now)
        await self._db.execute(
            "UPDATE projects SET owner_name = ? WHERE id = ?",
            (owner_name, project_id),
        )
        if owner_name:
            await self._add_owner_history(project_id, owner_name, now)

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

    async def soft_delete_project(self, project_id: int) -> None:
        now = self._today()
        await self._db.execute(
            "UPDATE projects SET status = 'deleted', deleted_at = ? WHERE id = ?",
            (now, project_id),
        )
        await self._close_open_owner_history(project_id, now)

    async def get_owner_history(self, project_id: int) -> List[dict]:
        return await self._db.fetchall(
            """
            SELECT project_id, owner_name, from_date, to_date
            FROM project_owner_history
            WHERE project_id = ?
            ORDER BY id ASC
            """,
            (project_id,),
        )

    async def _add_owner_history(self, project_id: int, owner_name: str, from_date: str) -> None:
        await self._db.execute(
            """
            INSERT INTO project_owner_history(project_id, owner_name, from_date, to_date)
            VALUES (?, ?, ?, NULL)
            """,
            (project_id, owner_name, from_date),
        )

    async def _close_open_owner_history(self, project_id: int, until: str) -> None:
        await self._db.execute(
            "UPDATE project_owner_history SET to_date = ? WHERE project_id = ? AND to_date IS NULL",
            (until, project_id),
        )
