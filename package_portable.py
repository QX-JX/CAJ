import shutil
import os
import sys
# 添加当前目录到 path 以便导入 core
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.constants import CURRENT_VERSION

def make_portable_archive():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, "dist")
    source_dir = os.path.join(dist_dir, "CAJ转换器")
    if not os.path.exists(source_dir):
        alt_source_dir = os.path.join(base_dir, "CAJ转换器", "dist", "CAJ转换器")
        if os.path.exists(alt_source_dir):
            print(f"提示: 使用备用目录 {alt_source_dir}")
            source_dir = alt_source_dir
        else:
            print(f"错误: 源目录不存在 {source_dir}")
            return

    output_filename = f"CAJ转换器_v{CURRENT_VERSION}_便携版"
    output_path = os.path.join(dist_dir, output_filename)
    
    print(f"正在创建便携版压缩包...")
    print(f"源目录: {source_dir}")
    print(f"目标文件: {output_path}.zip")
    
    shutil.make_archive(output_path, 'zip', source_dir)
    
    print(f"✓ 便携版创建成功: {output_path}.zip")

if __name__ == "__main__":
    make_portable_archive()
