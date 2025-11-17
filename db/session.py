from __future__ import annotations
import asyncio
from pathlib import Path
from typing import Any, Iterable, List, Optional

import aiosqlite


class Database:
    def __init__(self, path: str):
        self.path = path
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)

    async def _open(self) -> aiosqlite.Connection:
        conn = await aiosqlite.connect(self.path)
        conn.row_factory = aiosqlite.Row
        return conn

    async def execute(self, query: str, params: Iterable[Any] = ()) -> None:
        conn = await self._open()
        try:
            await conn.execute(query, tuple(params))
            await conn.commit()
        finally:
            await conn.close()

    async def fetchone(self, query: str, params: Iterable[Any] = ()) -> Optional[dict]:
        conn = await self._open()
        try:
            cursor = await conn.execute(query, tuple(params))
            row = await cursor.fetchone()
            await cursor.close()
            if row is None:
                return None
            return dict(row)
        finally:
            await conn.close()

    async def fetchall(self, query: str, params: Iterable[Any] = ()) -> List[dict]:
        conn = await self._open()
        try:
            cursor = await conn.execute(query, tuple(params))
            rows = await cursor.fetchall()
            await cursor.close()
            return [dict(row) for row in rows]
        finally:
            await conn.close()

    async def executescript(self, script: str) -> None:
        conn = await self._open()
        try:
            await conn.executescript(script)
            await conn.commit()
        finally:
            await conn.close()

    async def column_exists(self, table: str, column: str) -> bool:
        conn = await self._open()
        try:
            cursor = await conn.execute(f"PRAGMA table_info({table})")
            rows = await cursor.fetchall()
            await cursor.close()
            return any(row["name"] == column for row in rows)
        finally:
            await conn.close()

    async def run_migrations(self, directory: str) -> None:
        path = Path(directory)
        if not path.exists():
            return
        await self.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY)"
        )
        for sql_file in sorted(path.glob("*.sql")):
            name = sql_file.name
            applied = await self.fetchone(
                "SELECT 1 FROM schema_migrations WHERE name = ?",
                (name,),
            )
            if applied:
                continue
            script = sql_file.read_text(encoding="utf-8")
            # Skip idempotent migrations if column already exists
            if "telegram_id" in script and await self.column_exists("users", "telegram_id"):
                await self.execute(
                    "INSERT INTO schema_migrations(name) VALUES (?)",
                    (name,),
                )
                continue
            if "created_at" in script and await self.column_exists("users", "created_at"):
                await self.execute(
                    "INSERT INTO schema_migrations(name) VALUES (?)",
                    (name,),
                )
                continue
            await self.executescript(script)
            await self.execute(
                "INSERT INTO schema_migrations(name) VALUES (?)",
                (name,),
            )
