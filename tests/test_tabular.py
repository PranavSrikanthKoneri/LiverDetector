"""Tests for the tabular stage (Person 3): contract shapes, validation, projection math.

Needs the committed tabular/risk_model.joblib (no NHANES download).
"""
import json

import pytest

from tabular.data import STAGES
from tabular.mock import predict_stage_mock, project_mock
from tabular.predict import predict_stage
from tabular.progression import project
from tabular.train import CARD_PATH

BASE = {"age": 50, "male": 1, "bmi": 30.0, "waist_cm": 102.0, "diabetes": 0, "drinks_week": 2.0}


def check_prediction(r):
    assert set(r) == {"stage", "probs", "p_ge_F2"}
    assert r["stage"] in STAGES
    assert len(r["probs"]) == 4 and all(isinstance(p, float) and 0 <= p <= 1 for p in r["probs"])
    assert sum(r["probs"]) == pytest.approx(1.0, abs=1e-4)
    assert r["p_ge_F2"] == pytest.approx(sum(r["probs"][1:]), abs=1e-4)


def check_projection(r):
    assert set(r) == {"stage_value", "low", "high", "years_per_stage", "source"}
    assert 0.5 <= r["low"] <= r["stage_value"] <= r["high"] <= 4.0
    assert isinstance(r["source"], str) and r["source"]


# ---- mocks

def test_mocks_match_contract():
    check_prediction(predict_stage_mock(BASE))
    check_projection(project_mock("F2", 10, slow=True))


# ---- predict_stage

def test_predict_stage_contract():
    r = predict_stage(BASE)
    check_prediction(r)
    assert r["stage"] == STAGES[r["probs"].index(max(r["probs"]))]


def test_waist_may_be_none():
    check_prediction(predict_stage({**BASE, "waist_cm": None}))


@pytest.mark.parametrize("bad", [
    {"age": 12}, {"age": "50"}, {"male": 2}, {"bmi": 5.0}, {"waist_cm": 10.0},
    {"diabetes": 3}, {"drinks_week": -1.0}, {"bmi": float("nan")},
])
def test_invalid_input_raises(bad):
    with pytest.raises(ValueError):
        predict_stage({**BASE, **bad})


def test_missing_key_raises():
    q = dict(BASE)
    del q["bmi"]
    with pytest.raises(ValueError, match="bmi"):
        predict_stage(q)


# ---- synthetic profiles: risk moves in the medically expected direction
# (alcohol is deliberately not tested: see tabular/README.md limitations)

@pytest.mark.parametrize("key, low, high", [
    ("diabetes", 0, 2), ("bmi", 22.0, 38.0), ("waist_cm", 80.0, 125.0), ("age", 30, 70),
])
def test_risk_increases_with_risk_factor(key, low, high):
    assert predict_stage({**BASE, key: high})["p_ge_F2"] > predict_stage({**BASE, key: low})["p_ge_F2"]


# ---- project

@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("slow", [True, False])
def test_project_contract_monotonic_and_capped(stage, slow):
    values = [project(stage, y, slow)["stage_value"] for y in range(0, 51, 5)]
    assert values == sorted(values)          # never goes down over time
    assert max(values) <= 4.0                # capped at F4
    for y in (0, 10, 20):
        check_projection(project(stage, y, slow))


def test_project_starts_at_current_stage():
    assert project("F0-F1", 0, True)["stage_value"] == 0.5
    assert project("F2", 0, False)["stage_value"] == 2.0


@pytest.mark.parametrize("stage", STAGES)
def test_slow_not_faster_than_fast(stage):
    for y in (5, 10, 20):
        assert project(stage, y, slow=True)["stage_value"] <= project(stage, y, slow=False)["stage_value"]


@pytest.mark.parametrize("args", [("F5", 10, True), ("F2", -1, True), ("F2", 10, "yes")])
def test_project_invalid_input_raises(args):
    with pytest.raises(ValueError):
        project(*args)


# ---- model card

def test_model_card_has_metrics():
    with open(CARD_PATH) as f:
        card = json.load(f)
    for key in ("features", "classes", "n_train", "class_counts", "cv_auroc_ge_F2", "cv_auroc_ge_F3",
                "nfs_auroc_ge_F2", "nfs_auroc_ge_F3", "n_nfs_subset", "label_source", "limitations"):
        assert key in card
    assert card["features"] == ["age", "male", "bmi", "waist_cm", "diabetes", "drinks_week"]
