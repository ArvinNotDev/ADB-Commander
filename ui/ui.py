"""PyQt6 graphical interface for ADB Commander."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, QRunnable, Qt, QThreadPool, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from functions.adb_commands import ADBError, ADBManager


class WorkerSignals(QObject):
    """Signals emitted by background workers."""

    finished = pyqtSignal(object)
    error = pyqtSignal(str)


class Worker(QRunnable):
    """Execute a callable without blocking the Qt event loop."""

    def __init__(self, fn) -> None:
        super().__init__()
        self.fn = fn
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self) -> None:
        try:
            self.signals.finished.emit(self.fn())
        except Exception as exc:  # noqa: BLE001 - report all worker errors to the GUI
            self.signals.error.emit(str(exc))


class ADBFastbootUI(QWidget):
    """Desktop interface for common ADB operations."""

    def __init__(self) -> None:
        super().__init__()
        self.adb = ADBManager()
        self.thread_pool = QThreadPool.globalInstance()
        self.active_workers = 0
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("ADB Commander")
        self.resize(900, 650)

        layout = QVBoxLayout(self)

        self.device_label = QLabel("Device: checking...")
        layout.addWidget(self.device_label)

        self.output_box = QTextEdit(readOnly=True)
        self.output_box.setPlaceholderText("ADB output will appear here.")
        layout.addWidget(self.output_box)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        grid = QGridLayout()
        layout.addLayout(grid)

        actions = [
            ("Device Status", self._get_device_status),
            ("Device Info", lambda: self._run(self.adb.get_device_info)),
            ("Storage Status", lambda: self._run(self.adb.storage_status)),
            ("Battery Status", lambda: self._run(self.adb.battery_status)),
            ("SD Card", lambda: self._run(lambda: "SD card found." if self.adb.is_there_any_sd() else "No SD card detected.")),
            ("Root Status", lambda: self._run(lambda: "Device is rooted." if self.adb.is_device_rooted() else "Device is not rooted.")),
            ("Reboot Bootloader", lambda: self._run(self.adb.reboot_device_to_bootloader)),
            ("Reboot Recovery", lambda: self._run(self.adb.reboot_device_to_recovery)),
            ("Install APK", self._install_apk),
            ("List Apps", lambda: self._run(self.adb.list_installed_apps)),
            ("Uninstall App", self._uninstall_app),
            ("Screenshot", self._capture_screenshot),
            ("Record Screen", self._record_screen),
        ]

        for index, (label, callback) in enumerate(actions):
            button = QPushButton(label)
            button.clicked.connect(callback)
            grid.addWidget(button, index // 3, index % 3)

        self._get_device_status()

    def _set_busy(self, busy: bool) -> None:
        self.progress_bar.setVisible(busy)
        for button in self.findChildren(QPushButton):
            button.setEnabled(not busy)

    def _run(self, fn) -> None:
        self.active_workers += 1
        self._set_busy(True)
        worker = Worker(fn)
        worker.signals.finished.connect(self._worker_finished)
        worker.signals.error.connect(self._worker_error)
        self.thread_pool.start(worker)

    @pyqtSlot(object)
    def _worker_finished(self, result) -> None:
        self.active_workers = max(0, self.active_workers - 1)
        self._set_busy(self.active_workers > 0)
        self._display_output(str(result))
        self._refresh_device_label()

    @pyqtSlot(str)
    def _worker_error(self, message: str) -> None:
        self.active_workers = max(0, self.active_workers - 1)
        self._set_busy(self.active_workers > 0)
        self._display_output(f"Error: {message}")
        self._refresh_device_label()

    def _display_output(self, text: str) -> None:
        self.output_box.append(text)
        scrollbar = self.output_box.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _refresh_device_label(self) -> None:
        try:
            devices = self.adb.get_devices()
            ready = next((device for device in devices if device.ready), None)
            self.device_label.setText(
                f"Device: {ready.serial}"
                if ready
                else "Device: not connected"
            )
        except ADBError as exc:
            self.device_label.setText(f"Device: error ({exc})")

    def _get_device_status(self) -> None:
        self._run(self._device_status_result)

    def _device_status_result(self) -> str:
        devices = self.adb.get_devices()
        if not devices:
            return "No devices detected."
        return "\n".join(f"{device.serial}: {device.state}" for device in devices)

    def _install_apk(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select APK", "", "APK Files (*.apk)")
        if path:
            self._run(lambda: self.adb.install_apk(path))

    def _uninstall_app(self) -> None:
        package, accepted = QInputDialog.getText(self, "Uninstall App", "Package name:")
        if accepted and package.strip():
            self._run(lambda: self.adb.uninstall_app(package))

    def _capture_screenshot(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save Screenshot", "screenshot.png", "PNG Files (*.png)")
        if path:
            self._run(lambda: self.adb.capture_screenshot(path))

    def _record_screen(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save Recording", "recording.mp4", "MP4 Files (*.mp4)")
        if not path:
            return
        duration, accepted = QInputDialog.getInt(self, "Record Screen", "Duration (seconds):", 10, 1, 3600)
        if accepted:
            self._run(lambda: self.adb.record_screen(path, duration))

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API
        if self.active_workers:
            QMessageBox.warning(self, "Operation in progress", "Wait for the current ADB operation to finish.")
            event.ignore()
            return
        event.accept()
