from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QFileDialog, QLabel, QProgressBar, QInputDialog
from PyQt6.QtCore import Qt, QTimer
import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from functions import get_permission, storage_status, battery_status, is_there_any_sd, is_device_rooted, reboot_device_to_bootloader, install_apk, list_installed_apps, uninstall_app, capture_screenshot, record_screen, reboot_device_to_recovery

class ADBFastbootUI(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("ADB Fastboot Tool")
        self.setGeometry(200, 200, 600, 500)

        layout = QVBoxLayout()

        self.output_box = QTextEdit(self)
        self.output_box.setReadOnly(True)
        layout.addWidget(self.output_box)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        buttons = {
            "Check Device Connection": self._get_permission,
            "Check Storage Status": self._storage_status,
            "Check Battery Status": self._battery_status,
            "Check SD Card": self._is_there_any_sd,
            "Check Root Status": self._is_device_rooted,
            "Reboot to Bootloader": self._reboot_device_to_bootloader,
            "Install APK": self._install_apk,
            "List Installed Apps": self._list_installed_apps,
            "Uninstall App": self._uninstall_app,
            "Capture Screenshot": self._capture_screenshot,
            "Record Screen": self._record_screen,
            "Reboot to Recovery": self._reboot_device_to_recovery
        }

        for label, function in buttons.items():
            btn = QPushButton(label, self)
            btn.clicked.connect(function)
            layout.addWidget(btn)

        self.setLayout(layout)

    def _show_progress(self, show: bool):
        """Show or hide the progress bar."""
        if show:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
        else:
            self.progress_bar.setValue(100)
            self.progress_bar.setVisible(False)

    def _delay(self, seconds: int):
        """Introduce a delay before proceeding."""
        for i in range(101):
            self.progress_bar.setValue(i)
            time.sleep(seconds / 100)

    def _get_permission(self):
        self._show_progress(True)
        self._delay(1)
        result = get_permission()
        self.output_box.setText("Device connected." if result else "No devices connected.")
        self._show_progress(False)

    def _is_there_any_sd(self):
        if not get_permission():
            self.output_box.setText("No device connected.")
            return
        self._show_progress(True)
        self._delay(1)
        result = is_there_any_sd()
        self.output_box.setText("SD card found!" if result else "No SD card detected.")
        self._show_progress(False)

    def _storage_status(self):
        self._show_progress(True)
        self._delay(1)
        result = storage_status()
        self.output_box.setText(result)
        self._show_progress(False)

    def _battery_status(self):
        self._show_progress(True)
        self._delay(1)
        result = battery_status()
        self.output_box.setText(result)
        self._show_progress(False)

    def _is_device_rooted(self):
        self._show_progress(True)
        self._delay(1)
        result = is_device_rooted()
        self.output_box.setText("Device is rooted." if result else "Device is not rooted.")
        self._show_progress(False)

    def _reboot_device_to_bootloader(self):
        self._show_progress(True)
        self._delay(1)
        reboot_device_to_bootloader()
        self.output_box.setText("Rebooting to bootloader...")
        self._show_progress(False)

    def _install_apk(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select APK File", "", "APK Files (*.apk)")
        if file_path:
            self._show_progress(True)
            self._delay(1)

            try:
                result = install_apk(file_path)
                
                if result:
                    self.output_box.setText(f"Installation Successful: {result}")
                else:
                    self.output_box.setText("APK installation failed. Please try again.")
            
            except Exception as e:
                self.output_box.setText(f"An error occurred: {str(e)}")
            
            finally:
                self._show_progress(False)


    def _list_installed_apps(self):
        self._show_progress(True)
        self._delay(1)
        apps = list_installed_apps()
        self.output_box.setText(apps)
        self._show_progress(False)

    def _uninstall_app(self):
        app_name, _ = QInputDialog.getText(self, "Enter Package Name", "Package Name:")
        if app_name:
            self._show_progress(True)
            self._delay(1)
            result = uninstall_app(app_name)
            self.output_box.setText(result)
            self._show_progress(False)

    def _capture_screenshot(self):
        output_file, _ = QFileDialog.getSaveFileName(self, "Save Screenshot", "", "PNG Files (*.png)")
        if output_file:
            self._show_progress(True)
            self._delay(1)
            result = capture_screenshot(output_file)
            self.output_box.setText(result)
            self._show_progress(False)

    def _record_screen(self):
        output_file, _ = QFileDialog.getSaveFileName(self, "Save Screen Recording", "", "MP4 Files (*.mp4)")
        if output_file:
            duration, _ = QInputDialog.getInt(self, "Enter Duration", "Duration in seconds:", 10, 1, 3600)
            self._show_progress(True)
            self._delay(1)
            result = record_screen(output_file, duration)
            self.output_box.setText(result)
            self._show_progress(False)

    def _reboot_device_to_recovery(self):
        self._show_progress(True)
        self._delay(2)
        result = reboot_device_to_recovery()
        self.output_box.setText(result)
        self._show_progress(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ADBFastbootUI()
    window.show()
    sys.exit(app.exec())
