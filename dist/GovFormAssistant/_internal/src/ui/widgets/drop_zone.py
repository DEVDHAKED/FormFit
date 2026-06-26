from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QLabel, QSizePolicy


class DropZone(QLabel):
    """A label that accepts drag-and-drop file drops and emits file paths."""

    files_dropped = Signal(list)  # List[str]

    def __init__(
        self,
        accepted_extensions: Optional[List[str]] = None,
        multiple: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._accepted = {ext.lower() for ext in (accepted_extensions or [])}
        self._multiple = multiple

        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setObjectName("dropZone")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumHeight(120)
        self._set_idle_text()

    def _set_idle_text(self) -> None:
        ext_hint = (
            ", ".join(e.upper().lstrip(".") for e in sorted(self._accepted))
            if self._accepted
            else "any file"
        )
        multi = "files" if self._multiple else "a file"
        self.setText(
            f"Drop {multi} here\n"
            f"or click Browse below\n"
            f"({ext_hint})"
        )

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            paths = [u.toLocalFile() for u in event.mimeData().urls()]
            if self._any_accepted(paths):
                event.acceptProposedAction()
                self.setProperty("dragOver", True)
                self.style().polish(self)
                return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self.setProperty("dragOver", False)
        self.style().polish(self)

    def dropEvent(self, event: QDropEvent) -> None:
        self.setProperty("dragOver", False)
        self.style().polish(self)

        paths = [u.toLocalFile() for u in event.mimeData().urls()]
        valid = [p for p in paths if self._is_accepted(p)]

        if not valid:
            return

        if not self._multiple:
            valid = [valid[0]]

        self.files_dropped.emit(valid)
        event.acceptProposedAction()

    def _is_accepted(self, path: str) -> bool:
        if not self._accepted:
            return True
        return Path(path).suffix.lower() in self._accepted

    def _any_accepted(self, paths: List[str]) -> bool:
        return any(self._is_accepted(p) for p in paths)
