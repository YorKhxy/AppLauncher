import uuid
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class AppItem:
    id: str
    name: str
    path: str
    working_dir: Optional[str] = ""
    icon: Optional[str] = ""
    description: Optional[str] = ""

    @classmethod
    def create(cls, name: str, path: str, working_dir: str = "", icon: str = "", description: str = "") -> 'AppItem':
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            path=path,
            working_dir=working_dir,
            icon=icon,
            description=description
        )

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'AppItem':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', ''),
            path=data.get('path', ''),
            working_dir=data.get('working_dir', ''),
            icon=data.get('icon', ''),
            description=data.get('description', '')
        )