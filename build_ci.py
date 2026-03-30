from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ENTRYPOINT = ROOT / "main.py"
APP_NAME = "CAJConverter"
DEFAULT_ICON = ROOT / "CAJ转换器.ico"
ENV_ICON = os.environ.get("CI_APP_ICON")
TARGET_ARCH = os.environ.get("CI_TARGET_ARCH")


def add_data_argument(source: Path, destination: str) -> str:
    separator = ";" if sys.platform == "win32" else ":"
    return f"{source}{separator}{destination}"


def build_command() -> list[str]:
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        APP_NAME,
        "--windowed",
        "--onedir",
        "--noconfirm",
        "--clean",
    ]

    icon_path = Path(ENV_ICON) if ENV_ICON else None
    if icon_path and icon_path.exists():
        command.extend(["--icon", str(icon_path)])
    elif DEFAULT_ICON.exists() and sys.platform != "darwin":
        command.extend(["--icon", str(DEFAULT_ICON)])

    if TARGET_ARCH and sys.platform == "darwin":
        command.extend(["--target-architecture", TARGET_ARCH])

    for source, destination in [
        (ROOT / "locales", "locales"),
        (ROOT / "lib", "lib"),
    ]:
        command.extend(["--add-data", add_data_argument(source, destination)])

    for icon_file in [
        ROOT / "CAJ转换器.ico",
        ROOT / "鲲穹01.ico",
        ROOT / "CAJ转换器.png",
        ROOT / "鲲穹01.png",
    ]:
        if icon_file.exists():
            command.extend(["--add-data", add_data_argument(icon_file, ".")])

    for hidden_import in [
        "PyQt6",
        "PyQt6.QtWidgets",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyPDF2",
        "pdf2docx",
        "PIL",
        "PIL.Image",
        "fitz",
        "pymupdf",
        "docx",
        "docx.document",
        "docx.oxml",
        "reportlab",
        "reportlab.pdfgen",
        "reportlab.lib",
        "reportlab.lib.pagesizes",
        "reportlab.lib.units",
    ]:
        command.extend(["--hidden-import", hidden_import])

    for package_name in ["PyQt6", "fitz", "docx", "reportlab"]:
        command.extend(["--collect-all", package_name])

    command.append(str(ENTRYPOINT))
    return command


def main() -> None:
    command = build_command()
    print("Running:", " ".join(str(part) for part in command))
    subprocess.run(command, check=True, cwd=ROOT)


if __name__ == "__main__":
    main()
