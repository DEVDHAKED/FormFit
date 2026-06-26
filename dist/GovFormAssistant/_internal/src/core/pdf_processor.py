import io
import os
from pathlib import Path
from typing import List, Tuple

from PIL import Image

try:
    import fitz  # PyMuPDF
    _HAS_FITZ = True
except ImportError:
    _HAS_FITZ = False

try:
    from pypdf import PdfWriter, PdfReader
    _HAS_PYPDF = True
except ImportError:
    _HAS_PYPDF = False


def _require_pypdf() -> None:
    if not _HAS_PYPDF:
        raise ImportError("pypdf is required. Run: pip install pypdf")


def _require_fitz() -> None:
    if not _HAS_FITZ:
        raise ImportError("PyMuPDF is required. Run: pip install PyMuPDF")


class PDFProcessor:
    @staticmethod
    def get_page_count(path: str) -> int:
        if _HAS_PYPDF:
            return len(PdfReader(path).pages)
        _require_fitz()
        doc = fitz.open(path)
        n = doc.page_count
        doc.close()
        return n

    @staticmethod
    def merge(input_paths: List[str], output_path: str) -> str:
        _require_pypdf()
        writer = PdfWriter()
        for path in input_paths:
            reader = PdfReader(path)
            for page in reader.pages:
                writer.add_page(page)
        with open(output_path, "wb") as f:
            writer.write(f)
        return output_path

    @staticmethod
    def split_by_pages(
        input_path: str,
        output_dir: str,
        pages_per_file: int = 1,
    ) -> List[str]:
        _require_pypdf()
        reader = PdfReader(input_path)
        total = len(reader.pages)
        stem = Path(input_path).stem
        outputs: List[str] = []

        for i in range(0, total, pages_per_file):
            writer = PdfWriter()
            for page in reader.pages[i : i + pages_per_file]:
                writer.add_page(page)
            part = i // pages_per_file + 1
            out = os.path.join(output_dir, f"{stem}_part{part}.pdf")
            with open(out, "wb") as f:
                writer.write(f)
            outputs.append(out)

        return outputs

    @staticmethod
    def split_by_range(
        input_path: str,
        output_dir: str,
        ranges: List[Tuple[int, int]],
    ) -> List[str]:
        """Split PDF by explicit page ranges (1-based, inclusive)."""
        _require_pypdf()
        reader = PdfReader(input_path)
        total = len(reader.pages)
        stem = Path(input_path).stem
        outputs: List[str] = []

        for idx, (start, end) in enumerate(ranges, start=1):
            writer = PdfWriter()
            for p in range(start - 1, min(end, total)):
                writer.add_page(reader.pages[p])
            out = os.path.join(output_dir, f"{stem}_range{idx}.pdf")
            with open(out, "wb") as f:
                writer.write(f)
            outputs.append(out)

        return outputs

    @staticmethod
    def compress(input_path: str, output_path: str) -> str:
        _require_fitz()
        doc = fitz.open(input_path)
        doc.save(output_path, garbage=4, deflate=True, clean=True)
        doc.close()
        return output_path

    @staticmethod
    def to_images(
        input_path: str,
        output_dir: str,
        dpi: int = 150,
        fmt: str = "jpg",
    ) -> List[str]:
        _require_fitz()
        doc = fitz.open(input_path)
        stem = Path(input_path).stem
        outputs: List[str] = []
        mat = fitz.Matrix(dpi / 72, dpi / 72)

        for i, page in enumerate(doc, start=1):
            pix = page.get_pixmap(matrix=mat)
            out = os.path.join(output_dir, f"{stem}_page{i}.{fmt.lower()}")

            if fmt.lower() == "png":
                pix.save(out)
            else:
                img_bytes = pix.tobytes("ppm")
                img = Image.open(io.BytesIO(img_bytes))
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(out, "JPEG", quality=85)

            outputs.append(out)

        doc.close()
        return outputs

    @staticmethod
    def images_to_pdf(image_paths: List[str], output_path: str) -> str:
        if not image_paths:
            raise ValueError("No images provided")

        imgs: List[Image.Image] = []
        for path in image_paths:
            img = Image.open(path)
            if img.mode != "RGB":
                img = img.convert("RGB")
            imgs.append(img)

        first = imgs[0]
        rest = imgs[1:]
        first.save(output_path, "PDF", save_all=True, append_images=rest)
        return output_path
