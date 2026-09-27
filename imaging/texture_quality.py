"""Texture measurement QC, not a disease or diagnostic image-quality classifier."""
import numpy as np
from scipy.ndimage import map_coordinates
from imaging.analyze import measure_texture_slice, summarize_texture

METHOD = 'texture_qc_v1_2mm_linear_32bins_6mm_erosion'
FEATURES = ('contrast', 'homogeneity', 'entropy')
# Explicit engineering review triggers, not clinically calibrated cutoffs.
POLICY = {'minimum_roi_pixels': 128, 'minimum_pairs_per_direction': 100,
          'relative_sensitivity_review': 0.25}


def resample_slice(image, mask, spacing_yx, target_mm):
    image, mask = np.asarray(image, dtype=float), np.asarray(mask)
    spacing = np.asarray(spacing_yx, dtype=float)
    if image.ndim != 2 or image.shape != mask.shape or min(image.shape) < 2:
        raise ValueError('Image and mask must be matching 2D arrays')
    if not np.isfinite(mask).all() or not np.isin(mask, [0, 1]).all():
        raise ValueError('Mask must be binary and finite')
    if spacing.shape != (2,) or not np.isfinite(spacing).all() or (spacing <= 0).any():
        raise ValueError('Expected positive finite y/x spacing in mm')
    if not np.isfinite(target_mm) or target_mm <= 0:
        raise ValueError('Expected positive finite target spacing')
    if not np.isfinite(image).all() or (image < 0).any():
        raise ValueError('Nonfinite or negative magnitude input')
    size = np.floor((np.array(image.shape) - 1) * spacing / target_mm).astype(int) + 1
    if size.min() < 2 or size.max() > 4096:
        raise ValueError('Unsupported resampling dimensions')
    coords = np.meshgrid(*(np.arange(n) * target_mm / s for n, s in zip(size, spacing)), indexing='ij')
    # Actual physical coordinates, no through-plane interpolation. Masks use NN.
    return (map_coordinates(image, coords, order=1, mode='nearest', prefilter=False),
            map_coordinates(mask.astype(float), coords, order=0, mode='nearest', prefilter=False) > .5)


def relative_change(base, variants):
    # Symmetric relative difference, bounded 0..2, well defined for zero features.
    return {k: float(max(2 * abs(v[k] - base[k]) /
                         max(abs(v[k]) + abs(base[k]), 1e-12) for v in variants))
            for k in FEATURES}


def check_texture_slice(image, mask, spacing_yx):
    result = {'method': METHOD, 'status': 'invalid', 'flags': [], 'texture': None,
              'boundary_sensitivity': None, 'spacing_sensitivity': None}
    try:
        standardized, roi = resample_slice(image, mask, spacing_yx, 2.0)
        baseline, details = measure_texture_slice(standardized, roi)
        result.update(texture=baseline, measurement=details)
        if details['warnings']:
            result['flags'].extend(details['warnings'])
        if details['valid_pixels'] < POLICY['minimum_roi_pixels']:
            result['flags'].append('small_roi')
        if min(details['pair_counts']) < POLICY['minimum_pairs_per_direction']:
            result['flags'].append('few_pixel_pairs')
        boundary = [measure_texture_slice(standardized, roi, erosion_radius_pixels=r)[0]
                    for r in (2, 4)]  # 4 / 8 mm vs baseline 6 mm
        spacing = []
        for mm in (1.8, 2.2):
            im, ma = resample_slice(image, mask, spacing_yx, mm)
            spacing.append(measure_texture_slice(im, ma, erosion_radius_pixels=6/mm)[0])
        result['boundary_sensitivity'] = relative_change(baseline, boundary)
        result['spacing_sensitivity'] = relative_change(baseline, spacing)
        for kind in ('boundary', 'spacing'):
            if max(result[f'{kind}_sensitivity'].values()) > POLICY['relative_sensitivity_review']:
                result['flags'].append(f'{kind}_sensitive')
        result['status'] = 'review_required' if result['flags'] else 'no_flags_detected'
    except ValueError as exc:
        result['flags'].append('measurement_not_evaluable')
        result['error'] = str(exc)
    return result


def summarize_quality(rows):
    if not rows:
        raise ValueError('No QC slices')
    statuses = [r['status'] for r in rows]
    complete = all(r['boundary_sensitivity'] is not None and
                   r['spacing_sensitivity'] is not None for r in rows)
    return {'method': METHOD, 'label': 'exploratory_measurement_quality',
            'status': 'invalid' if 'invalid' in statuses else (
                'review_required' if 'review_required' in statuses else 'no_flags_detected'),
            'flags': sorted(set(f for r in rows for f in r['flags'])),
            'policy': POLICY.copy(), 'slice_count': len(rows),
            'texture_2mm': summarize_texture([r['texture'] for r in rows]) if complete else None,
            'boundary_sensitivity_max': max(max(r['boundary_sensitivity'].values()) for r in rows) if complete else None,
            'spacing_sensitivity_max': max(max(r['spacing_sensitivity'].values()) for r in rows) if complete else None,
            'interpretation': 'Checks measurement stability only. No flags does not establish healthy liver, '
                              'absence of motion, correct segmentation, or diagnostic image quality.'}


def compare_quality(target, references):
    """CHAOS stress-test context, not acquisition-matched tissue percentiles."""
    if target['quality']['method'] != METHOD:
        raise ValueError('Target QC method mismatch')
    ids = [r['case_id'] for r in references]
    hashes = [r['image_fingerprint'] for r in references]
    if len(ids) != len(set(ids)) or len(hashes) != len(set(hashes)):
        raise ValueError('Duplicate reference patient or image')
    peers = [r for r in references if r['case_id'] != target['case_id']
             and r['image_fingerprint'] != target['image_fingerprint']
             and r['quality']['method'] == METHOD and r['quality']['status'] != 'invalid']
    ready = len(peers) >= 10 and target['quality']['status'] != 'invalid'
    out = {'status': 'exploratory_context' if ready else 'insufficient_reference_data',
           'reference_count': len(peers), 'reference_ids': [r['case_id'] for r in peers],
           'label': 'CHAOS_measurement_stability_context', 'percentiles': {},
           'limitations': 'Heterogeneous acquisitions and expert reference masks; not a healthy tissue '
                         'range or scanner harmonization. Percentiles do not change QC status.'}
    for k in ('boundary_sensitivity_max', 'spacing_sensitivity_max'):
        value = target['quality'][k]
        vals = np.array([r['quality'][k] for r in peers], dtype=float)
        out['percentiles'][k] = (float(100 * (np.sum(vals < value) + .5*np.sum(vals == value))/len(vals))
                                  if ready else None)
    return out
