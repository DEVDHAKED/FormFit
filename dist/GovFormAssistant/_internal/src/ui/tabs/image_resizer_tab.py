import os
from typing import Optional

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.config.settings import settings
from src.core.converters import bytes_to_kb, cm_to_px, mm_to_px
from src.core.image_processor import ImageInfo, ImageProcessor
from src.ui.widgets.drop_zone import DropZone
from src.ui.widgets.image_preview import ImagePreview


class ImageResizerTab(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._current_img: Optional[Image.Image] = None
        self._current_path: Optional[str] = None
        self._build_ui()

    # ------------------------------------------------------------------ #
    # UI Construction
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        # Left: controls
        left = QVBoxLayout()
        left.setSpacing(12)

        # Drop zone
        self.drop = DropZone(accepted_extensions=[".jpg", ".jpeg", ".png", ".bmp", ".tiff"])
        self.drop.files_dropped.connect(self._load_file)
        left.addWidget(self.drop)

        # Browse button
        browse_btn = QPushButton("Browse Image...")
        browse_btn.setObjectName("primaryButton")
        browse_btn.clicked.connect(self._browse)
        left.addWidget(browse_btn)

        # Image info panel
        self.info_box = QGroupBox("Image Information")
        info_layout = QVBoxLayout(self.info_box)
        self.info_label = QLabel("No image loaded.")
        self.info_label.setObjectName("infoLabel")
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        left.addWidget(self.info_box)

        # Resize unit selector
        unit_box = QGroupBox("Resize Mode")
        unit_layout = QVBoxLayout(unit_box)
        self.rb_pixels = QRadioButton("Pixels (px)")
        self.rb_cm = QRadioButton("Centimeters (cm)")
        self.rb_mm = QRadioButton("Millimeters (mm)")
        self.rb_pixels.setChecked(True)
        for rb in (self.rb_pixels, self.rb_cm, self.rb_mm):
            unit_layout.addWidget(rb)
        left.addWidget(unit_box)

        # Dimensions group
        dim_box = QGroupBox("Target Dimensions")
        dim_layout = QVBoxLayout(dim_box)

        row_w = QHBoxLayout()
        row_w.addWidget(QLabel("Width:"))
        self.spin_w = QDoubleSpinBox()
        self.spin_w.setRange(1, 99999)
        self.spin_w.setValue(200)
        self.spin_w.setSuffix(" px")
        self.spin_w.valueChanged.connect(self._refresh_preview)
        row_w.addWidget(self.spin_w)
        dim_layout.addLayout(row_w)

        row_h = QHBoxLayout()
        row_h.addWidget(QLabel("Height:"))
        self.spin_h = QDoubleSpinBox()
        self.spin_h.setRange(1, 99999)
        self.spin_h.setValue(200)
        self.spin_h.setSuffix(" px")
        self.spin_h.valueChanged.connect(self._refresh_preview)
        row_h.addWidget(self.spin_h)
        dim_layout.addLayout(row_h)

        row_dpi = QHBoxLayout()
        row_dpi.addWidget(QLabel("DPI (for cm/mm):"))
        self.spin_dpi = QSpinBox()
        self.spin_dpi.setRange(72, 600)
        self.spin_dpi.setValue(settings.default_dpi)
        row_dpi.addWidget(self.spin_dpi)
        dim_layout.addLayout(row_dpi)

        left.addWidget(dim_box)

        # Options
        opt_box = QGroupBox("Options")
        opt_layout = QVBoxLayout(opt_box)
        self.chk_aspect = QCheckBox("Maintain aspect ratio")
        self.chk_crop = QCheckBox("Crop to fit (exact dimensions)")
        opt_layout.addWidget(self.chk_aspect)
        opt_layout.addWidget(self.chk_crop)
        left.addWidget(opt_box)

        # Update suffix when unit changes
        for rb in (self.rb_pixels, self.rb_cm, self.rb_mm):
            rb.toggled.connect(self._update_unit_suffix)

        # Action buttons
        save_btn = QPushButton("Save Resized Image")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._save)
        left.addWidget(save_btn)

        left.addStretch()

        # Right: previews
        right = QVBoxLayout()
        right.setSpacing(12)

        preview_row = QHBoxLayout()
        self.before_preview = ImagePreview("Original")
        self.after_preview = ImagePreview("Resized Preview")
        preview_row.addWidget(self.before_preview)
        preview_row.addWidget(self.after_preview)
        right.addLayout(preview_row)
        right.addStretch()

        root.addLayout(left, stretch=1)
        root.addLayout(right, stretch=2)

    # ------------------------------------------------------------------ #
    # Logic
    # ------------------------------------------------------------------ #

    def _update_unit_suffix(self) -> None:
        if self.rb_pixels.isChecked():
            suffix = " px"
        elif self.rb_cm.isChecked():
            suffix = " cm"
        else:
            suffix = " mm"
        self.spin_w.setSuffix(suffix)
        self.spin_h.setSuffix(suffix)

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            settings.last_output_dir,
            "Images (*.jpg *.jpeg *.png *.bmp *.tiff *.webp)",
        )
        if path:
            self._load_file([path])

    def _load_file(self, paths: list) -> None:
        path = paths[0]
        try:
            img = ImageProcessor.open_image(path)
            self._current_img = img
            self._current_path = path
            info = ImageInfo(path)
            self.info_label.setText(
                f"File: {info.filename}\n"
                f"Size: {info.width} × {info.height} px\n"
                f"File size: {info.file_size_kb:.1f} KB\n"
                f"Format: {info.format}  |  DPI: {info.dpi}"
            )
            self.before_preview.set_image(img)
            self._refresh_preview()
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"Could not open image:\n{exc}")

    def _compute_resized(self) -> Optional[Image.Image]:
        if self._current_img is None:
            return None
        w = self.spin_w.value()
        h = self.spin_h.value()
        dpi = self.spin_dpi.value()
        maintain = self.chk_aspect.isChecked()
        crop = self.chk_crop.isChecked()

        if self.rb_pixels.isChecked():
            return ImageProcessor.resize_by_pixels(
                self._current_img.copy(), int(w), int(h), maintain, crop
            )
        elif self.rb_cm.isChecked():
            return ImageProcessor.resize_by_cm(
                self._current_img.copy(), w, h, dpi, maintain, crop
            )
        else:
            return ImageProcessor.resize_by_mm(
                self._current_img.copy(), w, h, dpi, maintain, crop
            )

    def _refresh_preview(self) -> None:
        result = self._compute_resized()
        if result:
            self.after_preview.set_image(
                result, f"{result.width} × {result.height} px"
            )

    def _save(self) -> None:
        if self._current_img is None:
            QMessageBox.information(self, "No Image", "Please load an image first.")
            return

        result = self._compute_resized()
        if result is None:
            return

        out_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Resized Image",
            os.path.join(settings.last_output_dir, "resized.jpg"),
            "JPEG (*.jpg);;PNG (*.png)",
        )
        if not out_path:
            return

        try:
            ImageProcessor.save_image(result, out_path)
            settings.last_output_dir = os.path.dirname(out_path)
            sz = bytes_to_kb(os.path.getsize(out_path))
            QMessageBox.information(
                self,
                "Saved",
                f"Image saved!\n{result.width} × {result.height} px | {sz:.1f} KB\n{out_path}",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Could not save image:\n{exc}")
