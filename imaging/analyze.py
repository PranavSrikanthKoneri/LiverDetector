"""MedSAM segmentation helpers for Person 2.

Single-slice integration check:
    python -m imaging.analyze case.zip --checkpoint /path/to/medsam_vit_b.pth

The measurement pipeline will be added after this integration check.
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


def main():
    """Check one real loader slice; save raw mask and comparison preview."""
    import argparse
    import cv2

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
    idx = slices[len(slices) // 2]
    image, box = inputs["ip"][idx], inputs["boxes"][idx]
    print(f"Running MedSAM on slice {idx}, box {box}", flush=True)
    mask = segment_slice(image, box, model)

    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)
    np.save(output / f"mask_{idx:03d}.npy", mask)
    preview = cv2.cvtColor(to_uint8(image), cv2.COLOR_GRAY2BGR)
    for outline, color in (
        (inputs["ts_mask"][idx], (0, 255, 0)),
        (mask, (0, 255, 255)),
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
    print(f"MedSAM mask: {mask.shape}, {int(mask.sum())} labeled pixels")
    print(f"Saved {path} (yellow: MedSAM; green: TotalSegmentator; red: box)")


if __name__ == "__main__":
    main()
