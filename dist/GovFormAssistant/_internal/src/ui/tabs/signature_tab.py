import io
import os
from typing import Optional

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.config.settings import settings
from src.core.image_processor import ImageInfo, ImageProcessor
from src.core.signature_processor import SignatureProcessor
from src.ui.widgets.drop_zone import DropZone
from src.ui.widgets.image_preview import ImagePreview


class SignatureTab(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._current_img: Optional[Image.Image] = None
        self._current_path: Optional[str] = None
        self._build_ui()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        left = QVBoxLayout()
        left.setSpacing(12)

        self.drop = DropZone(accepted_extensions=[".jpg", ".jpeg", ".png", ".bmp"])
        self.drop.files_dropped.connect(self._load_file)
        left.addWidget(self.drop)

        browse_btn = QPushButton("Browse Signature Image...")
        browse_btn.setObjectName("primaryButton")
        browse_btn.clicked.connect(self._browse)
        left.addWidget(browse_btn)

        # Info
        self.info_box = QGroupBox("Loaded File")
        info_layout = QVBoxLayout(self.info_box)
        self.info_label = QLabel("No image loaded.")
        self.info_label.setObjectName("infoLabel")
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        left.addWidget(self.info_box)

        # Target dimensions
        dim_box = QGroupBox("Target Dimensions")
        dim_layout = QVBoxLayout(dim_box)

        row_w = QHBoxLayout()
        row_w.addWidget(QLabel("Width (px):"))
        self.spin_w = QSpinBox()
        self.spin_w.setRange(10, 5000)
        self.spin_w.setValue(140)
        self.spin_w.valueChanged.connect(self._refresh_preview)
        row_w.addWidget(self.spin_w)
        dim_layout.addLayout(row_w)

        row_h = QHBoxLayout()
        row_h.addWidget(QLabel("Height (px):"))
        self.spin_h = QSpinBox()
        self.spin_h.setRange(10, 5000)
        self.spin_h.setValue(60)
        self.spin_h.valueChanged.connect(self._refresh_preview)
        row_h.addWidget(self.spin_h)
        dim_layout.addLayout(row_h)

        left.addWidget(dim_box)

        # Compression
        comp_box = QGroupBox("File Size Target")
        comp_layout = QVBoxLayout(comp_box)

        self.chk_compress = QCheckBox("Compress to max KB")
        self.chk_compress.setChecked(True)
        self.chk_compress.toggled.connect(self._refresh_preview)
        comp_layout.addWidget(self.chk_compress)

        row_kb = QHBoxLayout()
        row_kb.addWidget(QLabel("Max size (KB):"))
        self.spin_kb = QDoubleSpinBox()
        self.spin_kb.setRange(1, 5000)
        self.spin_kb.setValue(20)
        self.spin_kb.setSuffix(" KB")
        self.spin_kb.valueChanged.connect(self._refresh_preview)
        row_kb.addWidget(self.spin_kb)
        comp_layout.addLayout(row_kb)

        left.addWidget(comp_box)

        # Processing options
        opt_box = QGroupBox("Processing Options")
        opt_layout = QVBoxLayout(opt_box)
        self.chk_remove_bg = QCheckBox("Clean white background")
        self.chk_remove_bg.setChecked(True)
        self.chk_remove_bg.toggled.connect(self._refresh_preview)
        self.chk_bw = QCheckBox("Convert to black & white")
        self.chk_bw.toggled.connect(self._refresh_preview)
        self.chk_trim = QCheckBox("Trim excess whitespace")
        self.chk_trim.setChecked(True)
        self.chk_trim.toggled.connect(self._refresh_preview)
        opt_layout.addWidget(self.chk_remove_bg)
        opt_layout.addWidget(self.chk_bw)
        opt_layout.addWidget(self.chk_trim)
        left.addWidget(opt_box)

        save_btn = QPushButton("Save Processed Signature")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._save)
        left.addWidget(save_btn)

        left.addStretch()

        # Right: previews
        right = QVBoxLayout()
        right.setSpacing(12)

        preview_row = QHBoxLayout()
        self.before_preview = ImagePreview("Original")
        self.after_preview = ImagePreview("Processed")
        preview_row.addWidget(self.before_preview)
        preview_row.addWidget(self.after_preview)
        right.addLayout(preview_row)

        self.result_label = QLabel()
        self.result_label.setObjectName("resultLabel")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right.addWidget(self.result_label)

        right.addStretch()

        root.addLayout(left, stretch=1)
        root.addLayout(right, stretch=2)

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Signature Image", settings.last_output_dir,
            "Images (*.jpg *.jpeg *.png *.bmp)"
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
                f"File size: {info.file_size_kb:.1f} KB"
            )
            self.before_preview.set_image(img)
            self._refresh_preview()
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"Could not open image:\n{exc}")

    def _process(self):
        if self._current_img is None:
            return None, None
        max_kb = self.spin_kb.value() if self.chk_compress.isChecked() else None
        return SignatureProcessor.process(
            self._current_img.copy(),
            self.spin_w.value(),
            self.spin_h.value(),
            max_kb,
            remove_bg=self.chk_remove_bg.isChecked(),
            make_bw=self.chk_bw.isChecked(),
            trim=self.chk_trim.isChecked(),
        )

    def _refresh_preview(self) -> None:
        if self._current_img is None:
            return
        try:
            result_img, compressed = self._process()
            if result_img:
                size_info = (
                    f"{len(compressed)/1024:.1f} KB"
                    if compressed
                    else f"{result_img.width}×{result_img.height}"
                )
                self.after_preview.set_image(result_img, size_info)
                if compressed:
                    self.result_label.setText(
                        f"Output: {result_img.width} × {result_img.height} px | "
                        f"{len(compressed)/1024:.1f} KB"
                    )
        except Exception:
            pass

    def _save(self) -> None:
        if self._current_img is None:
            QMessageBox.information(self, "No Image", "Please load an image first.")
            return
        result_img, compressed = self._process()
        if result_img is None:
            return

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Save Signature", os.path.join(settings.last_output_dir, "signature.jpg"),
            "JPEG (*.jpg);;PNG (*.png)"
        )
        if not out_path:
            return
        try:
            if compressed and out_path.lower().endswith((".jpg", ".jpeg")):
                ImageProcessor.save_bytes(compressed, out_path)
            else:
                ImageProcessor.save_image(result_img, out_path)
            settings.last_output_dir = os.path.dirname(out_path)
            QMessageBox.information(self, "Saved", f"Signature saved!\n{out_path}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Could not save:\n{exc}")
