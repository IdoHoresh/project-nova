"""Auto-calibrating fast-path OCR for the Unity 6 fork of 2048.

Calibration locates the 4x4 grid by edge-detecting the screenshot, finding
contours with aspect ratio ~1.0 at a plausible scale, and caching the
largest match's bounding box. Subsequent reads reuse the cached bbox until
the image dimensions change (e.g. emulator restarts at a new resolution),
at which point recalibration runs on the next frame.

Sampling strategy is per-channel median over the cell interior. Median is
chosen over mean because:

  1. The Unity 6 fork HUD ("Score: ..." / "Best: 0") overlays the row 0 /
     row 1 boundary, contaminating mean-sampling of row 0 cells.
  2. The black digit text inside non-empty tiles is a minority of pixels
     against a flat-color background; mean is biased by it, median is not.

Empirical comparison on the 9-fixture gauntlet: center-mean misclassified
16/144 cells (all in row 0 or text-heavy cells); median misclassifies 0/144.

The palette is derived empirically from clean tile samples on the Unity 6
fork build. The canonical 2048 web palette does NOT match this fork; do
not substitute it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np
import pytesseract  # type: ignore[import-untyped]
from PIL import Image

from nova_agent.perception.types import BoardState

# Unity 6 fork tile palette (RGB) -> tile value.
# Derived from per-channel median sampling of clean fixture cells.
# Re-derive here when adding higher-value tiles (16+) once they appear in
# live play; do not pull values from the canonical web palette.
_PALETTE: dict[tuple[int, int, int], int] = {
    (170, 166, 132): 0,  # empty (sandy olive)
    (138, 197, 170): 2,  # mint green
    (138, 179, 196): 4,  # sky blue
    (255, 181, 239): 8,  # pink (light magenta)
    (255, 124, 142): 16,  # salmon / coral (sampled live 2026-05-02)
    (125, 255, 150): 32,  # bright lime green (sampled live 2026-05-02)
    (231, 151, 247): 128,  # light purple (sampled live 2026-05-02; 64 still unsampled)
}


def _nearest_tile(rgb: tuple[int, int, int]) -> tuple[int, int]:
    """Return (tile_value, squared_distance_to_palette_match)."""
    best, best_d = 0, 10**9
    for ref_rgb, val in _PALETTE.items():
        d = sum((a - b) ** 2 for a, b in zip(ref_rgb, rgb))
        if d < best_d:
            best, best_d = val, d
    return best, best_d


@dataclass(frozen=True)
class BoardBBox:
    """Pixel coordinates of the 4x4 grid in the source image."""

    top: int
    left: int
    cell_size: int

    @property
    def width(self) -> int:
        return self.cell_size * 4


class CalibrationError(RuntimeError):
    """Raised when the fast path can't find the grid. Caller falls through to VLM perception."""


def calibrate_board_bbox(image: Image.Image) -> BoardBBox:
    """Find the 4x4 grid via OpenCV; no hardcoded coordinates."""
    arr = np.asarray(image.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 4
    )
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    img_area = arr.shape[0] * arr.shape[1]
    candidates: list[tuple[int, int, int, int]] = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w < 100 or h < 100:
            continue
        if abs(w - h) / max(w, h) > 0.05:
            continue
        area_frac = (w * h) / img_area
        if not 0.05 < area_frac < 0.65:
            continue
        candidates.append((w * h, x, y, w))

    if not candidates:
        raise CalibrationError("no square grid contour found at plausible scale")

    candidates.sort(reverse=True)
    _, x, y, w = candidates[0]
    cell_size = w // 4
    return BoardBBox(top=y, left=x, cell_size=cell_size)


def _read_score(image: Image.Image, bbox: BoardBBox) -> int:
    """Read the score HUD ('Score: 000000016') overlaid on the row 0 / row 1
    boundary band of the Unity 6 fork. White-text-on-mixed-tiles is a hard
    OCR target raw; we mask near-white pixels (text) into a binary image and
    invert before passing to Tesseract for stable digit extraction.

    Returns 0 when OCR finds no digit — matches the placeholder behavior of
    earlier ticks so retrieval never crashes on a transient HUD glitch.
    """
    boundary = bbox.top + bbox.cell_size
    band = image.crop((0, boundary - 25, image.width, boundary + 50))
    arr = np.asarray(band.convert("RGB"))
    gray = arr.min(axis=2)
    mask = (gray > 200).astype(np.uint8) * 255
    pad = 30
    padded = cv2.copyMakeBorder(mask, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
    inv = cv2.bitwise_not(padded)
    text = pytesseract.image_to_string(inv, config="--psm 7 -c tessedit_char_whitelist=0123456789")
    m = re.search(r"(\d+)", text)
    return int(m.group(1)) if m else 0


@dataclass
class BoardOCR:
    bbox: Optional[BoardBBox] = None
    _calibration_image_size: tuple[int, int] = field(default=(0, 0))

    def read(self, image: Image.Image) -> BoardState:
        size = image.size
        if self.bbox is None or size != self._calibration_image_size:
            self.bbox = calibrate_board_bbox(image)
            self._calibration_image_size = size

        bbox = self.bbox
        arr = np.asarray(image.convert("RGB"))
        margin = max(4, bbox.cell_size // 6)
        half = bbox.cell_size // 2 - margin
        grid = [[0] * 4 for _ in range(4)]
        for r in range(4):
            for c in range(4):
                cy = bbox.top + r * bbox.cell_size + bbox.cell_size // 2
                cx = bbox.left + c * bbox.cell_size + bbox.cell_size // 2
                patch = arr[cy - half : cy + half, cx - half : cx + half]
                med = np.median(patch.reshape(-1, 3), axis=0)
                rgb = (int(med[0]), int(med[1]), int(med[2]))
                value, _ = _nearest_tile(rgb)
                grid[r][c] = value
        score = _read_score(image, bbox)
        return BoardState(grid=grid, score=score)
