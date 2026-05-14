import uuid
from dataclasses import dataclass, asdict
from typing import Optional


_URL_BROWSERS = frozenset({"default", "edge", "chrome", "qq"})


@dataclass
class AppItem:
    id: str
    name: str
    path: str
    working_dir: Optional[str] = ""
    icon: Optional[str] = ""
    description: Optional[str] = ""
    kind: str = "app"
    url_browser: str = ""

    @classmethod
    def create(
        cls,
        name: str,
        path: str,
        working_dir: str = "",
        icon: str = "",
        description: str = "",
        kind: str = "app",
        url_browser: str = "",
    ) -> 'AppItem':
        k = kind if kind in ("app", "url") else "app"
        ub = (url_browser or "").strip().lower()
        if k == "url":
            if ub not in _URL_BROWSERS:
                ub = "default"
        else:
            ub = ""
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            path=path,
            working_dir=working_dir,
            icon=icon,
            description=description,
            kind=k,
            url_browser=ub,
        )

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'AppItem':
        k = data.get("kind") or "app"
        if k not in ("app", "url"):
            k = "app"
        ub = str(data.get("url_browser") or "").strip().lower()
        if k == "url":
            if ub not in _URL_BROWSERS:
                ub = "default"
        else:
            ub = ""
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', ''),
            path=data.get('path', ''),
            working_dir=data.get('working_dir', ''),
            icon=data.get('icon', ''),
            description=data.get('description', ''),
            kind=k,
            url_browser=ub,
        )