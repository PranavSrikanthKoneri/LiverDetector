"""predict_stage(): fibrosis-stage probabilities from questionnaire answers only.

Uses tabular/risk_model.joblib (trained by `python -m tabular.train`).
Imaging results (fat %, texture) are NOT inputs: NHANES has no MRI.
"""
import math
import os
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd

from tabular.data import FEATURES, STAGES

MODEL_PATH = os.path.join(os.path.dirname(__file__), "risk_model.joblib")
NHANES_MAX_AGE = 80  # NHANES top-codes age at 80


@lru_cache(maxsize=1)
def _model():
    return joblib.load(MODEL_PATH)


def _check_range(name, value, lo, hi):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or math.isnan(value):
        raise ValueError(f"{name} must be a number, got {value!r}")
    if not lo <= value <= hi:
        raise ValueError(f"{name} must be between {lo} and {hi}, got {value}")


def validate(q: dict) -> dict:
    """Check the questionnaire; returns a clean copy. Raises ValueError on bad input."""
    missing = [k for k in FEATURES if k not in q]
    if missing:
        raise ValueError(f"questionnaire is missing: {', '.join(missing)}")
    _check_range("age", q["age"], 18, 120)
    if q["male"] not in (0, 1) or isinstance(q["male"], bool):
        raise ValueError(f"male must be 0 or 1, got {q['male']!r}")
    _check_range("bmi", q["bmi"], 10, 100)
    if q["waist_cm"] is not None:
        _check_range("waist_cm", q["waist_cm"], 40, 250)
    if q["diabetes"] not in (0, 1, 2) or isinstance(q["diabetes"], bool):
        raise ValueError(f"diabetes must be 0 (no), 1 (borderline) or 2 (yes), got {q['diabetes']!r}")
    _check_range("drinks_week", q["drinks_week"], 0, 200)
    return {k: q[k] for k in FEATURES}


def predict_stage(q: dict) -> dict:
    q = validate(q)
    row = {**q, "age": min(q["age"], NHANES_MAX_AGE),
           "waist_cm": np.nan if q["waist_cm"] is None else q["waist_cm"]}
    x = pd.DataFrame([row], columns=FEATURES).astype(float)
    p = _model().predict_proba(x)[0].astype(float)
    p = p / p.sum()
    probs = [round(float(v), 6) for v in p]
    return {
        "stage": STAGES[int(np.argmax(p))],
        "probs": probs,
        "p_ge_F2": round(float(p[1:].sum()), 6),
    }
