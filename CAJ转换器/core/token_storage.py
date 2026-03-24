"""
Token持久化存储模块
负责Token的保存和恢复
"""
from PyQt6.QtCore import QSettings
from typing import Optional


class TokenStorage:
    """Token存储管理"""
    
    def __init__(self, org_name: str = "KunqiongAI", app_name: str = "CAJConverter"):
        """
        初始化Token存储
        
        Args:
            org_name: 组织名称
            app_name: 应用名称
        """
        self.settings = QSettings(org_name, app_name)
    
    def save_token(self, token: str) -> bool:
        """
        保存Token
        
        Args:
            token: 要保存的Token
            
        Returns:
            bool: 保存成功返回True
        """
        try:
            self.settings.setValue("auth/token", token)
            self.settings.sync()
            return True
        except Exception:
            return False
    
    def load_token(self) -> Optional[str]:
        """
        加载Token
        
        Returns:
            str: 保存的Token，不存在返回None
        """
        try:
            token = self.settings.value("auth/token", None)
            return token if token else None
        except Exception:
            return None
    
    def clear_token(self) -> bool:
        """
        清除Token
        
        Returns:
            bool: 清除成功返回True
        """
        try:
            self.settings.remove("auth/token")
            self.settings.sync()
            return True
        except Exception:
            return False
    
    def save_user_info(self, user_info: dict) -> bool:
        """
        保存用户信息
        
        Args:
            user_info: 用户信息字典
            
        Returns:
            bool: 保存成功返回True
        """
        try:
            import json
            user_info_json = json.dumps(user_info)
            self.settings.setValue("auth/user_info", user_info_json)
            self.settings.sync()
            return True
        except Exception:
            return False
    
    def load_user_info(self) -> Optional[dict]:
        """
        加载用户信息
        
        Returns:
            dict: 保存的用户信息，不存在返回None
        """
        try:
            import json
            user_info_json = self.settings.value("auth/user_info", None)
            if user_info_json:
                return json.loads(user_info_json)
            return None
        except Exception:
            return None
    
    def clear_user_info(self) -> bool:
        """
        清除用户信息
        
        Returns:
            bool: 清除成功返回True
        """
        try:
            self.settings.remove("auth/user_info")
            self.settings.sync()
            return True
        except Exception:
            return False
    
    def save_auth_code(self, auth_code: str) -> bool:
        """
        保存授权码
        
        Args:
            auth_code: 要保存的授权码
            
        Returns:
            bool: 保存成功返回True
        """
        try:
            self.settings.setValue("auth/auth_code", auth_code)
            self.settings.sync()
            return True
        except Exception:
            return False
    
    def load_auth_code(self) -> Optional[str]:
        """
        加载授权码
        
        Returns:
            str: 保存的授权码，不存在返回None
        """
        try:
            auth_code = self.settings.value("auth/auth_code", None)
            return auth_code if auth_code else None
        except Exception:
            return None
    
    def clear_auth_code(self) -> bool:
        """
        清除授权码
        
        Returns:
            bool: 清除成功返回True
        """
        try:
            self.settings.remove("auth/auth_code")
            self.settings.sync()
            return True
        except Exception:
            return False
    
    def clear_all(self) -> bool:
        """
        清除所有认证信息
        
        Returns:
            bool: 清除成功返回True
        """
        return self.clear_token() and self.clear_user_info() and self.clear_auth_code()
