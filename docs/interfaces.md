load_and_locate(zip_path) -> {
  "ip": np.ndarray,   # in-phase volume
  "op": np.ndarray,   # opposed-phase volume
  "liver_slices": [int],
  "boxes": {slice_idx: [x_min, y_min, x_max, y_max]},
  "ts_mask": np.ndarray,  # TotalSegmentator mask (fallback)
  "spacing": (z, y, x)   # voxel size in mm
}

segment_and_measure(ip, op, liver_slices, boxes, ts_mask) -> {
  "masks": {slice_idx: np.ndarray},
  "fat_pct": float, "steatosis": bool,
  "texture": {"contrast": float, "homogeneity": float, "entropy": float}
}

predict_stage(q: {"age","male","bmi","waist_cm","diabetes","drinks_week"}) -> {
  "stage": "F0-F1"|"F2"|"F3"|"F4", "probs": [float x4],
  "p_ge_F2": float   # probability of significant fibrosis (F2 or worse)
}
# q types: age int, male 0/1, bmi float, waist_cm float|None,
#          diabetes 0=no 1=borderline 2=yes, drinks_week float

project(stage, years, slow: bool) -> {"stage_value": float, "low": float, "high": float,
  "years_per_stage": float, "source": str}   # stage_value 0.5 (F0-F1) .. 4.0 (capped)

summarize(all_results) -> {"text": str}   # LLM

Integration layout: these Python packages now live under backend/. Install the
repository with `python -m pip install -e .` to keep the imports above available.

HTTP demo contract:
  POST /api/analyze
  multipart fields: file (DICOM ZIP), patient (JSON string with q above)
  returns demo.pipeline.run_pipeline's JSON object:
    imaging, risk, projection, recommendation, disclaimer
  GET /api/health -> {"status": "ok"}

segment_and_measure also accepts keyword-only checkpoint, device, spacing (z,y,x),
and model. Defaults use MEDSAM_CHECKPOINT and MEDSAM_DEVICE. Its extra outputs are
quality_report, texture_quality, and candidates. The pipeline preserves these
diagnostics and encodes selected-mask/grayscale previews as PNG data URLs instead
of returning NumPy arrays. imaging.warnings reports fat clipping; texture_quality
contains measurement-stability flags, not disease severity. Imaging is not an
input to the questionnaire model. LLM summarize remains unimplemented; the demo
uses rule-based recommendation text.
