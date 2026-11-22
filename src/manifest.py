"""Index completed studies. Paths in the manifest are relative to outputs/."""

import json
import struct
from pathlib import Path


def asset(root, path):
    path.resolve().relative_to(root.resolve())
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.relative_to(root).as_posix()


def generate(root):
    variants = []
    for record in sorted(root.rglob("results.json")):
        folder = record.parent
        data = json.loads(record.read_text())
        for row in data["rows"]:
            name = row["name"]
            # Old results encoded method, weight and dither in the filename.
            method, _, dither = name.rpartition("-")
            algorithm = row.get("algorithm", method.rpartition("-")[0])
            albedo = folder / row.get("albedo", f"{name}.png")
            normal = folder / row.get("normal", f"{name}-normal.png")
            path = asset(root, albedo)
            with albedo.open("rb") as stream:
                header = stream.read(24)
            if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
                raise ValueError(f"Invalid PNG: {albedo}")
            experiment = folder.relative_to(root).as_posix()
            variants.append(
                {
                    "id": f"{experiment}/{name}",
                    "experiment": experiment,
                    "name": name,
                    "albedo": path,
                    "normal": asset(root, normal)
                    if "normal" in row or normal.exists()
                    else None,
                    "source": asset(root, folder / row.get("source", "source.png")),
                    "algorithm": algorithm,
                    "dither": row.get("dither", dither),
                    "resolution": struct.unpack(">II", header[16:24]),
                    "palette": row["palette"],
                    "record": asset(root, record),
                    "config": data["config"],
                    "metrics": {
                        k: v for k, v in row.items() if isinstance(v, (int, float))
                    },
                }
            )
    if len({v["id"] for v in variants}) != len(variants):
        raise ValueError("Duplicate variant ID")
    (root / "manifest.json").write_text(
        json.dumps({"variants": variants}, indent=2) + "\n"
    )
    return variants


if __name__ == "__main__":
    generate(Path("outputs"))
