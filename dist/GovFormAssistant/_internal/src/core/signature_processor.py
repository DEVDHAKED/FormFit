from typing import Optional, Tuple

from PIL import Image, ImageOps

from .image_processor import ImageProcessor, _to_rgb


class SignatureProcessor:
    @staticmethod
    def to_black_and_white(img: Image.Image, threshold: int = 128) -> Image.Image:
        """Threshold to pure black-and-white (no grays)."""
        gray = img.convert("L")
        bw = gray.point(lambda p: 255 if p > threshold else 0)
        return bw.convert("RGB")

    @staticmethod
    def remove_background(
        img: Image.Image,
        tolerance: int = 30,
    ) -> Image.Image:
        """Replace near-white pixels with white (non-destructive cleanup)."""
        rgb = img.convert("RGB")
        pixels = rgb.load()
        w, h = rgb.size

        for y in range(h):
            for x in range(w):
                r, g, b = pixels[x, y]  # type: ignore[index]
                if r > 255 - tolerance and g > 255 - tolerance and b > 255 - tolerance:
                    pixels[x, y] = (255, 255, 255)  # type: ignore[index]

        return rgb

    @staticmethod
    def trim_whitespace(img: Image.Image, padding: int = 5) -> Image.Image:
        """Crop away excess white borders around signature content."""
        gray = img.convert("L")
        inverted = ImageOps.invert(gray)
        bbox = inverted.getbbox()

        if bbox is None:
            return img

        w, h = img.size
        left = max(0, bbox[0] - padding)
        top = max(0, bbox[1] - padding)
        right = min(w, bbox[2] + padding)
        bottom = min(h, bbox[3] + padding)

        return img.crop((left, top, right, bottom))

    @staticmethod
    def process(
        img: Image.Image,
        target_width: int,
        target_height: int,
        target_max_kb: Optional[float] = None,
        remove_bg: bool = True,
        make_bw: bool = False,
        trim: bool = True,
    ) -> Tuple[Image.Image, Optional[bytes]]:
        """Full signature processing pipeline. Returns (preview_img, compressed_bytes_or_None)."""
        result = img.copy()

        if remove_bg:
            result = SignatureProcessor.remove_background(result)

        if make_bw:
            result = SignatureProcessor.to_black_and_white(result)

        if trim:
            result = SignatureProcessor.trim_whitespace(result)

        result = ImageProcessor.resize_by_pixels(
            result, target_width, target_height, crop_to_fit=True
        )

        compressed: Optional[bytes] = None
        if target_max_kb:
            compressed = ImageProcessor.compress_to_size(result, target_max_kb, "JPEG")

        return result, compressed
