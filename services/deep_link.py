from dataclasses import dataclass
from typing import Optional


@dataclass
class DeepLinkData:
    type: str
    entity_id: int
    chat_id: int | None = None


def parse_start_param(param: Optional[str]) -> Optional[DeepLinkData]:
    if not param:
        return None
    if param.startswith("project_"):
        try:
            project_id = int(param.split("_", maxsplit=1)[1])
            return DeepLinkData(type="project", entity_id=project_id)
        except (ValueError, IndexError):
            return None
    if param.startswith("gproject_"):
        parts = param.split("_")
        if len(parts) >= 3:
            try:
                project_id = int(parts[1])
                chat_id = int(parts[2])
                return DeepLinkData(type="group_project", entity_id=project_id, chat_id=chat_id)
            except ValueError:
                return None
    return None
