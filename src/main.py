"""Entry point for the PDF-to-Word GUI."""
from __future__ import annotations

import sys
from pathlib import Path

# Make `converter` and `gui` importable whether we run from source
# (python src/main.py) or from a PyInstaller bundle.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from PyQt6.QtWidgets import QApplication  # noqa: E402

from gui.main_window import MainWindow  # noqa: E402


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("PDF to Word")
    app.setOrganizationName("PDF to Word")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
