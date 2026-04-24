# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — builds a single-folder app for macOS/Windows/Linux.

Run:
    pyinstaller pdf2word.spec --noconfirm
"""
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

PROJECT_ROOT = Path(SPECPATH).resolve()
SRC = PROJECT_ROOT / "src"

block_cipher = None

# pdf2docx pulls in fonts / default configs at runtime — collect them.
hidden = collect_submodules("pdf2docx") + collect_submodules("fitz")
datas = collect_data_files("pdf2docx") + collect_data_files("fontTools")

a = Analysis(
    [str(SRC / "main.py")],
    pathex=[str(SRC)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "PIL.ImageTk",
        "PyQt5",
        "PySide6",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PDF2Word",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # windowed app — no console
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="PDF2Word",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="PDF2Word.app",
        icon=None,
        bundle_identifier="com.dinghui.pdf2word",
        info_plist={
            "CFBundleName": "PDF2Word",
            "CFBundleDisplayName": "PDF 转 Word",
            "CFBundleShortVersionString": "0.1.0",
            "CFBundleVersion": "0.1.0",
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "10.15.0",
        },
    )
