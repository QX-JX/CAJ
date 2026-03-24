import json
import os
from core.utils import get_logger

logger = get_logger(__name__)

class I18nManager:
    _instance = None
    _translations = {}
    _current_locale = "zh_CN"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(I18nManager, cls).__new__(cls)
            cls._instance._load_translations()
        return cls._instance

    def _get_locales_dir(self):
        """获取 locales 目录路径，支持开发环境和打包后的环境"""
        import sys
        if getattr(sys, 'frozen', False):
            # 打包后的环境
            if hasattr(sys, '_MEIPASS'):
                # onefile 模式
                locales_dir = os.path.join(sys._MEIPASS, "locales")
                if os.path.exists(locales_dir):
                    return locales_dir
            
            # onedir 模式或 _internal 目录 (PyInstaller 6+)
            base_dir = os.path.dirname(sys.executable)
            # 尝试在 _internal 目录查找
            internal_locales = os.path.join(base_dir, "_internal", "locales")
            if os.path.exists(internal_locales):
                return internal_locales
            # 尝试在根目录查找
            root_locales = os.path.join(base_dir, "locales")
            if os.path.exists(root_locales):
                return root_locales
        
        # 开发环境
        # 脚本路径: .../CAJ转换器/core/i18n_manager.py
        # locales 路径: .../CAJ转换器/locales
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, "locales")

    def _load_translations(self):
        """加载翻译文件"""
        try:
            locales_dir = self._get_locales_dir()
            locale_path = os.path.join(locales_dir, f"{self._current_locale}.json")
            
            if os.path.exists(locale_path):
                with open(locale_path, "r", encoding="utf-8") as f:
                    self._translations = json.load(f)
                logger.info(f"Loaded translations for {self._current_locale} from {locale_path}")
            else:
                logger.warning(f"Translation file not found: {locale_path}")
                self._translations = {}
        except Exception as e:
            logger.error(f"Failed to load translations: {e}")
            self._translations = {}

    def set_locale(self, locale):
        """设置当前语言"""
        logger.info(f"Setting locale to: {locale} (current: {self._current_locale})")
        # 即使语言相同也强制重新加载一次，确保翻译字典已填充
        self._current_locale = locale
        self._load_translations()
        return True

    def get_locale(self):
        """获取当前语言"""
        return self._current_locale

    def get_available_locales(self):
        """获取可用语言列表"""
        locales_dir = self._get_locales_dir()
        if not os.path.exists(locales_dir):
            logger.warning(f"Locales directory not found: {locales_dir}")
            return []
        
        locales = []
        for filename in os.listdir(locales_dir):
            if filename.endswith(".json"):
                locales.append(filename[:-5])
        return locales

    def get_text(self, key, default=None):
        """获取翻译文本"""
        if default is None:
            default = key
        
        # 支持层级 key，例如 "main_window.title"
        keys = key.split('.')
        value = self._translations
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    @classmethod
    def tr(cls, key, default=None):
        """静态翻译方法"""
        return cls().get_text(key, default)

def tr(key, default=None):
    """全局翻译函数"""
    return I18nManager.tr(key, default)
