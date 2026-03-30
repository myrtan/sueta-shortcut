# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\Python\\Sueta Shortcut\\Sueta_Shortcut.pyw'],
    pathex=[],
    binaries=[],
    datas=[('D:\\Python\\Sueta Shortcut\\sueta.ico', '.')],
    hiddenimports=[],
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
    name='Sueta Shortcut',
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
    icon=['D:\\Python\\Sueta Shortcut\\sueta.ico'],
)
