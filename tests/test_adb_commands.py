from __future__ import annotations

from unittest.mock import patch
import subprocess

import pytest

from functions.adb_commands import ADBError, ADBManager, Device


@pytest.fixture
def manager() -> ADBManager:
    return ADBManager(adb_path="adb")


def completed(stdout: str = "", stderr: str = "", returncode: int = 0):
    return subprocess.CompletedProcess(["adb"], returncode, stdout=stdout, stderr=stderr)


def test_parse_devices(manager: ADBManager) -> None:
    output = "List of devices attached\nABC123\tdevice\nXYZ789\tunauthorized\n\n"
    with patch("subprocess.run", return_value=completed(output)):
        devices = manager.get_devices()
        permission = manager.get_permission()

    assert devices == [Device("ABC123", "device"), Device("XYZ789", "unauthorized")]
    assert permission is True


def test_get_permission_does_not_match_substrings(manager: ADBManager) -> None:
    output = "List of devices attached\nABC123\toffline\n"
    with patch("subprocess.run", return_value=completed(output)):
        assert manager.get_permission() is False
        with pytest.raises(ADBError, match="No authorized"):
            manager.require_device()


def test_storage_status_parses_percentage(manager: ADBManager) -> None:
    responses = [
        completed("List of devices attached\nABC123\tdevice\n"),
        completed("Filesystem  1024  512  512  50%  /data\n"),
    ]
    with patch("subprocess.run", side_effect=responses):
        assert manager.storage_status("ABC123") == "Storage is 50% full."


def test_failed_command_raises_adb_error(manager: ADBManager) -> None:
    with patch("subprocess.run", return_value=completed(stderr="device offline", returncode=1)):
        with pytest.raises(ADBError, match="device offline"):
            manager._run(["devices"])


def test_invalid_apk_is_rejected(manager: ADBManager) -> None:
    assert "not found" in manager.install_apk("missing.apk").lower()


def test_package_validation(manager: ADBManager) -> None:
    assert "invalid" in manager.uninstall_app("not-a-package").lower()
