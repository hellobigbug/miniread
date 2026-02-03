"""
MiniRead - 字体设置对话框
提供字体选择、大小调节等功能
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFontComboBox, QSpinBox, QSlider, QCheckBox, QColorDialog,
    QGroupBox, QFrame, QWidget, QListWidget, QListWidgetItem,
    QAbstractItemView, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette
import os
import time


class FontSettingsDialog(QDialog):
    """字体设置对话框"""

    # 信号
    font_changed = pyqtSignal(QFont)
    color_changed = pyqtSignal(QColor)
    settings_applied = pyqtSignal(dict)

    def __init__(self, parent=None, current_font=None, current_color=None):
        super().__init__(parent)

        self.setWindowTitle("字体设置")
        self.setFixedSize(400, 450)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # 当前设置
        self._current_font = current_font or QFont("Microsoft YaHei", 16)
        self._current_color = current_color or QColor("#FFFFFF")

        self._init_ui()
        self._load_current_settings()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 字体选择组
        font_group = QGroupBox("字体")
        font_layout = QVBoxLayout(font_group)

        # 字体族选择
        font_family_layout = QHBoxLayout()
        font_family_layout.addWidget(QLabel("字体:"))
        self._font_combo = QFontComboBox()
        self._font_combo.setStyleSheet("""
            QFontComboBox {
                background-color: #3D3D3D;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px 4px;
                min-height: 30px;
            }
            QFontComboBox::drop-down {
                border: none;
            }
            QFontComboBox QAbstractItemView {
                background-color: #3D3D3D;
                color: white;
                selection-background-color: #007ACC;
                min-height: 30px;
                padding: 8px;
            }
        """)
        self._font_combo.currentFontChanged.connect(self._on_font_changed)
        font_family_layout.addWidget(self._font_combo, 1)
        font_layout.addLayout(font_family_layout)

        # 字号选择
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(QLabel("字号:"))

        self._size_spin = QSpinBox()
        self._size_spin.setRange(8, 72)
        self._size_spin.setValue(16)
        self._size_spin.setSuffix(" px")
        self._size_spin.setStyleSheet("""
            QSpinBox {
                background-color: #3D3D3D;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px 4px;
                min-height: 30px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #4D4D4D;
                border: none;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #5D5D5D;
            }
        """)
        self._size_spin.valueChanged.connect(self._on_size_changed)
        font_size_layout.addWidget(self._size_spin)

        self._size_slider = QSlider(Qt.Horizontal)
        self._size_slider.setRange(8, 72)
        self._size_slider.setValue(16)
        self._size_slider.valueChanged.connect(self._size_spin.setValue)
        self._size_spin.valueChanged.connect(self._size_slider.setValue)
        font_size_layout.addWidget(self._size_slider, 1)

        font_layout.addLayout(font_size_layout)

        # 字体样式
        style_layout = QHBoxLayout()
        self._bold_check = QCheckBox("粗体")
        self._bold_check.setStyleSheet("""
            QCheckBox {
                min-height: 30px;
                padding: 8px;
            }
        """)
        self._bold_check.stateChanged.connect(self._on_style_changed)
        style_layout.addWidget(self._bold_check)

        self._italic_check = QCheckBox("斜体")
        self._italic_check.setStyleSheet("""
            QCheckBox {
                min-height: 30px;
                padding: 8px;
            }
        """)
        self._italic_check.stateChanged.connect(self._on_style_changed)
        style_layout.addWidget(self._italic_check)

        style_layout.addStretch()
        font_layout.addLayout(style_layout)

        layout.addWidget(font_group)

        # 颜色设置组
        color_group = QGroupBox("颜色")
        color_layout = QHBoxLayout(color_group)

        color_layout.addWidget(QLabel("文字颜色:"))

        self._color_preview = QFrame()
        self._color_preview.setFixedSize(60, 30)
        self._color_preview.setFrameStyle(QFrame.Box | QFrame.Plain)
        self._color_preview.setAutoFillBackground(True)
        color_layout.addWidget(self._color_preview)

        self._color_btn = QPushButton("选择颜色...")
        self._color_btn.setStyleSheet("""
            QPushButton {
                min-height: 16px;
                padding: 8px 16px;
            }
        """)
        self._color_btn.clicked.connect(self._choose_color)
        color_layout.addWidget(self._color_btn)

        color_layout.addStretch()
        layout.addWidget(color_group)

        # 预览
        preview_group = QGroupBox("预览")
        preview_layout = QVBoxLayout(preview_group)

        self._preview_label = QLabel("MiniRead 阅读辅助工具 - 预览文本")
        self._preview_label.setAlignment(Qt.AlignCenter)
        self._preview_label.setMinimumHeight(50)
        self._preview_label.setStyleSheet("""
            QLabel {
                background-color: #2D2D2D;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        preview_layout.addWidget(self._preview_label)

        layout.addWidget(preview_group)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._reset_btn = QPushButton("重置默认")
        self._reset_btn.setStyleSheet("""
            QPushButton {
                min-height: 30px;
                padding: 8px 16px;
            }
        """)
        self._reset_btn.clicked.connect(self._reset_to_default)
        button_layout.addWidget(self._reset_btn)

        self._cancel_btn = QPushButton("取消")
        self._cancel_btn.setStyleSheet("""
            QPushButton {
                min-height: 30px;
                padding: 8px 16px;
            }
        """)
        self._cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self._cancel_btn)

        self._apply_btn = QPushButton("应用")
        self._apply_btn.setStyleSheet("""
            QPushButton {
                min-height: 30px;
                padding: 8px 16px;
            }
        """)
        self._apply_btn.clicked.connect(self._apply_settings)
        self._apply_btn.setDefault(True)
        button_layout.addWidget(self._apply_btn)

        layout.addLayout(button_layout)

    def _load_current_settings(self):
        """加载当前设置"""
        # 字体
        self._font_combo.setCurrentFont(self._current_font)
        self._size_spin.setValue(self._current_font.pointSize())
        self._bold_check.setChecked(self._current_font.bold())
        self._italic_check.setChecked(self._current_font.italic())

        # 颜色
        self._update_color_preview()
        self._update_preview()

    def _on_font_changed(self, font):
        """字体改变"""
        self._current_font.setFamily(font.family())
        self._update_preview()

    def _on_size_changed(self, size):
        """字号改变"""
        self._current_font.setPointSize(size)
        self._update_preview()

    def _on_style_changed(self):
        """样式改变"""
        self._current_font.setBold(self._bold_check.isChecked())
        self._current_font.setItalic(self._italic_check.isChecked())
        self._update_preview()

    def _choose_color(self):
        """选择颜色"""
        color = QColorDialog.getColor(self._current_color, self, "选择文字颜色")
        if color.isValid():
            self._current_color = color
            self._update_color_preview()
            self._update_preview()

    def _update_color_preview(self):
        """更新颜色预览"""
        palette = self._color_preview.palette()
        palette.setColor(QPalette.Window, self._current_color)
        self._color_preview.setPalette(palette)

    def _update_preview(self):
        """更新预览"""
        self._preview_label.setFont(self._current_font)
        self._preview_label.setStyleSheet(f"""
            QLabel {{
                background-color: #2D2D2D;
                border-radius: 5px;
                padding: 10px;
                color: {self._current_color.name()};
            }}
        """)

    def _reset_to_default(self):
        """重置为默认设置"""
        self._current_font = QFont("Microsoft YaHei", 16)
        self._current_color = QColor("#FFFFFF")
        self._load_current_settings()

    def _apply_settings(self):
        """应用设置"""
        settings = {
            'font': self._current_font,
            'color': self._current_color,
            'family': self._current_font.family(),
            'size': self._current_font.pointSize(),
            'bold': self._current_font.bold(),
            'italic': self._current_font.italic()
        }
        self.settings_applied.emit(settings)
        self.accept()

    def get_font(self) -> QFont:
        """获取字体"""
        return self._current_font

    def get_color(self) -> QColor:
        """获取颜色"""
        return self._current_color



class SpeedSettingsDialog(QDialog):
    """滚动速度设置对话框"""

    settings_applied = pyqtSignal(dict)

    def __init__(self, parent=None, current_speed=50, current_direction="left"):
        super().__init__(parent)

        self.setWindowTitle("滚动设置")
        self.setFixedSize(350, 200)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._current_speed = current_speed
        self._current_direction = current_direction

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 速度设置
        speed_group = QGroupBox("滚动速度")
        speed_layout = QHBoxLayout(speed_group)

        speed_layout.addWidget(QLabel("速度:"))

        self._speed_spin = QSpinBox()
        self._speed_spin.setRange(10, 500)
        self._speed_spin.setValue(self._current_speed)
        self._speed_spin.setSuffix(" px/s")
        speed_layout.addWidget(self._speed_spin)

        self._speed_slider = QSlider(Qt.Horizontal)
        self._speed_slider.setRange(10, 500)
        self._speed_slider.setValue(self._current_speed)
        self._speed_slider.valueChanged.connect(self._speed_spin.setValue)
        self._speed_spin.valueChanged.connect(self._speed_slider.setValue)
        speed_layout.addWidget(self._speed_slider, 1)

        layout.addWidget(speed_group)

        # 方向设置
        direction_group = QGroupBox("滚动方向")
        direction_layout = QHBoxLayout(direction_group)

        self._left_check = QCheckBox("向左滚动")
        self._left_check.setChecked(self._current_direction == "left")
        self._left_check.toggled.connect(self._on_direction_changed)
        direction_layout.addWidget(self._left_check)

        self._right_check = QCheckBox("向右滚动")
        self._right_check.setChecked(self._current_direction == "right")
        self._right_check.toggled.connect(lambda checked: self._left_check.setChecked(not checked))
        direction_layout.addWidget(self._right_check)

        layout.addWidget(direction_group)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        apply_btn = QPushButton("应用")
        apply_btn.clicked.connect(self._apply_settings)
        apply_btn.setDefault(True)
        button_layout.addWidget(apply_btn)

        layout.addLayout(button_layout)

    def _on_direction_changed(self, checked):
        """方向改变"""
        self._right_check.setChecked(not checked)

    def _apply_settings(self):
        """应用设置"""
        settings = {
            'speed': self._speed_spin.value(),
            'direction': 'left' if self._left_check.isChecked() else 'right'
        }
        self.settings_applied.emit(settings)
        self.accept()


class DisplaySettingsDialog(QDialog):
    """显示设置对话框（背景色、透明度）"""

    settings_applied = pyqtSignal(dict)

    def __init__(self, parent=None, current_bg_color=None, current_opacity=0.95):
        super().__init__(parent)

        self.setWindowTitle("显示设置")
        self.setFixedSize(450, 420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._current_bg_color = current_bg_color or QColor("#2D2D2D")
        self._current_opacity = current_opacity

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 背景色设置组
        bg_group = QGroupBox("背景颜色")
        bg_layout = QHBoxLayout(bg_group)

        bg_layout.addWidget(QLabel("背景色:"))
        bg_layout.setSpacing(15)

        self._bg_color_preview = QFrame()
        self._bg_color_preview.setFixedSize(80, 40)
        self._bg_color_preview.setFrameStyle(QFrame.Box | QFrame.Plain)
        self._bg_color_preview.setAutoFillBackground(True)
        self._update_bg_color_preview()
        bg_layout.addWidget(self._bg_color_preview)

        self._bg_color_btn = QPushButton("选择颜色...")
        self._bg_color_btn.setStyleSheet("""
            QPushButton {
                min-height: 20px;
                padding: 10px 20px;
                font-size: 14px;
            }
        """)
        self._bg_color_btn.clicked.connect(self._choose_bg_color)
        bg_layout.addWidget(self._bg_color_btn)

        bg_layout.addStretch()
        layout.addWidget(bg_group)

        # 透明度设置组
        opacity_group = QGroupBox("透明度")
        opacity_layout = QVBoxLayout(opacity_group)

        opacity_row = QHBoxLayout()
        opacity_row.addWidget(QLabel("透明度:"))
        opacity_row.setSpacing(15)

        self._opacity_slider = QSlider(Qt.Horizontal)
        self._opacity_slider.setRange(1, 100)  # 最小1%，防止完全透明无法点击
        self._opacity_slider.setValue(int(self._current_opacity * 100))
        self._opacity_slider.setStyleSheet("""
            QSlider::handle:horizontal {
                min-height: 20px;
                width: 20px;
            }
        """)
        self._opacity_slider.valueChanged.connect(self._on_opacity_changed)
        opacity_row.addWidget(self._opacity_slider, 1)

        self._opacity_label = QLabel(f"{int(self._current_opacity * 100)}%")
        self._opacity_label.setFixedWidth(60)
        self._opacity_label.setStyleSheet("""
            QLabel {
                min-height: 40px;
                padding: 10px;
                font-size: 14px;
            }
        """)
        opacity_row.addWidget(self._opacity_label)

        opacity_layout.addLayout(opacity_row)

        # 透明度提示
        hint_label = QLabel("提示: 1% 为几乎透明，100% 为完全不透明")
        hint_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 12px; padding: 8px 0;")
        opacity_layout.addWidget(hint_label)

        layout.addWidget(opacity_group)

        # 预览
        preview_group = QGroupBox("预览")
        preview_layout = QVBoxLayout(preview_group)

        self._preview_frame = QFrame()
        self._preview_frame.setMinimumHeight(80)
        self._preview_frame.setStyleSheet(self._get_preview_style())

        preview_inner_layout = QHBoxLayout(self._preview_frame)
        self._preview_label = QLabel("MiniRead 预览效果")
        self._preview_label.setAlignment(Qt.AlignCenter)
        self._preview_label.setStyleSheet("color: white; background: transparent;")
        preview_inner_layout.addWidget(self._preview_label)

        preview_layout.addWidget(self._preview_frame)
        layout.addWidget(preview_group)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._reset_btn = QPushButton("重置默认")
        self._reset_btn.setStyleSheet("""
            QPushButton {
                min-height: 40px;
                padding: 10px 20px;
                font-size: 14px;
            }
        """)
        self._reset_btn.clicked.connect(self._reset_to_default)
        button_layout.addWidget(self._reset_btn)

        self._cancel_btn = QPushButton("取消")
        self._cancel_btn.setStyleSheet("""
            QPushButton {
                min-height: 40px;
                padding: 10px 20px;
                font-size: 14px;
            }
        """)
        self._cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self._cancel_btn)

        self._apply_btn = QPushButton("应用")
        self._apply_btn.setStyleSheet("""
            QPushButton {
                min-height: 40px;
                padding: 10px 20px;
                font-size: 14px;
            }
        """)
        self._apply_btn.clicked.connect(self._apply_settings)
        self._apply_btn.setDefault(True)
        button_layout.addWidget(self._apply_btn)

        layout.addLayout(button_layout)

    def _get_preview_style(self):
        """获取预览样式"""
        r, g, b = self._current_bg_color.red(), self._current_bg_color.green(), self._current_bg_color.blue()
        alpha = self._current_opacity
        return f"""
            QFrame {{
                background-color: rgba({r}, {g}, {b}, {alpha});
                border-radius: 8px;
                border: 1px solid rgba(100, 100, 100, 0.5);
            }}
        """

    def _update_bg_color_preview(self):
        """更新背景色预览"""
        palette = self._bg_color_preview.palette()
        palette.setColor(QPalette.Window, self._current_bg_color)
        self._bg_color_preview.setPalette(palette)

    def _update_preview(self):
        """更新整体预览"""
        self._preview_frame.setStyleSheet(self._get_preview_style())

    def _choose_bg_color(self):
        """选择背景颜色"""
        color = QColorDialog.getColor(self._current_bg_color, self, "选择背景颜色")
        if color.isValid():
            self._current_bg_color = color
            self._update_bg_color_preview()
            self._update_preview()

    def _on_opacity_changed(self, value):
        """透明度改变"""
        self._current_opacity = value / 100.0
        self._opacity_label.setText(f"{value}%")
        self._update_preview()

    def _reset_to_default(self):
        """重置为默认设置"""
        self._current_bg_color = QColor("#2D2D2D")
        self._current_opacity = 0.95
        self._opacity_slider.setValue(95)
        self._update_bg_color_preview()
        self._update_preview()

    def _apply_settings(self):
        """应用设置"""
        settings = {
            'background_color': self._current_bg_color,
            'opacity': self._current_opacity
        }
        self.settings_applied.emit(settings)
        self.accept()


class LibraryDialog(QDialog):
    """阅读目录对话框"""

    file_selected = pyqtSignal(str)
    file_removed = pyqtSignal(str)

    def __init__(self, parent=None, reading_history=None):
        super().__init__(parent)

        self.setWindowTitle("阅读目录")
        self.setFixedSize(500, 400)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._reading_history = reading_history or {}

        # 拖拽相关
        self._is_dragging = False
        self._drag_position = QPoint()

        self._init_ui()
        self._load_history()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 背景容器
        self._bg_frame = QFrame()
        self._bg_frame.setStyleSheet("""
            QFrame {
                background-color: #2D2D2D;
                border: 1px solid #3D3D3D;
                border-radius: 8px;
            }
        """)
        bg_layout = QVBoxLayout(self._bg_frame)
        bg_layout.setContentsMargins(15, 15, 15, 15)
        bg_layout.setSpacing(10)

        # 顶部标题栏
        title_bar = QHBoxLayout()

        title_label = QLabel("阅读目录")
        title_label.setStyleSheet("color: white; font-weight: bold; font-size: 14px; border: none;")
        title_bar.addWidget(title_label)

        title_bar.addStretch()

        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888;
                border: none;
                font-size: 18px;
                font-weight: bold;
                margin-top: -5px;
            }
            QPushButton:hover {
                color: white;
            }
        """)
        close_btn.clicked.connect(self.reject)
        title_bar.addWidget(close_btn)

        bg_layout.addLayout(title_bar)

        # 列表标题
        recent_label = QLabel("最近阅读:")
        recent_label.setStyleSheet("color: #AAA; font-size: 12px; border: none; margin-top: 5px;")
        bg_layout.addWidget(recent_label)

        # 书籍列表
        self._list_widget = QListWidget()
        self._list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self._list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._list_widget.setStyleSheet("""
            QListWidget {
                background-color: #1E1E1E;
                color: #DDD;
                border: 1px solid #3D3D3D;
                border-radius: 4px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #2D2D2D;
            }
            QListWidget::item:selected {
                background-color: #3D3D3D;
                color: white;
            }
            QListWidget::item:hover:!selected {
                background-color: #2D2D2D;
            }
        """)
        # 移除滚动条样式
        self._list_widget.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: #1E1E1E;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #444;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        bg_layout.addWidget(self._list_widget)

        # 按钮栏
        button_layout = QHBoxLayout()

        self._remove_btn = QPushButton("删除记录")
        self._remove_btn.setCursor(Qt.PointingHandCursor)
        self._remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #3D3D3D;
                color: #BBB;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #4D4D4D;
                color: white;
            }
        """)
        self._remove_btn.clicked.connect(self._remove_selected)
        button_layout.addWidget(self._remove_btn)

        button_layout.addStretch()

        self._open_btn = QPushButton("开始阅读")
        self._open_btn.setCursor(Qt.PointingHandCursor)
        self._open_btn.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0098FF;
            }
        """)
        self._open_btn.clicked.connect(self._open_selected)
        self._open_btn.setDefault(True)
        button_layout.addWidget(self._open_btn)

        bg_layout.addLayout(button_layout)
        layout.addWidget(self._bg_frame)

    # 鼠标拖动支持
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._is_dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._is_dragging = False

    def _load_history(self):
        """加载阅读历史"""
        self._list_widget.clear()

        # 按最后阅读时间排序
        sorted_files = sorted(
            self._reading_history.items(),
            key=lambda x: x[1].get('last_read', 0),
            reverse=True
        )

        for file_path, data in sorted_files:
            if not os.path.exists(file_path):
                continue

            filename = os.path.basename(file_path)
            last_read_time = time.strftime(
                "%Y-%m-%d %H:%M",
                time.localtime(data.get('last_read', 0))
            )

            # 这里可以根据文件总长度计算百分比，但目前只保存了行号
            # 我们简单显示最后阅读的行号
            current_line = data.get('char_index', 0)

            item_text = f"{filename}\n  上次阅读: {last_read_time} | 进度: 第 {current_line + 1} 行"

            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, file_path)
            self._list_widget.addItem(item)

        if self._list_widget.count() > 0:
            self._list_widget.setCurrentRow(0)

    def _on_item_double_clicked(self, item):
        """双击项目"""
        file_path = item.data(Qt.UserRole)
        self.file_selected.emit(file_path)
        self.accept()

    def _open_selected(self):
        """打开选中文件"""
        items = self._list_widget.selectedItems()
        if items:
            self._on_item_double_clicked(items[0])

    def _remove_selected(self):
        """删除选中记录"""
        items = self._list_widget.selectedItems()
        if not items:
            return

        item = items[0]
        file_path = item.data(Qt.UserRole)

        # 移除列表项
        row = self._list_widget.row(item)
        self._list_widget.takeItem(row)

        # 发送删除信号
        self.file_removed.emit(file_path)




class ConfirmationDialog(QDialog):
    """自定义确认对话框"""

    def __init__(self, parent=None, title="确认", content="确定要执行此操作吗？"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(300, 150)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._title = title
        self._content = content

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 主背景容器
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #2D2D2D;
                border: 1px solid #3D3D3D;
                border-radius: 8px;
            }
        """)
        layout.addWidget(container)

        inner_layout = QVBoxLayout(container)
        inner_layout.setContentsMargins(20, 20, 20, 20)
        inner_layout.setSpacing(15)

        # 标题
        title_label = QLabel(self._title)
        title_label.setStyleSheet("""
            color: #FFFFFF;
            font-size: 16px;
            font-weight: bold;
            font-family: "Microsoft YaHei";
            border: none;
        """)
        inner_layout.addWidget(title_label)

        # 内容
        content_label = QLabel(self._content)
        content_label.setWordWrap(True)
        content_label.setStyleSheet("""
            color: #CCCCCC;
            font-size: 14px;
            font-family: "Microsoft YaHei";
            border: none;
        """)
        inner_layout.addWidget(content_label)

        inner_layout.addStretch()

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #CCCCCC;
                padding: 6px 12px;
                font-family: "Microsoft YaHei";
            }
            QPushButton:hover {
                background-color: #3D3D3D;
                border-color: #666666;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background-color: #444444;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        confirm_btn = QPushButton("确定")
        confirm_btn.setCursor(Qt.PointingHandCursor)
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
                border: none;
                border-radius: 4px;
                color: #FFFFFF;
                padding: 6px 16px;
                font-family: "Microsoft YaHei";
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E53935;
            }
            QPushButton:pressed {
                background-color: #C62828;
            }
        """)
        confirm_btn.clicked.connect(self.accept)
        btn_layout.addWidget(confirm_btn)

        inner_layout.addLayout(btn_layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()


class ScreenColorPicker(QWidget):
    """全屏取色器 - 点击屏幕任意位置获取颜色"""

    color_picked = pyqtSignal(QColor)
    picker_closed = pyqtSignal()

    def __init__(self, initial_color=None):
        super().__init__()

        self._current_color = initial_color or QColor("#FFFFFF")
        self._screenshot = None
        self._magnifier_size = 150  # 放大镜大小
