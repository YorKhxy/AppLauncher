import json
import os
import shutil
import sys
import uuid
from typing import Any, Dict, List, Optional, Tuple

from models.app_item import AppItem


def _normalize_custom_group(raw: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(raw, dict):
        return None
    gid = str(raw.get("id") or "").strip() or str(uuid.uuid4())
    name = (str(raw.get("name") or "").strip() or "未命名组")
    collapsed = bool(raw.get("collapsed", False))
    raw_ids = raw.get("item_ids")
    if raw_ids is None:
        raw_ids = raw.get("items") or []
    item_ids: List[str] = []
    seen = set()
    for x in raw_ids or []:
        s = str(x).strip()
        if s and s not in seen:
            seen.add(s)
            item_ids.append(s)
    return {"id": gid, "name": name, "collapsed": collapsed, "item_ids": item_ids}


def _normalize_groups_list(raw: Any) -> List[Dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, Any]] = []
    for g in raw:
        ng = _normalize_custom_group(g)
        if ng:
            out.append(ng)
    return out


def _sanitize_group_item_ids(groups: List[Dict[str, Any]], valid_app_ids: set) -> None:
    for g in groups:
        g["item_ids"] = [i for i in g.get("item_ids", []) if i in valid_app_ids]


_APP_ITEM_SHELL: Dict[str, Any] = {
    "id": "",
    "name": "",
    "path": "",
    "working_dir": "",
    "icon": "",
    "description": "",
    "kind": "app",
    "url_browser": "",
}


class ConfigService:
    def __init__(self):
        self.config_path = self._get_config_path()
        self._ensure_config_dir()
        self._seed_apps_from_bundle_if_missing()

    def _get_config_path(self) -> str:
        if getattr(sys, "frozen", False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        return os.path.join(app_dir, "config", "apps.json")

    def _ensure_config_dir(self):
        config_dir = os.path.dirname(self.config_path)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

    def _bundled_defaults_apps_path(self) -> Optional[str]:
        """PyInstaller 解压目录或源码树内的默认 apps.json（与 build --add-data 对齐）。"""
        if getattr(sys, "frozen", False):
            base = getattr(sys, "_MEIPASS", None)
            if not base:
                return None
            return os.path.join(base, "config", "defaults", "apps.json")
        here = os.path.dirname(os.path.abspath(__file__))
        src_root = os.path.dirname(here)
        return os.path.join(src_root, "config", "defaults", "apps.json")

    def _seed_apps_from_bundle_if_missing(self) -> None:
        """exe 旁尚无 apps.json 时，从包内拷贝一份默认结构（避免同事只有 exe 没有 config）。"""
        if os.path.isfile(self.config_path):
            return
        bp = self._bundled_defaults_apps_path()
        if bp and os.path.isfile(bp):
            try:
                shutil.copy2(bp, self.config_path)
            except OSError:
                pass

    @staticmethod
    def _migrate_apps_document(doc: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """补全根级与每条 app 的字段，旧版缺字段时与当前 AppItem 对齐并触发一次回写。"""
        changed = False
        if "version" not in doc:
            doc["version"] = "1.0"
            changed = True

        raw_apps = doc.get("apps")
        if not isinstance(raw_apps, list):
            doc["apps"] = []
            changed = True
        else:
            merged: List[Dict[str, Any]] = []
            for item in raw_apps:
                if not isinstance(item, dict):
                    changed = True
                    continue
                if any(k not in item for k in _APP_ITEM_SHELL):
                    changed = True
                merged.append({**_APP_ITEM_SHELL, **item})
            doc["apps"] = merged

        raw_groups = doc.get("custom_groups")
        if not isinstance(raw_groups, list):
            doc["custom_groups"] = []
            changed = True

        return doc, changed

    def _persist_document(self, doc: Dict[str, Any]) -> None:
        apps: List[AppItem] = []
        for raw in doc.get("apps", []):
            if not isinstance(raw, dict):
                continue
            try:
                apps.append(AppItem.from_dict(raw))
            except Exception:
                continue
        groups = _normalize_groups_list(doc.get("custom_groups", []))
        self._write_document(apps, groups)

    def _read_document(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_path):
            return {"version": "1.0", "apps": [], "custom_groups": []}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return {"version": "1.0", "apps": [], "custom_groups": []}
            migrated, changed = self._migrate_apps_document(data)
            if changed:
                self._persist_document(migrated)
            return migrated
        except Exception:
            return {"version": "1.0", "apps": [], "custom_groups": []}

    def _write_document(self, apps: List[AppItem], groups: List[Dict[str, Any]]) -> bool:
        try:
            groups = _normalize_groups_list(groups)
            valid = {a.id for a in apps}
            _sanitize_group_item_ids(groups, valid)
            config_data = {
                "version": "1.0",
                "apps": [app.to_dict() for app in apps],
                "custom_groups": groups,
            }
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

    def load_config(self) -> List[AppItem]:
        if not os.path.exists(self.config_path):
            return self._create_default_config()
        doc = self._read_document()
        apps_data = doc.get("apps", [])
        if not isinstance(apps_data, list):
            apps_data = []
        try:
            return [AppItem.from_dict(item) for item in apps_data]
        except Exception:
            return self._create_default_config()

    def load_custom_groups(self) -> List[Dict[str, Any]]:
        doc = self._read_document()
        groups = _normalize_groups_list(doc.get("custom_groups", []))
        apps = self.load_config()
        valid = {a.id for a in apps}
        _sanitize_group_item_ids(groups, valid)
        return groups

    def save_config(self, apps: List[AppItem]) -> bool:
        doc = self._read_document()
        groups = _normalize_groups_list(doc.get("custom_groups", []))
        valid = {a.id for a in apps}
        _sanitize_group_item_ids(groups, valid)
        return self._write_document(apps, groups)

    def save_apps_and_custom_groups(
        self, apps: List[AppItem], groups: List[Dict[str, Any]]
    ) -> bool:
        groups = _normalize_groups_list(groups)
        valid = {a.id for a in apps}
        _sanitize_group_item_ids(groups, valid)
        return self._write_document(apps, groups)

    def _create_default_config(self) -> List[AppItem]:
        default_apps: List[AppItem] = []
        self._write_document(default_apps, [])
        return default_apps

    def add_app(self, app: AppItem) -> bool:
        apps = self.load_config()
        apps.append(app)
        return self.save_config(apps)

    def update_app(self, app_id: str, updated_app: AppItem) -> bool:
        apps = self.load_config()
        for i, app in enumerate(apps):
            if app.id == app_id:
                apps[i] = updated_app
                return self.save_config(apps)
        return False

    def delete_app(self, app_id: str) -> bool:
        apps = self.load_config()
        apps = [app for app in apps if app.id != app_id]
        doc = self._read_document()
        groups = _normalize_groups_list(doc.get("custom_groups", []))
        valid = {a.id for a in apps}
        _sanitize_group_item_ids(groups, valid)
        return self._write_document(apps, groups)

    def get_app_by_id(self, app_id: str) -> Optional[AppItem]:
        apps = self.load_config()
        for app in apps:
            if app.id == app_id:
                return app
        return None
