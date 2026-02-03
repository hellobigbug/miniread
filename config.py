"""
MiniRead - 配置管理模块
负责保存和加载用户配置
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """配置管理器，负责保存和加载用户配置"""

    # 默认配置
    DEFAULT_CONFIG = {
        # 窗口设置
        "window": {
            "x": 100,
            "y": 100,
            "width": 800,
            "height": 60,
            "opacity": 0.95,
            "always_on_top": True
        },
        # 字体设置
        "font": {
            "family": "Microsoft YaHei",
            "size": 16,
            "bold": False,
            "italic": False,
            "color": "#FFFFFF"
        },
        # 滚动设置
        "scroll": {
            "speed": 50,  # 像素/秒
            "direction": "left",  # left 或 right
            "auto_start": False,
            "pause_on_hover": True
        },
        # 显示设置
        "display": {
            "background_color": "#2D2D2D",
            "text_color": "#FFFFFF",
            "border_radius": 8,
            "show_controls": True
        },
        # 快捷键设置
        "hotkeys": {
            "toggle_visibility": "ctrl+shift+r",
            "toggle_scroll": "ctrl+shift+space",
            "increase_font": "ctrl+shift+up",
            "decrease_font": "ctrl+shift+down",
            "increase_speed": "ctrl+shift+right",
            "decrease_speed": "ctrl+shift+left",
            "open_file": "ctrl+shift+o"
        },
        # 最近文件
        "recent_files": [],
        # 最后阅读位置
        "last_position": {
            "file": "",
            "char_index": 0
        },
        # 阅读历史（保存每个文件的进度）
        "reading_history": {}
    }

    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_dir: 配置文件目录，默认为用户目录下的.miniread
        """
        if config_dir is None:
            config_dir = os.path.join(os.path.expanduser("~"), ".miniread")

        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.json"
        self.config: Dict[str, Any] = {}

        # 确保配置目录存在
        self._ensure_config_dir()

        # 加载配置
        self.load()

    def _ensure_config_dir(self) -> None:
        """确保配置目录存在"""
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        """
        加载配置文件

        Returns:
            配置字典
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                # 合并默认配置和加载的配置
                self.config = self._merge_config(self.DEFAULT_CONFIG, loaded_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"加载配置文件失败: {e}")
                self.config = self.DEFAULT_CONFIG.copy()
        else:
            self.config = self.DEFAULT_CONFIG.copy()
            self.save()  # 创建默认配置文件

        return self.config

    def save(self) -> bool:
        """
        保存配置到文件

        Returns:
            是否保存成功
        """
        try:
            self._ensure_config_dir()
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            print(f"保存配置文件失败: {e}")
            return False

    def _merge_config(self, default: Dict, loaded: Dict) -> Dict:
        """
        递归合并配置，确保所有默认键都存在

        Args:
            default: 默认配置
            loaded: 加载的配置

        Returns:
            合并后的配置
        """
        result = default.copy()
        for key, value in loaded.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._merge_config(result[key], value)
                else:
                    result[key] = value
        return result

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值，支持点号分隔的路径

        Args:
            key_path: 配置键路径，如 "font.size"
            default: 默认值

        Returns:
            配置值
        """
        keys = key_path.split('.')
        value = self.config

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key_path: str, value: Any, auto_save: bool = True) -> None:
        """
        设置配置值，支持点号分隔的路径

        Args:
            key_path: 配置键路径，如 "font.size"
            value: 配置值
            auto_save: 是否自动保存
        """
        keys = key_path.split('.')
        config = self.config

        # 导航到最后一个键的父级
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        # 设置值
        config[keys[-1]] = value

        if auto_save:
            self.save()

    def add_recent_file(self, file_path: str, max_files: int = 10) -> None:
        """
        添加最近打开的文件

        Args:
            file_path: 文件路径
            max_files: 最大保存数量
        """
        recent = self.config.get("recent_files", [])

        # 如果文件已存在，移到最前面
        if file_path in recent:
            recent.remove(file_path)

        recent.insert(0, file_path)

        # 限制数量
        self.config["recent_files"] = recent[:max_files]
        self.save()

    def get_recent_files(self) -> list:
        """
        获取最近打开的文件列表

        Returns:
            文件路径列表
        """
        return self.config.get("recent_files", [])

    def save_reading_position(self, file_path: str, char_index: int) -> None:
        """
        保存阅读位置

        Args:
            file_path: 文件路径
            char_index: 字符索引
        """
        # 更新最后一次阅读位置
        self.config["last_position"] = {
            "file": file_path,
            "char_index": char_index
        }

        # 更新阅读历史
        history = self.config.get("reading_history", {})
        history[file_path] = {
            "char_index": char_index,
            "last_read": time.time()
        }
        self.config["reading_history"] = history

        self.save()

    def get_reading_position(self, file_path: str) -> int:
        """
        获取阅读位置

        Args:
            file_path: 文件路径

        Returns:
            字符索引，如果没有记录返回0
        """
        # 先从阅读历史中查找
        history = self.config.get("reading_history", {})
        if file_path in history:
            return history[file_path].get("char_index", 0)

        # 兼容旧配置
        last_pos = self.config.get("last_position", {})
        if last_pos.get("file") == file_path:
            return last_pos.get("char_index", 0)
        return 0

    def get_reading_history(self) -> Dict[str, Dict]:
        """获取阅读历史"""
        return self.config.get("reading_history", {})

    def remove_reading_history(self, file_path: str) -> None:
        """删除指定文件的阅读记录"""
        history = self.config.get("reading_history", {})
        if file_path in history:
            del history[file_path]
            self.config["reading_history"] = history
            self.save()

    def reset_to_default(self) -> None:
        """重置为默认配置"""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save()


# 全局配置实例
_config_instance: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """
    获取全局配置实例

    Returns:
        ConfigManager实例
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance
