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
