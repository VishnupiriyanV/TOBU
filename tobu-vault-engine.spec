# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Helm\\FossHack\\TOBU\\tobu_launcher.py'],
    pathex=['C:\\Helm\\FossHack\\TOBU'],
    binaries=[],
    datas=[],
    hiddenimports=['backend.search_and_index.sql_database', 'backend.search_and_index.runtime_service', 'backend.search_and_index.watch', 'uvicorn', 'fastapi', 'chromadb', 'sqlite3', 'sentence_transformers'],
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
    [],
    exclude_binaries=True,
    name='tobu-vault-engine',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='tobu-vault-engine',
)
