import json
import logging
from datetime import datetime

from core.utils import log_directory


class LogService:
    def __init__(self, logs_root: str, level: str, log_to_console: bool = False) -> None:
        self._logs_root = logs_root
        self._log_to_console = log_to_console
        self._logger = logging.getLogger("project_manager_bot")
        self._logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        self._json_file = None
        self._errors_file = None
        self._configure_handler()

    def _configure_handler(self) -> None:
        log_dir = log_directory(self._logs_root)
        self._json_file = log_dir / "bot.json"
        self._errors_file = log_dir / "errors.json"
        if self._log_to_console:
            if not any(isinstance(h, logging.StreamHandler) for h in self._logger.handlers):
                console = logging.StreamHandler()
                console.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
                self._logger.addHandler(console)

    async def info(self, message: str) -> None:
        await self._write("INFO", message)

    async def error(self, message: str) -> None:
        await self._write("ERROR", message)

    async def _write(self, level: str, message: str) -> None:
        level_name = level.upper()
        self._logger.log(getattr(logging, level_name, logging.INFO), message)
        timestamp = datetime.utcnow().isoformat()
        entry = {"timestamp": timestamp, "level": level_name, "message": message}
        await self._append(self._json_file, entry)
        if level_name == "ERROR":
            await self._append(self._errors_file, entry)

    async def _append(self, path, entry) -> None:
        if not path:
            return
        try:
            if path.exists():
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    if not isinstance(data, list):
                        data = []
                except json.JSONDecodeError:
                    data = []
            else:
                data = []
            data.append(entry)
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            self._logger.error("نوشتن لاگ در فایل JSON با خطا مواجه شد.")
