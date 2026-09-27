# FibroLens

Research demo combining dual-echo MRI measurements with a separate questionnaire
fibrosis-risk model. **Not diagnostic.** Texture is exploratory; the two-echo fat
estimate is not calibrated PDFF. Clipping and texture stability flags are retained.

## Project layout

```text
frontend/                 React/Vite dashboard and HTTP client
backend/
  app/                    FastAPI: /api/health and /api/analyze
  demo/                   Shared pipeline, CLI, example questionnaire, handoff
  imaging/                DICOM loader, MedSAM, fallback, fat, texture and QC
    resources/            Versioned numerical texture reference (with attribution)
  tabular/                Questionnaire model, saved artifact and projections
  tests/                  Python unit and integration tests
  scripts/                Dataset/cohort preparation utilities
docs/                     Contracts, research notes and branch audit
pyproject.toml            Installable backend and pytest configuration
requirements.txt          Redirects to backend/requirements.txt
debug/                    Local generated results (ignored)
```

The earlier local `models/` prototype, environments, downloaded data, and saved
result ZIPs are preserved and ignored. The active model is
`backend/tabular/risk_model.joblib`; no training is needed to run the demo.

## Setup on the existing Windows GPU machine

Run from the repository root. Reuse the environment that already ran MedSAM:

```powershell
.\.venv-medsam\Scripts\Activate.ps1
uv pip install --python .\.venv-medsam\Scripts\python.exe -e . "torch==2.6.0+cu124" "torchvision==0.21.0+cu124"
$env:PYTHONPATH = (Resolve-Path ..\MedSAM).Path
$env:MEDSAM_CHECKPOINT = "E:\Personal\Build Fest 2026\medsam_vit_b.pth"
$env:MEDSAM_DEVICE = "cuda:0"
python -c "import torch; print(torch.cuda.is_available())"
```

For a fresh machine, create a Python 3.10+ virtual environment, install a
compatible torch/torchvision build, then `python -m pip install -e .`.
Clone original [MedSAM](https://github.com/bowang-lab/MedSAM) alongside this repo
and obtain its official checkpoint; source is imported using `PYTHONPATH`.
Weights and patient ZIPs are intentionally not in Git. `MEDSAM_DEVICE` defaults
to CPU if unset; TotalSegmentator selects its device separately.

Editable installation keeps the established imports (`imaging`, `tabular`,
`demo`) and `python -m imaging.analyze` commands working after the directory move.

## Run the app

Backend, in the configured terminal:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend, in a second terminal from the repository root (Node 22.12+ or 24):

```powershell
npm --prefix frontend ci
npm --prefix frontend run dev
```

Open the URL Vite prints (normally http://localhost:5173). Its `/api` proxy points
to `127.0.0.1:8000`. Upload the **inner patient DICOM ZIP**, complete the questionnaire,
and click Analyze. The dashboard uses actual results and scan previews, not mocks.
The API accepts multipart `file` plus JSON `patient` and uses one inference at a
time to avoid concurrent GPU allocations. Use one backend worker. Uploads are
temporary, limited to 512 MiB, and deleted after processing. This is a local demo,
not an authenticated production service.

The dashboard shows questionnaire-only `p_ge_F2` and tier prominently. MRI fat
and texture are separate measurements, not risk-model inputs. Projection curves
are population scenarios; the original scan is unchanged. An optional, liver-only illustrative overlay
changes shading with the slider; it is not a prediction of future MRI appearance.
Recommendations are deterministic placeholder text; no LLM is connected.

## CLI and tests

```powershell
python -m demo.pipeline "E:\Personal\Build Fest 2026\patient33\chaos_patient33.zip" --questionnaire backend/demo/example_questionnaire.json --out debug/demo_patient33/result.json
python -m imaging.analyze "E:\Personal\Build Fest 2026\patient33\chaos_patient33.zip" --checkpoint "$env:MEDSAM_CHECKPOINT" --device cuda:0 --out debug/texture_patient33
python -m pytest
npm --prefix frontend run build
npm --prefix frontend run lint
npm --prefix frontend test
```

`pytest` discovers only `backend/tests`, excluding the old local prototype.
The optional real-data loader test requires `CHAOS_TEST_ZIP`; other tests mock
model inference. Keep scripts invoking the loader behind a `__main__` guard for
Windows worker processes. Backend model and QC files resolve relative to their
modules, not the current directory.

See [pipeline handoff](backend/demo/HANDOFF.md),
[backend setup](backend/README.md), [frontend setup](frontend/README.md),
[interface contract](docs/interfaces.md), and [branch audit](docs/integration_audit.md).
