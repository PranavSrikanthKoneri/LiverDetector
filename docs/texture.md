# Exploratory liver texture

`imaging.analyze.measure_texture_slice(ip_slice, mask)` returns three GLCM
features plus method diagnostics. The existing GPU CLI now writes
`texture_summary.json` and includes per-slice texture in `quality_report.json`.
`fat_summary.json` and its 0–50% clipping behavior remain unchanged.

These features describe brightness patterns. They are not fibrosis stages,
image-quality grades, or validated normal/abnormal scores.

## Method

- Use the original in-phase image and the selected MedSAM/fallback mask.
- Erode the mask with a disk of radius 3 native pixels. Exclude nonfinite and
  negative image values; accept zero intensity for texture.
- Window each slice using the valid ROI's 1st and 99th percentiles. If the
  bounds coincide, use its minimum and maximum. Quantize to 32 equal-width
  bins, with the upper endpoint in bin 31. Constant ROIs use bin 0 and emit
  a diagnostic warning.
- Count neighboring pairs at row/column offsets `(0,1)`, `(1,1)`, `(1,0)`,
  `(1,-1)`. Both pixels must be in the valid ROI; background and mask-boundary
  transitions never enter the GLCM. Zeroing background alone would not suffice.
- Symmetrize and normalize each directional GLCM separately. Compute contrast,
  homogeneity, and joint entropy; average features equally over directions,
  then equally over the selected slices. A direction with no pairs is an error,
  not a substituted zero.

For normalized matrix P, contrast is `sum(P[i,j]*(i-j)^2)`, homogeneity is
`sum(P[i,j]/(1+(i-j)^2))`, and entropy is `-sum(P[i,j]*log2(P[i,j]))` for
nonzero entries. Entropy is in bits. Contrast and homogeneity follow the
[scikit-image definitions](https://scikit-image.org/docs/stable/api/skimage.feature.html#skimage.feature.graycoprops);
our entropy explicitly uses base 2.

Higher contrast describes larger neighboring brightness differences; higher
homogeneity describes more similar neighboring brightness; higher entropy
indicates a more dispersed distribution of gray-level pairs. None implies
better/worse health or image quality by itself.

Native pixel size, per-slice normalization, scanner settings, noise, vessels,
and segmentation affect these values. No physical-spacing resampling or vessel
exclusion is performed. Do not compare values across protocols as calibrated
biomarkers. The diagonal offsets have sqrt(2) pixel distance, while the horizontal
and vertical offsets have one-pixel distance. Method settings and pair counts are
saved for reproducibility.

## Patient 5 check

Using the friend's saved masks on slices 17–21, without rerunning either model:
contrast 9.36753, homogeneity 0.443676, entropy 7.48821 bits. Existing per-slice
fat measurements reproduced unchanged. These are example outputs, not thresholds.

Run repository checks with `python -m pytest tests -q`. The ignored debug folder
contains independent research scripts/environments and is not part of this suite.
