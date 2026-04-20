# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for reflecto_sim.

Build:
    pyinstaller reflecto_sim.spec

Output:  dist/reflecto_sim/   (--onedir)

Use --onedir (not --onefile) because numba/llvmlite extract large binaries
at startup which is very slow when bundled into a single exe.
"""

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("materials", "materials"),
        ("assets", "assets"),
    ],
    hiddenimports=[
        # Numba / LLVM
        "numba",
        "numba.core",
        "numba.core.typing",
        "numba.np.ufunc",
        "llvmlite",
        "llvmlite.binding",
        # PySide6 modules that may be missed by the hook
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PySide6.QtOpenGL",
        "PySide6.QtOpenGLWidgets",
        "PySide6.QtSvg",
        "PySide6.QtSvgWidgets",
        # pyqtgraph
        "pyqtgraph",
        "pyqtgraph.graphicsItems",
        "pyqtgraph.widgets",
        # scipy sparse — often auto-missed
        "scipy.sparse.csgraph._validation",
        "scipy.special._cdflib",
        # matplotlib backends (Agg only)
        "matplotlib.backends.backend_agg",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude heavy unused backends
        "matplotlib.backends.backend_qt5agg",
        "matplotlib.backends.backend_tkagg",
        "tkinter",
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
    name="reflecto_sim",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # no console window on Windows
    icon="assets/icon.ico",  # Windows taskbar + exe icon
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="reflecto_sim",
)
