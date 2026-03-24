"""
广告横幅组件 - 一比一复刻
"""
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QPixmap, QFont
import requests
from typing import List
from core.ad_cache import AdCache

# 创建全局session以复用连接
session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

# 创建全局缓存实例
ad_cache = AdCache()


class AdBannerWorker(QThread):
    """广告加载工作线程"""
    ads_loaded = pyqtSignal(list, object)  # 传递广告列表和第一张图片
    
    def __init__(self, soft_number: str, ad_positions: List[str]):
        super().__init__()
        self.soft_number = soft_number
        self.ad_positions = ad_positions
    
    def run(self):
        ads = []
        first_pixmap = None
        try:
            url = "https://api-web.kunqiongai.com/soft_desktop/get_adv"
            for position in self.ad_positions:
                try:
                    data = {"soft_number": self.soft_number, "adv_position": position}
                    response = session.post(url, data=data, timeout=3)
                    result = response.json()
                    if result.get("code") == 1 and result.get("data"):
                        ads.extend(result["data"])
                except:
                    pass
            
            # 立即加载第一张图片（优先从缓存）
            if ads:
                first_ad_url = ads[0].get("adv_url", "")
                if first_ad_url:
                    # 先尝试从缓存加载
                    cached_data = ad_cache.get_cached_image(first_ad_url)
                    if cached_data:
                        first_pixmap = QPixmap()
                        first_pixmap.loadFromData(cached_data)
                    else:
                        # 缓存未命中，从网络加载
                        try:
                            img_response = session.get(first_ad_url, timeout=8)
                            if img_response.status_code == 200:
                                image_data = img_response.content
                                first_pixmap = QPixmap()
                                first_pixmap.loadFromData(image_data)
                                # 保存到缓存
                                ad_cache.save_image(first_ad_url, image_data)
                        except:
                            pass
        except:
            pass
        
        self.ads_loaded.emit(ads, first_pixmap)


class AdBanner(QWidget):
    """广告横幅 - 一比一复刻"""
    
    # 添加加载完成信号
    loaded = pyqtSignal()
    
    def __init__(self, soft_number: str = "10004", ad_positions: List[str] = None, parent=None):
        super().__init__(parent)
        self.soft_number = soft_number
        self.ad_positions = ad_positions or ["adv_position_02", "adv_position_03"]
        self.ads = []
        self.current_index = 0
        self.ad_pixmaps = {}
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_ad)
        self.load_worker = None
        
        self.setFixedWidth(980)
        self.setMinimumHeight(200)
        
        self.setup_ui()
        self.load_ads()
    
    def setup_ui(self):
        """设置UI - 使用绝对定位"""
        # 广告图片
        self.ad_label = QLabel(self)
        self.ad_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ad_label.setGeometry(0, 0, 980, 200)
        self.ad_label.setStyleSheet("background-color: #f0f5ff; border-radius: 12px;")
        self.ad_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ad_label.mousePressEvent = self.on_ad_clicked
        
        # 左按钮 - 圆形，半透明，在图片左边缘
        self.prev_btn = QPushButton("‹", self)
        self.prev_btn.setFixedSize(36, 36)
        self.prev_btn.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        self.prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.7);
                border: none;
                border-radius: 18px;
                color: #666666;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.9);
                color: #333333;
            }
        """)
        self.prev_btn.clicked.connect(self.prev_ad)
        self.prev_btn.hide()
        
        # 右按钮 - 圆形，半透明，在图片右边缘
        self.next_btn = QPushButton("›", self)
        self.next_btn.setFixedSize(36, 36)
        self.next_btn.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.7);
                border: none;
                border-radius: 18px;
                color: #666666;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.9);
                color: #333333;
            }
        """)
        self.next_btn.clicked.connect(self.next_ad)
        self.next_btn.hide()
        
        # 指示器 - 右上角，半透明背景
        self.page_indicator = QLabel("1/2", self)
        self.page_indicator.setFont(QFont("Microsoft YaHei", 10))
        self.page_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_indicator.setFixedSize(40, 24)
        self.page_indicator.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 0.3);
                border-radius: 4px;
                color: white;
            }
        """)
        self.page_indicator.hide()
        
        self.setMouseTracking(True)
    
    def resizeEvent(self, event):
        """调整子控件位置"""
        super().resizeEvent(event)
        h = self.ad_label.height()
        
        # 左按钮 - 左边缘中间
        self.prev_btn.move(10, (h - 36) // 2)
        
        # 右按钮 - 右边缘中间
        self.next_btn.move(980 - 46, (h - 36) // 2)
        
        # 指示器 - 右上角
        self.page_indicator.move(980 - 50, 10)
    
    def load_ads(self):
        """加载广告"""
        self.load_worker = AdBannerWorker(self.soft_number, self.ad_positions)
        self.load_worker.ads_loaded.connect(self.on_ads_loaded)
        self.load_worker.start()
    
    @pyqtSlot(list, object)
    def on_ads_loaded(self, ads: list, first_pixmap):
        """广告加载完成"""
        self.ads = ads
        if self.ads:
            # 如果第一张图片已加载，立即显示
            if first_pixmap and not first_pixmap.isNull():
                first_ad_url = self.ads[0].get("adv_url", "")
                self.ad_pixmaps[first_ad_url] = first_pixmap
                self.show_pixmap(first_pixmap)
            
            # 异步预加载其他图片
            self.preload_other_images()
            self.display_ad(0)
            self.timer.start(5000)
        
        # 发出加载完成信号
        self.loaded.emit()
    
    def preload_other_images(self):
        """预加载其他广告图片"""
        from threading import Thread
        for i, ad in enumerate(self.ads):
            if i == 0:  # 跳过第一张，已经加载了
                continue
            ad_url = ad.get("adv_url", "")
            if ad_url and ad_url not in self.ad_pixmaps:
                Thread(target=self._load_image, args=(ad_url,), daemon=True).start()
    
    def display_ad(self, index: int):
        """显示广告"""
        if not self.ads or index >= len(self.ads):
            return
        
        self.current_index = index
        ad = self.ads[index]
        ad_url = ad.get("adv_url", "")
        
        self.page_indicator.setText(f"{index + 1}/{len(self.ads)}")
        
        if ad_url in self.ad_pixmaps:
            self.show_pixmap(self.ad_pixmaps[ad_url])
            return
        
        from threading import Thread
        Thread(target=self._load_image, args=(ad_url,), daemon=True).start()
    
    def _load_image(self, ad_url: str):
        """加载图片"""
        try:
            response = session.get(ad_url, timeout=3)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                self.ad_pixmaps[ad_url] = pixmap
                
                # 如果是当前显示的图片，立即更新
                if self.ads and self.current_index < len(self.ads):
                    current_url = self.ads[self.current_index].get("adv_url", "")
                    if current_url == ad_url:
                        self.show_pixmap(pixmap)
        except:
            pass
    
    def show_pixmap(self, pixmap: QPixmap):
        """显示图片"""
        scaled = pixmap.scaledToWidth(980, Qt.TransformationMode.SmoothTransformation)
        self.ad_label.setPixmap(scaled)
        self.ad_label.setFixedHeight(scaled.height())
        self.setFixedHeight(scaled.height())
        
        # 更新按钮位置
        h = scaled.height()
        self.prev_btn.move(10, (h - 36) // 2)
        self.next_btn.move(980 - 46, (h - 36) // 2)
        self.page_indicator.move(980 - 50, 10)
    
    def next_ad(self):
        if self.ads:
            self.display_ad((self.current_index + 1) % len(self.ads))
    
    def prev_ad(self):
        if self.ads:
            self.display_ad((self.current_index - 1) % len(self.ads))
    
    def on_ad_clicked(self, event):
        if self.current_index < len(self.ads):
            url = self.ads[self.current_index].get("target_url", "")
            if url:
                import webbrowser
                webbrowser.open(url)
    
    def enterEvent(self, event):
        self.prev_btn.show()
        self.next_btn.show()
        self.page_indicator.show()
    
    def leaveEvent(self, event):
        self.prev_btn.hide()
        self.next_btn.hide()
        self.page_indicator.hide()
