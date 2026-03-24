"""
下载便携版JRE（Java运行环境）
用于CAJ转OFD功能
"""
import os
import sys
import urllib.request
import zipfile
import shutil

# JRE下载配置 - 使用Eclipse Adoptium（开源、免费、可靠）
JRE_VERSION = "17.0.13+11"
# 使用清华大学镜像源（国内下载更快）
JRE_URL = "https://mirrors.tuna.tsinghua.edu.cn/Adoptium/17/jre/x64/windows/OpenJDK17U-jre_x64_windows_hotspot_17.0.13_11.zip"
# 备用：官方源
JRE_URL_BACKUP = "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.13%2B11/OpenJDK17U-jre_x64_windows_hotspot_17.0.13_11.zip"

JRE_DIR = "jre"
TEMP_ZIP = "jre_temp.zip"

def download_file(url, filename):
    """下载文件"""
    print(f"正在下载: {url}")
    try:
        # 设置User-Agent避免被拒绝
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60) as response:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            chunk_size = 8192
            
            with open(filename, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r下载进度: {percent:.1f}% ({downloaded/1024/1024:.1f}/{total_size/1024/1024:.1f} MB)", end='')
            print("\n下载完成!")
            return True
    except Exception as e:
        print(f"\n下载失败: {e}")
        return False

def extract_jre(zip_file, target_dir):
    """解压JRE"""
    print(f"正在解压到: {target_dir}")
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            # 获取压缩包中的根目录名
            namelist = zip_ref.namelist()
            if not namelist:
                print("压缩包为空")
                return False
            
            root_dir = namelist[0].split('/')[0]
            
            # 解压到临时目录
            temp_extract = "temp_jre_extract"
            if os.path.exists(temp_extract):
                shutil.rmtree(temp_extract)
            
            print("解压中...")
            zip_ref.extractall(temp_extract)
            
            # 移动到目标目录
            extracted_path = os.path.join(temp_extract, root_dir)
            if not os.path.exists(extracted_path):
                # 可能直接解压到temp_extract
                extracted_path = temp_extract
            
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            
            # 查找jre目录
            if os.path.exists(os.path.join(extracted_path, "bin", "java.exe")):
                # 直接就是JRE
                shutil.move(extracted_path, target_dir)
            elif os.path.exists(os.path.join(extracted_path, "jre")):
                # JDK中的JRE
                shutil.move(os.path.join(extracted_path, "jre"), target_dir)
            else:
                print("未找到有效的JRE结构")
                return False
            
            # 清理临时目录
            if os.path.exists(temp_extract):
                shutil.rmtree(temp_extract)
            
        print("解压完成!")
        return True
    except Exception as e:
        print(f"解压失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("  下载便携版JRE for CAJ转换器")
    print("  用途：CAJ转OFD功能需要Java运行环境")
    print("=" * 60)
    
    # 检查是否已存在
    if os.path.exists(JRE_DIR):
        java_exe = os.path.join(JRE_DIR, "bin", "java.exe")
        if os.path.exists(java_exe):
            print(f"\n✓ JRE已存在: {JRE_DIR}")
            print(f"✓ 大小: {get_dir_size(JRE_DIR):.1f} MB")
            response = input("\n是否重新下载？(y/n): ")
            if response.lower() != 'y':
                print("保持现有JRE")
                return
        shutil.rmtree(JRE_DIR)
    
    # 尝试清华镜像源（国内快）
    print("\n尝试从清华大学镜像源下载...")
    if download_file(JRE_URL, TEMP_ZIP):
        if extract_jre(TEMP_ZIP, JRE_DIR):
            if os.path.exists(TEMP_ZIP):
                os.remove(TEMP_ZIP)
            print(f"\n✓ JRE已成功下载到: {JRE_DIR}")
            print(f"✓ 大小: {get_dir_size(JRE_DIR):.1f} MB")
            print(f"✓ Java版本: {JRE_VERSION}")
            return
        if os.path.exists(TEMP_ZIP):
            os.remove(TEMP_ZIP)
    
    # 尝试官方源
    print("\n尝试从官方源下载...")
    if download_file(JRE_URL_BACKUP, TEMP_ZIP):
        if extract_jre(TEMP_ZIP, JRE_DIR):
            if os.path.exists(TEMP_ZIP):
                os.remove(TEMP_ZIP)
            print(f"\n✓ JRE已成功下载到: {JRE_DIR}")
            print(f"✓ 大小: {get_dir_size(JRE_DIR):.1f} MB")
            print(f"✓ Java版本: {JRE_VERSION}")
            return
        if os.path.exists(TEMP_ZIP):
            os.remove(TEMP_ZIP)
    
    print("\n✗ 自动下载失败！")
    print("\n手动下载方法：")
    print("1. 访问: https://adoptium.net/zh-CN/temurin/releases/")
    print("2. 选择: Version=17, Operating System=Windows, Architecture=x64, Package Type=JRE")
    print("3. 下载.zip文件")
    print("4. 解压后将jre文件夹（包含bin目录）放到当前目录")
    print("5. 确保目录结构为: jre/bin/java.exe")

def get_dir_size(path):
    """获取目录大小（MB）"""
    total = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total += os.path.getsize(filepath)
    except:
        pass
    return total / (1024 * 1024)

if __name__ == '__main__':
    main()
