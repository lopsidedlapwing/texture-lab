"""Controlled palette comparisons on a shared concrete source."""

import argparse
import csv
import json
import os
import subprocess
from importlib.metadata import version
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, sobel
from skimage.color import lab2rgb, rgb2lab
from sklearn.cluster import KMeans

BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]])


def concrete(size, seed):
    rng = np.random.default_rng(seed)

    def field(scale):
        layer = gaussian_filter(rng.normal(size=(size, size)), scale, mode="wrap")
        return layer / layer.std()

    grain = 12 * field(0.45) + 18 * field(1.6) + 9 * field(12)
    base = np.array([134, 132, 124]) + grain[..., None]
    rust = (field(11) > 1.15) & (field(1.3) > 0.1)
    base[rust] += [31, -18, -33]
    image = Image.fromarray(np.uint8(np.clip(base, 0, 255)))
    draw = ImageDraw.Draw(image)
    y = size // 3
    for x in range(0, size, 4):
        yy = y + int(rng.integers(-3, 4))
        draw.line((x, y, x + 4, yy), fill=(52, 48, 44), width=2)
        y = yy
    return image


def palette(image, method, k, weight, seed, folder):
    if method == "lab-kmeans":
        pixels = np.asarray(image).reshape(-1, 3)
        lab = rgb2lab(pixels.reshape(-1, 1, 3)).reshape(-1, 3)
        weights = np.where(pixels[:, 0].astype(float) - pixels[:, 2] > 25, weight, 1)
        model = KMeans(k, n_init=4, random_state=seed).fit(lab, sample_weight=weights)
        return np.uint8(np.rint(lab2rgb(model.cluster_centers_[None])[0] * 255))
    if method == "libimagequant":
        target = folder / "pngquant-baseline.png"
        subprocess.run(
            [
                "pngquant",
                "--force",
                "--nofs",
                str(k),
                "--output",
                str(target),
                str(folder / "input.png"),
            ],
            check=True,
        )
        with Image.open(target) as p:
            return np.array(p.getpalette(), dtype=np.uint8).reshape(-1, 3)[:k]
    p = image.quantize(
        k,
        method={
            "median": Image.Quantize.MEDIANCUT,
            "octree": Image.Quantize.FASTOCTREE,
        }[method],
    )
    return np.array(p.getpalette(), dtype=np.uint8).reshape(-1, 3)[:k]


def render(image, colours, mode):
    rgb = np.asarray(image, dtype=float)
    if mode == "bayer4":
        y, x = np.indices(rgb.shape[:2])
        rgb += ((BAYER[y % 4, x % 4] + 0.5) / 16 - 0.5)[..., None] * 32
    indices = np.zeros(rgb.shape[:2], dtype=np.uint8)
    if mode == "floyd":
        height, width = indices.shape
        for y, x in np.ndindex(indices.shape):
            i = np.argmin(np.sum((colours - rgb[y, x]) ** 2, axis=1))
            indices[y, x] = i
            error = rgb[y, x] - colours[i]
            for dy, dx, w in [(0, 1, 7), (1, -1, 3), (1, 0, 5), (1, 1, 1)]:
                if y + dy < height and 0 <= x + dx < width:
                    rgb[y + dy, x + dx] += error * w / 16
    else:
        indices[:] = np.argmin(
            np.sum((rgb[:, :, None, :] - colours) ** 2, axis=-1), axis=-1
        )
    result = Image.fromarray(indices)
    result.putpalette(colours.flatten().tolist())
    return result


def study(cfg, folder, report):
    folder.mkdir(parents=True, exist_ok=True)
    report.mkdir(parents=True, exist_ok=True)
    source = concrete(cfg["source_size"], cfg["seed"])
    source.save(folder / "source.png")
    image = source.resize((cfg["size"],) * 2, Image.Resampling.BOX)
    image.save(folder / "input.png")
    ref = rgb2lab(np.asarray(image))
    rows = []
    for method in cfg["methods"]:
        for weight in cfg["rarity_weights"] if method == "lab-kmeans" else [1]:
            colours = palette(
                image, method, cfg["colours"], weight, cfg["seed"], folder
            )
            for mode in cfg["dithers"]:
                result = render(image, colours, mode)
                name = f"{method}-{weight}-{mode}"
                result.save(folder / f"{name}.png")
                lab = rgb2lab(np.asarray(result.convert("RGB")))
                rows.append(
                    {
                        "name": name,
                        "algorithm": method,
                        "dither": mode,
                        "weight": weight,
                        "mean_delta_e": float(
                            np.linalg.norm(ref - lab, axis=-1).mean()
                        ),
                        "edge_mae": float(
                            np.abs(
                                sobel(ref[..., 0], axis=1) - sobel(lab[..., 0], axis=1)
                            ).mean()
                        ),
                        "warm_fraction": float(np.mean(lab[..., 1] > 6)),
                        "lightness_range": float(np.ptp(lab[..., 0])),
                        "palette": colours.tolist(),
                        "counts": np.bincount(
                            np.asarray(result).ravel(), minlength=len(colours)
                        ).tolist(),
                    }
                )
    (folder / "results.json").write_text(
        json.dumps(
            {
                "config": cfg,
                "versions": {
                    p: version(p)
                    for p in [
                        "numpy",
                        "scipy",
                        "Pillow",
                        "scikit-learn",
                        "scikit-image",
                    ]
                },
                "rows": rows,
            },
            indent=2,
        )
    )
    with (folder / "metrics.csv").open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "name",
                "mean_delta_e",
                "edge_mae",
                "warm_fraction",
                "lightness_range",
            ],
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)
    names = ["input"] + [r["name"] for r in rows]
    sheet = Image.new("RGB", (4 * 180, ((len(names) + 3) // 4) * 156), "#222222")
    canvas = ImageDraw.Draw(sheet)
    for i, name in enumerate(names):
        x, y = (i % 4) * 180, (i // 4) * 156
        with Image.open(folder / f"{name}.png") as tile:
            sheet.paste(
                tile.convert("RGB").resize((128, 128), Image.Resampling.NEAREST), (x, y)
            )
        canvas.text((x, y + 130), name)
    sheet.save(report / "comparison.png")
    rel = os.path.relpath(folder, report)
    (report / "index.html").write_text(
        f'<!doctype html><meta charset=utf-8><title>Concrete comparison</title><h1>Concrete comparison</h1><p><a href="{rel}/source.png">Full source</a> · <a href="{rel}/metrics.csv">Metrics</a></p><img src="comparison.png" alt="Labelled palette and dither comparisons">'
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    study(
        json.loads(args.config.read_text()),
        Path("outputs") / args.config.stem,
        Path("reports"),
    )
    if __package__:
        from .manifest import generate
    else:
        from manifest import generate

    generate(Path("outputs"))
