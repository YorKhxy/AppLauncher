import os
import shutil
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# 请在项目根目录执行: python build.py（或运行 build.bat）

ROOT = os.path.dirname(os.path.abspath(__file__))


def main():
    today = datetime.now()
    date_str = today.strftime("%m%d_%H%M%S")
    date_dir = today.strftime("%Y%m%d")
    output_name = f"VrLauncher_{date_str}"

    release_dir = os.path.join(ROOT, "release", date_dir)
    os.makedirs(release_dir, exist_ok=True)

    build_dir = os.path.join(ROOT, "build")
    os.makedirs(build_dir, exist_ok=True)

    print(f"Packaging {output_name}.exe...")
    print(f"Output directory: {release_dir}")

    spec = os.path.join(ROOT, "VrLauncher.spec")
    if os.path.isfile(spec):
        os.remove(spec)

    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--noconsole",
        "--name=VrLauncher",
        "--add-data=src/web;web",
        "--add-data=src/config;config",
        "--workpath=" + build_dir,
        "--distpath=" + release_dir,
        "--noconfirm",
        os.path.join(ROOT, "src", "main.py"),
    ]

    try:
        result = subprocess.run(
            args, check=False, capture_output=True, text=True, cwd=ROOT
        )

        built_exe = os.path.join(release_dir, "VrLauncher.exe")
        output_exe = os.path.join(release_dir, f"{output_name}.exe")

        if os.path.isfile(built_exe):
            os.rename(built_exe, output_exe)
            print(f"Done! Output file: {output_exe}")
            release_config = os.path.join(release_dir, "config")
            os.makedirs(release_config, exist_ok=True)
            defaults_dir = os.path.join(ROOT, "src", "config", "defaults")
            for fn in ("apps.json", "ui.json"):
                src_f = os.path.join(defaults_dir, fn)
                dst_f = os.path.join(release_config, fn)
                if os.path.isfile(src_f) and not os.path.isfile(dst_f):
                    shutil.copy2(src_f, dst_f)
                    print(f"Placed default config: {dst_f}")
        else:
            print(f"Error: VrLauncher.exe not found at {built_exe}")
            sys.exit(1)

    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
