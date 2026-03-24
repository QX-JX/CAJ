"""
CAJ转换器打包脚本
将程序打包成独立的exe，包含JRE环境
"""
import os
import sys
import shutil
import subprocess

def main():
    # 获取当前目录
    app_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(app_dir)
    
    print("=" * 60)
    print("CAJ转换器 - 打包工具")
    print("=" * 60)
    
    # 检查PyInstaller是否安装
    try:
        import PyInstaller
        print(f"✓ PyInstaller 已安装: {PyInstaller.__version__}")
    except ImportError:
        print("✗ PyInstaller 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("✓ PyInstaller 安装完成")
    
    # 检查图标文件
    icon_path = os.path.join(os.path.dirname(app_dir), "CAJ转换器.ico")
    if not os.path.exists(icon_path):
        # 尝试当前目录
        icon_path = os.path.join(app_dir, "CAJ转换器.ico")
        
    if not os.path.exists(icon_path):
        print(f"✗ 图标文件不存在: {icon_path}")
        return
    print(f"✓ 图标文件: {icon_path}")
    
    # 清理旧的构建文件
    for folder in ["build", "dist"]:
        folder_path = os.path.join(app_dir, folder)
        if os.path.exists(folder_path):
            print(f"清理目录: {folder}")
            try:
                shutil.rmtree(folder_path)
            except PermissionError:
                print(f"  警告: 无法删除 {folder}，可能被占用，继续...")
                import time
                time.sleep(1)
                try:
                    shutil.rmtree(folder_path)
                except:
                    print(f"  跳过 {folder}")
    
    spec_file = os.path.join(app_dir, "CAJ转换器.spec")
    if os.path.exists(spec_file):
        os.remove(spec_file)
    
    # 构建PyInstaller命令
    # 查找鲲穹01.ico
    kq_icon = os.path.join(os.path.dirname(app_dir), "鲲穹01.ico")
    if not os.path.exists(kq_icon):
        kq_icon = os.path.join(app_dir, "鲲穹01.ico")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=CAJ转换器",
        "--windowed",
        "--onedir",
        f"--icon={icon_path}",
        "--noconfirm",
        "--clean",
        # 添加数据文件
        f"--add-data={icon_path};.",
        f"--add-data={kq_icon};.",
        f"--add-data=lib/caj2pdf;lib/caj2pdf",
        f"--add-data=locales;locales",
        # 隐藏导入 - 核心库
        "--hidden-import=PyQt6",
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        # 隐藏导入 - PDF/文档处理
        "--hidden-import=PyPDF2",
        "--hidden-import=pdf2docx",
        "--hidden-import=PIL",
        "--hidden-import=PIL.Image",
        "--hidden-import=fitz",
        "--hidden-import=pymupdf",
        # 隐藏导入 - Word转PDF（完整版）
        "--hidden-import=docx",
        "--hidden-import=docx.document",
        "--hidden-import=docx.oxml",
        "--hidden-import=docx.oxml.ns",
        "--hidden-import=docx.oxml.xmlchemy",
        "--hidden-import=docx.oxml.text.paragraph",
        "--hidden-import=docx.oxml.text.run",
        "--hidden-import=docx.text.paragraph",
        "--hidden-import=docx.text.run",
        "--hidden-import=reportlab",
        "--hidden-import=reportlab.pdfgen",
        "--hidden-import=reportlab.pdfgen.canvas",
        "--hidden-import=reportlab.lib",
        "--hidden-import=reportlab.lib.pagesizes",
        "--hidden-import=reportlab.lib.units",
        "--hidden-import=reportlab.lib.colors",
        "--hidden-import=reportlab.lib.styles",
        # 隐藏导入 - 备选方案
        "--hidden-import=comtypes",
        "--hidden-import=comtypes.client",
        # 排除非必要的重型依赖
        "--exclude-module=torch",
        "--exclude-module=tensorflow",
        "--exclude-module=scipy",
        "--exclude-module=matplotlib",
        "--exclude-module=pandas",
        "--exclude-module=numba",
        "--exclude-module=onnxruntime",
        "--exclude-module=tensorboard",
        "--exclude-module=notebook",
        "--exclude-module=jedi",
        # 收集所有子模块
        "--collect-all=PyQt6",
        "--collect-all=fitz",
        "--collect-all=docx",
        "--collect-all=reportlab",
        # 入口文件
        "main.py"
    ]
    
    print("\n" + "=" * 60)
    print("开始打包程序...")
    print("=" * 60)
    
    result = subprocess.run(cmd, cwd=app_dir)
    
    if result.returncode != 0:
        print("✗ 打包失败")
        return
    
    print("✓ 程序打包完成")
    
    # 复制依赖库 (手动复制以确保存在)
    dist_dir = os.path.join(app_dir, "dist", "CAJ转换器")
    internal_dir = os.path.join(dist_dir, "_internal")
    
    # 如果_internal存在，资源放在那里；否则放在根目录
    if os.path.exists(internal_dir):
        target_root = internal_dir
    else:
        target_root = dist_dir
        
    print(f"目标资源目录: {target_root}")

    # 1. 复制lib目录
    lib_source = os.path.join(app_dir, "lib")
    lib_dest = os.path.join(target_root, "lib")
    
    print(f"\n复制依赖库...")
    print(f"从: {lib_source}")
    print(f"到: {lib_dest}")
    
    if os.path.exists(lib_dest):
        shutil.rmtree(lib_dest)
        
    try:
        shutil.copytree(lib_source, lib_dest, dirs_exist_ok=True)
        # 移除 lib 中的 ofd_converter 目录
        ofd_lib_path = os.path.join(lib_dest, "ofd_converter")
        if os.path.exists(ofd_lib_path):
            shutil.rmtree(ofd_lib_path)
        print("✓ 依赖库复制完成")
    except Exception as e:
        print(f"✗ 依赖库复制失败: {e}")

    # 2. 复制updater.exe
    updater_src = os.path.join(app_dir, "更新", "通用更新组件", "updater.exe")
    updater_dest = os.path.join(dist_dir, "updater.exe")
    
    print(f"\n复制更新程序...")
    if os.path.exists(updater_src):
        try:
            shutil.copy2(updater_src, updater_dest)
            print(f"✓ 已复制: {updater_dest}")
        except Exception as e:
            print(f"✗ 复制更新程序失败: {e}")
    else:
        print(f"✗ 更新程序不存在: {updater_src}")
    
    # 验证打包结果
    print("\n" + "=" * 60)
    print("验证打包结果...")
    print("=" * 60)
    
    exe_path = os.path.join(dist_dir, "CAJ转换器.exe")
    if os.path.exists(exe_path):
        print(f"✓ EXE文件: {exe_path}")
    else:
        print(f"✗ EXE文件不存在: {exe_path}")
    
    print("\n" + "=" * 60)
    print("打包完成！")
    print("=" * 60)
    
    # 计算目录大小
    total_size = get_dir_size(dist_dir)
    print(f"输出目录: {dist_dir}")
    print(f"总大小: {total_size / 1024 / 1024:.2f} MB")
    print("\n提示: 可以将整个目录压缩后分发给用户")


def copy_jre_minimal(src, dest):
    """复制JRE（只包含运行时必要文件）"""
    # 需要复制的目录和文件
    required_items = [
        "bin",
        "conf", 
        "lib",
        "release"
    ]
    
    os.makedirs(dest, exist_ok=True)
    
    for item in required_items:
        src_path = os.path.join(src, item)
        dest_path = os.path.join(dest, item)
        
        if os.path.isdir(src_path):
            print(f"  复制目录: {item}...")
            shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
        elif os.path.isfile(src_path):
            print(f"  复制文件: {item}")
            shutil.copy2(src_path, dest_path)
        else:
            print(f"  跳过: {item} (不存在)")


def get_dir_size(path):
    """计算目录大小"""
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total += os.path.getsize(fp)
            except:
                pass
    return total


if __name__ == "__main__":
    main()
