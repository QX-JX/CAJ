"""
小型广告组件
"""
from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QPixmap, QFont
import requests
from typing import List
from core.ad_cache import AdCache

# 复用session
session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

# 创建全局缓存实例
ad_cache = AdCache()


class AdSmallWorker(QThread):
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


class AdSmallBanner(QWidget):
    """小型横幅广告 - 4:1比例，用于标题栏"""
    
    def __init__(self, soft_number: str = "10004", ad_position: str = "adv_position_01", 
                 width: int = 120, parent=None):
        super().__init__(parent)
        self.soft_number = soft_number
        self.ad_position = ad_position
        self.target_width = width
        self.target_height = width // 4  # 4:1比例
        self.ads = []
        self.ad_pixmap = None
        self.load_worker = None
        
        self.setup_ui()
        self.load_ads()
    
    def setup_ui(self):
        self.setFixedSize(self.target_width, self.target_height)
        
        self.ad_label = QLabel(self)
        self.ad_label.setGeometry(0, 0, self.target_width, self.target_height)
        self.ad_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ad_label.setStyleSheet("background-color: transparent; border-radius: 4px;")
        self.ad_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ad_label.mousePressEvent = self.on_ad_clicked
    
    def load_ads(self):
        self.load_worker = AdSmallWorker(self.soft_number, [self.ad_position])
        self.load_worker.ads_loaded.connect(self.on_ads_loaded)
        self.load_worker.start()
    
    @pyqtSlot(list, object)
    def on_ads_loaded(self, ads: list, first_pixmap):
        self.ads = ads
        if self.ads and first_pixmap and not first_pixmap.isNull():
            self.ad_pixmap = first_pixmap
            self.show_pixmap(first_pixmap)
    
    def _load_image(self, ad_url: str):
        try:
            response = session.get(ad_url, timeout=3)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                self.ad_pixmap = pixmap
                self.show_pixmap(pixmap)
        except:
            pass
    
    def show_pixmap(self, pixmap: QPixmap):
        scaled = pixmap.scaled(
            self.target_width, self.target_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.ad_label.setPixmap(scaled)
    
    def on_ad_clicked(self, event):
        if self.ads:
            url = self.ads[0].get("target_url", "")
            if url:
                import webbrowser
                webbrowser.open(url)


class AdSideCarousel(QWidget):
    """侧边栏广告轮播 - 2:3比例"""
    
    def __init__(self, soft_number: str = "10004", ad_positions: List[str] = None,
                 width: int = 120, parent=None):
        super().__init__(parent)
        self.soft_number = soft_number
        self.ad_positions = ad_positions or ["adv_position_04", "adv_position_05"]
        self.target_width = width
        self.target_height = int(width * 1.5)  # 2:3比例
        self.ads = []
        self.current_index = 0
        self.ad_pixmaps = {}
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_ad)
        self.load_worker = None
        
        self.setup_ui()
        self.load_ads()
    
    def setup_ui(self):
        self.setFixedSize(self.target_width, self.target_height)
        
        # 广告图片
        self.ad_label = QLabel(self)
        self.ad_label.setGeometry(0, 0, self.target_width, self.target_height)
        self.ad_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ad_label.setStyleSheet("background-color: #f5f5f5; border-radius: 6px;")
        self.ad_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ad_label.mousePressEvent = self.on_ad_clicked
        
        # 指示器
        self.page_indicator = QLabel("1/2", self)
        self.page_indicator.setFont(QFont("Microsoft YaHei", 9))
        self.page_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_indicator.setFixedSize(32, 18)
        self.page_indicator.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 0.3);
                border-radius: 3px;
                color: white;
            }
        """)
        self.page_indicator.move(self.target_width - 38, 6)
        self.page_indicator.hide()
        
        self.setMouseTracking(True)
    
    def load_ads(self):
        self.load_worker = AdSmallWorker(self.soft_number, self.ad_positions)
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
            from threading import Thread
            for i, ad in enumerate(self.ads):
                if i == 0:  # 跳过第一张，已经加载了
                    continue
                ad_url = ad.get("adv_url", "")
                if ad_url and ad_url not in self.ad_pixmaps:
                    Thread(target=self._load_image, args=(ad_url,), daemon=True).start()
            
            self.display_ad(0)
            self.timer.start(5000)
    
    def display_ad(self, index: int):
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
        max_retries = 2
        for attempt in range(max_retries):
            try:
                print(f"AdSideCarousel: 开始加载图片 {ad_url} (尝试 {attempt + 1}/{max_retries})")
                response = session.get(ad_url, timeout=8)
                if response.status_code == 200:
                    pixmap = QPixmap()
                    pixmap.loadFromData(response.content)
                    self.ad_pixmaps[ad_url] = pixmap
                    print(f"AdSideCarousel: 图片加载成功 {ad_url}")
                    
                    # 如果是当前显示的图片，立即更新
                    if self.ads and self.current_index < len(self.ads):
                        current_url = self.ads[self.current_index].get("adv_url", "")
                        if current_url == ad_url:
                            print(f"AdSideCarousel: 显示图片 {ad_url}")
                            self.show_pixmap(pixmap)
                    return
                else:
                    print(f"AdSideCarousel: 图片加载失败，状态码: {response.status_code}")
            except Exception as e:
                print(f"AdSideCarousel: 图片加载异常 (尝试 {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(1)  # 等待1秒后重试
    
    def show_pixmap(self, pixmap: QPixmap):
        scaled = pixmap.scaled(
            self.target_width, self.target_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.ad_label.setPixmap(scaled)
    
    def next_ad(self):
        if self.ads:
            self.display_ad((self.current_index + 1) % len(self.ads))
    
    def on_ad_clicked(self, event):
        if self.current_index < len(self.ads):
            url = self.ads[self.current_index].get("target_url", "")
            if url:
                import webbrowser
                webbrowser.open(url)
    
    def enterEvent(self, event):
        self.page_indicator.show()
    
    def leaveEvent(self, event):
        self.page_indicator.hide()
