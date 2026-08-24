# ADB Commander

A lightweight desktop and CLI utility for common Android Debug Bridge (ADB) workflows.

## Features

- Detects connected, unauthorized, and offline Android devices reliably.
- Shows device identity, Android version, storage usage, battery diagnostics, and root status.
- Installs and uninstalls APK packages.
- Lists installed applications.
- Reboots devices into bootloader or recovery mode.
- Captures PNG screenshots directly from `adb exec-out`.
- Records the device screen and pulls the resulting MP4 to the host.
- Runs GUI ADB operations in background Qt workers so the interface remains responsive.
- Provides a reusable, testable `ADBManager` command layer shared by the CLI and GUI.

## Requirements

- Python 3.10+
- Android SDK Platform Tools (`adb`) installed and available on `PATH`
- PyQt6 for the GUI

Install the Python dependency:

```bash
python -m pip install -r requirements.txt
```

Install ADB / Platform Tools from the official Android documentation:

https://developer.android.com/tools/releases/platform-tools

## Run

CLI:

```bash
python main_CLI.py
```

GUI:

```bash
python main_GUI.py
```

You can also inspect the ADB layer directly:

```bash
python -m functions.adb_commands
```

## Testing

The command layer is tested with mocked ADB subprocesses, so the test suite does not require a physical Android device or a locally installed ADB executable.

```bash
python -m pytest
```

## Notes

Enable USB debugging on the Android device and accept the computer's RSA authorization prompt before running device operations. Some operations, particularly screen recording and package management, may require additional Android permissions or may vary slightly by vendor ROM.

## License

MIT
