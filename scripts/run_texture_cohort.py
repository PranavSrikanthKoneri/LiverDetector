"""Run manifest cases sequentially on the friend's GPU, then compare texture."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest', type=Path)
    p.add_argument('--checkpoint', type=Path, required=True)
    args = p.parse_args()
    base = args.manifest.resolve().parent
    manifest = json.loads(args.manifest.read_text())
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA is unavailable. Run this on the GPU computer; CPU fallback is disabled.')
    for case in manifest['cases']:
        dest = base / case['results_dir']
        if (dest / 'texture_summary.json').exists():
            print(f"Reusing {case['case_id']}; measurements will be verified during comparison.", flush=True)
            continue
        subprocess.run([sys.executable, '-m', 'imaging.analyze', str(base / case['zip_path']),
                        '--checkpoint', str(args.checkpoint.resolve()), '--device', 'cuda:0',
                        '--out', str(dest)], check=True)
    subprocess.run([sys.executable, '-m', 'imaging.chaos_texture_qc', 'check', str(args.manifest.resolve()),
                    '--out', str(base / 'texture_quality_comparison.json')], check=True)


if __name__ == '__main__':
    main()
