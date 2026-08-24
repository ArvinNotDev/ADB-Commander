"""ADB command execution and Android device helpers.

The module deliberately keeps subprocess handling in one place so the CLI, GUI,
and tests all share the same error handling and command semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess
from typing import Sequence


class ADBError(RuntimeError):
    """Raised when an ADB command cannot be completed."""


@dataclass(frozen=True, slots=True)
class Device:
    """A device reported by ``adb devices``."""

    serial: str
    state: str

    @property
    def ready(self) -> bool:
        return self.state == "device"


class ADBManager:
    """High-level wrapper around the Android Debug Bridge executable."""

    def __init__(self, adb_path: str | None = None, timeout: float = 30.0) -> None:
        self.adb_path = adb_path or shutil.which("adb")
        self.timeout = timeout
        if not self.adb_path:
            raise EnvironmentError(
                "ADB (Android Debug Bridge) is not installed or not in PATH. "
                "Install Android Platform Tools and make 'adb' available in PATH."
            )

    @staticmethod
    def check_adb_installed() -> bool:
        """Return whether the ADB executable can be found on PATH."""
        return shutil.which("adb") is not None

    def _run(
        self,
        args: Sequence[str],
        *,
        timeout: float | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Run an ADB command and normalize subprocess failures."""
        command = [self.adb_path, *args]
        try:
            result = subprocess.run(
                command,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=timeout or self.timeout,
                check=False,
            )
        except FileNotFoundError as exc:
            raise ADBError("ADB executable was not found.") from exc
        except subprocess.TimeoutExpired as exc:
            raise ADBError(f"ADB command timed out after {exc.timeout:g}s: {' '.join(command)}") from exc
        except OSError as exc:
            raise ADBError(f"Unable to execute ADB: {exc}") from exc

        if check and result.returncode != 0:
            detail = (result.stderr or result.stdout).strip() or "Unknown ADB error."
            raise ADBError(f"ADB command failed ({result.returncode}): {detail}")
        return result

    def _run_bytes(
        self,
        args: Sequence[str],
        *,
        timeout: float | None = None,
    ) -> bytes:
        """Run an ADB command when binary stdout is required."""
        command = [self.adb_path, *args]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                timeout=timeout or self.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ADBError(f"ADB command timed out after {exc.timeout:g}s: {' '.join(command)}") from exc
        except OSError as exc:
            raise ADBError(f"Unable to execute ADB: {exc}") from exc

        if result.returncode != 0:
            detail = result.stderr.decode("utf-8", errors="replace").strip()
            raise ADBError(f"ADB command failed ({result.returncode}): {detail or 'Unknown ADB error.'}")
        return result.stdout

    def get_devices(self) -> list[Device]:
        """Return all devices reported by ADB, including unauthorized/offline ones."""
        output = self._run(["devices"], timeout=min(self.timeout, 10)).stdout
        devices: list[Device] = []
        for line in output.splitlines():
            line = line.strip()
            if not line or line.startswith("List of devices attached") or line.startswith("*"):
                continue
            parts = line.split("\t", 1)
            if len(parts) != 2:
                continue
            serial, state = parts
            devices.append(Device(serial=serial.strip(), state=state.strip()))
        return devices

    def get_permission(self) -> bool:
        """Return True when at least one authorized ADB device is available."""
        return any(device.ready for device in self.get_devices())

    def _device_args(self, serial: str | None = None) -> list[str]:
        """Build the optional serial selector for an ADB command."""
        return ["-s", serial] if serial else []

    def require_device(self, serial: str | None = None) -> str:
        """Return an authorized device serial, or raise a useful error."""
        devices = self.get_devices()
        ready = [device for device in devices if device.ready]
        if serial:
            if any(device.serial == serial and device.ready for device in ready):
                return serial
            raise ADBError(f"Device '{serial}' is not connected or authorized.")
        if not ready:
            if any(device.state == "unauthorized" for device in devices):
                raise ADBError("Device is connected but unauthorized. Unlock it and accept the USB debugging prompt.")
            raise ADBError("No authorized Android device is connected.")
        return ready[0].serial

    def is_there_any_sd(self, serial: str | None = None) -> bool:
        """Check whether a mounted removable/external storage directory exists."""
        self.require_device(serial)
        output = self._run([*self._device_args(serial), "shell", "ls", "-1", "/storage"], check=True).stdout
        ignored = {"emulated", "self"}
        return any(line.strip() not in ignored for line in output.splitlines() if line.strip())

    def storage_status(self, serial: str | None = None) -> str:
        """Return used percentage for the primary data partition."""
        self.require_device(serial)
        output = self._run([*self._device_args(serial), "shell", "df", "-P", "/data"]).stdout
        for line in reversed(output.splitlines()):
            match = re.search(r"\s(\d+)%\s+\S+\s*$", line)
            if match:
                return f"Storage is {match.group(1)}% full."
        return "Storage info not available."

    def battery_status(self, serial: str | None = None) -> str:
        """Return the raw Android battery service output."""
        self.require_device(serial)
        return self._run([*self._device_args(serial), "shell", "dumpsys", "battery"]).stdout.strip()

    def is_device_rooted(self, serial: str | None = None) -> bool:
        """Check for actual root execution rather than only checking for a ``su`` binary."""
        self.require_device(serial)
        result = self._run(
            [*self._device_args(serial), "shell", "su", "-c", "id"],
            check=False,
            timeout=min(self.timeout, 10),
        )
        output = f"{result.stdout}\n{result.stderr}"
        return result.returncode == 0 and bool(re.search(r"uid=0(?:\(|\s)", output))

    def reboot_device_to_bootloader(self, serial: str | None = None) -> str:
        """Reboot the selected device into bootloader mode."""
        self.require_device(serial)
        self._run([*self._device_args(serial), "reboot", "bootloader"], timeout=10)
        return "Device is rebooting into bootloader mode."

    def reboot_device_to_recovery(self, serial: str | None = None) -> str:
        """Reboot the selected device into recovery mode."""
        self.require_device(serial)
        self._run([*self._device_args(serial), "reboot", "recovery"], timeout=10)
        return "Device is rebooting into recovery mode."

    def install_apk(self, apk_path: str, serial: str | None = None) -> str:
        """Install an APK directly using ``adb install``."""
        path = Path(apk_path).expanduser()
        if not path.is_file():
            return f"APK file not found: {path}"
        if path.suffix.lower() != ".apk":
            return "The selected file is not an APK."
        self.require_device(serial)
        result = self._run(
            [*self._device_args(serial), "install", "-r", str(path)],
            timeout=max(self.timeout, 120),
        )
        return (result.stdout or result.stderr).strip() or "APK installed successfully."

    def list_installed_apps(self, serial: str | None = None, third_party_only: bool = True) -> str:
        """List installed package names."""
        self.require_device(serial)
        args = [*self._device_args(serial), "shell", "pm", "list", "packages"]
        if third_party_only:
            args.append("-3")
        return self._run(args).stdout.strip()

    def uninstall_app(self, package_name: str, serial: str | None = None) -> str:
        """Uninstall an application package."""
        package_name = package_name.strip()
        if not re.fullmatch(r"[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+", package_name):
            return "Invalid Android package name."
        self.require_device(serial)
        result = self._run([*self._device_args(serial), "uninstall", package_name], check=False)
        return (result.stdout or result.stderr).strip() or "Package operation completed."

    def capture_screenshot(self, output_file: str, serial: str | None = None) -> str:
        """Capture a PNG screenshot to a local file."""
        destination = Path(output_file).expanduser()
        if destination.suffix.lower() != ".png":
            destination = destination.with_suffix(".png")
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.require_device(serial)
        data = self._run_bytes([*self._device_args(serial), "exec-out", "screencap", "-p"])
        if not data.startswith(b"\x89PNG"):
            raise ADBError("Device did not return a valid PNG screenshot.")
        destination.write_bytes(data)
        return f"Screenshot saved to: {destination}"

    def record_screen(self, output_file: str, duration: int, serial: str | None = None) -> str:
        """Record the device screen and pull the resulting MP4 to the host."""
        if not 1 <= duration <= 3600:
            return "Recording duration must be between 1 and 3600 seconds."
        destination = Path(output_file).expanduser()
        if destination.suffix.lower() != ".mp4":
            destination = destination.with_suffix(".mp4")
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.require_device(serial)
        remote = "/sdcard/adb-commander-screen.mp4"
        try:
            self._run(
                [*self._device_args(serial), "shell", "screenrecord", "--time-limit", str(duration), remote],
                timeout=duration + 20,
            )
            self._run([*self._device_args(serial), "pull", remote, str(destination)], timeout=30)
        finally:
            self._run([*self._device_args(serial), "shell", "rm", "-f", remote], check=False, timeout=10)
        return f"Screen recording saved to: {destination}"

    def get_device_info(self, serial: str | None = None) -> str:
        """Get basic device identity and Android version information."""
        self.require_device(serial)
        values = {}
        for key, label in (
            ("ro.product.brand", "Brand"),
            ("ro.product.model", "Model"),
            ("ro.build.version.release", "Android Version"),
            ("ro.build.version.sdk", "SDK"),
        ):
            result = self._run([*self._device_args(serial), "shell", "getprop", key])
            values[label] = result.stdout.strip() or "Unknown"
        return "\n".join(f"{label}: {value}" for label, value in values.items())


if __name__ == "__main__":
    try:
        adb = ADBManager()
        devices = adb.get_devices()
        if not devices:
            print("No devices detected.")
        else:
            for device in devices:
                print(f"{device.serial}: {device.state}")
            if any(device.ready for device in devices):
                print("\n" + adb.get_device_info())
    except (EnvironmentError, ADBError) as exc:
        print(f"Error: {exc}")
