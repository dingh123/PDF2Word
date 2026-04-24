"""PDF to Word conversion using pdf2docx."""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from pdf2docx import Converter


ProgressCallback = Callable[[int, int], None]
"""Callback signature: (pages_done, total_pages)."""


class ConversionCancelled(Exception):
    """Raised when the user cancels an in-progress conversion."""


class PDFConverter:
    """Convert a PDF file to a Word .docx file, preserving layout, tables, and images."""

    def __init__(self, cancel_check: Optional[Callable[[], bool]] = None) -> None:
        self._cancel_check = cancel_check or (lambda: False)

    def convert(
        self,
        pdf_path: str | Path,
        docx_path: str | Path,
        progress: Optional[ProgressCallback] = None,
    ) -> None:
        pdf_path = Path(pdf_path)
        docx_path = Path(docx_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        docx_path.parent.mkdir(parents=True, exist_ok=True)

        cv = Converter(str(pdf_path))
        try:
            total = len(cv.fitz_doc)
            if progress:
                progress(0, total)

            # pdf2docx needs its full settings dict (keys like 'ocr', 'debug',
            # 'ignore_page_error', ...) in every pipeline step, so start from
            # default_settings and force single-process mode (nested processes
            # inside QThread misbehave on macOS/Windows).
            settings = dict(cv.default_settings)
            settings["multi_processing"] = False

            # Drive the pipeline manually so we can report per-page progress
            # and honor cancellation. If the internal API ever changes, fall
            # back to a single convert() call with coarse progress.
            try:
                cv.load_pages(0, total, None).parse_document(**settings)
                for i, page in enumerate(cv.pages, start=1):
                    if self._cancel_check():
                        raise ConversionCancelled()
                    if not getattr(page, "skip_parsing", False):
                        page.parse(**settings)
                    if progress:
                        progress(i, total)
                cv.make_docx(str(docx_path), **settings)
            except ConversionCancelled:
                raise
            except AttributeError:
                cv.convert(str(docx_path), start=0, end=total, multi_processing=False)
                if progress:
                    progress(total, total)
        finally:
            cv.close()


def default_output_path(pdf_path: str | Path, output_dir: Optional[str | Path] = None) -> Path:
    pdf_path = Path(pdf_path)
    out_dir = Path(output_dir) if output_dir else pdf_path.parent
    return out_dir / (pdf_path.stem + ".docx")
