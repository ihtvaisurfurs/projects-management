import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def _optional_env(key: str) -> Optional[str]:
    value = os.getenv(key, "").strip()
    return value or None


def _float_env(key: str, default: float) -> float:
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"مقدار {key} باید عددی معتبر باشد.") from exc
    return value


def _bool_env(key: str, default: bool = False) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


@dataclass
class Settings:
    bot_token: str
    bot_username: str
    db_path: str
    log_level: str
    log_to_console: bool
    telegram_api_base: Optional[str]
    telegram_file_api_base: Optional[str]
    telegram_proxy: Optional[str]
    telegram_request_timeout: float
    telegram_retry_delay: float
    updates_group_id: Optional[int]
    enable_group_id_command: bool

    @classmethod
    def load(cls) -> "Settings":
        token = os.getenv("BOT_TOKEN", "").strip()
        raw_username = os.getenv("BOT_USERNAME", "").strip()
        username = raw_username.lstrip("@")
        if not token:
            raise ValueError("BOT_TOKEN در فایل .env تعریف نشده است")
        if not username:
            raise ValueError("BOT_USERNAME در فایل .env تعریف نشده است")
        group_raw = os.getenv("UPDATES_GROUP_ID", "").strip()
        group_id = int(group_raw) if group_raw else None
        return cls(
            bot_token=token,
            bot_username=username,
            db_path=os.getenv("DB_PATH", "data/app.db"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_to_console=_bool_env("LOG_TO_CONSOLE", False),
            telegram_api_base=_optional_env("TELEGRAM_API_BASE"),
            telegram_file_api_base=_optional_env("TELEGRAM_FILE_API_BASE"),
            telegram_proxy=_optional_env("TELEGRAM_PROXY"),
            telegram_request_timeout=_float_env("TELEGRAM_REQUEST_TIMEOUT", 60.0),
            telegram_retry_delay=_float_env("TELEGRAM_RETRY_DELAY", 5.0),
            updates_group_id=group_id,
            enable_group_id_command=_bool_env("ENABLE_GROUP_ID_COMMAND", True),
        )
