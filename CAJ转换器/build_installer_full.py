"""
完整打包脚本 - 生成安装版
1. 使用PyInstaller打包成目录模式
2. 使用Inno Setup生成安装程序
"""
import os
import sys
import subprocess
import shutil

# 配置
APP_NAME = "CAJ转换器"
VERSION = "1.0.0"
INNO_SETUP_PATH = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

def clean_build():
    """清理构建目录"""
    print("清理构建目录...")
    dirs_to_clean = ['build', f'dist/{APP_NAME}']
    for d in dirs_to_clean:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"  已删除: {d}")

def build_with_pyinstaller():
    """使用PyInstaller打包"""
    print("\n使用PyInstaller打包...")
    
    # 检查JRE是否存在
    jre_exists = os.path.exists('jre')
    if jre_exists:
        print("✓ 检测到JRE目录，将打包到安装程序中")
    else:
        print("⚠ 未检测到JRE目录，CAJ转OFD功能需要用户自行安装Java")
        print("  提示：运行 python download_jre.py 可自动下载JRE")
    
    # PyInstaller命令
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name', APP_NAME,
        '--windowed',  # 无控制台窗口
        '--icon', f'{APP_NAME}.ico',
        '--add-data', 'lib;lib',
        '--add-data', '鲲穹01.ico;.',
        '--add-data', f'{APP_NAME}.ico;.',
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
        # 隐藏导入 - Word转PDF（新增）
        '--hidden-import=docx',
        '--hidden-import=docx.document',
        '--hidden-import=docx.oxml',
        '--hidden-import=reportlab',
        '--hidden-import=reportlab.pdfgen',
        '--hidden-import=reportlab.lib',
        '--hidden-import=reportlab.lib.pagesizes',
        '--hidden-import=reportlab.lib.units',
        # 隐藏导入 - 备选方案
        '--hidden-import=comtypes',
        '--hidden-import=comtypes.client',
        # 收集所有子模块
        '--collect-all=PyQt6',
        '--collect-all=fitz',
        '--collect-all=docx',
        '--collect-all=reportlab',
        '--noconfirm',
        '--clean',
        'main.py'
    ]
    
    # 如果JRE存在，添加到打包中
    if jre_exists:
        cmd.insert(-1, '--add-data')
        cmd.insert(-1, 'jre;jre')
    
    print(f"执行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode != 0:
        print("PyInstaller打包失败!")
        return False
    
    print("PyInstaller打包完成!")
    return True

def build_installer():
    """使用Inno Setup生成安装程序"""
    print("\n使用Inno Setup生成安装程序...")
    
    if not os.path.exists(INNO_SETUP_PATH):
        print(f"错误: 找不到Inno Setup: {INNO_SETUP_PATH}")
        return False
    
    iss_file = f"{APP_NAME}.iss"
    if not os.path.exists(iss_file):
        print(f"错误: 找不到ISS文件: {iss_file}")
        return False
    
    cmd = [INNO_SETUP_PATH, iss_file]
    print(f"执行命令: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode != 0:
        print("Inno Setup编译失败!")
        return False
    
    print("安装程序生成完成!")
    return True

def main():
    print("=" * 50)
    print(f"  {APP_NAME} v{VERSION} 安装版打包脚本")
    print("=" * 50)
    
    # 1. 清理
    clean_build()
    
    # 2. PyInstaller打包
    if not build_with_pyinstaller():
        sys.exit(1)
    
    # 3. Inno Setup生成安装程序
    if not build_installer():
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("打包完成!")
    print(f"安装程序位置: dist/{APP_NAME}_v{VERSION}_安装程序.exe")
    print("=" * 50)

if __name__ == '__main__':
    main()
