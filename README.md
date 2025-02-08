# ADB Fastboot Tool  

A powerful and easy-to-use tool for managing Android devices using **ADB (Android Debug Bridge)** and **Fastboot**. This project includes both a **GUI** (built with PyQt6) and a **console-based CLI**, making it accessible for both beginners and advanced users.  


## Features  

✅ **GUI & CLI Support** – Use either the graphical interface or the command-line tool.  
✅ **Device Management** – Check device connection, storage, battery, and root status.  
✅ **App Management** – Install, list, and uninstall APKs with ease.  
✅ **Screen Utilities** – Capture screenshots and record screen videos.  
✅ **Reboot Options** – Reboot into bootloader, recovery, or system mode.  
✅ **Fast & Efficient** – No command-line knowledge required for GUI users!


---

## Installation  

### Prerequisites  
Ensure you have **ADB & Fastboot** installed. If not, install them using:  

- **Windows**: [Download ADB & Fastboot](https://developer.android.com/studio/releases/platform-tools)  
- **Linux/macOS**: Install via package manager:  
  ```bash
  sudo apt install adb fastboot  # Debian/Ubuntu
  brew install android-platform-tools  # macOS
  ```

### Enable USB Debugging  
You need to **enable USB debugging** on your Android device for this tool to work.  

1. **Go to Settings** on your Android device.  
2. Scroll down and tap **About phone**.  
3. Find **Build number** and tap it **7 times** to enable **Developer options**.  
4. Go back to **Settings** and open **Developer options**.  
5. Scroll down and enable **USB debugging**.  
6. When you connect your phone to the computer, select **"Allow USB Debugging"** when prompted.  

Now your device should be detected by ADB! 🚀  

---

### Clone the Repository  
```bash
git clone https://github.com/yourusername/adb-fastboot-tool.git
cd adb-fastboot-tool
```


## Usage  

### GUI Version (PyQt6)  
Run the GUI with:  
```bash
python ui/ui.py
```
A modern UI will open, allowing you to manage your Android device without using the command line.

### Console (CLI) Version  
Run the CLI tool with:  
```bash
python cli.py
```
Follow the on-screen prompts to execute ADB and Fastboot commands easily.

---
## Contributing  
Feel free to open an issue or submit a pull request if you want to improve this tool!  

---

## License  
This project is licensed under the **MIT License**.  
