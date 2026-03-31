# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

block_cipher = None

datas_list = []
datas_list += collect_data_files('fastapi')
datas_list += collect_data_files('starlette')
datas_list += collect_data_files('faster_whisper')
datas_list += collect_data_files('ctranslate2')
datas_list += collect_data_files('sentence_transformers')
datas_list += collect_data_files('torch')
datas_list += collect_data_files('transformers')
datas_list += collect_data_files('tokenizers')
datas_list += collect_data_files('lancedb')
datas_list += collect_data_files('pyarrow')
datas_list += collect_data_files('cv2')

# Collect models directory if it exists
if os.path.exists('models'):
    datas_list.append(('models', 'models'))

# --- GPU DEPENDENCY COLLECTION ---
# Automate inclusion of NVIDIA GPU dependencies (cuBLAS and cuDNN)
# This implements the logic from GPU_TRANSCRIBTION_TEMPORARY_FIX.md automatically
binaries_list = collect_dynamic_libs('ctranslate2')

for pkg_name in ['nvidia.cublas', 'nvidia.cudnn']:
    try:
        import importlib.util
        spec = importlib.util.find_spec(pkg_name)
        if spec and spec.submodule_search_locations:
            # handle namespace packages
            pkg_root = list(spec.submodule_search_locations)[0] 
            bin_dir = os.path.join(pkg_root, 'bin')
            if os.path.exists(bin_dir):
                for f in os.listdir(bin_dir):
                    if f.endswith('.dll'):
                        dll_path = os.path.join(bin_dir, f)
                        # Place directly in the root distribution folder
                        binaries_list.append((dll_path, '.'))
                        print(f"[TOBU BUILD] Found GPU dependency: {f}")
    except (Exception, ImportError) as e:
        print(f"[TOBU BUILD] Warning: Could not collect {pkg_name} DLLs: {e}")
# ---------------------------------

a = Analysis(
    ['tobu_launcher.py'],
    pathex=['.'],
    binaries=binaries_list,
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
        'pydantic_core',
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
        
        # Internal Backend modules
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

exe = EXE(pyz,
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


