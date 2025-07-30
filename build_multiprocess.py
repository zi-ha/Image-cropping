#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多进程版本打包脚本
专门用于打包支持多进程的图片尺寸调整工具
"""

import os
import sys
import subprocess
import shutil

def clean_build_dirs():
    """清理之前的构建目录"""
    dirs_to_clean = ['build', '__pycache__']
    files_to_clean = []
    
    # 检查dist目录中的文件
    if os.path.exists('dist'):
        for file in os.listdir('dist'):
            if file.endswith('.exe'):
                files_to_clean.append(os.path.join('dist', file))
    
    # 清理目录
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                print(f"清理目录: {dir_name}")
                shutil.rmtree(dir_name)
            except PermissionError:
                print(f"警告: 无法删除目录 {dir_name}，可能有文件正在使用")
    
    # 清理exe文件
    for file_path in files_to_clean:
        try:
            print(f"清理文件: {file_path}")
            os.remove(file_path)
        except PermissionError:
            print(f"警告: 无法删除文件 {file_path}，可能正在运行中")
        except FileNotFoundError:
            pass  # 文件已经不存在

def build_exe():
    """使用PyInstaller构建exe文件"""
    
    # 清理之前的构建
    clean_build_dirs()
    
    # PyInstaller命令
    cmd = [
        'pyinstaller',
        '--onefile',                    # 打包成单个exe文件
        '--windowed',                   # 无控制台窗口
        '--name=图片尺寸调整工具_多进程版',  # 指定exe文件名
        '--icon=logo.ico',              # 图标文件
        '--add-data=README.md;.',       # 包含README文件
        '--hidden-import=multiprocessing',
        '--hidden-import=multiprocessing.spawn',
        '--hidden-import=multiprocessing.pool',
        '--hidden-import=concurrent.futures',
        '--hidden-import=concurrent.futures.process',
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image',
        '--hidden-import=PIL.ImageOps',
        '--hidden-import=PySide6',
        '--hidden-import=PySide6.QtCore',
        '--hidden-import=PySide6.QtWidgets',
        '--hidden-import=PySide6.QtGui',
        '--optimize=0',                 # 不优化，避免多进程问题
        '--noupx',                      # 不使用UPX压缩
        'main.py'
    ]
    
    print("开始打包...")
    print("命令:", ' '.join(cmd))
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("打包成功!")
        print("输出:", result.stdout)
        
        # 检查生成的exe文件
        exe_path = os.path.join('dist', '图片尺寸调整工具_多进程版.exe')
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"生成的exe文件: {exe_path}")
            print(f"文件大小: {size_mb:.1f} MB")
        
    except subprocess.CalledProcessError as e:
        print("打包失败!")
        print("错误:", e.stderr)
        return False
    
    return True

def test_multiprocessing():
    """测试多进程功能是否正常"""
    print("\n测试多进程功能...")
    
    test_code = '''
import multiprocessing as mp
import sys

def test_worker(x):
    return x * x

if __name__ == "__main__":
    mp.freeze_support()
    
    try:
        with mp.Pool(2) as pool:
            results = pool.map(test_worker, [1, 2, 3, 4])
            print(f"多进程测试成功: {results}")
    except Exception as e:
        print(f"多进程测试失败: {e}")
'''
    
    # 写入临时测试文件
    with open('test_mp.py', 'w', encoding='utf-8') as f:
        f.write(test_code)
    
    try:
        result = subprocess.run([sys.executable, 'test_mp.py'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("多进程功能测试通过")
            return True
        else:
            print(f"多进程功能测试失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"测试过程出错: {e}")
        return False
    finally:
        # 清理测试文件
        if os.path.exists('test_mp.py'):
            os.remove('test_mp.py')

def main():
    """主函数"""
    print("=== 图片尺寸调整工具 - 多进程版打包脚本 ===\n")
    
    # 检查依赖
    try:
        import PyInstaller
        print(f"PyInstaller版本: {PyInstaller.__version__}")
    except ImportError:
        print("错误: 未安装PyInstaller")
        print("请运行: pip install pyinstaller")
        return
    
    # 测试多进程功能
    if not test_multiprocessing():
        print("警告: 多进程功能测试失败，但仍将继续打包")
    
    # 开始打包
    if build_exe():
        print("\n=== 打包完成 ===")
        print("生成的文件位于 dist 目录中")
        print("\n使用说明:")
        print("1. 生成的exe文件支持多进程处理")
        print("2. 首次运行可能需要较长时间初始化")
        print("3. 如果遇到问题，请检查Windows防火墙设置")
    else:
        print("\n=== 打包失败 ===")
        print("请检查错误信息并重试")

if __name__ == "__main__":
    main()