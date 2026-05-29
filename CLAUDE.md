# CLAUDE.md

This file guides Claude Code when working in this repository.

## 项目概述

**ClickDone** 是一个 Windows 本地启动工具（仓库目录名为 `VrLauncher`）。用卡片化面板统一管理本地应用（`.exe` / `.bat` / `.cmd`）和网页入口，支持启动、关闭进程、搜索、拖拽排序、自定义分组、皮肤切换。单机、本地 JSON 配置、单用户，无登录/云同步。

需求细节见 [Product-Spec.md](Product-Spec.md)。注意：`AGENTS.md`、`.codex/`、`.trae/` 属于 Codex CLI 的另一套工作流，**已被 `.gitignore` 忽略**，不是本仓库代码的一部分。

## 技术栈

- **Python 3.12+**（运行时用到 `sys.frozen`/`_MEIPASS`，需 Windows）
- **pywebview** — 桌面窗口承载 HTML 前端（WebView2）
- **psutil** — 进程树清理
- **Pillow** — 打包时生成多尺寸 `.ico`
- **PyInstaller** — 打包为单文件 exe
- 前端：单文件 `src/web/app.html`（原生 HTML/CSS/JS，无框架，约 3600 行）

## 运行与构建

```bat
run.bat        :: 源码启动 -> python src\main.py
build.bat      :: 打包 -> python build.py（PyInstaller --onefile --noconsole）
```

- 依赖安装：`pip install -r requirements.txt`
- `build.py` 产物输出到 `release/<YYYYMMDD>/ClickDone_<时间戳>.exe`，并把 `src/config/defaults/` 的默认配置拷到产物旁。
- 仓库根的 `ClickDone.spec` 含旧的硬编码绝对路径（`D:\AppLauncher\...`），已 gitignore，**不要**用它打包；以 `build.py` 为准。
- 无自动化测试套件。验证靠手动运行 `run.bat`。

## 架构

数据从前端 JS 经 pywebview 桥接调用后端 Python，单向通过 `LauncherApi` 的方法进出。

```
src/main.py              入口；设置 Windows Per-Monitor DPI 感知后调 run_web_ui
└─ ui/web_main.py        创建 pywebview 窗口，挂载 LauncherApi 为 js_api，加载 app.html
   └─ ui/web_api.py      LauncherApi：前端唯一可调的后端 API（js_api 桥）
      ├─ services/config_service.py      apps.json 读写、迁移、自定义组
      ├─ services/launcher_service.py    启动/关闭进程、URL 与浏览器解析
      ├─ services/ui_settings_service.py ui.json（皮肤、长按拖拽时长）
      └─ models/app_item.py              AppItem 数据类
src/web/app.html         前端单文件；通过 window.pywebview.api.<method>() 调后端
```

### 关键约定

- **前后端契约**：前端 `app.html` 里的 `api(method, ...args)` 调用，必须对应 `LauncherApi` 上的同名 public 方法。改 API 时两边同步。
- **状态模型**：几乎所有 `LauncherApi` 方法都返回 `get_state()` 的完整快照（`slots`、`custom_groups`、`running_ids`、`skin` 等），前端 `render(s)` 整体重渲染。不要做增量返回。
- **配置文件**（运行时在 exe 旁或源码树根的 `config/` 下）：
  - `config/apps.json` — `{version, apps[], custom_groups[]}`，卡片顺序即数组顺序
  - `config/ui.json` — `{version, skin, reorder_long_press_sec}`
  - `src/config/defaults/` — 打包随附的默认值，首次运行无配置时 seed
  - `ConfigService` 有字段迁移逻辑（`_migrate_apps_document`），旧配置缺字段会自动补齐并回写。
- **AppItem**：`kind` 为 `app` 或 `url`；`url` 类的 `url_browser` ∈ `{default, edge, chrome, qq}`，`app` 类该字段强制为空。校验/归一化集中在 `AppItem.create`/`from_dict`。
- **进程管理**（`launcher_service.py`）：`.bat`/`.cmd` 会被改写成临时 `_clickdone_*.bat`（移除 taskkill、给裸 exe 行加 `start`），关闭时按 exe 名用 psutil 杀进程树；`.exe` 直接 Popen。网页用 `webbrowser` 或解析到的浏览器 exe 打开。
- **文件对话框**：`pick_executable` 用 tkinter `filedialog`，跑在独立守护线程（`_ensure_tk`/`_invoke_tk`），避免与 pywebview 主循环冲突。
- **皮肤**：5 种，`ALLOWED_SKINS = (neon, ember, aurora, shadow, daylight)`，CSS 里按 `data-skin` 切换。

## 注意事项

- 全部交互文案、注释、状态提示用**中文**。
- 仅 Windows 平台（DPI 感知、`os.startfile`、浏览器路径、`STARTUPINFO`、`CREATE_NEW_CONSOLE` 等均依赖 Win API）。
- `web_api.py` 中 `_confirm_action` / `_do_*` 留有 `print("[DEBUG] ...")` 调试输出，且 `custom_groups_reorder` 被重复定义了两次（后者覆盖前者，逻辑相同）—— 改动该文件时留意。
- 提交信息沿用中文短句风格（见 git log）。
