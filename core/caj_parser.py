"""
CAJ 文件解析器
基于 caj2pdf 项目的逆向工程实现
"""
import os
import struct
import zlib
from typing import Optional, BinaryIO


class CAJParser:
    """CAJ 文件解析器"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.file: Optional[BinaryIO] = None
        self.format = ""  # CAJ, HN, KDH
        self.page_num = 0
        self._page_count = None
        
    def __enter__(self):
        self.file = open(self.filename, 'rb')
        self._detect_format()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()

    def get_page_count(self) -> int:
        """获取文件页数"""
        if self._page_count is not None:
            return self._page_count
            
        try:
            # 首先检查文件是否是PDF格式
            with open(self.filename, 'rb') as f:
                header = f.read(4)
            
            if header == b'%PDF':
                # 是PDF文件，使用PyMuPDF获取页数
                try:
                    import fitz
                    doc = fitz.open(self.filename)
                    self._page_count = len(doc)
                    doc.close()
                    return self._page_count
                except ImportError:
                    self._page_count = 0
                    return 0
            
            # 尝试使用 caj2pdf 库获取页数
            import sys
            import importlib.util
            
            # 判断是否为打包环境
            if getattr(sys, 'frozen', False):
                # 打包后的环境 - 使用多种方式尝试找到lib路径
                if hasattr(sys, '_MEIPASS'):
                    lib_path = os.path.join(sys._MEIPASS, "lib", "caj2pdf")
                else:
                    app_dir = os.path.dirname(sys.executable)
                    lib_path = os.path.join(app_dir, "_internal", "lib", "caj2pdf")
            else:
                # 开发环境
                app_dir = os.path.dirname(os.path.dirname(__file__))
                lib_path = os.path.join(app_dir, "lib", "caj2pdf")
            
            # 使用importlib直接加载cajparser模块
            cajparser_path = os.path.join(lib_path, "cajparser.py")
            if os.path.exists(cajparser_path):
                spec = importlib.util.spec_from_file_location("cajparser", cajparser_path)
                cajparser_module = importlib.util.module_from_spec(spec)
                
                # 将lib_path加到sys.path，以便cajparser能导入utils
                if lib_path not in sys.path:
                    sys.path.insert(0, lib_path)
                
                spec.loader.exec_module(cajparser_module)
                Caj2PdfParser = cajparser_module.CAJParser
                
                parser = Caj2PdfParser(self.filename)
                self._page_count = parser.page_num
                return self._page_count
        except Exception:
            pass
        
        # 默认返回 0
        self._page_count = 0
        return self._page_count
        
        # 备用方法：转换为 PDF 后获取页数
        try:
            import tempfile
            import fitz
            
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                temp_pdf = tmp.name
            
            # 尝试提取 PDF
            with open(self.filename, 'rb') as f:
                data = f.read()
            
            pdf_start = data.find(b'%PDF')
            if pdf_start != -1:
                pdf_end = data.rfind(b'%%EOF')
                if pdf_end != -1:
                    pdf_end += 5
                else:
                    pdf_end = len(data)
                
                with open(temp_pdf, 'wb') as out:
                    out.write(data[pdf_start:pdf_end])
                
                doc = fitz.open(temp_pdf)
                self._page_count = len(doc)
                doc.close()
                os.unlink(temp_pdf)
                return self._page_count
        except Exception as e:
            print(f"备用方法获取页数失败: {e}")
        
        # 默认返回 0
        self._page_count = 0
        return self._page_count
            
    def _detect_format(self):
        """检测文件格式"""
        self.file.seek(0)
        header = self.file.read(4)
        
        if header == b'%PDF':
            self.format = "PDF"
        elif header[:2] == b'HN':
            self.format = "HN"
        elif header == b'CAJ\x00' or header[:3] == b'CAJ':
            self.format = "CAJ"
        elif header == b'KDH ':
            self.format = "KDH"
        else:
            # 尝试检测是否是伪装的 PDF
            self.file.seek(0)
            content = self.file.read(1024)
            if b'%PDF' in content:
                self.format = "PDF"
            else:
                self.format = "UNKNOWN"
                
    def convert_to_pdf(self, output_path: str) -> bool:
        """
        将 CAJ 转换为 PDF
        
        Returns:
            bool: 转换是否成功
        """
        if self.format == "PDF":
            # 已经是 PDF，直接复制
            self.file.seek(0)
            with open(output_path, 'wb') as out:
                out.write(self.file.read())
            return True
            
        elif self.format == "HN":
            return self._convert_hn_to_pdf(output_path)
            
        elif self.format == "CAJ":
            return self._convert_caj_to_pdf(output_path)
            
        elif self.format == "KDH":
            return self._convert_kdh_to_pdf(output_path)
            
        else:
            raise ValueError(f"不支持的文件格式: {self.format}")
            
    def _convert_hn_to_pdf(self, output_path: str) -> bool:
        """转换 HN 格式"""
        self.file.seek(0)
        data = self.file.read()
        
        # HN 格式通常在某个偏移位置包含 PDF 数据
        pdf_start = data.find(b'%PDF')
        if pdf_start == -1:
            raise ValueError("无法在 HN 文件中找到 PDF 数据")
            
        with open(output_path, 'wb') as out:
            out.write(data[pdf_start:])
        return True
        
    def _convert_caj_to_pdf(self, output_path: str) -> bool:
        """转换 CAJ 格式"""
        self.file.seek(0)
        data = self.file.read()
        
        # 尝试查找嵌入的 PDF
        pdf_start = data.find(b'%PDF')
        if pdf_start != -1:
            # 找到 PDF 结束标记
            pdf_end = data.rfind(b'%%EOF')
            if pdf_end != -1:
                pdf_end += 5  # 包含 %%EOF
                with open(output_path, 'wb') as out:
                    out.write(data[pdf_start:pdf_end])
                return True
                
        # 如果没有嵌入 PDF，尝试解析 CAJ 结构
        # CAJ 文件结构比较复杂，需要更详细的解析
        raise ValueError("CAJ 文件格式解析失败，该文件可能需要专门的解析工具")
        
    def _convert_kdh_to_pdf(self, output_path: str) -> bool:
        """转换 KDH 格式"""
        self.file.seek(0)
        data = self.file.read()
        
        # KDH 格式类似，尝试查找 PDF
        pdf_start = data.find(b'%PDF')
        if pdf_start != -1:
            with open(output_path, 'wb') as out:
                out.write(data[pdf_start:])
            return True
            
        raise ValueError("KDH 文件格式解析失败")


def convert_caj_to_pdf(caj_path: str, pdf_path: str) -> bool:
    """
    便捷函数：将 CAJ 文件转换为 PDF
    
    Args:
        caj_path: CAJ 文件路径
        pdf_path: 输出 PDF 路径
        
    Returns:
        bool: 转换是否成功
    """
    with CAJParser(caj_path) as parser:
        return parser.convert_to_pdf(pdf_path)
