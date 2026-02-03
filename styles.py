"""
MiniRead - 样式表定义模块
集中管理所有QSS样式
"""

# 应用全局样式
APP_STYLE = """
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

# 移除焦点虚线框的通用样式
NO_FOCUS_STYLE = """
    QWidget {
        outline: none;
    }
    QPushButton {
        outline: none;
    }
    QPushButton:focus {
        outline: none;
        border: none;
    }
    QCheckBox {
        outline: none;
    }
    QCheckBox:focus {
        outline: none;
    }
    QSlider {
        outline: none;
    }
    QSlider:focus {
        outline: none;
    }
    QSpinBox {
        outline: none;
    }
    QSpinBox:focus {
        outline: none;
    }
    QFontComboBox {
        outline: none;
    }
    QFontComboBox:focus {
        outline: none;
    }
    QListWidget {
        outline: none;
    }
    QListWidget:focus {
        outline: none;
    }
    QGroupBox {
        outline: none;
    }
"""
