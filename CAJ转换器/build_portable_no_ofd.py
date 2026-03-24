import os
import sys
import subprocess
import shutil

# 配置
APP_NAME = "CAJ转换器"
VERSION = "1.0.2"
APP_DIR = os.path.dirname(os.path.abspath(__file__))

def clean_build():
    """清理构建目录"""
    print("清理构建目录...")
    dirs_to_clean = [os.path.join(APP_DIR, 'build'), os.path.join(APP_DIR, 'dist')]
    for d in dirs_to_clean:
        if os.path.exists(d):
            try:
                shutil.rmtree(d)
                print(f"  已删除: {d}")
            except Exception as e:
                print(f"  无法删除 {d}: {e}")

def build_with_pyinstaller():
    """使用PyInstaller打包(单文件模式)"""
    print("\n使用PyInstaller打包(单文件模式)...")
    
    # 查找图标
    icon_path = os.path.join(os.path.dirname(APP_DIR), f"{APP_NAME}.ico")
    if not os.path.exists(icon_path):
        icon_path = os.path.join(APP_DIR, f"{APP_NAME}.ico")
        
    kq_icon = os.path.join(os.path.dirname(APP_DIR), "鲲穹01.ico")
    if not os.path.exists(kq_icon):
        kq_icon = os.path.join(APP_DIR, "鲲穹01.ico")

    # PyInstaller命令
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name', APP_NAME,
        '--windowed',  # 无控制台窗口
        '--onefile',   # 单文件模式
        '--icon', icon_path,
        '--noconfirm',
        '--clean',
        # 添加数据文件
        f'--add-data={icon_path};.',
        f'--add-data={kq_icon};.',
        '--add-data=lib/caj2pdf;lib/caj2pdf',
        '--add-data=locales;locales',
        # 排除大型库 (这些库不应该被自动包含，但显式排除以防万一)
        '--exclude-module=torch',
        '--exclude-module=torchvision',
        '--exclude-module=torchaudio',
        '--exclude-module=pandas',
        '--exclude-module=numpy',
        '--exclude-module=scipy',
        '--exclude-module=matplotlib',
        '--exclude-module=cv2',
        '--exclude-module=notebook',
        '--exclude-module=jedi',
        # 隐藏导入 - 核心库
        '--hidden-import=PyQt6',
        '--hidden-import=PyQt6.QtWidgets',
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtGui',
        # 隐藏导入 - PDF/文档处理
        '--hidden-import=PyPDF2',
        '--hidden-import=pdf2docx',
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image',
        '--hidden-import=fitz',
        '--hidden-import=pymupdf',
        '--hidden-import=docx',
        '--hidden-import=reportlab',
        # 收集必要子模块
        '--collect-all=PyQt6',
        '--collect-all=fitz',
        '--collect-all=docx',
        '--collect-all=reportlab',
        'main.py'
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    # 使用 Popen 以便实时查看输出
    process = subprocess.Popen(
        cmd,
        cwd=APP_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    for line in process.stdout:
        print(line, end='')
        
    process.wait()
    
    if process.returncode != 0:
        print("\nPyInstaller打包失败!")
        return False
    
    print("\nPyInstaller打包完成!")
    return True

def main():
    print("=" * 60)
    print(f"  {APP_NAME} v{VERSION} 便携版(单文件)打包脚本")
    print("=" * 60)
    
    # 1. 清理
    clean_build()
    
    # 2. PyInstaller打包
    if not build_with_pyinstaller():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("打包完成!")
    print(f"程序位置: CAJ转换器/dist/{APP_NAME}.exe")
    print("=" * 60)

if __name__ == '__main__':
    main()
