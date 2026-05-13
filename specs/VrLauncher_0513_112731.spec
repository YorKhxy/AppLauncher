# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 配置：单文件 exe，内含 Web 壳静态资源（src/web → 解压目录 web/）。"""
import os

block_cipher = None

ROOT = os.path.abspath(SPECPATH)

a = Analysis(
    [os.path.join(ROOT, "src", "main.py")],
    pathex=[os.path.join(ROOT, "src")],
    binaries=[],
    datas=[(os.path.join(ROOT, "src", "web"), "web")],
    hiddenimports=["webview", "clr_loader", "pythonnet"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="VrLauncher",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
