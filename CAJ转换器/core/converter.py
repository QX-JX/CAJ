"""
CAJ 转换器核心模块
使用 caj2pdf 开源库进行 CAJ 文件解析
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Callable


class ConvertResult:
    """转换结果"""

    def __init__(self, success: bool, output_path: str = "", error_msg: str = ""):
        self.success = success
        self.output_path = output_path
        self.error_msg = error_msg


class CAJConverter:
    """CAJ 文件转换器"""

    def __init__(self):
        # 添加 lib 目录到 Python 路径
        # 判断是否为打包环境
        if getattr(sys, 'frozen', False):
            # 打包后的环境
            if hasattr(sys, '_MEIPASS'):
                # Onefile 模式：资源解压到临时目录
                app_dir = sys._MEIPASS
                lib_path = os.path.join(app_dir, "lib", "caj2pdf")
            else:
                # Onedir 模式：资源在 _internal 目录或当前目录
                app_dir = os.path.dirname(sys.executable)
                lib_path = os.path.join(app_dir, "_internal", "lib", "caj2pdf")
                # 如果_internal路径不存在，尝试直接在app_dir下查找
                if not os.path.exists(lib_path):
                    lib_path = os.path.join(app_dir, "lib", "caj2pdf")
        else:
            # 开发环境
            app_dir = os.path.dirname(os.path.dirname(__file__))
            lib_path = os.path.join(app_dir, "lib", "caj2pdf")
        
        if lib_path not in sys.path:
            sys.path.insert(0, lib_path)

    def _detect_format(self, file_path: str) -> str:
        """检测文件格式"""
        with open(file_path, "rb") as f:
            header = f.read(16)

        if header[:4] == b"%PDF":
            return "PDF"
        elif header[:2] == b"HN":
            return "HN"
        elif header[:4] == b"CAJ\x00" or header[:3] == b"CAJ":
            return "CAJ"
        elif header[:4] == b"KDH ":
            return "KDH"
        elif header[0:1] == b"\xc8":
            return "C8"
        else:
            # 检查是否有嵌入的 PDF
            with open(file_path, "rb") as f:
                content = f.read(4096)
                if b"%PDF" in content:
                    return "PDF_EMBEDDED"
            return "UNKNOWN"

    def convert_to_pdf(
        self,
        caj_path: str,
        output_path: str,
        page_range: str = "全部",
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> ConvertResult:
        """
        将 CAJ 文件转换为 PDF
        
        Args:
            caj_path: CAJ 文件路径
            output_path: 输出 PDF 路径
            page_range: 页码范围 (全部/前N页/自定义如1-5,8,10-12)
            progress_callback: 进度回调
        """
        if not os.path.exists(caj_path):
            return ConvertResult(False, error_msg="CAJ 文件不存在")

        if progress_callback:
            progress_callback(10)

        try:
            file_format = self._detect_format(caj_path)

            if progress_callback:
                progress_callback(20)

            # 先转换完整的 PDF
            temp_full_pdf = None
            
            if file_format == "PDF":
                # 已经是 PDF
                temp_full_pdf = caj_path
                
            elif file_format == "PDF_EMBEDDED":
                # 提取嵌入的 PDF 到临时文件
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    temp_full_pdf = tmp.name
                if not self._extract_embedded_pdf(caj_path, temp_full_pdf):
                    return ConvertResult(False, error_msg="无法提取嵌入的 PDF")

            elif file_format in ["CAJ", "HN", "KDH", "C8"]:
                # 使用 caj2pdf 库转换到临时文件
                if progress_callback:
                    progress_callback(30)
                    
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    temp_full_pdf = tmp.name
                    
                result = self._convert_with_caj2pdf(caj_path, temp_full_pdf, progress_callback)
                if not result.success:
                    return result

            else:
                return ConvertResult(False, error_msg=f"不支持的文件格式: {file_format}")

            if progress_callback:
                progress_callback(70)

            # 如果需要选择页码范围，使用 PyMuPDF 提取指定页面
            if page_range and page_range != "全部":
                try:
                    import fitz
                    
                    doc = fitz.open(temp_full_pdf)
                    total_pages = len(doc)
                    pages_to_extract = self._parse_page_range(page_range, total_pages)
                    
                    if pages_to_extract and len(pages_to_extract) < total_pages:
                        # 创建新的 PDF，只包含选定的页面
                        new_doc = fitz.open()
                        for page_num in pages_to_extract:
                            new_doc.insert_pdf(doc, from_page=page_num-1, to_page=page_num-1)
                        new_doc.save(output_path)
                        new_doc.close()
                        doc.close()
                        
                        # 清理临时文件
                        if temp_full_pdf != caj_path and os.path.exists(temp_full_pdf):
                            os.unlink(temp_full_pdf)
                            
                        if progress_callback:
                            progress_callback(100)
                        return ConvertResult(True, output_path)
                    
                    doc.close()
                except ImportError:
                    pass  # 如果没有 PyMuPDF，则输出完整 PDF
            
            # 输出完整 PDF
            if temp_full_pdf != caj_path:
                if temp_full_pdf != output_path:
                    shutil.copy2(temp_full_pdf, output_path)
                    os.unlink(temp_full_pdf)
            else:
                shutil.copy2(caj_path, output_path)
                
            if progress_callback:
                progress_callback(100)
            return ConvertResult(True, output_path)

        except Exception as e:
            import traceback
            return ConvertResult(False, error_msg=f"转换失败: {str(e)}\n{traceback.format_exc()}")

    def _extract_embedded_pdf(self, caj_path: str, output_path: str) -> bool:
        """提取嵌入的 PDF"""
        with open(caj_path, "rb") as f:
            content = f.read()

        pdf_start = content.find(b"%PDF")
        if pdf_start == -1:
            return False

        pdf_end = content.rfind(b"%%EOF")
        if pdf_end != -1:
            pdf_end += 5
        else:
            pdf_end = len(content)

        with open(output_path, "wb") as f:
            f.write(content[pdf_start:pdf_end])

        return True

    def _convert_with_caj2pdf(
        self,
        caj_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> ConvertResult:
        """使用 caj2pdf 库转换"""
        try:
            from cajparser import CAJParser as Caj2PdfParser

            if progress_callback:
                progress_callback(40)

            parser = Caj2PdfParser(caj_path)

            if progress_callback:
                progress_callback(60)

            # 保存当前目录
            original_dir = os.getcwd()
            # 切换到临时目录进行转换（caj2pdf 会生成临时文件）
            temp_dir = tempfile.mkdtemp()

            try:
                os.chdir(temp_dir)
                parser.convert(output_path)

                if progress_callback:
                    progress_callback(90)

                if os.path.exists(output_path):
                    if progress_callback:
                        progress_callback(100)
                    return ConvertResult(True, output_path)
                else:
                    return ConvertResult(False, error_msg="PDF 文件生成失败")

            finally:
                os.chdir(original_dir)
                # 清理临时目录
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass

        except ImportError as e:
            return ConvertResult(False, error_msg=f"无法导入 caj2pdf 库: {str(e)}")
        except SystemExit as e:
            return ConvertResult(False, error_msg=f"转换失败: {str(e)}")
        except Exception as e:
            import traceback
            return ConvertResult(False, error_msg=f"转换失败: {str(e)}\n{traceback.format_exc()}")

    def convert_to_image(
        self,
        caj_path: str,
        output_dir: str,
        image_format: str = "png",
        dpi: int = 150,
        long_image: bool = False,
        quality: str = "高",
        page_range: str = "全部",
        max_pages_per_long_image: int = 10,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> ConvertResult:
        """
        将 CAJ 文件转换为图片
        
        Args:
            caj_path: CAJ 文件路径
            output_dir: 输出目录
            image_format: 图片格式 (png, jpg, bmp)
            dpi: 图片 DPI
            long_image: 是否生成长图（将所有页面拼接成一张图）
            quality: 输出质量 (高/中/低)
            page_range: 页码范围 (全部/前N页/自定义如1-5,8,10-12)
            max_pages_per_long_image: 长图模式下每张长图最大页数
            progress_callback: 进度回调
        """
        if not os.path.exists(caj_path):
            return ConvertResult(False, error_msg="CAJ 文件不存在")

        if progress_callback:
            progress_callback(10)

        try:
            # 根据质量设置 DPI
            quality_dpi = {"高": 200, "中": 150, "低": 100}
            dpi = quality_dpi.get(quality, 150)
            
            # 根据质量设置 JPEG 质量
            jpeg_quality = {"高": 95, "中": 85, "低": 70}
            jpg_quality = jpeg_quality.get(quality, 85)

            # 先转换为 PDF
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                temp_pdf = tmp.name

            pdf_result = self.convert_to_pdf(caj_path, temp_pdf)

            if not pdf_result.success:
                return pdf_result

            if progress_callback:
                progress_callback(40)

            # 使用 PyMuPDF 将 PDF 转为图片
            import fitz

            doc = fitz.open(temp_pdf)
            os.makedirs(output_dir, exist_ok=True)
            base_name = Path(caj_path).stem

            zoom = dpi / 72
            matrix = fitz.Matrix(zoom, zoom)
            total_pages = len(doc)

            # 解析页码范围
            pages_to_convert = self._parse_page_range(page_range, total_pages)

            if long_image:
                # 长图模式：将页面拼接成长图，超过10页分割
                from PIL import Image
                
                # 分组页面
                page_groups = []
                for i in range(0, len(pages_to_convert), max_pages_per_long_image):
                    page_groups.append(pages_to_convert[i:i + max_pages_per_long_image])
                
                for group_idx, page_group in enumerate(page_groups):
                    page_images = []
                    total_height = 0
                    max_width = 0
                    
                    # 渲染该组的所有页面
                    for i, page_num in enumerate(page_group):
                        page = doc[page_num - 1]  # 页码从1开始，索引从0开始
                        pix = page.get_pixmap(matrix=matrix)
                        # 转换为 PIL Image
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        page_images.append(img)
                        total_height += pix.height
                        max_width = max(max_width, pix.width)
                        
                        if progress_callback:
                            overall_progress = sum(len(g) for g in page_groups[:group_idx]) + i + 1
                            progress = 40 + int(30 * overall_progress / len(pages_to_convert))
                            progress_callback(progress)
                    
                    # 创建长图
                    long_img = Image.new("RGB", (max_width, total_height), (255, 255, 255))
                    y_offset = 0
                    
                    for img in page_images:
                        # 居中放置
                        x_offset = (max_width - img.width) // 2
                        long_img.paste(img, (x_offset, y_offset))
                        y_offset += img.height
                    
                    # 保存长图
                    suffix = f"_长图_{group_idx + 1}" if len(page_groups) > 1 else "_长图"
                    if image_format.lower() == "jpg":
                        output_file = os.path.join(output_dir, f"{base_name}{suffix}.jpg")
                        long_img.save(output_file, "JPEG", quality=jpg_quality)
                    elif image_format.lower() == "bmp":
                        output_file = os.path.join(output_dir, f"{base_name}{suffix}.bmp")
                        long_img.save(output_file, "BMP")
                    else:
                        output_file = os.path.join(output_dir, f"{base_name}{suffix}.png")
                        long_img.save(output_file, "PNG")
                
                if progress_callback:
                    progress_callback(80)
                
            else:
                # 普通模式：每页一张图
                for i, page_num in enumerate(pages_to_convert):
                    page = doc[page_num - 1]  # 页码从1开始，索引从0开始
                    pix = page.get_pixmap(matrix=matrix)

                    if image_format.lower() == "jpg":
                        output_file = os.path.join(output_dir, f"{base_name}_page_{page_num}.jpg")
                        # 先保存为 PNG，再转换为 JPG 以控制质量
                        temp_png = output_file.replace(".jpg", "_temp.png")
                        pix.save(temp_png)
                        try:
                            from PIL import Image
                            img = Image.open(temp_png)
                            img.save(output_file, "JPEG", quality=jpg_quality)
                            os.remove(temp_png)
                        except ImportError:
                            pix.save(output_file, "jpeg")
                    elif image_format.lower() == "bmp":
                        output_file = os.path.join(output_dir, f"{base_name}_page_{page_num}.png")
                        pix.save(output_file)
                        try:
                            from PIL import Image
                            img = Image.open(output_file)
                            bmp_file = output_file.replace(".png", ".bmp")
                            img.save(bmp_file, "BMP")
                            os.remove(output_file)
                        except ImportError:
                            pass
                    else:
                        output_file = os.path.join(output_dir, f"{base_name}_page_{page_num}.png")
                        pix.save(output_file)

                    if progress_callback:
                        progress = 40 + int(50 * (i + 1) / len(pages_to_convert))
                        progress_callback(progress)

            doc.close()
            os.unlink(temp_pdf)

            if progress_callback:
                progress_callback(100)

            return ConvertResult(True, output_dir)

        except ImportError as e:
            return ConvertResult(False, error_msg=f"未找到必要的库: {e}")
        except Exception as e:
            import traceback
            return ConvertResult(False, error_msg=f"{str(e)}\n{traceback.format_exc()}")

    def _parse_page_range(self, page_range: str, total_pages: int) -> list:
        """解析页码范围字符串，返回页码列表"""
        if not page_range or page_range == "全部":
            return list(range(1, total_pages + 1))

        if page_range.startswith("前"):
            try:
                num = int(page_range.replace("前", "").replace("页", ""))
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

    def convert_to_word(
        self,
        caj_path: str,
        output_path: str,
        format_type: str = "docx",
        page_range: str = "全部",
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> ConvertResult:
        """将 CAJ 文件转换为 Word 文档"""
        if not os.path.exists(caj_path):
            return ConvertResult(False, error_msg="CAJ 文件不存在")

        if progress_callback:
            progress_callback(10)

        try:
            # 先转换为 PDF（支持页码范围）
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                temp_pdf = tmp.name

            pdf_result = self.convert_to_pdf(caj_path, temp_pdf, page_range)

            if not pdf_result.success:
                self._write_error_log(f"PDF转换失败: {pdf_result.error_msg}")
                return pdf_result

            if progress_callback:
                progress_callback(50)

            from pdf2docx import Converter

            cv = Converter(temp_pdf)
            cv.convert(output_path)
            cv.close()

            os.unlink(temp_pdf)

            if progress_callback:
                progress_callback(100)

            return ConvertResult(True, output_path)

        except ImportError as e:
            import traceback
            err_msg = f"未找到 pdf2docx 库: {e}\n{traceback.format_exc()}"
            self._write_error_log(err_msg)
            return ConvertResult(False, error_msg=err_msg)
        except Exception as e:
            import traceback
            err_msg = f"转换失败: {e}\n{traceback.format_exc()}"
            self._write_error_log(err_msg)
            return ConvertResult(False, error_msg=err_msg)
    
    def _write_error_log(self, msg: str):
        """写入错误日志"""
        try:
            if getattr(sys, 'frozen', False):
                log_path = os.path.join(os.path.dirname(sys.executable), "convert_error.log")
            else:
                log_path = os.path.join(os.path.dirname(__file__), "convert_error.log")
            
            with open(log_path, 'a', encoding='utf-8') as f:
                import datetime
                f.write(f"\n{'='*60}\n")
                f.write(f"Time: {datetime.datetime.now()}\n")
                f.write(f"{msg}\n")
        except:
            pass

    def convert_to_txt(
        self,
        caj_path: str,
        output_path: str,
        page_range: str = "全部",
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> ConvertResult:
        """将 CAJ 文件转换为纯文本"""
        if not os.path.exists(caj_path):
            return ConvertResult(False, error_msg="CAJ 文件不存在")

        if progress_callback:
            progress_callback(10)

        try:
            # 先转换为 PDF（支持页码范围）
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                temp_pdf = tmp.name

            pdf_result = self.convert_to_pdf(caj_path, temp_pdf, page_range)

            if not pdf_result.success:
                return pdf_result

            if progress_callback:
                progress_callback(40)

            import fitz

            doc = fitz.open(temp_pdf)
            text_content = []
            total_pages = len(doc)

            for i, page in enumerate(doc):
                text = page.get_text()
                if text:
                    text_content.append(f"--- 第 {i+1} 页 ---\n{text}")

                if progress_callback:
                    progress = 40 + int(50 * (i + 1) / total_pages)
                    progress_callback(progress)

            doc.close()
            os.unlink(temp_pdf)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n\n".join(text_content))

            if progress_callback:
                progress_callback(100)

            return ConvertResult(True, output_path)

        except ImportError:
            return ConvertResult(False, error_msg="未找到 PyMuPDF 库")
        except Exception as e:
            return ConvertResult(False, error_msg=str(e))

    def convert_pdf_to_caj(
        self,
        pdf_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> ConvertResult:
        """将 PDF 文件转换为 CAJ 格式（实际上是重命名为.caj扩展名）"""
        if not os.path.exists(pdf_path):
            return ConvertResult(False, error_msg="PDF 文件不存在")

        if progress_callback:
            progress_callback(10)

        try:
            # 直接复制PDF文件并改名为.caj
            shutil.copy2(pdf_path, output_path)
            
            if progress_callback:
                progress_callback(100)
            
            return ConvertResult(True, output_path)
        except Exception as e:
            return ConvertResult(False, error_msg=f"转换失败: {str(e)}")

    def convert_word_to_caj(
        self,
        word_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> ConvertResult:
        """将 Word 文件转换为 CAJ 格式"""
        if not os.path.exists(word_path):
            return ConvertResult(False, error_msg="Word 文件不存在")

        if progress_callback:
            progress_callback(10)

        try:
            # 先将 Word 转换为 PDF
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                temp_pdf = tmp.name

            if progress_callback:
                progress_callback(20)

            word_to_pdf_success = False
            conversion_method = None
            
            # 方法1：优先使用 Windows COM (保持最佳排版)
            if sys.platform == "win32":
                try:
                    import win32com.client
                    
                    word = win32com.client.DispatchEx('Word.Application')
                    word.Visible = False
                    word.DisplayAlerts = 0
                    
                    doc = word.Documents.Open(os.path.abspath(word_path))
                    
                    # 更新所有域字段（包括目录）
                    try:
                        doc.Fields.Update()
                    except:
                        pass
                    
                    # 使用ExportAsFixedFormat获得最佳质量
                    try:
                        doc.ExportAsFixedFormat(
                            OutputFileName=os.path.abspath(temp_pdf),
                            ExportFormat=17,  # wdExportFormatPDF
                            OpenAfterExport=False,
                            OptimizeFor=0,  # wdExportOptimizeForPrint (最高质量)
                            CreateBookmarks=1,  # wdExportCreateHeadingBookmarks (创建书签，保留目录结构)
                            DocStructureTags=True,
                            BitmapMissingFonts=True
                        )
                    except Exception as export_err:
                        # 如果ExportAsFixedFormat失败，使用SaveAs
                        doc.SaveAs(os.path.abspath(temp_pdf), FileFormat=17)
                    
                    doc.Close(False)
                    
                    # 安全地退出Word
                    try:
                        word.Quit()
                    except:
                        # 如果Quit失败，尝试强制关闭
                        try:
                            import win32process
                            import win32api
                            # 获取Word进程并强制结束
                            pass
                        except:
                            pass
                    
                    if os.path.exists(temp_pdf) and os.path.getsize(temp_pdf) > 0:
                        word_to_pdf_success = True
                        conversion_method = "Microsoft Word (win32com)"
                        if progress_callback:
                            progress_callback(70)
                except Exception as e:
                    # win32com失败，尝试comtypes
                    try:
                        import comtypes.client
                        word = comtypes.client.CreateObject('Word.Application')
                        word.Visible = False
                        word.DisplayAlerts = 0
                        
                        doc = word.Documents.Open(os.path.abspath(word_path))
                        
                        # 更新所有域字段（包括目录）
                        try:
                            doc.Fields.Update()
                        except:
                            pass
                        
                        # 尝试使用ExportAsFixedFormat
                        try:
                            doc.ExportAsFixedFormat(
                                OutputFileName=os.path.abspath(temp_pdf),
                                ExportFormat=17,
                                OpenAfterExport=False,
                                OptimizeFor=0,
                                CreateBookmarks=1,  # 创建书签，保留目录
                                DocStructureTags=True,
                                BitmapMissingFonts=True
                            )
                        except:
                            doc.SaveAs(os.path.abspath(temp_pdf), FileFormat=17)
                        
                        doc.Close(False)
                        
                        try:
                            word.Quit()
                        except:
                            pass
                        
                        if os.path.exists(temp_pdf) and os.path.getsize(temp_pdf) > 0:
                            word_to_pdf_success = True
                            conversion_method = "Microsoft Word (comtypes)"
                            if progress_callback:
                                progress_callback(70)
                    except Exception as e2:
                        pass
            
            # 方法2：尝试使用 LibreOffice (次优，但也能保持排版)
            if not word_to_pdf_success:
                try:
                    import subprocess
                    # 查找 LibreOffice
                    libreoffice_paths = [
                        r"C:\Program Files\LibreOffice\program\soffice.exe",
                        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
                        "soffice",  # 如果在PATH中
                    ]
                    
                    libreoffice_cmd = None
                    for path in libreoffice_paths:
                        if path == "soffice":
                            try:
                                subprocess.run([path, "--version"], capture_output=True, timeout=5)
                                libreoffice_cmd = path
                                break
                            except:
                                pass
                        elif os.path.exists(path):
                            libreoffice_cmd = path
                            break
                    
                    if libreoffice_cmd:
                        result = subprocess.run(
                            [libreoffice_cmd, '--headless', '--convert-to', 'pdf', 
                             '--outdir', os.path.dirname(temp_pdf), word_path],
                            capture_output=True,
                            timeout=60
                        )
                        
                        # LibreOffice 会生成与输入文件同名的PDF
                        base_name = os.path.splitext(os.path.basename(word_path))[0]
                        libreoffice_pdf = os.path.join(os.path.dirname(temp_pdf), f"{base_name}.pdf")
                        
                        if os.path.exists(libreoffice_pdf):
                            shutil.move(libreoffice_pdf, temp_pdf)
                            word_to_pdf_success = True
                            conversion_method = "LibreOffice"
                            if progress_callback:
                                progress_callback(70)
                except Exception as e:
                    pass
            
            # 方法3：使用 python-docx + reportlab (最后备选，排版会丢失但能显示内容)
            if not word_to_pdf_success:
                try:
                    from docx import Document
                    from reportlab.pdfgen import canvas
                    from reportlab.lib.pagesizes import A4
                    from reportlab.lib.units import cm
                    from reportlab.pdfbase import pdfmetrics
                    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
                    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
                    
                    # 注册中文字体
                    try:
                        pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
                        font_name = 'STSong-Light'
                    except:
                        font_name = 'Helvetica'
                    
                    doc = Document(word_path)
                    
                    # 使用SimpleDocTemplate创建PDF，可以更好地处理排版
                    pdf_doc = SimpleDocTemplate(temp_pdf, pagesize=A4,
                                               leftMargin=2*cm, rightMargin=2*cm,
                                               topMargin=2*cm, bottomMargin=2*cm)
                    
                    # 创建样式
                    styles = getSampleStyleSheet()
                    normal_style = ParagraphStyle(
                        'CustomNormal',
                        parent=styles['Normal'],
                        fontName=font_name,
                        fontSize=12,
                        leading=18,
                        alignment=TA_LEFT
                    )
                    
                    heading_style = ParagraphStyle(
                        'CustomHeading',
                        parent=styles['Heading1'],
                        fontName=font_name,
                        fontSize=16,
                        leading=22,
                        alignment=TA_LEFT,
                        spaceAfter=12
                    )
                    
                    # 构建内容
                    story = []
                    for para in doc.paragraphs:
                        if para.text.strip():
                            # 检查是否是标题
                            if para.style.name.startswith('Heading'):
                                story.append(Paragraph(para.text, heading_style))
                            else:
                                story.append(Paragraph(para.text, normal_style))
                            story.append(Spacer(1, 0.2*cm))
                    
                    # 如果没有内容，添加一个空段落
                    if not story:
                        story.append(Paragraph("(空文档)", normal_style))
                    
                    # 生成PDF
                    pdf_doc.build(story)
                    
                    if os.path.exists(temp_pdf) and os.path.getsize(temp_pdf) > 0:
                        word_to_pdf_success = True
                        conversion_method = "reportlab (排版简化)"
                        if progress_callback:
                            progress_callback(70)
                        
                except Exception as e:
                    pass
            
            if not word_to_pdf_success:
                if os.path.exists(temp_pdf):
                    os.unlink(temp_pdf)
                
                # 提供简洁的错误信息
                error_msg = "Word转PDF失败。请确保已安装Microsoft Word。"
                
                return ConvertResult(False, error_msg=error_msg)

            if progress_callback:
                progress_callback(80)

            # 将 PDF 复制为 CAJ
            shutil.copy2(temp_pdf, output_path)
            os.unlink(temp_pdf)

            if progress_callback:
                progress_callback(100)

            return ConvertResult(True, output_path)

        except Exception as e:
            import traceback
            return ConvertResult(False, error_msg=f"转换失败: {str(e)}")

    def convert_image_to_caj(
        self,
        image_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> ConvertResult:
        """将图片文件转换为 CAJ 格式"""
        if not os.path.exists(image_path):
            return ConvertResult(False, error_msg="图片文件不存在")

        if progress_callback:
            progress_callback(10)

        try:
            from PIL import Image
            import fitz  # PyMuPDF

            if progress_callback:
                progress_callback(30)

            # 打开图片
            img = Image.open(image_path)
            if img.mode == 'RGBA':
                # 转换为RGB（PDF不支持透明通道）
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            if progress_callback:
                progress_callback(50)

            # 创建 PDF
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                temp_pdf = tmp.name

            # 使用 PIL 保存为 PDF
            img.save(temp_pdf, "PDF", resolution=150)

            if progress_callback:
                progress_callback(80)

            # 将 PDF 复制为 CAJ
            shutil.copy2(temp_pdf, output_path)
            os.unlink(temp_pdf)

            if progress_callback:
                progress_callback(100)

            return ConvertResult(True, output_path)

        except ImportError as e:
            return ConvertResult(False, error_msg=f"缺少必要的库: {str(e)}")
        except Exception as e:
            import traceback
            return ConvertResult(False, error_msg=f"转换失败: {str(e)}\n{traceback.format_exc()}")

    def convert_to_caj(
        self,
        input_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> ConvertResult:
        """将各种格式转换为 CAJ 格式（自动检测输入格式）"""
        if not os.path.exists(input_path):
            return ConvertResult(False, error_msg="输入文件不存在")

        # 获取文件扩展名
        ext = os.path.splitext(input_path)[1].lower()

        if ext == ".pdf":
            return self.convert_pdf_to_caj(input_path, output_path, progress_callback)
        elif ext in [".doc", ".docx"]:
            return self.convert_word_to_caj(input_path, output_path, progress_callback)
        elif ext in [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif"]:
            return self.convert_image_to_caj(input_path, output_path, progress_callback)
        elif ext == ".txt":
            return self.convert_txt_to_caj(input_path, output_path, progress_callback)
        else:
            return ConvertResult(False, error_msg=f"不支持的文件格式: {ext}")

    def convert_txt_to_caj(
        self,
        txt_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> ConvertResult:
        """将 TXT 文件转换为 CAJ 格式"""
        if not os.path.exists(txt_path):
            return ConvertResult(False, error_msg="TXT 文件不存在")

        if progress_callback:
            progress_callback(10)

        try:
            # 先将 TXT 转换为 PDF
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                temp_pdf = tmp.name

            if progress_callback:
                progress_callback(20)

            # 读取TXT内容，尝试多种编码
            text_content = None
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16', 'latin-1']
            
            for encoding in encodings:
                try:
                    with open(txt_path, 'r', encoding=encoding) as f:
                        text_content = f.read()
                    break
                except:
                    continue
            
            if text_content is None:
                return ConvertResult(False, error_msg="无法读取TXT文件，编码格式不支持")

            if progress_callback:
                progress_callback(40)

            # 使用reportlab的canvas直接绘制文本
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import cm
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.cidfonts import UnicodeCIDFont
            
            # 注册中文字体
            try:
                pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
                font_name = 'STSong-Light'
            except:
                font_name = 'Helvetica'
            
            # 创建PDF
            c = canvas.Canvas(temp_pdf, pagesize=A4)
            width, height = A4
            
            # 设置参数
            margin_left = 2*cm
            margin_right = 2*cm
            margin_top = 2*cm
            margin_bottom = 2*cm
            font_size = 11
            line_height = font_size * 1.5
            
            max_width = width - margin_left - margin_right
            y = height - margin_top
            
            c.setFont(font_name, font_size)
            
            # 按行处理文本
            lines = text_content.split('\n')
            
            for line in lines:
                # 如果是空行，只移动y位置
                if not line.strip():
                    y -= line_height * 0.5
                    if y < margin_bottom:
                        c.showPage()
                        c.setFont(font_name, font_size)
                        y = height - margin_top
                    continue
                
                # 处理长行，需要自动换行
                while line:
                    # 计算这一行能放多少字符
                    test_line = ""
                    for i, char in enumerate(line):
                        test_text = test_line + char
                        text_width = c.stringWidth(test_text, font_name, font_size)
                        
                        if text_width > max_width:
                            # 超出宽度，使用之前的文本
                            break
                        test_line = test_text
                    
                    # 如果一个字符都放不下，至少放一个
                    if not test_line and line:
                        test_line = line[0]
                        line = line[1:]
                    else:
                        line = line[len(test_line):]
                    
                    # 检查是否需要新页
                    if y < margin_bottom + line_height:
                        c.showPage()
                        c.setFont(font_name, font_size)
                        y = height - margin_top
                    
                    # 绘制文本
                    try:
                        c.drawString(margin_left, y, test_line)
                    except:
                        pass
                    
                    y -= line_height
            
            if progress_callback:
                progress_callback(70)
            
            # 保存PDF
            c.save()

            if progress_callback:
                progress_callback(90)

            # 复制为.caj文件
            shutil.copy2(temp_pdf, output_path)
            
            # 删除临时文件
            os.unlink(temp_pdf)

            if progress_callback:
                progress_callback(100)

            return ConvertResult(True, output_path)
        except Exception as e:
            import traceback
            return ConvertResult(False, error_msg=f"转换失败: {str(e)}\n{traceback.format_exc()}")
