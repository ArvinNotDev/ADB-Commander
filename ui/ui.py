import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout,
    QPushButton, QTextEdit, QFileDialog, QProgressBar, QInputDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon

# Ensure parent directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from functions.adb_commands import ADBManager


class ADBFastbootUI(QWidget):
    def __init__(self):
        super().__init__()
        try:
            self.adb = ADBManager()
        except EnvironmentError as e:
            raise SystemExit(str(e))
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("ADB Fastboot Tool")
        self.setGeometry(200, 200, 800, 600)
        self.setStyleSheet("background-color: #1e1e1e; color: white; font-size: 14px;")

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Output box
        self.output_box = QTextEdit(self)
        self.output_box.setReadOnly(True)
        self.output_box.setStyleSheet("background-color: #2d2d2d; border-radius: 5px; padding: 5px;")
        main_layout.addWidget(self.output_box)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #555;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #05B8CC;
                width: 20px;
            }
        """)
        main_layout.addWidget(self.progress_bar)

        # Button grid
        button_layout = QGridLayout()
        main_layout.addLayout(button_layout)

        buttons = {
            "Check Device": self._get_permission,
            "Storage Status": self._storage_status,
            "Battery Status": self._battery_status,
            "SD Card": self._is_there_any_sd,
            "Root Status": self._is_device_rooted,
            "Reboot Bootloader": self._reboot_device_to_bootloader,
            "Reboot Recovery": self._reboot_device_to_recovery,
            "Install APK": self._install_apk,
            "List Apps": self._list_installed_apps,
            "Uninstall App": self._uninstall_app,
            "Screenshot": self._capture_screenshot,
            "Record Screen": self._record_screen
        }

        row, col = 0, 0
        for label, func in buttons.items():
            btn = QPushButton(label)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3a3a3a;
                    border-radius: 5px;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: #05B8CC;
                }
            """)
            btn.clicked.connect(func)
            button_layout.addWidget(btn, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1

    # ----------------- Utility -----------------
    def _show_progress(self, show: bool):
        self.progress_bar.setVisible(show)
        self.progress_bar.setValue(0 if show else 100)

    def _start_progress(self, duration=1000):
        """Non-blocking progress using QTimer"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.timer_value = 0
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: self._update_progress(duration))
        self.timer.start(10)

    def _update_progress(self, duration):
        self.timer_value += 1
        progress = min(int((self.timer_value / (duration / 10)) * 100), 100)
        self.progress_bar.setValue(progress)
        if progress >= 100:
            self.timer.stop()
            self.progress_bar.setVisible(False)

    def _display_output(self, text):
        self.output_box.append(text)
        self.output_box.verticalScrollBar().setValue(self.output_box.verticalScrollBar().maximum())

    # ----------------- ADB Functions -----------------
    def _get_permission(self):
        self._start_progress()
        result = self.adb.get_permission()
        self._display_output("Device connected." if result else "No devices connected.")

    def _is_there_any_sd(self):
        self._start_progress()
        result = self.adb.is_there_any_sd()
        self._display_output("SD card found!" if result else "No SD card detected.")

    def _storage_status(self):
        self._start_progress()
        result = self.adb.storage_status()
        self._display_output(result)

    def _battery_status(self):
        self._start_progress()
        result = self.adb.battery_status()
        self._display_output(result)

    def _is_device_rooted(self):
        self._start_progress()
        result = self.adb.is_device_rooted()
        self._display_output("Device is rooted." if result else "Device is not rooted.")

    def _reboot_device_to_bootloader(self):
        self._start_progress(2000)
        result = self.adb.reboot_device_to_bootloader()
        self._display_output(result)

    def _reboot_device_to_recovery(self):
        self._start_progress(2000)
        result = self.adb.reboot_device_to_recovery()
        self._display_output(result)

    def _install_apk(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select APK File", "", "APK Files (*.apk)")
        if file_path:
            self._start_progress(2000)
            result = self.adb.install_apk(file_path)
            self._display_output(f"Installation result:\n{result}")

    def _list_installed_apps(self):
        self._start_progress()
        result = self.adb.list_installed_apps()
        self._display_output(result)

    def _uninstall_app(self):
        pkg_name, _ = QInputDialog.getText(self, "Uninstall App", "Package Name:")
        if pkg_name:
            self._start_progress()
            result = self.adb.uninstall_app(pkg_name)
            self._display_output(result)

    def _capture_screenshot(self):
        output_file, _ = QFileDialog.getSaveFileName(self, "Save Screenshot", "", "PNG Files (*.png)")
        if output_file:
            self._start_progress()
            result = self.adb.capture_screenshot(output_file)
            self._display_output(result)

    def _record_screen(self):
        output_file, _ = QFileDialog.getSaveFileName(self, "Save Recording", "", "MP4 Files (*.mp4)")
        if output_file:
            duration, _ = QInputDialog.getInt(self, "Duration", "Seconds:", 10, 1, 3600)
            self._start_progress(duration*100)
            result = self.adb.record_screen(output_file, duration)
            self._display_output(result)
