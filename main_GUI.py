import sys
import os
from PyQt6.QtWidgets import QApplication

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ui.ui import ADBFastbootUI

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ADBFastbootUI()
    window.show()
    sys.exit(app.exec())
