"""Tests for the imaging stage (Person 1).

The mock and pairing tests always run. The real end-to-end test needs a CHAOS
T1DUAL zip:  CHAOS_TEST_ZIP=path/to/case.zip pytest tests/test_imaging.py
"""
import os
import zipfile

import numpy as np
import pytest

from imaging.load import find_ip_op_pair, load_and_locate
from imaging.mock import load_and_locate_mock


def check_contract(r: dict) -> None:
    """Assert r matches the shared load_and_locate contract."""
    assert set(r) == {"ip", "op", "liver_slices", "boxes", "ts_mask", "spacing"}
    ip, op, mask = r["ip"], r["op"], r["ts_mask"]
    assert ip.ndim == 3 and ip.dtype == np.float32
    assert op.shape == ip.shape and op.dtype == np.float32
    assert mask.shape == ip.shape and mask.dtype == np.uint8
    assert set(np.unique(mask)) <= {0, 1}

    slices = r["liver_slices"]
    assert 1 <= len(slices) <= 5 and slices == sorted(slices)
    assert set(r["boxes"]) == set(slices)
    z, y, x = ip.shape
    for s in slices:
        assert 0 <= s < z and mask[s].any()
        x0, y0, x1, y1 = r["boxes"][s]
        assert all(isinstance(v, int) for v in (x0, y0, x1, y1))
        assert 0 <= x0 < x1 <= x - 1 and 0 <= y0 < y1 <= y - 1

    assert len(r["spacing"]) == 3 and all(v > 0 for v in r["spacing"])


def test_mock_matches_contract():
    check_contract(load_and_locate_mock())


# ---- pairing rule on synthetic series headers (no DICOMs needed)

def _group(te, n=30, folder="x", seq="GR", z0=0.0):
    return {"series_number": "1", "description": "", "sequence": seq, "echo_time": te,
            "n": n, "shape2d": (256, 256), "orient": (1, 0, 0, 0, 1, 0),
            "z_range": (z0, z0 + 200), "folder": folder, "files": []}


def test_pair_shorter_te_is_opposed_phase():
    ip, op = find_ip_op_pair([_group(4.6), _group(2.3), _group(90.0, seq="SE")])
    assert ip["echo_time"] == 4.6 and op["echo_time"] == 2.3


def test_pair_requires_same_geometry():
    with pytest.raises(ValueError, match="in-phase / opposed-phase"):
        find_ip_op_pair([_group(4.6), _group(2.3, n=40)])


def test_pair_falls_back_to_chaos_folder_names():
    ip, op = find_ip_op_pair([_group(None, folder="inphase"), _group(None, folder="outphase")])
    assert ip["folder"] == "inphase" and op["folder"] == "outphase"


# ---- error handling and the real pipeline

def test_zip_without_dicoms_raises(tmp_path):
    z = tmp_path / "empty.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("readme.txt", "not a scan")
    with pytest.raises(ValueError, match="No DICOM images"):
        load_and_locate(str(z))


@pytest.mark.skipif(not os.environ.get("CHAOS_TEST_ZIP"), reason="set CHAOS_TEST_ZIP to a CHAOS T1DUAL zip")
def test_real_chaos_case():
    r = load_and_locate(os.environ["CHAOS_TEST_ZIP"])
    check_contract(r)
    assert len(r["liver_slices"]) == 5
    assert r["ip"][r["ts_mask"] > 0].mean() > r["ip"].mean()  # liver brighter than average (air is dark)
