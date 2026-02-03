"""
将 PNG 图片转换为 ICO 格式
用于 PyInstaller 打包时设置应用图标
"""

from PIL import Image
import os

def png_to_ico(png_path, ico_path):
    """
    将 PNG 图片转换为 ICO 格式

    Args:
        png_path: PNG 图片路径
        ico_path: 输出的 ICO 文件路径
    """
    try:
        # 打开 PNG 图片
        img = Image.open(png_path)

        # 转换为 RGBA 模式（如果不是的话）
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # 创建多个尺寸的图标（Windows 标准尺寸）
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

        # 保存为 ICO 格式
        img.save(ico_path, format='ICO', sizes=icon_sizes)

        print(f"✅ 成功将 {png_path} 转换为 {ico_path}")
        print(f"   包含尺寸: {', '.join([f'{w}x{h}' for w, h in icon_sizes])}")

        return True

    except Exception as e:
        print(f"❌ 转换失败: {e}")
        return False

if __name__ == "__main__":
    # 输入和输出路径
    png_file = "mini阅读软件logo.png"
    ico_file = "icon.ico"

    # 检查文件是否存在
    if not os.path.exists(png_file):
        print(f"❌ 错误: 找不到文件 {png_file}")
        exit(1)

    # 执行转换
    if png_to_ico(png_file, ico_file):
        print(f"\n📁 ICO 文件已保存到: {os.path.abspath(ico_file)}")
    else:
        exit(1)
