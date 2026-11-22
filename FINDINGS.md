# First assessment

On the enlarged contact sheet the median-cut surface reads mostly grey-brown. The sparse orange patches remain distinct in the Lab k-means and libimagequant tiles. The octree tiles have broad flat grey regions. Bayer introduces a regular stipple, especially visible in the octree tile. The fracture is faint even in the downsampled input, which limits what palette changes alone can recover.

Use unweighted Lab k-means with nearest mapping as the provisional reference for this source. It preserved the orange patches without introducing an ordered pattern. This assessment covers one seed and one scale. Mean CIE76 measures pixel reconstruction, while the horizontal Sobel error covers only one derivative direction.
