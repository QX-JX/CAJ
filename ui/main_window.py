from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFrame, QStackedWidget, QMenu,
    QDialog, QComboBox, QCheckBox, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt, QSize, QSettings, QPoint
from PyQt6.QtGui import QFont, QIcon, QPainter, QColor, QPen, QLinearGradient, QBrush, QAction, QPixmap, QGuiApplication
from ui.convert_page import ConvertPage
from ui.login_panel import UserButton, LoginDialog, UserInfoPanel
from ui.ad_banner import AdBanner
from ui.ad_small import AdSmallBanner
from core.auth_manager import AuthManager
from core.token_storage import TokenStorage
from core.constants import CURRENT_VERSION
from core.update_manager import UpdateManager
from core.i18n_manager import tr, I18nManager
import webbrowser


class SettingsDialog(QDialog):
    """通用设置对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("main_window.settings.title"))
        self.setMinimumSize(450, 400)  # 改为最小尺寸，允许根据内容扩展
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self.settings = QSettings("KunqiongAI", "CAJConverter")
        self.i18n = I18nManager()
        
        # 设置对话框图标
        icon_path = get_icon_path("CAJ转换器.ico")
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 移除内置标题栏，保留系统窗口标题栏
        
        # 使用滚动区域以防文本过长导致显示不全
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 内容区域
        content = QWidget()
        content.setStyleSheet("background-color: #ffffff;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 20, 30, 20)
        content_layout.setSpacing(25)
        
        # 同时处理文件数量
        file_count_layout = QHBoxLayout()
        file_count_layout.setSpacing(15)
        
        file_count_label = QLabel(tr("main_window.settings.file_count"))
        file_count_label.setFont(QFont("Microsoft YaHei", 11))
        file_count_label.setStyleSheet("color: #333333;")
        file_count_label.setWordWrap(True)  # 支持换行
        file_count_layout.addWidget(file_count_label, 1) # 增加权重允许伸缩
        
        self.file_count_combo = QComboBox()
        self.file_count_combo.setMinimumSize(100, 36) # 使用最小尺寸
        self.file_count_combo.setFont(QFont("Microsoft YaHei", 11))
        self.file_count_combo.addItems(["1", "2", "3"])
        self.file_count_combo.setCurrentText("2")
        self.file_count_combo.setStyleSheet(self.get_combo_style())
        file_count_layout.addWidget(self.file_count_combo)
        
        content_layout.addLayout(file_count_layout)
        
        # 语言选择
        lang_layout = QHBoxLayout()
        lang_layout.setSpacing(15)
        
        lang_label = QLabel(tr("main_window.settings.language"))
        lang_label.setFont(QFont("Microsoft YaHei", 11))
        lang_label.setStyleSheet("color: #333333;")
        lang_label.setWordWrap(True)
        lang_layout.addWidget(lang_label, 1)
        
        self.lang_combo = QComboBox()
        self.lang_combo.setMinimumSize(200, 36)
        self.lang_combo.setFont(QFont("Microsoft YaHei", 11))
        
        # 获取可用语言并添加到下拉框
        available_locales = self.i18n.get_available_locales()
        
        for locale in sorted(available_locales):
            # 使用翻译文件中的名称
            name = tr(f"main_window.languages.{locale}", locale)
            self.lang_combo.addItem(name, locale)
            
        self.lang_combo.setStyleSheet(self.get_combo_style())
        lang_layout.addWidget(self.lang_combo)
        
        content_layout.addLayout(lang_layout)
        
        # 自动新建文件夹选项
        self.auto_folder_checkbox = QCheckBox(tr("main_window.settings.auto_folder"))
        self.auto_folder_checkbox.setFont(QFont("Microsoft YaHei", 11))
        self.auto_folder_checkbox.setChecked(True)
        self.auto_folder_checkbox.setStyleSheet("""
            QCheckBox {
                color: #333333;
                spacing: 10px;
                line-height: 1.5;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #d9d9d9;
                border-radius: 3px;
                background: white;
            }
            QCheckBox::indicator:checked {
                background: #1890ff;
                border-color: #1890ff;
            }
            QCheckBox::indicator:hover {
                border-color: #1890ff;
            }
        """)
        # 允许 checkbox 文字换行
        # self.auto_folder_checkbox.setWordWrap(True) # QCheckBox 没有 setWordWrap
        content_layout.addWidget(self.auto_folder_checkbox)
        
        content_layout.addStretch()
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        btn_layout.addStretch()
        
        cancel_btn = QPushButton(tr("main_window.settings.cancel"))
        cancel_btn.setMinimumSize(100, 38) # 改为最小尺寸
        cancel_btn.setFont(QFont("Microsoft YaHei", 11))
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("""
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
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        confirm_btn = QPushButton(tr("main_window.settings.confirm"))
        confirm_btn.setMinimumSize(100, 38) # 改为最小尺寸
        confirm_btn.setFont(QFont("Microsoft YaHei", 11))
        confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm_btn.setStyleSheet("""
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
        confirm_btn.clicked.connect(self.save_and_close)
        btn_layout.addWidget(confirm_btn)
        
        content_layout.addLayout(btn_layout)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def get_combo_style(self):
        return """
            QComboBox {
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                padding: 5px 10px;
                background: white;
            }
            QComboBox:hover {
                border-color: #1890ff;
            }
            QComboBox:focus {
                border-color: #1890ff;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #666666;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #d9d9d9;
                background: white;
                selection-background-color: #e6f7ff;
                selection-color: #1890ff;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                height: 32px;
                padding: 5px 10px;
            }
        """
    
    def load_settings(self):
        """加载设置"""
        file_count = self.settings.value("concurrent_files", "2")
        auto_folder = self.settings.value("auto_create_folder", True, type=bool)
        current_locale = self.settings.value("language", self.i18n.get_locale())
        
        self.file_count_combo.setCurrentText(str(file_count))
        self.auto_folder_checkbox.setChecked(auto_folder)
        
        # 设置当前语言
        index = self.lang_combo.findData(current_locale)
        if index >= 0:
            self.lang_combo.setCurrentIndex(index)
    
    def save_and_close(self):
        """保存设置并关闭"""
        new_locale = self.lang_combo.currentData()
        old_locale = self.settings.value("language", self.i18n.get_locale())
        
        self.settings.setValue("concurrent_files", self.file_count_combo.currentText())
        self.settings.setValue("auto_create_folder", self.auto_folder_checkbox.isChecked())
        self.settings.setValue("language", new_locale)
        
        # 如果语言改变了，更新 I18nManager 并通知父窗口刷新
        if new_locale != old_locale:
            self.i18n.set_locale(new_locale)
            if hasattr(self.parent(), "retranslate_ui"):
                self.parent().retranslate_ui()
                
        self.accept()
    
    def get_concurrent_files(self) -> int:
        """获取同时处理文件数量"""
        return int(self.file_count_combo.currentText())
    
    def get_auto_create_folder(self) -> bool:
        """获取是否自动创建文件夹"""
        return self.auto_folder_checkbox.isChecked()


class FeatureCard(QFrame):
    """功能卡片组件"""
    def __init__(self, icon_type: str, title: str, description: str, parent=None):
        super().__init__(parent)
        self.icon_type = icon_type
        self.setMinimumSize(280, 320)  # 设置最小尺寸而不是固定尺寸
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setup_ui(title, description)
        self.setStyleSheet("""
            FeatureCard {
                background-color: #f8fbff;
                border: 1px solid #e8f0f8;
                border-radius: 12px;
            }
            FeatureCard:hover {
                background-color: #f0f7ff;
                border: 1px solid #d0e4f8;
            }
        """)
    
    def setup_ui(self, title: str, description: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 30, 20, 30)  # 增加底部边距
        layout.setSpacing(15)
        
        # 图标区域
        icon_label = QLabel()
        icon_label.setFixedSize(120, 120)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(f"""
            background-color: transparent;
        """)
        
        # 使用自定义绘制的图标
        self.icon_widget = IconWidget(self.icon_type)
        self.icon_widget.setFixedSize(120, 120)
        
        layout.addWidget(self.icon_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 标题
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)  # 允许标题换行
        self.title_label.setStyleSheet("color: #333333; background: transparent; border: none;")
        layout.addWidget(self.title_label)
        
        # 描述
        self.desc_label = QLabel(description)
        self.desc_label.setFont(QFont("Microsoft YaHei", 11))
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color: #888888; background: transparent; border: none;")
        layout.addWidget(self.desc_label)
        
        layout.addStretch()

    def retranslate_ui(self, title: str, description: str):
        """重新翻译"""
        if hasattr(self, 'title_label'):
            self.title_label.setText(title)
        if hasattr(self, 'desc_label'):
            self.desc_label.setText(description)


class IconWidget(QWidget):
    """自定义图标绘制组件"""
    def __init__(self, icon_type: str, parent=None):
        super().__init__(parent)
        self.icon_type = icon_type
        self.cached_pixmap = None
    
    def paintEvent(self, event):
        if self.cached_pixmap is None:
            # 第一次绘制时缓存
            self.cached_pixmap = QPixmap(self.width(), self.height())
            self.cached_pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(self.cached_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            self._draw_icon(painter)
            painter.end()
        
        # 使用缓存的pixmap
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.cached_pixmap)
    
    def _draw_icon(self, painter: QPainter):
        """绘制图标"""
        # 绘制文档图标背景
        gradient = QLinearGradient(15, 15, 105, 105)
        gradient.setColorAt(0, QColor("#7dd3fc"))
        gradient.setColorAt(1, QColor("#38bdf8"))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(20, 15, 80, 90, 8, 8)
        
        # 绘制文档线条
        painter.setPen(QPen(QColor("#ffffff"), 3))
        painter.drawLine(35, 35, 85, 35)
        painter.drawLine(35, 50, 85, 50)
        painter.drawLine(35, 65, 65, 65)
        
        # 根据类型绘制不同的小图标
        if self.icon_type == "caj_to_other":
            # 右下角小文档
            painter.setBrush(QColor("#60a5fa"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(70, 70, 40, 45, 6, 6)
            painter.setPen(QPen(QColor("#ffffff"), 2))
            painter.drawLine(80, 85, 100, 85)
            painter.drawLine(80, 100, 95, 100)
        elif self.icon_type == "caj_to_image":
            # 右下角图片图标
            painter.setBrush(QColor("#a78bfa"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(70, 70, 40, 40, 6, 6)
            # 山形
            painter.setPen(QPen(QColor("#ffffff"), 3))
            painter.drawLine(75, 105, 85, 90)
            painter.drawLine(85, 90, 95, 100)
            painter.drawLine(95, 100, 107, 85)
        else:  # other_to_caj
            # 右下角CAJ标签
            painter.setBrush(QColor("#fb923c"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(70, 70, 40, 40, 6, 6)
            painter.setPen(QPen(QColor("#ffffff"), 1))
            font = painter.font()
            font.setPointSize(10)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(72, 75, 36, 30, Qt.AlignmentFlag.AlignCenter, "CAJ")


import os
import sys


from core.utils import get_icon_path


class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CAJ转换器")
        self.resize(1200, 800)
        self.setMinimumSize(1100, 750)  # 调整最小窗口大小以适应所有内容
        
        # 设置无边框窗口
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # 设置窗口图标
        self.set_window_icon()
        
        # 用于窗口拖动
        self._drag_pos = None
        
        # 初始化认证管理器和Token存储
        self.auth_manager = AuthManager()
        self.token_storage = TokenStorage()
        self.user_info_panel = None

        # 初始化更新管理器
        self.update_manager = UpdateManager()
        self.update_manager.update_available.connect(self.on_update_available)
        self.update_manager.no_update.connect(self.on_no_update)
        self.update_manager.check_failed.connect(self.on_update_check_failed)
        
        # 启动时自动检查更新
        self.manual_update_check = False
        self.update_manager.check_for_updates()
        
        # 连接登录成功信号
        self.auth_manager.login_success.connect(self.on_login_success)
        self.auth_manager.login_failed.connect(self.on_login_failed)
        
        self.setup_ui()
        self.apply_styles()
        self.restore_login_state()
        
        # 强制执行一次翻译刷新，确保所有组件（包括UserButton）都处于当前语言状态
        self.retranslate_ui()
    
    def set_window_icon(self):
        """设置窗口图标"""
        icon_path = get_icon_path("CAJ转换器.ico")
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))
    
    def setup_ui(self):
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 顶部标题栏
        self.create_title_bar(main_layout)
        
        # 使用 StackedWidget 管理页面
        self.stacked_widget = QStackedWidget()
        
        # 首页 - 直接添加，不使用滚动区域
        self.home_page = QWidget()
        self.setup_home_page()
        self.stacked_widget.addWidget(self.home_page)
        
        # 转换页面 - 为每个功能创建独立实例
        self.convert_pages = {}
        
        # CAJ转其他
        self.convert_pages["caj_to_other"] = ConvertPage("caj_to_other")
        self.convert_pages["caj_to_other"].go_home.connect(self.show_home)
        self.convert_pages["caj_to_other"].switch_page.connect(self.show_convert_page)
        self.stacked_widget.addWidget(self.convert_pages["caj_to_other"])
        
        # CAJ转图片
        self.convert_pages["caj_to_image"] = ConvertPage("caj_to_image")
        self.convert_pages["caj_to_image"].go_home.connect(self.show_home)
        self.convert_pages["caj_to_image"].switch_page.connect(self.show_convert_page)
        self.stacked_widget.addWidget(self.convert_pages["caj_to_image"])
        
        # 其他转CAJ
        self.convert_pages["other_to_caj"] = ConvertPage("other_to_caj")
        self.convert_pages["other_to_caj"].go_home.connect(self.show_home)
        self.convert_pages["other_to_caj"].switch_page.connect(self.show_convert_page)
        self.stacked_widget.addWidget(self.convert_pages["other_to_caj"])
        
        main_layout.addWidget(self.stacked_widget)
    
    def setup_home_page(self):
        """设置首页内容"""
        content_layout = QVBoxLayout(self.home_page)
        content_layout.setContentsMargins(40, 20, 40, 15)
        content_layout.setSpacing(15)
        
        # 主标题
        self.create_main_title(content_layout)
        
        # 广告轮播 - 包含两个广告位
        self.ad_banner = AdBanner(
            soft_number="10004",
            ad_positions=["adv_position_02", "adv_position_03"]
        )
        content_layout.addWidget(self.ad_banner, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 增加间距
        content_layout.addSpacing(15)
        
        # 功能卡片区域
        self.create_feature_cards(content_layout)
        
        content_layout.addStretch()
        
        # 品牌信息和版本号（并行布局）
        self.create_brand_info(content_layout)
    
    def retranslate_ui(self):
        """重新翻译 UI"""
        self.setWindowTitle(tr("main_window.title"))
        
        # 标题栏
        if hasattr(self, 'app_title'):
            self.app_title.setText(tr("main_window.title"))
        if hasattr(self, 'subtitle'):
            self.subtitle.setText(tr("main_window.subtitle"))
        if hasattr(self, 'customize_btn'):
            self.customize_btn.setText(tr("main_window.customize"))
        if hasattr(self, 'feedback_btn'):
            self.feedback_btn.setText(tr("main_window.feedback"))
            
        # 用户按钮
        if hasattr(self, 'user_btn'):
            self.user_btn.retranslate_ui()
            
        # 首页
        if hasattr(self, 'title_label'):
            self.title_label.setText(tr("main_window.home.title_prefix"))
        if hasattr(self, 'highlight_label'):
            self.highlight_label.setText(tr("main_window.home.title_highlight"))
        if hasattr(self, 'lang_btn'):
            self.lang_btn.setText("🌐 " + tr("main_window.settings.language"))
            # 刷新语言菜单
            self.setup_language_menu()
        if hasattr(self, 'brand_text'):
            self.brand_text.setText(tr("main_window.brand_text"))
        if hasattr(self, 'version_label'):
            self.version_label.setText(tr("main_window.version").format(version=CURRENT_VERSION))
            
        # 功能卡片
        if hasattr(self, 'card1'):
            self.card1.retranslate_ui(
                tr("main_window.home.cards.caj_to_other.title"),
                tr("main_window.home.cards.caj_to_other.desc")
            )
        if hasattr(self, 'card2'):
            self.card2.retranslate_ui(
                tr("main_window.home.cards.caj_to_image.title"),
                tr("main_window.home.cards.caj_to_image.desc")
            )
        if hasattr(self, 'card3'):
            self.card3.retranslate_ui(
                tr("main_window.home.cards.other_to_caj.title"),
                tr("main_window.home.cards.other_to_caj.desc")
            )
            
        # 更新所有转换页面
        for page in self.convert_pages.values():
            if hasattr(page, "retranslate_ui"):
                page.retranslate_ui()
                
        # 更新菜单项
        self.update_menu_text()

    def get_menu_style(self):
        """获取统一的菜单样式"""
        return """
            QMenu {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 5px 0;
            }
            QMenu::item {
                padding: 10px 30px 10px 40px;
                font-family: "Microsoft YaHei";
                font-size: 12px;
                color: #333333;
                background-color: transparent;
            }
            QMenu::item:selected {
                background-color: #e6f7ff;
                color: #1890ff;
            }
            QMenu::item:checked {
                font-weight: bold;
                color: #1890ff;
            }
            QMenu::separator {
                height: 1px;
                background-color: #f0f0f0;
                margin: 5px 10px;
            }
        """

    def setup_language_menu(self):
        """设置语言切换菜单"""
        i18n = I18nManager()
        
        # 如果按钮已经有菜单，先清理
        old_menu = self.lang_btn.menu()
        if old_menu:
            old_menu.deleteLater()
            
        menu = QMenu(self.lang_btn)
        menu.setStyleSheet(self.get_menu_style())
        
        available_locales = i18n.get_available_locales()
        
        # 按照显示名称排序
        sorted_locales = sorted(available_locales)
        
        for locale in sorted_locales:
            # 使用 tr() 获取翻译后的语言名称
            name = tr(f"main_window.languages.{locale}", locale)
            action = QAction(name, self)
            action.triggered.connect(lambda checked, l=locale: self.change_language(l))
            
            # 标记当前选中的语言
            if locale == i18n.get_locale():
                action.setCheckable(True)
                action.setChecked(True)
            menu.addAction(action)
            
        self.lang_btn.setMenu(menu)

    def change_language(self, locale):
        """切换语言"""
        i18n = I18nManager()
        if i18n.set_locale(locale):
            # 保存到设置
            settings = QSettings("KunqiongAI", "CAJConverter")
            settings.setValue("language", locale)
            # 刷新 UI
            self.retranslate_ui()

    def update_menu_text(self):
        """更新菜单文本"""
        if hasattr(self, 'settings_action'):
            self.settings_action.setText(tr("main_window.menu.settings"))
        if hasattr(self, 'update_action'):
            self.update_action.setText(tr("main_window.menu.update"))

    def create_title_bar(self, parent_layout):
        """创建顶部标题栏"""
        title_bar = QWidget()
        title_bar.setFixedHeight(50)
        title_bar.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #f0f0f0;")
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(15, 0, 15, 0)
        
        # 左侧图标和标题
        left_layout = QHBoxLayout()
        left_layout.setSpacing(8)
        
        # 应用图标 - 使用ico文件
        app_icon = QLabel()
        app_icon.setFixedSize(24, 24)
        icon_path = get_icon_path("CAJ转换器.ico")
        if icon_path:
            from PyQt6.QtGui import QPixmap
            pixmap = QPixmap(icon_path).scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            app_icon.setPixmap(pixmap)
        else:
            app_icon.setText("📄")
            app_icon.setFont(QFont("Segoe UI Emoji", 16))
        left_layout.addWidget(app_icon)
        
        self.app_title = QLabel(tr("main_window.title"))
        self.app_title.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self.app_title.setStyleSheet("color: #333333;")
        left_layout.addWidget(self.app_title)
        
        # 竖条分隔符
        separator = QLabel("|")
        separator.setFont(QFont("Microsoft YaHei", 11))
        separator.setStyleSheet("color: #cccccc; margin: 0px 8px;")
        left_layout.addWidget(separator)
        
        # 鲲穹AI旗下产品
        self.subtitle = QLabel(tr("main_window.subtitle"))
        self.subtitle.setFont(QFont("Microsoft YaHei", 9))
        self.subtitle.setStyleSheet("color: #999999;")
        left_layout.addWidget(self.subtitle)
        
        layout.addLayout(left_layout)
        layout.addStretch()
        
        # 右侧：广告、软件定制、用户按钮、菜单和窗口控制按钮
        right_layout = QHBoxLayout()
        right_layout.setSpacing(8)
        
        # 标题栏小广告 - 4:1比例
        self.title_ad = AdSmallBanner(
            soft_number="10004",
            ad_position="adv_position_01",
            width=120
        )
        right_layout.addWidget(self.title_ad)
        
        # 语言切换按钮 - 放在广告旁边
        self.lang_btn = QPushButton("🌐 " + tr("main_window.settings.language"))
        self.lang_btn.setFixedHeight(32)
        self.lang_btn.setFont(QFont("Microsoft YaHei", 10))
        self.lang_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lang_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                color: #666666;
                padding: 0px 10px;
            }
            QPushButton:hover {
                border-color: #1890ff;
                color: #1890ff;
            }
            QPushButton::menu-indicator {
                image: none;
            }
        """)
        self.setup_language_menu()
        right_layout.addWidget(self.lang_btn)
        
        # 软件定制/联系我们按钮
        self.customize_btn = QPushButton(tr("main_window.customize"))
        self.customize_btn.setFixedHeight(32)
        self.customize_btn.setFont(QFont("Microsoft YaHei", 10))
        self.customize_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.customize_btn.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
                border: none;
                border-radius: 4px;
                color: white;
                padding: 0px 15px;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
        """)
        self.customize_btn.clicked.connect(self.open_customize_page)
        right_layout.addWidget(self.customize_btn)
        
        # 问题反馈按钮
        self.feedback_btn = QPushButton(tr("main_window.feedback"))
        self.feedback_btn.setFixedHeight(32)
        self.feedback_btn.setFont(QFont("Microsoft YaHei", 10))
        self.feedback_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.feedback_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                border: none;
                border-radius: 4px;
                color: white;
                padding: 0px 15px;
            }
            QPushButton:hover {
                background-color: #ffb74d;
            }
        """)
        self.feedback_btn.clicked.connect(self.open_feedback_page)
        right_layout.addWidget(self.feedback_btn)
        
        # 用户按钮
        self.user_btn = UserButton()
        self.user_btn.login_clicked.connect(self.show_login_dialog)
        self.user_btn.user_clicked.connect(self.show_user_panel)
        right_layout.addWidget(self.user_btn)
        
        # 菜单按钮（三条横线）
        menu_btn = QPushButton("≡")
        menu_btn.setFixedSize(30, 30)
        menu_btn.setFont(QFont("Arial", 16))
        menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        menu_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #666666;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        
        # 创建下拉菜单
        self.menu = QMenu(menu_btn)
        self.menu.setStyleSheet(self.get_menu_style())
        
        # 添加菜单项并连接信号
        self.settings_action = self.menu.addAction(tr("main_window.menu.settings"))
        self.settings_action.triggered.connect(self.show_settings_dialog)
        
        self.update_action = self.menu.addAction(tr("main_window.menu.update"))
        self.update_action.triggered.connect(self.check_update)
        
        menu_btn.setMenu(self.menu)
        right_layout.addWidget(menu_btn)
        
        # 窗口控制按钮
        for btn_text, btn_action in [("─", self.showMinimized), ("□", self.toggle_maximize), ("×", self.close)]:
            btn = QPushButton(btn_text)
            btn.setFixedSize(30, 30)
            btn.setFont(QFont("Arial", 12))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if btn_text == "×":
                btn.setStyleSheet("""
                    QPushButton {
                        background: transparent;
                        border: none;
                        color: #666666;
                    }
                    QPushButton:hover {
                        background-color: #ff4444;
                        color: white;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background: transparent;
                        border: none;
                        color: #666666;
                    }
                    QPushButton:hover {
                        background-color: #e0e0e0;
                    }
                """)
            btn.clicked.connect(btn_action)
            right_layout.addWidget(btn)
        
        layout.addLayout(right_layout)
        
        # 保存标题栏引用用于拖动
        self.title_bar = title_bar
        parent_layout.addWidget(title_bar)
    
    def mousePressEvent(self, event):
        """鼠标按下事件 - 用于窗口拖动"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 检查是否在标题栏区域
            if hasattr(self, 'title_bar') and self.title_bar.geometry().contains(event.pos()):
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 用于窗口拖动"""
        if self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        self._drag_pos = None
    
    def mouseDoubleClickEvent(self, event):
        """双击标题栏最大化/还原"""
        if hasattr(self, 'title_bar') and self.title_bar.geometry().contains(event.pos()):
            self.toggle_maximize()
    
    def create_main_title(self, parent_layout):
        """创建主标题"""
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.title_label = QLabel(tr("main_window.home.title_prefix"))
        self.title_label.setFont(QFont("Microsoft YaHei", 24, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #333333;")
        
        self.highlight_label = QLabel(tr("main_window.home.title_highlight"))
        self.highlight_label.setFont(QFont("Microsoft YaHei", 24, QFont.Weight.Bold))
        self.highlight_label.setStyleSheet("color: #f97316;")
        
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.highlight_label)
        
        parent_layout.addLayout(title_layout)
    
    def create_feature_cards(self, parent_layout):
        """创建功能卡片"""
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(40)
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # CAJ转其他
        self.card1 = FeatureCard(
            "caj_to_other",
            tr("main_window.home.cards.caj_to_other.title"),
            tr("main_window.home.cards.caj_to_other.desc")
        )
        self.card1.mousePressEvent = lambda e: self.show_convert_page("caj_to_other")
        cards_layout.addWidget(self.card1)
        
        # CAJ转图片
        self.card2 = FeatureCard(
            "caj_to_image", 
            tr("main_window.home.cards.caj_to_image.title"),
            tr("main_window.home.cards.caj_to_image.desc")
        )
        self.card2.mousePressEvent = lambda e: self.show_convert_page("caj_to_image")
        cards_layout.addWidget(self.card2)
        
        # 其他转CAJ
        self.card3 = FeatureCard(
            "other_to_caj",
            tr("main_window.home.cards.other_to_caj.title"), 
            tr("main_window.home.cards.other_to_caj.desc")
        )
        self.card3.mousePressEvent = lambda e: self.show_convert_page("other_to_caj")
        cards_layout.addWidget(self.card3)
        
        parent_layout.addLayout(cards_layout)
    
    def show_convert_page(self, page_type: str):
        """显示转换页面"""
        # 获取对应的页面实例
        page = self.convert_pages.get(page_type)
        if page:
            # 更新侧边栏选中状态
            for menu_id, item in page.menu_items.items():
                item.set_selected(menu_id == page_type)
            # 切换到对应页面
            page_index = {"caj_to_other": 1, "caj_to_image": 2, "other_to_caj": 3}
            self.stacked_widget.setCurrentIndex(page_index.get(page_type, 1))
    
    def show_home(self):
        """返回首页"""
        self.stacked_widget.setCurrentIndex(0)
    
    def create_brand_info(self, parent_layout):
        """创建品牌信息和版本号（并行布局，居中）"""
        parent_layout.addSpacing(40)
        
        # 创建外层容器用于居中
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # 左侧弹性空间
        container_layout.addStretch()
        
        # 创建统一的底部布局
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(60)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        # 左侧：品牌信息
        brand_layout = QHBoxLayout()
        brand_layout.setSpacing(8)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        
        # 品牌图标
        brand_icon = QLabel()
        brand_icon.setFixedSize(20, 20)
        icon_path = get_icon_path("鲲穹01.ico")
        if icon_path:
            from PyQt6.QtGui import QPixmap
            pixmap = QPixmap(icon_path).scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            brand_icon.setPixmap(pixmap)
        else:
            brand_icon.setText("◆")
            brand_icon.setFont(QFont("Arial", 12))
            brand_icon.setStyleSheet("color: #3b82f6;")
        
        brand_text = QLabel(tr("main_window.brand_text"))
        self.brand_text = brand_text
        brand_text.setFont(QFont("Microsoft YaHei", 12))
        brand_text.setStyleSheet("color: #999999;")
        
        brand_layout.addWidget(brand_icon)
        brand_layout.addWidget(brand_text)
        
        bottom_layout.addLayout(brand_layout)
        
        # 右侧：版本号
        self.version_label = QLabel(tr("main_window.version").format(version=CURRENT_VERSION))
        self.version_label.setFont(QFont("Microsoft YaHei", 9))
        self.version_label.setStyleSheet("color: #999999;")
        bottom_layout.addWidget(self.version_label)
        
        container_layout.addLayout(bottom_layout, 0)
        
        # 右侧弹性空间
        container_layout.addStretch()
        
        parent_layout.addWidget(container)
    
    def create_status_bar(self, parent_layout):
        """创建底部状态栏（已合并到create_brand_info中）"""
        # 此方法已弃用，品牌信息和版本号现在在create_brand_info中并行显示
        pass
    
    def apply_styles(self):
        """应用全局样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            * {
                /* 确保tooltip样式不被覆盖 */
            }
            QToolTip {
                background-color: #333333;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 10px;
                font-family: "Microsoft YaHei";
                font-size: 12px;
            }
        """)
    
    def toggle_maximize(self):
        """切换最大化状态"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
    
    def show_settings_dialog(self):
        """显示通用设置对话框"""
        dialog = SettingsDialog(self)
        dialog.exec()
    
    def show_tutorial(self):
        """显示软件教程"""
        QMessageBox.information(
            self, 
            tr("main_window.tutorial.title"), 
            tr("main_window.tutorial.content")
        )
    
    def check_update(self):
        """检查更新"""
        self.manual_update_check = True
        self.update_manager.check_for_updates()

    def on_update_available(self, version, download_url, package_hash):
        """发现新版本"""
        reply = QMessageBox.question(
            self,
            tr("main_window.update_dialog.found_title"),
            tr("main_window.update_dialog.found_message").format(version=version),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.update_manager.start_update(download_url, package_hash)
            except Exception as e:
                QMessageBox.critical(self, tr("main_window.update_dialog.fail_title"), str(e))

    def on_no_update(self):
        """无更新"""
        if getattr(self, 'manual_update_check', False):
            QMessageBox.information(
                self, 
                tr("main_window.update_dialog.no_update_title"), 
                tr("main_window.update_dialog.no_update_message").format(version=CURRENT_VERSION)
            )
            self.manual_update_check = False

    def on_update_check_failed(self, error_msg):
        """检查更新失败"""
        # 自动检查失败时不打扰用户，除非是手动检查
        if getattr(self, 'manual_update_check', False):
            QMessageBox.warning(self, tr("main_window.update_dialog.check_fail_title"), error_msg)
            self.manual_update_check = False
    
    def show_about(self):
        """显示关于我们"""
        QMessageBox.about(
            self,
            tr("main_window.about.title"),
            f"<h3>{tr('main_window.about.app_name')}</h3>"
            f"<p>{tr('main_window.about.version_prefix')}{CURRENT_VERSION}</p>"
            f"<p>{tr('main_window.about.desc')}</p>"
            "<br>"
            f"<p>{tr('main_window.about.features_title')}</p>"
            f"<ul>{tr('main_window.about.feature_list')}</ul>"
            "<br>"
            f"<p>{tr('main_window.about.copyright')}</p>"
        )
    
    def open_feedback_page(self):
        """打开问题反馈页面"""
        from core.constants import SOFTWARE_ID
        url = self.auth_manager.get_feedback_url(SOFTWARE_ID)
        if url:
            import webbrowser
            webbrowser.open(url)
        else:
            QMessageBox.warning(self, tr("common.error"), tr("main_window.errors.feedback_fail"))

    
    def open_customize_page(self):
        """打开软件定制页面"""
        customize_url = self.auth_manager.get_customize_url()
        if customize_url:
            import webbrowser
            webbrowser.open(customize_url)
        else:
            QMessageBox.warning(self, tr("common.error"), tr("main_window.errors.customize_fail"))

    def restore_login_state(self):
        """恢复登录状态"""
        # 尝试从存储中恢复Token
        token = self.token_storage.load_token()
        if token:
            # 验证Token有效性
            if self.auth_manager.set_token(token):
                user_info = self.auth_manager.get_user_info()
                if user_info:
                    self.update_login_state(True, user_info)
                    return
        
        # Token无效或不存在，清除存储
        self.token_storage.clear_all()
        self.update_login_state(False)
    
    def show_login_dialog(self):
        """显示登录对话框或直接跳转"""
        # 启动登录流程
        login_url = self.auth_manager.start_login_flow()
        if not login_url:
            QMessageBox.warning(self, tr("common.error"), tr("main_window.errors.login_flow_fail"))
            return
        
        # 直接用浏览器打开
        try:
            import webbrowser
            webbrowser.open(login_url)
        except Exception as e:
            QMessageBox.warning(self, tr("common.error"), tr("main_window.errors.browser_open_fail").format(error=str(e)))
            return
        
        # 启动轮询
        self.auth_manager.start_polling_thread(
            timeout=AuthManager.POLL_TIMEOUT,
            on_progress=self.on_polling_progress
        )
        
        # 显示轮询状态提示
        QMessageBox.information(
            self,
            tr("login.dialog.logging_in_title"),
            tr("login.dialog.logging_in_message")
        )
    
    def on_login_success(self, user_info: dict):
        """登录成功处理"""
        # 保存Token和用户信息
        token = self.auth_manager.get_token()
        if token:
            self.token_storage.save_token(token)
            self.token_storage.save_user_info(user_info)
        
        # 更新UI
        self.update_login_state(True, user_info)
    
    def show_user_panel(self):
        """显示用户信息面板"""
        user_info = self.auth_manager.get_user_info()
        if not user_info:
            stored_info = self.token_storage.load_user_info()
            if stored_info:
                user_info = stored_info
            else:
                self.show_login_dialog()
                return
        
        if self.user_info_panel:
            self.user_info_panel.close()
        
        self.user_info_panel = UserInfoPanel(user_info, self)
        self.user_info_panel.logout_clicked.connect(self.on_logout)
        
        btn_global = self.user_btn.mapToGlobal(self.user_btn.rect().bottomLeft())
        # 考虑到UserInfoPanel现在有20px的透明内边距，需要相应调整位置
        # x坐标向左偏移20px，使内容对齐按钮左侧
        panel_global_x = btn_global.x() - 20
        # y坐标向上偏移20px，再加上原有的6px间距，即 -14px
        panel_global_y = btn_global.y() + 6 - 20
        
        screen = self.user_btn.screen() or QGuiApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            
            # 边界检查
            if panel_global_x + self.user_info_panel.width() > geom.right():
                panel_global_x = geom.right() - self.user_info_panel.width()
            if panel_global_x < geom.left():
                panel_global_x = geom.left()
                
            # 底部边界检查 - 如果下方放不下，就放上面
            if panel_global_y + self.user_info_panel.height() > geom.bottom():
                # 放上面: 按钮顶部 - 面板高度 - 间距 + padding修正
                # 按钮顶部 = btn_global.y() - self.user_btn.height()
                btn_top_y = btn_global.y() - self.user_btn.height()
                panel_global_y = btn_top_y - self.user_info_panel.height() - 6 + 20
            
            if panel_global_y < geom.top():
                panel_global_y = geom.top()
        
        # Popup是顶级窗口，直接移动到全局坐标
        self.user_info_panel.move(panel_global_x, panel_global_y)
        self.user_info_panel.show()
    
    def on_logout(self):
        """退出登录"""
        result = self.auth_manager.logout()
        self.token_storage.clear_all()
        self.update_login_state(False)
        if self.user_info_panel:
            self.user_info_panel.close()
        if result:
            QMessageBox.information(self, tr("login.logout.title"), tr("login.logout.success"))
        else:
            QMessageBox.information(self, tr("login.logout.title"), tr("login.logout.stale"))
    
    def update_login_state(self, logged_in: bool, user_info: dict = None):
        """更新登录状态"""
        self.user_btn.update_state(logged_in, user_info)
    
    def on_polling_progress(self, remaining: int):
        """轮询进度回调"""
        # 可以在这里添加进度显示逻辑
        pass
    
    def on_login_failed(self, error_msg: str):
        """登录失败处理"""
        QMessageBox.warning(self, tr("login.dialog.failure"), error_msg)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        super().closeEvent(event)
