from copy import deepcopy

import pytest

from imaging.texture_reference import FEATURES, METHOD, compare_records, compatible


def record(i, value=1.0):
    return {'case_id': str(i), 'image_fingerprint': str(i), 'method': METHOD,
            'acquisition': {'manufacturer': 'test', 'scanner': 'test', 'sequence': 'GR',
                            'field_T': 1.5, 'te_ms': 4.6, 'tr_ms': 150,
                            'flip_degrees': 80, 'spacing_xyz': [1.7, 1.7, 9]},
            'texture': {k: value for k in FEATURES},
            'slice_ranges': {k: [value, value] for k in FEATURES}}


def test_small_cohort_does_not_report_percentiles():
    results = compare_records([record(i) for i in range(3)])
    assert all(r['status'] == 'insufficient_reference_data' for r in results)
    assert all(r['reference_count'] == 2 for r in results)
    assert all(r['features']['contrast']['percentile'] is None for r in results)


def test_leave_one_patient_out_and_midrank_ties():
    records = [record(i, float(i)) for i in range(11)]
    records[6]['texture'] = records[5]['texture'].copy()
    result = compare_records(records)[5]
    assert result['reference_count'] == 10
    assert '5' not in result['reference_ids']
    assert result['features']['contrast']['percentile'] == 55.0
    assert result['features']['contrast']['slice_range'] == [5., 5.]


@pytest.mark.parametrize('key', ['case_id', 'image_fingerprint'])
def test_duplicate_patients_or_images_rejected(key):
    records = [record(1), record(2)]
    records[1][key] = records[0][key]
    with pytest.raises(ValueError, match='Duplicate'):
        compare_records(records)


def test_missing_or_different_acquisition_is_excluded():
    a = record(1)['acquisition']
    assert compatible(a, a)
    for key, value in [('scanner', None), ('field_T', 3), ('spacing_xyz', [1, 1, 9])]:
        b = deepcopy(a)
        b[key] = value
        assert not compatible(a, b)
    records = [record(i) for i in range(11)]
    records[1]['acquisition']['field_T'] = 3
    result = compare_records(records)[0]
    assert result['reference_count'] == 9
    assert result['excluded_incompatible_ids'] == ['1']
    assert result['status'] == 'insufficient_reference_data'
