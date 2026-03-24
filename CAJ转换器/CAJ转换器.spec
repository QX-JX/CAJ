# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('E:\\总任务\\任务四-CAJ转换器\\caj_converter\\CAJ转换器.ico', '.'), ('E:\\总任务\\任务四-CAJ转换器\\caj_converter\\鲲穹01.ico', '.'), ('lib/caj2pdf', 'lib/caj2pdf'), ('locales', 'locales')]
binaries = []
hiddenimports = ['PyQt6', 'PyQt6.QtWidgets', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyPDF2', 'pdf2docx', 'PIL', 'PIL.Image', 'fitz', 'pymupdf', 'docx', 'docx.document', 'docx.oxml', 'docx.oxml.ns', 'docx.oxml.xmlchemy', 'docx.oxml.text.paragraph', 'docx.oxml.text.run', 'docx.text.paragraph', 'docx.text.run', 'reportlab', 'reportlab.pdfgen', 'reportlab.pdfgen.canvas', 'reportlab.lib', 'reportlab.lib.pagesizes', 'reportlab.lib.units', 'reportlab.lib.colors', 'reportlab.lib.styles', 'comtypes', 'comtypes.client']
tmp_ret = collect_all('PyQt6')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('fitz')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('docx')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('reportlab')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'tensorflow', 'scipy', 'matplotlib', 'pandas', 'numba', 'onnxruntime', 'tensorboard', 'notebook', 'jedi'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CAJ转换器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['E:\\总任务\\任务四-CAJ转换器\\caj_converter\\CAJ转换器.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CAJ转换器',
)
