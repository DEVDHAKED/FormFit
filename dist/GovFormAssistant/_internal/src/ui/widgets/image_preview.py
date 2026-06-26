from typing import Optional

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout


def pil_to_pixmap(img: Image.Image, max_w: int = 400, max_h: int = 400) -> QPixmap:
    """Convert a PIL image to a scaled QPixmap for display."""
    display = img.copy()
    display.thumbnail((max_w, max_h), Image.LANCZOS)

    if display.mode == "RGBA":
        fmt = QImage.Format.Format_RGBA8888
        raw = display.tobytes("raw", "RGBA")
    else:
        rgb = display.convert("RGB")
        fmt = QImage.Format.Format_RGB888
        raw = rgb.tobytes("raw", "RGB")

    qimg = QImage(raw, display.width, display.height, fmt)
    return QPixmap.fromImage(qimg)


class ImagePreview(QFrame):
    """A bordered frame that shows a PIL image with dimensions label underneath."""

    def __init__(self, label: str = "Preview", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("imagePreviewFrame")
        self._label_text = label

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        self._title = QLabel(label)
        self._title.setObjectName("previewTitle")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._title)

        self._img_label = QLabel()
        self._img_label.setObjectName("previewImage")
        self._img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_label.setMinimumSize(200, 200)
        self._img_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._img_label.setText("No image")
        layout.addWidget(self._img_label)

        self._info_label = QLabel()
        self._info_label.setObjectName("previewInfo")
        self._info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._info_label)

    def set_image(self, img: Image.Image, info: str = "") -> None:
        pixmap = pil_to_pixmap(img, max_w=380, max_h=380)
        self._img_label.setPixmap(pixmap)
        self._info_label.setText(info or f"{img.width} × {img.height} px")

    def set_pixmap(self, pixmap: QPixmap, info: str = "") -> None:
        self._img_label.setPixmap(pixmap)
        self._info_label.setText(info)

    def clear(self) -> None:
        self._img_label.clear()
        self._img_label.setText("No image")
        self._info_label.setText("")
