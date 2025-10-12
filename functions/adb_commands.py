import subprocess
import shutil


class ADBManager:
    def __init__(self):
        if not self.check_adb_installed():
            raise EnvironmentError(
                "ADB (Android Debug Bridge) is not installed or not in PATH. "
                "Please install it and make sure it's accessible from the command line."
            )

    @staticmethod
    def check_adb_installed() -> bool:
        """Check if adb is available in PATH."""
        return shutil.which("adb") is not None

    @staticmethod
    def get_permission() -> bool:
        """Check if an ADB device is connected."""
        try:
            result = subprocess.check_output(['adb', 'devices'])
            decoded = result.decode('utf-8')
            if "device" in decoded.split("\n")[1]:
                return True
            else:
                print("No device detected. Please connect your phone.")
                return False
        except subprocess.CalledProcessError as e:
            print(f"Error: {e.returncode}")
            return False
        except FileNotFoundError:
            print("ADB not found.")
            return False

    def is_there_any_sd(self) -> bool:
        """Check if there is an SD card in the connected phone."""
        if not self.get_permission():
            return False

        try:
            storages = subprocess.check_output(['adb', 'shell', 'ls', '/storage'])
            decoded = storages.decode("utf-8")
            if any(x in decoded for x in ['sdcard', 'sdcard1', 'extSdCard']):
                print("SD card found!")
                return True
            else:
                print("No SD card detected.")
                return False
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
            return False

    def storage_status(self) -> str:
        """Check the phone's storage usage percentage."""
        if not self.get_permission():
            return "No device connected."

        try:
            storage_percent = subprocess.check_output(['adb', 'shell', 'df'])
            decoded = storage_percent.decode('utf-8')
            where_is_emulated = decoded.find('/storage/emulated')
            if where_is_emulated != -1:
                percentage = decoded[where_is_emulated - 4: where_is_emulated - 1]
                return f"Storage is {percentage} full."
            else:
                return "Storage info not available."
        except subprocess.CalledProcessError as e:
            return f"Error retrieving storage info: {e}"

    def battery_status(self) -> str:
        """Get battery status of the connected phone."""
        if not self.get_permission():
            return "No device connected."

        try:
            battery = subprocess.check_output(['adb', 'shell', 'dumpsys', 'battery'])
            return battery.decode('utf-8')
        except subprocess.CalledProcessError as e:
            return f"Error retrieving battery status: {e}"

    def is_device_rooted(self) -> bool:
        """Check if the device has root access."""
        if not self.get_permission():
            return False

        try:
            result = subprocess.check_output(['adb', 'shell', 'su', '-v'], stderr=subprocess.PIPE)
            if result:
                print("Device is rooted.")
                return True
            return False
        except subprocess.CalledProcessError:
            print("Device is not rooted.")
            return False

    def reboot_device_to_bootloader(self) -> str:
        """Reboot the device into bootloader mode."""
        if not self.get_permission():
            return "No device connected."

        try:
            print("Rebooting device to bootloader mode...")
            subprocess.check_call(['adb', 'reboot', 'bootloader'])
            return "Device is rebooting into bootloader mode."
        except subprocess.CalledProcessError as e:
            return f"Error while rebooting: {e}"

    def reboot_device_to_recovery(self) -> str:
        """Reboot the device into recovery mode."""
        if not self.get_permission():
            return "No device connected."

        try:
            print("Rebooting device to recovery mode...")
            subprocess.check_call(['adb', 'reboot', 'recovery'])
            return "Device is rebooting into recovery mode."
        except subprocess.CalledProcessError as e:
            return f"Error while rebooting: {e}"

    def install_apk(self, apk_path: str) -> str:
        """Push the APK to a writable location and install it."""
        if not self.get_permission():
            return "No device connected."

        remote_path = "/data/local/tmp/app.apk"

        try:
            push_result = subprocess.check_output(['adb', 'push', apk_path, remote_path], stderr=subprocess.PIPE)
            print(f"Push Result: {push_result.decode('utf-8')}")

            install_result = subprocess.check_output(['adb', 'shell', 'pm', 'install', remote_path], stderr=subprocess.PIPE)
            return f"Installation successful: {install_result.decode('utf-8')}"
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr.decode('utf-8')}" if e.stderr else str(e)

    def get_device_info(self) -> str:
        """Get device information including model, brand, and Android version."""
        if not self.get_permission():
            return "No device connected."

        try:
            brand = subprocess.check_output(['adb', 'shell', 'getprop', 'ro.product.brand']).decode('utf-8').strip()
            model = subprocess.check_output(['adb', 'shell', 'getprop', 'ro.product.model']).decode('utf-8').strip()
            android_version = subprocess.check_output(['adb', 'shell', 'getprop', 'ro.build.version.release']).decode('utf-8').strip()
            return f"Brand: {brand}\nModel: {model}\nAndroid Version: {android_version}"
        except subprocess.CalledProcessError as e:
            return f"Error retrieving device info: {e}"

if __name__ == "__main__":
    try:
        adb = ADBManager()
        if adb.get_permission():
            print(adb.get_device_info())
        else:
            print("No device connected.")
    except EnvironmentError as e:
        print(e)
