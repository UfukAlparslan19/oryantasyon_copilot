import fitz  # PyMuPDF
from pathlib import Path
import io
from PIL import Image

class PDFViewer:
    def __init__(self, pdf_dir: Path):
        self.pdf_dir = pdf_dir

    def get_page_image(self, filename: str, page_num: int) -> Image.Image | None:
        """Belirtilen PDF dosyasının ilgili sayfasını PIL Image olarak döndürür."""
        pdf_path = self.pdf_dir / filename
        if not pdf_path.exists():
            return None
            
        try:
            # fitz sayfa numaraları 0'dan başlar
            doc = fitz.open(pdf_path)
            if page_num > 0 and page_num <= len(doc):
                page = doc[page_num - 1]
                # Yüksek çözünürlük için matrix kullanımı
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat)
                
                img_data = pix.tobytes("png")
                return Image.open(io.BytesIO(img_data))
        except Exception as e:
            print(f"PDF Render hatası: {e}")
        return None
