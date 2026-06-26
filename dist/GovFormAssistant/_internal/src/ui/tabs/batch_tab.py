import os
from pathlib import Path
from typing import List, Optional

from PIL import Image
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.config.settings import settings
from src.core.image_processor import ImageProcessor
from src.utils.helpers import is_image_file, unique_output_path


class _BatchWorker(QThread):
    progress = Signal(int, int, str)  # current, total, filename
    finished = Signal(int, int)       # success_count, fail_count
    error = Signal(str)

    def __init__(self, paths: List[str], output_dir: str, operation: str, params: dict):
        super().__init__()
        self.paths = paths
        self.output_dir = output_dir
        self.operation = operation
        self.params = params

    def run(self) -> None:
        success = 0
        fail = 0
        total = len(self.paths)

        for i, path in enumerate(self.paths):
            filename = os.path.basename(path)
            self.progress.emit(i + 1, total, filename)
            try:
                img = ImageProcessor.open_image(path)
                out_path = unique_output_path(self.output_dir, filename, "_batch")

                if self.operation == "resize_px":
                    w = self.params["width"]
                    h = self.params["height"]
                    maintain = self.params.get("maintain_aspect", False)
                    crop = self.params.get("crop_to_fit", False)
                    result = ImageProcessor.resize_by_pixels(img, w, h, maintain, crop)
                    ImageProcessor.save_image(result, out_path)

                elif self.operation == "compress":
                    max_kb = self.params["max_kb"]
                    fmt = self.params.get("format", "JPEG")
                    data = ImageProcessor.compress_to_size(img, max_kb, fmt)
                    ext = ".jpg" if fmt.upper() in ("JPEG", "JPG") else ".png"
                    out_path = unique_output_path(
                        self.output_dir, Path(filename).stem + ext, "_batch"
                    )
                    ImageProcessor.save_bytes(data, out_path)

                elif self.operation == "convert":
                    target_ext = self.params["target_ext"]
                    converted = ImageProcessor.convert_format(img, target_ext)
                    out_path = unique_output_path(
                        self.output_dir, Path(filename).stem + target_ext, "_batch"
                    )
                    ImageProcessor.save_image(converted, out_path)

                success += 1
            except Exception:
                fail += 1

        self.finished.emit(success, fail)


class BatchTab(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._worker: Optional[_BatchWorker] = None
        self._build_ui()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        # Left: file list
        left = QVBoxLayout()
        left.setSpacing(10)

        left.addWidget(QLabel("Files to Process:"))
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        left.addWidget(self.file_list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add Files...")
        add_btn.clicked.connect(self._add_files)
        add_dir_btn = QPushButton("Add Folder...")
        add_dir_btn.clicked.connect(self._add_folder)
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._remove_selected)
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.file_list.clear)
        for b in (add_btn, add_dir_btn, remove_btn, clear_btn):
            btn_row.addWidget(b)
        left.addLayout(btn_row)

        self.file_count_label = QLabel("0 files")
        self.file_count_label.setObjectName("infoLabel")
        left.addWidget(self.file_count_label)

        # Right: operations
        right = QVBoxLayout()
        right.setSpacing(12)

        # Operation selector
        op_box = QGroupBox("Batch Operation")
        op_layout = QVBoxLayout(op_box)
        self.combo_op = QComboBox()
        self.combo_op.addItems(["Resize (pixels)", "Compress to size", "Convert format"])
        self.combo_op.currentIndexChanged.connect(self._toggle_op_panels)
        op_layout.addWidget(self.combo_op)
        right.addWidget(op_box)

        # Resize panel
        self.resize_panel = QGroupBox("Resize Settings")
        rp_layout = QVBoxLayout(self.resize_panel)
        row_w = QHBoxLayout()
        row_w.addWidget(QLabel("Width (px):"))
        self.spin_w = QSpinBox()
        self.spin_w.setRange(1, 99999)
        self.spin_w.setValue(200)
        row_w.addWidget(self.spin_w)
        rp_layout.addLayout(row_w)
        row_h = QHBoxLayout()
        row_h.addWidget(QLabel("Height (px):"))
        self.spin_h = QSpinBox()
        self.spin_h.setRange(1, 99999)
        self.spin_h.setValue(200)
        row_h.addWidget(self.spin_h)
        rp_layout.addLayout(row_h)
        self.chk_aspect = QCheckBox("Maintain aspect ratio")
        self.chk_crop = QCheckBox("Crop to fit")
        rp_layout.addWidget(self.chk_aspect)
        rp_layout.addWidget(self.chk_crop)
        right.addWidget(self.resize_panel)

        # Compress panel
        self.compress_panel = QGroupBox("Compression Settings")
        cp_layout = QVBoxLayout(self.compress_panel)
        row_kb = QHBoxLayout()
        row_kb.addWidget(QLabel("Max size (KB):"))
        self.spin_kb = QDoubleSpinBox()
        self.spin_kb.setRange(1, 100000)
        self.spin_kb.setValue(50)
        self.spin_kb.setSuffix(" KB")
        row_kb.addWidget(self.spin_kb)
        cp_layout.addLayout(row_kb)
        row_fmt = QHBoxLayout()
        row_fmt.addWidget(QLabel("Output format:"))
        self.combo_comp_fmt = QComboBox()
        self.combo_comp_fmt.addItems(["JPEG", "PNG"])
        row_fmt.addWidget(self.combo_comp_fmt)
        cp_layout.addLayout(row_fmt)
        right.addWidget(self.compress_panel)
        self.compress_panel.setVisible(False)

        # Convert panel
        self.convert_panel = QGroupBox("Conversion Settings")
        cv_layout = QVBoxLayout(self.convert_panel)
        row_cv = QHBoxLayout()
        row_cv.addWidget(QLabel("Convert to:"))
        self.combo_target_fmt = QComboBox()
        self.combo_target_fmt.addItems([".jpg", ".png", ".bmp"])
        row_cv.addWidget(self.combo_target_fmt)
        cv_layout.addLayout(row_cv)
        right.addWidget(self.convert_panel)
        self.convert_panel.setVisible(False)

        # Output folder
        out_box = QGroupBox("Output Folder")
        out_layout = QHBoxLayout(out_box)
        self.out_label = QLabel(settings.last_output_dir)
        self.out_label.setObjectName("infoLabel")
        self.out_label.setWordWrap(True)
        out_layout.addWidget(self.out_label, stretch=1)
        pick_btn = QPushButton("Browse...")
        pick_btn.clicked.connect(self._pick_output)
        out_layout.addWidget(pick_btn)
        right.addWidget(out_box)

        # Run button & progress
        self.run_btn = QPushButton("Start Batch Processing")
        self.run_btn.setObjectName("primaryButton")
        self.run_btn.clicked.connect(self._start_batch)
        right.addWidget(self.run_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right.addWidget(self.progress_bar)

        self.status_label = QLabel()
        self.status_label.setObjectName("resultLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right.addWidget(self.status_label)

        right.addStretch()

        root.addLayout(left, stretch=1)
        root.addLayout(right, stretch=1)

    def _add_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Add Images", settings.last_output_dir,
            "Images (*.jpg *.jpeg *.png *.bmp *.tiff *.webp)"
        )
        for p in paths:
            if is_image_file(p):
                self.file_list.addItem(QListWidgetItem(p))
        self._update_count()

    def _add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder", settings.last_output_dir
        )
        if not folder:
            return
        for f in Path(folder).iterdir():
            if is_image_file(str(f)):
                self.file_list.addItem(QListWidgetItem(str(f)))
        self._update_count()

    def _remove_selected(self) -> None:
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))
        self._update_count()

    def _update_count(self) -> None:
        n = self.file_list.count()
        self.file_count_label.setText(f"{n} file{'s' if n != 1 else ''}")

    def _pick_output(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", settings.last_output_dir
        )
        if folder:
            self.out_label.setText(folder)
            settings.last_output_dir = folder

    def _toggle_op_panels(self, idx: int) -> None:
        self.resize_panel.setVisible(idx == 0)
        self.compress_panel.setVisible(idx == 1)
        self.convert_panel.setVisible(idx == 2)

    def _start_batch(self) -> None:
        paths = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        if not paths:
            QMessageBox.information(self, "No Files", "Add images before processing.")
            return

        output_dir = self.out_label.text()
        if not output_dir or not os.path.exists(output_dir):
            QMessageBox.warning(self, "Error", "Select a valid output folder.")
            return

        op_idx = self.combo_op.currentIndex()
        if op_idx == 0:
            operation = "resize_px"
            params = {
                "width": self.spin_w.value(),
                "height": self.spin_h.value(),
                "maintain_aspect": self.chk_aspect.isChecked(),
                "crop_to_fit": self.chk_crop.isChecked(),
            }
        elif op_idx == 1:
            operation = "compress"
            params = {
                "max_kb": self.spin_kb.value(),
                "format": self.combo_comp_fmt.currentText(),
            }
        else:
            operation = "convert"
            params = {"target_ext": self.combo_target_fmt.currentText()}

        self.run_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(paths))
        self.progress_bar.setValue(0)

        self._worker = _BatchWorker(paths, output_dir, operation, params)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, current: int, total: int, filename: str) -> None:
        self.progress_bar.setValue(current)
        self.status_label.setText(f"Processing {current}/{total}: {filename}")

    def _on_finished(self, success: int, fail: int) -> None:
        self.progress_bar.setVisible(False)
        self.run_btn.setEnabled(True)
        msg = f"Batch complete!\n✓ {success} succeeded  ✗ {fail} failed"
        self.status_label.setText(msg)
        QMessageBox.information(self, "Done", msg)

    def _on_error(self, error: str) -> None:
        self.progress_bar.setVisible(False)
        self.run_btn.setEnabled(True)
        QMessageBox.critical(self, "Batch Error", error)
