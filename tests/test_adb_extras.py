from __future__ import annotations

from pathlib import Path
from unittest.mock import patch
import subprocess

import pytest

from functions.adb_commands import ADBManager
from functions.adb_extras import ADBExtras


def completed(stdout: str = "", stderr: str = "", returncode: int = 0):
    return subprocess.CompletedProcess(["adb"], returncode, stdout=stdout, stderr=stderr)


@pytest.fixture
def extras() -> ADBExtras:
    return ADBExtras(ADBManager(adb_path="adb"))


def test_wireless_endpoint_rejects_invalid_port(extras: ADBExtras) -> None:
    with pytest.raises(ValueError, match="port"):
        extras.connect_wireless("192.168.1.5:70000")


def test_wireless_endpoint_rejects_missing_port(extras: ADBExtras) -> None:
    with pytest.raises(ValueError, match="host"):
        extras.connect_wireless("192.168.1.5")


def test_shell_command_requires_content(extras: ADBExtras) -> None:
    with pytest.raises(ValueError, match="Enter a command"):
        extras.execute_shell("   ")


def test_shell_command_uses_selected_device(extras: ADBExtras) -> None:
    with patch("subprocess.run", side_effect=[
        completed("List of devices attached\nABC123\tdevice\n"),
        completed("Pixel"),
    ]) as run:
        assert extras.execute_shell("getprop ro.product.model", "ABC123") == "Pixel"
    command = run.call_args_list[1].args[0]
    assert command[-2:] == ["shell", "getprop ro.product.model"]
    assert "-s" in command and "ABC123" in command


def test_push_requires_existing_local_file(extras: ADBExtras, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="does not exist"):
        extras.push_file(str(tmp_path / "missing.txt"), "/sdcard/Download/missing.txt")


def test_logcat_line_count_is_bounded(extras: ADBExtras) -> None:
    with pytest.raises(ValueError, match="between 1 and 10000"):
        extras.get_logcat(lines=10001)
