# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('data', 'data'),
        ('models', 'models'),
    ],
    hiddenimports=[
        'pystray',
        'PIL',
        'PIL.Image',
        'win32com.client',
        'win32gui',
        'win32process',
        'win32api',
        'ctypes',
        'requests',
        'queue',
        'sqlite3',
        'core.hook',
        'core.sender',
        'core.word_buffer',
        'core.filters',
        'core.language',
        'core.corrector_base',
        'core.corrector_jamspell',
        'core.corrector_yandex',
        'core.corrector_chain',
        'core.casing',
        'core.whitelist',
        'core.blacklist',
        'core.history',
        'core.undo',
        'core.stats',
        'core.autostart',
        'ui.tray',
        'ui.settings_window',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='t10',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Без консольного окна
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Можно добавить путь к .ico файлу
)
