"""Additional ADB operations used by the desktop UI."""

from __future__ import annotations

from pathlib import Path
import re

from functions.adb_commands import ADBError, ADBManager


class ADBExtras:
    """Small extension layer for file transfer, wireless ADB and diagnostics."""

    def __init__(self, manager: ADBManager) -> None:
        self.adb = manager

    @staticmethod
    def _validate_wireless_endpoint(endpoint: str) -> str:
        """Validate an ADB host:port endpoint and return its normalized value."""
        endpoint = endpoint.strip()
        match = re.fullmatch(r"(?:[A-Za-z0-9.-]+|\\[[0-9A-Fa-f:]+\\]):([0-9]{1,5})", endpoint)
        if not match:
            raise ValueError("Enter a valid host and port, e.g. 192.168.1.45:37123.")
        port = int(match.group(1))
        if not 1 <= port <= 65535:
            raise ValueError("The port must be between 1 and 65535.")
        return endpoint

    def pair_wireless(self, endpoint: str, pairing_code: str) -> str:
        """Pair this computer with Android 11+ wireless debugging using its pairing port."""
        endpoint = self._validate_wireless_endpoint(endpoint)
        pairing_code = pairing_code.strip()
        if not re.fullmatch(r"[0-9]{6}", pairing_code):
            raise ValueError("Enter the six-digit pairing code shown by Android Wireless Debugging.")

        result = self.adb._run(["pair", endpoint, pairing_code], timeout=30, check=False)
        output = (result.stdout or result.stderr).strip()
        lowered = output.lower()
        if result.returncode != 0 or any(
            marker in lowered
            for marker in ("failed:", "failed to", "cannot pair", "unable to pair", "error:")
        ):
            if "unknown command" in lowered or "not recognized" in lowered:
                raise ADBError(
                    "This ADB version does not support wireless pairing. Update Android SDK Platform-Tools, "
                    "then restart ADB Commander."
                )
            raise ADBError(output or "ADB could not pair with the wireless debugging endpoint.")
        return output or ("ADB pairing completed for " + endpoint)

    def connect_wireless(self, endpoint: str) -> str:
        """Connect ADB to an explicitly supplied wireless-debugging host:port endpoint."""
        endpoint = self._validate_wireless_endpoint(endpoint)
        result = self.adb._run(["connect", endpoint], timeout=15, check=False)
        output = (result.stdout or result.stderr).strip()
        lowered = output.lower()
        if result.returncode != 0 or any(
            marker in lowered
            for marker in ("failed to connect", "cannot connect", "unable to connect", "connection refused",
                           "no route to host", "failed:")
        ):
            raise ADBError(output or "ADB could not connect to the wireless endpoint.")
        return output or ("ADB connection requested for " + endpoint)

    def disconnect_wireless(self, endpoint: str | None = None) -> str:
        """Disconnect one endpoint, or all wireless endpoints when omitted."""
        args = ["disconnect"]
        if endpoint:
            endpoint = endpoint.strip()
            match = re.fullmatch(r"(?:[A-Za-z0-9.-]+|\[[0-9A-Fa-f:]+\]):([0-9]{1,5})", endpoint)
            if not match or not 1 <= int(match.group(1)) <= 65535:
                raise ValueError("Enter a valid host:port endpoint.")
            args.append(endpoint)
        result = self.adb._run(args, timeout=15, check=False)
        output = (result.stdout or result.stderr).strip()
        if result.returncode != 0:
            raise ADBError(output or "ADB could not disconnect the endpoint.")
        return output or "ADB disconnect requested."

    def get_screen_resolution(self, serial: str | None = None) -> str:
        """Return Android's configured and physical screen sizes."""
        self.adb.require_device(serial)
        output = self.adb._run([*self.adb._device_args(serial), "shell", "wm", "size"]).stdout.strip()
        return output or "Display resolution unavailable."

    def get_wifi_ip(self, serial: str | None = None) -> str:
        """Find the current Wi-Fi IPv4 address when Android exposes it."""
        self.adb.require_device(serial)
        result = self.adb._run(
            [*self.adb._device_args(serial), "shell", "ip", "-f", "inet", "addr", "show", "wlan0"],
            check=False,
            timeout=10,
        )
        match = re.search(r"\binet\s+(\d{1,3}(?:\.\d{1,3}){3})/", result.stdout)
        if match:
            return "Wi-Fi IPv4: " + match.group(1)
        fallback = self.adb._run(
            [*self.adb._device_args(serial), "shell", "getprop", "dhcp.wlan0.ipaddress"],
            check=False,
            timeout=10,
        ).stdout.strip()
        if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", fallback):
            return "Wi-Fi IPv4: " + fallback
        return "No Wi-Fi IPv4 address found. Make sure Wi-Fi is connected."

    def push_file(self, local_path: str, remote_path: str, serial: str | None = None) -> str:
        """Copy a local file onto the selected Android device."""
        source = Path(local_path).expanduser()
        if not source.is_file():
            raise ValueError("Local file does not exist: " + str(source))
        destination = remote_path.strip()
        if not destination or "\x00" in destination:
            raise ValueError("Enter a valid Android destination path.")
        self.adb.require_device(serial)
        result = self.adb._run(
            [*self.adb._device_args(serial), "push", str(source), destination],
            timeout=max(self.adb.timeout, 120),
        )
        return (result.stdout or result.stderr).strip() or "File pushed successfully."

    def pull_file(self, remote_path: str, local_path: str, serial: str | None = None) -> str:
        """Copy a remote Android file onto the local computer."""
        source = remote_path.strip()
        destination = Path(local_path).expanduser()
        if not source or "\x00" in source:
            raise ValueError("Enter a valid Android source path.")
        if destination.exists() and destination.is_dir():
            raise ValueError("Choose a file destination, not a directory.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.adb.require_device(serial)
        result = self.adb._run(
            [*self.adb._device_args(serial), "pull", source, str(destination)],
            timeout=max(self.adb.timeout, 120),
        )
        return (result.stdout or result.stderr).strip() or ("File pulled to: " + str(destination))

    def execute_shell(self, command: str, serial: str | None = None) -> str:
        """Execute one explicit command through Android's shell and return its output."""
        command = command.strip()
        if not command:
            raise ValueError("Enter a command to execute.")
        if len(command) > 2000 or "\x00" in command:
            raise ValueError("The command is invalid or exceeds the 2000-character limit.")
        self.adb.require_device(serial)
        result = self.adb._run(
            [*self.adb._device_args(serial), "shell", command],
            timeout=max(self.adb.timeout, 60),
            check=False,
        )
        output, errors = result.stdout.strip(), result.stderr.strip()
        combined = "\n".join(part for part in (output, errors) if part)
        if result.returncode != 0 and not combined:
            raise ADBError("Android shell command failed with exit code " + str(result.returncode))
        return combined or ("Command completed with exit code " + str(result.returncode))

    def get_logcat(self, serial: str | None = None, lines: int = 200) -> str:
        """Read recent device logs without starting a continuous stream."""
        if not 1 <= lines <= 10000:
            raise ValueError("Log line count must be between 1 and 10000.")
        self.adb.require_device(serial)
        result = self.adb._run(
            [*self.adb._device_args(serial), "shell", "logcat", "-d", "-t", str(lines)],
            timeout=max(self.adb.timeout, 30),
            check=False,
        )
        output = (result.stdout or result.stderr).strip()
        if result.returncode != 0 and not output:
            raise ADBError("Unable to read logcat.")
        return output or "No log output returned."
