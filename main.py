"""
MiniRead - Windows阅读工具
主程序入口（增强兼容性版本）

功能特点:
- 悬浮置顶窗口，支持透明背景
- 单行滚动文本显示
- 支持TXT、PDF、DOCX、EPUB等格式
- 自定义字体和滚动速度
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

# 配置日志 - 使用APPDATA目录避免权限问题
def get_log_dir():
    """获取日志目录，优先使用APPDATA"""
    try:
        # 优先使用APPDATA目录（Windows标准应用数据目录）
        appdata = os.environ.get('APPDATA')
        if appdata:
            log_dir = Path(appdata) / 'MiniRead'
        else:
            # 回退到用户主目录
            log_dir = Path.home() / '.miniread'
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir
    except Exception:
        # 最后回退到临时目录
        import tempfile
        return Path(tempfile.gettempdir())

log_dir = get_log_dir()
log_file = log_dir / 'miniread.log'

# 配置日志，添加异常处理防止日志写入失败导致程序崩溃
try:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
except Exception as e:
    # 如果文件日志配置失败，只用控制台日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    print(f"警告: 无法配置文件日志: {e}")

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
    from config import get_config
    from styles import APP_STYLE
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

            logger.info("MiniRead 应用初始化成功")

        except Exception as e:
            logger.error(f"应用初始化失败: {e}\n{traceback.format_exc()}")
            self._show_error("初始化失败", f"应用初始化时发生错误:\n{str(e)}")
            raise

    def _set_style(self):
        """设置应用样式"""
        self.app.setStyleSheet(APP_STYLE)

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
            logger.info("应用清理完成")
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
