"""Tests for the ADB action wrapper.

The Unity 6 fork of 2048 (`com.idohoresh.nova2048`) ignores `adb shell input
swipe` events — its input layer only listens for keyboard / DPAD keycodes.
The ADB wrapper therefore translates each `SwipeDirection` to the matching
`KEYCODE_DPAD_*` and sends `input keyevent <code>`.
"""

from unittest.mock import MagicMock, patch

import pytest

from nova_agent.action.adb import ADB, SwipeDirection

# Android KeyEvent constants (frameworks/base/core/java/android/view/KeyEvent.java).
KEYCODE_DPAD_UP = 19
KEYCODE_DPAD_DOWN = 20
KEYCODE_DPAD_LEFT = 21
KEYCODE_DPAD_RIGHT = 22


@pytest.mark.parametrize(
    "direction,keycode",
    [
        (SwipeDirection.UP, KEYCODE_DPAD_UP),
        (SwipeDirection.DOWN, KEYCODE_DPAD_DOWN),
        (SwipeDirection.LEFT, KEYCODE_DPAD_LEFT),
        (SwipeDirection.RIGHT, KEYCODE_DPAD_RIGHT),
    ],
)
@patch("nova_agent.action.adb.subprocess.run")
def test_swipe_sends_dpad_keyevent(mock_run, direction, keycode):
    mock_run.return_value = MagicMock(returncode=0, stdout=b"", stderr=b"")
    adb = ADB(adb_path="adb", device_id="emulator-5554", screen_w=1080, screen_h=2400)
    adb.swipe(direction)
    args = mock_run.call_args[0][0]
    assert "keyevent" in args
    assert args[-1] == str(keycode)


@patch("nova_agent.action.adb.subprocess.run")
def test_swipe_failure_raises(mock_run):
    mock_run.return_value = MagicMock(returncode=1, stdout=b"", stderr=b"adb error")
    adb = ADB(adb_path="adb", device_id="emulator-5554", screen_w=1080, screen_h=2400)
    with pytest.raises(RuntimeError):
        adb.swipe(SwipeDirection.LEFT)
