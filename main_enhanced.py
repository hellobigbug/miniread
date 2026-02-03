"""
MiniRead - Windows阅读工具
主程序入口（增强兼容性版本）

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
import traceback
import logging
from pathlib import Path

# 配置日志
log_dir = Path.home() / '.miniread'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'miniread.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 确保当前目录在路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from PyQt5.QtCore import Qt, QTimer, QCoreApplication
    from PyQt5.QtGui import QFont
except ImportError as e:
    logger.error(f"PyQt5 导入失败: {e}")
    print(f"错误: 无法导入 PyQt5。请确保已安装 PyQt5。\n{e}")
    sys.exit(1)

try:
    from main_window import MainWindow
    from hotkeys import get_hotkey_manager, KEYBOARD_AVAILABLE
    from config import get_config
except ImportError as e:
    logger.error(f"模块导入失败: {e}")
    print(f"错误: 无法导入必要模块。\n{e}")
    sys.exit(1)


class MiniReadApp:
    """MiniRead应用程序类（增强版）"""

    def __init__(self):
        try:
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

            logger.info("MiniRead 应用初始化成功")

        except Exception as e:
            logger.error(f"应用初始化失败: {e}\n{traceback.format_exc()}")
            self._show_error("初始化失败", f"应用初始化时发生错误:\n{str(e)}")
            raise

    def _init_hotkeys(self):
        """延迟初始化快捷键"""
        try:
            if not KEYBOARD_AVAILABLE:
                logger.warning("keyboard 模块不可用，全局快捷键功能已禁用")
                return

            self.hotkey_manager = get_hotkey_manager()
            self._register_hotkeys()
            logger.info("全局快捷键注册成功")

        except Exception as e:
            logger.error(f"快捷键初始化失败: {e}\n{traceback.format_exc()}")
            # 快捷键失败不影响主程序运行
            logger.warning("全局快捷键功能不可用，但程序将继续运行")

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
        try:
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

        except Exception as e:
            logger.error(f"快捷键注册失败: {e}\n{traceback.format_exc()}")

    def _safe_call(self, func):
        """创建线程安全的回调函数"""
        def wrapper():
            try:
                # 使用QTimer在主线程中执行
                QTimer.singleShot(0, func)
            except Exception as e:
                logger.error(f"回调函数执行失败: {e}\n{traceback.format_exc()}")
        return wrapper

    def _show_error(self, title, message):
        """显示错误对话框"""
        try:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec_()
        except:
            # 如果GUI显示失败，至少打印到控制台
            print(f"{title}: {message}")

    def run(self) -> int:
        """运行应用程序"""
        try:
            # 直接显示主窗口（无启动画面延迟）
            self.main_window.show()
            logger.info("主窗口显示成功")

            # 运行事件循环
            return self.app.exec_()

        except Exception as e:
            logger.error(f"应用运行失败: {e}\n{traceback.format_exc()}")
            self._show_error("运行错误", f"应用运行时发生错误:\n{str(e)}")
            return 1

    def cleanup(self):
        """清理资源"""
        try:
            if self.hotkey_manager:
                self.hotkey_manager.unregister_all()
                logger.info("快捷键已清理")
        except Exception as e:
            logger.error(f"清理资源失败: {e}\n{traceback.format_exc()}")


def exception_hook(exc_type, exc_value, exc_traceback):
    """全局异常处理钩子"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("未捕获的异常:", exc_info=(exc_type, exc_value, exc_traceback))
    print(f"\n发生未处理的错误:\n{exc_type.__name__}: {exc_value}")
    print(f"\n详细信息已保存到: {log_file}")


def main():
    """主函数"""
    try:
        # 设置全局异常处理
        sys.excepthook = exception_hook

        logger.info("=" * 50)
        logger.info("MiniRead 启动")
        logger.info(f"Python 版本: {sys.version}")
        logger.info(f"工作目录: {os.getcwd()}")
        logger.info("=" * 50)

        # 高DPI支持
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        # 创建并运行应用
        app = MiniReadApp()

        try:
            exit_code = app.run()
            logger.info(f"应用正常退出，退出码: {exit_code}")
        finally:
            app.cleanup()

        sys.exit(exit_code)

    except Exception as e:
        logger.error(f"主函数异常: {e}\n{traceback.format_exc()}")
        print(f"\n程序启动失败: {e}")
        print(f"详细信息已保存到: {log_file}")
        input("\n按回车键退出...")
        sys.exit(1)


if __name__ == "__main__":
    main()
