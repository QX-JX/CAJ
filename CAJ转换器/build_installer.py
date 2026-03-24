#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Inno Setup创建安装程序
"""
import os
import sys
import subprocess
import shutil

def find_inno_setup():
    """查找Inno Setup安装位置"""
    possible_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

def main():
    app_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(app_dir)
    
    print("=" * 70)
    print("CAJ转换器 - Inno Setup 安装程序生成工具")
    print("=" * 70)
    
    # 检查Inno Setup
    print("\n[1/3] 检查Inno Setup...")
    print("-" * 70)
    
    inno_setup = find_inno_setup()
    if not inno_setup:
        print("✗ 未找到Inno Setup")
        print("\n请先安装Inno Setup:")
        print("  下载地址: https://jrsoftware.org/isdl.php")
        print("  或使用 choco install innosetup")
        return False
    
    print(f"✓ 找到Inno Setup: {inno_setup}")
    
    # 检查必要文件
    print("\n[2/3] 检查必要文件...")
    print("-" * 70)
    
    required_files = [
        "CAJ转换器.iss",
        "CAJ转换器.ico",
        "鲲穹01.ico",
        "dist/CAJ转换器/CAJ转换器.exe",
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file}")
        else:
            print(f"✗ {file} - 不存在")
            return False
    
    # 编译安装程序
    print("\n[3/3] 编译安装程序...")
    print("-" * 70)
    
    iss_file = os.path.join(app_dir, "CAJ转换器.iss")
    
    cmd = [inno_setup, iss_file]
    
    print(f"运行命令: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print("\n✗ 编译失败")
        return False
    
    # 检查输出文件
    print("\n" + "=" * 70)
    print("✓ 安装程序生成完成！")
    print("=" * 70)
    
    dist_dir = os.path.join(app_dir, "dist")
    installer_file = os.path.join(dist_dir, "CAJ转换器_v1.0.1_安装程序.exe")
    
    if os.path.exists(installer_file):
        size = os.path.getsize(installer_file) / 1024 / 1024
        print(f"\n✓ 安装程序: CAJ转换器_v1.0.1_安装程序.exe ({size:.2f} MB)")
        print(f"  位置: {dist_dir}")
        print("\n功能特性:")
        print("  ✓ 用户可自行选择安装目录")
        print("  ✓ 创建开始菜单快捷方式")
        print("  ✓ 可选创建桌面快捷方式")
        print("  ✓ 支持卸载程序")
        print("  ✓ 安装完成后自动启动程序")
        return True
    else:
        print(f"\n✗ 安装程序未生成: {installer_file}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
