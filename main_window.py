"""
MiniRead - 主窗口
实现悬浮置顶、透明背景、拖动等功能
"""

import sys
import os
import time
from typing import Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QFileDialog, QMenu, QAction, QSystemTrayIcon,
    QApplication, QMessageBox, QToolTip, QDialog
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


class MainWindow(QMainWindow):
    """主窗口类"""

    # 常量定义
    WINDOW_HIDE_TIMEOUT = 120000  # 窗口自动隐藏时间（毫秒）- 2分钟
    CONFIG_SAVE_DELAY = 2000  # 配置保存延迟（毫秒）- 2秒
    EDGE_MARGIN = 15  # 边缘检测距离（像素）
    POSITION_SAVE_INTERVAL = 10  # 每翻页N次保存一次阅读位置

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

        # 边缘拖拽调整大小相关
        self._resize_edge = None
        self._resize_start_pos = QPoint()
        self._resize_start_geometry = None

        # 窗口自动隐藏相关
        self._window_hide_timer = QTimer(self)
        self._window_hide_timer.timeout.connect(self._auto_hide_window)
        self._window_hide_timer.setSingleShot(True)

        # 配置保存定时器（延迟保存，避免频繁IO）
        self._config_save_timer = QTimer(self)
        self._config_save_timer.timeout.connect(self._save_config)
        self._config_save_timer.setSingleShot(True)

        # 鼠标摇动检测相关
        self._shake_positions = []
        self._last_mouse_time = 0

        # 阅读位置保存优化
        self._page_turn_count = 0  # 翻页计数器
        self._last_saved_position = 0  # 上次保存的位置

        # 初始化UI（轻量级，不做耗时操作）
        self._init_window()
        self._init_ui()
        self._init_tray()
        self._load_config()

        # 检查是否首次启动
        is_first_launch = self.config.get("app.first_launch", True)

        if is_first_launch:
            # 首次启动，显示欢迎文本
            self._show_welcome()
            # 标记为已启动过
            self.config.set("app.first_launch", False)
        else:
            # 非首次启动，延迟加载上次阅读的文件
            QTimer.singleShot(100, self._deferred_load_last_file)

        # 启动窗口自动隐藏定时器
        self._window_hide_timer.start(self.WINDOW_HIDE_TIMEOUT)

    def _deferred_load_last_file(self) -> None:
        """延迟加载上次阅读的文件（在窗口显示后调用）"""
        last_pos = self.config.get("last_position", {})
        file_path = last_pos.get("file")
        if file_path and os.path.exists(file_path):
            self._load_file(file_path)

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

        # 启用拖拽文件功能
        self.setAcceptDrops(True)

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

        # 文本显示区域
        self._text_widget = LineTextWidget()
        self._text_widget.progress_changed.connect(self._on_progress_changed)
        main_layout.addWidget(self._text_widget, 1)

        # 进度显示（百分比）
        self._line_label = QLabel("0%")
        self._line_label.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 12px;")
        self._line_label.setFixedWidth(50)
        self._line_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self._line_label)

    def _init_tray(self):
        """初始化系统托盘"""
        # 创建托盘图标
        self._tray_icon = QSystemTrayIcon(self)
        self._tray_icon.setToolTip("MiniRead - 阅读工具")

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
        welcome_text = """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    欢迎使用 MiniRead 阅读工具
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📖 快速开始
  ▸ 右键打开菜单 → 选择"打开文件"
  ▸ 或直接拖拽文件到窗口中

⌨️ 键盘快捷键
  ▸ 空格 / 回车 / ↓ / → ────── 下一行
  ▸ ↑ / ← / Backspace ────── 上一行
  ▸ Home / End ──────────── 跳转到首行/末行
  ▸ PageUp / PageDown ───── 快速翻页 (±10%)

🖱️ 鼠标操作
  ▸ 滚轮 ──────────────── 上下翻页
  ▸ 右键 ──────────────── 打开功能菜单
  ▸ 左键拖拽 ───────────── 移动窗口位置
  ▸ 边缘拖拽 ───────────── 调整窗口大小

⚙️ 智能功能
  ▸ 自动保存阅读进度
  ▸ 下次打开自动恢复到上次位置
  ▸ 2分钟无操作自动隐藏窗口
  ▸ 双击托盘图标可快速显示/隐藏

📄 支持格式
  ▸ TXT、PDF、DOCX、MD 等多种文本格式

🎨 个性化设置
  ▸ 右键菜单 → 字体设置 → 自定义字体和颜色
  ▸ 右键菜单 → 显示设置 → 调整背景色和透明度

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  提示：右键打开菜单开始使用 →
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
        self._text_widget.setText(welcome_text)

    def _open_file(self):
        """打开文件"""
        self._reset_window_hide_timer()
        file_filter = FileParser.get_file_filter()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开文件", "", file_filter
        )

        if file_path:
            self._load_file(file_path)

    def _load_file(self, file_path: str):
        """加载文件 - 增强错误处理"""
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
            restored = False
            if last_pos > 0:
                self._text_widget.setPosition(last_pos)
                self._last_saved_position = last_pos
                restored = True

            # 重置翻页计数器
            self._page_turn_count = 0

            # 添加到最近文件
            self.config.add_recent_file(file_path)

            # 立即保存阅读历史（确保文件出现在阅读目录中）
            self.config.save_reading_position(
                file_path,
                self._text_widget.getCurrentCharIndex()
            )

            # 更新托盘提示
            self._tray_icon.setToolTip(f"MiniRead - {filename}")

            # 显示恢复提示
            if restored:
                progress = self._text_widget.getProgress()
                self._tray_icon.showMessage(
                    "已恢复阅读进度",
                    f"已恢复到上次阅读位置 (进度: {int(progress * 100)}%)",
                    QSystemTrayIcon.Information,
                    2000
                )

        except FileNotFoundError:
            QMessageBox.critical(self, "错误", f"文件不存在:\n{file_path}")
        except PermissionError:
            QMessageBox.critical(self, "错误", f"没有权限读取文件:\n{file_path}")
        except UnicodeDecodeError:
            QMessageBox.critical(
                self, "错误",
                f"文件编码错误，无法读取:\n{file_path}\n\n建议：请确保文件是UTF-8编码"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "错误",
                f"无法打开文件:\n{file_path}\n\n错误详情: {str(e)}"
            )

    def _prev_line(self):
        """上一行"""
        self._text_widget.prevLine()
        self._on_page_turn()

    def _next_line(self):
        """下一行"""
        self._text_widget.nextLine()
        self._on_page_turn()

    def _on_page_turn(self):
        """翻页时调用 - 优化阅读位置保存"""
        if not self._current_file:
            return

        self._page_turn_count += 1

        # 每翻页N次才保存一次
        if self._page_turn_count >= self.POSITION_SAVE_INTERVAL:
            current_pos = self._text_widget.getCurrentCharIndex()
            # 只有位置真正改变时才保存
            if current_pos != self._last_saved_position:
                self.config.save_reading_position(self._current_file, current_pos)
                self._last_saved_position = current_pos
                self._page_turn_count = 0

    def _toggle_scroll(self):
        """切换下一行（兼容旧快捷键）"""
        self._next_line()

    def _on_progress_changed(self, progress: float):
        """进度改变"""
        percent = int(progress * 100)
        self._line_label.setText(f"{percent}%")

    def _show_font_settings(self):
        """显示字体设置对话框"""
        self._reset_window_hide_timer()
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
        self._reset_window_hide_timer()
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
        self._reset_window_hide_timer()
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
            # 显示窗口时重启定时器
            self._window_hide_timer.start(self.WINDOW_HIDE_TIMEOUT)
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
        new_size = min(20, font.pointSize() + 2)
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

    def _set_font_size_preset(self, size: int):
        """设置字体大小预设"""
        font = self._text_widget.font()
        font.setPointSize(size)
        self._text_widget.setFont(font)
        self._save_config()

    def increase_speed(self):
        """下一行（兼容旧接口）"""
        self._next_line()

    def decrease_speed(self):
        """上一行（兼容旧接口）"""
        self._prev_line()

    def _reset_hide_timer(self):
        """重置隐藏定时器（用户交互时调用）- 简化版，仅重置窗口隐藏"""
        self._reset_window_hide_timer()

    def _reset_window_hide_timer(self):
        """重置窗口隐藏定时器（任何用户活动时调用）"""
        self._window_hide_timer.stop()
        self._window_hide_timer.start(self.WINDOW_HIDE_TIMEOUT)

    def _auto_hide_window(self):
        """自动隐藏窗口（2分钟无操作）"""
        if not self._is_hidden:
            self.hide()
            self._is_hidden = True
            self.visibility_changed.emit(False)

    def _detect_shake(self, pos, current_time: int):
        """检测鼠标摇动 - 优化算法减少计算量

        Args:
            pos: 鼠标位置
            current_time: 当前时间戳（毫秒）
        """
        # 添加当前位置和时间
        self._shake_positions.append((pos.x(), pos.y(), current_time))

        # 移除超过时间窗口的旧位置（优化：只保留必要的数据）
        cutoff_time = current_time - self.SHAKE_TIME_WINDOW
        self._shake_positions = [
            (x, y, t) for x, y, t in self._shake_positions
            if t >= cutoff_time
        ]

        # 需要至少指定数量的位置点来检测摇动
        if len(self._shake_positions) < self.SHAKE_MIN_POINTS:
            return False

        # 优化：只检查最近的位置点，避免处理过多历史数据
        recent_positions = self._shake_positions[-self.SHAKE_MIN_POINTS * 2:]

        # 检测是否有足够次数的大幅度左右摇动
        shake_count = 0
        direction = None

        for i in range(1, len(recent_positions)):
            x_prev, _, _ = recent_positions[i-1]
            x_curr, _, _ = recent_positions[i]
            x_diff = x_curr - x_prev

            # 检测大幅度移动
            if abs(x_diff) > self.SHAKE_THRESHOLD:
                current_direction = 'right' if x_diff > 0 else 'left'

                # 如果方向改变，计数增加
                if direction is not None and direction != current_direction:
                    shake_count += 1
                    if shake_count >= self.SHAKE_COUNT_THRESHOLD:
                        # 检测到足够次数的摇动，清空历史并隐藏窗口
                        self._shake_positions.clear()
                        return True

                direction = current_direction

        return False

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

    def _get_resize_edge(self, pos):
        """检测鼠标是否在窗口边缘，返回边缘类型"""
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        margin = self.EDGE_MARGIN

        # 检测角落（优先级更高）
        if x <= margin and y <= margin:
            return 'topleft'
        elif x >= w - margin and y <= margin:
            return 'topright'
        elif x <= margin and y >= h - margin:
            return 'bottomleft'
        elif x >= w - margin and y >= h - margin:
            return 'bottomright'
        # 检测边缘
        elif x <= margin:
            return 'left'
        elif x >= w - margin:
            return 'right'
        elif y <= margin:
            return 'top'
        elif y >= h - margin:
            return 'bottom'

        return None

    def _update_cursor(self, edge):
        """根据边缘类型更新鼠标光标"""
        if edge == 'left' or edge == 'right':
            self.setCursor(Qt.SizeHorCursor)
        elif edge == 'top' or edge == 'bottom':
            self.setCursor(Qt.SizeVerCursor)
        elif edge == 'topleft' or edge == 'bottomright':
            self.setCursor(Qt.SizeFDiagCursor)
        elif edge == 'topright' or edge == 'bottomleft':
            self.setCursor(Qt.SizeBDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    # 鼠标事件
    def enterEvent(self, event):
        """鼠标进入窗口"""
        self._reset_window_hide_timer()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开窗口"""
        self.setCursor(Qt.ArrowCursor)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """鼠标按下"""
        self.setFocus()  # 确保窗口获得焦点
        self._reset_hide_timer()  # 重置隐藏定时器
        self._reset_window_hide_timer()  # 重置窗口隐藏定时器

        if event.button() == Qt.LeftButton:
            pos = event.pos()
            edge = self._get_resize_edge(pos)

            if edge:
                # 在边缘，开始调整大小
                self._resize_edge = edge
                self._resize_start_pos = event.globalPos()
                self._resize_start_geometry = self.geometry()
            else:
                # 不在边缘，开始拖动窗口
                self._is_dragging = True
                self._drag_position = event.globalPos() - self.frameGeometry().topLeft()

            event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动"""
        # 正在调整大小
        if self._resize_edge and event.buttons() == Qt.LeftButton:
            self._do_resize(event.globalPos())
            event.accept()
            return

        # 正在拖拽窗口
        if self._is_dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_position)
            event.accept()
            return

        # 没有按下鼠标，更新光标样式
        if not event.buttons():
            edge = self._get_resize_edge(event.pos())
            self._update_cursor(edge)

            # 只在没有按下鼠标时检测摇动（频率限制优化）
            current_time = int(time.time() * 1000)
            if current_time - self._last_mouse_time >= self.SHAKE_DETECT_INTERVAL:
                self._last_mouse_time = current_time
                if self._detect_shake(event.globalPos(), current_time):
                    # 检测到摇动，隐藏窗口
                    if not self._is_hidden:
                        self.hide()
                        self._is_hidden = True
                        self.visibility_changed.emit(False)
                    return

                # 重置窗口隐藏定时器（限频后调用）
                self._reset_window_hide_timer()

    def _do_resize(self, global_pos):
        """执行窗口大小调整"""
        delta = global_pos - self._resize_start_pos
        geo = self._resize_start_geometry

        new_x = geo.x()
        new_y = geo.y()
        new_width = geo.width()
        new_height = geo.height()

        # 根据边缘类型调整
        if 'left' in self._resize_edge:
            new_x = geo.x() + delta.x()
            new_width = geo.width() - delta.x()
        elif 'right' in self._resize_edge:
            new_width = geo.width() + delta.x()

        if 'top' in self._resize_edge:
            new_y = geo.y() + delta.y()
            new_height = geo.height() - delta.y()
        elif 'bottom' in self._resize_edge:
            new_height = geo.height() + delta.y()

        # 限制最小尺寸
        if new_width < self.minimumWidth():
            new_width = self.minimumWidth()
            if 'left' in self._resize_edge:
                new_x = geo.x() + geo.width() - new_width

        if new_height < self.minimumHeight():
            new_height = self.minimumHeight()
            if 'top' in self._resize_edge:
                new_y = geo.y() + geo.height() - new_height

        # 应用新的几何形状
        self.setGeometry(new_x, new_y, new_width, new_height)

    def mouseReleaseEvent(self, event):
        """鼠标释放"""
        if event.button() == Qt.LeftButton:
            self._is_dragging = False
            self._resize_edge = None
            # 延迟保存配置，避免频繁IO导致卡顿
            self._config_save_timer.stop()
            self._config_save_timer.start(self.CONFIG_SAVE_DELAY)
            event.accept()

    def _create_menu_stylesheet(self) -> str:
        """创建菜单样式表"""
        return """
            QMenu {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3A3A3A, stop:1 #2A2A2A);
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 5px 3px;
                font-size: 13px;
            }
            QMenu::item {
                padding: 8px 35px 8px 20px;
                border-radius: 4px;
                margin: 1px 4px;
                background-color: transparent;
            }
            QMenu::item:selected {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0078D4, stop:1 #005A9E);
                color: #FFFFFF;
            }
            QMenu::item:pressed {
                background-color: #004578;
            }
            QMenu::item:disabled {
                color: #888888;
                background-color: transparent;
            }
            QMenu::separator {
                height: 1px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent, stop:0.5 #555555, stop:1 transparent);
                margin: 4px 12px;
            }
        """

    def _create_file_menu_section(self, menu: QMenu) -> None:
        """创建文件菜单部分"""
        # 打开文件
        open_action = QAction("打开文件...", self)
        open_action.triggered.connect(self._open_file)
        menu.addAction(open_action)

        # 最近文件子菜单
        recent_history = self.config.get_reading_history()
        if recent_history:
            recent_files = sorted(
                recent_history.items(),
                key=lambda x: x[1].get('last_read', 0),
                reverse=True
            )[:5]  # 最近5个文件

            if recent_files:
                recent_menu = menu.addMenu("最近文件")
                recent_menu.setStyleSheet(self._create_menu_stylesheet())
                for file_path, _ in recent_files:
                    if os.path.exists(file_path):
                        filename = os.path.basename(file_path)
                        # 截断过长的文件名
                        if len(filename) > 30:
                            filename = filename[:27] + "..."
                        action = QAction(filename, self)
                        action.setToolTip(file_path)  # 完整路径作为提示
                        action.triggered.connect(lambda checked, p=file_path: self._load_file(p))
                        recent_menu.addAction(action)

        # 阅读目录
        library_action = QAction("阅读目录", self)
        library_action.triggered.connect(self._show_library)
        menu.addAction(library_action)

    def _create_settings_menu_section(self, menu: QMenu) -> None:
        """创建设置菜单部分"""
        # 字体设置
        font_action = QAction("字体设置...", self)
        font_action.triggered.connect(self._show_font_settings)
        menu.addAction(font_action)

        # 字体大小快速选择
        font_size_menu = menu.addMenu("字体大小")
        font_size_menu.setStyleSheet(self._create_menu_stylesheet())
        current_size = self._text_widget.font().pointSize()
        sizes = [
            ("极小", 9),
            ("小", 12),
            ("中等", 16),
            ("大", 24),
            ("特大", 32)
        ]
        for name, size in sizes:
            if size == current_size:
                action = QAction(f"✓ {name} ({size}px)", self)
            else:
                action = QAction(f"   {name} ({size}px)", self)
            action.triggered.connect(lambda checked, s=size: self._set_font_size_preset(s))
            font_size_menu.addAction(action)

        # 显示设置
        display_action = QAction("显示设置...", self)
        display_action.triggered.connect(self._show_display_settings)
        menu.addAction(display_action)

    def _create_help_menu_section(self, menu: QMenu) -> None:
        """创建帮助菜单部分"""
        help_menu = menu.addMenu("操作说明")
        help_menu.setStyleSheet(self._create_menu_stylesheet())

        # 键盘操作说明
        keyboard_section = QAction("键盘操作", self)
        keyboard_section.setEnabled(False)
        help_menu.addAction(keyboard_section)

        keyboard_shortcuts = [
            ("空格 / 回车", "下一行"),
            ("方向键 ↑↓", "上/下一行"),
            ("方向键 ←→", "上/下一行"),
            ("Home / End", "首行/末行"),
            ("PageUp / PageDown", "快速翻页 (±10%)")
        ]
        for key, desc in keyboard_shortcuts:
            action = QAction(f"  {key} → {desc}", self)
            action.setEnabled(False)
            help_menu.addAction(action)

        help_menu.addSeparator()

        # 鼠标操作说明
        mouse_section = QAction("鼠标操作", self)
        mouse_section.setEnabled(False)
        help_menu.addAction(mouse_section)

        mouse_operations = [
            ("滚轮", "上/下翻页"),
            ("左键拖拽", "移动窗口"),
            ("边缘拖拽", "调整窗口大小"),
            ("快速摇动3次", "隐藏窗口")
        ]
        for operation, desc in mouse_operations:
            action = QAction(f"  {operation} → {desc}", self)
            action.setEnabled(False)
            help_menu.addAction(action)

    def _create_window_menu_section(self, menu: QMenu) -> None:
        """创建窗口操作菜单部分"""
        # 隐藏窗口
        hide_action = QAction("隐藏窗口", self)
        hide_action.triggered.connect(self._toggle_visibility)
        menu.addAction(hide_action)

        # 退出程序
        quit_action = QAction("退出程序", self)
        quit_action.triggered.connect(self._confirm_close)
        menu.addAction(quit_action)

    def contextMenuEvent(self, event):
        """右键菜单"""
        self._reset_hide_timer()
        self._reset_window_hide_timer()

        # 创建右键菜单
        context_menu = QMenu(self)
        context_menu.setStyleSheet(self._create_menu_stylesheet())

        # 构建菜单结构
        self._create_file_menu_section(context_menu)
        context_menu.addSeparator()

        self._create_settings_menu_section(context_menu)
        context_menu.addSeparator()

        self._create_help_menu_section(context_menu)
        context_menu.addSeparator()

        self._create_window_menu_section(context_menu)

        # 显示菜单
        context_menu.exec_(event.globalPos())

    def keyPressEvent(self, event):
        """键盘按键 - 翻页"""
        key = event.key()

        # 重置窗口隐藏定时器
        self._reset_window_hide_timer()

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
            # 向下跳 10%
            progress = self._text_widget.getProgress()
            self._text_widget.setProgress(min(1.0, progress + 0.1))
            event.accept()
        elif key == Qt.Key_PageUp:
            # 向上跳 10%
            progress = self._text_widget.getProgress()
            self._text_widget.setProgress(max(0.0, progress - 0.1))
            event.accept()
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        """鼠标滚轮 - 翻页"""
        # 重置窗口隐藏定时器
        self._reset_window_hide_timer()

        delta = event.angleDelta().y()
        if delta > 0:
            self._prev_line()  # 向上滚动 = 上一行
        elif delta < 0:
            self._next_line()  # 向下滚动 = 下一行
        event.accept()

    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """拖拽放下事件"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path:
                self._load_file(file_path)
                event.acceptProposedAction()

    def closeEvent(self, event):
        """窗口关闭事件"""
        self._save_config()
        event.accept()
