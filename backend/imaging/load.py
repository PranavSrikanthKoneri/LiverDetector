"""Person 1: DICOM zip -> in/opposed-phase volumes -> liver slices + boxes.

Privacy: only technical DICOM tags are read below (series UID, echo time,
geometry). Patient-identifying tags are never read, printed or returned.
"""
import os
import tempfile
import zipfile
from collections import defaultdict

import numpy as np
import pydicom
import SimpleITK as sitk

# Dual-echo T1 GRE echo times are a few ms; anything longer is T2/SE/etc.
MAX_DUAL_ECHO_TE_MS = 10.0
MIN_SLICES = 10


def _log(msg: str) -> None:
    print(f"[imaging] {msg}")


# ---------------------------------------------------------------- discovery

def _unzip(zip_path: str, dest: str) -> None:
    if not zipfile.is_zipfile(zip_path):
        raise ValueError(f"Upload is not a valid zip file: {os.path.basename(zip_path)}")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest)


def _read_header(path: str):
    """Technical header fields of one DICOM image, or None if not a usable image."""
    try:
        ds = pydicom.dcmread(path, stop_before_pixels=True, force=True)
    except Exception:
        return None
    needed = ("SeriesInstanceUID", "Rows", "Columns", "ImagePositionPatient", "ImageOrientationPatient")
    if not all(k in ds for k in needed):
        return None  # not an image slice (DICOMDIR, report, stray file, ...)
    orient = [float(v) for v in ds.ImageOrientationPatient]
    normal = np.cross(orient[:3], orient[3:])
    pos = np.array([float(v) for v in ds.ImagePositionPatient])
    te = ds.get("EchoTime")
    return {
        "path": path,
        "series_uid": str(ds.SeriesInstanceUID),
        "series_number": str(ds.get("SeriesNumber", "?")),
        "description": str(ds.get("SeriesDescription", "")),
        "sequence": str(ds.get("ScanningSequence", "")),
        "echo_time": float(te) if te not in (None, "") else None,
        "rows": int(ds.Rows),
        "cols": int(ds.Columns),
        "orient": tuple(round(v, 2) for v in orient),
        "slice_pos": float(np.dot(pos, normal)),  # position along the slice normal
        "folder": os.path.basename(os.path.dirname(path)).lower(),
    }


def scan_series(root: str) -> list:
    """Group all DICOM images under root by series and echo time.

    Some scanners store both echoes in one series, so (series, TE) is the key.
    Each group's files are sorted along the slice normal, ready for SimpleITK.
    """
    groups = defaultdict(list)
    for dirpath, _, files in os.walk(root):
        for name in files:
            h = _read_header(os.path.join(dirpath, name))
            if h is not None:
                te = round(h["echo_time"], 2) if h["echo_time"] is not None else None
                groups[(h["series_uid"], te)].append(h)

    out = []
    for (_, te), hs in groups.items():
        hs.sort(key=lambda h: h["slice_pos"])
        first = hs[0]
        out.append({
            "series_number": first["series_number"],
            "description": first["description"],
            "sequence": first["sequence"],
            "echo_time": te,
            "n": len(hs),
            "shape2d": (first["rows"], first["cols"]),
            "orient": first["orient"],
            "z_range": (hs[0]["slice_pos"], hs[-1]["slice_pos"]),
            "folder": first["folder"],
            "files": [h["path"] for h in hs],
        })
    return out


# ------------------------------------------------------------------ pairing

def _same_geometry(a: dict, b: dict, tol_mm: float = 1.0) -> bool:
    return (
        a["n"] == b["n"]
        and a["shape2d"] == b["shape2d"]
        and a["orient"] == b["orient"]
        and abs(a["z_range"][0] - b["z_range"][0]) <= tol_mm
        and abs(a["z_range"][1] - b["z_range"][1]) <= tol_mm
    )


def _describe(g: dict) -> str:
    return (f"series #{g['series_number']} '{g['description']}' "
            f"TE={g['echo_time']} ms, {g['n']} slices {g['shape2d'][0]}x{g['shape2d'][1]}")


def find_ip_op_pair(groups: list):
    """Return (in_phase_group, opposed_phase_group). Raises ValueError if none found.

    Rule: two T1 gradient-echo groups with identical geometry and different echo
    times. The SHORTER TE is opposed-phase, the LONGER TE is in-phase (true for
    the standard first echoes at 1.5 T and 3 T).
    Fallback: CHAOS-style folder names 'InPhase' / 'OutPhase'.
    """
    cands = [
        g for g in groups
        if g["echo_time"] is not None
        and g["echo_time"] < MAX_DUAL_ECHO_TE_MS
        and g["n"] >= MIN_SLICES
        and ("GR" in g["sequence"] or not g["sequence"])  # gradient echo (or tag missing)
    ]
    pairs = []
    for i, a in enumerate(cands):
        for b in cands[i + 1:]:
            if abs(a["echo_time"] - b["echo_time"]) > 0.5 and _same_geometry(a, b):
                op, ip = sorted((a, b), key=lambda g: g["echo_time"])
                pairs.append((ip, op))
    if pairs:
        ip, op = max(pairs, key=lambda p: p[0]["n"])  # most slices = best liver coverage
        _log(f"in-phase:      {_describe(ip)}")
        _log(f"opposed-phase: {_describe(op)}")
        _log("chosen by: same geometry, different echo times (shorter TE = opposed-phase)")
        return ip, op

    # Fallback: CHAOS dataset layout (T1DUAL/DICOM_anon/InPhase, .../OutPhase).
    ip = [g for g in groups if g["folder"] == "inphase"]
    op = [g for g in groups if g["folder"] in ("outphase", "opposedphase")]
    if len(ip) == 1 and len(op) == 1 and _same_geometry(ip[0], op[0]):
        _log(f"in-phase:      {_describe(ip[0])}")
        _log(f"opposed-phase: {_describe(op[0])}")
        _log("chosen by: folder names InPhase/OutPhase (CHAOS layout)")
        return ip[0], op[0]

    raise ValueError(
        "No in-phase / opposed-phase T1 pair found. The upload needs a dual-echo "
        "T1 gradient-echo (Dixon in/opposed-phase) MRI series of the abdomen."
    )


def read_volume(files: list) -> sitk.Image:
    """Read a sorted list of slice files as one 3D image (array order z, y, x)."""
    reader = sitk.ImageSeriesReader()
    reader.SetFileNames(files)
    return sitk.Cast(reader.Execute(), sitk.sitkFloat32)


# ------------------------------------------------------- liver localisation

def run_totalsegmentator(ip_img: sitk.Image, work_dir: str) -> sitk.Image:
    """Liver mask from TotalSegmentator (MR model), resampled onto the ip grid."""
    from totalsegmentator.python_api import totalsegmentator  # heavy import (torch)

    in_nii = os.path.join(work_dir, "ip.nii.gz")
    out_dir = os.path.join(work_dir, "ts")
    sitk.WriteImage(ip_img, in_nii)

    _log("running TotalSegmentator (task=total_mr, roi=liver); first run on CPU takes ~1 min")
    try:
        totalsegmentator(in_nii, out_dir, task="total_mr", roi_subset=["liver"], fast=True, quiet=True)
    except Exception as e:
        _log(f"fast mode failed ({e.__class__.__name__}), retrying at full resolution")
        totalsegmentator(in_nii, out_dir, task="total_mr", roi_subset=["liver"], quiet=True)

    mask = sitk.ReadImage(os.path.join(out_dir, "liver.nii.gz"))
    if mask.GetSize() != ip_img.GetSize():
        _log(f"mask size {mask.GetSize()} != image size {ip_img.GetSize()}, resampling")
    # Nearest-neighbour resample onto the exact ip grid (identity if already equal).
    return sitk.Resample(mask, ip_img, sitk.Transform(), sitk.sitkNearestNeighbor, 0, sitk.sitkUInt8)


def select_slices_and_boxes(mask: np.ndarray, n: int = 5, margin: int = 5):
    """Top-n z-slices by liver area (sorted), and a padded box per slice.

    Box format: [x_min, y_min, x_max, y_max] in pixel coords, clipped to the image.
    """
    _, h, w = mask.shape
    areas = mask.sum(axis=(1, 2))
    top = [int(i) for i in np.argsort(areas)[::-1][:n] if areas[i] > 0]
    slices = sorted(top)

    boxes = {}
    for s in slices:
        ys, xs = np.nonzero(mask[s])
        boxes[s] = [
            max(int(xs.min()) - margin, 0), max(int(ys.min()) - margin, 0),
            min(int(xs.max()) + margin, w - 1), min(int(ys.max()) + margin, h - 1),
        ]
    return slices, boxes


# ------------------------------------------------------------ public entry

def load_and_locate(zip_path: str) -> dict:
    """DICOM zip -> aligned in/opposed-phase volumes, liver mask, top slices and boxes.

    All arrays are (z, y, x). Raises ValueError with a readable message if the
    zip has no DICOMs, no in/opposed-phase pair, or no liver is found.
    """
    with tempfile.TemporaryDirectory(prefix="livercast_") as tmp:
        dicom_dir = os.path.join(tmp, "dicom")
        _unzip(zip_path, dicom_dir)

        groups = scan_series(dicom_dir)
        if not groups:
            raise ValueError("No DICOM images found in the uploaded zip.")
        _log(f"found {len(groups)} image series/echo groups")
        ip_group, op_group = find_ip_op_pair(groups)

        # Both volumes read by SimpleITK from sorted file lists -> same grid as the mask.
        ip_img = read_volume(ip_group["files"])
        op_img = read_volume(op_group["files"])
        if ip_img.GetSize() != op_img.GetSize():
            raise ValueError("In-phase and opposed-phase series have different sizes.")

        mask_img = run_totalsegmentator(ip_img, tmp)

        ip = sitk.GetArrayFromImage(ip_img).astype(np.float32)
        op = sitk.GetArrayFromImage(op_img).astype(np.float32)
        ts_mask = (sitk.GetArrayFromImage(mask_img) > 0).astype(np.uint8)
        sx, sy, sz = ip_img.GetSpacing()

    if not ts_mask.any():
        raise ValueError("No liver detected in the in-phase MRI. Is this an abdominal scan?")
    assert ts_mask.shape == ip.shape == op.shape

    liver_slices, boxes = select_slices_and_boxes(ts_mask)
    _log(f"liver on {int((ts_mask.sum(axis=(1, 2)) > 0).sum())}/{ts_mask.shape[0]} slices; "
         f"kept {liver_slices}")
    return {
        "ip": ip,
        "op": op,
        "liver_slices": liver_slices,
        "boxes": boxes,
        "ts_mask": ts_mask,
        "spacing": (float(sz), float(sy), float(sx)),
    }
