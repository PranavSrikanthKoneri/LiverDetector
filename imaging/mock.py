"""Fake output of load_and_locate() in the exact contract shape.

Lets teammates build against the imaging stage before the real pipeline
(DICOM -> TotalSegmentator) is ready. No real data involved.
"""
import numpy as np


def load_and_locate_mock(zip_path: str = "", seed: int = 0) -> dict:
    rng = np.random.default_rng(seed)
    z, y, x = 20, 256, 256

    # Fake liver: an ellipsoid in the upper-left of the image (patient's right).
    zz, yy, xx = np.mgrid[0:z, 0:y, 0:x]
    ellipsoid = ((zz - 10) / 7) ** 2 + ((yy - 110) / 60) ** 2 + ((xx - 90) / 70) ** 2 <= 1
    ts_mask = ellipsoid.astype(np.uint8)

    # In-phase: noisy background, brighter liver. Opposed-phase: liver ~10% darker
    # (i.e. some fat signal cancellation), so Person 2 gets a non-zero fat %.
    ip = rng.normal(100, 10, (z, y, x)).astype(np.float32)
    ip[ellipsoid] += 200
    op = ip.copy()
    op[ellipsoid] *= 0.9

    # Same selection rule as the real pipeline: top 5 slices by liver area.
    areas = ts_mask.sum(axis=(1, 2))
    liver_slices = sorted(int(i) for i in np.argsort(areas)[::-1][:5] if areas[i] > 0)

    boxes = {}
    for s in liver_slices:
        ys, xs = np.nonzero(ts_mask[s])
        boxes[s] = [
            max(int(xs.min()) - 5, 0), max(int(ys.min()) - 5, 0),
            min(int(xs.max()) + 5, x - 1), min(int(ys.max()) + 5, y - 1),
        ]

    return {
        "ip": ip,
        "op": op,
        "liver_slices": liver_slices,
        "boxes": boxes,
        "ts_mask": ts_mask,
        "spacing": (5.0, 1.5, 1.5),
    }
