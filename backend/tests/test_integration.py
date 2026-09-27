"""Exercise real measurement/serialization with model inference replaced only."""
import json
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app import main as api
from demo import pipeline
from imaging import analyze

Q = {"age": 58, "male": 1, "bmi": 33., "waist_cm": 112., "diabetes": 2, "drinks_week": 2.}


@pytest.fixture
def measured(monkeypatch):
    mask = np.zeros((1, 40, 40), dtype=np.uint8)
    mask[:, 5:35, 5:35] = 1
    ip = np.full(mask.shape, 100., dtype=np.float32)
    img = {"ip": ip, "op": ip * 1.02, "ts_mask": mask,
           "boxes": {0: [3, 3, 36, 36]}, "liver_slices": [0], "spacing": (5., 2., 2.)}
    monkeypatch.setenv("MEDSAM_CHECKPOINT", "unused")
    monkeypatch.setattr(pipeline, "load_and_locate", lambda path: img)
    monkeypatch.setattr(analyze, "load_medsam", lambda *args: object())
    monkeypatch.setattr(analyze, "segment_slice", lambda *args: mask[0].astype(bool))
    return img


def test_full_measurement_preserves_qc_clipping_and_previews(measured):
    result = pipeline.run_pipeline("unused.zip", Q)
    json.dumps(result, allow_nan=False)
    imaging = result["imaging"]
    assert imaging["status"] == "ok"
    assert imaging["fat_pct"] == 0
    assert imaging["warnings"] == ["negative_dixon_median_clipped_to_zero"]
    assert imaging["quality_report"]["0"]["fat_measurement"]["unclipped_fat_pct"] < 0
    assert imaging["texture_quality"]["quality"]["status"]
    assert imaging["masks"]["0"]["overlay"].startswith("data:image/png;base64,")
    assert any("clipping" in point for point in result["recommendation"]["points"])
    assert not any("little liver fat" in point for point in result["recommendation"]["points"])


def test_api_upload_cleanup_and_real_contract(measured, monkeypatch, tmp_path):
    checkpoint = tmp_path / "checkpoint.pth"
    checkpoint.touch()
    monkeypatch.setenv("MEDSAM_CHECKPOINT", str(checkpoint))
    seen = []
    def run(path, q):
        assert Path(path).read_bytes() == b"test zip"
        seen.append(Path(path))
        return pipeline.run_pipeline(path, q)
    monkeypatch.setattr(api, "run_pipeline", run)
    response = TestClient(api.app).post("/api/analyze", data={"patient": json.dumps(Q)},
                                        files={"file": ("scan.zip", b"test zip", "application/zip")})
    assert response.status_code == 200
    assert response.json()["imaging"]["quality_report"]
    assert response.json()["recommendation"]["alcohol_caveat"]["ranges"][1]["women"] == "8 or more drinks"
    assert not seen[0].exists()


@pytest.mark.parametrize("patient", ["not-json", "[]", json.dumps({**Q, "diabetes": True}), json.dumps({**Q, "age": 5})])
def test_api_rejects_questionnaire_before_inference(monkeypatch, patient):
    monkeypatch.setattr(api, "run_pipeline", lambda *args: pytest.fail("Inference must not run"))
    response = TestClient(api.app).post("/api/analyze", data={"patient": patient}, files={"file": ("scan.zip", b"x")})
    assert response.status_code == 422


def test_api_missing_model_configuration(monkeypatch):
    monkeypatch.delenv("MEDSAM_CHECKPOINT", raising=False)
    response = TestClient(api.app).post("/api/analyze", data={"patient": json.dumps(Q)}, files={"file": ("scan.zip", b"x")})
    assert response.status_code == 503
