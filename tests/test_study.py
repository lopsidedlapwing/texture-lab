import numpy as np
import pytest
from PIL import Image

from src.study import concrete, render


def test_source():
    a = concrete(64, 42)
    assert a.size == (64, 64)
    np.testing.assert_array_equal(a, concrete(64, 42))
    assert not np.array_equal(a, concrete(64, 43))


@pytest.mark.parametrize("mode", ["nearest", "bayer4", "floyd"])
def test_binary_palette_roundtrip(mode, tmp_path):
    colours = np.array([[0, 0, 0], [255, 255, 255]], dtype=np.uint8)
    ramp = np.tile(np.arange(256, dtype=np.uint8), (4, 1))
    image = Image.fromarray(ramp).convert("RGB")
    result = render(image, colours, mode)
    result.save(tmp_path / "tile.png")
    with Image.open(tmp_path / "tile.png") as loaded:
        assert loaded.mode == "P" and loaded.size == image.size
        assert len(loaded.getcolors()) == 2
        np.testing.assert_array_equal(loaded.convert("RGB"), result.convert("RGB"))
        np.testing.assert_array_equal(loaded, render(image, colours, mode))
    if mode == "nearest":
        np.testing.assert_array_equal(result, ramp >= 128)
