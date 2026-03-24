"""
转换页面模块
"""
import os
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QListWidget, QListWidgetItem,
    QFileDialog, QComboBox, QProgressBar, QMessageBox,
    QSizePolicy, QStackedWidget, QCheckBox, QRadioButton,
    QButtonGroup, QLineEdit, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QLinearGradient, QBrush, QDragEnterEvent, QDropEvent, QDragMoveEvent
from ui.ad_small import AdSideCarousel
from core.utils import get_icon_path
from core.i18n_manager import tr


class SidebarItem(QFrame):
    """侧边栏菜单项"""
    clicked = pyqtSignal(str)

    def __init__(self, icon_type: str, text: str, item_id: str, parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self.icon_type = icon_type
        self.is_selected = False
        self.setMinimumHeight(45)  # 改为最小高度
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setup_ui(text)
        self.update_style()

    def setup_ui(self, text: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 8, 15, 8)
        layout.setSpacing(10)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.update_icon()
        layout.addWidget(self.icon_label)

        self.text_label = QLabel(text)
        self.text_label.setFont(QFont("Microsoft YaHei", 10))
        self.text_label.setWordWrap(True)  # 允许换行
        layout.addWidget(self.text_label)
        layout.addStretch()

    def update_icon(self):
        icons = {
            "home": "🏠",
            "caj_to_other": "📄",
            "caj_to_image": "🖼",
            "other_to_caj": "📑"
        }
        self.icon_label.setText(icons.get(self.icon_type, "📄"))
        self.icon_label.setFont(QFont("Segoe UI Emoji", 12))

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self.update_style()

    def update_style(self):
        if self.is_selected:
            self.setStyleSheet("""
                SidebarItem {
                    background-color: #e8f4fc;
                    border-left: 3px solid #1890ff;
                    border-radius: 0px;
                }
            """)
            self.text_label.setStyleSheet("color: #1890ff; background: transparent;")
        else:
            self.setStyleSheet("""
                SidebarItem {
                    background-color: transparent;
                    border: none;
                }
                SidebarItem:hover {
                    background-color: #f5f5f5;
                }
            """)
            self.text_label.setStyleSheet("color: #333333; background: transparent;")

    def mousePressEvent(self, event):
        self.clicked.emit(self.item_id)
        super().mousePressEvent(event)

    def retranslate_ui(self, text: str):
        """重新翻译"""
        if hasattr(self, 'text_label'):
            self.text_label.setText(text)
            self.update_icon()


class DropZone(QFrame):
    """拖拽上传区域"""
    clicked = pyqtSignal()
    files_dropped = pyqtSignal(list)

    def __init__(self, hint_text: str, support_text: str, icon_type: str = "blue", parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setup_ui(hint_text, support_text, icon_type)
        self.setStyleSheet("""
            DropZone {
                background-color: #fafbfc;
                border: 2px dashed #d9d9d9;
                border-radius: 12px;
            }
            DropZone:hover {
                border-color: #1890ff;
                background-color: #f0f7ff;
            }
        """)

    def setup_ui(self, hint_text: str, support_text: str, icon_type: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 50, 40, 50)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_widget = DropZoneIcon(icon_type)
        icon_widget.setFixedSize(100, 100)
        layout.addWidget(icon_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        self.hint_label = QLabel(hint_text)
        self.hint_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        self.hint_label.setStyleSheet("color: #333333; background: transparent; border: none;")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setWordWrap(True)  # 允许换行
        layout.addWidget(self.hint_label)

        self.support_label = QLabel(support_text)
        self.support_label.setFont(QFont("Microsoft YaHei", 9))
        self.support_label.setStyleSheet("color: #999999; background: transparent; border: none;")
        self.support_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.support_label.setWordWrap(True)  # 允许换行
        layout.addWidget(self.support_label)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
            self.setStyleSheet("""
                DropZone {
                    background-color: #e6f7ff;
                    border: 2px dashed #1890ff;
                    border-radius: 12px;
                }
            """)
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            DropZone {
                background-color: #fafbfc;
                border: 2px dashed #d9d9d9;
                border-radius: 12px;
            }
            DropZone:hover {
                border-color: #1890ff;
                background-color: #f0f7ff;
            }
        """)

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            event.accept()
            files = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    files.append(file_path)
                elif os.path.isdir(file_path):
                    for root, _, filenames in os.walk(file_path):
                        for filename in filenames:
                            files.append(os.path.join(root, filename))
            if files:
                self.files_dropped.emit(files)
        else:
            event.ignore()
        self.setStyleSheet("""
            DropZone {
                background-color: #fafbfc;
                border: 2px dashed #d9d9d9;
                border-radius: 12px;
            }
            DropZone:hover {
                border-color: #1890ff;
                background-color: #f0f7ff;
            }
        """)

    def retranslate_ui(self, hint_text: str, support_text: str):
        """重新翻译"""
        if hasattr(self, 'hint_label'):
            self.hint_label.setText(hint_text)
        if hasattr(self, 'support_label'):
            self.support_label.setText(support_text)


class DropZoneIcon(QWidget):
    """拖拽区域图标"""
    def __init__(self, icon_type: str = "blue", parent=None):
        super().__init__(parent)
        self.icon_type = icon_type

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.icon_type == "purple":
            main_color1 = "#c4b5fd"
            main_color2 = "#a78bfa"
            tag_color = "#a78bfa"
            circle_color = "#8b5cf6"
        else:
            main_color1 = "#7dd3fc"
            main_color2 = "#38bdf8"
            tag_color = "#60a5fa"
            circle_color = "#3b82f6"

        gradient = QLinearGradient(20, 15, 60, 70)
        gradient.setColorAt(0, QColor(main_color1))
        gradient.setColorAt(1, QColor(main_color2))

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(25, 15, 45, 55, 6, 6)

        painter.setPen(QPen(QColor("#ffffff"), 2))
        painter.drawLine(33, 30, 62, 30)
        painter.drawLine(33, 40, 62, 40)
        painter.drawLine(33, 50, 52, 50)

        painter.setBrush(QColor(tag_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(55, 5, 30, 18, 3, 3)
        painter.setPen(QPen(QColor("#ffffff"), 1))
        font = painter.font()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(55, 5, 30, 18, Qt.AlignmentFlag.AlignCenter, "CAJ")

        painter.setBrush(QColor(circle_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(35, 55, 30, 30)
        painter.setPen(QPen(QColor("#ffffff"), 2))
        painter.drawArc(42, 62, 16, 16, 30 * 16, 270 * 16)


class StepIndicator(QWidget):
    """步骤指示器"""
    def __init__(self, step_num: str, title: str, desc: str, parent=None):
        super().__init__(parent)
        self.setup_ui(step_num, title, desc)

    def setup_ui(self, step_num: str, title: str, desc: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.icon_label = QLabel("📁")
        self.icon_label.setFont(QFont("Segoe UI Emoji", 16))
        self.icon_label.setStyleSheet("color: #1890ff;")
        layout.addWidget(self.icon_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        self.title_label = QLabel(f"{step_num}、{title}")
        self.title_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #333333;")
        self.title_label.setWordWrap(True)  # 允许换行
        text_layout.addWidget(self.title_label)

        self.desc_label = QLabel(desc)
        self.desc_label.setFont(QFont("Microsoft YaHei", 9))
        self.desc_label.setStyleSheet("color: #999999;")
        self.desc_label.setWordWrap(True)  # 允许换行
        text_layout.addWidget(self.desc_label)

        layout.addLayout(text_layout)

    def retranslate_ui(self, step_num: str, title: str, desc: str):
        """重新翻译"""
        if hasattr(self, 'title_label'):
            self.title_label.setText(f"{step_num}、{title}")
        if hasattr(self, 'desc_label'):
            self.desc_label.setText(desc)


class PageSelectDialog(QWidget):
    """页码选择对话框"""
    page_selected = pyqtSignal(str, str)  # file_path, page_range

    def __init__(self, file_path: str, total_pages: int, current_selection: str = "all", parent=None):
        super().__init__(parent, Qt.WindowType.Popup)
        self.file_path = file_path
        self.total_pages = total_pages
        self.current_selection = current_selection
        self.setMinimumWidth(300)  # 改为最小宽度
        self.setup_ui()
        self.setStyleSheet("""
            PageSelectDialog {
                background-color: white;
                border: 1px solid #d9d9d9;
                border-radius: 8px;
            }
        """)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 标题
        title = QLabel(tr("convert.page.total_pages").format(total=self.total_pages))
        title.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        title.setStyleSheet("color: #333333;")
        title.setWordWrap(True)  # 允许换行
        layout.addWidget(title)

        # 选项组
        from PyQt6.QtWidgets import QRadioButton, QButtonGroup, QLineEdit
        self.btn_group = QButtonGroup(self)

        # 全部页面
        self.all_radio = QRadioButton(tr("convert.page.all_pages"))
        self.all_radio.setFont(QFont("Microsoft YaHei", 9))
        self.btn_group.addButton(self.all_radio, 0)
        layout.addWidget(self.all_radio)

        # 前N页
        first_layout = QHBoxLayout()
        self.first_radio = QRadioButton(tr("convert.page.first_pages"))
        self.first_radio.setFont(QFont("Microsoft YaHei", 9))
        self.btn_group.addButton(self.first_radio, 1)
        first_layout.addWidget(self.first_radio)

        self.first_input = QLineEdit("3")
        self.first_input.setFixedWidth(50)
        self.first_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                padding: 3px 8px;
            }
        """)
        first_layout.addWidget(self.first_input)

        first_layout.addWidget(QLabel(tr("convert.page.pages_unit")))
        first_layout.addStretch()
        layout.addLayout(first_layout)

        # 自定义范围
        custom_layout = QHBoxLayout()
        self.custom_radio = QRadioButton(tr("convert.page.custom_range"))
        self.custom_radio.setFont(QFont("Microsoft YaHei", 9))
        self.btn_group.addButton(self.custom_radio, 2)
        custom_layout.addWidget(self.custom_radio)

        self.custom_input = QLineEdit("1-10")
        self.custom_input.setFixedWidth(120)
        self.custom_input.setPlaceholderText(tr("convert.page.custom_placeholder"))
        self.custom_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                padding: 3px 8px;
            }
        """)
        custom_layout.addWidget(self.custom_input)
        custom_layout.addStretch()
        layout.addLayout(custom_layout)

        # 提示
        hint = QLabel(tr("convert.page.hint"))
        hint.setFont(QFont("Microsoft YaHei", 8))
        hint.setStyleSheet("color: #999999;")
        hint.setWordWrap(True)  # 允许换行
        layout.addWidget(hint)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton(tr("convert.page.cancel"))
        cancel_btn.setMinimumSize(80, 32) # 改为最小尺寸
        cancel_btn.setStyleSheet("""
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
        cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(cancel_btn)

        confirm_btn = QPushButton(tr("convert.page.confirm"))
        confirm_btn.setMinimumSize(80, 32) # 改为最小尺寸
        confirm_btn.setStyleSheet("""
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
        confirm_btn.clicked.connect(self.on_confirm)
        btn_layout.addWidget(confirm_btn)

        layout.addLayout(btn_layout)

        # 设置默认选中
        if self.current_selection == "all":
            self.all_radio.setChecked(True)
        elif self.current_selection.startswith(tr("convert.page.first_pages")):
            self.first_radio.setChecked(True)
            try:
                num = self.current_selection.replace(tr("convert.page.first_pages"), "").replace(tr("convert.page.pages_unit"), "")
                self.first_input.setText(num)
            except:
                pass
        else:
            self.custom_radio.setChecked(True)
            self.custom_input.setText(self.current_selection)

    def on_confirm(self):
        if self.all_radio.isChecked():
            result = tr("convert.page.all")
        elif self.first_radio.isChecked():
            num = self.first_input.text().strip()
            if not num.isdigit():
                num = "3"
            result = tr("convert.page.first_n_pages").format(num=num)
        else:
            result = self.custom_input.text().strip() or "1-10"

        self.page_selected.emit(self.file_path, result)
        self.close()


class FileListItem(QWidget):
    """文件列表项"""
    remove_clicked = pyqtSignal(str)
    refresh_clicked = pyqtSignal(str)
    open_folder_clicked = pyqtSignal(str)
    page_range_changed = pyqtSignal(str, str)

    def __init__(self, file_path: str, page_type: str = "caj_to_other", row_index: int = 0, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.page_type = page_type
        self.row_index = row_index
        self.page_count = 0
        self.page_range = tr("convert.page.all")
        self.setMinimumHeight(45)  # 改为最小高度
        self.setup_ui()
        if row_index % 2 == 0:
            self.setStyleSheet("background-color: #ffffff;")
        else:
            self.setStyleSheet("background-color: #fafafa;")

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 5, 15, 5) # 增加上下边距
        layout.setSpacing(0)

        # 文件名称 - 弹性宽度(3)，左对齐
        file_name = os.path.basename(self.file_path)
        display_name = self.truncate_filename(file_name, 40)
        self.name_label = QLabel(display_name)
        self.name_label.setFont(QFont("Microsoft YaHei", 10))
        self.name_label.setStyleSheet("color: #333333;")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.name_label.setMinimumWidth(150)
        self.name_label.setWordWrap(True) # 允许换行
        layout.addWidget(self.name_label, 3)  # stretch factor 3

        # 大小 - 弹性宽度(1)，居中
        try:
            size = os.path.getsize(self.file_path)
            size_str = self.format_size(size)
        except:
            size_str = tr("convert.page.unknown_size")
        self.size_label = QLabel(size_str)
        self.size_label.setFont(QFont("Microsoft YaHei", 9))
        self.size_label.setStyleSheet("color: #666666;")
        self.size_label.setMinimumWidth(60)
        self.size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.size_label.setWordWrap(True) # 允许换行
        layout.addWidget(self.size_label, 1)  # stretch factor 1

        # CAJ转其他和CAJ转图片都显示页数和页码选择
        if self.page_type in ["caj_to_other", "caj_to_image"]:
            # 页数 - 弹性宽度(1)，居中
            self.page_label = QLabel("0")
            self.page_label.setFont(QFont("Microsoft YaHei", 9))
            self.page_label.setStyleSheet("color: #666666;")
            self.page_label.setMinimumWidth(50)
            self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.page_label, 1)  # stretch factor 1

            # 页码选择 - 弹性宽度(1)，居中
            self.page_select_btn = QPushButton(tr("convert.page.all"))
            self.page_select_btn.setFont(QFont("Microsoft YaHei", 9))
            self.page_select_btn.setMinimumWidth(60)
            self.page_select_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.page_select_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    color: #1890ff;
                    text-align: center;
                    padding: 0 5px;
                }
                QPushButton:hover {
                    text-decoration: underline;
                }
            """)
            self.page_select_btn.clicked.connect(self.show_page_select_dialog)
            layout.addWidget(self.page_select_btn, 1)  # stretch factor 1
        else:
            # other_to_caj 不需要页数和页码选择
            self.page_label = None
            self.page_select_btn = None

        # 状态容器 - 弹性宽度(1)
        status_container = QWidget()
        status_container.setMinimumWidth(120)
        status_layout = QVBoxLayout(status_container)
        status_layout.setContentsMargins(8, 4, 8, 4)
        status_layout.setSpacing(4)
        status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.status_label = QLabel(tr("convert.page.status_pending"))
        self.status_label.setFont(QFont("Microsoft YaHei", 9))
        self.status_label.setStyleSheet("color: #666666;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True) # 允许换行
        status_layout.addWidget(self.status_label)

        # 进度条（隐藏）- 更宽更醒目
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedSize(100, 6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { 
                background-color: #e8e8e8; 
                border: none; 
                border-radius: 3px; 
            }
            QProgressBar::chunk { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1890ff, stop:1 #36cfc9);
                border-radius: 3px; 
            }
        """)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(status_container, 1)  # stretch factor 1

        # 操作按钮容器 - 弹性宽度(1)
        op_container = QWidget()
        op_container.setMinimumWidth(70)
        op_layout = QHBoxLayout(op_container)
        op_layout.setContentsMargins(0, 0, 0, 0)
        op_layout.setSpacing(8)
        op_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(28, 28)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.setStyleSheet("""
            QPushButton { background: transparent; border: 1px solid #d9d9d9; border-radius: 4px; }
            QPushButton:hover { border-color: #1890ff; background-color: #e6f7ff; }
        """)
        self.refresh_btn.clicked.connect(lambda: self.refresh_clicked.emit(self.file_path))
        op_layout.addWidget(self.refresh_btn)

        self.remove_btn = QPushButton("🗑")
        self.remove_btn.setFixedSize(28, 28)
        self.remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_btn.setStyleSheet("""
            QPushButton { background: transparent; border: 1px solid #d9d9d9; border-radius: 4px; }
            QPushButton:hover { border-color: #ff4444; background-color: #fff2f0; }
        """)
        self.remove_btn.clicked.connect(lambda: self.remove_clicked.emit(self.file_path))
        op_layout.addWidget(self.remove_btn)

        layout.addWidget(op_container, 1)  # stretch factor 1

    def truncate_filename(self, filename: str, max_length: int) -> str:
        """截断文件名，保留首尾关键信息"""
        if len(filename) <= max_length:
            return filename
        name, ext = os.path.splitext(filename)
        # 保留扩展名，计算可用长度
        available = max_length - len(ext) - 3  # 3 for "..."
        if available < 10:
            return filename[:max_length-3] + "..."
        # 保留前半部分和后半部分
        front = available // 2
        back = available - front
        return name[:front] + "..." + name[-back:] + ext

    def show_page_select_dialog(self):
        """显示页码选择对话框"""
        if self.page_count <= 0:
            QMessageBox.information(self, tr("common.hint"), tr("convert.page.wait_pages"))
            return

        dialog = PageSelectDialog(self.file_path, self.page_count, self.page_range, self)
        dialog.page_selected.connect(self.on_page_selected)

        # 计算弹出位置
        btn_pos = self.page_select_btn.mapToGlobal(self.page_select_btn.rect().bottomLeft())
        dialog.move(btn_pos)
        dialog.show()

    def on_page_selected(self, file_path: str, page_range: str):
        """页码选择完成"""
        self.page_range = page_range
        self.page_select_btn.setText(page_range)
        self.page_range_changed.emit(file_path, page_range)

    def format_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

    def set_status(self, status: str, color: str = "#1890ff"):
        self.status_label.setText(status)
        self.status_label.setStyleSheet(f"color: {color};")
        # 转换中时显示进度条
        if tr("convert.page.status_converting").split()[0] in status:
            self.progress_bar.setVisible(True)
        elif tr("convert.page.status_pending") in status or tr("convert.page.status_waiting") in status:
            self.progress_bar.setVisible(False)
            self.progress_bar.setValue(0)

    def set_progress(self, value: int):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(value)
        # 更新状态文本显示百分比
        self.status_label.setText(tr("convert.page.status_converting").format(percent=value))
        self.status_label.setStyleSheet("color: #1890ff;")

    def set_page_count(self, count: int):
        self.page_count = count
        if hasattr(self, 'page_label'):
            self.page_label.setText(str(count))

    def get_page_range(self) -> str:
        """获取页码范围"""
        return self.page_range

    def set_success(self):
        self.status_label.setText(tr("convert.page.status_success"))
        self.status_label.setStyleSheet("color: #52c41a; font-weight: bold;")
        self.progress_bar.setValue(100)
        self.progress_bar.setStyleSheet("""
            QProgressBar { 
                background-color: #e8e8e8; 
                border: none; 
                border-radius: 3px; 
            }
            QProgressBar::chunk { 
                background-color: #52c41a;
                border-radius: 3px; 
            }
        """)
        # 延迟隐藏进度条
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1500, lambda: self.progress_bar.setVisible(False))

    def retranslate_ui(self):
        """重新翻译"""
        if hasattr(self, 'size_label'):
            try:
                size = os.path.getsize(self.file_path)
                size_str = self.format_size(size)
            except:
                size_str = tr("convert.page.unknown_size")
            self.size_label.setText(size_str)
        
        if hasattr(self, 'page_select_btn'):
            # 这里如果用户改了页码，再切语言，可能会丢失用户的页码选择文本（如果是自定义的）
            # 但 tr("convert.page.all") 是最常见的
            if self.page_range == "全部": # 之前的中文
                 self.page_range = tr("convert.page.all")
            self.page_select_btn.setText(self.page_range)
            
        if hasattr(self, 'status_label'):
            # 这里的状态很难完美重新翻译，因为可能处于各种中间状态
            # 我们至少更新待处理状态
            if self.status_label.text() in ["待处理", "Pending"]:
                self.status_label.setText(tr("convert.page.status_pending"))


class ConvertThread(QThread):
    """转换线程"""
    progress = pyqtSignal(str, int)  # file_path, progress
    finished = pyqtSignal(str, bool, str)  # file_path, success, message
    all_finished = pyqtSignal()

    def __init__(self, files: list, output_dir: str, output_format: str, page_type: str, 
                 long_image: bool = False, quality: str = None, page_ranges: dict = None):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.output_format = output_format
        self.page_type = page_type
        self.long_image = long_image
        self.quality = quality or tr("convert.page.bottom.high")
        self.page_ranges = page_ranges or {}  # {file_path: page_range_str}
        self.max_pages_per_long_image = 10  # 长图最大页数

    def parse_page_range(self, page_range: str, total_pages: int) -> list:
        """解析页码范围字符串，返回页码列表"""
        if not page_range or page_range == tr("convert.page.all"):
            return list(range(1, total_pages + 1))

        if page_range.startswith(tr("convert.page.first_pages")):
            try:
                num = int(page_range.replace(tr("convert.page.first_pages"), "").replace(tr("convert.page.pages_unit"), ""))
                return list(range(1, min(num + 1, total_pages + 1)))
            except:
                return list(range(1, total_pages + 1))

        # 解析自定义范围，如 "1-5,8,10-12"
        pages = set()
        parts = page_range.replace(" ", "").split(",")
        for part in parts:
            if "-" in part:
                try:
                    start, end = part.split("-")
                    start = max(1, int(start))
                    end = min(int(end), total_pages)
                    pages.update(range(start, end + 1))
                except:
                    pass
            else:
                try:
                    page = int(part)
                    if 1 <= page <= total_pages:
                        pages.add(page)
                except:
                    pass

        return sorted(list(pages)) if pages else list(range(1, total_pages + 1))

    def run(self):
        try:
            import sys
            import os
            # 确保能找到 core 模块
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if app_dir not in sys.path:
                sys.path.insert(0, app_dir)
            # 确保能找到 caj2pdf 库
            lib_path = os.path.join(app_dir, "lib", "caj2pdf")
            if lib_path not in sys.path:
                sys.path.insert(0, lib_path)
            
            from core.converter import CAJConverter
            converter = CAJConverter()
        except ImportError as e:
            import traceback
            for file_path in self.files:
                self.finished.emit(file_path, False, f"导入转换模块失败: {e}\n{traceback.format_exc()}")
            self.all_finished.emit()
            return

        for file_path in self.files:
            try:
                self.progress.emit(file_path, 10)
                base_name = Path(file_path).stem
                
                # 获取页码范围
                page_range = self.page_ranges.get(file_path, tr("convert.page.all"))
                
                if self.page_type == "caj_to_image":
                    # 转换为图片
                    result = converter.convert_to_image(
                        file_path,
                        self.output_dir,
                        self.output_format,
                        long_image=self.long_image,
                        quality=self.quality,
                        page_range=page_range,
                        max_pages_per_long_image=self.max_pages_per_long_image,
                        progress_callback=lambda p: self.progress.emit(file_path, p)
                    )
                elif self.output_format == "pdf":
                    output_path = os.path.join(self.output_dir, f"{base_name}.pdf")
                    result = converter.convert_to_pdf(
                        file_path,
                        output_path,
                        page_range=page_range,
                        progress_callback=lambda p: self.progress.emit(file_path, p)
                    )
                elif self.output_format in ["doc", "docx"]:
                    output_path = os.path.join(self.output_dir, f"{base_name}.{self.output_format}")
                    result = converter.convert_to_word(
                        file_path,
                        output_path,
                        self.output_format,
                        page_range=page_range,
                        progress_callback=lambda p: self.progress.emit(file_path, p)
                    )
                elif self.output_format == "txt":
                    output_path = os.path.join(self.output_dir, f"{base_name}.txt")
                    result = converter.convert_to_txt(
                        file_path,
                        output_path,
                        page_range=page_range,
                        progress_callback=lambda p: self.progress.emit(file_path, p)
                    )
                elif self.output_format == "caj":
                    # 其他格式转CAJ
                    output_path = os.path.join(self.output_dir, f"{base_name}.caj")
                    result = converter.convert_to_caj(
                        file_path,
                        output_path,
                        progress_callback=lambda p: self.progress.emit(file_path, p)
                    )
                else:
                    result = type('Result', (), {'success': False, 'error_msg': tr("converter.error_unsupported_format").format(format=self.output_format)})()

                self.finished.emit(file_path, result.success, result.error_msg if not result.success else tr("converter.success"))
            except Exception as e:
                import traceback
                error_msg = f"{tr('converter.failure').format(error=str(e))}\n\n详细信息:\n{traceback.format_exc()}"
                self.finished.emit(file_path, False, error_msg)

        self.all_finished.emit()


class ConvertPage(QWidget):
    """转换页面"""
    go_home = pyqtSignal()
    switch_page = pyqtSignal(str)  # 切换到其他功能页面

    def __init__(self, page_type: str = "caj_to_other", parent=None):
        super().__init__(parent)
        self.page_type = page_type
        self.current_menu = page_type
        self.file_list = []  # 存储文件路径
        self.file_widgets = {}  # 文件路径 -> FileListItem
        self.convert_thread = None
        self.output_dir = os.path.expanduser("~/Desktop")
        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.create_sidebar(main_layout)
        self.create_content_area(main_layout)

    def create_sidebar(self, parent_layout):
        """创建左侧边栏"""
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-right: 1px solid #f0f0f0;
            }
        """)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 15, 0, 15)
        layout.setSpacing(5)

        self.home_item = SidebarItem("home", tr("convert.page.sidebar.home"), "home")
        self.home_item.clicked.connect(self.on_menu_clicked)
        layout.addWidget(self.home_item)

        layout.addSpacing(10)

        self.menu_items = {}
        menu_data = [
            ("caj_to_other", tr("convert.page.sidebar.caj_to_other"), "caj_to_other"),
            ("caj_to_image", tr("convert.page.sidebar.caj_to_image"), "caj_to_image"),
            ("other_to_caj", tr("convert.page.sidebar.other_to_caj"), "other_to_caj"),
        ]

        for icon_type, text, item_id in menu_data:
            item = SidebarItem(icon_type, text, item_id)
            item.clicked.connect(self.on_menu_clicked)
            self.menu_items[item_id] = item
            layout.addWidget(item)

        if self.page_type in self.menu_items:
            self.menu_items[self.page_type].set_selected(True)

        layout.addStretch()
        
        # 侧边栏广告 - 2:3比例
        self.side_ad = AdSideCarousel(
            soft_number="10004",
            ad_positions=["adv_position_04", "adv_position_05"],
            width=180
        )
        layout.addWidget(self.side_ad, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(15)
        
        parent_layout.addWidget(sidebar)

    def create_content_area(self, parent_layout):
        """创建右侧内容区"""
        self.content = QWidget()
        self.content.setStyleSheet("""
            background-color: #f5f7fa;
            QToolTip {
                background-color: #333333;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 10px;
            }
        """)

        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(20, 15, 20, 15)
        self.content_layout.setSpacing(15)

        # 顶部工具栏
        self.create_toolbar(self.content_layout)

        # 使用 StackedWidget 切换空状态和文件列表
        self.stacked_content = QStackedWidget()

        # 空状态 - 拖拽区域
        self.create_drop_area()

        # 文件列表视图
        self.create_file_list_view()

        self.content_layout.addWidget(self.stacked_content, 1)

        # 底部选项区域（仅在有文件时显示）
        self.create_bottom_options()

        # 底部步骤指示
        self.create_steps_indicator(self.content_layout)

        # 版本号
        self.create_version_info(self.content_layout)

        parent_layout.addWidget(self.content)

    def create_bottom_options(self):
        """创建底部选项区域"""
        from PyQt6.QtWidgets import QCheckBox, QRadioButton, QButtonGroup

        # 第一行：输出格式
        self.options_row = QWidget()
        self.options_row.setStyleSheet("background-color: transparent;")
        options_layout = QHBoxLayout(self.options_row)
        options_layout.setContentsMargins(0, 10, 0, 5)
        options_layout.setSpacing(15)

        # 输出格式标签
        format_label = QLabel(tr("convert.page.bottom.output_format"))
        format_label.setFont(QFont("Microsoft YaHei", 10))
        format_label.setStyleSheet("color: #666666;")
        format_label.setWordWrap(True) # 允许换行
        options_layout.addWidget(format_label)

        # CAJ转其他 - 单选按钮组
        self.format_radio_container = QWidget()
        format_radio_layout = QHBoxLayout(self.format_radio_container)
        format_radio_layout.setContentsMargins(0, 0, 0, 0)
        format_radio_layout.setSpacing(15)

        self.format_btn_group = QButtonGroup(self)
        radio_style = """
            QRadioButton {
                color: #666666;
                spacing: 5px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
            QRadioButton::indicator:checked {
                background: #1890ff;
                border: 2px solid #1890ff;
                border-radius: 8px;
            }
            QRadioButton::indicator:unchecked {
                background: white;
                border: 2px solid #d9d9d9;
                border-radius: 8px;
            }
            QRadioButton::indicator:hover {
                border-color: #1890ff;
            }
        """

        self.format_radios = {}
        for fmt in ["pdf", "doc", "docx", "txt"]:
            radio = QRadioButton(fmt)
            radio.setFont(QFont("Microsoft YaHei", 10))
            radio.setStyleSheet(radio_style)
            self.format_btn_group.addButton(radio)
            self.format_radios[fmt] = radio
            format_radio_layout.addWidget(radio)

        self.format_radios["pdf"].setChecked(True)  # 默认选中pdf
        options_layout.addWidget(self.format_radio_container)

        # CAJ转图片 - 下拉框（保留原有）
        self.format_combo_container = QWidget()
        format_combo_layout = QHBoxLayout(self.format_combo_container)
        format_combo_layout.setContentsMargins(0, 0, 0, 0)
        format_combo_layout.setSpacing(8)

        self.format_combo = QComboBox()
        self.format_combo.setFont(QFont("Microsoft YaHei", 10))
        self.format_combo.setMinimumWidth(100) # 改为最小宽度
        self.format_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                padding: 5px 10px;
                background: white;
            }
            QComboBox:hover {
                border-color: #1890ff;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #d9d9d9;
                background: white;
                selection-background-color: #e6f7ff;
                selection-color: #1890ff;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                height: 30px;
                padding: 5px 10px;
            }
        """)
        format_combo_layout.addWidget(self.format_combo)
        options_layout.addWidget(self.format_combo_container)

        options_layout.addSpacing(10)

        # 输出质量容器（仅图片转换显示）
        self.quality_container = QWidget()
        quality_layout = QHBoxLayout(self.quality_container)
        quality_layout.setContentsMargins(0, 0, 0, 0)
        quality_layout.setSpacing(8)

        self.quality_label = QLabel(tr("convert.page.bottom.quality"))
        self.quality_label.setFont(QFont("Microsoft YaHei", 10))
        self.quality_label.setStyleSheet("color: #666666;")
        self.quality_label.setWordWrap(True) # 允许换行
        quality_layout.addWidget(self.quality_label)

        self.quality_combo = QComboBox()
        self.quality_combo.setFont(QFont("Microsoft YaHei", 10))
        self.quality_combo.setMinimumWidth(80) # 改为最小宽度
        self.quality_combo.addItems([tr("convert.page.bottom.high"), tr("convert.page.bottom.medium"), tr("convert.page.bottom.low")])
        self.quality_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                padding: 5px 10px;
                background: white;
            }
            QComboBox:hover {
                border-color: #1890ff;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #d9d9d9;
                background: white;
                selection-background-color: #e6f7ff;
                selection-color: #1890ff;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                height: 30px;
                padding: 5px 10px;
            }
        """)
        quality_layout.addWidget(self.quality_combo)
        options_layout.addWidget(self.quality_container)

        options_layout.addSpacing(10)

        # 输出竖屏长图容器
        self.long_image_container = QWidget()
        long_image_layout = QHBoxLayout(self.long_image_container)
        long_image_layout.setContentsMargins(0, 0, 0, 0)
        long_image_layout.setSpacing(8)

        self.long_image_checkbox = QCheckBox(tr("convert.page.bottom.long_image"))
        self.long_image_checkbox.setFont(QFont("Microsoft YaHei", 10))
        self.long_image_checkbox.setChecked(True)
        self.long_image_checkbox.setStyleSheet("""
            QCheckBox {
                color: #666666;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #d9d9d9;
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
        self.long_image_checkbox.stateChanged.connect(self.on_long_image_changed)
        # self.long_image_checkbox.setWordWrap(True) # QCheckBox 没有 setWordWrap
        long_image_layout.addWidget(self.long_image_checkbox)
        options_layout.addWidget(self.long_image_container)

        options_layout.addStretch()  # 右侧弹性空间

        # 第二行：输出目录 + 开始转换按钮
        self.output_row = QWidget()
        output_row_layout = QHBoxLayout(self.output_row)
        output_row_layout.setContentsMargins(0, 5, 0, 10)
        output_row_layout.setSpacing(10)

        output_label = QLabel(tr("convert.page.bottom.output_dir"))
        output_label.setFont(QFont("Microsoft YaHei", 10))
        output_label.setStyleSheet("color: #666666;")
        output_label.setWordWrap(True) # 允许换行
        output_row_layout.addWidget(output_label)

        # 输出目录下拉框 - 弹性宽度
        self.output_dir_combo = QComboBox()
        self.output_dir_combo.setFont(QFont("Microsoft YaHei", 9))
        self.output_dir_combo.setMinimumWidth(350) # 改为最小宽度
        self.output_dir_combo.setEditable(True)
        self.output_dir_combo.addItem(self.output_dir)
        self.output_dir_combo.addItem(tr("convert.page.output_same_as_source"))
        self.output_dir_combo.addItem(tr("convert.page.output_custom"))
        self.output_dir_combo.setStyleSheet("""
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
                subcontrol-position: right center;
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
        """)
        self.output_dir_combo.currentIndexChanged.connect(self.on_output_dir_changed)
        output_row_layout.addWidget(self.output_dir_combo, 1) # 增加权重

        # 浏览按钮
        browse_btn = QPushButton("📁")
        browse_btn.setFixedSize(32, 32)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setStyleSheet("""
            QPushButton {
                background: white;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                border-color: #1890ff;
                background-color: #e6f7ff;
            }
        """)
        browse_btn.clicked.connect(self.browse_output_dir)
        output_row_layout.addWidget(browse_btn)

        output_row_layout.addStretch()  # 弹性空间，让按钮靠右

        # 开始转换按钮
        self.convert_btn = QPushButton(tr("convert.page.bottom.start_convert"))
        self.convert_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self.convert_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.convert_btn.setMinimumSize(140, 40) # 改为最小尺寸
        self.convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
                border: none;
                border-radius: 6px;
                color: white;
                padding: 0 15px;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
            QPushButton:disabled {
                background-color: #d9d9d9;
            }
        """)
        self.convert_btn.clicked.connect(self.start_convert)
        output_row_layout.addWidget(self.convert_btn)

        # 底部选项容器
        bottom_container = QWidget()
        bottom_container_layout = QVBoxLayout(bottom_container)
        bottom_container_layout.setContentsMargins(0, 0, 0, 0)
        bottom_container_layout.setSpacing(0)
        bottom_container_layout.addWidget(self.options_row)
        bottom_container_layout.addWidget(self.output_row)

        self.bottom_options_container = bottom_container
        self.bottom_options_container.setVisible(False)
        self.content_layout.addWidget(self.bottom_options_container)

        # 初始化格式选项
        self.update_format_options()
        # 更新可见性
        self.update_bottom_options_visibility()

        # 底部选项容器
        bottom_container = QWidget()
        bottom_container_layout = QVBoxLayout(bottom_container)
        bottom_container_layout.setContentsMargins(0, 0, 0, 0)
        bottom_container_layout.setSpacing(0)
        bottom_container_layout.addWidget(self.options_row)
        bottom_container_layout.addWidget(self.output_row)

        self.bottom_options_container = bottom_container
        self.bottom_options_container.setVisible(False)
        self.content_layout.addWidget(self.bottom_options_container)

        # 初始化格式选项
        self.update_format_options()
        # 更新可见性
        self.update_bottom_options_visibility()

    def on_output_dir_changed(self, index: int):
        """输出目录选择变化"""
        text = self.output_dir_combo.currentText()
        if text == tr("convert.page.output_same_as_source"):
            # 使用源文件所在目录
            if self.file_list:
                self.output_dir = os.path.dirname(self.file_list[0])
        elif text == tr("convert.page.output_custom"):
            # 打开文件夹选择对话框
            self.browse_output_dir()
        else:
            self.output_dir = text

    def on_long_image_changed(self, state: int):
        """竖屏长图选项变化 - 提供视觉反馈"""
        if state == 2:  # Checked
            self.long_image_checkbox.setStyleSheet("""
                QCheckBox {
                    color: #1890ff;
                    spacing: 5px;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                    border: 1px solid #1890ff;
                    border-radius: 3px;
                    background: #1890ff;
                }
                QCheckBox::indicator:hover {
                    border-color: #40a9ff;
                }
            """)
        else:
            self.long_image_checkbox.setStyleSheet("""
                QCheckBox {
                    color: #666666;
                    spacing: 5px;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                    border: 1px solid #d9d9d9;
                    border-radius: 3px;
                    background: white;
                }
                QCheckBox::indicator:hover {
                    border-color: #1890ff;
                }
            """)

    def browse_output_dir(self):
        """浏览输出目录"""
        folder = QFileDialog.getExistingDirectory(self, tr("convert.page.select_output_dir"), self.output_dir)
        if folder:
            self.output_dir = folder
            self.output_dir_combo.setCurrentText(folder)

    def update_bottom_options_visibility(self):
        """更新底部选项可见性"""
        is_image_mode = self.page_type == "caj_to_image"
        is_caj_to_other = self.page_type == "caj_to_other"
        is_other_to_caj = self.page_type == "other_to_caj"
        
        # CAJ转其他显示单选按钮组，CAJ转图片显示下拉框，其他转CAJ不显示格式选项
        self.format_radio_container.setVisible(is_caj_to_other)
        self.format_combo_container.setVisible(is_image_mode)
        
        # 输出质量和竖屏长图仅图片模式显示
        self.quality_container.setVisible(is_image_mode)
        self.long_image_container.setVisible(is_image_mode)
        
        # 其他转CAJ时隐藏输出格式标签（因为格式固定为caj）
        if hasattr(self, 'options_row'):
            # 找到输出格式标签并设置可见性
            for i in range(self.options_row.layout().count()):
                widget = self.options_row.layout().itemAt(i).widget()
                if widget and isinstance(widget, QLabel) and widget.text() == tr("convert.page.bottom.output_format"):
                    widget.setVisible(not is_other_to_caj)
                    break

    def create_toolbar(self, parent_layout):
        """创建顶部工具栏"""
        toolbar = QWidget()
        toolbar.setStyleSheet("background-color: transparent;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(15)

        # 添加文件按钮
        self.add_file_btn = QPushButton("📄 " + tr("convert.page.toolbar.add_files"))
        self.add_file_btn.setFont(QFont("Microsoft YaHei", 10))
        self.add_file_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_file_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #333333;
                padding: 8px 15px;
            }
            QPushButton:hover {
                color: #1890ff;
            }
        """)
        self.add_file_btn.clicked.connect(self.on_add_file)
        toolbar_layout.addWidget(self.add_file_btn)

        # 添加文件夹按钮
        self.add_folder_btn = QPushButton("📁 " + tr("convert.page.toolbar.add_folder"))
        self.add_folder_btn.setFont(QFont("Microsoft YaHei", 10))
        self.add_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #333333;
                padding: 8px 15px;
            }
            QPushButton:hover {
                color: #1890ff;
            }
        """)
        self.add_folder_btn.clicked.connect(self.on_add_folder)
        toolbar_layout.addWidget(self.add_folder_btn)

        toolbar_layout.addStretch()

        # 文件计数标签
        self.file_count_label = QLabel(tr("convert.page.list_header.name") + "（0）")
        self.file_count_label.setFont(QFont("Microsoft YaHei", 10))
        self.file_count_label.setStyleSheet("color: #666666;")
        self.file_count_label.setVisible(False)
        toolbar_layout.addWidget(self.file_count_label)

        toolbar_layout.addStretch()

        # 清空列表按钮
        self.clear_btn = QPushButton("🗑 " + tr("convert.page.toolbar.clear_all"))
        self.clear_btn.setFont(QFont("Microsoft YaHei", 10))
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #666666;
                padding: 8px 15px;
            }
            QPushButton:hover {
                color: #ff4444;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_file_list)
        toolbar_layout.addWidget(self.clear_btn)

        parent_layout.addWidget(toolbar)

    def create_drop_area(self):
        """创建拖拽上传区域"""
        drop_container = QWidget()
        drop_layout = QVBoxLayout(drop_container)
        drop_layout.setContentsMargins(0, 0, 0, 0)

        hint_text, support_text, icon_type = self.get_hints()
        self.drop_zone = DropZone(hint_text, support_text, icon_type)
        self.drop_zone.setMinimumHeight(200)
        self.drop_zone.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.drop_zone.clicked.connect(self.on_add_file)
        self.drop_zone.files_dropped.connect(self.add_files)

        drop_layout.addWidget(self.drop_zone)
        self.stacked_content.addWidget(drop_container)

    def create_file_list_view(self):
        """创建文件列表视图"""
        list_container = QWidget()
        list_container.setStyleSheet("background-color: white; border-radius: 8px;")
        list_container.setMinimumWidth(720)  # 设置最小宽度
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)

        # 列表头容器 - 固定高度，边距与列表项一致
        self.list_header = QWidget()
        self.list_header.setFixedHeight(45)
        self.list_header.setMinimumWidth(720)
        self.list_header.setStyleSheet("background-color: #fafafa; border-bottom: 1px solid #f0f0f0;")
        self.list_header_layout = QHBoxLayout(self.list_header)
        self.list_header_layout.setContentsMargins(15, 0, 15, 0)  # 与FileListItem一致
        self.list_header_layout.setSpacing(0)

        self.update_list_header()

        list_layout.addWidget(self.list_header)

        # 文件列表滚动区域
        from PyQt6.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: white;
            }
            QScrollBar:vertical {
                background: #f5f5f5;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #d9d9d9;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #bfbfbf;
            }
            QScrollBar:horizontal {
                background: #f5f5f5;
                height: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: #d9d9d9;
                border-radius: 4px;
                min-width: 30px;
            }
        """)

        self.file_list_widget = QWidget()
        self.file_list_widget.setMinimumWidth(720)
        self.file_list_widget.setStyleSheet("background-color: white;")
        self.file_list_layout = QVBoxLayout(self.file_list_widget)
        self.file_list_layout.setContentsMargins(0, 0, 0, 0)
        self.file_list_layout.setSpacing(0)
        self.file_list_layout.addStretch()

        scroll_area.setWidget(self.file_list_widget)
        list_layout.addWidget(scroll_area, 1)

        self.stacked_content.addWidget(list_container)

    def update_list_header(self):
        """更新列表头"""
        # 清空现有header
        while self.list_header_layout.count():
            item = self.list_header_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 文件名称(数量) - 弹性宽度(3)，左对齐
        count = len(self.file_list) if hasattr(self, 'file_list') else 0
        name_label = QLabel(tr("convert.page.list_header.name") + f"（{count}）")
        name_label.setFont(QFont("Microsoft YaHei", 10))
        name_label.setStyleSheet("color: #666666;")
        name_label.setMinimumWidth(150)
        name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.list_header_layout.addWidget(name_label, 3)  # stretch factor 3

        # 大小 - 弹性宽度(1)，居中
        size_label = QLabel(tr("convert.page.list_header.size"))
        size_label.setFont(QFont("Microsoft YaHei", 10))
        size_label.setStyleSheet("color: #666666;")
        size_label.setMinimumWidth(60)
        size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.list_header_layout.addWidget(size_label, 1)  # stretch factor 1

        # CAJ转其他和CAJ转图片都显示页数和页码选择
        if self.page_type in ["caj_to_other", "caj_to_image"]:
            # 页数 - 弹性宽度(1)，居中
            page_label = QLabel(tr("convert.page.list_header.pages"))
            page_label.setFont(QFont("Microsoft YaHei", 10))
            page_label.setStyleSheet("color: #666666;")
            page_label.setMinimumWidth(50)
            page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_header_layout.addWidget(page_label, 1)  # stretch factor 1

            # 页码选择 - 弹性宽度(1)，居中
            select_label = QLabel(tr("convert.page.list_header.page_select"))
            select_label.setFont(QFont("Microsoft YaHei", 10))
            select_label.setStyleSheet("color: #666666;")
            select_label.setMinimumWidth(60)
            select_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_header_layout.addWidget(select_label, 1)  # stretch factor 1

        # 状态 - 弹性宽度(1)，居中
        status_label = QLabel(tr("convert.page.list_header.status"))
        status_label.setFont(QFont("Microsoft YaHei", 10))
        status_label.setStyleSheet("color: #666666;")
        status_label.setMinimumWidth(120)
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.list_header_layout.addWidget(status_label, 1)  # stretch factor 1

        # 操作 - 弹性宽度(1)，居中
        op_label = QLabel(tr("convert.page.list_header.operation"))
        op_label.setFont(QFont("Microsoft YaHei", 10))
        op_label.setStyleSheet("color: #666666;")
        op_label.setMinimumWidth(70)
        op_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.list_header_layout.addWidget(op_label, 1)  # stretch factor 1

    def on_polling_progress(self, message: str):
        """轮询进度更新"""
        pass

    def retranslate_ui(self):
        """重新翻译 UI"""
        # 侧边栏
        if hasattr(self, 'home_item'):
            self.home_item.retranslate_ui(tr("convert.page.sidebar.home"))
        
        menu_data = {
            "caj_to_other": tr("convert.page.sidebar.caj_to_other"),
            "caj_to_image": tr("convert.page.sidebar.caj_to_image"),
            "other_to_caj": tr("convert.page.sidebar.other_to_caj"),
        }
        for item_id, text in menu_data.items():
            if item_id in self.menu_items:
                self.menu_items[item_id].retranslate_ui(text)

        # 工具栏
        if hasattr(self, 'add_file_btn'):
            self.add_file_btn.setText("📄 " + tr("convert.page.toolbar.add_files"))
        if hasattr(self, 'add_folder_btn'):
            self.add_folder_btn.setText("📁 " + tr("convert.page.toolbar.add_folder"))
        if hasattr(self, 'clear_btn'):
            self.clear_btn.setText("🗑 " + tr("convert.page.toolbar.clear_all"))
        
        # 拖拽区域
        hint_text, support_text, _ = self.get_hints()
        if hasattr(self, 'drop_zone'):
            self.drop_zone.retranslate_ui(hint_text, support_text)

        # 底部选项
        if hasattr(self, 'options_row'):
            # 找到输出格式标签并设置可见性
            for i in range(self.options_row.layout().count()):
                widget = self.options_row.layout().itemAt(i).widget()
                if widget and isinstance(widget, QLabel) and widget.text().startswith(tr("convert.page.bottom.output_format", "Output")): # 模糊匹配旧的
                    widget.setText(tr("convert.page.bottom.output_format"))
                    
        if hasattr(self, 'quality_label'):
            self.quality_label.setText(tr("convert.page.bottom.quality"))
        if hasattr(self, 'quality_combo'):
            old_idx = self.quality_combo.currentIndex()
            self.quality_combo.clear()
            self.quality_combo.addItems([tr("convert.page.bottom.high"), tr("convert.page.bottom.medium"), tr("convert.page.bottom.low")])
            self.quality_combo.setCurrentIndex(old_idx)
        if hasattr(self, 'long_image_checkbox'):
            self.long_image_checkbox.setText(tr("convert.page.bottom.long_image"))
        if hasattr(self, 'output_row'):
            for i in range(self.output_row.layout().count()):
                widget = self.output_row.layout().itemAt(i).widget()
                if widget and isinstance(widget, QLabel) and widget.text().startswith(tr("convert.page.bottom.output_dir", "Output")):
                    widget.setText(tr("convert.page.bottom.output_dir"))
        if hasattr(self, 'output_dir_combo'):
            # 复杂逻辑，暂时只更新翻译项
            for i in range(self.output_dir_combo.count()):
                if self.output_dir_combo.itemText(i) in [tr("convert.page.output_same_as_source", "old"), "同源目录"]:
                     self.output_dir_combo.setItemText(i, tr("convert.page.output_same_as_source"))
                if self.output_dir_combo.itemText(i) in [tr("convert.page.output_custom", "old"), "自定义..."]:
                     self.output_dir_combo.setItemText(i, tr("convert.page.output_custom"))
                     
        if hasattr(self, 'convert_btn'):
            self.convert_btn.setText(tr("convert.page.bottom.start_convert"))

        # 步骤指示器
        if hasattr(self, 'step1'):
            self.step1.retranslate_ui("1", tr("convert.page.step1_title"), tr("convert.page.step1_desc"))
        if hasattr(self, 'step2'):
            self.step2.retranslate_ui("2", tr("convert.page.step2_title"), tr("convert.page.step2_desc"))
        if hasattr(self, 'step3'):
            self.step3.retranslate_ui("3", tr("convert.page.step3_title"), tr("convert.page.step3_desc"))

        # 版本号和品牌信息
        if hasattr(self, 'brand_text'):
            self.brand_text.setText(tr("main_window.brand_text"))
        if hasattr(self, 'version_label'):
            from core.constants import CURRENT_VERSION
            self.version_label.setText(tr("main_window.version").format(version=CURRENT_VERSION))

        # 文件列表头
        self.update_list_header()
        
        # 刷新所有列表项 (可选，根据需求)
        for item in self.file_widgets.values():
             if hasattr(item, "retranslate_ui"):
                 item.retranslate_ui()

    def update_format_options(self):
        """更新格式选项"""
        # CAJ转图片使用下拉框
        self.format_combo.clear()
        if self.page_type == "caj_to_image":
            self.format_combo.addItems(["PNG", "JPG", "BMP"])
        else:
            self.format_combo.addItems(["CAJ"])

    def get_hints(self):
        """根据页面类型获取提示文字和图标类型"""
        hints = {
            "caj_to_other": (tr("convert.page.drop_zone.hint"), tr("convert.page.drop_zone.caj_to_other_support"), "blue"),
            "caj_to_image": (tr("convert.page.drop_zone.hint"), tr("convert.page.drop_zone.caj_to_image_support"), "blue"),
            "other_to_caj": (tr("convert.page.drop_zone.hint"), tr("convert.page.drop_zone.other_to_caj_support"), "purple"),
        }
        return hints.get(self.page_type, hints["caj_to_other"])

    def get_file_filter(self):
        """获取文件过滤器"""
        if self.page_type in ["caj_to_other", "caj_to_image"]:
            return "CAJ文件 (*.caj);;所有文件 (*.*)"
        elif self.page_type == "other_to_caj":
            return "支持的文件 (*.pdf *.doc *.docx *.txt *.jpg *.jpeg *.png *.bmp);;PDF文件 (*.pdf);;Word文件 (*.doc *.docx);;文本文件 (*.txt);;图片文件 (*.jpg *.jpeg *.png *.bmp);;所有文件 (*.*)"
        else:
            return "文档文件 (*.pdf *.doc *.docx);;所有文件 (*.*)"

    def on_add_file(self):
        """添加文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            tr("convert.page.dialogs.select_files"),
            "",
            self.get_file_filter()
        )
        if files:
            self.add_files(files)

    def on_add_folder(self):
        """添加文件夹"""
        folder = QFileDialog.getExistingDirectory(self, tr("convert.page.dialogs.select_folder"))
        if folder:
            files = []
            ext = ".caj" if self.page_type in ["caj_to_other", "caj_to_image"] else None
            for root, _, filenames in os.walk(folder):
                for filename in filenames:
                    if ext is None or filename.lower().endswith(ext):
                        files.append(os.path.join(root, filename))
            if files:
                self.add_files(files)
            else:
                QMessageBox.information(self, tr("common.hint"), tr("convert.page.dialogs.no_files"))

    def add_files(self, files: list):
        """添加文件到列表"""
        # 根据页面类型确定支持的扩展名
        if self.page_type in ["caj_to_other", "caj_to_image"]:
            valid_exts = [".caj"]
        elif self.page_type == "other_to_caj":
            valid_exts = [".pdf", ".doc", ".docx", ".txt", ".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif"]
        else:
            valid_exts = None  # 不限制
        
        added = 0

        for file_path in files:
            if file_path in self.file_list:
                continue
            
            # 检查扩展名
            if valid_exts:
                file_ext = os.path.splitext(file_path)[1].lower()
                if file_ext not in valid_exts:
                    continue

            self.file_list.append(file_path)
            row_index = len(self.file_list) - 1
            item_widget = FileListItem(file_path, self.page_type, row_index)
            item_widget.remove_clicked.connect(self.remove_file)
            item_widget.refresh_clicked.connect(self.refresh_file)
            item_widget.open_folder_clicked.connect(self.open_file_folder)
            item_widget.page_range_changed.connect(self.on_page_range_changed)
            self.file_widgets[file_path] = item_widget

            # 插入到列表末尾（stretch之前）
            self.file_list_layout.insertWidget(self.file_list_layout.count() - 1, item_widget)
            added += 1

            # 异步获取页数 - CAJ转其他和CAJ转图片都需要
            if self.page_type in ["caj_to_other", "caj_to_image"]:
                self.load_file_page_count(file_path)

        if added > 0:
            self.stacked_content.setCurrentIndex(1)
            self.bottom_options_container.setVisible(True)
            self.update_file_count()
            self.update_list_header()  # 更新列表头显示文件数量

    def load_file_page_count(self, file_path: str):
        """异步加载文件页数"""
        from PyQt6.QtCore import QTimer
        # 使用定时器延迟加载，避免阻塞UI
        QTimer.singleShot(100, lambda: self._do_load_page_count(file_path))

    def _do_load_page_count(self, file_path: str):
        """实际加载页数"""
        try:
            import sys
            import importlib.util
            
            # 首先检查文件是否是PDF格式
            with open(file_path, 'rb') as f:
                header = f.read(4)
            
            page_count = 0
            
            if header == b'%PDF':
                # 是PDF文件，使用PyMuPDF获取页数
                try:
                    import fitz
                    doc = fitz.open(file_path)
                    page_count = len(doc)
                    doc.close()
                except ImportError:
                    pass
            else:
                # 使用caj2pdf库获取页数
                if getattr(sys, 'frozen', False):
                    # 打包后的环境 - 使用_MEIPASS
                    if hasattr(sys, '_MEIPASS'):
                        lib_path = os.path.join(sys._MEIPASS, "lib", "caj2pdf")
                    else:
                        app_dir = os.path.dirname(sys.executable)
                        lib_path = os.path.join(app_dir, "_internal", "lib", "caj2pdf")
                else:
                    # 开发环境
                    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    lib_path = os.path.join(app_dir, "lib", "caj2pdf")
                
                cajparser_path = os.path.join(lib_path, "cajparser.py")
                if os.path.exists(cajparser_path):
                    # 将lib_path加到sys.path
                    if lib_path not in sys.path:
                        sys.path.insert(0, lib_path)
                    
                    # 使用importlib直接加载cajparser模块
                    spec = importlib.util.spec_from_file_location("cajparser_for_ui", cajparser_path)
                    cajparser_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(cajparser_module)
                    Caj2PdfParser = cajparser_module.CAJParser
                    
                    parser = Caj2PdfParser(file_path)
                    page_count = parser.page_num

            if file_path in self.file_widgets:
                self.file_widgets[file_path].set_page_count(page_count)
        except Exception:
            if file_path in self.file_widgets:
                self.file_widgets[file_path].set_page_count(0)

    def on_page_range_changed(self, file_path: str, page_range: str):
        """页码范围变化"""
        # 可以在这里保存页码范围设置
        pass

    def refresh_file(self, file_path: str):
        """重新转换单个文件"""
        if file_path in self.file_widgets:
            self.file_widgets[file_path].set_status(tr("convert.page.status_waiting"), "#1890ff")
            self.file_widgets[file_path].progress_bar.setValue(0)

    def open_file_folder(self, file_path: str):
        """打开文件所在文件夹"""
        import subprocess
        import platform
        folder = self.output_dir
        if platform.system() == "Windows":
            subprocess.run(["explorer", folder])
        elif platform.system() == "Darwin":
            subprocess.run(["open", folder])
        else:
            subprocess.run(["xdg-open", folder])

    def update_file_count(self):
        """更新文件计数"""
        count = len(self.file_list)
        self.file_count_label.setText(f"{tr('convert.page.list_header.name')}（{count}）")
        self.file_count_label.setVisible(count > 0)

    def remove_file(self, file_path: str):
        """从列表移除文件"""
        if file_path in self.file_list:
            self.file_list.remove(file_path)
        if file_path in self.file_widgets:
            widget = self.file_widgets.pop(file_path)
            widget.setParent(None)
            widget.deleteLater()

        self.update_file_count()
        self.update_list_header()  # 更新列表头显示文件数量
        if not self.file_list:
            self.stacked_content.setCurrentIndex(0)
            self.bottom_options_container.setVisible(False)

    def clear_file_list(self):
        """清空文件列表"""
        for widget in self.file_widgets.values():
            widget.setParent(None)
            widget.deleteLater()
        self.file_widgets.clear()
        self.file_list.clear()
        self.stacked_content.setCurrentIndex(0)
        self.bottom_options_container.setVisible(False)
        self.update_file_count()
        self.update_list_header()  # 更新列表头显示文件数量

    def start_convert(self):
        """开始转换"""
        if not self.file_list:
            QMessageBox.warning(self, tr("common.hint"), tr("convert.page.no_files_added"))
            return
        
        try:
            # 检查是否需要授权码
            from core.auth_manager import AuthManager
            from ui.auth_code_dialog import AuthCodeDialog
            
            auth_manager = AuthManager()
            
            # 首先检查本地是否有有效的授权码缓存
            if not auth_manager.is_auth_code_valid():
                # 检查是否需要授权码
                is_need_auth, auth_url = auth_manager.check_need_auth_code()
                
                if is_need_auth:
                    # 显示授权码对话框
                    auth_dialog = AuthCodeDialog(self)
                    if auth_dialog.exec() != QDialog.DialogCode.Accepted:
                        # 用户取消了授权
                        return
        except Exception as e:
            print(f"授权码检查出错: {str(e)}")
            # 继续转换，不中断流程

        # 获取输出目录
        output_dir = self.output_dir_combo.currentText()
        if output_dir == tr("convert.page.output_same_as_source") and self.file_list:
            output_dir = os.path.dirname(self.file_list[0])
        elif output_dir == tr("convert.page.output_custom") or not output_dir or not os.path.isdir(output_dir):
            output_dir = QFileDialog.getExistingDirectory(self, tr("convert.page.select_output_dir"), self.output_dir)
            if not output_dir:
                return
            self.output_dir_combo.setCurrentText(output_dir)
        self.output_dir = output_dir

        # 禁用按钮
        self.convert_btn.setEnabled(False)
        self.convert_btn.setText(tr("convert.page.status_converting").format(percent="..."))

        # 获取输出格式
        if self.page_type == "caj_to_other":
            # 从单选按钮组获取格式
            checked_btn = self.format_btn_group.checkedButton()
            output_format = checked_btn.text() if checked_btn else "pdf"
        elif self.page_type == "other_to_caj":
            output_format = "caj"
        else:
            output_format = self.format_combo.currentText().lower()

        # 获取长图模式
        long_image = self.long_image_checkbox.isChecked() if self.page_type == "caj_to_image" else False

        # 获取输出质量
        quality = self.quality_combo.currentText() if self.page_type == "caj_to_image" else tr("convert.page.bottom.high")

        # 收集页码范围
        page_ranges = {}
        for file_path, widget in self.file_widgets.items():
            if hasattr(widget, 'get_page_range'):
                page_ranges[file_path] = widget.get_page_range()

        # 启动转换线程
        self.convert_thread = ConvertThread(
            self.file_list.copy(),
            output_dir,
            output_format,
            self.page_type,
            long_image,
            quality,
            page_ranges
        )
        self.convert_thread.progress.connect(self.on_convert_progress)
        self.convert_thread.finished.connect(self.on_convert_finished)
        self.convert_thread.all_finished.connect(self.on_all_finished)
        self.convert_thread.start()

    def on_convert_progress(self, file_path: str, progress: int):
        """转换进度更新"""
        if file_path in self.file_widgets:
            self.file_widgets[file_path].set_status(tr("convert.page.status_converting").format(percent=progress), "#1890ff")
            self.file_widgets[file_path].set_progress(progress)

    def on_convert_finished(self, file_path: str, success: bool, message: str):
        """单个文件转换完成"""
        if file_path in self.file_widgets:
            if success:
                self.file_widgets[file_path].set_success()
            else:
                self.file_widgets[file_path].set_status(tr("convert.page.status_failure"), "#ff4444")
                self.file_widgets[file_path].progress_bar.setVisible(False)  # 隐藏进度条
                # 保存错误信息以便查看
                self.file_widgets[file_path].error_message = message

    def on_all_finished(self):
        """所有文件转换完成"""
        self.convert_btn.setEnabled(True)
        self.convert_btn.setText(tr("convert.page.bottom.start_convert"))

        # 统计结果 - 检查状态文本是否包含"转换成功"
        success_count = sum(1 for w in self.file_widgets.values() if tr("convert.page.status_success") in w.status_label.text())
        fail_count = len(self.file_list) - success_count

        if fail_count == 0:
            QMessageBox.information(self, tr("convert.page.convert_complete"), tr("convert.page.convert_success_msg").format(count=success_count, dir=self.output_dir))
        else:
            QMessageBox.warning(self, tr("convert.page.convert_complete"), tr("convert.page.convert_result_msg").format(success=success_count, fail=fail_count))

    def update_drop_zone(self):
        """更新拖拽区域"""
        hint_text, support_text, icon_type = self.get_hints()
        self.drop_zone.setParent(None)
        self.drop_zone.deleteLater()

        self.drop_zone = DropZone(hint_text, support_text, icon_type)
        self.drop_zone.setMinimumHeight(200)
        self.drop_zone.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.drop_zone.clicked.connect(self.on_add_file)
        self.drop_zone.files_dropped.connect(self.add_files)

        drop_container = self.stacked_content.widget(0)
        drop_container.layout().addWidget(self.drop_zone)

    def create_steps_indicator(self, parent_layout):
        """创建底部步骤指示器"""
        steps_widget = QWidget()
        steps_widget.setStyleSheet("background-color: transparent;")
        steps_layout = QHBoxLayout(steps_widget)
        steps_layout.setContentsMargins(20, 15, 20, 15)
        steps_layout.setSpacing(40)

        steps_layout.addStretch()

        self.step_indicators = []
        
        self.step1 = StepIndicator("1", tr("convert.page.step1_title"), tr("convert.page.step1_desc"))
        self.step_indicators.append(self.step1)
        steps_layout.addWidget(self.step1)

        arrow1 = QLabel(">>>")
        arrow1.setStyleSheet("color: #cccccc;")
        arrow1.setFont(QFont("Arial", 10))
        steps_layout.addWidget(arrow1)

        self.step2 = StepIndicator("2", tr("convert.page.step2_title"), tr("convert.page.step2_desc"))
        self.step_indicators.append(self.step2)
        steps_layout.addWidget(self.step2)

        arrow2 = QLabel(">>>")
        arrow2.setStyleSheet("color: #cccccc;")
        arrow2.setFont(QFont("Arial", 10))
        steps_layout.addWidget(arrow2)

        self.step3 = StepIndicator("3", tr("convert.page.step3_title"), tr("convert.page.step3_desc"))
        self.step_indicators.append(self.step3)
        steps_layout.addWidget(self.step3)

        steps_layout.addStretch()
        parent_layout.addWidget(steps_widget)

    def create_version_info(self, parent_layout):
        """创建版本信息和品牌信息"""
        # 添加间距
        parent_layout.addSpacing(20)
        
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
        from core.constants import CURRENT_VERSION
        self.version_label = QLabel(tr("main_window.version").format(version=CURRENT_VERSION))
        self.version_label.setFont(QFont("Microsoft YaHei", 9))
        self.version_label.setStyleSheet("color: #999999;")
        bottom_layout.addWidget(self.version_label)
        
        container_layout.addLayout(bottom_layout, 0)
        
        # 右侧弹性空间
        container_layout.addStretch()
        
        parent_layout.addWidget(container)

    def on_menu_clicked(self, item_id: str):
        """菜单点击处理"""
        if item_id == "home":
            self.go_home.emit()
            return

        # 如果点击的是其他功能，发送切换信号
        if item_id != self.page_type:
            self.switch_page.emit(item_id)
            return

        # 更新当前页面的选中状态
        for menu_id, item in self.menu_items.items():
            item.set_selected(menu_id == item_id)
