"""Package extracted CHAOS training MR cases and write a portable GPU manifest.

python backend/scripts/prepare_texture_cohort.py C:/data/Train_Sets/MR --out data/texture_cohort
Does not run any models. Only T1DUAL/DICOM_anon files are packaged.
"""
import argparse
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mr_root', type=Path)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    folders = sorted(args.mr_root.glob('*/T1DUAL/DICOM_anon'))
    if not folders:
        raise ValueError('No cases found; supply the extracted Train_Sets/MR directory')
    args.out.mkdir(parents=True, exist_ok=True)
    if (args.out / 'manifest.json').exists():
        raise ValueError('Manifest already exists; use a fresh output directory')
    cases = []
    for folder in folders:
        case_id = 'chaos_' + folder.parent.parent.name
        dest = args.out / f'{case_id}.zip'
        with ZipFile(dest, 'x', ZIP_DEFLATED) as z:
            for f in sorted(folder.rglob('*')):
                if f.is_file():
                    z.write(f, f.relative_to(folder.parent).as_posix())
        cases.append({'case_id': case_id, 'zip_path': dest.name,
                      'results_dir': f'results/{case_id}'})
    (args.out / 'manifest.json').write_text(json.dumps({'cohort': 'CHAOS MR training set', 'cases': cases}, indent=2))
    print(f'Prepared {len(cases)} cases. Run backend/scripts/run_texture_cohort.py on the GPU computer.')


if __name__ == '__main__':
    main()
