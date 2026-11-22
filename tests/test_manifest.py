import json
from pathlib import Path

import pytest
from PIL import Image

from src.manifest import generate


def test_manifest_discovers_nested_studies_and_maps(tmp_path):
    folder = tmp_path / "series" / "slab"
    folder.mkdir(parents=True)
    for name in ["source", "weighted-lab-4-nearest", "surface-normal"]:
        Image.new("RGB", (16, 8)).save(folder / f"{name}.png")
    row = {
        "name": "weighted-lab-4-nearest",
        "palette": [[0, 0, 0]],
        "normal": "surface-normal.png",
    }
    record = folder / "results.json"
    record.write_text(json.dumps({"config": {}, "rows": [row]}))
    (variant,) = generate(tmp_path)
    (saved,) = json.loads((tmp_path / "manifest.json").read_text())["variants"]
    assert saved["resolution"] == [16, 8]
    assert variant["algorithm"] == "weighted-lab" and variant["dither"] == "nearest"
    assert Path(variant["normal"]).parts == ("series", "slab", "surface-normal.png")
    (folder / "surface-normal.png").unlink()
    with pytest.raises(FileNotFoundError):
        generate(tmp_path)
