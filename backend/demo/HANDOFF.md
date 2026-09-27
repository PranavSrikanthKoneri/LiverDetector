# LiverCast demo pipeline: handoff

Read this before changing `backend/demo/pipeline.py`, whether you are a person or a
coding agent. It describes what is finished, what is pending, and the rules
that must keep holding.

## What the pipeline does

```
DICOM zip + questionnaire
  1. imaging.load.load_and_locate(zip)          Person 1  DONE
  2. imaging.analyze.segment_and_measure(...)   Person 2  CONNECTED (fat, texture, diagnostics/QC)
  3. tabular.predict.predict_stage(q)           Person 3  DONE
  4. tabular.progression.project(stage, y, s)   Person 3  DONE
  5. recommend(risk, liver)                     Person 4  PLACEHOLDER rules
     summarize(result)  (LLM)                   Person 4  NOT STARTED
  -> one JSON-serializable dict (see "Output")
```

Run it on one case:

```bash
python -m demo.pipeline case.zip --questionnaire backend/demo/example_questionnaire.json --out debug/result.json
python -m pytest backend/tests/        # fast; mocks imaging, no data needed
```

`run_pipeline(zip_path, questionnaire)` is the function a FastAPI
`POST /api/analyze` handler calls. It validates the questionnaire first,
which is instant, before the imaging step, which takes about 1 minute on CPU.
A bad questionnaire therefore fails fast with a `ValueError`.

## Imaging connection

`backend/imaging/analyze.py` now exposes `segment_and_measure` and shares it with
its diagnostic CLI. Configure `MEDSAM_CHECKPOINT`, `MEDSAM_DEVICE` and MedSAM's
`PYTHONPATH` as shown in the root README. `measure_liver` passes real voxel spacing
and returns `status="ok"`, fat diagnostics, per-slice mask checks, exploratory
texture and texture stability QC. Missing configuration fails explicitly.

Array masks stay in process; the JSON `masks` field contains dimensions, selected
pixel counts, and actual grayscale/overlay PNG data URLs for the frontend.
Clipped-zero fat estimates carry a warning and are never described as absence
of fat. Texture `review_required` must remain visible.

Prior diagnostic runs: patients 1/2 produced zero after clipping negative values;
patient 5 about 26.71%; patient 33 about 11.11%. These are regression references,
not validated clinical ground truth or targets to force the output to match.

## Person 4: recommendation, LLM summary, frontend

`recommend()` is a **placeholder** built from simple rules. Replace or extend
it, for example by feeding the whole result dict to the LLM `summarize()`, but
keep these rules. `tests/test_pipeline.py::test_recommendation_safety_rules`
checks several of them.

- **Language and scope:** plain language, general lifestyle tips only, and
  always tell the user to see a doctor.
- **Forbidden content:** never name medications, and never diagnose. Say
  "chance of significant scarring", not "you have fibrosis".
- **Headline number:** lead with `risk["p_ge_F2"]` and `risk["tier"]`, **not**
  `risk["stage"]`. The stage is the single most likely class, which is F0-F1
  for almost everyone (see `backend/tabular/README.md`).
- **Alcohol:** never say or imply that drinking lowers risk. The model
  gives heavy drinkers lower risk because of an NHANES self-report artifact.
  "Limiting alcohol" as general advice is fine.
- **Imaging is not a model input:** show fat % next to the risk; it is not
  part of `predict_stage`, because NHANES has no MRI.
- **Disclaimer:** the "Not diagnostic" text (`DISCLAIMER`) must stay on
  screen.
- **LLM input:** send the LLM only numbers and tiers, never DICOM data or
  identifiers.

Risk tiers (`RISK_TIERS`) are cut-offs on `p_ge_F2`. The observed rates
below come from the independent NHANES 2021–2023 sample:

| Tier | p_ge_F2 | Share of people | Observed rate of ≥F2 |
|---|---|---|---|
| low | < 0.10 | 68.9% | 5.9% |
| intermediate | 0.10 – 0.25 | 22.4% | 18.7% |
| high | ≥ 0.25 | 8.7% | 37.9% |

**Frontend:** `projection.typical` and `projection.slower` each hold 21 points,
one per year from 0 to 20, for the slider and the Recharts band. Use
`stage_value` for the line and `low`/`high` for the shaded range. The
"slower-progression scenario" toggle switches from `typical` to `slower`.

## Output

```jsonc
{
  "imaging": {
    "liver_slices": [17, 18, 19, 20, 21],
    "boxes": {"17": [x0, y0, x1, y1], ...},     // keys are strings (JSON)
    "spacing_mm": [z, y, x],
    "status": "ok",
    "fat_pct": float | null, "steatosis": bool | null,
    "texture": {"contrast", "homogeneity", "entropy"},
    "warnings": [str], "quality_report": {"slice_index": {...}},
    "texture_quality": {...}, "texture_label": "exploratory",
    "masks": {"slice_index": {"width": int, "height": int, "liverPixels": int, "image": "PNG data URL", "overlay": "PNG data URL"}}
  },
  "alcohol_consumption": {"category": "low|elevated|critical", "label": str, "drinks_week": float, "sex_label": str, "model_independent": true, "ranges": [...], "range_note": str, "caveat": str},
  "risk": {"stage": "F0-F1", "probs": [4 floats], "p_ge_F2": float, "tier": "low|intermediate|high"},
  "projection": {
    "start_stage": "F0-F1", "source": "Singh et al. 2015; ...",
    "typical": [{"years": 0, "stage_value": 0.5, "low": ..., "high": ..., "years_per_stage": 7.1}, ...],
    "slower":  [... same, years_per_stage 14.3 ...]
  },
  "recommendation": {"tier": ..., "headline": str, "points": [str], "disclaimer": str},
  "disclaimer": str
}
```

## Pitfalls (each of these has already caused a problem once)

- **Script guard:** TotalSegmentator starts worker processes. Any script that
  calls `load_and_locate` must be a real `.py` file with an
  `if __name__ == "__main__":` guard. Running it from stdin or `python -` makes
  the workers loop forever. uvicorn/FastAPI is fine.
- **XGBoost on macOS** needs OpenMP: `brew install libomp`. Without Homebrew,
  run `export DYLD_FALLBACK_LIBRARY_PATH=$PWD/.venv/lib/python3.11/site-packages/torch/lib`
  first.
- **Runtime:** the first imaging run downloads the TotalSegmentator weights
  (about 280 MB). After that each case takes about 1 minute on CPU.
- **Data in git:** never commit DICOMs, zips, NIfTI files or NHANES `.xpt`
  files; they are gitignored. The model files in `backend/tabular/` are committed on
  purpose.
- **Wrong scan type:** an upload without an in-phase/opposed-phase T1 series
  raises a readable `ValueError`. Show that message to the user.

## Alcohol information in results

The backend returns `alcohol_consumption` separately from `risk` and
`recommendation`. `demo/alcohol.py` computes this informational category directly
from the submitted `male` and `drinks_week` values. It neither changes the
questionnaire nor injects a category into the trained model. The existing model
still receives its original inputs, including the existing drinks feature.

Project-defined categories: Low risk for women below 8 drinks/week and men below
15 (0–7 and 0–14 for whole drinks); Elevated at 8 and 15 respectively; Critical
at 20 or more for either sex. Critical overrides Elevated. Fractional averages
are compared directly with the cutoffs, without rounding. Invalid values raise
an error instead of defaulting to Low risk.

The frontend displays the backend category, submitted drink count and applicable
sex range in a separate results card in both dashboard views. The questionnaire
contains the original intake field but no category table or alcohol caveat.
These labels are project-defined information, not validated disease probabilities,
clinical severity categories or new model outputs. Low risk does not imply safe
consumption. No training or model-weight changes are involved.

The dashboard shows the main questionnaire risk percentage once; the summary
headline uses the tier without repeating the percentage.
