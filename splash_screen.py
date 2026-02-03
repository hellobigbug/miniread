"""
MiniRead - 启动加载界面
显示启动提示和进度
"""

from PyQt5.QtWidgets import QSplashScreen
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QPen


class SplashScreen(QSplashScreen):
    """启动加载界面"""

    def __init__(self):
        # 创建启动画面
        pixmap = QPixmap(400, 250)
        pixmap.fill(QColor("#2D2D2D"))

        # 绘制内容
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制边框
        painter.setPen(QPen(QColor("#3D3D3D"), 2))
        painter.drawRect(1, 1, 398, 248)

        # 绘制标题
        font = QFont("Microsoft YaHei", 24, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(0, 80, 400, 40, Qt.AlignCenter, "MiniRead")

        # 绘制副标题
        font = QFont("Microsoft YaHei", 12)
        painter.setFont(font)
        painter.setPen(QColor("#AAAAAA"))
        painter.drawText(0, 120, 400, 30, Qt.AlignCenter, "阅读工具")

        # 绘制版本信息
        font = QFont("Microsoft YaHei", 9)
        painter.setFont(font)
        painter.setPen(QColor("#888888"))
        painter.drawText(0, 200, 400, 20, Qt.AlignCenter, "v1.0.0")

        painter.end()

        super().__init__(pixmap, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

    def show_message(self, message):
        """显示加载消息"""
        self.showMessage(
            message,
            Qt.AlignBottom | Qt.AlignCenter,
            QColor("#FFFFFF")
        )
