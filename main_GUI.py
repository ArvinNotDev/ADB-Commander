"""PyQt6 entry point for ADB Commander."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from ui.ui import ADBFastbootUI


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ADBFastbootUI()
    window.show()
    sys.exit(app.exec())
