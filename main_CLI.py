import shutil
from functions.adb_commands import ADBManager


class ADBCLI:
    def __init__(self):
        if not self.check_adb_installed():
            raise EnvironmentError(
                "ADB (Android Debug Bridge) is not installed or not in PATH.\n"
                "Please install ADB and make sure it's accessible from the command line."
            )
        self.adb = ADBManager()
        self.device_connected = self.adb.get_permission()

    @staticmethod
    def check_adb_installed() -> bool:
        """Check if adb is available in PATH."""
        return shutil.which("adb") is not None

    def update_device_status(self):
        """Update the device connection status."""
        self.device_connected = self.adb.get_permission()
        if not self.device_connected:
            print("No devices connected.")

    def run(self):
        """Main CLI loop."""
        self.update_device_status()
        if not self.device_connected:
            return

        while True:
            print("\nSelect an option:")
            print("1. Check if device is connected")
            print("2. Check storage status")
            print("3. Check battery status")
            print("4. Check SD card status")
            print("5. Check if the device is rooted")
            print("6. Reboot the device into bootloader")
            print("7. Install an APK")
            print("8. Close")

            choice = input("Enter your choice (1-8): ")

            if choice != '1':
                self.update_device_status()
                if not self.device_connected:
                    continue

            match choice:
                case '1':
                    print("Device connected." if self.device_connected else "No devices connected.")
                case '2':
                    print(self.adb.storage_status())
                case '3':
                    print(self.adb.battery_status())
                case '4':
                    self.adb.is_there_any_sd()
                case '5':
                    print("Device is rooted." if self.adb.is_device_rooted() else "Device is not rooted.")
                case '6':
                    print(self.adb.reboot_device_to_bootloader())
                case '7':
                    apk_path = input("Enter the full path of the APK file: ")
                    print(self.adb.install_apk(apk_path))
                case '8':
                    print("Exiting...")
                    break
                case _:
                    print("Invalid choice, please try again.")


if __name__ == "__main__":
    try:
        cli_app = ADBCLI()
        cli_app.run()
    except EnvironmentError as e:
        print(e)
