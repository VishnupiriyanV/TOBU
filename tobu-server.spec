# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

from PyInstaller.utils.hooks import collect_data_files

datas_list = []
datas_list += collect_data_files('fastapi')
datas_list += collect_data_files('starlette')

a = Analysis(
    ['tobu_launcher.py'],
    pathex=['.'],
    binaries=[],
    datas=datas_list,
    hiddenimports=[
        'fastapi',
        'fastapi.applications',
        'fastapi.routing',
        'fastapi.middleware',
        'fastapi.middleware.cors',
        'fastapi.staticfiles',
        'fastapi.responses',
        'uvicorn',
        'uvicorn.main',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'starlette',
        'starlette.routing',
        'starlette.middleware',
        'starlette.responses',
        'anyio',
        'anyio._backends._asyncio',
        'click',
        'pydantic',
        'sqlite3',
        'watchdog',
        'python-multipart',
        
        # Heavy ML & Processing Libraries
        'sentence_transformers', 
        'lancedb', 
        'faster_whisper',
        'ctranslate2',
        'torch', 
        'transformers',
        'tokenizers',
        'accelerate',
        'numpy',
        'pandas',
        'pyarrow',
        'chromadb',
        'chromadb.api',
        'chromadb.db.impl',
        'hnswlib',
        
        # Media & Documents
        'PIL', 
        'cv2', 
        'fitz', # PyMuPDF
        'frontmatter',
        
        # Internal Backend modules required to exist dynamically
        'backend.search_and_index.sql_database', 
        'backend.search_and_index.runtime_service', 
        'backend.search_and_index.watch',
        'backend.search_and_index.aural_engine',
        'backend.search_and_index.visual_engine',
        'backend.search_and_index.semantic_engine',
        'backend.search_and_index.document_engine',
        'backend.search_and_index.api_app'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='fastapi-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='fastapi-server',
)
