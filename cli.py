from functions import *


def main():
    if not get_permission():
        print("No devices connected.")
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

        if choice != '1' and not get_permission():
            print("No device detected. Please connect a device first.")
            continue

        match choice:
            case '1':
                print("Device connected." if get_permission() else "No devices connected.")
            case '2':
                print("Storage is", storage_status(), "full.")
            case '3':
                print("Battery Status: \n", battery_status())
            case '4':
                is_there_any_sd()
            case '5':
                print("Device is rooted." if is_device_rooted() else "Device is not rooted.")
            case '6':
                reboot_device_to_bootloader()
            case '7':
                apk_path = input("Enter the full path of the APK file: ")
                print(install_apk(apk_path))
            case '8':
                print("Exiting...")
                break
            case _:
                print("Invalid choice, please try again.")


if __name__ == '__main__':
    main()
