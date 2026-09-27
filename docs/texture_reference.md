# Exploratory texture reference comparison

This adds a cohort comparison of the existing liver-only contrast, homogeneity,
and entropy measurements. It does not diagnose texture disease, fibrosis, or
normality. Fat measurements and their 0–50% clipping remain unchanged.

## Data and GPU run

Use the official [CHAOS training data](https://zenodo.org/records/3431873).
Download `CHAOS_Train_Sets.zip` (890.8 MB), extract it, and locate `Train_Sets/MR`.
There are 20 training MR patients; only T1DUAL is used here. Do not mix the test
set into this workflow. No clinical disease labels are supplied by this workflow.

On the friend's GPU computer, activate the same environment used successfully
for the three patient runs, then run from the repository root (PowerShell).
Replace the two example absolute paths with the actual locations:

```powershell
git switch segmentation-math
git pull --ff-only
python scripts/prepare_texture_cohort.py "C:/data/Train_Sets/MR" --out data/texture_cohort
python scripts/run_texture_cohort.py data/texture_cohort/manifest.json --checkpoint "C:/MedSAM/work_dir/MedSAM/medsam_vit_b.pth"
```

The preparation script packages T1 images and writes a portable manifest. The
runner first checks acquisition metadata for every case and stops before inference
if no patient can reach the reference count. It then requires CUDA, processes
patients sequentially, and reuses completed
texture outputs on restart. The comparison rechecks every saved measurement
against the original DICOM and selected mask, without rerunning segmentation.
For a new complete rerun, use a fresh output directory. Incomplete or incompatible
saved outputs produce an error instead of silently being accepted.

Outputs:

- `data/texture_cohort/results/chaos_*/`: masks, overlays, fat and texture summaries.
- `data/texture_cohort/comparison/reference_records.json`: verified features and acquisition metadata.
- `data/texture_cohort/comparison/texture_comparisons.json`: per-patient reference comparisons.

Send back the two comparison JSONs and each patient's quality report, texture
summary, and overlays for review. Original DICOMs need not be sent again.

## Interpretation and limits

Each patient is excluded from their own reference group. Duplicate case IDs or
identical image volumes are rejected. Manifest IDs must identify unique patients;
renaming another scan from the same person does not create an independent sample.
Each patient contributes one equal-slice-mean feature vector, not five independent
samples. Slice minima/maxima describe variation, not confidence intervals.

Comparison requires matching manufacturer, scanner model and scanning sequence;
field strength, echo time, repetition time, flip angle and physical voxel spacing
must meet the conservative tolerances in `imaging/texture_reference.py`. Missing
metadata excludes a comparison. This screen is not full protocol harmonization.
The native-pixel GLCM method and preprocessing must also match.

At least 10 compatible *other* patients are required before reporting midrank
percentiles, reference median and interquartile range. This is an engineering
reporting floor, not a validated clinical sample size. Even all 20 CHAOS cases may
leave too few compatible patients. In that case, `insufficient_reference_data`
and null comparison fields are the correct outputs; do not loosen the screen
just to obtain a label. More matched data or a separately evaluated harmonization
method would be needed.

A percentile says where a measurement falls in this selected cohort. It does not
mean healthy/abnormal, disease probability, or a diagnostic reference interval.
A clinically meaningful classifier needs patient-level disease labels and
independent validation. These comparison outputs are separate from the existing
measurement API and are not yet connected to an application report UI.

## Saved-result check

For a manifest listing original zip paths and existing GPU result directories:

```powershell
python -m imaging.texture_reference manifest.json --out debug/texture_reference
```

The available patients 1, 2 and 5 were checked locally without model inference.
All 15 slice measurements reproduced. None had compatible other patients under
the acquisition screen, so all three correctly returned insufficient reference
data with no percentile or disease classification.

The three available exports have blank manufacturer and scanner-model fields,
which alone prevents eligibility. They also differ in voxel spacing. The full
dataset has not been processed or established as a usable reference cohort.
The preflight may therefore stop the full batch; this is a known data limitation,
not a reason to rerun segmentation or invent scanner metadata.
