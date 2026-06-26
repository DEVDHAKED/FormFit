from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.core.converters import (
    aspect_ratio,
    bytes_to_kb,
    cm_to_px,
    inch_to_px,
    kb_to_mb,
    mb_to_kb,
    mm_to_px,
    px_to_cm,
    px_to_inch,
    px_to_mm,
)


class ConverterTab(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        col1 = QVBoxLayout()
        col1.setSpacing(16)
        col2 = QVBoxLayout()
        col2.setSpacing(16)

        # -- Pixel ↔ cm / mm / inch --
        px_box = QGroupBox("Pixels ↔ cm / mm / inch")
        px_layout = QVBoxLayout(px_box)

        dpi_row = QHBoxLayout()
        dpi_row.addWidget(QLabel("DPI:"))
        self.spin_dpi = QSpinBox()
        self.spin_dpi.setRange(72, 600)
        self.spin_dpi.setValue(96)
        dpi_row.addWidget(self.spin_dpi)
        px_layout.addLayout(dpi_row)

        form = QFormLayout()

        self.px_input = QDoubleSpinBox()
        self.px_input.setRange(0, 99999)
        self.px_input.setDecimals(2)
        form.addRow("Pixels:", self.px_input)

        self.cm_result = QLabel("-")
        form.addRow("→ cm:", self.cm_result)
        self.mm_result = QLabel("-")
        form.addRow("→ mm:", self.mm_result)
        self.inch_result = QLabel("-")
        form.addRow("→ inch:", self.inch_result)
        px_layout.addLayout(form)

        btn_px2unit = QPushButton("Convert px → cm / mm / inch")
        btn_px2unit.clicked.connect(self._convert_px_to_units)
        px_layout.addWidget(btn_px2unit)

        form2 = QFormLayout()
        self.cm_input = QDoubleSpinBox()
        self.cm_input.setRange(0, 9999)
        self.cm_input.setDecimals(4)
        form2.addRow("cm:", self.cm_input)
        self.mm_input = QDoubleSpinBox()
        self.mm_input.setRange(0, 9999)
        self.mm_input.setDecimals(4)
        form2.addRow("mm:", self.mm_input)
        self.inch_input = QDoubleSpinBox()
        self.inch_input.setRange(0, 9999)
        self.inch_input.setDecimals(4)
        form2.addRow("inch:", self.inch_input)
        self.unit_to_px_result = QLabel("-")
        form2.addRow("→ Pixels:", self.unit_to_px_result)
        px_layout.addLayout(form2)

        btn_unit2px = QPushButton("Convert cm / mm / inch → px")
        btn_unit2px.clicked.connect(self._convert_units_to_px)
        px_layout.addWidget(btn_unit2px)

        col1.addWidget(px_box)

        # -- KB ↔ MB --
        kb_box = QGroupBox("KB ↔ MB")
        kb_layout = QVBoxLayout(kb_box)
        form3 = QFormLayout()

        self.kb_input = QDoubleSpinBox()
        self.kb_input.setRange(0, 99999999)
        self.kb_input.setDecimals(2)
        form3.addRow("KB:", self.kb_input)
        self.mb_from_kb = QLabel("-")
        form3.addRow("→ MB:", self.mb_from_kb)

        self.mb_input = QDoubleSpinBox()
        self.mb_input.setRange(0, 99999)
        self.mb_input.setDecimals(4)
        form3.addRow("MB:", self.mb_input)
        self.kb_from_mb = QLabel("-")
        form3.addRow("→ KB:", self.kb_from_mb)

        kb_layout.addLayout(form3)

        btn_kb = QPushButton("Convert")
        btn_kb.clicked.connect(self._convert_kb_mb)
        kb_layout.addWidget(btn_kb)
        col1.addWidget(kb_box)

        col1.addStretch()

        # -- Aspect Ratio --
        ar_box = QGroupBox("Aspect Ratio Calculator")
        ar_layout = QVBoxLayout(ar_box)
        form4 = QFormLayout()

        self.ar_w = QSpinBox()
        self.ar_w.setRange(1, 99999)
        self.ar_w.setValue(1920)
        form4.addRow("Width (px):", self.ar_w)

        self.ar_h = QSpinBox()
        self.ar_h.setRange(1, 99999)
        self.ar_h.setValue(1080)
        form4.addRow("Height (px):", self.ar_h)

        self.ar_result = QLabel("-")
        self.ar_result.setObjectName("resultLabel")
        form4.addRow("Aspect Ratio:", self.ar_result)

        ar_layout.addLayout(form4)
        btn_ar = QPushButton("Calculate Aspect Ratio")
        btn_ar.clicked.connect(self._calc_aspect)
        ar_layout.addWidget(btn_ar)
        col2.addWidget(ar_box)

        # -- DPI Calculator --
        dpi_box = QGroupBox("DPI Calculator")
        dpi_layout = QVBoxLayout(dpi_box)
        dpi_layout.addWidget(QLabel("Find required DPI for print size:"))
        form5 = QFormLayout()

        self.dpi_px_w = QSpinBox()
        self.dpi_px_w.setRange(1, 99999)
        self.dpi_px_w.setValue(600)
        form5.addRow("Image width (px):", self.dpi_px_w)

        self.dpi_print_w_cm = QDoubleSpinBox()
        self.dpi_print_w_cm.setRange(0.1, 9999)
        self.dpi_print_w_cm.setValue(5.0)
        self.dpi_print_w_cm.setSuffix(" cm")
        form5.addRow("Print width:", self.dpi_print_w_cm)

        self.dpi_calc_result = QLabel("-")
        self.dpi_calc_result.setObjectName("resultLabel")
        form5.addRow("Required DPI:", self.dpi_calc_result)

        dpi_layout.addLayout(form5)
        btn_dpi = QPushButton("Calculate DPI")
        btn_dpi.clicked.connect(self._calc_dpi)
        dpi_layout.addWidget(btn_dpi)
        col2.addWidget(dpi_box)

        # -- Passport photo helper --
        pp_box = QGroupBox("Passport Photo Dimensions")
        pp_layout = QVBoxLayout(pp_box)
        pp_layout.addWidget(QLabel("Common standard sizes (at 96 DPI):"))

        standards = [
            ("India Passport (35×45 mm)", 35, 45),
            ("US Passport (51×51 mm)", 51, 51),
            ("UK Passport (35×45 mm)", 35, 45),
            ("3.5×4.5 cm", 35, 45),
            ("2×2 inch (US)", 51, 51),
        ]
        for name, w_mm, h_mm in standards:
            px_w = int(mm_to_px(w_mm, 96))
            px_h = int(mm_to_px(h_mm, 96))
            label = QLabel(f"{name}  →  {px_w} × {px_h} px")
            label.setObjectName("infoLabel")
            pp_layout.addWidget(label)

        col2.addWidget(pp_box)
        col2.addStretch()

        root.addLayout(col1, stretch=1)
        root.addLayout(col2, stretch=1)

    def _convert_px_to_units(self) -> None:
        px = self.px_input.value()
        dpi = self.spin_dpi.value()
        self.cm_result.setText(f"{px_to_cm(px, dpi):.4f} cm")
        self.mm_result.setText(f"{px_to_mm(px, dpi):.4f} mm")
        self.inch_result.setText(f"{px_to_inch(px, dpi):.4f} inch")

    def _convert_units_to_px(self) -> None:
        dpi = self.spin_dpi.value()
        cm = self.cm_input.value()
        mm = self.mm_input.value()
        inch = self.inch_input.value()
        # Use cm if non-zero, else mm, else inch
        if cm > 0:
            result = cm_to_px(cm, dpi)
            src = f"{cm} cm"
        elif mm > 0:
            result = mm_to_px(mm, dpi)
            src = f"{mm} mm"
        else:
            result = inch_to_px(inch, dpi)
            src = f"{inch} inch"
        self.unit_to_px_result.setText(f"{result:.2f} px  (from {src} at {dpi} DPI)")

    def _convert_kb_mb(self) -> None:
        kb = self.kb_input.value()
        mb = self.mb_input.value()
        self.mb_from_kb.setText(f"{kb_to_mb(kb):.4f} MB")
        self.kb_from_mb.setText(f"{mb_to_kb(mb):.2f} KB")

    def _calc_aspect(self) -> None:
        w = self.ar_w.value()
        h = self.ar_h.value()
        r_w, r_h = aspect_ratio(w, h)
        self.ar_result.setText(f"{r_w} : {r_h}")

    def _calc_dpi(self) -> None:
        px_w = self.dpi_px_w.value()
        print_cm = self.dpi_print_w_cm.value()
        if print_cm <= 0:
            self.dpi_calc_result.setText("Invalid print size")
            return
        inch_w = print_cm / 2.54
        dpi = px_w / inch_w
        self.dpi_calc_result.setText(f"{dpi:.1f} DPI")
