"""Mask-selection checks use synthetic masks; no model weights or GPU needed."""
import numpy as np
import pytest

from imaging.analyze import select_mask


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
