import os
import sys
import json
import requests
import subprocess
from PyQt6.QtCore import QObject, pyqtSignal
from core.constants import SOFTWARE_ID, CURRENT_VERSION, UPDATE_API_URL

class UpdateManager(QObject):
    """
    软件更新管理器
    负责检查更新和启动更新程序
    """
    update_available = pyqtSignal(str, str, str)  # version, download_url, hash
    no_update = pyqtSignal()
    check_failed = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def check_for_updates(self):
        """检查更新"""
        try:
            params = {
                "software": SOFTWARE_ID,
                "version": CURRENT_VERSION
            }
            
            response = requests.get(UPDATE_API_URL, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("has_update"):
                version = data.get("version")
                download_url = data.get("download_url")
                package_hash = data.get("package_hash", "")
                
                if version and download_url:
                    self.update_available.emit(version, download_url, package_hash)
                else:
                    self.check_failed.emit("返回数据格式错误")
            else:
                self.no_update.emit()
                
        except Exception as e:
            self.check_failed.emit(f"检查更新失败: {str(e)}")

    def start_update(self, download_url: str, package_hash: str):
        """启动更新程序"""
        try:
            # 获取updater.exe路径
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                # 如果是源码运行，main.py在CAJ转换器源码目录下，updater.exe应该也在那里
                # 但base_dir这里取的是core的上级，即CAJ转换器源码
            
            updater_path = os.path.join(base_dir, "updater.exe")
            
            if not os.path.exists(updater_path):
                # 尝试在当前工作目录查找
                updater_path = os.path.join(os.getcwd(), "updater.exe")
            
            if not os.path.exists(updater_path):
                raise FileNotFoundError(f"未找到更新程序: {updater_path}")

            main_exe = "CAJ转换器.exe" if getattr(sys, 'frozen', False) else "main.py"
            # 如果是源码运行，exe参数可能需要调整，或者updater支持重启python脚本？
            # 通用updater通常重启exe。如果是源码，可能不太好重启。
            # 但用户要求"打包一个版本"，所以最终是在exe环境下运行。
            # 在源码环境下，我们可以让它重启 python main.py，但这需要updater支持命令。
            # 这里的updater.exe只接受 --exe 参数作为文件名。
            # 如果是源码，我们暂时传入 python.exe? 不，updater会尝试启动 dir/exe。
            # 所以源码环境下测试更新可能无法自动重启成功，但可以测试启动updater。
            
            if not getattr(sys, 'frozen', False):
                 # 开发环境特殊处理：告诉updater重启 python，但这很难通过 --exe 参数实现
                 # 除非我们把 main_exe 设为 python.exe 并把参数传进去，但updater可能不支持参数
                 # 暂时假设主要用于生产环境
                 pass

            cmd = [
                updater_path,
                "--url", download_url,
                "--hash", package_hash,
                "--dir", base_dir,
                "--exe", main_exe,
                "--pid", str(os.getpid())
            ]
            
            # 独立进程启动
            subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
            
            # 退出主程序
            sys.exit(0)
            
        except Exception as e:
            raise Exception(f"启动更新失败: {str(e)}")
