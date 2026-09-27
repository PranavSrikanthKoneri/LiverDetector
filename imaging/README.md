# imaging: DICOM zip → liver slices and boxes (Person 1)

`imaging.load.load_and_locate(zip_path)` turns an uploaded zip of abdominal MRI
DICOMs into aligned in-phase/opposed-phase volumes plus liver locations for
MedSAM (Person 2).

## Output contract

```python
{
    "ip": np.ndarray,          # in-phase volume, float32, (z, y, x)
    "op": np.ndarray,          # opposed-phase volume, same shape/alignment as ip
    "liver_slices": list[int], # top 5 z-indices by liver area, sorted
    "boxes": dict[int, list[int]],  # slice -> [x_min, y_min, x_max, y_max], +5 px, clipped
    "ts_mask": np.ndarray,     # TotalSegmentator liver mask, uint8 0/1, same shape as ip
    "spacing": tuple,          # (z, y, x) voxel size in mm
}
```

Raises `ValueError` with a readable message if the zip has no DICOMs, has no
in/opposed-phase pair, or no liver is found.

`imaging.mock.load_and_locate_mock()` returns fake data in the same shape, for
building against before the real pipeline runs.

## How it works

1. Unzip into a temporary directory, which is deleted afterwards.
2. Read DICOM headers (technical tags only) and group slices by
   (SeriesInstanceUID, EchoTime). Some scanners store both echoes in one series.
3. Pick two T1 gradient-echo groups with identical geometry and different echo
   times: the **shorter TE is opposed-phase** and the **longer TE is in-phase**. If
   that fails, fall back to CHAOS-style `InPhase`/`OutPhase` folder names.
4. Read both with SimpleITK so ip, op and the mask share one voxel grid.
5. Run TotalSegmentator (`total_mr`, `roi_subset=["liver"]`, `fast=True`, with a
   full-resolution retry) on the in-phase image and resample the mask onto the
   ip grid (nearest neighbour).
6. Keep the 5 slices with the largest liver area. Each box is the mask extent
   plus 5 px.

## Run it

```bash
uv venv --python 3.11 .venv && uv pip install --python .venv/bin/python -r requirements.txt

# Debug previews: green = TotalSegmentator, red = box, cyan = ground truth
.venv/bin/python -m imaging.cli case.zip --out debug/
.venv/bin/python -m imaging.cli case.zip --out debug/ --ground path/to/T1DUAL/Ground  # + Dice

# Tests (the real-data test only runs if CHAOS_TEST_ZIP is set)
.venv/bin/python -m pytest tests/
CHAOS_TEST_ZIP=data/chaos_patient1.zip .venv/bin/python -m pytest tests/
```

To make a CHAOS test zip from the
[CHAOS dataset](https://zenodo.org/records/3431873) (`CHAOS_Train_Sets.zip`):

```bash
cd Train_Sets/MR/1/T1DUAL && zip -r ~/chaos_patient1.zip DICOM_anon
```

## Results (CHAOS MR T1DUAL, CPU, TotalSegmentator 2.18)

| Patient | Dice vs ground truth | Runtime |
|---|---|---|
| 1 | 0.916 | ~1 min |
| 2 | 0.909 | ~1 min |
| 5 | 0.868 | ~1 min |

The first run also downloads the TotalSegmentator MR weights (~280 MB).

## Privacy

Only technical tags are read: series UID/number/description, echo time,
geometry and sequence type. Patient name, ID and birth date are never read,
logged, saved or returned. Only in-memory arrays leave the function, and data
files (`*.zip`, `*.dcm`, `*.nii*`, `data/`, `debug/`) are gitignored.

## Known limitations

- Requires a **dual-echo T1 in/opposed-phase** series. Studies that only
  export Dixon water/fat images (e.g. GE "T1-WATER") or contrast MRA series are
  rejected with a clear error.
- The in/opposed-phase rule assumes the standard first echoes (e.g. 2.3/4.6 ms at
  1.5 T). Unusual multi-echo protocols may pair wrongly.
- Enhanced (multi-frame) DICOM files are not supported.
- If several valid pairs exist, the one with the most slices is used.
- Runtime is about 1 minute per case on CPU; a GPU is used automatically if one
  is available.
