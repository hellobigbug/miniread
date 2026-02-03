"""
MiniRead - 按行显示文本组件
实现单行文本静态显示，通过鼠标/键盘切换行
"""

from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QFontMetrics, QPainter, QColor


class LineTextWidget(QWidget):
    """按行显示文本组件"""

    # 信号
    line_changed = pyqtSignal(int, int)  # 当前行, 总行数
    reached_end = pyqtSignal()  # 到达末尾
    reached_start = pyqtSignal()  # 到达开头

    def __init__(self, parent=None):
        super().__init__(parent)

        # 文本内容
        self._full_text = ""  # 完整文本
        self._lines = []  # 按行分割的显示文本
        self._line_start_indices = []  # 每一行在完整文本中的起始索引
        self._current_line = 0  # 当前行号
        self._total_lines = 0  # 总行数

        # 字体设置
        self._font = QFont("Microsoft YaHei", 16)
        self._text_color = QColor("#FFFFFF")

        # 设置属性
        self.setFocusPolicy(Qt.NoFocus)  # 不接收焦点，让主窗口处理键盘
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # 鼠标事件穿透到父窗口

    def setText(self, text: str) -> None:
        """设置文本内容，自动排版"""
        self._full_text = text or ""
        self._reflow_text()
        self._current_line = 0
        self.line_changed.emit(self._current_line, self._total_lines)
        self.update()

    def _reflow_text(self) -> None:
        """重新排版文本"""
        if not self._full_text:
            self._lines = []
            self._line_start_indices = []
            self._total_lines = 0
            return

        fm = QFontMetrics(self._font)
        available_width = max(100, self.width() - 20)  # 左右各留10像素边距

        self._lines = []
        self._line_start_indices = []

        current_idx = 0
        # 按段落分割（硬换行）
        paragraphs = self._full_text.split('\n')

        for i, para in enumerate(paragraphs):
            # 如果不是最后一段，para 后面原本有一个换行符
            # 计算该段落结束后在 full_text 中的下一个索引位置
            # split 会移除分隔符，所以 para 的长度不包含换行符
            # 但我们需要维护在 _full_text 中的索引

            # 如果段落为空（即原文本有连续换行），也算一行空行或者忽略？
            # 这里的逻辑是：如果是空行，显示为空行
            if not para:
                # self._lines.append("")
                # self._line_start_indices.append(current_idx)
                current_idx += 1 # 跳过换行符
                continue

            # 如果段落宽度小于可用宽度，直接作为一行
            if fm.horizontalAdvance(para) <= available_width:
                self._lines.append(para)
                self._line_start_indices.append(current_idx)
                current_idx += len(para) + 1  # +1 是因为换行符
                continue

            # 需要拆分长段落
            current_line = ""
            current_width = 0
            line_start_idx = current_idx

            for char in para:
                char_width = fm.horizontalAdvance(char)
                if current_width + char_width > available_width:
                    self._lines.append(current_line)
                    self._line_start_indices.append(line_start_idx)

                    line_start_idx += len(current_line)
                    current_line = char
                    current_width = char_width
                else:
                    current_line += char
                    current_width += char_width

            if current_line:
                self._lines.append(current_line)
                self._line_start_indices.append(line_start_idx)

            current_idx += len(para) + 1

        self._total_lines = len(self._lines)

    def resizeEvent(self, event) -> None:
        """窗口大小改变时重新排版"""
        # 记录当前阅读位置的字符索引
        current_char_idx = self.getCurrentCharIndex()

        self._reflow_text()

        # 恢复阅读位置
        self.setPosition(current_char_idx)

        super().resizeEvent(event)

    def text(self) -> str:
        """获取当前显示的文本"""
        if self._lines and 0 <= self._current_line < len(self._lines):
            return self._lines[self._current_line]
        return ""

    def fullText(self) -> str:
        """获取完整文本"""
        return self._full_text

    def setFont(self, font: QFont) -> None:
        """设置字体"""
        self._font = font
        # 记录位置，重排，恢复位置
        current_char_idx = self.getCurrentCharIndex()
        self._reflow_text()
        self.setPosition(current_char_idx)
        self.update()

    def font(self) -> QFont:
        """获取字体"""
        return self._font

    def setTextColor(self, color: QColor) -> None:
        """设置文本颜色"""
        self._text_color = color
        self.update()

    def textColor(self) -> QColor:
        """获取文本颜色"""
        return self._text_color

    def nextLine(self) -> None:
        """切换到下一行"""
        if self._lines and self._current_line < self._total_lines - 1:
            self._current_line += 1
            self.line_changed.emit(self._current_line, self._total_lines)
            self.update()
        elif self._lines and self._current_line >= self._total_lines - 1:
            self.reached_end.emit()

    def prevLine(self) -> None:
        """切换到上一行"""
        if self._lines and self._current_line > 0:
            self._current_line -= 1
            self.line_changed.emit(self._current_line, self._total_lines)
            self.update()
        elif self._lines and self._current_line <= 0:
            self.reached_start.emit()

    def firstLine(self) -> None:
        """跳转到第一行"""
        if self._lines:
            self._current_line = 0
            self.line_changed.emit(self._current_line, self._total_lines)
            self.update()

    def lastLine(self) -> None:
        """跳转到最后一行"""
        if self._lines:
            self._current_line = self._total_lines - 1
            self.line_changed.emit(self._current_line, self._total_lines)
            self.update()

    def gotoLine(self, line_num: int) -> None:
        """跳转到指定行"""
        if self._lines and 0 <= line_num < self._total_lines:
            self._current_line = line_num
            self.line_changed.emit(self._current_line, self._total_lines)
            self.update()

    def getCurrentLine(self) -> int:
        """获取当前行号"""
        return self._current_line

    def getTotalLines(self) -> int:
        """获取总行数"""
        return self._total_lines

    def setPosition(self, index: int) -> None:
        """设置到指定字符索引位置"""
        # 查找包含该索引的行
        target_line = 0
        if self._line_start_indices:
            for i, start_idx in enumerate(self._line_start_indices):
                if start_idx > index:
                    break
                target_line = i

        self.gotoLine(target_line)

    def getCurrentCharIndex(self) -> int:
        """获取当前行在全文中的起始字符索引"""
        if 0 <= self._current_line < len(self._line_start_indices):
            return self._line_start_indices[self._current_line]
        return 0

    # 兼容旧接口的空方法
    def setScrollSpeed(self, speed: int) -> None:
        pass

    def scrollSpeed(self) -> int:
        return 50

    def setScrollDirection(self, direction: str) -> None:
        pass

    def scrollDirection(self) -> str:
        return "left"

    def setPauseOnHover(self, pause: bool) -> None:
        pass

    def startScrolling(self) -> None:
        pass

    def stopScrolling(self) -> None:
        pass

    def toggleScrolling(self) -> None:
        self.nextLine()

    def isScrolling(self) -> bool:
        return False

    def resetPosition(self) -> None:
        self.firstLine()

    def paintEvent(self, event) -> None:
        """绘制文本"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        painter.setFont(self._font)
        painter.setPen(self._text_color)

        # 获取当前行文本
        text = self.text()
        if not text:
            text = "无内容 - 点击📁打开文件"

        # 计算绘制位置（垂直居中）
        fm = QFontMetrics(self._font)
        y = (self.height() + fm.ascent() - fm.descent()) // 2

        # 水平居中绘制
        text_width = fm.horizontalAdvance(text)
        x = (self.width() - text_width) // 2
        if x < 10:
            x = 10  # 左边留点边距

        painter.drawText(x, y, text)


# 保持旧类名兼容
ScrollingTextWidget = LineTextWidget
