# LiverCast demo pipeline: handoff

Read this before changing `demo/pipeline.py`, whether you are a person or a
coding agent. It describes what is finished, what is pending, and the rules
that must keep holding.

## What the pipeline does

```
DICOM zip + questionnaire
  1. imaging.load.load_and_locate(zip)          Person 1  DONE
  2. imaging.analyze.segment_and_measure(...)   Person 2  PENDING  (hook: measure_liver)
  3. tabular.predict.predict_stage(q)           Person 3  DONE
  4. tabular.progression.project(stage, y, s)   Person 3  DONE
  5. recommend(risk, liver)                     Person 4  PLACEHOLDER rules
     summarize(result)  (LLM)                   Person 4  NOT STARTED
  -> one JSON-serializable dict (see "Output")
```

Run it on one case:

```bash
python -m demo.pipeline case.zip --questionnaire demo/example_questionnaire.json --out debug/result.json
python -m pytest tests/        # fast; mocks imaging, no data needed
```

`run_pipeline(zip_path, questionnaire)` is the function a FastAPI
`POST /analyze` handler should call. It validates the questionnaire first,
which is instant, before the imaging step, which takes about 1 minute on CPU.
A bad questionnaire therefore fails fast with a `ValueError`.

## Person 2: plugging in fat % (`segment_and_measure`)

1. Add `segment_and_measure(ip, op, liver_slices, boxes, ts_mask)` to
   `imaging/analyze.py` with the contract in `docs/interfaces.md`:
   `{"masks": {slice: ndarray}, "fat_pct": float, "steatosis": bool,
   "texture": {"contrast", "homogeneity", "entropy"}}`.
2. You don't need to edit anything else. `measure_liver()` in
   `demo/pipeline.py` imports it automatically, sets `status` to `"ok"`, and
   drops `masks` because arrays are not JSON. Until then `status` is
   `"pending"` and the fat values are `None`.
3. Acceptance check with the anonymised CHAOS test zips. The expected fat %
   values were measured with the `tasks.md` recipe on the TotalSegmentator
   mask; MedSAM results should be close.

   | Test zip | Expected fat % | Steatosis (>5%) |
   |---|---|---|
   | CHAOS MR patient 1 or 2 | ~0% (raw slightly negative, clipped) | no |
   | `LiverCast_test_patient33.zip` | ~11% | yes |
   | `LiverCast_test_patient32.zip` | ~23% | yes |
   | `LiverCast_test_patient5.zip` | ~27% | yes |

   The zips are not in git: medical images are gitignored. Ask Sahitha, or
   rebuild them from the public CHAOS dataset (see `imaging/README.md`).

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
  for almost everyone (see `tabular/README.md`).
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
    "status": "pending" | "ok",
    "fat_pct": float | null, "steatosis": bool | null,
    "texture": {"contrast", "homogeneity", "entropy"} | null
  },
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
  files; they are gitignored. The model files in `tabular/` are committed on
  purpose.
- **Wrong scan type:** an upload without an in-phase/opposed-phase T1 series
  raises a readable `ValueError`. Show that message to the user.
