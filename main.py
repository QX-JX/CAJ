import sys
import os
import ctypes
from PyQt6.QtWidgets import QApplication, QToolTip
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor
from ui.main_window import MainWindow
from core.i18n_manager import I18nManager
from PyQt6.QtCore import QSettings


def get_icon_path(icon_name: str) -> str:
    """获取图标文件路径，支持打包后的环境"""
    # 如果是PyInstaller打包的环境
    if getattr(sys, 'frozen', False):
        # 优先从_MEIPASS临时目录获取（onefile模式）
        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, icon_name)
            if os.path.exists(icon_path):
                return icon_path
        # 其次从exe所在目录获取（onedir模式）
        base_dir = os.path.dirname(sys.executable)
    else:
        # 开发环境：当前目录
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    icon_path = os.path.join(base_dir, icon_name)
    return icon_path if os.path.exists(icon_path) else None


from core.constants import CURRENT_VERSION

def main():
    # 初始化国际化管理器并加载保存的语言
    settings = QSettings("KunqiongAI", "CAJConverter")
    saved_locale = settings.value("language", "zh_CN")
    i18n = I18nManager()
    i18n.set_locale(saved_locale)

    # Windows任务栏图标设置 - 必须在创建QApplication之前设置
    if sys.platform == 'win32':
        # 设置应用程序ID，使Windows任务栏正确显示图标
        app_id = f'KunqiongAI.CAJConverter.{CURRENT_VERSION}'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 设置全局ToolTip字体
    QToolTip.setFont(QFont("Microsoft YaHei", 10))
    
    # 使用QPalette设置ToolTip颜色 - 这是最可靠的方式
    palette = app.palette()
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(51, 51, 51))  # #333333
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))  # #ffffff
    app.setPalette(palette)
    
    # 设置应用程序图标
    icon_path = get_icon_path("鲲穹01.ico")
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
