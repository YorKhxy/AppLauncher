import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog
from typing import Any, Callable, Dict, List, Optional, Set

from models.app_item import AppItem
from services.config_service import ConfigService
from services.launcher_service import LauncherService
from services.ui_settings_service import UiSettingsService

# 拖到「+ 添加应用」卡上：插入到全局列表末尾（紧贴添加入口之前）
REORDER_BEFORE_ADD = "__add_new__"


_IMG_ICON_EXT = frozenset({".png", ".jpg", ".jpeg", ".webp", ".ico", ".gif"})


def _resolve_icon_display_url(app: AppItem) -> str:
    raw = (app.icon or "").strip()
    if not raw or not os.path.isfile(raw):
        return ""
    ext = os.path.splitext(raw)[1].lower()
    if ext not in _IMG_ICON_EXT:
        return ""
    try:
        return Path(os.path.normpath(raw)).resolve().as_uri()
    except OSError:
        return ""


def _app_dict_for_ui(app: AppItem) -> Dict[str, Any]:
    d = app.to_dict()
    d["icon_display_url"] = _resolve_icon_display_url(app)
    return d


def _norm_search(q: str) -> str:
    t = (q or "").strip().lower()
    if t == "筛选应用...":
        return ""
    return t


class LauncherApi:
    """供 pywebview js_api 调用。"""

    def __init__(self) -> None:
        self.config_service = ConfigService()
        self.launcher_service = LauncherService()
        self.ui_settings = UiSettingsService()
        self.apps: List[AppItem] = []
        self.displayed_apps: List[AppItem] = []
        self.selected_app_id: Optional[str] = None
        self.running_ids: Set[str] = set()
        self.launching_ids: Set[str] = set()
        self._search_raw: str = ""
        self.status_text = "状态：就绪"
        self.status_kind = "ok"

        self._tk_lock = threading.Lock()
        self._tk_thread: Optional[threading.Thread] = None
        self._tk_ready = threading.Event()
        self._tk_root: Optional[tk.Tk] = None

        self._pending_action: Optional[Dict[str, Any]] = None

    def _ensure_tk(self) -> None:
        with self._tk_lock:
            if self._tk_thread is not None:
                return

            def _tk_main() -> None:
                root = tk.Tk()
                root.withdraw()
                self._tk_root = root
                self._tk_ready.set()
                root.mainloop()

            self._tk_thread = threading.Thread(target=_tk_main, daemon=True)
            self._tk_thread.start()

        self._tk_ready.wait(timeout=30)
        if self._tk_root is None:
            raise RuntimeError("Tk 子系统未在超时内就绪")

    def _invoke_tk(self, fn: Callable[[], Any], timeout: float = 300.0) -> Any:
        self._ensure_tk()
        root = self._tk_root
        assert root is not None
        out: List[Any] = []
        err: List[BaseException] = []
        done = threading.Event()

        def job() -> None:
            try:
                out.append(fn())
            except BaseException as e:
                err.append(e)
            finally:
                done.set()

        root.after(0, job)
        if not done.wait(timeout=timeout):
            raise TimeoutError("Tk 对话框超时")
        if err:
            raise err[0]
        return out[0] if out else None

    def _set_status(self, text: str, kind: str) -> None:
        self.status_text = text
        self.status_kind = kind

    def _apply_filter(self) -> None:
        q = _norm_search(self._search_raw)
        if not q:
            self.displayed_apps = list(self.apps)
        else:
            self.displayed_apps = [
                app
                for app in self.apps
                if q in app.name.lower() or q in (app.path or "").lower()
            ]
        if self.selected_app_id and not any(
            a.id == self.selected_app_id for a in self.displayed_apps
        ):
            self.selected_app_id = None

    def _slots(self) -> List[Optional[AppItem]]:
        return list(self.displayed_apps)

    def get_state(self) -> Dict[str, Any]:
        slots = [{"index": i, "app": _app_dict_for_ui(app)} for i, app in enumerate(self._slots())]
        ui = self.ui_settings.load()
        return {
            "slots": slots,
            "selected_id": self.selected_app_id,
            "running_ids": list(self.running_ids),
            "launching_ids": list(self.launching_ids),
            "status_text": self.status_text,
            "status_kind": self.status_kind,
            "search": self._search_raw,
            "skin": ui["skin"],
            "reorder_long_press_sec": ui["reorder_long_press_sec"],
            "total_count": len(self.displayed_apps),
        }

    def save_ui_settings(self, data: Any) -> Dict[str, Any]:
        if not isinstance(data, dict):
            data = {}
        ok = self.ui_settings.save(data)
        if not ok:
            return {**self.get_state(), "ui_error": "外观设置保存失败"}
        return self.get_state()

    def load(self) -> Dict[str, Any]:
        self.apps = self.config_service.load_config()
        self._apply_filter()
        return self.get_state()

    def search(self, query: str) -> Dict[str, Any]:
        self._search_raw = query if query is not None else ""
        self._apply_filter()
        return self.get_state()

    def select(self, app_id: Optional[str]) -> Dict[str, Any]:
        self.selected_app_id = app_id
        return self.get_state()

    def refresh(self) -> Dict[str, Any]:
        return self.load()

    def _finish_launch(self, app_id: str) -> None:
        self.launching_ids.discard(app_id)
        self.running_ids.add(app_id)
        self._set_status("状态：就绪", "ok")

    def _finish_close(self, app_id: str) -> None:
        self.running_ids.discard(app_id)
        self._set_status("状态：就绪", "ok")

    def _confirm_action(self, action: str) -> Dict[str, Any]:
        print(f"[DEBUG] _confirm_action called with action={action}, pending={self._pending_action}")
        if not self._pending_action:
            print("[DEBUG] No pending action!")
            return self.get_state()

        action_type = self._pending_action.get("type")
        if action != "confirm" or action_type != self._pending_action.get("type"):
            print(f"[DEBUG] Action mismatch: {action} != confirm or type mismatch")
            self._pending_action = None
            return self.get_state()

        data = self._pending_action
        self._pending_action = None
        print(f"[DEBUG] Executing action type={data.get('type')}, app_id={data.get('app_id')}")

        if data["type"] == "launch":
            return self._do_launch(data["app_id"])
        elif data["type"] == "close":
            return self._do_close(data["app_id"])
        elif data["type"] == "delete":
            return self._do_delete()
        elif data["type"] == "move_up":
            return self._do_move_up(data.get("app_id"))
        elif data["type"] == "move_down":
            return self._do_move_down(data.get("app_id"))

        return self.get_state()

    def _do_launch(self, app_id: str) -> Dict[str, Any]:
        app = self.config_service.get_app_by_id(app_id)
        if not app:
            return self.get_state()
        if app.kind == "url":
            self._set_status("状态：正在打开浏览器…", "busy")
            ok = self.launcher_service.launch_app(app)
            if ok:
                threading.Timer(0.9, lambda: self._set_status("状态：就绪", "ok")).start()
            else:
                self._set_status("状态：打开链接失败（请检查网址或所选浏览器是否已安装）", "err")
                threading.Timer(1.5, lambda: self._set_status("状态：就绪", "ok")).start()
            return self.get_state()

        self._set_status("状态：正在启动…", "busy")
        ok = self.launcher_service.launch_app(app)
        if ok:
            self.launching_ids.add(app.id)
            threading.Timer(1.5, lambda: self._finish_launch(app.id)).start()
        else:
            self._set_status("状态：启动失败", "err")
            threading.Timer(1.5, lambda: self._set_status("状态：就绪", "ok")).start()
        return self.get_state()

    def _do_close(self, app_id: str) -> Dict[str, Any]:
        app = self.config_service.get_app_by_id(app_id)
        if not app:
            return self.get_state()
        self._set_status("状态：正在关闭…", "warn")
        ok = self.launcher_service.close_app(app.id)
        if ok:
            self.running_ids.discard(app.id)
            threading.Timer(1.5, lambda: self._set_status("状态：就绪", "ok")).start()
        else:
            self._set_status("状态：关闭失败", "err")
            self.running_ids.discard(app.id)
            threading.Timer(1.5, lambda: self._set_status("状态：就绪", "ok")).start()
        return self.get_state()

    def _do_delete(self) -> Dict[str, Any]:
        if not self.selected_app_id:
            return self.get_state()
        app = self.config_service.get_app_by_id(self.selected_app_id)
        if not app:
            return self.get_state()
        self.config_service.delete_app(app.id)
        self.selected_app_id = None
        return self.load()

    def _do_move_up(self, app_id: Optional[str] = None) -> Dict[str, Any]:
        target_id = app_id or self.selected_app_id
        if not target_id:
            return self.get_state()
        apps = self.config_service.load_config()
        for i, app in enumerate(apps):
            if app.id == target_id:
                if i == 0:
                    return self.get_state()
                apps[i], apps[i - 1] = apps[i - 1], apps[i]
                self.config_service.save_config(apps)
                self.load()
                self.selected_app_id = target_id
                self._apply_filter()
                return self.get_state()
        return self.get_state()

    def _do_move_down(self, app_id: Optional[str] = None) -> Dict[str, Any]:
        target_id = app_id or self.selected_app_id
        if not target_id:
            return self.get_state()
        apps = self.config_service.load_config()
        for i, app in enumerate(apps):
            if app.id == target_id:
                if i == len(apps) - 1:
                    return self.get_state()
                apps[i], apps[i + 1] = apps[i + 1], apps[i]
                self.config_service.save_config(apps)
                self.load()
                self.selected_app_id = target_id
                self._apply_filter()
                return self.get_state()
        return self.get_state()

    def launch(self, app_id: str) -> Dict[str, Any]:
        return self._do_launch(app_id)

    def close(self, app_id: str) -> Dict[str, Any]:
        return self._do_close(app_id)

    def pick_executable(self) -> Optional[str]:
        def run() -> str:
            assert self._tk_root is not None
            p = filedialog.askopenfilename(
                parent=self._tk_root,
                title="选择应用程序",
                filetypes=[
                    ("可执行与脚本", "*.exe *.bat *.cmd"),
                    ("可执行文件", "*.exe"),
                    ("批处理", "*.bat;*.cmd"),
                    ("所有文件", "*.*"),
                ],
            )
            return p or ""

        path = self._invoke_tk(run)
        if not path:
            return None
        return path

    def open_app_folder(self, app_id: str) -> Dict[str, Any]:
        """在资源管理器中打开本地应用路径所在文件夹（不选中文件）。链接类无操作。"""
        aid = str(app_id or "").strip()
        if not aid:
            return self.get_state()
        app = self.config_service.get_app_by_id(aid)
        if not app:
            return self.get_state()
        if app.kind == "url":
            self._set_status("状态：网页链接无本地文件夹", "warn")
            threading.Timer(1.4, lambda: self._set_status("状态：就绪", "ok")).start()
            return self.get_state()
        raw = (app.path or "").strip()
        if not raw:
            self._set_status("状态：路径为空", "err")
            threading.Timer(1.4, lambda: self._set_status("状态：就绪", "ok")).start()
            return self.get_state()
        norm = os.path.normpath(os.path.expandvars(raw))
        if os.path.isfile(norm):
            folder = os.path.dirname(norm)
        elif os.path.isdir(norm):
            folder = norm
        else:
            folder = os.path.dirname(norm)
        if not folder or not os.path.isdir(folder):
            self._set_status("状态：目标文件夹不存在", "err")
            threading.Timer(1.6, lambda: self._set_status("状态：就绪", "ok")).start()
            return self.get_state()
        try:
            os.startfile(folder)
        except OSError as e:
            print(f"打开文件夹失败: {e}")
            self._set_status("状态：打开文件夹失败", "err")
            threading.Timer(1.6, lambda: self._set_status("状态：就绪", "ok")).start()
            return self.get_state()
        self._set_status("状态：已打开所在文件夹", "ok")
        threading.Timer(1.2, lambda: self._set_status("状态：就绪", "ok")).start()
        return self.get_state()

    def save_app_form(self, data: Any) -> Dict[str, Any]:
        def err(msg: str) -> Dict[str, Any]:
            return {**self.get_state(), "form_error": msg}

        if not isinstance(data, dict):
            data = {}

        name = str(data.get("name") or "").strip()
        path = str(data.get("path") or "").strip()
        working_dir = str(data.get("working_dir") or "").strip()
        icon = str(data.get("icon") or "").strip()
        description = str(data.get("description") or "").strip()
        kind = str(data.get("kind") or "app").strip().lower()
        if kind not in ("app", "url"):
            kind = "app"
        url_browser = str(data.get("url_browser") or "default").strip().lower()
        if url_browser not in ("default", "edge", "chrome", "qq"):
            url_browser = "default"
        if kind == "url":
            if url_browser != "default" and not LauncherService.resolve_browser_exe(url_browser):
                labels = {"edge": "Microsoft Edge", "chrome": "Google Chrome", "qq": "QQ 浏览器"}
                return err(f"未在系统中找到 {labels[url_browser]}，请安装该浏览器或改用「系统默认」。")
        else:
            url_browser = ""
        app_id = data.get("id")
        if app_id is not None:
            app_id = str(app_id).strip() or None
        else:
            app_id = None

        if not name:
            return err("请输入名称")

        if kind == "url":
            path = LauncherService.normalize_url(path)
            if not path:
                return err("请输入网页链接")
            if not LauncherService.validate_url(path):
                return err("请输入有效的 http(s) 网址（可省略 https://，将自动补全）")
            working_dir = ""
        else:
            if not path:
                return err("请选择应用路径")
            if not LauncherService.validate_path(path):
                return err("指定的应用路径不存在")

        if app_id:
            old = self.config_service.get_app_by_id(app_id)
            if not old:
                return err("应用不存在")
            wd = "" if kind == "url" else (working_dir if working_dir else (old.working_dir or ""))
            item = AppItem(
                id=old.id,
                name=name,
                path=path,
                working_dir=wd,
                icon=icon if icon else (old.icon or ""),
                description=description,
                kind=kind,
                url_browser=url_browser,
            )
            if not self.config_service.update_app(old.id, item):
                return err("保存失败")
        else:
            item = AppItem.create(
                name=name,
                path=path,
                working_dir="" if kind == "url" else working_dir,
                icon=icon,
                description=description,
                kind=kind,
                url_browser=url_browser if kind == "url" else "",
            )
            if not self.config_service.add_app(item):
                return err("保存失败")

        return self.load()

    def delete_app(self) -> Dict[str, Any]:
        return self._do_delete()

    def move_up(self) -> Dict[str, Any]:
        return self._do_move_up()

    def move_down(self) -> Dict[str, Any]:
        return self._do_move_down()

    def reorder_app(self, payload: Any) -> Dict[str, Any]:
        """全局顺序：拖到另一应用上则与该项互换位置；拖到 + 添加应用则移到列表末尾。"""
        if not isinstance(payload, dict):
            payload = {}
        from_id = str(payload.get("from_id") or "").strip()
        before_id = str(payload.get("before_id") or "").strip()
        if not from_id:
            return self.get_state()

        apps = self.config_service.load_config()
        from_idx = next((i for i, a in enumerate(apps) if a.id == from_id), None)
        if from_idx is None:
            return self.get_state()

        if before_id == REORDER_BEFORE_ADD:
            insert_idx = len(apps)
            item = apps.pop(from_idx)
            if insert_idx > from_idx:
                insert_idx -= 1
            apps.insert(insert_idx, item)
        else:
            if not before_id or before_id == from_id:
                return self.load()
            to_idx = next((i for i, a in enumerate(apps) if a.id == before_id), None)
            if to_idx is None:
                return self.get_state()
            if to_idx == from_idx:
                return self.load()
            apps[from_idx], apps[to_idx] = apps[to_idx], apps[from_idx]

        self.config_service.save_config(apps)
        self.load()
        self.selected_app_id = from_id
        self._apply_filter()
        return self.get_state()
