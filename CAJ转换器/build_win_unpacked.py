"""
win-unpacked 打包脚本 - 生成文件夹形式的便携版（用于软件签名）
1. 使用 PyInstaller 打包成 onedir 模式
2. 包含完整的 JRE 环境
3. 最终输出为 dist/win-unpacked 目录
"""
import os
import sys
import subprocess
import shutil

# 配置
APP_NAME = "CAJ转换器"
VERSION = "1.0.1"
# 获取根目录下的 jre 路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JRE_SOURCE = os.path.join(BASE_DIR, "jre")

def copy_jre_minimal(src, dest):
    """复制最小化 JRE"""
    print(f"准备 JRE: {src} -> {dest}")
    if os.path.exists(dest):
        shutil.rmtree(dest)
    
    os.makedirs(os.path.join(dest, "bin"), exist_ok=True)
    
    # 1. 复制 bin 目录下的主要文件
    bin_files = [
        "java.exe", "javaw.exe", "keytool.exe",
        "java.dll", "jli.dll", "verify.dll", "zip.dll", "net.dll", "nio.dll",
        "awt.dll", "fontmanager.dll", "javajpeg.dll", "lcms.dll"
    ]
    
    # 复制所有 .dll 文件以防万一
    if os.path.exists(os.path.join(src, "bin")):
        for f in os.listdir(os.path.join(src, "bin")):
            if f.endswith(".dll") or f in bin_files:
                s = os.path.join(src, "bin", f)
                d = os.path.join(dest, "bin", f)
                if os.path.exists(s):
                    shutil.copy2(s, d)
    
    # 2. 复制 lib 目录
    if os.path.exists(os.path.join(src, "lib")):
        shutil.copytree(os.path.join(src, "lib"), os.path.join(dest, "lib"))
    
    # 3. 复制 conf 目录
    if os.path.exists(os.path.join(src, "conf")):
        shutil.copytree(os.path.join(src, "conf"), os.path.join(dest, "conf"))

def prepare_jre():
    """准备 JRE 环境"""
    if not os.path.exists(JRE_SOURCE):
        print(f"⚠ JRE 源路径不存在: {JRE_SOURCE}")
        return False
        
    print("准备 JRE 环境...")
    copy_jre_minimal(JRE_SOURCE, "jre")
    return True

def clean_build():
    """清理构建目录"""
    print("清理旧的构建目录...")
    dirs_to_clean = ['build', 'dist', 'win-unpacked']
    for d in dirs_to_clean:
        if os.path.exists(d):
            try:
                shutil.rmtree(d)
                print(f"  已删除: {d}")
            except Exception as e:
                print(f"  警告: 无法删除 {d}: {e}")

def build_with_pyinstaller():
    """使用 PyInstaller 打包成目录模式"""
    print("\n使用 PyInstaller 打包 (onedir 模式)...")
    
    # 检查 JRE 是否存在
    jre_exists = os.path.exists('jre')
    
    # PyInstaller 命令
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name', APP_NAME,
        '--windowed',  # 无控制台窗口
        '--onedir',    # 文件夹模式（默认）
        '--icon', f'..\\{APP_NAME}.ico',
        '--add-data', '..\\lib;lib',
        '--add-data', '..\\鲲穹01.ico;.',
        '--add-data', f'..\\{APP_NAME}.ico;.',
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
        # 隐藏导入 - 其他依赖
        '--hidden-import=docx',
        '--hidden-import=docx.document',
        '--hidden-import=docx.oxml',
        '--hidden-import=reportlab',
        '--hidden-import=reportlab.pdfgen',
        '--hidden-import=reportlab.lib',
        '--hidden-import=reportlab.lib.pagesizes',
        '--hidden-import=reportlab.lib.units',
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
    
    # 如果 JRE 存在，添加到打包中
    if jre_exists:
        cmd.insert(-1, '--add-data')
        cmd.insert(-1, 'jre;jre')
    
    print(f"执行打包命令...")
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode != 0:
        print("PyInstaller 打包失败!")
        return False
    
    # 重命名 dist 目录下的文件夹为 win-unpacked
    src_folder = os.path.join('dist', APP_NAME)
    dest_folder = os.path.join('dist', 'win-unpacked')
    
    if os.path.exists(dest_folder):
        shutil.rmtree(dest_folder)
        
    if os.path.exists(src_folder):
        print(f"\n重命名输出目录: {src_folder} -> {dest_folder}")
        os.rename(src_folder, dest_folder)
        return True
    else:
        print("⚠ 找不到打包输出目录!")
        return False

def main():
    print("=" * 50)
    print(f"  {APP_NAME} v{VERSION} win-unpacked 打包脚本")
    print("=" * 50)
    
    # 1. 清理
    clean_build()
    
    # 2. 准备 JRE
    if not prepare_jre():
        print("⚠ JRE 准备失败，可能导致 OFD 转换功能失效。")
    
    # 3. PyInstaller 打包
    if not build_with_pyinstaller():
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("打包完成!")
    print(f"文件夹位置: dist/win-unpacked")
    print("=" * 50)

if __name__ == '__main__':
    main()
