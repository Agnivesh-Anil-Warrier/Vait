# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller specification file for Vait Infinite Canvas Whiteboard (Windows)."""

import os
from pathlib import Path

block_cipher = None
project_root = Path(__file__).resolve().parent if "__file__" in locals() else Path.cwd()
icon_file = str(project_root / "assets" / "icon.ico")

a = Analysis(
    ["main.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        ("assets", "assets"),
    ],
    hiddenimports=[
        "vait",
        "vait.canvas",
        "vait.clipboard",
        "vait.commands",
        "vait.constants",
        "vait.items",
        "vait.storage",
        "vait.ui",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude massive unused Qt submodules to shrink package size and build time
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebEngineQuick",
        "PySide6.QtPdf",
        "PySide6.QtPdfWidgets",
        "PySide6.QtQuick",
        "PySide6.QtQuickWidgets",
        "PySide6.QtQml",
        "PySide6.Qt3DCore",
        "PySide6.QtSensors",
        "PySide6.QtSerialPort",
        "PySide6.QtNetworkAuth",
        "PySide6.QtBluetooth",
        "PySide6.QtNfc",
        "PySide6.QtPositioning",
        "PySide6.QtSpatialAudio",
        "tkinter",
        "unittest",
        "pytest",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Single-file standalone executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Vait",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)
