import subprocess


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


def is_there_any_sd() -> bool:
    """Check if there is an SD card in the connected phone."""
    if not get_permission():
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


def storage_status() -> str:
    """Check the phone's storage usage percentage."""
    if not get_permission():
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
        print(f"Error: {e}")
        return "Error retrieving storage info."


def battery_status() -> str:
    """Get battery status of the connected phone."""
    if not get_permission():
        return "No device connected."

    try:
        battery = subprocess.check_output(['adb', 'shell', 'dumpsys', 'battery'])
        return battery.decode('utf-8')
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return "Error retrieving battery status."


def is_device_rooted() -> bool:
    """Check if the device has root access."""
    if not get_permission():
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


def reboot_device_to_bootloader():
    """Reboot the device into bootloader mode."""
    if not get_permission():
        return "No device connected."

    try:
        print("Rebooting device to bootloader mode...")
        subprocess.check_call(['adb', 'reboot', 'bootloader'])
        return "Device is rebooting into bootloader mode."
    except subprocess.CalledProcessError as e:
        return f"Error while rebooting: {e}"


def install_apk(apk_path: str) -> str: 
    """Push the APK to a writable location and install it."""
    if not get_permission():
        return "No device connected."

    remote_path = "/data/local/tmp/app.apk"

    try:
        push_result = subprocess.check_output(['adb', 'push', apk_path, remote_path], stderr=subprocess.PIPE)
        print(f"Push Result: {push_result.decode('utf-8')}")

        install_result = subprocess.check_output(['adb', 'shell', 'pm', 'install', remote_path], stderr=subprocess.PIPE)
        return f"Installation successful: {install_result.decode('utf-8')}"
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.decode('utf-8')}" if e.stderr else str(e)

def list_installed_apps() -> str:
    """List all installed apps on the device."""
    if not get_permission():
        return "No device connected."

    try:
        apps = subprocess.check_output(['adb', 'shell', 'pm', 'list', 'packages'])
        return apps.decode('utf-8')
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"


def uninstall_app(package_name: str) -> str:
    """Uninstall an app by package name."""
    if not get_permission():
        return "No device connected."

    try:
        subprocess.check_call(['adb', 'shell', 'pm', 'uninstall', package_name])
        return f"Successfully uninstalled {package_name}."
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"


def capture_screenshot(output_file: str = "screenshot.png") -> str:
    """Take a screenshot and save it locally."""
    if not get_permission():
        return "No device connected."

    try:
        remote_path = "/sdcard/screenshot.png"
        subprocess.check_call(['adb', 'shell', 'screencap', '-p', remote_path])
        subprocess.check_call(['adb', 'pull', remote_path, output_file])
        return f"Screenshot saved as {output_file}"
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"


def record_screen(output_file: str = "screen_record.mp4", duration: int = 10) -> str:
    """Record the screen for a given duration (default: 10s)."""
    if not get_permission():
        return "No device connected."

    try:
        remote_path = "/sdcard/screen_record.mp4"
        subprocess.check_call(['adb', 'shell', 'screenrecord', '--time-limit', str(duration), remote_path])
        subprocess.check_call(['adb', 'pull', remote_path, output_file])
        return f"Screen recording saved as {output_file}"
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"


def pull_apk(package_name: str, output_file: str) -> str:
    """Extract an installed app's APK from the device."""
    if not get_permission():
        return "No device connected."

    try:
        apk_path = subprocess.check_output(
            ['adb', 'shell', 'pm', 'path', package_name]
        ).decode('utf-8').strip().replace("package:", "")

        if not apk_path:
            return "Error: APK path not found."

        subprocess.check_call(['adb', 'pull', apk_path, output_file])
        return f"APK saved as {output_file}"
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"


def reboot_device_to_bootloader():
    """Reboot the device into bootloader mode."""
    if not get_permission():
        return "No device connected."

    try:
        print("Rebooting device to bootloader mode...")
        subprocess.check_call(['adb', 'reboot', 'bootloader'])
        return "Device is rebooting into bootloader mode."
    except subprocess.CalledProcessError as e:
        return f"Error while rebooting: {e}"


def reboot_device_to_recovery():
    """Reboot the device into recovery mode."""
    if not get_permission():
        return "No device connected."

    try:
        print("Rebooting device to recovery mode...")
        subprocess.check_call(['adb', 'reboot', 'recovery'])
        return "Device is rebooting into recovery mode."
    except subprocess.CalledProcessError as e:
        return f"Error while rebooting: {e}"


def check_adb_root() -> bool:
    """Check if ADB has root access."""
    if not get_permission():
        return False

    try:
        result = subprocess.check_output(['adb', 'shell', 'id'], stderr=subprocess.PIPE)
        if "root" in result.decode('utf-8'):
            print("ADB has root access.")
            return True
        return False
    except subprocess.CalledProcessError:
        print("ADB does not have root access.")
        return False


def get_device_info() -> str:
    """Get device information including model, brand, and Android version."""
    if not get_permission():
        return "No device connected."

    try:
        brand = subprocess.check_output(['adb', 'shell', 'getprop', 'ro.product.brand']).decode('utf-8').strip()
        model = subprocess.check_output(['adb', 'shell', 'getprop', 'ro.product.model']).decode('utf-8').strip()
        android_version = subprocess.check_output(['adb', 'shell', 'getprop', 'ro.build.version.release']).decode('utf-8').strip()

        return f"Brand: {brand}\nModel: {model}\nAndroid Version: {android_version}"
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"
