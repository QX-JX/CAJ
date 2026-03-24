import logging
import os
import sys
from pathlib import Path


def setup_logging():
    """配置日志"""
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    log_dir = os.path.join(base_dir, "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "app.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def get_logger(name):
    """获取指定名称的日志对象"""
    return logging.getLogger(name)


def _candidate_resource_names(resource_name: str) -> list[str]:
    """Build a small fallback list so packaged apps can find icons across platforms."""
    resource_path = Path(resource_name)
    stem = resource_path.stem

    candidates = [resource_name]
    for suffix in (".png", ".ico", ".icns"):
        candidate = f"{stem}{suffix}"
        if candidate not in candidates:
            candidates.append(candidate)

    return candidates


def get_icon_path(icon_name: str) -> str | None:
    """获取图标文件路径，兼容开发环境和打包环境"""
    candidates = _candidate_resource_names(icon_name)

    if getattr(sys, "frozen", False):
        search_dirs = []

        if hasattr(sys, "_MEIPASS"):
            search_dirs.append(sys._MEIPASS)

        base_dir = os.path.dirname(sys.executable)
        search_dirs.extend(
            [
                os.path.join(base_dir, "_internal"),
                base_dir,
            ]
        )
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        search_dirs = [base_dir]

    for search_dir in search_dirs:
        for candidate in candidates:
            icon_path = os.path.join(search_dir, candidate)
            if os.path.exists(icon_path):
                return icon_path

    return None
