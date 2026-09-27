# Backend

Install from the repository root with `python -m pip install -e .`. This exposes
`app`, `demo`, `imaging`, and `tabular` as Python packages while their sources live
under `backend/`. Dependencies are declared in `requirements.txt` here.

- `app/main.py`: multipart HTTP upload adapter; temporary uploads and serialized inference.
- `demo/pipeline.py`: questionnaire validation → localization → measurements/QC → risk scenarios → JSON.
- `imaging/analyze.py`: shared `segment_and_measure` plus diagnostic CLI.
- `tabular/predict.py`: saved questionnaire model; unrelated to the ignored old `models/` prototype.
- `tests/`: imaging, tabular, texture and HTTP integration tests.

Set `MEDSAM_CHECKPOINT` to the official weights, `MEDSAM_DEVICE=cuda:0`, and
`PYTHONPATH` to the original MedSAM checkout. Then run from the repository root:

```text
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
python -m pytest
```

No training, external LLM key, or data upload to an external service is needed.
The API forwards the complete pipeline result, including fat warnings, per-slice
quality checks, texture stability context and actual PNG previews encoded as data
URLs. Array masks stay in process; the diagnostic CLI can save them to disk.

Multipart handling follows the [FastAPI file/form documentation](https://fastapi.tiangolo.com/tutorial/request-forms-and-files/).

See the repository README for Windows commands and research limitations.
