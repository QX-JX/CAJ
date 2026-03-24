"""
广告缓存管理
"""
import os
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict


class AdCache:
    """广告缓存管理器"""
    
    def __init__(self):
        # 缓存目录
        self.cache_dir = Path.home() / ".caj_converter" / "ad_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 缓存索引文件
        self.index_file = self.cache_dir / "index.json"
        self.index = self._load_index()
    
    def _load_index(self) -> Dict:
        """加载缓存索引"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_index(self):
        """保存缓存索引"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def _get_cache_key(self, url: str) -> str:
        """生成缓存键"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def get_cached_image(self, url: str) -> Optional[bytes]:
        """获取缓存的图片"""
        cache_key = self._get_cache_key(url)
        if cache_key in self.index:
            cache_file = self.cache_dir / f"{cache_key}.jpg"
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        return f.read()
                except:
                    pass
        return None
    
    def save_image(self, url: str, image_data: bytes):
        """保存图片到缓存"""
        cache_key = self._get_cache_key(url)
        cache_file = self.cache_dir / f"{cache_key}.jpg"
        try:
            with open(cache_file, 'wb') as f:
                f.write(image_data)
            self.index[cache_key] = {"url": url}
            self._save_index()
        except:
            pass
    
    def clear_cache(self):
        """清除所有缓存"""
        try:
            for file in self.cache_dir.glob("*.jpg"):
                file.unlink()
            self.index = {}
            self._save_index()
        except:
            pass
