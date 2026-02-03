"""
MiniRead - Windows阅读工具
主程序入口

功能特点:
- 悬浮置顶窗口，支持透明背景
- 单行滚动文本显示
- 支持TXT、PDF、DOCX、EPUB等格式
- 自定义字体和滚动速度
- 全局快捷键支持
- 阅读目录功能
- 配置自动保存

作者: MiniRead Team
版本: 1.0.0
"""

import sys
import os

# 确保当前目录在路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QTimer, QCoreApplication
from PyQt5.QtGui import QFont

from main_window import MainWindow
from hotkeys import get_hotkey_manager
from config import get_config


class MiniReadApp:
    """MiniRead应用程序类"""

    def __init__(self):
        # 创建Qt应用
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("MiniRead")
        self.app.setApplicationVersion("1.0.0")

        # 设置默认字体
        default_font = QFont("Microsoft YaHei", 9)
        self.app.setFont(default_font)

        # 快速设置应用样式（不显示启动画面）
        self._set_style()

        # 配置管理器
        self.config = get_config()

        # 创建主窗口
        self.main_window = MainWindow()

        # 快捷键管理器（延迟初始化）
        self.hotkey_manager = None

        # 延迟注册快捷键，避免阻塞启动
        QTimer.singleShot(100, self._init_hotkeys)

    def _init_hotkeys(self):
        """延迟初始化快捷键"""
        self.hotkey_manager = get_hotkey_manager()
        self._register_hotkeys()

    def _set_style(self):
        """设置应用样式"""
        style = """
            QToolTip {
                background-color: #2D2D2D;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
            }

            QMenu {
                background-color: #2D2D2D;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
            }

            QMenu::item {
                padding: 5px 20px;
                border-radius: 3px;
            }

            QMenu::item:selected {
                background-color: #3D3D3D;
            }

            QMessageBox {
                background-color: #2D2D2D;
                color: white;
            }

            QMessageBox QPushButton {
                background-color: #3D3D3D;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 60px;
            }

            QMessageBox QPushButton:hover {
                background-color: #4D4D4D;
            }

            QDialog {
                background-color: #2D2D2D;
                color: white;
            }

            QGroupBox {
                color: white;
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }

            QLabel {
                color: white;
            }

            QPushButton {
                background-color: #3D3D3D;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }

            QPushButton:hover {
                background-color: #4D4D4D;
            }

            QPushButton:pressed {
                background-color: #5D5D5D;
            }

            QSpinBox, QDoubleSpinBox {
                background-color: #3D3D3D;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                selection-background-color: #007ACC;
                selection-color: white;
            }

            QSpinBox::up-button, QDoubleSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 20px;
                border: none;
                background-color: #4D4D4D;
                border-top-right-radius: 4px;
            }

            QSpinBox::down-button, QDoubleSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 20px;
                border: none;
                background-color: #4D4D4D;
                border-bottom-right-radius: 4px;
            }

            QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
            QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
                background-color: #5D5D5D;
            }

            QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
                width: 10px;
                height: 10px;
            }

            QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
                width: 10px;
                height: 10px;
            }

            QLineEdit {
                background-color: #3D3D3D;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                selection-background-color: #007ACC;
                selection-color: white;
            }

            QSlider::groove:horizontal {
                height: 6px;
                background: #3D3D3D;
                border-radius: 3px;
            }

            QSlider::handle:horizontal {
                background: #007ACC;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }

            QSlider::handle:horizontal:hover {
                background: #1E90FF;
            }

            QCheckBox {
                color: white;
                spacing: 8px;
            }

            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #555;
                background-color: #3D3D3D;
            }

            QCheckBox::indicator:checked {
                background-color: #007ACC;
                border-color: #007ACC;
            }

            QFontComboBox {
                background-color: #3D3D3D;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
            }

            QFontComboBox::drop-down {
                border: none;
                width: 20px;
            }

            QFontComboBox QAbstractItemView {
                background-color: #2D2D2D;
                color: white;
                selection-background-color: #007ACC;
            }
        """
        self.app.setStyleSheet(style)

    def _register_hotkeys(self):
        """注册全局快捷键"""
        hotkeys = self.config.get("hotkeys", {})

        # 显示/隐藏切换
        self.hotkey_manager.register(
            "toggle_visibility",
            hotkeys.get("toggle_visibility", "ctrl+shift+r"),
            self._safe_call(self.main_window._toggle_visibility)
        )

        # 下一行
        self.hotkey_manager.register(
            "next_line",
            hotkeys.get("next_line", "ctrl+shift+space"),
            self._safe_call(self.main_window._next_line)
        )

        # 上一行
        self.hotkey_manager.register(
            "prev_line",
            hotkeys.get("prev_line", "ctrl+shift+b"),
            self._safe_call(self.main_window._prev_line)
        )

        # 增大字号
        self.hotkey_manager.register(
            "increase_font",
            hotkeys.get("increase_font", "ctrl+shift+up"),
            self._safe_call(self.main_window.increase_font_size)
        )

        # 减小字号
        self.hotkey_manager.register(
            "decrease_font",
            hotkeys.get("decrease_font", "ctrl+shift+down"),
            self._safe_call(self.main_window.decrease_font_size)
        )

        # 下一行（方向键）
        self.hotkey_manager.register(
            "next_line_arrow",
            hotkeys.get("next_line_arrow", "ctrl+shift+right"),
            self._safe_call(self.main_window._next_line)
        )

        # 上一行（方向键）
        self.hotkey_manager.register(
            "prev_line_arrow",
            hotkeys.get("prev_line_arrow", "ctrl+shift+left"),
            self._safe_call(self.main_window._prev_line)
        )

        # 打开文件
        self.hotkey_manager.register(
            "open_file",
            hotkeys.get("open_file", "ctrl+shift+o"),
            self._safe_call(self.main_window._open_file)
        )

    def _safe_call(self, func):
        """创建线程安全的回调函数"""
        def wrapper():
            # 使用QTimer在主线程中执行
            QTimer.singleShot(0, func)
        return wrapper

    def run(self) -> int:
        """运行应用程序"""
        # 直接显示主窗口（无启动画面延迟）
        self.main_window.show()

        # 运行事件循环
        return self.app.exec_()

    def cleanup(self):
        """清理资源"""
        if self.hotkey_manager:
            self.hotkey_manager.unregister_all()


def main():
    """主函数"""
    # 高DPI支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # 创建并运行应用
    app = MiniReadApp()

    try:
        exit_code = app.run()
    finally:
        app.cleanup()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
