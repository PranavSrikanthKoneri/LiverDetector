"""Tests for demo/pipeline.py using the imaging mock (fast, no TotalSegmentator)."""
import json

import pytest

import demo.pipeline as pipeline
from imaging.mock import load_and_locate_mock

Q = {"age": 58, "male": 1, "bmi": 33.0, "waist_cm": 112.0, "diabetes": 2, "drinks_week": 2.0}
FAKE_FAT = {"status": "ok", "fat_pct": 27.0, "steatosis": True,
            "texture": {"contrast": 1.0, "homogeneity": 0.5, "entropy": 3.0}}


@pytest.fixture
def mock_imaging(monkeypatch):
    monkeypatch.setattr(pipeline, "load_and_locate", lambda zip_path: load_and_locate_mock())
    monkeypatch.setattr(pipeline, "measure_liver", lambda img: FAKE_FAT)


def test_pipeline_json_serializable(mock_imaging):
    r = pipeline.run_pipeline("unused.zip", Q)
    json.dumps(r)  # must not raise: FastAPI returns this as-is
    assert set(r) == {"imaging", "risk", "projection", "recommendation", "disclaimer"}
    assert r["imaging"]["status"] == "ok"
    assert len(r["projection"]["typical"]) == len(r["projection"]["slower"]) == 21


def test_pipeline_uses_fat_when_available(mock_imaging, monkeypatch):
    monkeypatch.setattr(pipeline, "measure_liver", lambda img: FAKE_FAT)
    r = pipeline.run_pipeline("unused.zip", Q)
    assert r["imaging"]["fat_pct"] == 27.0
    assert any("fat" in p and "27%" in p for p in r["recommendation"]["points"])
    assert any("doctor" in p for p in r["recommendation"]["points"])


def test_bad_questionnaire_fails_before_imaging(monkeypatch):
    def boom(zip_path):
        raise AssertionError("imaging should not run on invalid input")
    monkeypatch.setattr(pipeline, "load_and_locate", boom)
    with pytest.raises(ValueError):
        pipeline.run_pipeline("unused.zip", {**Q, "age": 5})


@pytest.mark.parametrize("p, tier", [(0.0, "low"), (0.099, "low"), (0.10, "intermediate"),
                                     (0.249, "intermediate"), (0.25, "high"), (1.0, "high")])
def test_risk_tiers(p, tier):
    assert pipeline.risk_tier(p) == tier


@pytest.mark.parametrize("p", [0.02, 0.15, 0.6])
@pytest.mark.parametrize("liver", [FAKE_FAT, {"status": "pending", "fat_pct": None, "steatosis": None}])
def test_recommendation_safety_rules(p, liver):
    rec = pipeline.recommend({"stage": "F0-F1", "probs": [1 - p, p, 0, 0], "p_ge_F2": p}, liver)
    text = " ".join([rec["headline"], *rec["points"]]).lower()
    assert "doctor" in text and rec["disclaimer"]
    for banned in ("medication", "medicine", "drug", "diagnos", "you have fibrosis", "cirrhosis"):
        assert banned not in text
