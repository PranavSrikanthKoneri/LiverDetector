"""Local research API. Run one worker: python -m uvicorn app.main:app."""
import json
import logging
import os
from pathlib import Path
import tempfile
from threading import Lock

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from demo.pipeline import run_pipeline
from tabular.predict import validate

app = FastAPI(title="FibroLens", version="0.1.0")
_inference_lock = Lock()
MAX_UPLOAD_BYTES = 512 * 1024 * 1024


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze")
def analyze(file: UploadFile = File(...), patient: str = Form(...)):
    try:
        questionnaire = json.loads(patient)
        if not isinstance(questionnaire, dict):
            raise ValueError("patient must be a JSON object")
        validate(questionnaire)
    except (ValueError, TypeError) as exc:
        file.file.close()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    checkpoint = os.environ.get("MEDSAM_CHECKPOINT")
    if not checkpoint or not Path(checkpoint).is_file():
        file.file.close()
        raise HTTPException(status_code=503, detail="Configure MEDSAM_CHECKPOINT on the backend before analyzing scans.")
    if not _inference_lock.acquire(blocking=False):
        file.file.close()
        raise HTTPException(status_code=503, detail="Another scan is being analyzed. Please retry when it finishes.")
    try:
        with tempfile.TemporaryDirectory(prefix="livercast_upload_") as directory:
            upload = Path(directory) / "scan.zip"
            size = 0
            with upload.open("wb") as destination:
                while chunk := file.file.read(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_UPLOAD_BYTES:
                        raise HTTPException(status_code=413, detail="Upload exceeds 512 MiB.")
                    destination.write(chunk)
            return run_pipeline(str(upload), questionnaire)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logging.exception("Analysis failed")
        raise HTTPException(status_code=500, detail="Analysis failed; check the backend terminal for details.") from exc
    finally:
        file.file.close()
        _inference_lock.release()
