import sys
from pathlib import Path


def _web_dir() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass) / "web"
        return Path(sys.executable).resolve().parent / "web"
    return Path(__file__).resolve().parent.parent / "web"


def run_web_ui() -> None:
    import webview

    from ui.web_api import LauncherApi

    html_path = _web_dir() / "app.html"
    if not html_path.is_file():
        raise FileNotFoundError(f"未找到 Web 壳页面: {html_path}")

    api = LauncherApi()

    window = webview.create_window(
        "VrLauncher",
        url=html_path.as_uri(),
        js_api=api,
        width=1100,
        height=800,
    )
    webview.start(debug=False)
