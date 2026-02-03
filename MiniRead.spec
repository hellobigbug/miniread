# -*- mode: python ; coding: utf-8 -*-
# MiniRead PyInstaller 配置文件（修复兼容性问题版本）

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

block_cipher = None

# 收集PyQt5平台插件和动态库 - 修复Qt平台插件缺失问题
qt_datas = collect_data_files('PyQt5', subdir='Qt5/plugins/platforms')
qt_binaries = collect_dynamic_libs('PyQt5')

# 注意：已改用ctypes替代pywin32，无需收集pywin32动态库
# 保留ctypes相关导入即可

# 合并所有二进制文件
all_binaries = qt_binaries

# 合并所有数据文件
all_datas = qt_datas

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=all_binaries,
    datas=all_datas,
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
        'lxml.html',
        'lxml.html.clean',
        'lxml.html.defs',
        'html.parser',
        'xml.etree.ElementTree',
        'xml.etree.cElementTree',

        # 工具库
        'chardet',
        'chardet.universaldetector',
        'charset_normalizer',

        # Windows API - 已改用ctypes，无需pywin32
        # 'win32api',
        # 'win32con',
        # 'win32gui',
        # 'pywintypes',
        # 'win32com',
        # 'win32com.client',
        # 'win32com.client.dynamic',
        # 'pythoncom',

        # 标准库（确保包含）
        'logging',
        'logging.handlers',
        'pathlib',
        'json',
        'traceback',
        'ctypes',
        'ctypes.wintypes',
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
        'tkinter',
        'PySide2',
        'PySide6',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

import platform

# 构建带版本号和平台信息的后缀
# 格式: MiniRead-v{版本号}-{平台}-{架构}.exe
APP_VERSION = "1.0.0"
system = platform.system().lower()  # windows/linux/darwin
machine = platform.machine().lower()  # amd64/x86_64/arm64

# 统一架构命名 (amd64 -> x64, x86_64 -> x64)
if machine in ['amd64', 'x86_64']:
    arch = 'x64'
elif machine in ['arm64', 'aarch64']:
    arch = 'arm64'
else:
    arch = machine

exe_name = f'MiniRead-v{APP_VERSION}-{system}-{arch}'

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=exe_name,
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
    icon='icon.ico',
    version_file='MiniRead_version.txt',  # 版本信息文件
    uac_admin=False,  # 不需要管理员权限
    uac_uiaccess=False,
)
