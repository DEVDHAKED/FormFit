import os
from typing import Optional

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from src.config.settings import settings
from src.core.converters import bytes_to_kb
from src.core.image_processor import ImageInfo, ImageProcessor
from src.ui.widgets.drop_zone import DropZone
from src.ui.widgets.image_preview import ImagePreview


class FileSizeTab(QWidget):
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

        # Drop zone
        self.drop = DropZone(accepted_extensions=[".jpg", ".jpeg", ".png"])
        self.drop.files_dropped.connect(self._load_file)
        left.addWidget(self.drop)

        browse_btn = QPushButton("Browse Image...")
        browse_btn.setObjectName("primaryButton")
        browse_btn.clicked.connect(self._browse)
        left.addWidget(browse_btn)

        # Info
        self.info_box = QGroupBox("Current File")
        info_layout = QVBoxLayout(self.info_box)
        self.info_label = QLabel("No image loaded.")
        self.info_label.setObjectName("infoLabel")
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        left.addWidget(self.info_box)

        # Target mode
        mode_box = QGroupBox("Target Size Mode")
        mode_layout = QVBoxLayout(mode_box)
        self.rb_under = QRadioButton("Under X KB")
        self.rb_between = QRadioButton("Between X and Y KB")
        self.rb_under.setChecked(True)
        mode_layout.addWidget(self.rb_under)
        mode_layout.addWidget(self.rb_between)
        left.addWidget(mode_box)

        # Size inputs
        size_box = QGroupBox("Target Size (KB)")
        size_layout = QVBoxLayout(size_box)

        row_max = QHBoxLayout()
        row_max.addWidget(QLabel("Max size (KB):"))
        self.spin_max = QDoubleSpinBox()
        self.spin_max.setRange(1, 100000)
        self.spin_max.setValue(50)
        self.spin_max.setSuffix(" KB")
        row_max.addWidget(self.spin_max)
        size_layout.addLayout(row_max)

        row_min = QHBoxLayout()
        row_min.addWidget(QLabel("Min size (KB):"))
        self.spin_min = QDoubleSpinBox()
        self.spin_min.setRange(1, 100000)
        self.spin_min.setValue(20)
        self.spin_min.setSuffix(" KB")
        row_min.addWidget(self.spin_min)
        size_layout.addLayout(row_min)

        left.addWidget(size_box)

        # Output format
        fmt_box = QGroupBox("Output Format")
        fmt_layout = QHBoxLayout(fmt_box)
        fmt_layout.addWidget(QLabel("Format:"))
        self.combo_fmt = QComboBox()
        self.combo_fmt.addItems(["JPEG", "PNG"])
        fmt_layout.addWidget(self.combo_fmt)
        left.addWidget(fmt_box)

        # Quick presets
        quick_box = QGroupBox("Quick Presets")
        quick_layout = QVBoxLayout(quick_box)
        presets = [
            ("Under 20 KB", 20, None),
            ("Under 50 KB", 50, None),
            ("Under 100 KB", 100, None),
            ("20 – 50 KB", 50, 20),
            ("10 – 20 KB", 20, 10),
        ]
        for label, mx, mn in presets:
            btn = QPushButton(label)
            btn.setObjectName("secondaryButton")
            btn.clicked.connect(lambda _, x=mx, n=mn: self._apply_quick_preset(x, n))
            quick_layout.addWidget(btn)
        left.addWidget(quick_box)

        # Actions
        compress_btn = QPushButton("Compress & Save")
        compress_btn.setObjectName("primaryButton")
        compress_btn.clicked.connect(self._compress_and_save)
        left.addWidget(compress_btn)

        left.addStretch()

        # Right: previews + result
        right = QVBoxLayout()
        right.setSpacing(12)

        preview_row = QHBoxLayout()
        self.before_preview = ImagePreview("Original")
        self.after_preview = ImagePreview("Compressed Preview")
        preview_row.addWidget(self.before_preview)
        preview_row.addWidget(self.after_preview)
        right.addLayout(preview_row)

        self.result_label = QLabel()
        self.result_label.setObjectName("resultLabel")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setWordWrap(True)
        right.addWidget(self.result_label)

        right.addStretch()

        root.addLayout(left, stretch=1)
        root.addLayout(right, stretch=2)

    def _apply_quick_preset(self, max_kb: float, min_kb: Optional[float]) -> None:
        self.spin_max.setValue(max_kb)
        if min_kb is not None:
            self.spin_min.setValue(min_kb)
            self.rb_between.setChecked(True)
        else:
            self.rb_under.setChecked(True)
        self._update_preview()

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            settings.last_output_dir,
            "Images (*.jpg *.jpeg *.png)",
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
                f"Current file size: {info.file_size_kb:.1f} KB"
            )
            self.before_preview.set_image(img, f"{info.file_size_kb:.1f} KB")
            self._update_preview()
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"Could not open image:\n{exc}")

    def _get_compressed(self) -> Optional[bytes]:
        if self._current_img is None:
            return None
        fmt = self.combo_fmt.currentText()
        max_kb = self.spin_max.value()

        if self.rb_between.isChecked():
            min_kb = self.spin_min.value()
            data, in_range = ImageProcessor.compress_between(
                self._current_img, min_kb, max_kb, fmt
            )
            if not in_range:
                self.result_label.setText(
                    f"Warning: Could only reach {len(data)/1024:.1f} KB "
                    f"(min target {min_kb} KB)"
                )
            else:
                self.result_label.setText(
                    f"Result: {len(data)/1024:.1f} KB  (target {min_kb}–{max_kb} KB)"
                )
            return data
        else:
            data = ImageProcessor.compress_to_size(self._current_img, max_kb, fmt)
            self.result_label.setText(
                f"Result: {len(data)/1024:.1f} KB  (target < {max_kb} KB)"
            )
            return data

    def _update_preview(self) -> None:
        if self._current_img is None:
            return
        from PIL import Image
        import io
        data = self._get_compressed()
        if data:
            preview_img = Image.open(io.BytesIO(data))
            self.after_preview.set_image(preview_img, f"{len(data)/1024:.1f} KB")

    def _compress_and_save(self) -> None:
        if self._current_img is None:
            QMessageBox.information(self, "No Image", "Please load an image first.")
            return

        data = self._get_compressed()
        if data is None:
            return

        fmt = self.combo_fmt.currentText().lower()
        ext = ".jpg" if fmt == "jpeg" else ".png"
        default_name = "compressed" + ext

        out_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Compressed Image",
            os.path.join(settings.last_output_dir, default_name),
            f"Image (*{ext})",
        )
        if not out_path:
            return

        try:
            ImageProcessor.save_bytes(data, out_path)
            settings.last_output_dir = os.path.dirname(out_path)
            QMessageBox.information(
                self,
                "Saved",
                f"Saved!\nFinal size: {len(data)/1024:.1f} KB\n{out_path}",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Could not save:\n{exc}")
