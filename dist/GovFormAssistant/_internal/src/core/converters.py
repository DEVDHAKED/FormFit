from math import gcd
from typing import Tuple


def px_to_cm(pixels: float, dpi: float = 96) -> float:
    return round((pixels / dpi) * 2.54, 4)


def cm_to_px(cm: float, dpi: float = 96) -> float:
    return (cm / 2.54) * dpi


def px_to_mm(pixels: float, dpi: float = 96) -> float:
    return round((pixels / dpi) * 25.4, 4)


def mm_to_px(mm: float, dpi: float = 96) -> float:
    return (mm / 25.4) * dpi


def px_to_inch(pixels: float, dpi: float = 96) -> float:
    return round(pixels / dpi, 4)


def inch_to_px(inches: float, dpi: float = 96) -> float:
    return inches * dpi


def bytes_to_kb(b: float) -> float:
    return round(b / 1024, 2)


def kb_to_bytes(kb: float) -> int:
    return int(kb * 1024)


def kb_to_mb(kb: float) -> float:
    return round(kb / 1024, 4)


def mb_to_kb(mb: float) -> float:
    return round(mb * 1024, 2)


def aspect_ratio(width: int, height: int) -> Tuple[int, int]:
    if width == 0 or height == 0:
        return (0, 0)
    g = gcd(int(width), int(height))
    return width // g, height // g


def scale_dimensions(
    src_w: int,
    src_h: int,
    dst_w: int,
    dst_h: int,
) -> Tuple[int, int]:
    """Scale src to fit inside dst while maintaining aspect ratio."""
    ratio = min(dst_w / max(src_w, 1), dst_h / max(src_h, 1))
    return int(src_w * ratio), int(src_h * ratio)
