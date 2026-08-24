"""Interactive command-line interface for ADB Commander."""

from __future__ import annotations

from pathlib import Path
import shutil

from functions.adb_commands import ADBError, ADBManager


class ADBCLI:
    """Small, defensive CLI around :class:`ADBManager`."""

    def __init__(self, adb: ADBManager | None = None) -> None:
        if not shutil.which("adb") and adb is None:
            raise EnvironmentError("ADB is not installed or not available in PATH.")
        self.adb = adb or ADBManager()
        self.device_serial: str | None = None

    def update_device_status(self) -> bool:
        """Refresh the selected device and report its state."""
        devices = self.adb.get_devices()
        ready = [device for device in devices if device.ready]
        self.device_serial = ready[0].serial if ready else None
        if not ready:
            print("No authorized Android devices connected.")
            for device in devices:
                print(f"- {device.serial}: {device.state}")
            return False
        print(f"Connected device: {self.device_serial}")
        return True

    def _print_result(self, action) -> None:
        try:
            result = action()
            print(result if result is not None else "Done.")
        except ADBError as exc:
            print(f"Error: {exc}")

    def run(self) -> None:
        """Run the interactive menu until the user exits."""
        self.update_device_status()

        while True:
            print(
                "\nADB Commander\n"
                "1. Device status\n"
                "2. Device information\n"
                "3. Storage status\n"
                "4. Battery status\n"
                "5. SD card status\n"
                "6. Root status\n"
                "7. Reboot bootloader\n"
                "8. Reboot recovery\n"
                "9. Install APK\n"
                "10. List installed apps\n"
                "11. Uninstall app\n"
                "12. Capture screenshot\n"
                "13. Record screen\n"
                "0. Exit"
            )
            choice = input("Select an option: ").strip()

            if choice == "0":
                print("Exiting...")
                return
            if choice == "1":
                self.update_device_status()
            elif choice == "2":
                self._print_result(lambda: self.adb.get_device_info(self.device_serial))
            elif choice == "3":
                self._print_result(lambda: self.adb.storage_status(self.device_serial))
            elif choice == "4":
                self._print_result(lambda: self.adb.battery_status(self.device_serial))
            elif choice == "5":
                self._print_result(lambda: "SD card found." if self.adb.is_there_any_sd(self.device_serial) else "No SD card detected.")
            elif choice == "6":
                self._print_result(lambda: "Device is rooted." if self.adb.is_device_rooted(self.device_serial) else "Device is not rooted.")
            elif choice == "7":
                self._print_result(lambda: self.adb.reboot_device_to_bootloader(self.device_serial))
                self.device_serial = None
            elif choice == "8":
                self._print_result(lambda: self.adb.reboot_device_to_recovery(self.device_serial))
                self.device_serial = None
            elif choice == "9":
                apk = input("APK path: ").strip()
                self._print_result(lambda: self.adb.install_apk(apk, self.device_serial))
            elif choice == "10":
                self._print_result(lambda: self.adb.list_installed_apps(self.device_serial))
            elif choice == "11":
                package = input("Package name: ").strip()
                self._print_result(lambda: self.adb.uninstall_app(package, self.device_serial))
            elif choice == "12":
                output = input("Output PNG path: ").strip()
                if output:
                    self._print_result(lambda: self.adb.capture_screenshot(output, self.device_serial))
            elif choice == "13":
                output = input("Output MP4 path: ").strip()
                try:
                    duration = int(input("Duration in seconds (1-3600): ").strip())
                except ValueError:
                    print("Duration must be an integer.")
                    continue
                self._print_result(lambda: self.adb.record_screen(output, duration, self.device_serial))
            else:
                print("Invalid choice.")


if __name__ == "__main__":
    try:
        ADBCLI().run()
    except EnvironmentError as exc:
        print(f"Error: {exc}")
