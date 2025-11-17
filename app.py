import asyncio
import logging
from typing import Optional

from aiohttp.client_exceptions import ClientConnectorError
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.exceptions import TelegramNetworkError
from aiogram.fsm.storage.memory import MemoryStorage

from bot.handlers import admin, common, projects, start, global_back
from core.config import Settings
from core.constants import AppPaths
from db.session import Database
from services.logging_service import LogService
from services.menu_service import MenuService
from services.project_service import ProjectService
from services.session_manager import SessionManager
from services.user_service import UserService


def _build_session(settings: Settings) -> Optional[AiohttpSession]:
    timeout: Optional[float] = None
    if settings.telegram_request_timeout and settings.telegram_request_timeout > 0:
        timeout = settings.telegram_request_timeout
    if not settings.telegram_proxy and timeout is None:
        return None
    return AiohttpSession(
        proxy=settings.telegram_proxy,
        timeout=timeout,
    )


def _build_server(settings: Settings) -> Optional[TelegramAPIServer]:
    base = settings.telegram_api_base
    file_base = settings.telegram_file_api_base
    if not base and not file_base:
        return None
    if base and not file_base:
        return TelegramAPIServer.from_base(base)
    if base and file_base:
        base_url = base.rstrip("/")
        file_url = file_base.rstrip("/")
        return TelegramAPIServer(
            base=f"{base_url}/bot{{token}}/{{method}}",
            file=f"{file_url}/file/bot{{token}}/{{path}}",
        )
    # اگر فقط فایل ست شده باشد نادیده گرفته می‌شود
    return None


async def main() -> None:
    settings = Settings.load()
    paths = AppPaths()
    database = Database(settings.db_path)
    await database.run_migrations(paths.migrations_dir)

    session_manager = SessionManager(storage_path="data/session_cache.json")
    user_service = UserService(database)
    project_service = ProjectService(database)
    menu_service = MenuService()
    log_service = LogService(
        paths.logs_root,
        settings.log_level,
        log_to_console=settings.log_to_console,
    )

    bot_kwargs = {
        "token": settings.bot_token,
        "default": DefaultBotProperties(parse_mode="HTML"),
    }
    session = _build_session(settings)
    if session:
        bot_kwargs["session"] = session
    server = _build_server(settings)
    if server:
        bot_kwargs["server"] = server
    bot = Bot(**bot_kwargs)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_routers(
        global_back.router,
        start.router,
        admin.router,
        projects.router,
        common.router,
    )

    dp.workflow_data.update(
        {
            "session_manager": session_manager,
            "user_service": user_service,
            "project_service": project_service,
            "menu_service": menu_service,
            "log_service": log_service,
            "bot_username": settings.bot_username,
            "updates_group_id": settings.updates_group_id,
        }
    )

    @dp.error()
    async def error_handler(event):
        exc = getattr(event, "exception", None)
        await log_service.error(f"خطا: {exc}")
        return True

    while True:
        try:
            await dp.start_polling(bot)
            break
        except (TelegramNetworkError, ClientConnectorError) as exc:
            await log_service.error(
                f"خطای ارتباط با تلگرام: {exc}. تلاش مجدد پس از {settings.telegram_retry_delay} ثانیه."
            )
            await asyncio.sleep(settings.telegram_retry_delay)
        except asyncio.CancelledError:
            await log_service.info("Polling متوقف شد (Cancel).")
            break


if __name__ == "__main__":
    asyncio.run(main())
