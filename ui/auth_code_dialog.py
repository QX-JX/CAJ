"""
授权码验证对话框
根据设计图重构的现代化界面
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QWidget, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter, QBrush, QColor, QPainterPath
import os
import sys
import webbrowser
import requests


def get_icon_path(icon_name: str) -> str:
    """获取图标文件路径，支持打包后的环境"""
    if getattr(sys, 'frozen', False):
        # 1. Onefile 模式：资源解压到临时目录
        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, icon_name)
            if os.path.exists(icon_path):
                return icon_path
        
        # 2. Onedir 模式：资源在 _internal 目录或当前目录
        base_dir = os.path.dirname(sys.executable)
        
        # 尝试在 _internal 目录查找 (PyInstaller 6+)
        internal_path = os.path.join(base_dir, "_internal", icon_name)
        if os.path.exists(internal_path):
            return internal_path
            
        # 尝试在根目录查找
        root_path = os.path.join(base_dir, icon_name)
        if os.path.exists(root_path):
            return root_path
            
        return None
    else:
        # 开发环境
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_dir, icon_name)
        return icon_path if os.path.exists(icon_path) else None


class AuthCodeDialog(QDialog):
    """授权码验证对话框 - 现代化白色主题"""
    auth_success = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("鲲穹AI工具箱·软件授权验证")
        self.setFixedSize(480, 420)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.set_window_icon()
        self.setup_ui()
        self._drag_pos = None
    
    def set_window_icon(self):
        icon_path = get_icon_path("CAJ转换器.ico")
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建带圆角的容器
        self.container = QFrame()
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            QFrame#container {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #e8e8e8;
            }
        """)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(32, 24, 32, 32)
        container_layout.setSpacing(16)
        
        # 顶部标题栏
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        
        # 图标
        icon_label = QLabel()
        icon_label.setFixedSize(36, 36)
        icon_path = get_icon_path("鲲穹01.ico")
        if icon_path:
            pixmap = QPixmap(icon_path).scaled(
                36, 36, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            icon_label.setPixmap(pixmap)
        else:
            icon_label.setText("🐋")
            icon_label.setFont(QFont("Segoe UI Emoji", 20))
        header_layout.addWidget(icon_label)
        
        # 标题文本
        title_label = QLabel("鲲穹AI工具箱·软件授权验证")
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1890ff;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(28, 28)
        close_btn.setFont(QFont("Arial", 18))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #999999;
            }
            QPushButton:hover {
                color: #333333;
            }
        """)
        close_btn.clicked.connect(self.reject)
        header_layout.addWidget(close_btn)
        
        container_layout.addLayout(header_layout)
        container_layout.addSpacing(8)
        
        # 描述文本
        desc_label = QLabel(
            "您当前安装的工具为鲲穹AI工具箱生态应用，需通过工具箱授权码\n"
            "完成激活，以启用完整功能。"
        )
        desc_label.setFont(QFont("Microsoft YaHei", 10))
        desc_label.setStyleSheet("color: #666666; line-height: 1.6;")
        desc_label.setWordWrap(True)
        container_layout.addWidget(desc_label)
        
        container_layout.addSpacing(8)
        
        # 输入框标签
        input_label = QLabel("请输入授权码")
        input_label.setFont(QFont("Microsoft YaHei", 10))
        input_label.setStyleSheet("color: #333333;")
        container_layout.addWidget(input_label)
        
        # 授权码输入框
        self.auth_code_input = QLineEdit()
        self.auth_code_input.setPlaceholderText("请输入授权码")
        self.auth_code_input.setFixedHeight(52)
        self.auth_code_input.setFont(QFont("Microsoft YaHei", 11))
        self.auth_code_input.setStyleSheet("""
            QLineEdit {
                background-color: #f5f5f5;
                border: none;
                border-radius: 8px;
                color: #333333;
                padding: 0px 16px;
            }
            QLineEdit:focus {
                background-color: #f0f0f0;
                border: 1px solid #1890ff;
            }
            QLineEdit::placeholder {
                color: #999999;
            }
        """)
        container_layout.addWidget(self.auth_code_input)
        
        container_layout.addSpacing(16)
        
        # 验证按钮 - 青绿色渐变
        verify_btn = QPushButton("验证授权")
        verify_btn.setFixedHeight(48)
        verify_btn.setFont(QFont("Microsoft YaHei", 13, QFont.Weight.Bold))
        verify_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        verify_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1890ff, stop:1 #40a9ff
                );
                border: none;
                border-radius: 8px;
                color: white;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #096dd9, stop:1 #1890ff
                );
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0050b3, stop:1 #096dd9
                );
            }
        """)
        verify_btn.clicked.connect(self.verify_auth_code)
        container_layout.addWidget(verify_btn)
        
        container_layout.addSpacing(16)
        
        # 底部链接
        link_layout = QHBoxLayout()
        link_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        link_layout.setSpacing(8)
        
        link_label = QLabel("还没有授权码？")
        link_label.setFont(QFont("Microsoft YaHei", 10))
        link_label.setStyleSheet("color: #999999;")
        link_layout.addWidget(link_label)
        
        get_code_btn = QPushButton("点击获取")
        get_code_btn.setFont(QFont("Microsoft YaHei", 10))
        get_code_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        get_code_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #1890ff;
            }
            QPushButton:hover {
                color: #40a9ff;
                text-decoration: underline;
            }
        """)
        get_code_btn.clicked.connect(self.open_get_auth_code_page)
        link_layout.addWidget(get_code_btn)
        
        container_layout.addLayout(link_layout)
        container_layout.addStretch()
        
        main_layout.addWidget(self.container)

    def paintEvent(self, event):
        """绘制阴影效果"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        shadow_color = QColor(0, 0, 0, 30)
        for i in range(10):
            path = QPainterPath()
            path.addRoundedRect(
                i, i, 
                self.width() - 2*i, self.height() - 2*i, 
                12, 12
            )
            painter.fillPath(path, QBrush(shadow_color))
    
    def mousePressEvent(self, event):
        """鼠标按下事件 - 用于拖动窗口"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 用于拖动窗口"""
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        self._drag_pos = None
    
    def verify_auth_code(self):
        """验证授权码"""
        auth_code = self.auth_code_input.text().strip()
        
        if not auth_code:
            self.show_message("提示", "请输入授权码", "warning")
            return
        
        try:
            from core.auth_manager import AuthManager
            auth_manager = AuthManager()
            
            if auth_manager.verify_auth_code(auth_code):
                auth_manager.save_auth_code(auth_code)
                self.show_message("成功", "授权码验证成功！", "success")
                self.auth_success.emit()
                self.accept()
            else:
                self.show_message("失败", "授权码无效或已过期，请重新输入", "error")
        except Exception as e:
            self.show_message("错误", f"验证授权码时出错: {str(e)}", "error")
    
    def show_message(self, title: str, message: str, msg_type: str = "info"):
        """显示消息提示框"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        
        if msg_type == "success":
            msg_box.setIcon(QMessageBox.Icon.Information)
        elif msg_type == "warning":
            msg_box.setIcon(QMessageBox.Icon.Warning)
        elif msg_type == "error":
            msg_box.setIcon(QMessageBox.Icon.Critical)
        else:
            msg_box.setIcon(QMessageBox.Icon.Information)
        
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #ffffff;
            }
            QMessageBox QLabel {
                color: #333333;
                font-size: 12px;
            }
            QPushButton {
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 20px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
        """)
        msg_box.exec()
    
    def open_get_auth_code_page(self):
        """打开获取授权码页面，自动带上设备ID和软件编号"""
        try:
            from core.auth_manager import AuthManager
            
            auth_manager = AuthManager()
            
            # 获取设备ID
            device_id = auth_manager.get_device_id()
            soft_number = "10004"  # 软件编号
            
            # 调用API检查是否需要授权码，获取授权码页面URL
            check_url = "https://api-web.kunqiongai.com/soft_desktop/check_get_auth_code"
            data = {
                "device_id": device_id,
                "soft_number": soft_number
            }
            
            response = requests.post(check_url, data=data, timeout=5)
            result = response.json()
            
            if result.get("code") == 1 and result.get("data"):
                auth_code_url = result["data"].get("auth_code_url")
                if auth_code_url:
                    # 拼接设备ID和软件编号参数
                    full_url = f"{auth_code_url}?device_id={device_id}&software_code={soft_number}&soft_number={soft_number}"
                    webbrowser.open(full_url)
                else:
                    self.show_message("错误", "无法获取授权码页面链接", "error")
            else:
                self.show_message("错误", f"获取授权码页面失败: {result.get('msg', '未知错误')}", "error")
        except requests.Timeout:
            self.show_message("错误", "网络请求超时，请检查网络连接", "error")
        except Exception as e:
            self.show_message("错误", f"打开授权码页面时出错: {str(e)}", "error")
