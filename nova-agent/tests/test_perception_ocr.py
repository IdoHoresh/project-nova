"""Fixture-driven tests for the OCR fast path."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from PIL import Image

from nova_agent.perception.ocr import BoardOCR

FIXTURES = Path(__file__).parent / "fixtures"
EXPECTED: dict[str, dict] = yaml.safe_load((FIXTURES / "expected.yaml").read_text())


@pytest.mark.parametrize("name,exp", sorted(EXPECTED.items()))
def test_ocr_reads_known_boards(name: str, exp: dict) -> None:
    img = Image.open(FIXTURES / f"{name}.png").convert("RGB")
    ocr = BoardOCR()
    state = ocr.read(img)
    assert state.grid == exp["grid"], f"{name}: grid mismatch"


def test_ocr_recalibrates_when_image_size_changes() -> None:
    """R2 — auto-calibration must survive emulator-resolution changes."""
    big = Image.open(FIXTURES / "board_8.png").convert("RGB")
    small = big.resize((big.width // 2, big.height // 2), Image.LANCZOS)
    ocr = BoardOCR()
    state_big = ocr.read(big)
    state_small = ocr.read(small)
    expected = EXPECTED["board_8"]["grid"]
    assert state_big.grid == expected
    assert state_small.grid == expected, "OCR did not recalibrate after rescale"
