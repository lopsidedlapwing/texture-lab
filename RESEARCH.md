# Methods in the first comparison

All variants share one box-filtered 64×64 input. The source combines correlated aggregate, a mottled iron-coloured region and a narrow dark fracture. Median cut and fast octree use Pillow. pngquant supplies the libimagequant palette and its own no-dither PNG as a separate baseline. Lab k-means fits CIELAB centres, converts them to sRGB, then uses the same RGB mapping as the other extracted palettes. Sharing the mapper isolates palette construction. The PNG from pngquant retains its native mapper.

The Bayer variant perturbs all RGB channels with the same 4×4 threshold before nearest-colour mapping. Floyd–Steinberg diffuses RGB error left to right. The follow-up weights warm input texels fourfold during k-means fitting. The warm-output diagnostic uses Lab a* > 6, a proxy for reddish material.

References

- [Pillow quantisation API](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.quantize)
- [libimagequant](https://pngquant.org/lib/)
- [scikit-learn k-means objective and sample weights](https://scikit-learn.org/stable/modules/clustering.html#k-means)
