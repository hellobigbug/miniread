"""
MiniRead - 文件解析模块
支持TXT、PDF、DOCX、EPUB等格式
"""

import os
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple

import chardet


class FileParser(ABC):
    """文件解析器基类"""

    @abstractmethod
    def parse(self, file_path: str) -> str:
        """
        解析文件内容

        Args:
            file_path: 文件路径

        Returns:
            文本内容
        """
        pass

    @staticmethod
    def get_parser(file_path: str) -> 'FileParser':
        """
        根据文件扩展名获取对应的解析器

        Args:
            file_path: 文件路径

        Returns:
            对应的解析器实例
        """
        ext = Path(file_path).suffix.lower()

        parsers = {
            '.txt': TxtParser,
            '.pdf': PdfParser,
            '.docx': DocxParser,
            '.epub': EpubParser,
            '.html': HtmlParser,
            '.htm': HtmlParser,
            '.md': TxtParser,  # Markdown作为纯文本处理
        }

        parser_class = parsers.get(ext)
        if parser_class is None:
            raise ValueError(f"不支持的文件格式: {ext}")

        return parser_class()

    @staticmethod
    def get_supported_formats() -> list:
        """
        获取支持的文件格式列表

        Returns:
            格式列表
        """
        return ['.txt', '.pdf', '.docx', '.epub', '.html', '.htm', '.md']

    @staticmethod
    def get_file_filter() -> str:
        """
        获取文件对话框过滤器

        Returns:
            过滤器字符串
        """
        return (
            "所有支持的格式 (*.txt *.pdf *.docx *.epub *.html *.htm *.md);;"
            "文本文件 (*.txt *.md);;"
            "PDF文件 (*.pdf);;"
            "Word文档 (*.docx);;"
            "电子书 (*.epub);;"
            "网页文件 (*.html *.htm);;"
            "所有文件 (*.*)"
        )


class TxtParser(FileParser):
    """TXT文件解析器"""

    def parse(self, file_path: str) -> str:
        """解析TXT文件"""
        # 检测文件编码
        encoding = self._detect_encoding(file_path)

        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
        except UnicodeDecodeError:
            # 如果检测的编码失败，尝试常见编码
            for enc in ['utf-8', 'gbk', 'gb2312', 'utf-16', 'latin-1']:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("无法识别文件编码")

        # 清理文本
        content = self._clean_text(content)
        return content

    def _detect_encoding(self, file_path: str) -> str:
        """检测文件编码"""
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)  # 读取前10KB用于检测

        result = chardet.detect(raw_data)
        encoding = result.get('encoding', 'utf-8')

        # 处理一些常见的编码别名
        encoding_map = {
            'gb2312': 'gbk',
            'ascii': 'utf-8',
        }

        return encoding_map.get(encoding.lower(), encoding) if encoding else 'utf-8'

    def _clean_text(self, text: str) -> str:
        """清理文本，保留换行符"""
        # 统一换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # 将多个连续换行替换为单个换行
        text = re.sub(r'\n+', '\n', text)
        return text.strip()


class PdfParser(FileParser):
    """PDF文件解析器"""

    def parse(self, file_path: str) -> str:
        """解析PDF文件"""
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            raise ImportError("请安装PyPDF2: pip install PyPDF2")

        reader = PdfReader(file_path)
        text_parts = []

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

        content = '\n'.join(text_parts)

        # 清理文本
        content = self._clean_text(content)
        return content

    def _clean_text(self, text: str) -> str:
        """清理PDF提取的文本"""
        # 统一换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # 将多个连续换行替换为单个换行
        text = re.sub(r'\n+', '\n', text)
        return text.strip()


class DocxParser(FileParser):
    """DOCX文件解析器"""

    def parse(self, file_path: str) -> str:
        """解析DOCX文件"""
        try:
            from docx import Document
        except ImportError:
            raise ImportError("请安装python-docx: pip install python-docx")

        doc = Document(file_path)
        text_parts = []

        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text.strip())

        content = '\n'.join(text_parts)
        return content


class EpubParser(FileParser):
    """EPUB文件解析器"""

    def parse(self, file_path: str) -> str:
        """解析EPUB文件"""
        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("请安装ebooklib和beautifulsoup4: pip install EbookLib beautifulsoup4")

        book = epub.read_epub(file_path)
        text_parts = []

        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                content = item.get_content().decode('utf-8', errors='ignore')
                soup = BeautifulSoup(content, 'lxml')

                # 移除脚本和样式
                for script in soup(["script", "style"]):
                    script.decompose()

                text = soup.get_text(separator=' ')
                if text.strip():
                    text_parts.append(text.strip())

        content = '\n'.join(text_parts)

        # 清理文本
        content = self._clean_text(content)
        return content

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 统一换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # 将多个连续换行替换为单个换行
        text = re.sub(r'\n+', '\n', text)
        return text.strip()


class HtmlParser(FileParser):
    """HTML文件解析器"""

    def parse(self, file_path: str) -> str:
        """解析HTML文件"""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("请安装beautifulsoup4: pip install beautifulsoup4")

        # 检测编码
        encoding = self._detect_encoding(file_path)

        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
            content = f.read()

        soup = BeautifulSoup(content, 'lxml')

        # 移除脚本和样式
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text(separator='\n')

        # 清理文本
        # 统一换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # 将多个连续换行替换为单个换行
        text = re.sub(r'\n+', '\n', text)
        text = text.strip()

        return text

    def _detect_encoding(self, file_path: str) -> str:
        """检测文件编码"""
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)

        result = chardet.detect(raw_data)
        return result.get('encoding', 'utf-8') or 'utf-8'


def parse_file(file_path: str) -> Tuple[str, str]:
    """
    解析文件的便捷函数

    Args:
        file_path: 文件路径

    Returns:
        (文件名, 文本内容)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    parser = FileParser.get_parser(file_path)
    content = parser.parse(file_path)
    filename = os.path.basename(file_path)

    return filename, content
