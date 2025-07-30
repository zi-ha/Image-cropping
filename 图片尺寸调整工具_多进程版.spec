# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('README.md', '.')],
    hiddenimports=['multiprocessing', 'multiprocessing.spawn', 'multiprocessing.pool', 'concurrent.futures', 'concurrent.futures.process', 'PIL', 'PIL.Image', 'PIL.ImageOps', 'PySide6', 'PySide6.QtCore', 'PySide6.QtWidgets', 'PySide6.QtGui'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='图片尺寸调整工具_多进程版',
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
    icon=['logo.ico'],
)
