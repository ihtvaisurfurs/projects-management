import json
from pathlib import Path
from typing import Dict, Optional, Set


class SessionManager:
    def __init__(self, storage_path: str = "data/session_cache.json") -> None:
        self._profiles: Dict[int, dict] = {}
        self._pending_project: Dict[int, int] = {}
        self._inline_messages: Dict[int, Set[int]] = {}
        self._storage_path = Path(storage_path)
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self) -> None:
        if not self._storage_path.exists():
            return
        try:
            data = json.loads(self._storage_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        if isinstance(data, dict):
            self._profiles = {int(k): v for k, v in data.items()}

    def _save(self) -> None:
        try:
            self._storage_path.write_text(
                json.dumps(self._profiles, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError:
            pass

    def set_profile(self, user_id: int, profile: dict) -> None:
        self._profiles[user_id] = profile
        self._save()

    def get_profile(self, user_id: int) -> Optional[dict]:
        return self._profiles.get(user_id)

    async def ensure_profile(self, user_id: int, user_service) -> Optional[dict]:
        """
        Validate the cached profile against DB; clears cache if user is missing or inactive.
        """
        cached = self._profiles.get(user_id)
        db_user = await user_service.get_by_telegram(user_id)
        if not db_user or not db_user.get("active", 1):
            self.clear_profile(user_id)
            return None
        if not cached or cached != db_user:
            self.set_profile(user_id, db_user)
            return db_user
        return cached

    def clear_profile(self, user_id: int) -> None:
        updated = self._profiles.pop(user_id, None)
        self._pending_project.pop(user_id, None)
        if updated is not None:
            self._save()

    def set_pending_project(self, user_id: int, project_id: int) -> None:
        self._pending_project[user_id] = project_id

    def pop_pending_project(self, user_id: int) -> Optional[int]:
        return self._pending_project.pop(user_id, None)

    def add_inline_message(self, user_id: int, message_id: int) -> None:
        self._inline_messages.setdefault(user_id, set()).add(message_id)

    def consume_inline_messages(self, user_id: int) -> Set[int]:
        return self._inline_messages.pop(user_id, set())

    def discard_inline_message(self, user_id: int, message_id: int) -> None:
        messages = self._inline_messages.get(user_id)
        if not messages:
            return
        messages.discard(message_id)
        if not messages:
            self._inline_messages.pop(user_id, None)
