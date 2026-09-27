from copy import deepcopy
import json

import numpy as np
import pytest

from imaging.texture_quality import (check_texture_slice, summarize_quality, resample_slice,
                                     compare_quality, METHOD, relative_change)
from imaging.chaos_texture_qc import DEFAULT_REFERENCE


def sample():
    y, x = np.mgrid[:64, :64]
    image = 100 + 10*np.sin(x/7) + 8*np.cos(y/9)
    mask = (x-32)**2 + (y-32)**2 < 25**2
    return image, mask


def test_resampling_uses_physical_coordinates_and_preserves_inputs():
    y, x = np.mgrid[:30, :40]
    image = 10 + y*3 + x*1.5
    mask = np.ones(image.shape, bool)
    before = image.copy()
    im, ma = resample_slice(image, mask, (3, 1.5), 2)
    yy, xx = np.mgrid[:im.shape[0], :im.shape[1]]
    np.testing.assert_allclose(im, 10 + yy*2 + xx*2)
    np.testing.assert_array_equal(image, before)
    assert ma.all()


def test_constant_image_requires_review_not_healthy_label():
    result = check_texture_slice(np.ones((64, 64)), np.ones((64, 64)), (2, 2))
    assert result['status'] == 'review_required'
    assert 'constant_intensity_roi' in result['flags']
    assert result['texture']['contrast'] == 0


@pytest.mark.parametrize('failure', ['nan', 'negative', 'empty', 'spacing'])
def test_invalid_inputs_propagate_to_patient_status(failure):
    image, mask = sample()
    spacing = (2, 2)
    if failure == 'nan': image[32, 32] = np.nan
    if failure == 'negative': image[32, 32] = -1
    if failure == 'empty': mask[:] = False
    if failure == 'spacing': spacing = (0, 2)
    row = check_texture_slice(image, mask, spacing)
    assert row['status'] == 'invalid'
    report = summarize_quality([row])
    assert report['status'] == 'invalid'
    assert report['texture_2mm'] is None


def test_real_features_and_sensitivity_are_finite():
    image, mask = sample()
    row = check_texture_slice(image, mask, (1.7, 1.7))
    assert row['status'] != 'invalid'
    for key in ('boundary_sensitivity', 'spacing_sensitivity'):
        assert all(np.isfinite(v) and 0 <= v <= 2 for v in row[key].values())
    assert summarize_quality([row])['slice_count'] == 1


def test_symmetric_relative_change_handles_zero():
    base = dict(contrast=0, homogeneity=1, entropy=0)
    assert relative_change(base, [base]) == dict(contrast=0, homogeneity=0, entropy=0)
    other = dict(contrast=1, homogeneity=1, entropy=1)
    assert relative_change(base, [other])['contrast'] == 2


def test_packaged_reference_has_twenty_independent_patients_and_excludes_self():
    ref = json.loads(DEFAULT_REFERENCE.read_text())
    assert ref['method'] == METHOD
    assert len(ref['records']) == 20
    target = deepcopy(ref['records'][0])
    out = compare_quality(target, ref['records'])
    assert out['reference_count'] == 19
    assert target['case_id'] not in out['reference_ids']
    target['case_id'] = 'renamed_scan'
    out = compare_quality(target, ref['records'])
    assert out['reference_count'] == 19  # fingerprint also excludes duplicate scan
    assert out['status'] == 'exploratory_context'
    assert all(0 <= v <= 100 for v in out['percentiles'].values())
    assert compare_quality(target, ref['records'][:3])['status'] == 'insufficient_reference_data'
    with pytest.raises(ValueError, match='Duplicate'):
        compare_quality(target, ref['records'] + [ref['records'][0]])


def test_boundary_pattern_triggers_review():
    y, x = np.mgrid[:80, :80]
    radius = np.sqrt((x-40)**2 + (y-40)**2)
    image = 100 + np.sin(x/8)
    band = (radius > 19) & (radius < 25)
    image[band] += 60 * ((x[band] + y[band]) % 2)
    row = check_texture_slice(image, radius < 25, (2, 2))
    assert row['status'] == 'review_required'
    assert 'boundary_sensitive' in row['flags']
