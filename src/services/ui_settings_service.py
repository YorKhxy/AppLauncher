import json
import os
import shutil
import sys
from typing import Any, Dict, Optional

ALLOWED_SKINS = ("neon", "ember", "aurora", "shadow", "daylight")
DEFAULT_SKIN = "neon"
DEFAULT_REORDER_LONG_PRESS_SEC = 3.0
MAX_REORDER_LONG_PRESS_SEC = 8.0


class UiSettingsService:
    """Web 壳外观与交互设置，存于 config/ui.json。"""

    def __init__(self) -> None:
        self._path = self._get_path()
        self._ensure_dir()
        self._seed_ui_from_bundle_if_missing()
        self._cache: Optional[Dict[str, Any]] = None

    def _bundled_defaults_ui_path(self) -> Optional[str]:
        if getattr(sys, "frozen", False):
            base = getattr(sys, "_MEIPASS", None)
            if not base:
                return None
            return os.path.join(base, "config", "defaults", "ui.json")
        here = os.path.dirname(os.path.abspath(__file__))
        src_root = os.path.dirname(here)
        return os.path.join(src_root, "config", "defaults", "ui.json")

    def _seed_ui_from_bundle_if_missing(self) -> None:
        if os.path.isfile(self._path):
            return
        bp = self._bundled_defaults_ui_path()
        if bp and os.path.isfile(bp):
            try:
                shutil.copy2(bp, self._path)
            except OSError:
                pass

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

    @staticmethod
    def _normalize_reorder_sec(value: Any) -> float:
        try:
            x = float(value)
        except (TypeError, ValueError):
            return DEFAULT_REORDER_LONG_PRESS_SEC
        if x <= 0:
            return DEFAULT_REORDER_LONG_PRESS_SEC
        return min(MAX_REORDER_LONG_PRESS_SEC, x)

    def _read_disk(self) -> Dict[str, Any]:
        if not os.path.exists(self._path):
            return {
                "skin": DEFAULT_SKIN,
                "reorder_long_press_sec": DEFAULT_REORDER_LONG_PRESS_SEC,
            }
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            skin = str(data.get("skin", DEFAULT_SKIN)).strip()
            if skin not in ALLOWED_SKINS:
                skin = DEFAULT_SKIN
            r = self._normalize_reorder_sec(
                data.get("reorder_long_press_sec", DEFAULT_REORDER_LONG_PRESS_SEC)
            )
            return {"skin": skin, "reorder_long_press_sec": r}
        except Exception:
            return {
                "skin": DEFAULT_SKIN,
                "reorder_long_press_sec": DEFAULT_REORDER_LONG_PRESS_SEC,
            }

    def load(self) -> Dict[str, Any]:
        if self._cache is not None:
            return dict(self._cache)
        self._cache = self._read_disk()
        return dict(self._cache)

    def save(self, data: Dict[str, Any]) -> bool:
        cur = self._read_disk()
        skin = str(data.get("skin", cur["skin"])).strip()
        if skin not in ALLOWED_SKINS:
            skin = DEFAULT_SKIN
        r = self._normalize_reorder_sec(
            data.get("reorder_long_press_sec", cur["reorder_long_press_sec"])
        )
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "version": "1.0",
                        "skin": skin,
                        "reorder_long_press_sec": r,
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
            self._cache = {"skin": skin, "reorder_long_press_sec": r}
            return True
        except Exception as e:
            print(f"保存 ui.json 失败: {e}")
            return False
