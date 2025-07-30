"""
批量图片尺寸调整工具
主程序入口 - PySide6版本
"""
import sys
import os
import multiprocessing

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui_pyside6 import main


if __name__ == "__main__":
    # 支持PyInstaller打包后的多进程功能
    multiprocessing.freeze_support()
    sys.exit(main())