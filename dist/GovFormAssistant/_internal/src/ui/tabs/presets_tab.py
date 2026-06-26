import os
from typing import Optional

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.config.presets import EXAM_PRESETS, ExamPreset, PhotoRequirement
from src.config.settings import settings
from src.core.image_processor import ImageInfo, ImageProcessor
from src.ui.widgets.drop_zone import DropZone
from src.ui.widgets.image_preview import ImagePreview


def _check_color(ok: bool) -> str:
    return "#2ecc71" if ok else "#e74c3c"


class ValidationRow(QWidget):
    def __init__(self, key: str, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.key_label = QLabel(key)
        self.key_label.setFixedWidth(130)
        self.value_label = QLabel("-")
        self.status_label = QLabel()
        self.status_label.setFixedWidth(24)
        layout.addWidget(self.key_label)
        layout.addWidget(self.value_label, stretch=1)
        layout.addWidget(self.status_label)

    def set(self, value: str, ok: Optional[bool] = None) -> None:
        self.value_label.setText(value)
        if ok is None:
            self.status_label.setText("")
        else:
            self.status_label.setText("✓" if ok else "✗")
            color = _check_color(ok)
            self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")


class PresetsTab(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._current_img: Optional[Image.Image] = None
        self._current_path: Optional[str] = None
        self._build_ui()
        self._on_preset_changed()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        left = QVBoxLayout()
        left.setSpacing(12)

        # Preset selector
        preset_box = QGroupBox("Select Government Exam Preset")
        preset_layout = QVBoxLayout(preset_box)

        self.combo_exam = QComboBox()
        for key, preset in EXAM_PRESETS.items():
            self.combo_exam.addItem(f"{preset.exam_name} — {preset.full_name}", key)
        idx = self.combo_exam.findData(settings.last_preset)
        if idx >= 0:
            self.combo_exam.setCurrentIndex(idx)
        self.combo_exam.currentIndexChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(self.combo_exam)

        # Type selector
        self.combo_type = QComboBox()
        self.combo_type.addItems(["Photo", "Signature"])
        self.combo_type.currentIndexChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(self.combo_type)

        left.addWidget(preset_box)

        # Requirements display
        req_box = QGroupBox("Requirements")
        req_layout = QVBoxLayout(req_box)
        self.req_label = QLabel()
        self.req_label.setObjectName("infoLabel")
        self.req_label.setWordWrap(True)
        req_layout.addWidget(self.req_label)
        left.addWidget(req_box)

        # Image loader
        self.drop = DropZone(accepted_extensions=[".jpg", ".jpeg", ".png", ".bmp"])
        self.drop.files_dropped.connect(self._load_file)
        left.addWidget(self.drop)

        browse_btn = QPushButton("Browse Image...")
        browse_btn.setObjectName("primaryButton")
        browse_btn.clicked.connect(self._browse)
        left.addWidget(browse_btn)

        # One-click process
        process_btn = QPushButton("Make Eligible (Auto-Process)")
        process_btn.setObjectName("successButton")
        process_btn.clicked.connect(self._make_eligible)
        left.addWidget(process_btn)

        left.addStretch()

        # Right: validation + preview
        right = QVBoxLayout()
        right.setSpacing(12)

        val_box = QGroupBox("Validation")
        val_layout = QVBoxLayout(val_box)
        self.val_width = ValidationRow("Width:")
        self.val_height = ValidationRow("Height:")
        self.val_size = ValidationRow("File Size:")
        self.val_format = ValidationRow("Format:")
        self.val_dpi = ValidationRow("DPI:")
        for row in (self.val_width, self.val_height, self.val_size, self.val_format, self.val_dpi):
            val_layout.addWidget(row)

        self.overall_label = QLabel("Load an image to validate.")
        self.overall_label.setObjectName("sectionTitle")
        self.overall_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val_layout.addWidget(self.overall_label)

        right.addWidget(val_box)

        preview_row = QHBoxLayout()
        self.before_preview = ImagePreview("Original")
        self.after_preview = ImagePreview("Processed (Preview)")
        preview_row.addWidget(self.before_preview)
        preview_row.addWidget(self.after_preview)
        right.addLayout(preview_row)

        right.addStretch()

        root.addLayout(left, stretch=1)
        root.addLayout(right, stretch=2)

    def _current_preset(self) -> Optional[ExamPreset]:
        key = self.combo_exam.currentData()
        return EXAM_PRESETS.get(key)

    def _current_requirement(self) -> Optional[PhotoRequirement]:
        preset = self._current_preset()
        if preset is None:
            return None
        if self.combo_type.currentText() == "Photo":
            return preset.photo
        return preset.signature

    def _on_preset_changed(self) -> None:
        key = self.combo_exam.currentData()
        if key:
            settings.last_preset = key
        req = self._current_requirement()
        if req:
            min_txt = f"{req.min_size_kb} KB" if req.min_size_kb else "—"
            max_txt = f"{req.max_size_kb} KB" if req.max_size_kb else "—"
            self.req_label.setText(
                f"Width: {req.width_px} px\n"
                f"Height: {req.height_px} px\n"
                f"Min size: {min_txt}\n"
                f"Max size: {max_txt}\n"
                f"Format: {req.format}\n"
                f"Notes: {req.notes or 'None'}"
            )
        if self._current_path:
            self._validate_current()

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", settings.last_output_dir,
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
            self.before_preview.set_image(img)
            self._validate_current()
        except Exception as exc:
            QMessageBox.warning(self, "Error", f"Could not open image:\n{exc}")

    def _validate_current(self) -> None:
        if not self._current_path:
            return
        req = self._current_requirement()
        if req is None:
            return

        result = ImageProcessor.validate(
            self._current_path,
            req.width_px,
            req.height_px,
            req.min_size_kb,
            req.max_size_kb,
        )

        self.val_width.set(
            f"{result['actual_width']} px  (need {req.width_px})", result["width_ok"]
        )
        self.val_height.set(
            f"{result['actual_height']} px  (need {req.height_px})", result["height_ok"]
        )
        size_txt = f"{result['actual_size_kb']:.1f} KB"
        if req.min_size_kb and req.max_size_kb:
            size_txt += f"  (need {req.min_size_kb}–{req.max_size_kb} KB)"
        elif req.max_size_kb:
            size_txt += f"  (max {req.max_size_kb} KB)"
        self.val_size.set(size_txt, result["size_ok"])
        self.val_format.set(result["format"])
        self.val_dpi.set(f"{result['dpi']} DPI")

        if result["all_ok"]:
            self.overall_label.setText("ELIGIBLE ✓ — Image meets all requirements")
            self.overall_label.setStyleSheet("color: #2ecc71; font-weight: bold;")
        else:
            self.overall_label.setText("NOT ELIGIBLE ✗ — Use 'Make Eligible' to fix")
            self.overall_label.setStyleSheet("color: #e74c3c; font-weight: bold;")

    def _make_eligible(self) -> None:
        if self._current_img is None:
            QMessageBox.information(self, "No Image", "Please load an image first.")
            return

        req = self._current_requirement()
        if req is None:
            return

        try:
            processed = ImageProcessor.resize_by_pixels(
                self._current_img.copy(),
                req.width_px,
                req.height_px,
                crop_to_fit=True,
            )
            self.after_preview.set_image(
                processed, f"{req.width_px} × {req.height_px} px"
            )

            # Ask to save
            out_path, _ = QFileDialog.getSaveFileName(
                self, "Save Processed Image",
                os.path.join(settings.last_output_dir, "eligible.jpg"),
                "JPEG (*.jpg);;PNG (*.png)"
            )
            if not out_path:
                return

            if req.max_size_kb:
                data = ImageProcessor.compress_to_size(processed, req.max_size_kb, "JPEG")
                ImageProcessor.save_bytes(data, out_path)
                final_kb = len(data) / 1024
            else:
                ImageProcessor.save_image(processed, out_path)
                final_kb = os.path.getsize(out_path) / 1024

            settings.last_output_dir = os.path.dirname(out_path)

            # Re-validate saved file
            result = ImageProcessor.validate(
                out_path, req.width_px, req.height_px, req.min_size_kb, req.max_size_kb
            )
            status = "ELIGIBLE ✓" if result["all_ok"] else "Check manually"
            QMessageBox.information(
                self, "Done",
                f"Saved as: {out_path}\n"
                f"Final size: {final_kb:.1f} KB | {req.width_px}×{req.height_px} px\n"
                f"Status: {status}"
            )
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Processing failed:\n{exc}")
