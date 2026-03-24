"""
便携版打包脚本 - 生成单文件EXE
1. 使用PyInstaller打包成单文件模式 (--onefile)
2. 包含必要的资源文件和JRE环境
3. 自动同步所有翻译文件
"""
import os
import sys
import subprocess
import shutil
import time

# 配置
APP_NAME = "CAJ转换器"
from core.constants import CURRENT_VERSION as VERSION
MAIN_SCRIPT = "main.py"
ICON_FILE = "CAJ转换器.ico"
LOGO_FILE = "鲲穹01.ico"

def clean_old_builds():
    """清理旧的构建目录"""
    print("清理旧的构建目录...")
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                print(f"  已删除: {folder}")
            except Exception as e:
                print(f"  无法删除 {folder}: {e}")
    
    spec_file = f"{APP_NAME}.spec"
    if os.path.exists(spec_file):
        try:
            os.remove(spec_file)
            print(f"  已删除: {spec_file}")
        except:
            pass

def build_portable():
    """开始打包"""
    print(f"\n开始打包 {APP_NAME} 便携版...")
    
    # 检查必要文件
    required_files = [MAIN_SCRIPT, ICON_FILE, LOGO_FILE, "locales", "lib"]
    for f in required_files:
        if not os.path.exists(f):
            print(f"❌ 缺失必要文件或目录: {f}")
            return False
    
    # 构建 PyInstaller 命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onefile",        # 单文件模式
        "--windowed",       # 无控制台
        "--clean",          # 清理缓存
        "--noconfirm",      # 不确认覆盖
        f"--icon={ICON_FILE}",
        
        # 添加数据文件
        f"--add-data=locales;locales",
        f"--add-data=lib/caj2pdf;lib/caj2pdf",
        f"--add-data={ICON_FILE};.",
        f"--add-data={LOGO_FILE};.",
        
        # 隐藏导入 - 确保所有动态加载的库都被包含
        "--hidden-import=PyQt6",
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=PyPDF2",
        "--hidden-import=pdf2docx",
        "--hidden-import=PIL",
        "--hidden-import=PIL.Image",
        "--hidden-import=fitz",
        "--hidden-import=pymupdf",
        "--hidden-import=docx",
        "--hidden-import=reportlab",
        "--hidden-import=requests",
        
        # 排除非必要的重型依赖，避免误收集导致构建膨胀或耗时
        "--exclude-module=torch",
        "--exclude-module=tensorflow",
        "--exclude-module=scipy",
        "--exclude-module=matplotlib",
        "--exclude-module=pandas",
        "--exclude-module=numba",
        "--exclude-module=onnxruntime",
        "--exclude-module=tensorboard",
        
        MAIN_SCRIPT
    ]
    
    print("\n执行 PyInstaller 命令:")
    print(" ".join(cmd))
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n✅ 打包成功！EXE文件位于 dist/{APP_NAME}.exe")
        
        # 重命名以区分版本
        portable_name = f"{APP_NAME}_v{VERSION}_便携版.exe"
        old_path = os.path.join("dist", f"{APP_NAME}.exe")
        new_path = os.path.join("dist", portable_name)
        
        if os.path.exists(old_path):
            if os.path.exists(new_path):
                os.remove(new_path)
            os.rename(old_path, new_path)
            print(f"已重命名为: {portable_name}")
            
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 打包失败: {e}")
        return False

if __name__ == "__main__":
    start_time = time.time()
    
    # 确保在正确的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    clean_old_builds()
    if build_portable():
        duration = time.time() - start_time
        print(f"\n总耗时: {duration:.1f} 秒")
    else:
        sys.exit(1)
