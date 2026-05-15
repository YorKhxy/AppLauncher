import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _apply_windows_dpi_awareness() -> None:
    """与从 python.exe 启动时对齐：PyInstaller 生成的 exe 常缺少 Per-Monitor DPI 清单，
    WebView2 在高分屏下会得到偏小的客户区，flex + overflow:hidden 会把卡片顶边裁掉。"""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        shcore = ctypes.windll.shcore
        # PROCESS_PER_MONITOR_DPI_AWARE_V2 = 3（Win10 1703+）
        try:
            shcore.SetProcessDpiAwareness(3)
        except OSError:
            shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            import ctypes

            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


_apply_windows_dpi_awareness()


def main():
    from ui.web_main import run_web_ui

    run_web_ui()


if __name__ == "__main__":
    main()
