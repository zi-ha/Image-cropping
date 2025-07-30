"""
图片尺寸调整工具 - 优化版EXE打包脚本
使用PyInstaller打包成体积最小的单文件可执行程序
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def clean_build_folder():
    """
    清理build文件夹
    """
    build_path = Path("build")
    if not build_path.exists():
        print("✅ build文件夹不存在，无需清理")
        return
    
    print("🧹 清理build文件夹...")
    
    try:
        shutil.rmtree(build_path)
        print("✅ 已删除build文件夹")
    except Exception as e:
        print(f"⚠️  无法删除build文件夹: {e}")


def check_upx():
    """检查UPX压缩工具是否可用"""
    try:
        subprocess.run(['upx', '--version'], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  UPX压缩工具未找到，将跳过UPX压缩")
        print("💡 提示：安装UPX可进一步减小文件体积")
        return False

def check_virtual_env():
    """检查是否在虚拟环境中运行"""
    in_venv = (
        hasattr(sys, 'real_prefix') or  # virtualenv
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or  # venv
        'VIRTUAL_ENV' in os.environ  # 环境变量
    )
    
    if not in_venv:
        print("⚠️  警告：未检测到虚拟环境！")
        print("💡 强烈建议在虚拟环境中打包以获得最小体积：")
        print("   1. python -m venv venv")
        print("   2. venv\\Scripts\\activate  (Windows)")
        print("   3. pip install -r requirements.txt")
        print("   4. 重新运行此脚本")
        
        choice = input("\n是否继续打包？(y/N): ").strip().lower()
        if choice != 'y':
            print("👋 建议设置虚拟环境后再打包")
            return False
    else:
        print("✅ 检测到虚拟环境，这有助于减小EXE体积")
    
    return True

def build_exe_optimized(auto_clean=True):
    """构建体积优化的EXE文件"""
    print("🚀 开始打包图片尺寸调整工具（体积优化版）...")
    
    # 检查虚拟环境
    if not check_virtual_env():
        return False
    
    # 检查UPX可用性
    use_upx = check_upx()
    
    # 优化的PyInstaller打包命令
    cmd = [
        'pyinstaller',
        '--onefile',                    # 打包成单个EXE文件
        '--windowed',                   # 无控制台窗口（GUI应用）
        '--name=图片尺寸调整工具',        # 指定EXE文件名
        '--icon=logo.ico',              # 使用logo.ico作为图标
        '--clean',                      # 清理临时文件
        '--strip',                      # 去除调试符号
        '--optimize=2',                 # Python字节码优化级别
        '--noupx' if not use_upx else '--upx-dir=.',  # UPX压缩控制
        
        # 体积优化选项 - 排除不需要的标准库和第三方库
        '--exclude-module=tkinter',     # 排除tkinter
        '--exclude-module=matplotlib',  # 排除matplotlib
        '--exclude-module=numpy',       # 排除numpy（如果不需要）
        '--exclude-module=scipy',       # 排除scipy
        '--exclude-module=pandas',      # 排除pandas
        '--exclude-module=IPython',     # 排除IPython
        '--exclude-module=jupyter',     # 排除jupyter
        '--exclude-module=notebook',    # 排除notebook
        '--exclude-module=PyQt5',       # 排除PyQt5
        '--exclude-module=PyQt6',       # 排除PyQt6
        '--exclude-module=wx',          # 排除wxPython
        '--exclude-module=email',       # 排除email模块
        '--exclude-module=http',        # 排除http模块
        '--exclude-module=xml',         # 排除xml模块
        '--exclude-module=unittest',    # 排除unittest
        '--exclude-module=doctest',     # 排除doctest
        '--exclude-module=pdb',         # 排除调试器
        '--exclude-module=calendar',    # 排除日历模块
        '--exclude-module=difflib',     # 排除差异比较
        '--exclude-module=sqlite3',     # 排除SQLite（如果不需要）
        '--exclude-module=csv',         # 排除CSV模块（如果不需要）
        '--exclude-module=json',        # 排除JSON模块（如果不需要）
        '--exclude-module=urllib',      # 排除urllib
        '--exclude-module=urllib3',     # 排除urllib3
        '--exclude-module=requests',    # 排除requests（如果不需要）
        
        # 精确导入控制
        '--hidden-import=PySide6.QtCore',
        '--hidden-import=PySide6.QtWidgets', 
        '--hidden-import=PySide6.QtGui',
        '--hidden-import=PIL.Image',
        '--hidden-import=PIL.ImageOps',
        '--hidden-import=PIL._imaging',
        
        # 排除不需要的PySide6模块
        '--exclude-module=PySide6.QtNetwork',
        '--exclude-module=PySide6.QtWebEngine',
        '--exclude-module=PySide6.QtWebEngineWidgets',
        '--exclude-module=PySide6.QtMultimedia',
        '--exclude-module=PySide6.QtOpenGL',
        '--exclude-module=PySide6.Qt3D',
        '--exclude-module=PySide6.QtCharts',
        '--exclude-module=PySide6.QtDataVisualization',
        
        'main.py'                       # 主程序文件
    ]
    
    try:
        # 执行打包命令
        print("📦 正在执行打包...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 打包成功！")
        
        # 分析文件大小
        exe_path = "dist/图片尺寸调整工具.exe"
        if os.path.exists(exe_path):
            size_bytes = os.path.getsize(exe_path)
            size_mb = size_bytes / (1024 * 1024)
            print(f"📁 EXE文件位置: {exe_path}")
            print(f"📊 文件大小: {size_mb:.1f} MB ({size_bytes:,} 字节)")
            
            # 如果启用了UPX，显示压缩效果
            if use_upx:
                print("🗜️  已应用UPX压缩")
            
            # 体积评估
            if size_mb < 50:
                print("🎉 体积优化效果：优秀")
            elif size_mb < 100:
                print("👍 体积优化效果：良好") 
            else:
                print("⚠️  体积较大，建议检查依赖")
        
        # 自动清理build文件夹
        if auto_clean:
            clean_build_folder()
                
    except subprocess.CalledProcessError as e:
        print("❌ 打包失败！")
        print(f"错误信息: {e.stderr}")
        return False
    
    except FileNotFoundError:
        print("❌ PyInstaller 未安装！")
        print("请先安装: pip install pyinstaller")
        return False
    
    return True

def build_exe_minimal(auto_clean=True):
    """构建极简版EXE（最小体积）"""
    print("🚀 开始打包极简版（最小体积）...")
    
    # 检查虚拟环境
    if not check_virtual_env():
        return False
    
    # 极简打包命令
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name=图片尺寸调整工具_极简版',
        '--icon=logo.ico',              # 使用logo.ico作为图标
        '--clean',
        '--strip',
        '--optimize=2',
        '--noupx',  # 极简版不使用UPX，避免兼容性问题
        
        # 排除所有可能的模块
        '--exclude-module=tkinter',
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=scipy',
        '--exclude-module=pandas',
        '--exclude-module=IPython',
        '--exclude-module=jupyter',
        '--exclude-module=PyQt5',
        '--exclude-module=PyQt6',
        '--exclude-module=wx',
        '--exclude-module=email',
        '--exclude-module=http',
        '--exclude-module=urllib3',
        '--exclude-module=xml',
        '--exclude-module=unittest',
        '--exclude-module=doctest',
        '--exclude-module=pdb',
        '--exclude-module=calendar',
        '--exclude-module=difflib',
        
        # 只包含必需的模块
        '--hidden-import=PySide6.QtCore',
        '--hidden-import=PySide6.QtWidgets', 
        '--hidden-import=PySide6.QtGui',
        '--hidden-import=PIL.Image',
        '--hidden-import=PIL.ImageOps',
        
        'main.py'
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 极简版打包成功！")
        
        exe_path = "dist/图片尺寸调整工具_极简版.exe"
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"📁 极简版EXE: {exe_path}")
            print(f"📊 文件大小: {size_mb:.1f} MB")
        
        # 自动清理build文件夹
        if auto_clean:
            clean_build_folder()
            
    except subprocess.CalledProcessError as e:
        print("❌ 极简版打包失败！")
        print(f"错误信息: {e.stderr}")
        return False
    
    return True

def build_exe_ultra_minimal(auto_clean=True):
    """构建超级极简版EXE（极限最小体积）"""
    print("🚀 开始打包超级极简版（极限最小体积）...")
    
    # 检查虚拟环境
    if not check_virtual_env():
        return False
    
    # 超级极简打包命令
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name=图片尺寸调整工具_超级极简版',
        '--icon=logo.ico',
        '--clean',
        '--strip',
        '--optimize=2',
        '--noupx',  # 超级极简版不使用UPX
        '--noconfirm',  # 不询问覆盖
        
        # 排除所有可能的模块（更激进的排除）
        '--exclude-module=tkinter',
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=scipy',
        '--exclude-module=pandas',
        '--exclude-module=IPython',
        '--exclude-module=jupyter',
        '--exclude-module=PyQt5',
        '--exclude-module=PyQt6',
        '--exclude-module=wx',
        '--exclude-module=email',
        '--exclude-module=http',
        '--exclude-module=urllib',
        '--exclude-module=urllib3',
        '--exclude-module=xml',
        '--exclude-module=unittest',
        '--exclude-module=doctest',
        '--exclude-module=pdb',
        '--exclude-module=calendar',
        '--exclude-module=difflib',
        '--exclude-module=sqlite3',
        '--exclude-module=csv',
        '--exclude-module=json',
        '--exclude-module=requests',
        # '--exclude-module=logging',  # 保留logging，可能被PySide6使用
        '--exclude-module=multiprocessing',
        '--exclude-module=threading',
        '--exclude-module=concurrent',
        '--exclude-module=asyncio',
        '--exclude-module=socket',
        '--exclude-module=ssl',
        # '--exclude-module=hashlib',  # 保留hashlib，可能被加密相关功能使用
        '--exclude-module=hmac',
        '--exclude-module=base64',
        '--exclude-module=binascii',
        '--exclude-module=pickle',
        '--exclude-module=shelve',
        '--exclude-module=dbm',
        '--exclude-module=gzip',
        # '--exclude-module=zipfile',  # PyInstaller需要zipfile，不能排除
        '--exclude-module=tarfile',
        '--exclude-module=bz2',
        '--exclude-module=lzma',
        
        # 只包含绝对必需的模块
        '--hidden-import=PySide6.QtCore',
        '--hidden-import=PySide6.QtWidgets', 
        '--hidden-import=PySide6.QtGui',
        '--hidden-import=PIL.Image',
        '--hidden-import=PIL.ImageOps',
        '--hidden-import=PIL._imaging',
        
        # 更激进的PySide6模块排除
        '--exclude-module=PySide6.QtNetwork',
        '--exclude-module=PySide6.QtWebEngine',
        '--exclude-module=PySide6.QtWebEngineWidgets',
        '--exclude-module=PySide6.QtMultimedia',
        '--exclude-module=PySide6.QtOpenGL',
        '--exclude-module=PySide6.Qt3D',
        '--exclude-module=PySide6.QtCharts',
        '--exclude-module=PySide6.QtDataVisualization',
        '--exclude-module=PySide6.QtSql',
        '--exclude-module=PySide6.QtTest',
        '--exclude-module=PySide6.QtXml',
        '--exclude-module=PySide6.QtHelp',
        '--exclude-module=PySide6.QtPrintSupport',
        '--exclude-module=PySide6.QtSvg',
        
        'main.py'
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 超级极简版打包成功！")
        
        exe_path = "dist/图片尺寸调整工具_超级极简版.exe"
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"📁 超级极简版EXE: {exe_path}")
            print(f"📊 文件大小: {size_mb:.1f} MB")
            
            if size_mb < 30:
                print("🎉 体积优化效果：极佳！")
            elif size_mb < 50:
                print("👍 体积优化效果：优秀")
            else:
                print("⚠️  体积仍然较大，可能需要进一步优化")
        
        # 自动清理build文件夹
        if auto_clean:
            clean_build_folder()
            
    except subprocess.CalledProcessError as e:
        print("❌ 超级极简版打包失败！")
        print(f"错误信息: {e.stderr}")
        return False
    
    return True

def analyze_dependencies():
    """分析项目依赖，帮助优化体积"""
    print("\n🔍 分析项目依赖...")
    
    try:
        # 使用pipreqs分析实际使用的包
        result = subprocess.run(['pipreqs', '.', '--print'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("📋 实际使用的依赖:")
            print(result.stdout)
        else:
            print("⚠️  无法自动分析依赖，请手动检查")
            
    except FileNotFoundError:
        print("💡 建议安装 pipreqs 来分析依赖: pip install pipreqs")
    
    # 检查当前安装的包
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            large_packages = []
            for line in lines[2:]:  # 跳过标题行
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        package = parts[0]
                        # 标记可能影响体积的大包
                        if package.lower() in ['numpy', 'scipy', 'matplotlib', 
                                             'pandas', 'tensorflow', 'torch',
                                             'opencv-python', 'pillow']:
                            large_packages.append(package)
            
            if large_packages:
                print(f"\n📦 检测到可能影响体积的包: {', '.join(large_packages)}")
                print("💡 如果不需要这些包，可以考虑在虚拟环境中只安装必需依赖")
                
    except Exception:
        pass

def clean_build_files():
    """清理构建文件"""
    print("\n🧹 清理构建文件...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['*.spec']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"🗑️  已删除: {dir_name}/")
    
    # 清理spec文件（除了我们的配置文件）
    for file in os.listdir('.'):
        if file.endswith('.spec') and file != 'build.spec':
            os.remove(file)
            print(f"🗑️  已删除: {file}")

def install_dependencies():
    """安装打包依赖"""
    print("📦 检查并安装打包依赖...")
    
    dependencies = ['pyinstaller']
    
    for dep in dependencies:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'show', dep], 
                          check=True, capture_output=True)
            print(f"✅ {dep} 已安装")
        except subprocess.CalledProcessError:
            print(f"📦 安装 {dep}...")
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', dep], 
                              check=True)
                print(f"✅ {dep} 安装成功")
            except subprocess.CalledProcessError:
                print(f"❌ {dep} 安装失败")
                return False
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🎯 图片尺寸调整工具 - 体积优化EXE打包器")
    print("=" * 60)
    
    # 显示菜单
    print("\n📋 请选择打包模式:")
    print("1. 🚀 标准优化版 (推荐)")
    print("2. 📦 极简版 (最小体积)")
    print("3. ⚡ 超级极简版 (极限最小体积)")
    print("4. 🔍 依赖分析")
    print("5. 🧹 清理构建文件")
    print("6. 📊 全部打包并对比")
    print("0. ❌ 退出")
    
    while True:
        try:
            choice = input("\n请输入选项 (0-6): ").strip()
            
            if choice == "0":
                print("👋 再见！")
                sys.exit(0)
                
            elif choice == "1":
                print("\n" + "="*50)
                print("🚀 标准优化版打包")
                print("="*50)
                
                if not install_dependencies():
                    sys.exit(1)
                
                if build_exe_optimized():
                    print("\n🎉 标准优化版打包完成！")
                    print("💡 提示：此版本在体积和兼容性之间取得平衡")
                else:
                    print("\n💥 打包失败")
                break
                
            elif choice == "2":
                print("\n" + "="*50)
                print("📦 极简版打包")
                print("="*50)
                
                if not install_dependencies():
                    sys.exit(1)
                
                if build_exe_minimal():
                    print("\n🎉 极简版打包完成！")
                    print("💡 提示：此版本体积最小，但可能在某些系统上兼容性较差")
                else:
                    print("\n💥 打包失败")
                break
                
            elif choice == "3":
                print("\n" + "="*50)
                print("⚡ 超级极简版打包")
                print("="*50)
                
                if not install_dependencies():
                    sys.exit(1)
                
                if build_exe_ultra_minimal():
                    print("\n🎉 超级极简版打包完成！")
                    print("💡 提示：此版本体积极限最小，但兼容性风险最高")
                else:
                    print("\n💥 打包失败")
                break
                
            elif choice == "4":
                print("\n" + "="*50)
                print("🔍 依赖分析")
                print("="*50)
                analyze_dependencies()
                print("\n✅ 分析完成")
                
            elif choice == "5":
                print("\n" + "="*50)
                print("🧹 清理构建文件")
                print("="*50)
                clean_build_files()
                print("\n✅ 清理完成")
                
            elif choice == "6":
                print("\n" + "="*50)
                print("📊 全部打包并对比")
                print("="*50)
                
                if not install_dependencies():
                    sys.exit(1)
                
                print("\n🔄 开始全部打包...")
                
                # 清理旧文件
                clean_build_files()
                
                # 打包标准版
                print("\n1️⃣ 打包标准优化版...")
                success1 = build_exe_optimized(auto_clean=False)
                
                # 打包极简版
                print("\n2️⃣ 打包极简版...")
                success2 = build_exe_minimal(auto_clean=False)
                
                # 打包超级极简版
                print("\n3️⃣ 打包超级极简版...")
                success3 = build_exe_ultra_minimal(auto_clean=False)
                
                # 对比结果
                if success1 or success2 or success3:
                    print("\n" + "="*50)
                    print("📊 打包结果对比")
                    print("="*50)
                    
                    files = [
                        ("标准优化版", "dist/图片尺寸调整工具.exe"),
                        ("极简版", "dist/图片尺寸调整工具_极简版.exe"),
                        ("超级极简版", "dist/图片尺寸调整工具_超级极简版.exe")
                    ]
                    
                    for name, path in files:
                        if os.path.exists(path):
                            size_mb = os.path.getsize(path) / (1024 * 1024)
                            print(f"📁 {name}: {size_mb:.1f} MB")
                        else:
                            print(f"❌ {name}: 打包失败")
                    
                    print("\n💡 建议:")
                    print("   - 优先选择体积最小且能正常运行的版本")
                    print("   - 超级极简版体积最小，但兼容性风险最高")
                    print("   - 极简版是体积和兼容性的平衡选择")
                    print("   - 标准优化版兼容性最好，适合大多数环境")
                    
                    # 统一清理build文件夹
                    print()
                    clean_build_folder()
                    
                print("\n🎉 全部打包完成！")
                break
                
            else:
                print("❌ 无效选项，请输入 0-6")
                
        except KeyboardInterrupt:
            print("\n\n👋 用户取消操作")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            
    print("\n💡 体积优化小贴士:")
    print("   🔹 使用虚拟环境，只安装必需的依赖包")
    print("   🔹 安装 UPX 工具可进一步压缩体积")
    print("   🔹 避免导入大型库（如 numpy, matplotlib）")
    print("   🔹 定期清理 __pycache__ 和构建文件")