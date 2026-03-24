import ctypes
import sys

from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QColor, QFont, QIcon, QPalette
from PyQt6.QtWidgets import QApplication, QToolTip

from core.constants import CURRENT_VERSION
from core.i18n_manager import I18nManager
from core.utils import get_icon_path
from ui.main_window import MainWindow


def main():
    settings = QSettings("KunqiongAI", "CAJConverter")
    saved_locale = settings.value("language", "zh_CN")
    i18n = I18nManager()
    i18n.set_locale(saved_locale)

    if sys.platform == "win32":
        app_id = f"KunqiongAI.CAJConverter.{CURRENT_VERSION}"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    QToolTip.setFont(QFont("Microsoft YaHei", 10))

    palette = app.palette()
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(51, 51, 51))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
    app.setPalette(palette)

    icon_path = get_icon_path("鲲穹01.ico")
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
