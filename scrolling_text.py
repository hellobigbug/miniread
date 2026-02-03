"""\
MiniRead - 按行显示文本组件

采用懒加载模式：
- 不预先构建行列表，setText 时 O(1)
- 只记录当前字符位置，按需查找当前行
- 进度保存为百分比，避免行号计算

这种设计使大文件加载几乎无延迟。
"""

from __future__ import annotations

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QFontMetrics, QPainter, QColor


class LineTextWidget(QWidget):
    """按行显示文本组件（懒加载模式）"""

    # 信号：当前行变化时发出 (当前行号仅用于显示，-1表示未知)
    line_changed = pyqtSignal(int, int)  # 当前行, 总行数（-1表示未统计）
    reached_end = pyqtSignal()  # 到达末尾
    reached_start = pyqtSignal()  # 到达开头
    progress_changed = pyqtSignal(float)  # 进度百分比 0.0-1.0

    def __init__(self, parent=None):
        super().__init__(parent)

        # 文本内容
        self._full_text = ""  # 完整文本
        self._text_length = 0  # 文本长度（缓存）
        self._current_pos = 0  # 当前字符位置（行首位置）

        # 字体设置
        self._font = QFont("Microsoft YaHei", 16)
        self._text_color = QColor("#FFFFFF")

        # 设置属性
        self.setFocusPolicy(Qt.NoFocus)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def setText(self, text: str) -> None:
        """设置文本内容 - O(1) 操作，不做任何预处理"""
        self._full_text = text or ""
        self._text_length = len(self._full_text)
        self._current_pos = 0
        self._emit_progress()
        self.update()

    def _emit_progress(self) -> None:
        """发出进度信号"""
        if self._text_length > 0:
            progress = self._current_pos / self._text_length
        else:
            progress = 0.0
        self.progress_changed.emit(progress)
        # 兼容旧接口：发送 -1 表示不统计行号
        self.line_changed.emit(-1, -1)

    def _get_current_line_text(self) -> str:
        """获取当前位置所在的显示行文本（根据窗口宽度自动分割）"""
        if not self._full_text:
            return ""

        # 确保位置有效
        pos = max(0, min(self._current_pos, self._text_length - 1)) if self._text_length > 0 else 0

        # 找原始行首（向前找换行符）
        line_start = self._full_text.rfind('\n', 0, pos + 1)
        line_start = line_start + 1 if line_start != -1 else 0

        # 找原始行尾（向后找换行符）
        line_end = self._full_text.find('\n', pos)
        if line_end == -1:
            line_end = self._text_length

        # 获取原始行文本
        full_line = self._full_text[line_start:line_end]

        # 计算从当前位置到行尾的文本
        offset_in_line = pos - line_start
        remaining_text = full_line[offset_in_line:]

        return remaining_text

    def _get_display_line_length(self, text: str, available_width: int) -> int:
        """计算在给定宽度下能显示多少个字符"""
        if not text:
            return 0

        fm = QFontMetrics(self._font)

        # 二分查找最大可显示字符数
        left, right = 0, len(text)
        result = 0

        while left <= right:
            mid = (left + right) // 2
            width = fm.horizontalAdvance(text[:mid])

            if width <= available_width:
                result = mid
                left = mid + 1
            else:
                right = mid - 1

        return result

    def text(self) -> str:
        """获取当前显示的行文本"""
        return self._get_current_line_text()

    def fullText(self) -> str:
        """获取完整文本"""
        return self._full_text

    def setFont(self, font: QFont) -> None:
        """设置字体"""
        self._font = font
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
        """切换到下一行（根据窗口宽度智能分行）"""
        if not self._full_text:
            return

        # 获取当前显示的文本
        current_text = self._get_current_line_text()
        if not current_text:
            self.reached_end.emit()
            return

        # 计算可显示的字符数
        available_width = max(10, self.width() - 20)
        display_length = self._get_display_line_length(current_text, available_width)

        if display_length == 0:
            # 窗口太窄，至少移动一个字符
            display_length = 1

        # 如果显示长度等于当前文本长度，说明当前行已经全部显示
        if display_length >= len(current_text):
            # 查找下一个换行符
            next_newline = self._full_text.find('\n', self._current_pos)
            if next_newline != -1:
                # 跳到换行符后面
                new_pos = next_newline + 1
            else:
                # 没有换行符，到达末尾
                self.reached_end.emit()
                return
        else:
            # 移动到下一个显示行（当前位置 + 显示长度）
            new_pos = self._current_pos + display_length

        # 检查是否到达末尾
        if new_pos >= self._text_length:
            self.reached_end.emit()
            return

        self._current_pos = new_pos
        self._emit_progress()
        self.update()

    def prevLine(self) -> None:
        """切换到上一行（根据窗口宽度智能分行）"""
        if not self._full_text:
            return

        if self._current_pos == 0:
            self.reached_start.emit()
            return

        # 获取可显示宽度
        available_width = max(10, self.width() - 20)

        # 找当前位置所在的原始行首
        current_line_start = self._full_text.rfind('\n', 0, self._current_pos)
        current_line_start = current_line_start + 1 if current_line_start != -1 else 0

        # 如果当前位置就是行首，需要回到上一个原始行
        if self._current_pos == current_line_start:
            if current_line_start == 0:
                self.reached_start.emit()
                return

            # 找上一个原始行首
            prev_line_start = self._full_text.rfind('\n', 0, current_line_start - 1)
            prev_line_start = prev_line_start + 1 if prev_line_start != -1 else 0

            # 找上一个原始行尾
            prev_line_end = current_line_start - 1
            prev_line_text = self._full_text[prev_line_start:prev_line_end]

            # 计算上一行的最后一个显示行的起始位置
            pos = prev_line_start
            last_display_start = pos

            while pos < prev_line_end:
                remaining = self._full_text[pos:prev_line_end]
                display_len = self._get_display_line_length(remaining, available_width)
                if display_len == 0:
                    display_len = 1

                next_pos = pos + display_len
                if next_pos < prev_line_end:
                    last_display_start = next_pos
                    pos = next_pos
                else:
                    break

            self._current_pos = last_display_start
        else:
            # 在当前原始行内回退一个显示行
            # 需要从行首开始计算所有显示行，找到当前位置的上一个显示行
            pos = current_line_start
            prev_display_start = current_line_start

            while pos < self._current_pos:
                remaining = self._full_text[pos:self._current_pos]
                display_len = self._get_display_line_length(remaining, available_width)
                if display_len == 0:
                    display_len = 1

                next_pos = pos + display_len
                if next_pos >= self._current_pos:
                    break

                prev_display_start = pos
                pos = next_pos

            self._current_pos = prev_display_start

        self._emit_progress()
        self.update()

    def firstLine(self) -> None:
        """跳转到第一行"""
        if self._current_pos != 0:
            self._current_pos = 0
            self._emit_progress()
            self.update()

    def lastLine(self) -> None:
        """跳转到最后一行"""
        if not self._full_text:
            return

        # 找最后一个换行符
        last_newline = self._full_text.rfind('\n')
        if last_newline == -1:
            self._current_pos = 0
        else:
            self._current_pos = last_newline + 1

        self._emit_progress()
        self.update()

    def gotoLine(self, line_num: int) -> None:
        """跳转到指定行（兼容接口，但效率较低）"""
        if not self._full_text or line_num < 0:
            return

        pos = 0
        for _ in range(line_num):
            next_newline = self._full_text.find('\n', pos)
            if next_newline == -1:
                break
            pos = next_newline + 1

        self._current_pos = pos
        self._emit_progress()
        self.update()

    def getCurrentLine(self) -> int:
        """获取当前行号（兼容接口，需要遍历计算）"""
        if not self._full_text:
            return 0
        return self._full_text[:self._current_pos].count('\n')

    def getTotalLines(self) -> int:
        """获取总行数（兼容接口，需要遍历计算）"""
        if not self._full_text:
            return 0
        return self._full_text.count('\n') + 1

    def setPosition(self, index: int) -> None:
        """设置到指定字符索引位置"""
        if not self._full_text:
            self._current_pos = 0
            return

        # 确保位置有效
        index = max(0, min(index, self._text_length - 1)) if self._text_length > 0 else 0

        # 对齐到行首
        line_start = self._full_text.rfind('\n', 0, index + 1)
        self._current_pos = line_start + 1 if line_start != -1 else 0

        self._emit_progress()
        self.update()

    def setProgress(self, progress: float) -> None:
        """设置进度百分比 (0.0-1.0)"""
        if not self._full_text:
            self._current_pos = 0
            return

        progress = max(0.0, min(1.0, progress))
        target_pos = int(self._text_length * progress)
        self.setPosition(target_pos)

    def getProgress(self) -> float:
        """获取当前进度百分比"""
        if self._text_length == 0:
            return 0.0
        return self._current_pos / self._text_length

    def getCurrentCharIndex(self) -> int:
        """获取当前行在全文中的起始字符索引"""
        return self._current_pos

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

    def resizeEvent(self, event) -> None:
        """窗口大小改变：只需重绘"""
        self.update()
        super().resizeEvent(event)

    def paintEvent(self, event) -> None:
        """绘制文本 - 单行显示，根据窗口宽度自动截断"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        painter.setFont(self._font)
        painter.setPen(self._text_color)

        if not self._full_text:
            text = "无内容 - 右键打开菜单或点击📂打开文件"
        else:
            text = self._get_current_line_text()

        fm = QFontMetrics(self._font)
        available_width = max(10, self.width() - 20)

        # 计算能显示多少字符
        display_length = self._get_display_line_length(text, available_width)
        if display_length > 0:
            display_text = text[:display_length]
        else:
            display_text = text[:1] if text else ""

        # 垂直居中绘制
        y = (self.height() + fm.ascent() - fm.descent()) // 2

        # 水平居中绘制
        text_width = fm.horizontalAdvance(display_text)
        x = (self.width() - text_width) // 2
        if x < 10:
            x = 10

        painter.drawText(x, y, display_text)


# 保持旧类名兼容
ScrollingTextWidget = LineTextWidget
