"""
MiniRead - 快捷键管理模块
实现全局快捷键支持
"""

import threading
from typing import Callable, Dict, Optional

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("警告: keyboard模块未安装，全局快捷键功能不可用")


class HotkeyManager:
    """快捷键管理器"""

    def __init__(self):
        self._hotkeys: Dict[str, str] = {}  # action -> hotkey
        self._callbacks: Dict[str, Callable] = {}  # action -> callback
        self._registered: Dict[str, bool] = {}  # action -> is_registered
        self._enabled = True

    def register(self, action: str, hotkey: str, callback: Callable) -> bool:
        """
        注册快捷键

        Args:
            action: 动作名称
            hotkey: 快捷键组合，如 "ctrl+shift+r"
            callback: 回调函数

        Returns:
            是否注册成功
        """
        if not KEYBOARD_AVAILABLE:
            return False

        # 如果已注册，先取消
        if action in self._registered and self._registered[action]:
            self.unregister(action)

        try:
            keyboard.add_hotkey(hotkey, lambda: self._on_hotkey(action))
            self._hotkeys[action] = hotkey
            self._callbacks[action] = callback
            self._registered[action] = True
            return True
        except Exception as e:
            print(f"注册快捷键失败 [{action}]: {e}")
            return False

    def unregister(self, action: str) -> bool:
        """
        取消注册快捷键

        Args:
            action: 动作名称

        Returns:
            是否取消成功
        """
        if not KEYBOARD_AVAILABLE:
            return False

        if action not in self._hotkeys:
            return False

        try:
            keyboard.remove_hotkey(self._hotkeys[action])
            self._registered[action] = False
            return True
        except Exception as e:
            print(f"取消快捷键失败 [{action}]: {e}")
            return False

    def unregister_all(self) -> None:
        """取消所有快捷键"""
        for action in list(self._hotkeys.keys()):
            self.unregister(action)

    def _on_hotkey(self, action: str) -> None:
        """快捷键触发回调"""
        if not self._enabled:
            return

        if action in self._callbacks:
            # 在主线程中执行回调
            callback = self._callbacks[action]
            try:
                callback()
            except Exception as e:
                print(f"快捷键回调执行失败 [{action}]: {e}")

    def set_enabled(self, enabled: bool) -> None:
        """设置是否启用快捷键"""
        self._enabled = enabled

    def is_enabled(self) -> bool:
        """获取是否启用快捷键"""
        return self._enabled

    def get_hotkey(self, action: str) -> Optional[str]:
        """获取动作对应的快捷键"""
        return self._hotkeys.get(action)

    def update_hotkey(self, action: str, new_hotkey: str) -> bool:
        """
        更新快捷键

        Args:
            action: 动作名称
            new_hotkey: 新的快捷键组合

        Returns:
            是否更新成功
        """
        if action not in self._callbacks:
            return False

        callback = self._callbacks[action]
        return self.register(action, new_hotkey, callback)


# 全局快捷键管理器实例
_hotkey_manager: Optional[HotkeyManager] = None


def get_hotkey_manager() -> HotkeyManager:
    """获取全局快捷键管理器"""
    global _hotkey_manager
    if _hotkey_manager is None:
        _hotkey_manager = HotkeyManager()
    return _hotkey_manager
