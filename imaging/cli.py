"""Debug CLI: run load_and_locate on a zip and save PNG previews.

    python -m imaging.cli path/to/case.zip --out debug/
    python -m imaging.cli case.zip --out debug/ --ground data/chaos/.../T1DUAL/Ground

Each preview shows the in-phase slice, the TotalSegmentator liver outline
(green) and the box sent to MedSAM (red). With --ground (CHAOS PNG masks),
the Dice overlap with the ground-truth liver is printed too.
"""
import argparse
import os
import tempfile

import cv2
import numpy as np

from imaging.load import _unzip, find_ip_op_pair, load_and_locate, scan_series

# CHAOS MR ground truth: liver pixels are ~63 (range 55-70).
CHAOS_LIVER_RANGE = (55, 70)


def to_uint8(img: np.ndarray) -> np.ndarray:
    lo, hi = np.percentile(img, (1, 99))
    return (np.clip((img - lo) / max(hi - lo, 1e-6), 0, 1) * 255).astype(np.uint8)


def save_preview(ip_slice, mask_slice, box, path, gt_slice=None) -> None:
    rgb = cv2.cvtColor(to_uint8(ip_slice), cv2.COLOR_GRAY2BGR)
    contours, _ = cv2.findContours(mask_slice.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(rgb, contours, -1, (0, 255, 0), 1)             # green: TS mask
    if gt_slice is not None:
        gt_contours, _ = cv2.findContours(gt_slice.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        cv2.drawContours(rgb, gt_contours, -1, (255, 255, 0), 1)    # cyan: ground truth
    x0, y0, x1, y1 = box
    cv2.rectangle(rgb, (x0, y0), (x1, y1), (0, 0, 255), 1)          # red: box
    rgb = cv2.resize(rgb, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(path, rgb)


def load_chaos_ground(zip_path: str, ground_dir: str) -> np.ndarray:
    """CHAOS liver ground truth stacked in the same z order as our ip volume.

    CHAOS names each PNG after its in-phase DICOM file, so we re-run pairing to
    get the sorted in-phase file list and map each file to its PNG.
    """
    with tempfile.TemporaryDirectory() as tmp:
        _unzip(zip_path, tmp)
        ip_group, _ = find_ip_op_pair(scan_series(tmp))
        names = [os.path.splitext(os.path.basename(f))[0] for f in ip_group["files"]]
    slices = []
    for name in names:
        png = cv2.imread(os.path.join(ground_dir, name + ".png"), cv2.IMREAD_GRAYSCALE)
        if png is None:
            raise FileNotFoundError(f"no ground-truth PNG for {name}")
        lo, hi = CHAOS_LIVER_RANGE
        slices.append(((png >= lo) & (png <= hi)).astype(np.uint8))
    return np.stack(slices)


def dice(a: np.ndarray, b: np.ndarray) -> float:
    return 2 * float((a & b).sum()) / max(float(a.sum() + b.sum()), 1.0)


def main() -> None:
    ap = argparse.ArgumentParser(description="Run imaging stage on a DICOM zip and save previews.")
    ap.add_argument("zip_path")
    ap.add_argument("--out", default="debug/")
    ap.add_argument("--ground", help="CHAOS T1DUAL/Ground folder for a Dice check (optional)")
    args = ap.parse_args()

    r = load_and_locate(args.zip_path)
    print(f"ip/op shape (z,y,x): {r['ip'].shape}, spacing (z,y,x) mm: "
          f"{tuple(round(s, 2) for s in r['spacing'])}")
    print(f"liver voxels: {int(r['ts_mask'].sum())}")
    print(f"liver_slices: {r['liver_slices']}")
    for s in r["liver_slices"]:
        print(f"  slice {s}: box {r['boxes'][s]}, liver area {int(r['ts_mask'][s].sum())} px")

    gt = None
    if args.ground:
        gt = load_chaos_ground(args.zip_path, args.ground)
        if gt.shape != r["ts_mask"].shape:
            print(f"ground truth shape {gt.shape} != mask shape {r['ts_mask'].shape}; skipping Dice")
            gt = None
        else:
            m = r["ts_mask"].astype(bool)
            g = gt.astype(bool)
            print(f"Dice vs CHAOS ground truth (whole volume): {dice(m, g):.3f}")
            # Report (never silently fix) orientation mismatches with the PNGs.
            flips = {"flip up-down": g[:, ::-1, :], "flip left-right": g[:, :, ::-1], "reverse z": g[::-1]}
            for name, gf in flips.items():
                d = dice(m, gf)
                if d > dice(m, g) + 0.05:
                    print(f"WARNING: Dice is higher ({d:.3f}) with ground truth {name}; "
                          f"orientation may not match the CHAOS PNGs")

    os.makedirs(args.out, exist_ok=True)
    for s in r["liver_slices"]:
        path = os.path.join(args.out, f"slice_{s:03d}.png")
        save_preview(r["ip"][s], r["ts_mask"][s], r["boxes"][s], path,
                     gt[s] if gt is not None else None)
    print(f"saved {len(r['liver_slices'])} previews to {args.out} "
          f"(green = TotalSegmentator, red = box{', cyan = ground truth' if gt is not None else ''})")


if __name__ == "__main__":
    main()
