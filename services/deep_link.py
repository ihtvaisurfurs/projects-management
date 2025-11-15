from dataclasses import dataclass
from typing import Optional


@dataclass
class DeepLinkData:
    type: str
    entity_id: int


def parse_start_param(param: Optional[str]) -> Optional[DeepLinkData]:
    if not param:
        return None
    if param.startswith("project_"):
        try:
            project_id = int(param.split("_", maxsplit=1)[1])
            return DeepLinkData(type="project", entity_id=project_id)
        except (ValueError, IndexError):
            return None
    return None