"""在 src/ 下执行 `python build.py` 时，转发到项目根目录的 build.py（cwd 为根目录）。"""
import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


if __name__ == "__main__":
    script = os.path.join(_ROOT, "build.py")
    raise SystemExit(subprocess.call([sys.executable, script], cwd=_ROOT))
