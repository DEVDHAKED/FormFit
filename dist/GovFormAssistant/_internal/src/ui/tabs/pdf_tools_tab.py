import os
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.config.settings import settings
from src.core.pdf_processor import PDFProcessor
from src.utils.helpers import is_pdf_file, is_image_file


class _Worker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self):
        try:
            result = self._fn(*self._args, **self._kwargs)
            self.finished.emit(str(result) if result else "Done")
        except Exception as exc:
            self.error.emit(str(exc))


class PDFToolsTab(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._workers: List[_Worker] = []
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        title = QLabel("PDF Tools")
        title.setObjectName("sectionTitle")
        root.addWidget(title)

        self.sub_tabs = QTabWidget()
        self.sub_tabs.addTab(self._build_merge_tab(), "Merge PDFs")
        self.sub_tabs.addTab(self._build_split_tab(), "Split PDF")
        self.sub_tabs.addTab(self._build_compress_tab(), "Compress PDF")
        self.sub_tabs.addTab(self._build_to_images_tab(), "PDF → Images")
        self.sub_tabs.addTab(self._build_to_pdf_tab(), "Images → PDF")

        root.addWidget(self.sub_tabs)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        root.addWidget(self.progress_bar)

        self.status_label = QLabel()
        self.status_label.setObjectName("resultLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.status_label)

    # ------------------------------------------------------------------ #
    # Merge PDFs
    # ------------------------------------------------------------------ #

    def _build_merge_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(8)

        layout.addWidget(QLabel("Add PDF files to merge (order matters):"))

        self.merge_list = QListWidget()
        layout.addWidget(self.merge_list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add PDFs...")
        add_btn.clicked.connect(self._merge_add_files)
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(lambda: self._remove_selected(self.merge_list))
        up_btn = QPushButton("↑ Up")
        up_btn.clicked.connect(lambda: self._move_item(self.merge_list, -1))
        down_btn = QPushButton("↓ Down")
        down_btn.clicked.connect(lambda: self._move_item(self.merge_list, 1))
        for b in (add_btn, remove_btn, up_btn, down_btn):
            btn_row.addWidget(b)
        layout.addLayout(btn_row)

        merge_btn = QPushButton("Merge All PDFs")
        merge_btn.setObjectName("primaryButton")
        merge_btn.clicked.connect(self._do_merge)
        layout.addWidget(merge_btn)

        return w

    def _merge_add_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Add PDFs", settings.last_output_dir, "PDF Files (*.pdf)"
        )
        for p in paths:
            self.merge_list.addItem(QListWidgetItem(p))

    def _do_merge(self) -> None:
        paths = [self.merge_list.item(i).text() for i in range(self.merge_list.count())]
        if len(paths) < 2:
            QMessageBox.warning(self, "Error", "Add at least 2 PDF files to merge.")
            return

        out, _ = QFileDialog.getSaveFileName(
            self, "Save Merged PDF", os.path.join(settings.last_output_dir, "merged.pdf"), "PDF (*.pdf)"
        )
        if not out:
            return

        self._run_worker(
            PDFProcessor.merge, [paths, out],
            success_msg=lambda r: f"Merged {len(paths)} files → {out}"
        )

    # ------------------------------------------------------------------ #
    # Split PDF
    # ------------------------------------------------------------------ #

    def _build_split_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(8)

        self.split_path_label = QLabel("No PDF loaded.")
        layout.addWidget(self.split_path_label)

        open_btn = QPushButton("Open PDF to Split...")
        open_btn.clicked.connect(self._split_open)
        layout.addWidget(open_btn)

        layout.addWidget(QLabel("Pages per output file:"))
        self.spin_pages = QSpinBox()
        self.spin_pages.setRange(1, 9999)
        self.spin_pages.setValue(1)
        layout.addWidget(self.spin_pages)

        split_btn = QPushButton("Split PDF")
        split_btn.setObjectName("primaryButton")
        split_btn.clicked.connect(self._do_split)
        layout.addWidget(split_btn)

        layout.addStretch()
        self._split_pdf_path: str = ""
        return w

    def _split_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF", settings.last_output_dir, "PDF (*.pdf)"
        )
        if path:
            self._split_pdf_path = path
            try:
                n = PDFProcessor.get_page_count(path)
                self.split_path_label.setText(
                    f"{os.path.basename(path)}  ({n} pages)"
                )
            except Exception as e:
                self.split_path_label.setText(f"Error reading PDF: {e}")

    def _do_split(self) -> None:
        if not self._split_pdf_path:
            QMessageBox.warning(self, "Error", "Open a PDF first.")
            return
        out_dir = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", settings.last_output_dir
        )
        if not out_dir:
            return

        ppf = self.spin_pages.value()
        self._run_worker(
            PDFProcessor.split_by_pages, [self._split_pdf_path, out_dir, ppf],
            success_msg=lambda r: f"Split complete → {out_dir}"
        )

    # ------------------------------------------------------------------ #
    # Compress
    # ------------------------------------------------------------------ #

    def _build_compress_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(8)

        self.compress_path_label = QLabel("No PDF loaded.")
        layout.addWidget(self.compress_path_label)

        open_btn = QPushButton("Open PDF to Compress...")
        open_btn.clicked.connect(self._compress_open)
        layout.addWidget(open_btn)

        comp_btn = QPushButton("Compress PDF")
        comp_btn.setObjectName("primaryButton")
        comp_btn.clicked.connect(self._do_compress)
        layout.addWidget(comp_btn)

        layout.addStretch()
        self._compress_pdf_path: str = ""
        return w

    def _compress_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF", settings.last_output_dir, "PDF (*.pdf)"
        )
        if path:
            self._compress_pdf_path = path
            sz = os.path.getsize(path) / 1024
            self.compress_path_label.setText(
                f"{os.path.basename(path)}  ({sz:.1f} KB)"
            )

    def _do_compress(self) -> None:
        if not self._compress_pdf_path:
            QMessageBox.warning(self, "Error", "Open a PDF first.")
            return
        stem = Path(self._compress_pdf_path).stem
        out, _ = QFileDialog.getSaveFileName(
            self, "Save Compressed PDF",
            os.path.join(settings.last_output_dir, f"{stem}_compressed.pdf"),
            "PDF (*.pdf)"
        )
        if not out:
            return

        self._run_worker(
            PDFProcessor.compress, [self._compress_pdf_path, out],
            success_msg=lambda r: (
                f"Compressed!\nOriginal: {os.path.getsize(self._compress_pdf_path)/1024:.1f} KB\n"
                f"Output: {os.path.getsize(out)/1024:.1f} KB"
            )
        )

    # ------------------------------------------------------------------ #
    # PDF → Images
    # ------------------------------------------------------------------ #

    def _build_to_images_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(8)

        self.to_img_path_label = QLabel("No PDF loaded.")
        layout.addWidget(self.to_img_path_label)

        open_btn = QPushButton("Open PDF...")
        open_btn.clicked.connect(self._to_img_open)
        layout.addWidget(open_btn)

        row = QHBoxLayout()
        row.addWidget(QLabel("DPI:"))
        self.spin_dpi = QSpinBox()
        self.spin_dpi.setRange(72, 600)
        self.spin_dpi.setValue(150)
        row.addWidget(self.spin_dpi)
        row.addWidget(QLabel("Format:"))
        self.combo_img_fmt = QComboBox()
        self.combo_img_fmt.addItems(["jpg", "png"])
        row.addWidget(self.combo_img_fmt)
        layout.addLayout(row)

        conv_btn = QPushButton("Convert to Images")
        conv_btn.setObjectName("primaryButton")
        conv_btn.clicked.connect(self._do_to_images)
        layout.addWidget(conv_btn)

        layout.addStretch()
        self._to_img_pdf_path: str = ""
        return w

    def _to_img_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF", settings.last_output_dir, "PDF (*.pdf)"
        )
        if path:
            self._to_img_pdf_path = path
            self.to_img_path_label.setText(os.path.basename(path))

    def _do_to_images(self) -> None:
        if not self._to_img_pdf_path:
            QMessageBox.warning(self, "Error", "Open a PDF first.")
            return
        out_dir = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", settings.last_output_dir
        )
        if not out_dir:
            return

        dpi = self.spin_dpi.value()
        fmt = self.combo_img_fmt.currentText()
        self._run_worker(
            PDFProcessor.to_images,
            [self._to_img_pdf_path, out_dir, dpi, fmt],
            success_msg=lambda r: f"Conversion complete → {out_dir}"
        )

    # ------------------------------------------------------------------ #
    # Images → PDF
    # ------------------------------------------------------------------ #

    def _build_to_pdf_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(8)

        layout.addWidget(QLabel("Add images to combine into a PDF:"))

        self.img_list = QListWidget()
        layout.addWidget(self.img_list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add Images...")
        add_btn.clicked.connect(self._img_add_files)
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(lambda: self._remove_selected(self.img_list))
        up_btn = QPushButton("↑ Up")
        up_btn.clicked.connect(lambda: self._move_item(self.img_list, -1))
        down_btn = QPushButton("↓ Down")
        down_btn.clicked.connect(lambda: self._move_item(self.img_list, 1))
        for b in (add_btn, remove_btn, up_btn, down_btn):
            btn_row.addWidget(b)
        layout.addLayout(btn_row)

        conv_btn = QPushButton("Create PDF")
        conv_btn.setObjectName("primaryButton")
        conv_btn.clicked.connect(self._do_to_pdf)
        layout.addWidget(conv_btn)

        return w

    def _img_add_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Add Images", settings.last_output_dir,
            "Images (*.jpg *.jpeg *.png *.bmp)"
        )
        for p in paths:
            self.img_list.addItem(QListWidgetItem(p))

    def _do_to_pdf(self) -> None:
        paths = [self.img_list.item(i).text() for i in range(self.img_list.count())]
        if not paths:
            QMessageBox.warning(self, "Error", "Add at least one image.")
            return
        out, _ = QFileDialog.getSaveFileName(
            self, "Save PDF", os.path.join(settings.last_output_dir, "output.pdf"), "PDF (*.pdf)"
        )
        if not out:
            return

        self._run_worker(
            PDFProcessor.images_to_pdf, [paths, out],
            success_msg=lambda r: f"PDF created → {out}"
        )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _remove_selected(self, lst: QListWidget) -> None:
        for item in lst.selectedItems():
            lst.takeItem(lst.row(item))

    def _move_item(self, lst: QListWidget, direction: int) -> None:
        row = lst.currentRow()
        new_row = row + direction
        if 0 <= new_row < lst.count():
            item = lst.takeItem(row)
            lst.insertItem(new_row, item)
            lst.setCurrentRow(new_row)

    def _run_worker(self, fn, args: list, success_msg=None) -> None:
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("Processing...")

        worker = _Worker(fn, *args)
        worker.finished.connect(lambda r: self._on_done(r, success_msg))
        worker.error.connect(self._on_error)
        self._workers.append(worker)
        worker.start()

    def _on_done(self, result: str, success_msg) -> None:
        self.progress_bar.setVisible(False)
        msg = success_msg(result) if callable(success_msg) else f"Done: {result}"
        self.status_label.setText(msg)
        QMessageBox.information(self, "Success", msg)

    def _on_error(self, error: str) -> None:
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Error: {error}")
        QMessageBox.critical(self, "Error", f"Operation failed:\n{error}")
