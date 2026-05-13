import json
import os
import sys
from typing import List, Optional
from models.app_item import AppItem


class ConfigService:
    def __init__(self):
        self.config_path = self._get_config_path()
        self._ensure_config_dir()

    def _get_config_path(self) -> str:
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        return os.path.join(app_dir, 'config', 'apps.json')

    def _ensure_config_dir(self):
        config_dir = os.path.dirname(self.config_path)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

    def load_config(self) -> List[AppItem]:
        if not os.path.exists(self.config_path):
            return self._create_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                apps_data = data.get('apps', [])
                return [AppItem.from_dict(item) for item in apps_data]
        except Exception:
            return self._create_default_config()

    def _create_default_config(self) -> List[AppItem]:
        default_apps = []
        self.save_config(default_apps)
        return default_apps

    def save_config(self, apps: List[AppItem]) -> bool:
        try:
            config_data = {
                "version": "1.0",
                "apps": [app.to_dict() for app in apps]
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

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
        return self.save_config(apps)

    def get_app_by_id(self, app_id: str) -> Optional[AppItem]:
        apps = self.load_config()
        for app in apps:
            if app.id == app_id:
                return app
        return None