"""Assemble a portable static site from locked Three.js modules and indexed results."""

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from manifest import generate

outputs = ROOT / "outputs"
variants = generate(outputs)
if not variants:
    raise SystemExit("No completed studies found in outputs/")
dest = ROOT / "dist"
dest.mkdir(exist_ok=True)
for name in ["index.html", "app.js", "scene.js", "style.css"]:
    shutil.copy2(ROOT / "viewer" / name, dest / name)
three = ROOT / "node_modules/three"
vendor = dest / "vendor"
vendor.mkdir(exist_ok=True)
for name in [
    "build/three.module.js",
    "build/three.core.js",
    "examples/jsm/controls/OrbitControls.js",
    "LICENSE",
]:
    shutil.copy2(three / name, vendor)
assets = {"manifest.json"}
for variant in variants:
    assets.update(
        variant[key] for key in ["albedo", "normal", "source", "record"] if variant[key]
    )
for name in sorted(assets):
    target = dest / "outputs" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(outputs / name, target)
print(f"Built {len(variants)} variants in {dest}")
