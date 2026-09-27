# tabular: fibrosis-stage risk from the questionnaire (Person 3)

`tabular.predict.predict_stage(q)` estimates liver-fibrosis stage probabilities
from six questionnaire answers. `tabular.progression.project()` projects the
stage forward in time using published population rates.

**The model does not use imaging.** NHANES has no MRI, so there is no training
data linking fat % or texture to fibrosis. The app shows imaging results next
to this prediction, not inside it.

## Contract

```python
predict_stage({"age": 55, "male": 1, "bmi": 31.0, "waist_cm": 104.0,  # waist may be None
               "diabetes": 2,          # 0 no, 1 borderline, 2 yes
               "drinks_week": 3.0})
# -> {"stage": "F0-F1", "probs": [0.940, 0.014, 0.035, 0.011], "p_ge_F2": 0.060}

project("F2", years=10, slow=False)
# -> {"stage_value": 3.41, "low": 2.70, "high": 4.0, "years_per_stage": 7.1,
#     "source": "Singh et al. 2015; population average, not a personal prediction"}
```

Invalid input raises `ValueError` with a readable message.
`tabular.mock` has `predict_stage_mock` / `project_mock` with the same shapes.

## Data and label

- **NHANES 2017–2018** (cycle J): DEMO, BMX, DIQ, ALQ, LUX, BIOPRO, CBC,
  merged on SEQN. `tabular/data.py` downloads them to `data/nhanes/`
  (gitignored).
- **Inclusion:** age ≥ 18, complete elastography exam (`LUAXSTAT == 1`),
  IQR/median < 0.30. That leaves 9,254 → 5,856 → 4,746 people. NHANES
  "complete" exams already meet the IQR rule.
- **Label:** liver stiffness `LUXSMED` in kPa (Eddowes et al. 2019 cutoffs).
  `LUXCAPM` (fat) is not used.

| Stage | LSM | n | % |
|---|---|---|---|
| F0-F1 | < 8.2 kPa | 4,291 | 90.4 |
| F2 | 8.2 – 9.7 | 165 | 3.5 |
| F3 | 9.7 – 13.6 | 170 | 3.6 |
| F4 | ≥ 13.6 | 120 | 2.5 |

- **Features:** `age` (clipped at 80, the NHANES top-code), `male`, `bmi`,
  `waist_cm`, `diabetes` (DIQ010), and `drinks_week`.
  `drinks_week` is days/year from ALQ121 × drinks/day from ALQ130, divided by 52.
  The ALQ121 frequency codes are mapped to the midpoints of their codebook ranges
  (see `ALQ121_DAYS_PER_YEAR` in `data.py`), and never-drinkers count as 0.

## Model

XGBoost `multi:softprob` (300 trees, depth 3, learning rate 0.05, no class
weights), saved as `tabular/risk_model.joblib`. Metrics are also in
`tabular/model_card.json`.

```bash
python -m tabular.train      # 5-fold CV + NFS baseline, saves model + card (~6 s)
python -m tabular.validate   # external validation on NHANES 2021-2023
python -m pytest tests/test_tabular.py
```

## Results

| AUROC | Ours: 5-fold CV, 2017–18 | Ours: external, 2021–23 | NFS: 2017–18 | NFS: 2021–23 |
|---|---|---|---|---|
| ≥ F2 | **0.774 ± 0.018** | **0.751** (0.730–0.769) | 0.731 | 0.696 |
| ≥ F3 | **0.795 ± 0.023** | **0.770** (0.746–0.793) | 0.754 | 0.721 |

- **NFS comparison:** the NAFLD Fibrosis Score needs bloodwork (AST, ALT,
  platelets, albumin, glucose), while ours uses only questionnaire answers.
  Each NFS number is compared with ours on the same people, those with complete
  bloodwork (n = 4,424 and 4,907). On those same people ours scores
  0.775 / 0.793 (2017–18) and 0.750 / 0.773 (2021–23).
- **External validation:** the 2021–23 check uses the saved model unchanged,
  on a later, independent NHANES sample (n = 5,526).
- **Calibration (2021–23):** the mean predicted P(≥F2) is 0.094, against an
  observed rate of 0.115, so the model slightly under-predicts.

## Limitations (read before using the output)

- **The `stage` field is almost always F0-F1.** With 90% of the data in F0-F1
  and no class weights, the most likely stage is F0-F1 for nearly everyone:
  CV recall is 0.00 for F2, 0.01 for F3 and 0.08 for F4. Show `p_ge_F2` and the
  probabilities, not just `stage`.
- **Alcohol shows the wrong direction.** Self-reported drinking is associated
  with *lower* predicted risk in NHANES. Likely reasons: people who quit because
  of illness are counted as non-drinkers, heavy drinking is under-reported, and
  heavy drinkers are rare. Do not tell users that drinking lowers risk.
- **Ranking, not diagnosis.** The model ranks risk moderately well (AUROC about
  0.75–0.80), but it is not a diagnosis.
- **Proxy label.** The label comes from elastography, a stand-in for
  biopsy-staged fibrosis.
- **Sample, not population.** NHANES survey weights are not applied, so the
  metrics describe the sample, not the US population.
- **NFS glucose.** NFS uses non-fasting serum glucose from the biochemistry panel.
- **Projection.** `project()` uses population-average rates (Singh et al. 2015:
  14.3 years per stage for NAFL, 7.1 for NASH). The CI values are marked to be
  verified against the paper.

## Mac setup

XGBoost needs OpenMP: `brew install libomp`. Without Homebrew, point it at
PyTorch's bundled copy for a session (PyTorch is installed by TotalSegmentator):

```bash
export DYLD_FALLBACK_LIBRARY_PATH=$PWD/.venv/lib/python3.11/site-packages/torch/lib
```
