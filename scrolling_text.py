"""\
MiniRead - 按行显示文本组件

采用懒加载模式：
- 不预先构建行列表，setText 时 O(1)
- 只记录当前字符位置，按需查找当前行
- 进度保存为百分比，避免行号计算
- 添加位置历史缓存，优化大文件性能

这种设计使大文件加载几乎无延迟。
"""

from __future__ import annotations

import re
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QFontMetrics, QPainter, QColor


class LineTextWidget(QWidget):
    """按行显示文本组件（懒加载模式 + 性能优化）"""

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

        # 性能优化：位置历史缓存（用于快速回退）
        self._position_history = []  # 最近访问的位置列表
        self._max_history = 100  # 最多缓存100个位置
        self._last_width = 0  # 上次计算时的窗口宽度

        # 设置属性
        self.setFocusPolicy(Qt.NoFocus)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def setText(self, text: str) -> None:
        """设置文本内容 - 将所有文本连接成一行"""
        if text:
            # 将所有换行符替换为空格，形成连续文本
            self._full_text = text.replace('\n', ' ').replace('\r', ' ')
            # 合并多个连续空格为一个
            self._full_text = re.sub(r'\s+', ' ', self._full_text).strip()
        else:
            self._full_text = ""

        self._text_length = len(self._full_text)
        self._current_pos = 0
        self._position_history = []  # 清空历史
        self._last_width = 0
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
        """获取当前位置的剩余文本"""
        if not self._full_text:
            return ""

        # 确保位置有效
        pos = max(0, min(self._current_pos, self._text_length - 1)) if self._text_length > 0 else 0

        # 返回从当前位置到文本末尾的所有内容
        return self._full_text[pos:]

    def _get_display_line_length(self, text: str, available_width: int) -> int:
        """计算在给定宽度下能显示多少个字符（智能断行）"""
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

        # 如果找到了可显示的字符数，尝试在标点符号处断行
        if result > 0:
            result = self._find_best_break_point(text, result, fm, available_width)

        return result

    def _find_best_break_point(self, text: str, max_length: int, fm: QFontMetrics, available_width: int) -> int:
        """在标点符号处寻找最佳断行点"""
        if max_length <= 0 or max_length >= len(text):
            return max_length

        # 特殊处理：检查下一个字符是否是句子结束符
        # 如果是，尝试将其包含在当前行（如果宽度允许）
        if max_length < len(text):
            next_char = text[max_length]
            if next_char in '。！？!?；;':
                # 尝试包含这个标点符号
                test_text = text[:max_length + 1]
                test_width = fm.horizontalAdvance(test_text)
                # 如果宽度在合理范围内（允许超出10%），则包含标点
                if test_width <= available_width * 1.1:
                    return max_length + 1

        # 特殊处理：检查是否在双引号内（对话内容）
        # 如果断点在双引号内，尝试延伸到右双引号之后
        quote_result = self._handle_quote_break(text, max_length, fm, available_width)
        if quote_result != max_length:
            return quote_result

        # 定义断行优先级（从高到低）
        # 优先级1: 句号、问号、感叹号等句子结束符
        sentence_end_marks = '。！？!?；;'
        # 优先级2: 逗号、顿号等句内停顿符
        pause_marks = '，、,、'
        # 优先级3: 其他标点符号
        other_marks = '：:）)】}」』"\'》>'

        # 在max_length范围内向前搜索最佳断点（最多回退30%）
        search_start = max(0, int(max_length * 0.7))
        search_text = text[search_start:max_length + 1]

        # 优先级1: 查找句子结束符
        for i in range(len(search_text) - 1, -1, -1):
            if search_text[i] in sentence_end_marks:
                return search_start + i + 1

        # 优先级2: 查找逗号等停顿符
        for i in range(len(search_text) - 1, -1, -1):
            if search_text[i] in pause_marks:
                return search_start + i + 1

        # 优先级3: 查找其他标点符号
        for i in range(len(search_text) - 1, -1, -1):
            if search_text[i] in other_marks:
                return search_start + i + 1

        # 优先级4: 查找空格
        for i in range(len(search_text) - 1, -1, -1):
            if search_text[i] == ' ':
                return search_start + i + 1

        # 如果没有找到合适的断点，返回原始长度
        return max_length

    def _handle_quote_break(self, text: str, max_length: int, fm: QFontMetrics, available_width: int) -> int:
        """处理双引号内的断行 - 尽量保持对话完整

        Args:
            text: 待处理的文本
            max_length: 最大可显示长度
            fm: 字体度量对象
            available_width: 可用宽度

        Returns:
            调整后的断点位置，如果不需要调整则返回max_length
        """
        # 支持的引号类型（中英文双引号）
        left_quotes = '""'
        right_quotes = '""'

        # 检查max_length位置前是否有未闭合的左引号
        text_before = text[:max_length]

        # 统计左右引号数量
        left_count = sum(text_before.count(q) for q in left_quotes)
        right_count = sum(text_before.count(q) for q in right_quotes)

        # 如果左引号多于右引号，说明在引号内
        if left_count > right_count:
            # 查找后续的右引号位置
            remaining_text = text[max_length:]

            # 在合理范围内查找右引号（最多延伸50%的max_length）
            search_limit = min(len(remaining_text), int(max_length * 0.5))

            for i in range(search_limit):
                if remaining_text[i] in right_quotes:
                    # 找到右引号，延伸到引号之后
                    new_length = max_length + i + 1

                    # 检查引号后是否紧跟标点符号，如果有则一起包含
                    if new_length < len(text):
                        next_char = text[new_length]
                        if next_char in '。！？!?，、,；;：:':
                            # 检查宽度是否允许
                            test_text = text[:new_length + 1]
                            test_width = fm.horizontalAdvance(test_text)
                            if test_width <= available_width * 1.1:
                                new_length += 1

                    # 检查新长度的宽度是否在合理范围内
                    test_text = text[:new_length]
                    test_width = fm.horizontalAdvance(test_text)
                    if test_width <= available_width * 1.15:  # 允许超出15%
                        return new_length

        # 如果不在引号内，或者找不到合适的右引号，返回原始长度
        return max_length

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

    def _add_to_history(self, pos: int) -> None:
        """添加位置到历史记录"""
        if not self._position_history or self._position_history[-1] != pos:
            self._position_history.append(pos)
            if len(self._position_history) > self._max_history:
                self._position_history.pop(0)

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
        current_width = self.width()

        # 如果窗口宽度改变，清空历史
        if current_width != self._last_width:
            self._position_history = []
            self._last_width = current_width

        display_length = self._get_display_line_length(current_text, available_width)

        if display_length == 0:
            display_length = 1

        # 保存当前位置到历史
        self._add_to_history(self._current_pos)

        # 移动到下一个显示行
        new_pos = self._current_pos + display_length

        # 检查是否到达末尾
        if new_pos >= self._text_length:
            self.reached_end.emit()
            return

        self._current_pos = new_pos
        self._emit_progress()
        self.update()

    def prevLine(self) -> None:
        """切换到上一行（根据窗口宽度智能分行）- 优化版"""
        if not self._full_text:
            return

        if self._current_pos == 0:
            self.reached_start.emit()
            return

        # 尝试从历史记录中获取上一个位置（O(1)操作）
        if len(self._position_history) >= 2:
            # 移除当前位置
            self._position_history.pop()
            # 获取上一个位置
            prev_pos = self._position_history[-1]
            self._current_pos = prev_pos
            self._emit_progress()
            self.update()
            return

        # 如果历史记录不足，使用估算方法（避免从头遍历）
        available_width = max(10, self.width() - 20)

        # 估算一行的平均字符数
        sample_text = self._full_text[max(0, self._current_pos - 200):self._current_pos]
        if sample_text:
            avg_display_len = self._get_display_line_length(sample_text, available_width)
            if avg_display_len == 0:
                avg_display_len = 1
        else:
            avg_display_len = 50

        # 从估算位置开始向前搜索
        search_start = max(0, self._current_pos - avg_display_len * 3)

        pos = search_start
        prev_display_start = search_start

        while pos < self._current_pos:
            remaining = self._full_text[pos:]
            display_len = self._get_display_line_length(remaining, available_width)
            if display_len == 0:
                display_len = 1

            next_pos = pos + display_len
            if next_pos >= self._current_pos:
                break

            prev_display_start = pos
            pos = next_pos

        self._current_pos = prev_display_start
        self._position_history = []  # 清空历史，因为使用了估算
        self._emit_progress()
        self.update()

    def firstLine(self) -> None:
        """跳转到第一行"""
        if self._current_pos != 0:
            self._current_pos = 0
            self._position_history = []
            self._emit_progress()
            self.update()

    def lastLine(self) -> None:
        """跳转到最后一行 - 优化版（使用反向估算）"""
        if not self._full_text:
            return

        # 获取可显示宽度
        available_width = max(10, self.width() - 20)

        # 从末尾取样本估算一行字符数
        sample_size = min(500, self._text_length)
        sample_text = self._full_text[-sample_size:]
        avg_display_len = self._get_display_line_length(sample_text, available_width)
        if avg_display_len == 0:
            avg_display_len = 1

        # 从估算的最后一行位置开始搜索
        estimated_last_pos = max(0, self._text_length - avg_display_len * 2)

        pos = estimated_last_pos
        last_display_start = estimated_last_pos

        while pos < self._text_length:
            remaining = self._full_text[pos:]
            display_len = self._get_display_line_length(remaining, available_width)
            if display_len == 0:
                display_len = 1

            next_pos = pos + display_len
            if next_pos >= self._text_length:
                last_display_start = pos
                break

            last_display_start = pos
            pos = next_pos

        self._current_pos = last_display_start
        self._position_history = []
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
        self._position_history = []
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
        self._current_pos = max(0, min(index, self._text_length - 1)) if self._text_length > 0 else 0
        self._position_history = []  # 清空历史，因为是跳转
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
        """窗口大小改变：清空历史缓存"""
        self._position_history = []
        self._last_width = 0
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
            text = "无内容 - 右键打开菜单加载文件"
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
