<div align="center">

# ADB Commander

**A modern desktop workspace for Android Debug Bridge**

Manage Android devices, inspect system health, handle APKs, capture the screen, transfer files, and run shell commands from one focused interface.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/UI-PyQt6-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://www.riverbankcomputing.com/software/pyqt/)
[![ADB](https://img.shields.io/badge/Android-Platform%20Tools-3DDC84?style=for-the-badge&logo=android&logoColor=white)](https://developer.android.com/tools/releases/platform-tools)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

</div>

---

## Overview

ADB Commander brings frequently used Android Debug Bridge workflows into a native desktop app. The interface is organized into a horizontal navigation bar with a device overview, device diagnostics, package management, capture tools, file transfer, and an advanced shell.

The device panel refreshes automatically and distinguishes authorized, unauthorized, offline, and disconnected states. A visual handset preview reflects the current connection state. Operations that may take time run in Qt background workers so normal navigation remains responsive.

## Features

### Device center
- Automatic ADB device discovery and connection-state refresh.
- Device selection when more than one device is attached.
- Brand, model, Android release, and SDK details.
- Storage usage, battery diagnostics, screen resolution, Wi-Fi IPv4, external-storage, and root-access checks.
- Confirmed reboot controls for Android, bootloader, and recovery.
- Connect to an ADB-over-TCP endpoint using host and port.

### Application management
- List third-party package names.
- Install APK files from the computer.
- Uninstall a package by selecting it or entering its package identifier.

### Capture and diagnostics
- Capture PNG screenshots directly from adb exec-out.
- Record the device screen to MP4 and copy the recording back to the computer.
- Read a bounded slice of recent logcat output.
- Export recent logs to a text file for troubleshooting.

### File transfer and terminal
- Push a local file to an Android device.
- Pull a remote file to the computer.
- Run a command through Android's shell and view output inside the app.
- Background execution and an activity feed for longer operations.

### Interface
- Dark PyQt6 desktop UI with horizontal navigation.
- Device illustration that changes with connection state.
- Dashboard metrics and one-click shortcuts.
- Device picker designed for multiple connected devices.
- Clear operation status, progress indicator, and recent activity.

## Requirements

- Python 3.10 or later
- Android SDK Platform Tools with adb available on PATH
- PyQt6

Install Platform Tools from the official Android documentation:

<https://developer.android.com/tools/releases/platform-tools>

Install the Python dependencies:

~~~bash
python -m pip install -r requirements.txt
~~~

For development and tests:

~~~bash
python -m pip install -r requirements-dev.txt
~~~

## Launch

Start the graphical application:

~~~bash
python main_GUI.py
~~~

Start the interactive CLI:

~~~bash
python main_CLI.py
~~~

Inspect the ADB command layer:

~~~bash
python -m functions.adb_commands
~~~

## Connect an Android device

1. Enable **Developer options** and **USB debugging** on the phone.
2. Connect the phone using a data-capable USB cable.
3. Unlock the phone and accept the computer's RSA authorization prompt.
4. Open ADB Commander and select the device from the top-right device picker.

For Android 11+ **Wireless Debugging** pairing-code mode, ADB Commander keeps pairing and connecting as two separate actions:

**Pair a new device (one-time per computer/device pairing):**

1. Keep the Android device and computer on the same trusted Wi-Fi network.
2. On Android, open **Developer options → Wireless debugging → Pair device with pairing code**.
3. In ADB Commander, open **Device → Pair new device…**.
4. Enter the pairing `IP:port` and six-digit code shown by the pairing dialog. ADB Commander runs `adb pair` only.

**Connect to a device that was already paired:**

1. Return to the main **Wireless debugging** screen on Android (not the pairing-code screen).
2. In ADB Commander, open **Device → Connect paired device…**.
3. Enter the current connection `IP:port`. ADB Commander runs `adb connect` and refreshes the device list.

The pairing port and connection port are different; never reuse the pairing port for the final connection. The connection port can change, so read its current value from the main Wireless Debugging screen. Pairing is normally remembered by Android for subsequent connections from the same computer.

Older ADB-over-TCP mode (where Android exposes a single debugging port and no pairing-code screen) can use **Connect paired device…** directly. Device and computer must be mutually reachable on the same trusted network. Disable Wireless Debugging when it is no longer needed.

## Tests

The test suite mocks ADB subprocess calls, so command-layer tests do not need a physical device:

~~~bash
python -m pytest
~~~

## Safety and compatibility notes

- The Terminal page executes commands on the selected Android device. A shell command can modify or delete data; only run commands you understand.
- Root detection reports whether a su command returns UID 0. It is a diagnostic check, not a guarantee that every privileged operation will work.
- Android versions and vendor ROMs may differ in the availability of properties, screen recording, package operations, and log output.
- Access to app-private directories is restricted by Android on many devices. File transfer may require a path accessible to the ADB shell user.
- Wireless ADB should only be enabled on networks you trust. Disconnect wireless debugging when it is no longer needed.

## Project structure

~~~text
ADB-Commander/
├── functions/
│   ├── adb_commands.py
│   └── adb_extras.py
├── ui/
│   └── ui.py
├── tests/
│   ├── test_adb_commands.py
│   └── test_adb_extras.py
├── main_GUI.py
├── main_CLI.py
├── requirements.txt
└── requirements-dev.txt
~~~

## License

This project is distributed under the MIT License. See the LICENSE file for the full text.
