"""
MiniRead - 主窗口
实现悬浮置顶、透明背景、拖动等功能
"""

import sys
import os
from typing import Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QFileDialog, QMenu, QAction, QSystemTrayIcon,
    QApplication, QMessageBox, QToolTip
)
from PyQt5.QtCore import Qt, QPoint, QTimer, pyqtSignal, QSize
from PyQt5.QtGui import (
    QFont, QColor, QIcon, QPainter, QBrush, QPen,
    QLinearGradient, QCursor, QPainterPath
)

from scrolling_text import LineTextWidget
from dialogs import FontSettingsDialog, DisplaySettingsDialog, LibraryDialog, ConfirmationDialog
from file_parser import parse_file, FileParser
from config import get_config


class ControlButton(QPushButton):
    """自定义控制按钮"""

    def __init__(self, text: str, tooltip: str = "", parent=None):
        super().__init__(text, parent)
        self.setToolTip(tooltip)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFocusPolicy(Qt.NoFocus)  # 防止按钮抢夺键盘焦点
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 4px;
                color: white;
                font-size: 12px;
                font-family: "Microsoft YaHei", sans-serif;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)


class MainWindow(QMainWindow):
    """主窗口类"""

    # 信号
    visibility_changed = pyqtSignal(bool)

    def __init__(self):
        super().__init__()

        # 配置管理器
        self.config = get_config()

        # 窗口状态
        self._is_dragging = False
        self._drag_position = QPoint()
        self._is_hidden = False
        self._current_file = ""
        self._current_text = ""

        # 初始化UI
        self._init_window()
        self._init_ui()
        self._init_tray()
        self._load_config()

        # 尝试加载上次阅读的文件
        if not self._load_last_file():
            # 如果没有上次文件，显示欢迎文本
            self._show_welcome()

    def _load_last_file(self) -> bool:
        """加载上次阅读的文件"""
        last_pos = self.config.get("last_position", {})
        file_path = last_pos.get("file")
        if file_path and os.path.exists(file_path):
            self._load_file(file_path)
            return True
        return False

    def _init_window(self):
        """初始化窗口属性"""
        # 无边框、置顶、透明背景
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool  # 不在任务栏显示
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 允许窗口接收键盘焦点
        self.setFocusPolicy(Qt.StrongFocus)

        # 启用鼠标跟踪
        self.setMouseTracking(True)

        # 窗口显示时自动获取焦点
        self.setAttribute(Qt.WA_ShowWithoutActivating, False)

        # 设置窗口大小
        self.setMinimumSize(400, 50)
        self.resize(
            self.config.get("window.width", 800),
            self.config.get("window.height", 60)
        )

        # 设置窗口位置
        self.move(
            self.config.get("window.x", 100),
            self.config.get("window.y", 100)
        )

    def _init_ui(self):
        """初始化UI组件"""
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.setSpacing(8)

        # 左侧控制按钮
        left_controls = QHBoxLayout()
        left_controls.setSpacing(4)

        # 文件按钮
        self._file_btn = ControlButton("打开", "打开文件 (Ctrl+Shift+O)")
        self._file_btn.clicked.connect(self._open_file)
        left_controls.addWidget(self._file_btn)

        # 目录按钮
        self._lib_btn = ControlButton("目录", "最近阅读目录")
        self._lib_btn.clicked.connect(self._show_library)
        left_controls.addWidget(self._lib_btn)

        # 上一行按钮
        self._prev_btn = ControlButton("上", "上一行 (↑/←)")
        self._prev_btn.clicked.connect(self._prev_line)
        left_controls.addWidget(self._prev_btn)

        # 下一行按钮
        self._next_btn = ControlButton("下", "下一行 (↓/→/空格)")
        self._next_btn.clicked.connect(self._next_line)
        left_controls.addWidget(self._next_btn)

        main_layout.addLayout(left_controls)

        # 文本显示区域
        self._text_widget = LineTextWidget()
        self._text_widget.line_changed.connect(self._on_line_changed)
        main_layout.addWidget(self._text_widget, 1)

        # 行号显示
        self._line_label = QLabel("0/0")
        self._line_label.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 12px;")
        self._line_label.setFixedWidth(60)
        self._line_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self._line_label)

        # 右侧控制按钮
        right_controls = QHBoxLayout()
        right_controls.setSpacing(4)

        # 字体设置按钮
        self._font_btn = ControlButton("字体", "字体设置")
        self._font_btn.clicked.connect(self._show_font_settings)
        right_controls.addWidget(self._font_btn)

        # 显示设置按钮（背景色等）
        self._display_btn = ControlButton("显示", "显示设置")
        self._display_btn.clicked.connect(self._show_display_settings)
        right_controls.addWidget(self._display_btn)

        # 隐藏按钮
        self._hide_btn = ControlButton("隐藏", "隐藏 (Ctrl+Shift+R)")
        self._hide_btn.clicked.connect(self._toggle_visibility)
        right_controls.addWidget(self._hide_btn)

        # 关闭按钮
        self._close_btn = ControlButton("关闭", "关闭")
        self._close_btn.clicked.connect(self._confirm_close)
        self._close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 100, 100, 0.3);
                border: none;
                border-radius: 4px;
                color: white;
                font-size: 12px;
                font-family: "Microsoft YaHei", sans-serif;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: rgba(255, 100, 100, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(255, 100, 100, 0.7);
            }
        """)
        right_controls.addWidget(self._close_btn)

        main_layout.addLayout(right_controls)

    def _init_tray(self):
        """初始化系统托盘"""
        # 创建托盘图标
        self._tray_icon = QSystemTrayIcon(self)
        self._tray_icon.setToolTip("MiniRead - 阅读辅助工具")

        # 创建托盘菜单
        tray_menu = QMenu()

        show_action = QAction("显示/隐藏", self)
        show_action.triggered.connect(self._toggle_visibility)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        open_action = QAction("打开文件", self)
        open_action.triggered.connect(self._open_file)
        tray_menu.addAction(open_action)

        tray_menu.addSeparator()

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self._quit_app)
        tray_menu.addAction(quit_action)

        self._tray_icon.setContextMenu(tray_menu)
        self._tray_icon.activated.connect(self._on_tray_activated)

        # 设置图标（使用默认图标）
        self._tray_icon.setIcon(self.style().standardIcon(
            self.style().SP_ComputerIcon
        ))
        self._tray_icon.show()

    def _load_config(self):
        """加载配置"""
        # 字体设置
        font = QFont(
            self.config.get("font.family", "Microsoft YaHei"),
            self.config.get("font.size", 16)
        )
        font.setBold(self.config.get("font.bold", False))
        font.setItalic(self.config.get("font.italic", False))
        self._text_widget.setFont(font)

        # 文字颜色
        color = QColor(self.config.get("font.color", "#FFFFFF"))
        self._text_widget.setTextColor(color)

    def _save_config(self):
        """保存配置"""
        # 窗口位置和大小
        pos = self.pos()
        size = self.size()
        self.config.set("window.x", pos.x(), auto_save=False)
        self.config.set("window.y", pos.y(), auto_save=False)
        self.config.set("window.width", size.width(), auto_save=False)
        self.config.set("window.height", size.height(), auto_save=False)

        # 字体设置
        font = self._text_widget.font()
        self.config.set("font.family", font.family(), auto_save=False)
        self.config.set("font.size", font.pointSize(), auto_save=False)
        self.config.set("font.bold", font.bold(), auto_save=False)
        self.config.set("font.italic", font.italic(), auto_save=False)
        self.config.set("font.color", self._text_widget.textColor().name(), auto_save=False)

        # 保存阅读位置
        if self._current_file:
            self.config.save_reading_position(
                self._current_file,
                self._text_widget.getCurrentCharIndex()
            )

        self.config.save()

    def _show_welcome(self):
        """显示欢迎文本"""
        welcome_text = "欢迎使用 MiniRead 阅读辅助工具\n点击[打开]按钮打开文件\n滚轮/方向键 - 翻页\n拖拽阅读框 - 移动窗口"
        self._text_widget.setText(welcome_text)

    def _open_file(self):
        """打开文件"""
        file_filter = FileParser.get_file_filter()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开文件", "", file_filter
        )

        if file_path:
            self._load_file(file_path)

    def _load_file(self, file_path: str):
        """加载文件"""
        try:
            filename, content = parse_file(file_path)

            if not content.strip():
                QMessageBox.warning(self, "警告", "文件内容为空")
                return

            self._current_file = file_path
            self._current_text = content
            self._text_widget.setText(content)

            # 恢复阅读位置
            last_pos = self.config.get_reading_position(file_path)
            if last_pos > 0:
                self._text_widget.setPosition(last_pos)

            # 添加到最近文件
            self.config.add_recent_file(file_path)

            # 更新托盘提示
            self._tray_icon.setToolTip(f"MiniRead - {filename}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开文件:\n{str(e)}")

    def _prev_line(self):
        """上一行"""
        self._text_widget.prevLine()

    def _next_line(self):
        """下一行"""
        self._text_widget.nextLine()

    def _toggle_scroll(self):
        """切换下一行（兼容旧快捷键）"""
        self._next_line()

    def _on_line_changed(self, current: int, total: int):
        """行号改变"""
        if total > 0:
            self._line_label.setText(f"{current + 1}/{total}")
        else:
            self._line_label.setText("0/0")

    def _show_font_settings(self):
        """显示字体设置对话框"""
        dialog = FontSettingsDialog(
            self,
            self._text_widget.font(),
            self._text_widget.textColor()
        )
        dialog.settings_applied.connect(self._apply_font_settings)
        dialog.exec_()

    def _apply_font_settings(self, settings: dict):
        """应用字体设置"""
        self._text_widget.setFont(settings['font'])
        self._text_widget.setTextColor(settings['color'])
        self._save_config()

    def _show_display_settings(self):
        """显示显示设置对话框（背景色等）"""
        dialog = DisplaySettingsDialog(
            self,
            QColor(self.config.get("display.background_color", "#2D2D2D")),
            self.config.get("window.opacity", 0.95)
        )
        dialog.settings_applied.connect(self._apply_display_settings)
        dialog.exec_()

    def _apply_display_settings(self, settings: dict):
        """应用显示设置"""
        self.config.set("display.background_color", settings['background_color'].name(), auto_save=False)
        self.config.set("window.opacity", settings['opacity'], auto_save=False)
        self.config.save()
        self.update()  # 重绘窗口

    def _show_library(self):
        """显示阅读目录"""
        dialog = LibraryDialog(self, self.config.get_reading_history())
        dialog.file_selected.connect(self._load_file)
        dialog.file_removed.connect(self._on_file_removed)
        dialog.exec_()

    def _on_file_removed(self, file_path: str):
        """文件被移除"""
        self.config.remove_reading_history(file_path)

    def _toggle_visibility(self):
        """切换显示/隐藏"""
        if self._is_hidden:
            self.show()
            self._is_hidden = False
        else:
            self.hide()
            self._is_hidden = True
        self.visibility_changed.emit(not self._is_hidden)

    def _on_tray_activated(self, reason):
        """托盘图标被激活"""
        if reason == QSystemTrayIcon.DoubleClick:
            self._toggle_visibility()

    def _confirm_close(self):
        """确认关闭"""
        dialog = ConfirmationDialog(self, "确认退出", "确定要退出 MiniRead 吗？")
        if dialog.exec_() == QDialog.Accepted:
            self._quit_app()

    def _quit_app(self):
        """退出应用"""
        self._save_config()
        if hasattr(self, '_tray_icon') and self._tray_icon:
            self._tray_icon.hide()
        QApplication.quit()

    def increase_font_size(self):
        """增大字号"""
        font = self._text_widget.font()
        new_size = min(72, font.pointSize() + 2)
        font.setPointSize(new_size)
        self._text_widget.setFont(font)
        self._save_config()

    def decrease_font_size(self):
        """减小字号"""
        font = self._text_widget.font()
        new_size = max(8, font.pointSize() - 2)
        font.setPointSize(new_size)
        self._text_widget.setFont(font)
        self._save_config()

    def increase_speed(self):
        """下一行（兼容旧接口）"""
        self._next_line()

    def decrease_speed(self):
        """上一行（兼容旧接口）"""
        self._prev_line()

    # 绘制圆角背景
    def paintEvent(self, event):
        """绘制窗口背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 背景颜色
        bg_color = QColor(self.config.get("display.background_color", "#2D2D2D"))
        opacity = self.config.get("window.opacity", 0.95)
        bg_color.setAlpha(int(255 * opacity))

        # 绘制圆角矩形
        path = QPainterPath()
        radius = self.config.get("display.border_radius", 8)
        path.addRoundedRect(0, 0, self.width(), self.height(), radius, radius)

        painter.fillPath(path, QBrush(bg_color))

        # 绘制边框
        painter.setPen(QPen(QColor(100, 100, 100, 100), 1))
        painter.drawPath(path)

    # 鼠标拖动
    def mousePressEvent(self, event):
        """鼠标按下"""
        self.setFocus()  # 确保窗口获得焦点
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动"""
        if self._is_dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标释放"""
        if event.button() == Qt.LeftButton:
            self._is_dragging = False
            self._save_config()
            event.accept()

    def keyPressEvent(self, event):
        """键盘按键 - 翻页"""
        key = event.key()

        if key in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter, Qt.Key_Down, Qt.Key_Right, Qt.Key_J):
            self._next_line()
            event.accept()
        elif key in (Qt.Key_Up, Qt.Key_Left, Qt.Key_K, Qt.Key_Backspace):
            self._prev_line()
            event.accept()
        elif key == Qt.Key_Home:
            self._text_widget.firstLine()
            event.accept()
        elif key == Qt.Key_End:
            self._text_widget.lastLine()
            event.accept()
        elif key == Qt.Key_PageDown:
            # 向下跳10行
            current = self._text_widget.getCurrentLine()
            total = self._text_widget.getTotalLines()
            target = min(current + 10, total - 1) if total > 0 else 0
            self._text_widget.gotoLine(target)
            event.accept()
        elif key == Qt.Key_PageUp:
            # 向上跳10行
            current = self._text_widget.getCurrentLine()
            target = max(current - 10, 0)
            self._text_widget.gotoLine(target)
            event.accept()
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        """鼠标滚轮 - 翻页"""
        delta = event.angleDelta().y()
        if delta > 0:
            self._prev_line()  # 向上滚动 = 上一行
        elif delta < 0:
            self._next_line()  # 向下滚动 = 下一行
        event.accept()

    def closeEvent(self, event):
        """窗口关闭事件"""
        self._save_config()
        event.accept()
