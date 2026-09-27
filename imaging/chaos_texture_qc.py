"""Build CHAOS texture QC context from expert masks, or check saved GPU results.

These commands perform numerical measurements only; no models are loaded.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile

import cv2
import numpy as np
import SimpleITK as sitk

from imaging.load import _unzip, scan_series, find_ip_op_pair, read_volume, select_slices_and_boxes
from imaging.texture_quality import check_texture_slice, summarize_quality, compare_quality, METHOD

DEFAULT_REFERENCE = Path(__file__).parent / 'resources' / 'chaos_texture_qc_v1.json'


def fingerprint(image):
    return hashlib.sha256(np.asarray(image, dtype='<f4').tobytes()).hexdigest()


def volume_record(case_id, image, masks, spacing_xyz, mask_source):
    rows = [dict(slice_index=int(idx), **check_texture_slice(image[idx], mask, spacing_xyz[1::-1]))
            for idx, mask in sorted(masks.items())]
    return {'case_id': case_id, 'image_fingerprint': fingerprint(image),
            'mask_source': mask_source, 'spacing_xyz': list(spacing_xyz),
            'quality': summarize_quality(rows), 'slices': rows}


def build_reference(root):
    records = []
    folders = sorted(root.glob('*/T1DUAL'))
    if len(folders) != 20:
        raise ValueError('Expected the complete 20-patient CHAOS training MR folder')
    for folder in folders:
        ipg, _ = find_ip_op_pair(scan_series(str(folder / 'DICOM_anon')))
        volume = read_volume(ipg['files'])
        image = sitk.GetArrayFromImage(volume)
        masks = []
        for f in ipg['files']:
            # Match by original filename, never lexicographic rank or guessed reversal.
            path = folder / 'Ground' / (Path(f).stem + '.png')
            labels = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
            if labels is None or labels.shape != image.shape[1:]:
                raise ValueError(f'Missing or mismatched ground truth: {path}')
            if not np.isin(labels, [0, 63, 126, 189, 252]).all():
                raise ValueError(f'Unexpected CHAOS label values: {path}')
            masks.append(labels == 63)
        masks = np.stack(masks)
        indices, _ = select_slices_and_boxes(masks)
        if len(indices) != 5:
            raise ValueError(f'Expected five liver slices in {folder.parent.name}')
        record = volume_record('chaos_' + folder.parent.name, image,
                               {i: masks[i] for i in indices}, volume.GetSpacing(), 'CHAOS_expert_liver')
        records.append(record)
        print(record['case_id'], record['quality']['status'], record['quality']['flags'], flush=True)
    # Validate uniqueness and attach leave-one-patient-out stability context.
    for record in records:
        record['reference_context'] = compare_quality(record, records)
    return {'method': METHOD, 'source': 'https://zenodo.org/records/3431873',
            'attribution': 'Ali Emre Kavur, M. Alper Selver, Oguz Dicle, Mustafa Baris, N. Sinem Gezer (2019), CHAOS Challenge Data v1.03. Derived numerical QC measurements.',
            'license': 'CC BY-NC-SA 4.0',
            'license_url': 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
            'source_archive_md5': 'df21053002a1cc86df918a87da3b2c19',
            'description': 'Derived numerical texture measurement QC from 20 CHAOS training patients; '
                           'five largest expert liver-mask slices per patient. Not clinical quality labels.',
            'records': records}


def check_manifest(manifest_path, reference):
    # Reproduce existing saved features first, preventing wrong zip/mask associations.
    from imaging.texture_reference import build_record
    manifest = json.loads(manifest_path.read_text())
    base = manifest_path.resolve().parent
    outputs = []
    for entry in manifest['cases']:
        verified = build_record(entry, base)
        with tempfile.TemporaryDirectory() as tmp:
            _unzip(str((base / entry['zip_path']).resolve()), tmp)
            ipg, _ = find_ip_op_pair(scan_series(tmp))
            volume = read_volume(ipg['files'])
            image = sitk.GetArrayFromImage(volume)
            masks = {i: np.load(base / entry['results_dir'] / f'mask_{i:03d}.npy', allow_pickle=False)
                     for i in verified['slices']}
            record = volume_record(entry['case_id'], image, masks, volume.GetSpacing(), 'saved_selected_masks')
        record['reference_context'] = compare_quality(record, reference['records'])
        outputs.append(record)
        print(record['case_id'], record['quality']['status'], record['quality']['flags'], flush=True)
    return {'method': METHOD, 'reference_source': reference['source'], 'patients': outputs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    build = sub.add_parser('build')
    build.add_argument('--mr-root', type=Path, required=True)
    build.add_argument('--out', type=Path, required=True)
    check = sub.add_parser('check')
    check.add_argument('manifest', type=Path)
    check.add_argument('--reference', type=Path, default=DEFAULT_REFERENCE)
    check.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'build':
        result = build_reference(args.mr_root)
    else:
        reference = json.loads(args.reference.read_text())
        if reference['method'] != METHOD:
            raise ValueError('Reference method mismatch')
        result = check_manifest(args.manifest, reference)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
