import os
from pathlib import Path
from typing import Optional


def unique_output_path(directory: str, filename: str, suffix: str = "_processed") -> str:
    """Return a path that won't overwrite an existing file."""
    stem = Path(filename).stem
    ext = Path(filename).suffix
    candidate = os.path.join(directory, f"{stem}{suffix}{ext}")
    counter = 1
    while os.path.exists(candidate):
        candidate = os.path.join(directory, f"{stem}{suffix}_{counter}{ext}")
        counter += 1
    return candidate


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    kb = size_bytes / 1024
    if kb < 1024:
        return f"{kb:.1f} KB"
    return f"{kb / 1024:.2f} MB"


def is_image_file(path: str) -> bool:
    return Path(path).suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}


def is_pdf_file(path: str) -> bool:
    return Path(path).suffix.lower() == ".pdf"


def safe_makedirs(directory: str) -> None:
    Path(directory).mkdir(parents=True, exist_ok=True)
