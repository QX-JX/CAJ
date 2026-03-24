import os
import json
from PyQt6.QtCore import QUrl, QByteArray
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt6.QtGui import QPixmap


class AdManager:
    """广告管理器"""
    
    def __init__(self):
        self.network_manager = QNetworkAccessManager()
        self.ads_data = []
        
    def load_ads_from_api(self, api_response_data):
        """从API响应数据加载广告
        
        Args:
            api_response_data: API返回的广告数据，格式如：
            {
                "code": 200,
                "msg": "success",
                "data": [
                    {
                        "adv_position": "adv_position_02",
                        "adv_url": "https://image.kunqiongai.com/adv/demo1.png",
                        "target_url": "http://111.229.158.50:1388/",
                        "width": 1920,
                        "height": 480
                    },
                    {
                        "adv_position": "adv_position_03",
                        "adv_url": "https://image.kunqiongai.com/adv/demo2.png",
                        "target_url": "http://111.229.158.50:1388/",
                        "width": 1920,
                        "height": 480
                    }
                ]
            }
        """
        try:
            if isinstance(api_response_data, dict):
                if api_response_data.get("code") == 200:
                    data = api_response_data.get("data", [])
                    if isinstance(data, list):
                        self.ads_data = data
                        return True
            return False
        except Exception as e:
            print(f"加载广告数据失败: {e}")
            return False
    
    def get_ads_for_position(self, position_prefix="adv_position_"):
        """获取指定位置的广告
        
        Args:
            position_prefix: 广告位置前缀
            
        Returns:
            list: 符合条件的广告数据
        """
        return [ad for ad in self.ads_data if ad.get("adv_position", "").startswith(position_prefix)]
    
    def download_ad_image(self, image_url, callback):
        """下载广告图片
        
        Args:
            image_url: 图片URL
            callback: 下载完成后的回调函数，参数为(QPixmap, str)
        """
        try:
            request = QNetworkRequest(QUrl(image_url))
            reply = self.network_manager.get(request)
            
            def on_finished():
                if reply.error() == QNetworkReply.NetworkError.NoError:
                    data = reply.readAll()
                    pixmap = QPixmap()
                    if pixmap.loadFromData(data):
                        callback(pixmap, image_url)
                    else:
                        callback(None, image_url)
                else:
                    print(f"下载图片失败: {reply.errorString()}")
                    callback(None, image_url)
                reply.deleteLater()
            
            reply.finished.connect(on_finished)
            
        except Exception as e:
            print(f"下载图片异常: {e}")
            callback(None, image_url)
    
    def create_fallback_ad(self, text="广告位置", bg_gradient=None):
        """创建备用广告（当图片加载失败时使用）
        
        Args:
            text: 显示文本
            bg_gradient: 背景渐变色，默认为蓝紫色渐变
            
        Returns:
            str: CSS样式字符串
        """
        if bg_gradient is None:
            bg_gradient = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2)"
        
        return f"""
            QLabel {{
                background: {bg_gradient};
                color: white;
                font-family: "Microsoft YaHei";
                font-size: 18px;
                font-weight: bold;
                border-radius: 8px;
                padding: 20px;
            }}
        """
    
    def get_local_ad_path(self, ad_position):
        """获取本地广告图片路径
        
        Args:
            ad_position: 广告位置，如 "adv_position_02"
            
        Returns:
            str: 本地图片路径，如果不存在则返回空字符串
        """
        # 构建可能的图片文件名
        possible_names = [
            f"{ad_position}.png",
            f"{ad_position}.jpg",
            f"{ad_position}.jpeg",
            f"adv_{ad_position.split('_')[-1]}.png",
            f"adv_{ad_position.split('_')[-1]}.jpg"
        ]
        
        # 检查资源目录
        base_dir = os.path.dirname(os.path.abspath(__file__))
        resources_dir = os.path.join(base_dir, "resources", "ads")
        
        for filename in possible_names:
            full_path = os.path.join(resources_dir, filename)
            if os.path.exists(full_path):
                return full_path
        
        return ""
    
    def create_sample_ads(self):
        """创建示例广告数据（用于测试）"""
        return [
            {
                "adv_position": "adv_position_02",
                "adv_url": "",
                "target_url": "https://example.com/ad1",
                "width": 1920,
                "height": 480,
                "fallback_text": "广告位置 02",
                "fallback_style": self.create_fallback_ad("广告位置 02", 
                    "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2)")
            },
            {
                "adv_position": "adv_position_03", 
                "adv_url": "",
                "target_url": "https://example.com/ad2",
                "width": 1920,
                "height": 480,
                "fallback_text": "广告位置 03",
                "fallback_style": self.create_fallback_ad("广告位置 03",
                    "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f093fb, stop:1 #f5576c)")
            }
        ]