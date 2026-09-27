"""MedSAM segmentation helpers for Person 2.

Segmentation integration check (all kept slices):
    python -m imaging.analyze case.zip --checkpoint /path/to/medsam_vit_b.pth

Includes the project-specified Dixon calculation and exploratory GLCM texture.
"""

from pathlib import Path

import numpy as np


def load_medsam(checkpoint, device="cpu"):
    """Load pretrained ViT-B weights once, ready for inference."""
    from segment_anything import sam_model_registry

    checkpoint = Path(checkpoint).expanduser()
    if not checkpoint.is_file():
        raise FileNotFoundError(f"MedSAM checkpoint not found: {checkpoint}")
    return sam_model_registry["vit_b"](checkpoint=str(checkpoint)).to(device).eval()


def segment_slice(image, box, model):
    """Return a boolean (H, W) mask for one slice and an original-pixel xyxy box.

    Uses MedSAM's square 1024 preprocessing and box scaling. Normalization
    applies only to a copy for segmentation; original MRI intensities are kept.
    """
    import torch
    import torch.nn.functional as functional
    from skimage.transform import resize

    image = np.asarray(image, dtype=np.float32)
    if image.ndim != 2 or not np.isfinite(image).all():
        raise ValueError("Expected a finite, two-dimensional MRI slice")
    height, width = image.shape
    box = np.asarray(box, dtype=np.float32)
    if box.shape != (4,) or not np.isfinite(box).all():
        raise ValueError("Expected box [x_min, y_min, x_max, y_max]")
    x0, y0, x1, y1 = box
    if not (0 <= x0 < x1 < width and 0 <= y0 < y1 < height):
        raise ValueError("Box must have positive area and lie inside the image")

    # Window the MRI before uint8 conversion to avoid truncating raw intensities.
    lo, hi = np.percentile(image, (1, 99))
    if hi <= lo:
        lo, hi = float(image.min()), float(image.max())
    if hi <= lo:
        raise ValueError("Cannot segment a constant-intensity slice")
    gray = (np.clip((image - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8)
    rgb = np.repeat(gray[..., None], 3, axis=-1)
    resized = resize(
        rgb, (1024, 1024), order=3, preserve_range=True, anti_aliasing=True
    ).astype(np.uint8)
    normalized = resized.astype(np.float32)
    normalized = (normalized - normalized.min()) / max(
        float(normalized.max() - normalized.min()), 1e-8
    )
    device = next(model.parameters()).device
    tensor = torch.from_numpy(normalized).permute(2, 0, 1)[None].to(device)
    scaled_box = box / np.array([width, height, width, height]) * 1024
    box_tensor = torch.as_tensor(scaled_box, dtype=torch.float32, device=device)[None, None]

    with torch.inference_mode():
        embedding = model.image_encoder(tensor)
        sparse, dense = model.prompt_encoder(points=None, boxes=box_tensor, masks=None)
        logits, _ = model.mask_decoder(
            image_embeddings=embedding,
            image_pe=model.prompt_encoder.get_dense_pe(),
            sparse_prompt_embeddings=sparse,
            dense_prompt_embeddings=dense,
            multimask_output=False,
        )
        probabilities = functional.interpolate(
            torch.sigmoid(logits), size=(height, width),
            mode="bilinear", align_corners=False,
        )
    return (probabilities[0, 0] > 0.5).cpu().numpy()


def select_mask(candidate, ts_mask, box):
    """Choose MedSAM or the binary TotalSegmentator fallback, with diagnostics.

    These are provisional engineering heuristics, not validated accuracy or
    confidence measures. Agreement with TotalSegmentator is not ground truth.
    """
    from scipy import ndimage

    reference = np.asarray(ts_mask)
    if (reference.ndim != 2 or not np.isfinite(reference).all()
            or not np.isin(reference, [0, 1]).all() or not reference.any()):
        raise ValueError("Fallback must be a nonempty, finite binary 2D mask")
    reference = reference.astype(bool)
    height, width = reference.shape
    coords = np.asarray(box, dtype=float)
    if coords.shape != (4,) or not np.isfinite(coords).all():
        raise ValueError("Expected a finite xyxy box")
    x0, y0, x1, y1 = coords
    if not (0 <= x0 < x1 < width and 0 <= y0 < y1 < height):
        raise ValueError("Box must lie inside the fallback mask dimensions")
    report = {"source": "totalsegmentator", "reasons": [], "metrics": {}}
    candidate = np.asarray(candidate)
    if (candidate.shape != reference.shape or not np.isfinite(candidate).all()
            or not np.isin(candidate, [0, 1]).all()):
        report["reasons"].append("invalid_medsam_mask")
        return reference.copy(), report
    candidate = candidate.astype(bool)
    area = int(candidate.sum())
    if area == 0:
        report["reasons"].append("empty_medsam_mask")
        return reference.copy(), report

    dice = 2 * int((candidate & reference).sum()) / (area + int(reference.sum()))
    ratio = area / int(reference.sum())
    ys, xs = np.nonzero(candidate)
    inside = float(((xs >= x0) & (xs <= x1) & (ys >= y0) & (ys <= y1)).mean())
    labels, _ = ndimage.label(candidate, structure=np.ones((3, 3)))
    largest = float(np.bincount(labels.ravel())[1:].max() / area)
    report["metrics"] = {
        "dice_vs_ts": float(dice), "area_ratio_vs_ts": float(ratio),
        "inside_box_fraction": inside, "largest_component_fraction": largest,
    }
    if dice < 0.5:
        report["reasons"].append("low_overlap_with_ts")
    if not 0.5 <= ratio <= 2.0:
        report["reasons"].append("area_disagrees_with_ts")
    if inside < 0.9:
        report["reasons"].append("outside_prompt_box")
    if largest < 0.8:
        report["reasons"].append("fragmented_mask")
    if report["reasons"]:
        return reference.copy(), report
    report["source"] = "medsam"
    return candidate.copy(), report


def measure_fat_slice(ip_slice, op_slice, mask):
    """Return fat percentage and diagnostics from one selected liver mask.

    Inputs must be aligned magnitude MRI intensities on a comparable scale,
    not independently normalized display images. This implements the project's
    two-echo estimate, not a calibrated multi-echo PDFF measurement.
    Erosion uses a disk of radius 3 pixels (not millimeters).
    """
    from scipy.ndimage import binary_erosion

    ip = np.asarray(ip_slice, dtype=np.float64)
    op = np.asarray(op_slice, dtype=np.float64)
    mask = np.asarray(mask)
    if ip.ndim != 2 or ip.shape != op.shape or ip.shape != mask.shape:
        raise ValueError("IP, OP, and mask must have identical 2D shapes")
    if not np.isfinite(mask).all() or not np.isin(mask, [0, 1]).all():
        raise ValueError("Expected a finite binary liver mask")
    yy, xx = np.ogrid[-3:4, -3:4]
    eroded = binary_erosion(mask.astype(bool), structure=xx**2 + yy**2 <= 9,
                            border_value=0)
    eroded_pixels = int(eroded.sum())
    if eroded_pixels == 0:
        raise ValueError("No liver pixels remain after 3-pixel erosion")

    # Exclude nonfinite or invalid magnitude signals, including zero IP.
    valid = eroded & np.isfinite(ip) & np.isfinite(op) & (ip > 0) & (op >= 0)
    ip_values, op_values = ip[valid], op[valid]
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        fractions = (ip_values - op_values) / (2.0 * ip_values)
    finite = np.isfinite(fractions)
    fractions = fractions[finite]
    ip_values, op_values = ip_values[finite], op_values[finite]
    if fractions.size == 0:
        raise ValueError("No valid Dixon pixels remain inside the eroded liver mask")
    # Median first, clip second, then convert a fraction to percent: 0.10 -> 10%.
    median_fraction = float(np.median(fractions))
    fat_pct = float(np.clip(median_fraction, 0.0, 0.5) * 100.0)
    return fat_pct, {
        "eroded_pixels": eroded_pixels,
        "valid_pixels": int(fractions.size),
        "excluded_pixels": eroded_pixels - int(fractions.size),
        "unclipped_fat_pct": median_fraction * 100.0,
        "clipped_to_zero": bool(median_fraction < 0),
        "ip_median": float(np.median(ip_values)),
        "op_median": float(np.median(op_values)),
        "op_greater_than_ip_fraction": float(np.mean(op_values > ip_values)),
        # A clipped result must not silently look like a measured absence of fat.
        "warnings": ["negative_dixon_median_clipped_to_zero"] if median_fraction < 0 else [],
    }


def summarize_fat(slice_percentages):
    """Equally weight per-slice medians, then apply the strict >5% threshold."""
    values = np.asarray(slice_percentages, dtype=np.float64)
    if (values.ndim != 1 or values.size == 0 or not np.isfinite(values).all()
            or ((values < 0) | (values > 50)).any()):
        raise ValueError("Expected nonempty slice fat percentages in [0, 50]")
    fat_pct = float(values.mean())
    return {"fat_pct": fat_pct, "steatosis": bool(fat_pct > 5.0)}



def measure_texture_slice(ip_slice, mask):
    """Exploratory liver texture, not a staging or image-quality score.

    Symmetric 32-level GLCMs use only pairs whose endpoints are both inside
    the finite, nonnegative, radius-3-eroded liver ROI. Window to the ROI's
    1st/99th percentiles per slice, then equally average four directions.
    Native pixel offsets (dy, dx): (0,1), (1,1), (1,0), (1,-1).
    Entropy uses log2 (bits). Input arrays are never modified.
    """
    from scipy.ndimage import binary_erosion

    image = np.asarray(ip_slice, dtype=np.float64)
    mask = np.asarray(mask)
    if image.ndim != 2 or image.shape != mask.shape:
        raise ValueError("IP and mask must have identical 2D shapes")
    if not np.isfinite(mask).all() or not np.isin(mask, [0, 1]).all():
        raise ValueError("Expected a finite binary liver mask")
    yy, xx = np.ogrid[-3:4, -3:4]
    eroded = binary_erosion(mask.astype(bool), structure=xx**2 + yy**2 <= 9,
                            border_value=0)
    valid = eroded & np.isfinite(image) & (image >= 0)
    if not valid.any():
        raise ValueError("No valid texture pixels remain after erosion")
    values = image[valid]
    lo, hi = np.percentile(values, [1, 99])
    # Preserve rare variation if percentile bounds collapse; constant ROIs
    # correctly have contrast=0, homogeneity=1, entropy=0.
    if hi <= lo:
        lo, hi = values.min(), values.max()
    quantized = np.zeros(image.shape, dtype=np.int64)
    if hi > lo:
        quantized[valid] = np.minimum(
            (np.clip((values - lo) / (hi - lo), 0, 1) * 32).astype(np.int64), 31)
    offsets = [(0, 1), (1, 1), (1, 0), (1, -1)]
    h, w = image.shape
    delta2 = (np.arange(32)[:, None] - np.arange(32)[None, :])**2
    directions, pair_counts = [], []
    for dy, dx in offsets:
        y0, y1 = max(0, -dy), min(h, h - dy)
        x0, x1 = max(0, -dx), min(w, w - dx)
        a = (slice(y0, y1), slice(x0, x1))
        b = (slice(y0 + dy, y1 + dy), slice(x0 + dx, x1 + dx))
        pairs = valid[a] & valid[b]
        count = int(pairs.sum())
        if count == 0:
            raise ValueError("No valid texture pairs for one or more directions")
        ids = quantized[a][pairs] * 32 + quantized[b][pairs]
        counts = np.bincount(ids, minlength=32 * 32).reshape(32, 32)
        symmetric = counts + counts.T
        probability = symmetric / symmetric.sum()
        nonzero = probability[probability > 0]
        directions.append({
            "contrast": float(np.sum(probability * delta2)),
            "homogeneity": float(np.sum(probability / (1 + delta2))),
            "entropy": float(-np.sum(nonzero * np.log2(nonzero))),
        })
        pair_counts.append(count)
    return summarize_texture(directions), {
        "label": "exploratory", "input": "in_phase",
        "gray_levels": 32, "erosion_radius_pixels": 3,
        "window_method": "per_slice_roi_percentiles_1_99_with_minmax_fallback",
        "window_low": float(lo), "window_high": float(hi),
        "valid_pixels": int(valid.sum()),
        "excluded_pixels": int(eroded.sum() - valid.sum()),
        "offsets_dy_dx": [list(offset) for offset in offsets],
        "pair_counts": pair_counts, "symmetric": True,
        "entropy_units": "bits", "direction_aggregation": "equal_mean",
        "warnings": ["constant_intensity_roi"] if hi <= lo else [],
    }


def summarize_texture(slice_features):
    """Equal mean of directional or slice features; no disease thresholds."""
    names = ("contrast", "homogeneity", "entropy")
    if not slice_features:
        raise ValueError("Expected nonempty texture measurements")
    values = np.asarray([[row[name] for name in names] for row in slice_features],
                        dtype=np.float64)
    if not np.isfinite(values).all():
        raise ValueError("Texture measurements must be finite")
    return dict(zip(names, map(float, values.mean(axis=0))))

def main():
    """Check kept liver slices; save candidate/selected masks and diagnostics."""
    import argparse
    import cv2
    import json

    from imaging.cli import to_uint8
    from imaging.load import load_and_locate

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip_path")
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--out", default="debug/medsam_patient1")
    args = parser.parse_args()

    model = load_medsam(args.checkpoint, args.device)
    inputs = load_and_locate(args.zip_path)
    slices = inputs["liver_slices"]
    if not slices:
        raise ValueError("Loader returned no liver slices")
    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)
    reports = {}
    slice_percentages = []
    slice_textures = []
    for idx in slices:
        image, box = inputs["ip"][idx], inputs["boxes"][idx]
        print(f"Running MedSAM on slice {idx}, box {box}", flush=True)
        candidate = segment_slice(image, box, model)
        mask, report = select_mask(candidate, inputs["ts_mask"][idx], box)
        report["selected_pixels"] = int(mask.sum())
        try:
            fat_pct, counts = measure_fat_slice(image, inputs["op"][idx], mask)
        except ValueError as exc:
            # Do not silently drop a kept slice or substitute a zero measurement.
            raise ValueError(f"Cannot measure fat on slice {idx}: {exc}") from exc
        report["fat_pct"] = fat_pct
        report["fat_measurement"] = counts
        texture, texture_details = measure_texture_slice(image, mask)
        report["texture"] = texture
        report["texture_measurement"] = texture_details
        slice_textures.append(texture)
        slice_percentages.append(fat_pct)
        reports[str(idx)] = report
        np.save(output / f"medsam_{idx:03d}.npy", candidate)
        np.save(output / f"mask_{idx:03d}.npy", mask)
        preview = cv2.cvtColor(to_uint8(image), cv2.COLOR_GRAY2BGR)
        for outline, color in (
            (inputs["ts_mask"][idx], (0, 255, 0)),
            (candidate, (0, 255, 255)),
        ):
            contours, _ = cv2.findContours(
                outline.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            cv2.drawContours(preview, contours, -1, color, 1)
        x0, y0, x1, y1 = box
        cv2.rectangle(preview, (x0, y0), (x1, y1), (0, 0, 255), 1)
        preview = cv2.resize(preview, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
        path = output / f"comparison_{idx:03d}.png"
        if not cv2.imwrite(str(path), preview):
            raise OSError(f"Could not save preview: {path}")
        print(f"Slice {idx}: {json.dumps(report)}", flush=True)
    (output / "quality_report.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")
    summary = summarize_fat(slice_percentages)
    (output / "fat_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    texture_summary = {"texture": summarize_texture(slice_textures),
                       "label": "exploratory", "slice_aggregation": "equal_mean",
                       "slices": [int(idx) for idx in slices]}
    (output / "texture_summary.json").write_text(
        json.dumps(texture_summary, indent=2), encoding="utf-8")
    print(f"Exploratory texture: {json.dumps(texture_summary)}")
    print(f"Fat summary: {json.dumps(summary)}")
    print(f"Saved masks and quality_report.json to {output}")
    print("Previews: yellow = MedSAM candidate; green = TotalSegmentator; red = box")


if __name__ == "__main__":
    main()
