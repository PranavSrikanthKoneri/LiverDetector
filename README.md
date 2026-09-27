# FibroLens

MRI-based liver fibrosis research demo.

## Description

FibroLens combines two independent signals into one report: a dual-echo MRI
measurement (liver segmentation, fat percentage, texture) computed from an
uploaded DICOM scan, and a separate fibrosis-risk estimate from a short
clinical questionnaire (age, BMI, waist circumference, diabetes status,
alcohol intake). The two are shown side by side rather than merged into a
single score, so each stays traceable to its own source.

**This is a research and education tool, not a diagnostic one.** The texture
measurement is exploratory, the two-echo fat estimate is not a calibrated
PDFF, and the questionnaire model is trained on proxy labels. It does not
replace a FibroScan, biopsy, or a clinician's evaluation.

## Getting Started

### Dependencies

- Windows, macOS, or Linux with Python 3.10+ and Node.js 18+
- A CUDA GPU is optional (falls back to CPU) but strongly recommended for
  the segmentation step — MedSAM and TotalSegmentator are slow on CPU
- The [MedSAM](https://github.com/bowang-lab/MedSAM) repository, cloned
  alongside this one, plus its official checkpoint weights
- No API key and no external service calls are required — inference runs
  entirely locally

### Installing

```powershell
git clone https://github.com/bowang-lab/MedSAM.git ../MedSAM
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
```

`python -m pip install -e .` installs the backend (`app`, `demo`, `imaging`,
`tabular`) as editable packages, using `backend/requirements.txt`.

Set these before running the server:

```powershell
$env:PYTHONPATH = (Resolve-Path ..\MedSAM).Path
$env:MEDSAM_CHECKPOINT = "C:\path\to\medsam_vit_b.pth"
$env:MEDSAM_DEVICE = "cuda:0"   # omit to fall back to CPU
```

Then install the frontend:

```powershell
cd frontend
npm install
```

Model weights and patient DICOM ZIPs are intentionally excluded from Git
(see `.gitignore`) — medical imaging data should never be committed.

### Executing program

Run the backend and frontend in two terminals, from the repository root:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm run dev
```

Then open the frontend's local URL (Vite prints it, typically
`http://127.0.0.1:5173`) and:

1. Upload a ZIP containing in-phase and opposed-phase DICOM images
2. Fill in the short clinical questionnaire
3. Review the scan, biomarkers, and risk estimate together

## Help

- **`/api/health` returns nothing / connection refused** — the backend
  isn't running, or the frontend's Vite proxy (`frontend/vite.config.js`)
  isn't pointed at the right port.
- **Segmentation fails or is very slow** — confirm `MEDSAM_CHECKPOINT` and
  `PYTHONPATH` are set correctly, and that `torch.cuda.is_available()`
  returns `True` if you expect GPU use.
- **Run the backend test suite:**

  ```powershell
  python -m pytest
  ```

- **Run the frontend test suite:**

  ```powershell
  cd frontend
  npm test
  ```

See `backend/README.md` and `docs/` for module-level notes and known
research limitations.

## Authors

- Sahitha Karapitiya
- Anish Deshpande
- Pranav Srikanth Koneri
- Muthamizharrasu K

## Version History

- **Unreleased** — Editorial frontend redesign; sticky research-notice
  banner; alcohol-warning and fibrosis-panel layout fixes; combined
  scan-overlay projection controls. See `git log` for the full history.
- **0.1** — Initial end-to-end pipeline: DICOM upload, TotalSegmentator/
  MedSAM liver localization, dual-echo fat and texture measurement,
  NHANES-trained questionnaire risk model, and the first FastAPI + React
  integration.

## License

Not yet assigned. Until a license file is added, all rights are reserved
by the authors above.

## Acknowledgments

- [MedSAM](https://github.com/bowang-lab/MedSAM) — promptable medical
  image segmentation, used for liver localization
- [TotalSegmentator](https://github.com/wasserth/TotalSegmentator) —
  whole-body CT/MRI segmentation, used as a localization fallback
- [NHANES](https://www.cdc.gov/nchs/nhanes/) — the population data behind
  the questionnaire risk model's proxy labels
