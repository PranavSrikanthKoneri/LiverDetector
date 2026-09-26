"""Mask-selection checks use synthetic masks; no model weights or GPU needed."""
import numpy as np
import pytest

from imaging.analyze import measure_fat_slice, select_mask, summarize_fat


def reference():
    mask = np.zeros((40, 40), dtype=bool)
    mask[10:30, 10:30] = True
    return mask


def test_agreeing_mask_keeps_medsam_without_mutating_inputs():
    ts = reference()
    candidate = ts.copy()
    candidate[10, 10] = False
    selected, report = select_mask(candidate, ts, [8, 8, 32, 32])
    assert report["source"] == "medsam"
    np.testing.assert_array_equal(selected, candidate)
    selected[:] = False
    assert candidate.any() and ts.sum() == 400


@pytest.mark.parametrize("candidate", [
    np.zeros((40, 40)), np.ones((40, 40)),
    np.full((40, 40), np.nan), np.zeros((3, 3)),
    np.full((40, 40), 0.6),
])
def test_bad_candidate_uses_exact_fallback(candidate):
    ts = reference()
    selected, report = select_mask(candidate, ts, [8, 8, 32, 32])
    assert report["source"] == "totalsegmentator" and report["reasons"]
    np.testing.assert_array_equal(selected, ts)


def test_disjoint_candidate_rejected_even_with_same_area():
    ts = reference()
    candidate = np.zeros_like(ts)
    candidate[:10, :] = True
    selected, report = select_mask(candidate, ts, [0, 0, 39, 39])
    assert "low_overlap_with_ts" in report["reasons"]
    np.testing.assert_array_equal(selected, ts)


def test_fragmentation_rejected_despite_overlap():
    ts = reference()
    candidate = ts.copy()
    candidate[19:21, :] = False
    _, report = select_mask(candidate, ts, [8, 8, 32, 32])
    assert "fragmented_mask" in report["reasons"]


def test_empty_fallback_is_an_error():
    with pytest.raises(ValueError, match="Fallback"):
        select_mask(reference(), np.zeros((40, 40)), [8, 8, 32, 32])


def test_dixon_uses_eroded_liver_pixels_and_preserves_inputs():
    mask = reference()
    ip = np.full(mask.shape, 100, dtype=np.uint16)
    op = np.full(mask.shape, 200, dtype=np.uint16)
    # Only the 14x14 interior remaining after erosion contains the true signal.
    op[13:27, 13:27] = 80
    before = op.copy()
    pct, counts = measure_fat_slice(ip, op, mask)
    assert pct == pytest.approx(10)
    assert counts == {"eroded_pixels": 196, "valid_pixels": 196, "excluded_pixels": 0}
    np.testing.assert_array_equal(op, before)
    assert mask.sum() == 400


@pytest.mark.parametrize("op_value, expected", [(100, 0), (120, 0), (0, 50)])
def test_dixon_clipping_and_unsigned_subtraction(op_value, expected):
    ip = np.full((40, 40), 100, dtype=np.uint16)
    op = np.full_like(ip, op_value)
    pct, _ = measure_fat_slice(ip, op, reference())
    assert pct == expected


def test_dixon_uses_median_not_mean():
    ip = np.full((40, 40), 100.0)
    op = np.full_like(ip, 80)
    op[13:16, 13:27] = 0
    pct, _ = measure_fat_slice(ip, op, reference())
    assert pct == pytest.approx(10)


def test_dixon_excludes_invalid_signals():
    ip = np.full((40, 40), 100.0)
    op = np.full_like(ip, 80)
    ip[15, 15:18] = [0, np.nan, -1]
    op[16, 15:17] = [np.inf, -1]
    pct, counts = measure_fat_slice(ip, op, reference())
    assert pct == pytest.approx(10)
    assert counts["valid_pixels"] == 191
    assert counts["excluded_pixels"] == 5


def test_dixon_empty_erosion_and_no_valid_pixels_fail_explicitly():
    ip = np.ones((40, 40))
    tiny = np.zeros_like(ip)
    tiny[20:23, 20:23] = 1
    with pytest.raises(ValueError, match="erosion"):
        measure_fat_slice(ip, ip, tiny)
    with pytest.raises(ValueError, match="No valid Dixon"):
        measure_fat_slice(ip * 0, ip, reference())


def test_fat_averages_slices_and_uses_strict_threshold():
    assert summarize_fat([0, 10]) == {"fat_pct": 5.0, "steatosis": False}
    assert summarize_fat([2, 10]) == {"fat_pct": 6.0, "steatosis": True}
    for invalid in ([], [np.nan], [-1], [51]):
        with pytest.raises(ValueError):
            summarize_fat(invalid)
