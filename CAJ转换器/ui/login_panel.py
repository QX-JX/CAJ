"""
登录面板UI组件
包含用户按钮、登录对话框、用户信息面板等
"""
from PyQt6.QtWidgets import (
    QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QDialog, QProgressBar, QMessageBox, QFrame,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal, QSettings
from PyQt6.QtGui import QFont, QIcon, QPixmap, QColor, QPainter, QBrush, QFontMetrics
import os
import sys
import webbrowser
from core.auth_manager import AuthManager
from core.utils import get_icon_path
from core.i18n_manager import tr


class UserButton(QPushButton):
    """右上角用户按钮"""
    
    login_clicked = pyqtSignal()
    user_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_logged_in = False
        self.user_info = None
        self.setMinimumSize(100, 36) # 改为最小尺寸
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setup_ui()
        self.update_state(False)
    
    def setup_ui(self):
        """设置UI"""
        self.setFont(QFont("Microsoft YaHei", 11))
        self.clicked.connect(self.on_clicked)
    
    def on_clicked(self):
        """按钮点击事件"""
        if self.is_logged_in:
            self.user_clicked.emit()
        else:
            self.login_clicked.emit()
    
    def update_state(self, logged_in: bool, user_info: dict = None):
        """更新按钮状态"""
        self.is_logged_in = logged_in
        self.user_info = user_info
        
        if logged_in and user_info:
            nickname = user_info.get("nickname", tr("login.user_button.default_nickname"))
            self.setText(nickname[:12])  # 增加一点长度
            self.setStyleSheet("""
                QPushButton {
                    background: #1890ff;
                    border: none;
                    border-radius: 4px;
                    color: white;
                    padding: 0 10px;
                }
                QPushButton:hover {
                    background: #40a9ff;
                }
            """)
        else:
            self.setText(tr("login.user_button.login_text"))
            self.setStyleSheet("""
                QPushButton {
                    background: white;
                    border: 1px solid #d9d9d9;
                    border-radius: 4px;
                    color: #666666;
                    padding: 0 10px;
                }
                QPushButton:hover {
                    border-color: #1890ff;
                    color: #1890ff;
                }
            """)

    def retranslate_ui(self):
        """重新翻译"""
        self.update_state(self.is_logged_in, self.user_info)


class LoginDialog(QDialog):
    """登录对话框"""
    
    login_success = pyqtSignal(dict)  # 登录成功
    login_cancelled = pyqtSignal()    # 登录取消
    
    def __init__(self, auth_manager: AuthManager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.setWindowTitle(tr("login.user_button.login_text"))
        self.setMinimumSize(500, 350) # 改为最小尺寸
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        
        # 设置对话框图标
        icon_path = get_icon_path("CAJ转换器.ico")
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))
        
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """设置UI"""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 标题栏
        title_bar = QWidget()
        title_bar.setFixedHeight(50)
        title_bar.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #f0f0f0;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(20, 0, 15, 0)
        
        title_label = QLabel(tr("login.dialog.title"))
        title_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333333;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 30)
        close_btn.setFont(QFont("Arial", 16))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #666666;
            }
            QPushButton:hover {
                color: #333333;
            }
        """)
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)
        
        layout.addWidget(title_bar)
        
        # 内容区域
        content = QWidget()
        content.setStyleSheet("background-color: #ffffff;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 30, 30, 20)
        content_layout.setSpacing(20)
        
        # 说明文本
        info_label = QLabel(tr("login.dialog.instructions"))
        info_label.setFont(QFont("Microsoft YaHei", 11))
        info_label.setStyleSheet("color: #666666;")
        info_label.setWordWrap(True)
        content_layout.addWidget(info_label)
        
        # 进度显示区域（初始隐藏）
        self.progress_widget = QWidget()
        progress_layout = QVBoxLayout(self.progress_widget)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(15)
        
        progress_label = QLabel(tr("login.dialog.waiting"))
        progress_label.setFont(QFont("Microsoft YaHei", 11))
        progress_label.setStyleSheet("color: #1890ff;")
        progress_label.setWordWrap(True) # 允许换行
        progress_layout.addWidget(progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #f0f0f0;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #1890ff;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        self.remaining_label = QLabel(tr("login.dialog.remaining_time").format(time=300))
        self.remaining_label.setFont(QFont("Microsoft YaHei", 10))
        self.remaining_label.setStyleSheet("color: #999999;")
        self.remaining_label.setWordWrap(True) # 允许换行
        progress_layout.addWidget(self.remaining_label)
        
        self.progress_widget.hide()
        content_layout.addWidget(self.progress_widget)
        
        content_layout.addStretch()
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton(tr("login.dialog.cancel"))
        self.cancel_btn.setMinimumSize(90, 38) # 改为最小尺寸
        self.cancel_btn.setFont(QFont("Microsoft YaHei", 11))
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: white;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                color: #666666;
                padding: 0 15px;
            }
            QPushButton:hover {
                border-color: #1890ff;
                color: #1890ff;
            }
        """)
        self.cancel_btn.clicked.connect(self.on_cancel)
        btn_layout.addWidget(self.cancel_btn)
        
        self.login_btn = QPushButton(tr("login.dialog.browser_login"))
        self.login_btn.setMinimumSize(150, 38) # 改为最小尺寸
        self.login_btn.setFont(QFont("Microsoft YaHei", 11))
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background: #1890ff;
                border: none;
                border-radius: 4px;
                color: white;
                padding: 0 15px;
            }
            QPushButton:hover {
                background: #40a9ff;
            }
        """)
        self.login_btn.clicked.connect(self.on_login_click)
        btn_layout.addWidget(self.login_btn)
        
        content_layout.addLayout(btn_layout)
        
        layout.addWidget(content)
    
    def connect_signals(self):
        """连接信号"""
        self.auth_manager.login_success.connect(self.on_login_success)
        self.auth_manager.login_failed.connect(self.on_login_failed)
        self.auth_manager.login_cancelled.connect(self.on_login_cancelled)
        self.auth_manager.polling_started.connect(self.on_polling_started)
        self.auth_manager.polling_stopped.connect(self.on_polling_stopped)
    
    def on_login_click(self):
        """登录按钮点击"""
        # 启动登录流程
        login_url = self.auth_manager.start_login_flow()
        if not login_url:
            QMessageBox.warning(self, tr("common.error"), tr("login.dialog.error_start"))
            return
        
        # 尝试用外部浏览器打开
        try:
            webbrowser.open(login_url)
        except Exception as e:
            QMessageBox.warning(self, tr("common.error"), tr("login.dialog.error_browser").format(error=str(e)))
            return
        
        # 启动轮询
        self.auth_manager.start_polling_thread(
            timeout=AuthManager.POLL_TIMEOUT,
            on_progress=self.update_progress
        )
    
    def on_cancel(self):
        """取消按钮点击"""
        if self.auth_manager.is_polling:
            self.auth_manager.cancel_polling()
        else:
            self.reject()
    
    def on_polling_started(self):
        """轮询开始"""
        self.login_btn.setEnabled(False)
        self.cancel_btn.setText(tr("login.dialog.cancel_login"))
        self.progress_widget.show()
        self.progress_bar.setValue(0)
    
    def on_polling_stopped(self):
        """轮询停止"""
        self.login_btn.setEnabled(True)
        self.cancel_btn.setText(tr("login.dialog.cancel"))
        self.progress_widget.hide()
    
    def update_progress(self, remaining: int):
        """更新进度"""
        total = AuthManager.POLL_TIMEOUT
        progress = int((total - remaining) / total * 100)
        self.progress_bar.setValue(progress)
        self.remaining_label.setText(tr("login.dialog.remaining_time").format(time=remaining))
    
    def on_login_success(self, user_info: dict):
        """登录成功"""
        self.login_success.emit(user_info)
        QMessageBox.information(self, tr("common.success"), tr("login.dialog.success"))
        self.accept()
    
    def on_login_failed(self, error_msg: str):
        """登录失败"""
        QMessageBox.warning(self, tr("login.dialog.failure"), error_msg)
    
    def on_login_cancelled(self):
        """登录被取消"""
        pass


class UserInfoPanel(QWidget):
    """用户信息面板 - 仿照设计图样式"""
    
    logout_clicked = pyqtSignal()
    
    def __init__(self, user_info: dict, parent=None):
        super().__init__(parent)
        self.user_info = user_info
        # 增加最小尺寸以容纳阴影
        self.setMinimumSize(280, 180)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        # 主布局（包含边距以显示阴影）
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(0)
        
        # 容器控件
        self.container = QWidget()
        self.container.setObjectName("Container")
        self.container.setStyleSheet("""
            #Container {
                background-color: #e8f4fc;
                border-radius: 12px;
            }
        """)
        
        # 容器阴影
        shadow = QGraphicsDropShadowEffect(self.container)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 50))
        self.container.setGraphicsEffect(shadow)
        
        main_layout.addWidget(self.container)
        
        # 内容布局
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(18, 18, 18, 14)
        layout.setSpacing(0)
        
        # 用户信息区域
        user_widget = QWidget()
        user_widget.setStyleSheet("background: transparent;")
        user_layout = QHBoxLayout(user_widget)
        user_layout.setContentsMargins(0, 0, 0, 0)
        user_layout.setSpacing(14)
        
        # 圆形蓝色头像
        avatar_label = QLabel()
        avatar_label.setFixedSize(48, 48)
        
        # 尝试加载头像或显示默认图标
        avatar_url = self.user_info.get("avatar", "")
        avatar_loaded = False
        if avatar_url:
            try:
                import requests
                response = requests.get(avatar_url, timeout=5)
                if response.status_code == 200:
                    pixmap = QPixmap()
                    pixmap.loadFromData(response.content)
                    scaled = pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                                          Qt.TransformationMode.SmoothTransformation)
                    avatar_label.setPixmap(scaled)
                    avatar_loaded = True
            except Exception:
                pass
        
        if not avatar_loaded:
            # 绘制默认用户图标（蓝色背景+白色人形）
            avatar_pixmap = QPixmap(48, 48)
            avatar_pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(avatar_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            # 蓝色圆形背景
            painter.setBrush(QBrush(QColor("#5b9bd5")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(0, 0, 48, 48)
            # 白色人形图标
            painter.setBrush(QBrush(QColor("#ffffff")))
            # 头部
            painter.drawEllipse(16, 8, 16, 16)
            # 身体
            painter.drawEllipse(10, 26, 28, 20)
            painter.end()
            avatar_label.setPixmap(avatar_pixmap)
        
        user_layout.addWidget(avatar_label)
        
        # 用户名和状态
        info_widget = QWidget()
        info_widget.setStyleSheet("background: transparent;")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 4, 0, 4)
        info_layout.setSpacing(4)
        
        # 用户名
        raw_nickname = self.user_info.get("nickname", tr("login.user_button.default_nickname"))
        nickname_font = QFont("Microsoft YaHei", 12)
        nickname_font.setWeight(QFont.Weight.Medium)
        
        nickname_label = QLabel(raw_nickname)
        nickname_label.setFont(nickname_font)
        nickname_label.setStyleSheet("color: #333333; background: transparent;")
        nickname_label.setWordWrap(True) # 允许换行，取代之前的省略号逻辑以防万一
        info_layout.addWidget(nickname_label)
        
        # 已登录状态
        status_label = QLabel(tr("login.user_button.logged_in"))
        status_label.setFont(QFont("Microsoft YaHei", 10))
        status_label.setStyleSheet("color: #888888; background: transparent;")
        status_label.setWordWrap(True)
        info_layout.addWidget(status_label)
        
        user_layout.addWidget(info_widget)
        user_layout.addStretch()
        
        layout.addWidget(user_widget)
        
        # 分隔线
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #d0e4f0; border: none;")
        layout.addSpacing(14)
        layout.addWidget(separator)
        layout.addSpacing(10)
        
        # 退出登录按钮
        logout_btn = QPushButton()
        logout_btn.setMinimumHeight(28) # 改为最小高度
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #e74c3c;
                text-align: left;
                padding-left: 0px;
            }
            QPushButton:hover {
                color: #c0392b;
            }
        """)
        
        # 按钮内容布局
        btn_layout = QHBoxLayout(logout_btn)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(6)
        
        # 退出图标（↩）
        icon_label = QLabel("↩")
        icon_label.setFont(QFont("Arial", 13))
        icon_label.setStyleSheet("color: #e74c3c; background: transparent;")
        btn_layout.addWidget(icon_label)
        
        # 退出文字
        text_label = QLabel(tr("login.user_button.logout_text"))
        text_label.setFont(QFont("Microsoft YaHei", 11))
        text_label.setStyleSheet("color: #e74c3c; background: transparent;")
        text_label.setWordWrap(True)
        btn_layout.addWidget(text_label)
        
        btn_layout.addStretch()
        
        logout_btn.clicked.connect(self.on_logout_click)
        layout.addWidget(logout_btn)
        
        layout.addStretch()
    
    def on_logout_click(self):
        """退出登录"""
        reply = QMessageBox.question(
            self,
            tr("login.logout.confirm_title"),
            tr("login.logout.confirm_message"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.logout_clicked.emit()
