# Texture measurement quality checks

The pipeline now writes `texture_quality.json` alongside the existing fat and
texture summaries. It checks whether texture measurements are numerically usable
and sensitive to small preprocessing changes. It does **not** classify liver
health, fibrosis, motion artifacts, diagnostic scan quality, or lesion types.

## What was built and evaluated

The official [CHAOS v1.03 training archive](https://zenodo.org/records/3431873)
was downloaded and its MD5 verified as `df21053002a1cc86df918a87da3b2c19`.
All 20 training MRI patients were used. Ground-truth liver label 63 was matched
to each in-phase DICOM by filename in the geometry-sorted volume. The five largest
liver slices per patient supplied 100 numerical slice evaluations. No segmentation
model was run for this reference build.

The numerical reference ships in `imaging/resources/chaos_texture_qc_v1.json`;
your friend does not need to download CHAOS or run 20 GPU segmentations to use it.
The reference contains derived numbers only, with dataset attribution and license.
It is an engineering stress-test context, not a clinically labelled quality dataset.

## Method

- Resample each 2D image to a 2.0 mm in-plane grid using linear interpolation and
  its mask using nearest-neighbor interpolation. Do not interpolate across slices.
- Compute the existing 32-bin, per-ROI p1/p99 GLCM measurements with a 6 mm
  erosion margin. These standardized features are stored separately from the
  existing native-grid texture summary; fat computation is unchanged.
- For boundary sensitivity, repeat with 4 mm and 8 mm erosion margins.
- For spacing sensitivity, repeat from the original image at 1.8 mm and 2.2 mm,
  keeping the erosion radius at 6 mm.
- For each feature compute the largest symmetric relative change
  `2 * abs(variant - baseline) / max(abs(variant) + abs(baseline), 1e-12)`.
  Patient sensitivity is the maximum over all features and selected slices.

The engineering review triggers are: constant ROI intensity, fewer than 128
valid standardized ROI pixels, fewer than 100 pixel pairs in any direction, or
symmetric relative sensitivity above 0.25. These values are fixed prototype
settings, **not thresholds trained or clinically validated on CHAOS**. They were
not tuned to make the three existing patients pass. Invalid inputs or failed
perturbation measurements propagate an `invalid` patient status.

Status meanings:

| Status | Meaning |
|---|---|
| `no_flags_detected` | None of these specific checks fired. |
| `review_required` | Inspect the listed flags, affected slices and overlays. |
| `invalid` | At least one required measurement could not be evaluated. |

A sensitivity percentile compares the amount of preprocessing sensitivity with
other CHAOS patients, using one observation per patient and excluding both the
same patient ID and identical image fingerprint. It requires at least 10 other
usable records and does not change the status. Higher means more sensitive in
this reference, not more diseased. No tissue-feature normal ranges are reported.

This purpose differs from `imaging.texture_reference`, which attempts tightly
matched acquisition comparisons of raw texture features. Missing scanner-model
fields block that older comparison, but need not block per-scan numerical QC.
No scanner metadata is invented. Resampling is not full harmonization: slice
thickness, acquisition, interpolation effects, slice selection, vessels, mask
accuracy and expert-vs-model masks can still change the results. The tests do not
establish noise tolerance, motion detection or test-retest repeatability.

## Observed results

On expert CHAOS masks: 15 patients had no flags; 5 required review; none were
invalid. These are results of the prototype rules, not labelled ground-truth
quality classes or sensitivity/specificity estimates.

On the existing saved GPU masks (all 15 original texture slice measurements were
also reproduced before QC):

| Patient | Status | Maximum boundary change | Maximum spacing change | Other reference patients |
|---|---|---:|---:|---:|
| 1 | no_flags_detected | 6.81% | 20.84% | 19 |
| 2 | no_flags_detected | 10.28% | 19.78% | 19 |
| 5 | no_flags_detected | 4.19% | 22.89% | 19 |

Changes above are symmetric relative differences, not fat percentages. The
expert-mask result for patient 1 differs from its saved-model-mask QC result;
reference masks and selected slices differ. This illustrates why a QC status
must not be presented as an intrinsic diagnosis of the patient.

## Friend's instructions: existing results, no GPU rerun

Activate the environment used for the previous successful runs, then:

```powershell
git switch segmentation-math
git pull --ff-only
```

Create `texture_patients.json` in the repository (use the real paths on that
computer; use forward slashes in JSON). Keep canonical dataset IDs:

```json
{
  "cases": [
    {"case_id": "chaos_1", "zip_path": "C:/data/chaos_patient1.zip", "results_dir": "C:/results/texture_patient1"},
    {"case_id": "chaos_2", "zip_path": "C:/data/chaos_patient2.zip", "results_dir": "C:/results/texture_patient2"},
    {"case_id": "chaos_5", "zip_path": "C:/data/chaos_patient5.zip", "results_dir": "C:/results/texture_patient5"}
  ]
}
```

```powershell
python -m imaging.chaos_texture_qc check texture_patients.json --out debug/texture_quality_three.json
```

This reads original DICOMs and saved selected masks, verifies the old measurements,
and writes all three QC reports and reference comparisons to one JSON. Send that
JSON back. No additional package or GPU inference is required in the existing
environment. Do not use screenshot intensities in place of the original DICOMs.

Future `python -m imaging.analyze ... --device cuda:0 ...` runs automatically
produce `texture_quality.json`. `scripts/run_texture_cohort.py` also now finishes
with the QC comparison; it no longer blocks QC because scanner-model tags are
blank. There is no need to run this GPU cohort script to rebuild the reference.

## Rebuild reference from expert annotations

Extract the official training archive, then:

```powershell
python -m imaging.chaos_texture_qc build --mr-root "C:/data/Train_Sets/MR" --out debug/chaos_reference_full.json
```

The builder produces full slice diagnostics as well as patient summaries. The
shipped reference omits slice diagnostics to keep the numerical artifact small.
The CLI verifies structure and labels; verify the downloaded archive against the
published checksum separately. It does not certify arbitrary folders as original
CHAOS data.
