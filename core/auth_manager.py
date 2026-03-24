"""
登录认证管理模块
处理用户登录、Token管理、轮询等逻辑
"""
import hmac
import hashlib
import uuid
import time
import requests
import json
import base64
from typing import Optional, Dict, Callable
from threading import Thread, Event
from PyQt6.QtCore import QObject, pyqtSignal


from core.constants import SOFTWARE_ID, API_BASE_URL

class AuthManager(QObject):
    login_success = pyqtSignal(dict)
    login_failed = pyqtSignal(str)
    login_cancelled = pyqtSignal()
    polling_started = pyqtSignal()
    polling_stopped = pyqtSignal()
    
    API_BASE_URL = API_BASE_URL
    GET_LOGIN_URL_ENDPOINT = "/soft_desktop/get_web_login_url"
    GET_TOKEN_ENDPOINT = "/user/desktop_get_token"
    CHECK_LOGIN_ENDPOINT = "/user/check_login"
    GET_USER_INFO_ENDPOINT = "/soft_desktop/get_user_info"
    GET_FEEDBACK_URL_ENDPOINT = "/soft_desktop/get_feedback_url"
    LOGOUT_ENDPOINT = "/logout"
    
    POLL_TIMEOUT = 300
    POLL_INTERVAL = 2
    
    SECRET_KEY = b"7530bfb1ad6c41627b0f0620078fa5ed"
    
    def __init__(self):
        super().__init__()
        self.token: Optional[str] = None
        self.user_info: Optional[Dict] = None
        self.client_nonce: Optional[str] = None
        self.polling_thread: Optional[Thread] = None
        self.stop_polling_event = Event()
        self.is_polling = False
        self.auth_code: Optional[str] = None
        self.token_storage = None
    
    def generate_signed_nonce(self) -> Dict:
        nonce = str(uuid.uuid4()).replace("-", "")
        timestamp = int(time.time())
        message = f"{nonce}|{timestamp}".encode("utf-8")
        hmac_obj = hmac.new(self.SECRET_KEY, message, hashlib.sha256)
        signature = base64.b64encode(hmac_obj.digest()).decode("utf-8")
        return {
            "nonce": nonce,
            "timestamp": timestamp,
            "signature": signature
        }
    
    def encode_signed_nonce(self, signed_nonce: Dict) -> str:
        json_str = json.dumps(signed_nonce, separators=(",", ":"))
        b64 = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
        url_safe = b64.replace("+", "-").replace("/", "_").rstrip("=")
        return url_safe
    
    def get_login_url(self) -> Optional[str]:
        try:
            url = f"{self.API_BASE_URL}{self.GET_LOGIN_URL_ENDPOINT}"
            response = requests.post(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") == 1 and data.get("data"):
                return data["data"].get("login_url")
            else:
                self.login_failed.emit(f"获取登录地址失败: {data.get('msg', '未知错误')}")
                return None
        except Exception as e:
            self.login_failed.emit(f"获取登录地址异常: {str(e)}")
            return None
    
    def start_login_flow(self) -> Optional[str]:
        signed_nonce = self.generate_signed_nonce()
        encoded_nonce = self.encode_signed_nonce(signed_nonce)
        self.client_nonce = encoded_nonce
        login_url = self.get_login_url()
        if not login_url:
            return None
        
        separator = "&" if "?" in login_url else "?"
        login_url_with_nonce = (
            f"{login_url}{separator}client_type=desktop&client_nonce={self.client_nonce}"
        )
        
        return login_url_with_nonce
    
    def poll_token(self, timeout: int = POLL_TIMEOUT, 
                   on_progress: Optional[Callable[[int], None]] = None) -> bool:
        """
        轮询获取Token
        
        Args:
            timeout: 轮询超时时间（秒）
            on_progress: 进度回调函数，接收剩余秒数
            
        Returns:
            bool: 成功返回True，失败或超时返回False
        """
        if not self.client_nonce:
            self.login_failed.emit("未初始化登录流程")
            return False
        
        self.is_polling = True
        self.stop_polling_event.clear()
        self.polling_started.emit()
        
        start_time = time.time()
        elapsed = 0
        poll_count = 0
        
        try:
            while elapsed < timeout:
                # 检查是否需要停止轮询
                if self.stop_polling_event.is_set():
                    self.polling_stopped.emit()
                    self.login_cancelled.emit()
                    return False
                
                # 每3次轮询才尝试一次获取Token（减少API调用）
                poll_count += 1
                if poll_count % 3 == 0:
                    # 尝试获取Token
                    if self._try_get_token():
                        # 获取用户信息
                        if self._fetch_user_info():
                            self.polling_stopped.emit()
                            self.login_success.emit(self.user_info)
                            return True
                        else:
                            # Token有效但获取用户信息失败
                            self.polling_stopped.emit()
                            self.login_failed.emit("获取用户信息失败")
                            return False
                
                # 计算剩余时间
                elapsed = time.time() - start_time
                remaining = timeout - int(elapsed)
                
                if on_progress:
                    on_progress(remaining)
                
                # 等待后再轮询（使用更短的等待时间）
                if not self.stop_polling_event.wait(0.5):
                    pass  # 超时继续轮询
            
            # 轮询超时
            self.polling_stopped.emit()
            self.login_failed.emit("登录超时，请重试")
            return False
            
        except Exception as e:
            self.polling_stopped.emit()
            self.login_failed.emit(f"轮询异常: {str(e)}")
            return False
        finally:
            self.is_polling = False
    
    def _try_get_token(self) -> bool:
        """
        尝试获取Token
        
        Returns:
            bool: 成功返回True，失败返回False
        """
        try:
            url = f"{self.API_BASE_URL}{self.GET_TOKEN_ENDPOINT}"
            data = {
                "client_type": "desktop",
                "client_nonce": self.client_nonce
            }
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get("code") == 1 and result.get("data"):
                self.token = result["data"].get("token")
                return self.token is not None
            
            return False
        except Exception:
            return False
    
    def _fetch_user_info(self) -> bool:
        """
        获取用户信息
        
        Returns:
            bool: 成功返回True，失败返回False
        """
        if not self.token:
            return False
        
        try:
            url = f"{self.API_BASE_URL}{self.GET_USER_INFO_ENDPOINT}"
            headers = {"token": self.token}
            
            response = requests.post(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get("code") == 1 and result.get("data"):
                self.user_info = result["data"].get("user_info", {})
                return True
            
            return False
        except Exception:
            return False
    
    def check_login(self) -> bool:
        """
        检查是否已登录
        
        Returns:
            bool: 已登录返回True，未登录返回False
        """
        if not self.token:
            return False
        
        try:
            url = f"{self.API_BASE_URL}{self.CHECK_LOGIN_ENDPOINT}"
            data = {"token": self.token}
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return result.get("code") == 1
        except Exception:
            return False
    
    def logout(self) -> bool:
        if not self.token:
            return False
        
        try:
            url = f"{self.API_BASE_URL}{self.LOGOUT_ENDPOINT}"
            headers = {"token": self.token}
            
            response = requests.post(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get("code") == 1:
                self.token = None
                self.user_info = None
                self.client_nonce = None
                return True
            return False
        except Exception:
            return False
    
    def cancel_polling(self):
        """取消轮询"""
        if self.is_polling:
            self.stop_polling_event.set()
    
    def start_polling_thread(self, timeout: int = POLL_TIMEOUT,
                            on_progress: Optional[Callable[[int], None]] = None):
        """
        在后台线程中启动轮询
        
        Args:
            timeout: 轮询超时时间
            on_progress: 进度回调函数
        """
        if self.polling_thread and self.polling_thread.is_alive():
            return
        
        self.polling_thread = Thread(
            target=self.poll_token,
            args=(timeout, on_progress),
            daemon=True
        )
        self.polling_thread.start()
    
    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        return self.token is not None and self.user_info is not None
    
    def get_user_info(self) -> Optional[Dict]:
        """获取用户信息"""
        return self.user_info
    
    def get_token(self) -> Optional[str]:
        """获取Token"""
        return self.token

    def get_feedback_url(self, soft_number: str) -> Optional[str]:
        """获取问题反馈页面链接"""
        try:
            url = f"{self.API_BASE_URL}{self.GET_FEEDBACK_URL_ENDPOINT}"
            response = requests.post(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") == 1 and data.get("data"):
                base_url = data["data"].get("url")
                if base_url:
                    return f"{base_url}{soft_number}"
                return None
            else:
                return None
        except Exception as e:
            print(f"获取反馈地址异常: {str(e)}")
            return None
    
    def set_token(self, token: str):
        """设置Token（用于恢复已保存的Token）"""
        self.token = token
        # 验证Token有效性
        if self.check_login():
            self._fetch_user_info()
            return True
        else:
            self.token = None
            return False
    
    def get_customize_url(self) -> Optional[str]:
        """获取软件定制页面链接"""
        try:
            url = f"{self.API_BASE_URL}/soft_desktop/get_custom_url"
            response = requests.post(url, timeout=5)
            result = response.json()
            if result.get("code") == 1 and result.get("data"):
                return result["data"].get("url")
        except Exception as e:
            print(f"获取定制链接失败: {str(e)}")
        return None
    
    def get_device_id(self) -> str:
        """获取设备ID（机器码）- 与demo.py保持一致"""
        import platform
        import subprocess
        
        hardware_infos = []
        
        # 1. CPU序列号
        system = platform.system()
        try:
            if system == "Windows":
                result = subprocess.check_output(
                    'wmic cpu get ProcessorId',
                    shell=True,
                    text=True,
                    stderr=subprocess.DEVNULL
                )
                lines = result.strip().split('\n')
                if len(lines) >= 2:
                    cpu_serial = lines[1].strip()
                    if cpu_serial:
                        hardware_infos.append(cpu_serial)
            elif system == "Linux":
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if line.startswith('serial'):
                            cpu_serial = line.split(':')[1].strip()
                            hardware_infos.append(cpu_serial)
                            break
            elif system == "Darwin":
                result = subprocess.check_output(
                    'sysctl -n machdep.cpu.core_count',
                    shell=True,
                    text=True,
                    stderr=subprocess.DEVNULL
                )
                hardware_infos.append(result.strip())
        except Exception:
            pass
        
        # 2. MAC地址
        mac_num = hex(uuid.getnode()).replace('0x', '').upper()
        mac = '-'.join([mac_num[i:i+2] for i in range(0, 11, 2)])
        hardware_infos.append(mac)
        
        # 3. 主板序列号（Windows）
        if system == "Windows":
            try:
                result = subprocess.check_output(
                    'wmic baseboard get SerialNumber',
                    shell=True,
                    text=True,
                    stderr=subprocess.DEVNULL
                )
                lines = result.strip().split('\n')
                if len(lines) >= 2:
                    board_serial = lines[1].strip()
                    if board_serial:
                        hardware_infos.append(board_serial)
            except Exception:
                pass
        
        # 组合所有信息并哈希
        combined = '|'.join(hardware_infos)
        device_id = hashlib.sha256(combined.encode('utf-8')).hexdigest()
        return device_id
    
    def check_need_auth_code(self, soft_number: str = SOFTWARE_ID) -> tuple[bool, Optional[str]]:
        """
        检查是否需要获取授权码
        
        Args:
            soft_number: 软件编号
            
        Returns:
            tuple: (is_need_auth_code, auth_code_url)
        """
        try:
            url = f"{self.API_BASE_URL}/soft_desktop/check_get_auth_code"
            device_id = self.get_device_id()
            data = {
                "device_id": device_id,
                "soft_number": soft_number
            }
            
            response = requests.post(url, data=data, timeout=5)
            response.raise_for_status()
            
            result = response.json()
            if result.get("code") == 1 and result.get("data"):
                is_need = result["data"].get("is_need_auth_code", 0)
                auth_url = result["data"].get("auth_code_url")
                return is_need == 1, auth_url
            
            return False, None
        except requests.Timeout:
            print("检查授权码需求超时，跳过授权检查")
            return False, None
        except Exception as e:
            print(f"检查授权码需求失败: {str(e)}")
            return False, None
    
    def verify_auth_code(self, auth_code: str, soft_number: str = SOFTWARE_ID) -> bool:
        """
        验证授权码
        
        Args:
            auth_code: 授权码
            soft_number: 软件编号
            
        Returns:
            bool: 授权码有效返回True，无效或过期返回False
        """
        try:
            url = f"{self.API_BASE_URL}/soft_desktop/check_auth_code_valid"
            device_id = self.get_device_id()
            data = {
                "device_id": device_id,
                "soft_number": soft_number,
                "auth_code": auth_code
            }
            
            response = requests.post(url, data=data, timeout=5)
            response.raise_for_status()
            
            result = response.json()
            if result.get("code") == 1 and result.get("data"):
                status = result["data"].get("auth_code_status", 0)
                return status == 1
            
            return False
        except requests.Timeout:
            print("验证授权码超时")
            return False
        except Exception as e:
            print(f"验证授权码失败: {str(e)}")
            return False
    
    def get_auth_code_url(self, soft_number: str = SOFTWARE_ID) -> Optional[str]:
        """
        获取授权码获取页面URL
        
        Args:
            soft_number: 软件编号
            
        Returns:
            str: 授权码页面URL，失败返回None
        """
        try:
            is_need, auth_url = self.check_need_auth_code(soft_number)
            if not auth_url:
                return None
            
            device_id = self.get_device_id()
            separator = "&" if "?" in auth_url else "?"
            full_url = f"{auth_url}{separator}device_id={device_id}&software_code={soft_number}"
            return full_url
        except Exception as e:
            print(f"获取授权码URL失败: {str(e)}")
            return None
    
    def _get_token_storage(self):
        """获取Token存储实例（延迟初始化避免循环导入）"""
        if self.token_storage is None:
            from core.token_storage import TokenStorage
            self.token_storage = TokenStorage()
        return self.token_storage
    
    def save_auth_code(self, auth_code: str) -> bool:
        """
        保存授权码到本地存储
        
        Args:
            auth_code: 授权码
            
        Returns:
            bool: 保存成功返回True
        """
        try:
            self.auth_code = auth_code
            storage = self._get_token_storage()
            return storage.save_auth_code(auth_code)
        except Exception as e:
            print(f"保存授权码失败: {str(e)}")
            return False
    
    def load_auth_code(self) -> Optional[str]:
        """
        从本地存储加载授权码
        
        Returns:
            str: 授权码，不存在返回None
        """
        try:
            if self.auth_code:
                return self.auth_code
            
            storage = self._get_token_storage()
            self.auth_code = storage.load_auth_code()
            return self.auth_code
        except Exception as e:
            print(f"加载授权码失败: {str(e)}")
            return None
    
    def clear_auth_code(self) -> bool:
        """
        清除本地存储的授权码
        
        Returns:
            bool: 清除成功返回True
        """
        try:
            self.auth_code = None
            storage = self._get_token_storage()
            return storage.clear_auth_code()
        except Exception as e:
            print(f"清除授权码失败: {str(e)}")
            return False
    
    def is_auth_code_valid(self, soft_number: str = SOFTWARE_ID) -> bool:
        """
        检查本地缓存的授权码是否有效
        
        Args:
            soft_number: 软件编号
            
        Returns:
            bool: 授权码有效返回True
        """
        auth_code = self.load_auth_code()
        if not auth_code:
            return False
        
        # 验证授权码是否仍然有效
        return self.verify_auth_code(auth_code, soft_number)
