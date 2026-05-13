import json
import os
import sys
from typing import Any, Dict, Optional

ALLOWED_SKINS = ("neon", "ember", "aurora")
DEFAULT_SKIN = "neon"


class UiSettingsService:
    """Web 壳外观设置（皮肤等），存于 config/ui.json。"""

    def __init__(self) -> None:
        self._path = self._get_path()
        self._ensure_dir()
        self._skin_cache: Optional[str] = None

    def _get_path(self) -> str:
        if getattr(sys, "frozen", False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(app_dir, "config", "ui.json")

    def _ensure_dir(self) -> None:
        d = os.path.dirname(self._path)
        if not os.path.exists(d):
            os.makedirs(d)

    def load(self) -> Dict[str, Any]:
        if self._skin_cache is not None:
            return {"skin": self._skin_cache}
        if not os.path.exists(self._path):
            self._skin_cache = DEFAULT_SKIN
            return {"skin": self._skin_cache}
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            skin = str(data.get("skin", DEFAULT_SKIN)).strip()
            if skin not in ALLOWED_SKINS:
                skin = DEFAULT_SKIN
            self._skin_cache = skin
            return {"skin": skin}
        except Exception:
            self._skin_cache = DEFAULT_SKIN
            return {"skin": self._skin_cache}

    def save(self, data: Dict[str, Any]) -> bool:
        skin = str(data.get("skin", DEFAULT_SKIN)).strip()
        if skin not in ALLOWED_SKINS:
            skin = DEFAULT_SKIN
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump({"version": "1.0", "skin": skin}, f, indent=2, ensure_ascii=False)
            self._skin_cache = skin
            return True
        except Exception as e:
            print(f"保存 ui.json 失败: {e}")
            return False
