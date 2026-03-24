from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QBrush, QColor, QLinearGradient, QFont
import os


class AdCarousel(QWidget):
    """轮播图广告组件"""
    
    ad_clicked = pyqtSignal(str)  # 广告点击信号，传递目标URL
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.advertisements = []
        self.current_index = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_ad)
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 轮播图主体区域
        self.carousel_widget = QWidget()
        self.carousel_widget.setFixedHeight(200)  # 4:1比例，宽度自适应
        self.carousel_widget.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border-radius: 8px;
            }
        """)
        
        carousel_layout = QVBoxLayout(self.carousel_widget)
        carousel_layout.setContentsMargins(0, 0, 0, 0)
        carousel_layout.setSpacing(0)
        
        # 图片堆叠区域
        self.image_stack = QStackedWidget()
        carousel_layout.addWidget(self.image_stack)
        
        # 指示器区域
        indicator_widget = QWidget()
        indicator_widget.setFixedHeight(30)
        indicator_layout = QHBoxLayout(indicator_widget)
        indicator_layout.setContentsMargins(0, 0, 10, 0)
        indicator_layout.setSpacing(5)
        indicator_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.indicators = []
        self.indicator_layout = indicator_layout
        carousel_layout.addWidget(indicator_widget)
        
        main_layout.addWidget(self.carousel_widget)
        
        # 设置默认背景
        self.set_default_background()
        
    def set_default_background(self):
        """设置默认背景"""
        default_label = QLabel("广告加载中...")
        default_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        default_label.setStyleSheet("""
            QLabel {
                color: #999999;
                font-family: "Microsoft YaHei";
                font-size: 14px;
                background-color: #f5f5f5;
                border-radius: 8px;
            }
        """)
        self.image_stack.addWidget(default_label)
        
    def add_advertisement(self, image_path: str, target_url: str = ""):
        """添加广告
        Args:
            image_path: 图片路径或URL
            target_url: 点击跳转URL
        """
        ad_widget = self.create_ad_widget(image_path, target_url)
        if ad_widget:
            self.advertisements.append({
                'widget': ad_widget,
                'url': target_url,
                'image_path': image_path
            })
            self.image_stack.addWidget(ad_widget)
            self.update_indicators()
            
            # 如果这是第一个广告，立即显示
            if len(self.advertisements) == 1:
                self.image_stack.setCurrentIndex(1)  # 跳过默认背景
                self.start_rotation()
    
    def create_ad_widget(self, image_path: str, target_url: str):
        """创建广告组件"""
        ad_label = QLabel()
        ad_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ad_label.setScaledContents(True)
        ad_label.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 设置图片
        pixmap = self.load_image(image_path)
        if pixmap:
            ad_label.setPixmap(pixmap)
        else:
            # 如果图片加载失败，创建渐变背景
            ad_label.setStyleSheet("""
                QLabel {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #667eea, stop:1 #764ba2);
                    border-radius: 8px;
                    color: white;
                    font-family: "Microsoft YaHei";
                    font-size: 18px;
                    font-weight: bold;
                }
            """)
            ad_label.setText("广告图片")
        
        # 添加点击事件
        if target_url:
            ad_label.mousePressEvent = lambda e, url=target_url: self.on_ad_clicked(url)
        
        return ad_label
    
    def load_image(self, image_path: str):
        """加载图片"""
        try:
            # 如果是网络图片，这里可以扩展支持网络加载
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    # 保持4:1比例缩放
                    return pixmap.scaled(
                        self.carousel_widget.width(),
                        self.carousel_widget.height(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
        except Exception as e:
            print(f"加载图片失败: {e}")
        return None
    
    def on_ad_clicked(self, url: str):
        """广告被点击"""
        self.ad_clicked.emit(url)
    
    def update_indicators(self):
        """更新指示器"""
        # 清除现有指示器
        for indicator in self.indicators:
            self.indicator_layout.removeWidget(indicator)
            indicator.deleteLater()
        self.indicators.clear()
        
        # 创建新指示器
        for i in range(len(self.advertisements)):
            indicator = QPushButton()
            indicator.setFixedSize(8, 8)
            indicator.setCursor(Qt.CursorShape.PointingHandCursor)
            indicator.setStyleSheet(f"""
                QPushButton {{
                    border: none;
                    border-radius: 4px;
                    background-color: {'#f97316' if i == self.current_index else '#d0d0d0'};
                }}
                QPushButton:hover {{
                    background-color: #f97316;
                }}
            """)
            indicator.clicked.connect(lambda checked, index=i: self.go_to_ad(index))
            self.indicators.append(indicator)
            self.indicator_layout.addWidget(indicator)
    
    def start_rotation(self, interval: int = 3000):
        """开始轮播
        Args:
            interval: 轮播间隔时间（毫秒）
        """
        if len(self.advertisements) > 1:
            self.timer.start(interval)
    
    def stop_rotation(self):
        """停止轮播"""
        self.timer.stop()
    
    def next_ad(self):
        """下一张广告"""
        if len(self.advertisements) <= 1:
            return
            
        self.current_index = (self.current_index + 1) % len(self.advertisements)
        self.image_stack.setCurrentIndex(self.current_index + 1)  # +1 跳过默认背景
        self.update_indicators()
    
    def previous_ad(self):
        """上一张广告"""
        if len(self.advertisements) <= 1:
            return
            
        self.current_index = (self.current_index - 1) % len(self.advertisements)
        self.image_stack.setCurrentIndex(self.current_index + 1)  # +1 跳过默认背景
        self.update_indicators()
    
    def go_to_ad(self, index: int):
        """跳转到指定广告"""
        if 0 <= index < len(self.advertisements):
            self.current_index = index
            self.image_stack.setCurrentIndex(self.current_index + 1)  # +1 跳过默认背景
            self.update_indicators()
    
    def resizeEvent(self, event):
        """处理大小变化事件"""
        super().resizeEvent(event)
        # 保持4:1比例
        new_height = self.width() // 4
        if new_height > 0:
            self.carousel_widget.setFixedHeight(min(new_height, 300))  # 最大高度限制为300
            
            # 重新加载图片以适应新尺寸
            for ad in self.advertisements:
                pixmap = self.load_image(ad['image_path'])
                if pixmap:
                    ad['widget'].setPixmap(pixmap)
    
    def clear_ads(self):
        """清除所有广告"""
        self.timer.stop()
        self.advertisements.clear()
        self.current_index = 0
        
        # 清除所有广告组件
        while self.image_stack.count() > 1:  # 保留默认背景
            widget = self.image_stack.widget(1)
            self.image_stack.removeWidget(widget)
            widget.deleteLater()
        
        self.image_stack.setCurrentIndex(0)  # 显示默认背景
        self.update_indicators()


class SimpleAdWidget(QWidget):
    """简单的广告组件，用于测试"""
    
    def __init__(self, text: str, bg_color: str = "#667eea", parent=None):
        super().__init__(parent)
        self.setup_ui(text, bg_color)
        
    def setup_ui(self, text: str, bg_color: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: white;
                font-family: "Microsoft YaHei";
                font-size: 18px;
                font-weight: bold;
                padding: 20px;
                border-radius: 8px;
            }}
        """)
        layout.addWidget(label)