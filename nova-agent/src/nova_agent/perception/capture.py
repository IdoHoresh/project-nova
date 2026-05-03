import hashlib
import io
import subprocess
import time

from PIL import Image
import structlog

log = structlog.get_logger()


class Capture:
    """ADB-based screen capture."""

    def __init__(self, *, adb_path: str, device_id: str | None):
        self.adb_path = adb_path
        self.device_id = device_id

    def grab(self) -> Image.Image:
        args = [self.adb_path]
        if self.device_id:
            args += ["-s", self.device_id]
        args += ["exec-out", "screencap", "-p"]
        log.debug("capture.grab", args=args)
        result = subprocess.run(args, capture_output=True, timeout=5.0)
        if result.returncode != 0:
            raise RuntimeError(f"adb screencap failed: {result.stderr!r}")
        return Image.open(io.BytesIO(result.stdout)).convert("RGB")

    def grab_stable(
        self,
        *,
        poll_interval_s: float = 0.05,
        timeout_s: float = 0.6,
    ) -> Image.Image:
        """Capture once the screen is visually static (§3.9 visual stability check).

        Replaces the prior hardcoded ~300ms post-swipe wait. Loop captures
        50ms apart, exits when two consecutive frames are pixel-identical
        (or near-identical via byte hash). Hard cap at timeout_s, then
        force-read + log — better to OCR a slightly-moving frame than to
        block forever on emulator lag.
        """
        prev_hash: str | None = None
        deadline = time.monotonic() + timeout_s
        last_img: Image.Image | None = None

        while time.monotonic() < deadline:
            img = self.grab()
            h = hashlib.blake2s(img.tobytes(), digest_size=16).hexdigest()
            if prev_hash is not None and h == prev_hash:
                return img
            prev_hash = h
            last_img = img
            time.sleep(poll_interval_s)

        log.warning("capture.grab_stable.timeout", timeout_s=timeout_s)
        assert last_img is not None
        return last_img

    @staticmethod
    def boards_differ(a: Image.Image, b: Image.Image) -> bool:
        """Cheap pixel-diff used by the action executor for no-op detection (§3.9)."""
        ha = hashlib.blake2s(a.tobytes(), digest_size=16).digest()
        hb = hashlib.blake2s(b.tobytes(), digest_size=16).digest()
        return ha != hb

    @staticmethod
    def to_vlm_bytes(image: Image.Image, *, max_side: int = 512) -> bytes:
        """Downscale + optimize for VLM transmission. Required — see plan §6.6.

        A raw 1080×2400 emulator screenshot encoded as PNG and sent on every
        move would obliterate the $80 budget in days. 2048 is a high-contrast
        grid; a 512-px-max-side image is more than enough for the VLM to read
        digits and reason. Always run via thumbnail (LANCZOS) + optimize=True.
        """
        thumb = image.copy()
        thumb.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        thumb.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
