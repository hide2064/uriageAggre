# PyInstaller spec — Sales Data Aggregator
from PyInstaller.utils.hooks import collect_all

block_cipher = None

webview_datas, webview_binaries, webview_hiddenimports = collect_all('webview')

a = Analysis(
    ['backend/main.py'],
    pathex=['.'],
    binaries=webview_binaries,
    datas=[
        ('frontend/dist', 'frontend/dist'),
        ('config',        'config'),
        *webview_datas,
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops', 'uvicorn.loops.auto',
        'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
        'uvicorn.lifespan', 'uvicorn.lifespan.off',
        'uvicorn.main',
        'fastapi',
        'sqlalchemy', 'sqlalchemy.dialects.sqlite',
        'pandas', 'openpyxl',
        *webview_hiddenimports,
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SalesAggregator',
    debug=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='SalesAggregator',
)
