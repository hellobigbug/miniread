# -*- mode: python ; coding: utf-8 -*-
# MiniRead PyInstaller 配置文件（增强兼容性版本）

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # PyQt5 核心模块
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.QtPrintSupport',
        'PyQt5.sip',

        # 文件解析库
        'PyPDF2',
        'PyPDF2.generic',
        'docx',
        'docx.oxml',
        'docx.oxml.ns',
        'ebooklib',
        'ebooklib.epub',
        'bs4',
        'lxml',
        'lxml.etree',
        'lxml._elementpath',

        # 系统交互
        'keyboard',
        'chardet',
        'chardet.universaldetector',

        # Windows API
        'win32api',
        'win32con',
        'win32gui',
        'pywintypes',
        'win32com',
        'win32com.client',

        # 标准库（确保包含）
        'logging',
        'logging.handlers',
        'pathlib',
        'json',
        'traceback',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块以减小体积
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'IPython',
        'notebook',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MiniRead',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口（GUI应用）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # 应用程序图标
    version_file=None,
    uac_admin=False,  # 不强制要求管理员权限
    uac_uiaccess=False,
)
