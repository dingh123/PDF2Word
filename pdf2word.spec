# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — builds a single-folder app for macOS/Windows/Linux.

Run:
    pyinstaller pdf2word.spec --noconfirm

Version is read from src/__version__.py — bump there, everywhere else follows.
"""
import runpy
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

PROJECT_ROOT = Path(SPECPATH).resolve()
SRC = PROJECT_ROOT / "src"

# --- Read version from the single source of truth -----------------------
VERSION = runpy.run_path(str(SRC / "__version__.py"))["__version__"]
# Windows VSVersionInfo wants a 4-tuple (major, minor, patch, build)
_parts = VERSION.split(".") + ["0", "0", "0", "0"]
VERSION_TUPLE = tuple(int(_parts[i]) for i in range(4))

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

# --- Windows version resource (ignored on macOS/Linux) ------------------
win_version_info = None
if sys.platform == "win32":
    from PyInstaller.utils.win32.versioninfo import (
        VSVersionInfo, FixedFileInfo, StringFileInfo, StringTable,
        StringStruct, VarFileInfo, VarStruct,
    )

    win_version_info = VSVersionInfo(
        ffi=FixedFileInfo(
            filevers=VERSION_TUPLE,
            prodvers=VERSION_TUPLE,
            mask=0x3F,
            flags=0x0,
            OS=0x40004,
            fileType=0x1,
            subtype=0x0,
            date=(0, 0),
        ),
        kids=[
            StringFileInfo([
                StringTable("040904B0", [
                    StringStruct("CompanyName", "DingHui"),
                    StringStruct("FileDescription", "PDF to Word Converter"),
                    StringStruct("FileVersion", VERSION),
                    StringStruct("InternalName", "PDF2Word"),
                    StringStruct("OriginalFilename", "PDF2Word.exe"),
                    StringStruct("ProductName", "PDF2Word"),
                    StringStruct("ProductVersion", VERSION),
                ]),
            ]),
            VarFileInfo([VarStruct("Translation", [0x0409, 1200])]),
        ],
    )

# --- Windows: onefile mode (single PDF2Word.exe) ------------------------
# --- macOS:   onedir + BUNDLE (produces PDF2Word.app, which is already a
#              single user-visible artifact) -----------------------------
if sys.platform == "win32":
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name="PDF2Word",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=None,
        version=win_version_info,
        runtime_tmpdir=None,  # use system default %TEMP%\_MEIxxxx
    )
else:
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
        console=False,
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
                "CFBundleShortVersionString": VERSION,
                "CFBundleVersion": VERSION,
                "NSHighResolutionCapable": True,
                "LSMinimumSystemVersion": "10.15.0",
            },
        )
