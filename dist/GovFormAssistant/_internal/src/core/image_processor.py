import io
import os
from pathlib import Path
from typing import Any, Optional, Tuple

from PIL import Image, ImageOps

from .converters import bytes_to_kb, cm_to_px, mm_to_px


class ImageInfo:
    """Holds metadata extracted from an image file."""

    def __init__(self, path: str) -> None:
        self.path = path
        self.filename = os.path.basename(path)
        self.file_size_bytes = os.path.getsize(path)
        self.file_size_kb = bytes_to_kb(self.file_size_bytes)

        with Image.open(path) as img:
            self.width, self.height = img.size
            self.format = img.format or "Unknown"
            self.mode = img.mode
            dpi_info = img.info.get("dpi")
            if dpi_info and dpi_info[0] > 0:
                self.dpi_x = round(float(dpi_info[0]))
                self.dpi_y = round(float(dpi_info[1]))
            else:
                self.dpi_x = 96
                self.dpi_y = 96

    @property
    def dpi(self) -> int:
        return self.dpi_x

    def to_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "width": self.width,
            "height": self.height,
            "dpi_x": self.dpi_x,
            "dpi_y": self.dpi_y,
            "format": self.format,
            "mode": self.mode,
            "file_size_bytes": self.file_size_bytes,
            "file_size_kb": self.file_size_kb,
        }


def _to_rgb(img: Image.Image) -> Image.Image:
    """Flatten any transparency onto a white background and convert to RGB."""
    if img.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        converted = img.convert("RGBA")
        background.paste(converted, mask=converted.split()[3])
        return background
    if img.mode != "RGB":
        return img.convert("RGB")
    return img


class ImageProcessor:
    SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}

    @staticmethod
    def get_info(path: str) -> ImageInfo:
        return ImageInfo(path)

    @staticmethod
    def open_image(path: str) -> Image.Image:
        img = Image.open(path)
        return img.copy()

    @staticmethod
    def resize_by_pixels(
        img: Image.Image,
        width: int,
        height: int,
        maintain_aspect: bool = False,
        crop_to_fit: bool = False,
    ) -> Image.Image:
        if maintain_aspect and not crop_to_fit:
            img = img.copy()
            img.thumbnail((width, height), Image.LANCZOS)
            return img

        if crop_to_fit:
            src_ratio = img.width / img.height
            dst_ratio = width / height

            if src_ratio > dst_ratio:
                new_h = img.height
                new_w = int(img.height * dst_ratio)
            else:
                new_w = img.width
                new_h = int(img.width / dst_ratio)

            left = (img.width - new_w) // 2
            top = (img.height - new_h) // 2
            img = img.crop((left, top, left + new_w, top + new_h))

        return img.resize((width, height), Image.LANCZOS)

    @staticmethod
    def resize_by_cm(
        img: Image.Image,
        width_cm: float,
        height_cm: float,
        dpi: float = 96,
        maintain_aspect: bool = False,
        crop_to_fit: bool = False,
    ) -> Image.Image:
        w_px = max(1, int(cm_to_px(width_cm, dpi)))
        h_px = max(1, int(cm_to_px(height_cm, dpi)))
        return ImageProcessor.resize_by_pixels(img, w_px, h_px, maintain_aspect, crop_to_fit)

    @staticmethod
    def resize_by_mm(
        img: Image.Image,
        width_mm: float,
        height_mm: float,
        dpi: float = 96,
        maintain_aspect: bool = False,
        crop_to_fit: bool = False,
    ) -> Image.Image:
        w_px = max(1, int(mm_to_px(width_mm, dpi)))
        h_px = max(1, int(mm_to_px(height_mm, dpi)))
        return ImageProcessor.resize_by_pixels(img, w_px, h_px, maintain_aspect, crop_to_fit)

    @staticmethod
    def compress_to_size(
        img: Image.Image,
        target_kb: float,
        output_format: str = "JPEG",
        min_quality: int = 5,
    ) -> bytes:
        """Binary-search JPEG quality to compress image to at most target_kb."""
        target_bytes = int(target_kb * 1024)
        rgb_img = _to_rgb(img)
        fmt = "JPEG" if output_format.upper() in ("JPG", "JPEG") else output_format.upper()

        lo, hi = min_quality, 95
        best: Optional[bytes] = None

        while lo <= hi:
            mid = (lo + hi) // 2
            buf = io.BytesIO()
            rgb_img.save(buf, format=fmt, quality=mid, optimize=True)
            data = buf.getvalue()

            if len(data) <= target_bytes:
                best = data
                lo = mid + 1
            else:
                hi = mid - 1

        if best is None:
            # Even quality=min_quality is still too large — shrink dimensions
            buf = io.BytesIO()
            rgb_img.save(buf, format=fmt, quality=min_quality, optimize=True)
            data = buf.getvalue()
            if len(data) > target_bytes:
                scale = (target_bytes / len(data)) ** 0.5
                nw = max(1, int(rgb_img.width * scale))
                nh = max(1, int(rgb_img.height * scale))
                rgb_img = rgb_img.resize((nw, nh), Image.LANCZOS)
                buf = io.BytesIO()
                rgb_img.save(buf, format=fmt, quality=min_quality, optimize=True)
            best = buf.getvalue()

        return best

    @staticmethod
    def compress_between(
        img: Image.Image,
        min_kb: float,
        max_kb: float,
        output_format: str = "JPEG",
    ) -> Tuple[bytes, bool]:
        """
        Compress to fit within [min_kb, max_kb].
        Returns (data, within_range).
        """
        data = ImageProcessor.compress_to_size(img, max_kb, output_format)
        size_kb = len(data) / 1024
        in_range = size_kb >= min_kb
        return data, in_range

    @staticmethod
    def save_image(
        img: Image.Image,
        output_path: str,
        quality: int = 85,
    ) -> str:
        ext = Path(output_path).suffix.lower()
        fmt = "JPEG" if ext in (".jpg", ".jpeg") else ext.lstrip(".").upper()

        save_img = img
        if fmt in ("JPEG",) and save_img.mode not in ("RGB",):
            save_img = _to_rgb(save_img)

        save_img.save(output_path, format=fmt, quality=quality, optimize=True)
        return output_path

    @staticmethod
    def save_bytes(data: bytes, output_path: str) -> str:
        with open(output_path, "wb") as f:
            f.write(data)
        return output_path

    @staticmethod
    def convert_format(img: Image.Image, target_ext: str) -> Image.Image:
        if target_ext.lower() in (".jpg", ".jpeg"):
            return _to_rgb(img)
        return img

    @staticmethod
    def validate(
        path: str,
        target_width: int,
        target_height: int,
        min_kb: Optional[float],
        max_kb: Optional[float],
    ) -> dict[str, Any]:
        info = ImageInfo(path)
        width_ok = info.width == target_width
        height_ok = info.height == target_height
        size_ok = True
        size_error = ""

        if min_kb is not None and info.file_size_kb < min_kb:
            size_ok = False
            size_error = f"Too small: {info.file_size_kb:.1f} KB (min {min_kb} KB)"
        elif max_kb is not None and info.file_size_kb > max_kb:
            size_ok = False
            size_error = f"Too large: {info.file_size_kb:.1f} KB (max {max_kb} KB)"

        return {
            "all_ok": width_ok and height_ok and size_ok,
            "width_ok": width_ok,
            "height_ok": height_ok,
            "size_ok": size_ok,
            "size_error": size_error,
            "actual_width": info.width,
            "actual_height": info.height,
            "actual_size_kb": info.file_size_kb,
            "format": info.format,
            "dpi": info.dpi,
        }
