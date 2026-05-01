from unittest.mock import patch, MagicMock
import pytest
from nova_agent.action.adb import ADB, SwipeDirection


@patch("nova_agent.action.adb.subprocess.run")
def test_swipe_up_invokes_correct_command(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout=b"", stderr=b"")
    adb = ADB(adb_path="adb", device_id="emulator-5554", screen_w=1080, screen_h=2400)
    adb.swipe(SwipeDirection.UP)
    args = mock_run.call_args[0][0]
    assert "swipe" in args
    # `adb shell input swipe x1 y1 x2 y2 duration_ms` → trailing args are
    # [x1, y1, x2, y2, duration]. Swipe-up starts near bottom (high y1) and
    # ends near top (low y2), so y1 > y2.
    y1, y2 = int(args[-4]), int(args[-2])
    assert y1 > y2


@patch("nova_agent.action.adb.subprocess.run")
def test_swipe_failure_raises(mock_run):
    mock_run.return_value = MagicMock(returncode=1, stdout=b"", stderr=b"adb error")
    adb = ADB(adb_path="adb", device_id="emulator-5554", screen_w=1080, screen_h=2400)
    with pytest.raises(RuntimeError):
        adb.swipe(SwipeDirection.LEFT)
