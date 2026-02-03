"""
MiniRead - 常量定义模块
集中管理所有常量，避免魔法数字分散在代码中
"""

# 窗口相关
WINDOW_HIDE_TIMEOUT = 120000  # 窗口自动隐藏时间（毫秒）- 2分钟
WINDOW_HIDE_TIMEOUT_FULLSCREEN = 300000  # 全屏模式隐藏时间（毫秒）- 5分钟
CONFIG_SAVE_DELAY = 2000  # 配置保存延迟（毫秒）- 2秒
AUTO_SAVE_INTERVAL = 30000  # 自动保存阅读位置间隔（毫秒）- 30秒
EDGE_MARGIN = 15  # 边缘检测距离（像素）
POSITION_SAVE_INTERVAL = 10  # 每翻页N次保存一次阅读位置

# 字体相关
MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 72
DEFAULT_FONT_FAMILY = "Microsoft YaHei"
DEFAULT_FONT_SIZE = 16

# 透明度相关
MIN_OPACITY = 0.1
MAX_OPACITY = 1.0
DEFAULT_OPACITY = 0.5

# 窗口默认尺寸
DEFAULT_WINDOW_WIDTH = 800
DEFAULT_WINDOW_HEIGHT = 60
DEFAULT_WINDOW_X = 100
DEFAULT_WINDOW_Y = 100

# 缓存相关
FILE_PARSE_CACHE_SIZE = 10  # 文件解析缓存最大数量
FILE_PARSE_CACHE_TTL = 3600  # 缓存过期时间（秒）
LIBRARY_MAX_DISPLAY = 50  # 阅读目录最大显示数量

# 摇动检测相关
SHAKE_TIME_WINDOW = 1000  # 摇动检测时间窗口（毫秒）
SHAKE_THRESHOLD = 30  # 摇动检测阈值（像素）
SHAKE_MIN_POINTS = 5  # 最小检测点数
SHAKE_COUNT_THRESHOLD = 3  # 摇动次数阈值

# 颜色相关
DEFAULT_BG_COLOR = "#2D2D2D"
DEFAULT_TEXT_COLOR = "#FFFFFF"
DEFAULT_BORDER_RADIUS = 8

# 文件相关
MAX_RECENT_FILES = 10  # 最近文件最大数量
MAX_TRAY_RECENT_FILES = 3  # 托盘菜单最近文件数量

# 支持的文件格式
SUPPORTED_FORMATS = ['.txt', '.pdf', '.docx', '.epub', '.html', '.htm', '.md']
