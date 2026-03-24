"""
单文件打包脚本 - 生成独立的exe
1. 使用PyInstaller打包成单文件模式
2. 包含完整的JRE环境
"""
import os
import sys
import subprocess
import shutil

# 配置
APP_NAME = "CAJ转换器"
VERSION = "1.0.0"
JRE_SOURCE = r"E:\JDK\openjdk-17_windows-x64_bin\jdk-17"  # 自动检测到的路径

def copy_jre_minimal(src, dest):
    """复制最小化JRE"""
    print(f"复制JRE: {src} -> {dest}")
    if os.path.exists(dest):
        shutil.rmtree(dest)
    
    os.makedirs(os.path.join(dest, "bin"), exist_ok=True)
    
    # 1. 复制bin目录下的主要文件
    bin_files = [
        "java.exe", "javaw.exe", "keytool.exe",
        "java.dll", "jli.dll", "verify.dll", "zip.dll", "net.dll", "nio.dll",
        "awt.dll", "fontmanager.dll", "javajpeg.dll", "lcms.dll"
    ]
    
    # 复制所有 .dll 文件以防万一
    for f in os.listdir(os.path.join(src, "bin")):
        if f.endswith(".dll") or f in bin_files:
            s = os.path.join(src, "bin", f)
            d = os.path.join(dest, "bin", f)
            if os.path.exists(s):
                shutil.copy2(s, d)
    
    # 2. 复制lib目录
    if os.path.exists(os.path.join(src, "lib")):
        shutil.copytree(os.path.join(src, "lib"), os.path.join(dest, "lib"))
    
    # 3. 复制conf目录
    if os.path.exists(os.path.join(src, "conf")):
        shutil.copytree(os.path.join(src, "conf"), os.path.join(dest, "conf"))

def prepare_jre():
    """准备JRE环境"""
    if not os.path.exists(JRE_SOURCE):
        print(f"⚠ JRE源路径不存在: {JRE_SOURCE}")
        return False
        
    print("准备JRE环境...")
    copy_jre_minimal(JRE_SOURCE, "jre")
    return True

def clean_build():
    """清理构建目录"""
    print("清理构建目录...")
    dirs_to_clean = ['build', f'dist']
    for d in dirs_to_clean:
        if os.path.exists(d):
            try:
                shutil.rmtree(d)
                print(f"  已删除: {d}")
            except:
                pass

def build_with_pyinstaller():
    """使用PyInstaller打包"""
    print("\n使用PyInstaller打包(单文件模式)...")
    
    # 检查JRE是否存在
    jre_exists = os.path.exists('jre')
    if jre_exists:
        print("✓ 检测到JRE目录，将打包到EXE中")
    else:
        print("⚠ 未检测到JRE目录，CAJ转OFD功能需要用户自行安装Java")
    
    # PyInstaller命令
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name', APP_NAME,
        '--windowed',  # 无控制台窗口
        '--onefile',   # 单文件模式
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

def main():
    print("=" * 50)
    print(f"  {APP_NAME} v{VERSION} 单文件打包脚本")
    print("=" * 50)
    
    # 1. 清理
    clean_build()
    
    # 2. 准备JRE
    prepare_jre()
    
    # 3. PyInstaller打包
    if not build_with_pyinstaller():
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("打包完成!")
    print(f"程序位置: dist/{APP_NAME}.exe")
    print("=" * 50)

if __name__ == '__main__':
    main()
