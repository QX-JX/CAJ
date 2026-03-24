import os
import sys
import logging

def setup_logging():
    """配置日志"""
    # 确定日志目录
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    log_dir = os.path.join(base_dir, "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, "app.log")
    
    # 配置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def get_logger(name):
    """获取指定名称的日志对象"""
    return logging.getLogger(name)

def get_icon_path(icon_name: str) -> str:
    """获取图标文件路径，支持打包后的环境"""
    # 如果是PyInstaller打包的环境
    if getattr(sys, 'frozen', False):
        # 优先从_MEIPASS临时目录获取（onefile模式）
        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, icon_name)
            if os.path.exists(icon_path):
                return icon_path
        # 其次从exe所在目录获取（onedir模式）
        base_dir = os.path.dirname(sys.executable)
        
        # 尝试在 _internal 目录查找 (PyInstaller 6+)
        internal_path = os.path.join(base_dir, "_internal", icon_name)
        if os.path.exists(internal_path):
            return internal_path
            
        # 尝试在根目录查找
        root_path = os.path.join(base_dir, icon_name)
        if os.path.exists(root_path):
            return root_path
    else:
        # 开发环境：从 core/utils.py 往上两级到项目根目录
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    icon_path = os.path.join(base_dir, icon_name)
    return icon_path if os.path.exists(icon_path) else None
