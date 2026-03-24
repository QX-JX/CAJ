#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAJ转换器 - 优化打包脚本
包含依赖检查、验证和完整的打包流程
"""
import os
import sys
import shutil
import subprocess
import json
from pathlib import Path

class PackageBuilder:
    def __init__(self):
        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.app_name = "鲲穹AI_CAJ转换器"
        self.version = "1.0.0"
        self.dist_dir = os.path.join(self.app_dir, "dist")
        self.build_dir = os.path.join(self.app_dir, "build")
        
    def log(self, level, msg):
        """日志输出"""
        symbols = {"✓": "✓", "✗": "✗", "→": "→", "!": "!"}
        prefix = {
            "success": "✓",
            "error": "✗",
            "info": "→",
            "warning": "!"
        }
        print(f"{prefix.get(level, '→')} {msg}")
    
    def check_dependencies(self):
        """检查所有依赖"""
        self.log("info", "检查依赖...")
        print("-" * 70)
        
        required_packages = {
            "PyQt6": "PyQt6>=6.4.0",
            "PyInstaller": "PyInstaller>=5.0",
            "caj2pdf": "caj2pdf-restructured>=0.1.0",
            "pdf2image": "pdf2image>=1.16.0",
            "pdf2docx": "pdf2docx>=0.5.6",
            "pdfplumber": "pdfplumber>=0.9.0",
            "PIL": "Pillow>=9.0.0",
            "requests": "requests>=2.28.0",
            "docx": "python-docx>=0.8.11",
            "reportlab": "reportlab>=4.0.0",
            "fitz": "PyMuPDF>=1.23.0",
        }
        
        missing = []
        for pkg_name, pkg_spec in required_packages.items():
            try:
                __import__(pkg_name)
                self.log("success", f"{pkg_spec}")
            except ImportError:
                self.log("error", f"{pkg_spec} - 未安装")
                missing.append(pkg_spec)
        
        if missing:
            print("\n缺少以下依赖，请运行:")
            print(f"  pip install {' '.join(missing)}")
            return False
        
        self.log("success", "所有依赖已安装")
        return True
    
    def check_files(self):
        """检查必要文件"""
        self.log("info", "检查必要文件...")
        print("-" * 70)
        
        required_files = {
            "main.py": "主程序入口",
            "鲲穹01.ico": "应用图标",
            "CAJ转换器.ico": "应用图标",
            "requirements.txt": "依赖列表",
            "core/converter.py": "转换器核心",
            "ui/main_window.py": "主窗口",
            "lib/caj2pdf": "CAJ解析库",
        }
        
        missing = []
        for file_path, desc in required_files.items():
            full_path = os.path.join(self.app_dir, file_path)
            if os.path.exists(full_path):
                self.log("success", f"{file_path} - {desc}")
            else:
                self.log("error", f"{file_path} - 不存在")
                missing.append(file_path)
        
        if missing:
            return False
        
        self.log("success", "所有必要文件已找到")
        return True
    
    def clean_build(self):
        """清理构建目录"""
        self.log("info", "清理构建目录...")
        print("-" * 70)
        
        dirs_to_clean = [self.build_dir, self.dist_dir]
        for d in dirs_to_clean:
            if os.path.exists(d):
                shutil.rmtree(d)
                self.log("success", f"已删除: {d}")
        
        # 清理spec文件
        spec_files = [
            "鲲穹AI_CAJ转换器.spec",
            "CAJ转换器.spec",
            "CAJ转换器_便携版.spec",
        ]
        for spec_file in spec_files:
            spec_path = os.path.join(self.app_dir, spec_file)
            if os.path.exists(spec_path):
                os.remove(spec_path)
                self.log("success", f"已删除: {spec_file}")
    
    def build_with_pyinstaller(self):
        """使用PyInstaller打包"""
        self.log("info", "使用PyInstaller打包...")
        print("-" * 70)
        
        icon_path = os.path.join(self.app_dir, "鲲穹01.ico")
        
        cmd = [
            sys.executable, "-m", "PyInstaller",
            f"--name={self.app_name}",
            "--windowed",
            "--onedir",
            f"--icon={icon_path}",
            "--noconfirm",
            "--clean",
            # 添加数据文件
            f"--add-data={icon_path};.",
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
            # 隐藏导入 - Word转PDF（关键）
            "--hidden-import=docx",
            "--hidden-import=docx.document",
            "--hidden-import=docx.oxml",
            "--hidden-import=reportlab",
            "--hidden-import=reportlab.pdfgen",
            "--hidden-import=reportlab.lib",
            "--hidden-import=reportlab.lib.pagesizes",
            "--hidden-import=reportlab.lib.units",
            # 隐藏导入 - 备选方案
            "--hidden-import=comtypes",
            "--hidden-import=comtypes.client",
            # 收集所有子模块
            "--collect-all=PyQt6",
            "--collect-all=fitz",
            "--collect-all=docx",
            "--collect-all=reportlab",
            # 入口文件
            "main.py"
        ]
        
        print(f"执行命令: {' '.join(cmd[:5])} ...")
        print()
        
        result = subprocess.run(cmd, cwd=self.app_dir)
        
        if result.returncode != 0:
            self.log("error", "PyInstaller打包失败")
            return False
        
        self.log("success", "PyInstaller打包完成")
        return True
    
    def verify_build(self):
        """验证打包结果"""
        self.log("info", "验证打包结果...")
        print("-" * 70)
        
        output_dir = os.path.join(self.dist_dir, self.app_name)
        
        required_items = {
            f"{self.app_name}.exe": "主程序",
            "lib/caj2pdf": "CAJ解析库",
        }
        
        all_ok = True
        for item, desc in required_items.items():
            item_path = os.path.join(output_dir, item)
            if os.path.exists(item_path):
                self.log("success", f"{item} - {desc}")
            else:
                self.log("error", f"{item} - 不存在")
                all_ok = False
        
        if all_ok:
            # 计算目录大小
            total_size = self._get_dir_size(output_dir)
            self.log("success", f"打包目录大小: {total_size / 1024 / 1024:.2f} MB")
        
        return all_ok
    
    def _get_dir_size(self, path):
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
    
    def create_portable(self):
        """创建便携版"""
        self.log("info", "创建便携版...")
        print("-" * 70)
        
        output_dir = os.path.join(self.dist_dir, self.app_name)
        portable_dir = os.path.join(self.dist_dir, f"{self.app_name}_便携版")
        
        if os.path.exists(portable_dir):
            shutil.rmtree(portable_dir)
        
        shutil.copytree(output_dir, portable_dir)
        
        # 创建启动脚本
        batch_file = os.path.join(portable_dir, "启动.bat")
        with open(batch_file, 'w', encoding='gbk') as f:
            f.write(f"@echo off\n")
            f.write(f"cd /d \"%~dp0\"\n")
            f.write(f"{self.app_name}.exe\n")
        
        self.log("success", f"便携版已创建: {portable_dir}")
        return True
    
    def build(self):
        """执行完整打包流程"""
        print("=" * 70)
        print(f"  {self.app_name} v{self.version} - 打包工具")
        print("=" * 70)
        print()
        
        # 1. 检查依赖
        if not self.check_dependencies():
            return False
        print()
        
        # 2. 检查文件
        if not self.check_files():
            return False
        print()
        
        # 3. 清理构建
        self.clean_build()
        print()
        
        # 4. PyInstaller打包
        if not self.build_with_pyinstaller():
            return False
        print()
        
        # 5. 验证结果
        if not self.verify_build():
            return False
        print()
        
        # 6. 创建便携版
        self.create_portable()
        print()
        
        # 完成
        print("=" * 70)
        self.log("success", "打包完成！")
        print("=" * 70)
        print()
        print("输出文件:")
        print(f"  • 标准版: {os.path.join(self.dist_dir, self.app_name)}")
        print(f"  • 便携版: {os.path.join(self.dist_dir, f'{self.app_name}_便携版')}")
        print()
        print("关键改进:")
        print("  ✓ 支持 Word (doc/docx) 转 CAJ")
        print("  ✓ 使用 python-docx + reportlab 库")
        print("  ✓ 无需安装 Microsoft Word")
        print("  ✓ 支持 Windows/Linux/macOS")
        print()
        
        return True


def main():
    builder = PackageBuilder()
    success = builder.build()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
