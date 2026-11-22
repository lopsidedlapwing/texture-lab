"""Generate reproducible pairs of 32×32 textures and indexed PNGs."""

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter


def run(output, count, seed, colours):
    rng = np.random.default_rng(seed)
    output.mkdir(parents=True, exist_ok=False)
    records = []
    figures = []
    for index in range(count):
        noise = gaussian_filter(rng.normal(size=(32, 32, 3)), (1, 1, 0), mode="wrap")
        pixels = np.uint8(255 * (noise - noise.min()) / np.ptp(noise))
        original = Image.fromarray(pixels)
        indexed = original.quantize(colors=colours)
        names = [f"{index:04d}-{kind}.png" for kind in ("source", "indexed")]
        for name, image in zip(names, (original, indexed), strict=True):
            image.save(output / name, compress_level=1)
            with Image.open(output / name) as reopened:
                if reopened.mode != image.mode:
                    raise ValueError(f"PNG mode changed in {name}")
                np.testing.assert_array_equal(
                    reopened.convert("RGB"), image.convert("RGB")
                )
        difference = pixels.astype(float) - np.asarray(indexed.convert("RGB"))
        mse = float(np.mean(difference**2))
        records.append(
            {
                "source": names[0],
                "indexed": names[1],
                "seed": seed,
                "sample": index,
                "palette_limit": colours,
                "rgb_mse": mse,
            }
        )
        images = " ".join(
            f'<img src="{name}" alt="{name}" width="96">' for name in names
        )
        figures.append(
            f"<figure>{images}<figcaption>#{index} · MSE {mse:.2f}</figcaption></figure>"
        )
    (output / "records.json").write_text(json.dumps(records, indent=2))
    with (output / "records.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=records[0])
        writer.writeheader()
        writer.writerows(records)
    (output / "index.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>Texture comparison</title>'
        "<style>main{display:flex;flex-wrap:wrap}figure{margin:.5em}img{image-rendering:pixelated}</style>"
        "<h1>Texture comparison</h1><p>Source (left) and quantised (right). Error is mean squared RGB difference.</p>"
        "<main>" + "\n".join(figures) + "</main>"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="new run directory")
    parser.add_argument("--count", type=int, default=128)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--colours", type=int, default=8)
    args = parser.parse_args()
    if args.count < 1 or args.seed < 0 or not 2 <= args.colours <= 256:
        parser.error("use a positive count, nonnegative seed and 2–256 colours")
    run(args.output, args.count, args.seed, args.colours)
