"""Preliminary cohort-relative texture comparison; never a disease classifier.

Build records from a manifest of original DICOM zips and saved GPU results:
python -m imaging.texture_reference manifest.json --out debug/texture_reference
No segmentation models are loaded by this module.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile

import numpy as np
import pydicom
import SimpleITK as sitk

from imaging.analyze import measure_texture_slice, summarize_texture
from imaging.load import _unzip, scan_series, find_ip_op_pair, read_volume

FEATURES = ('contrast', 'homogeneity', 'entropy')
METHOD = 'ip_glcm32_erode3_roi_p1p99_four_offsets_bits_v1'
MIN_REFERENCES = 10  # Engineering reporting floor, not a clinical sample-size claim.


def compatible(a, b):
    """Conservative acquisition screen; matching does not prove harmonization."""
    for key in ('manufacturer', 'scanner', 'sequence'):
        if not a.get(key) or a[key] != b.get(key):
            return False
    # Native-pixel features require similar physical sampling. These tolerances
    # are engineering choices and must not be optimized to produce disease labels.
    for key, rtol, atol in [('field_T', .02, .01), ('te_ms', .05, .01),
                            ('tr_ms', .10, .1), ('flip_degrees', 0, 2),
                            ('spacing_xyz', .05, .01)]:
        if a.get(key) is None or b.get(key) is None:
            return False
        if not np.allclose(a[key], b[key], rtol=rtol, atol=atol):
            return False
    return True


def compare_records(records):
    ids = [r['case_id'] for r in records]
    hashes = [r['image_fingerprint'] for r in records]
    if len(set(ids)) != len(ids) or len(set(hashes)) != len(hashes):
        raise ValueError('Duplicate patient ID or duplicate image volume in reference set')
    results = []
    for target in records:
        peers = [r for r in records if r['case_id'] != target['case_id']
                 and r['method'] == target['method']
                 and compatible(target['acquisition'], r['acquisition'])]
        ready = len(peers) >= MIN_REFERENCES
        result = {'case_id': target['case_id'], 'label': 'exploratory',
                  'status': 'preliminary_comparison' if ready else 'insufficient_reference_data',
                  'reference_count': len(peers), 'minimum_reference_count': MIN_REFERENCES,
                  'reference_ids': [r['case_id'] for r in peers],
                  'excluded_incompatible_ids': [r['case_id'] for r in records
                      if r['case_id'] != target['case_id'] and r not in peers],
                  'features': {}}
        for name in FEATURES:
            value = target['texture'][name]
            values = np.array([r['texture'][name] for r in peers], dtype=float)
            entry = {'value': value, 'slice_range': target['slice_ranges'][name],
                     'percentile': None, 'reference_median': None, 'reference_iqr': None}
            if ready:
                # Midrank: half credit for ties; patients, not slices, are samples.
                percentile = 100 * (np.sum(values < value) + .5 * np.sum(values == value)) / len(values)
                entry.update(percentile=float(percentile), reference_median=float(np.median(values)),
                             reference_iqr=np.percentile(values, [25, 75]).tolist())
            result['features'][name] = entry
        result['interpretation'] = (
            'Percentiles describe position among compatible reference scans only; '
            'they are not healthy/abnormal thresholds or disease probabilities.' if ready else
            'Not enough compatible independent reference patients to report percentiles. '
            'Raw features and slice variation are available.')
        results.append(result)
    return results


def acquisition_metadata(ipg, volume):
    headers = [pydicom.dcmread(f, stop_before_pixels=True) for f in ipg['files']]
    def uniform(tag, numeric=False):
        vals = [getattr(h, tag, None) for h in headers]
        if any(v is None for v in vals):
            return None
        if numeric:
            vals = [float(v) for v in vals]
            return vals[0] if np.isfinite(vals).all() and np.allclose(vals, vals[0]) else None
        vals = [str(v) for v in vals]
        return vals[0] if len(set(vals)) == 1 else None
    acquisition = {'manufacturer': uniform('Manufacturer'),
                   'scanner': uniform('ManufacturerModelName'),
                   'sequence': uniform('ScanningSequence'),
                   'field_T': uniform('MagneticFieldStrength', True),
                   'te_ms': uniform('EchoTime', True),
                   'tr_ms': uniform('RepetitionTime', True),
                   'flip_degrees': uniform('FlipAngle', True),
                   'spacing_xyz': list(volume.GetSpacing())}
    return acquisition


def build_record(entry, base):
    case_id = entry['case_id']  # Dataset identifier, not DICOM patient information.
    source = (base / entry['zip_path']).resolve()
    folder = (base / entry['results_dir']).resolve()
    quality = json.loads((folder / 'quality_report.json').read_text())
    saved = json.loads((folder / 'texture_summary.json').read_text())
    slices = sorted(map(int, quality))
    if len(slices) != 5 or slices != saved['slices'] or saved['label'] != 'exploratory':
        raise ValueError(f'{case_id}: expected five matching exploratory slice results')
    features = []
    with tempfile.TemporaryDirectory() as tmp:
        _unzip(str(source), tmp)
        ipg, _ = find_ip_op_pair(scan_series(tmp))
        volume = read_volume(ipg['files'])
        image = sitk.GetArrayFromImage(volume)
        if min(slices) < 0 or max(slices) >= len(image):
            raise ValueError(f'{case_id}: slice indices do not match volume')
        acquisition = acquisition_metadata(ipg, volume)
        fingerprint = hashlib.sha256(np.asarray(image, dtype='<f4').tobytes()).hexdigest()
        for idx in slices:
            mask = np.load(folder / f'mask_{idx:03d}.npy', allow_pickle=False)
            feature, details = measure_texture_slice(image[idx], mask)
            if details['warnings']:
                raise ValueError(f'{case_id}: texture warning on slice {idx}')
            row = quality[str(idx)]
            if row['texture_measurement'] != details:
                raise ValueError(f'{case_id}: texture method or input mismatch on slice {idx}')
            for name in FEATURES:
                if not np.isclose(feature[name], row['texture'][name], rtol=0, atol=1e-9):
                    raise ValueError(f'{case_id}: saved features do not reproduce')
            features.append(feature)
    texture = summarize_texture(features)
    for name in FEATURES:
        if not np.isclose(texture[name], saved['texture'][name], rtol=0, atol=1e-9):
            raise ValueError(f'{case_id}: summary mismatch')
    return {'case_id': case_id, 'method': METHOD, 'image_fingerprint': fingerprint,
            'acquisition': acquisition, 'texture': texture, 'slices': slices,
            'slice_ranges': {k: [min(f[k] for f in features), max(f[k] for f in features)] for k in FEATURES}}


def preflight(manifest, base):
    """Check whether any reference group can meet the floor before GPU work."""
    acquisitions = []
    for entry in manifest['cases']:
        with tempfile.TemporaryDirectory() as tmp:
            _unzip(str((base / entry['zip_path']).resolve()), tmp)
            ipg, _ = find_ip_op_pair(scan_series(tmp))
            acquisitions.append(acquisition_metadata(ipg, read_volume(ipg['files'])))
    counts = [sum(i != j and compatible(a, b) for j, b in enumerate(acquisitions))
              for i, a in enumerate(acquisitions)]
    for entry, count in zip(manifest['cases'], counts):
        print(f"{entry['case_id']}: {count} eligible reference scans before segmentation")
    if not any(count >= MIN_REFERENCES for count in counts):
        raise ValueError('No patient has enough compatible references. GPU batch stopped before inference. '
                         'Review missing metadata and acquisition differences; do not infer normality.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    records = [build_record(e, args.manifest.resolve().parent) for e in manifest['cases']]
    comparisons = compare_records(records)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'reference_records.json').write_text(json.dumps(records, indent=2))
    report = {'label': 'exploratory', 'cohort': manifest.get('cohort', 'unspecified'),
              'sample_unit': 'patient', 'method': METHOD, 'comparisons': comparisons,
              'limitations': 'Small selected cohort; protocol screen is not harmonization. No disease labels, diagnostic thresholds, or clinical reference intervals.'}
    (args.out / 'texture_comparisons.json').write_text(json.dumps(report, indent=2))
    for r in comparisons:
        print(f"{r['case_id']}: {r['status']}; {r['reference_count']} compatible other patients")


if __name__ == '__main__':
    main()
