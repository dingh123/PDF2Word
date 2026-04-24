"""Background worker that converts PDFs on a QThread."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import QThread, pyqtSignal

from converter.pdf_converter import (
    ConversionCancelled,
    PDFConverter,
    default_output_path,
)


class ConversionWorker(QThread):
    """Convert a list of PDFs; emit per-file and per-page progress."""

    # (file_index, total_files, file_name)
    file_started = pyqtSignal(int, int, str)
    # (file_index, pages_done, total_pages)
    file_progress = pyqtSignal(int, int, int)
    # (file_index, output_path)
    file_finished = pyqtSignal(int, str)
    # (file_index, error_message)
    file_failed = pyqtSignal(int, str)
    # (ok_count, fail_count, cancelled)
    all_finished = pyqtSignal(int, int, bool)

    def __init__(
        self,
        pdf_paths: List[Path],
        output_dir: Optional[Path],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._pdf_paths = pdf_paths
        self._output_dir = output_dir
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        converter = PDFConverter(cancel_check=lambda: self._cancel)
        total_files = len(self._pdf_paths)
        ok_count = 0
        fail_count = 0

        for idx, pdf_path in enumerate(self._pdf_paths):
            if self._cancel:
                break

            self.file_started.emit(idx, total_files, pdf_path.name)
            docx_path = default_output_path(pdf_path, self._output_dir)

            def on_progress(done: int, total: int, _idx: int = idx) -> None:
                self.file_progress.emit(_idx, done, total)

            try:
                converter.convert(pdf_path, docx_path, progress=on_progress)
                self.file_finished.emit(idx, str(docx_path))
                ok_count += 1
            except ConversionCancelled:
                break
            except Exception as exc:  # noqa: BLE001 — surface any error to the UI
                self.file_failed.emit(idx, str(exc))
                fail_count += 1

        self.all_finished.emit(ok_count, fail_count, self._cancel)
