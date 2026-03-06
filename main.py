from __future__ import annotations

import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from axiomvault.modules import analyze_contradictions, build_report, extract_text, save_report


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / os.getenv("UPLOAD_DIR", "uploads")
OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "output")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "50"))

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AxiomVault", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/upload")
async def upload(file: UploadFile = File(...)) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    file_id = uuid.uuid4().hex
    safe_name = Path(file.filename).name
    dest = UPLOAD_DIR / f"{file_id}__{safe_name}"

    # Best-effort size check while streaming.
    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    written = 0

    with dest.open("wb") as f:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            written += len(chunk)
            if written > max_bytes:
                try:
                    dest.unlink(missing_ok=True)  # py3.8+: missing_ok
                except TypeError:
                    if dest.exists():
                        dest.unlink()
                raise HTTPException(status_code=413, detail="File too large")
            f.write(chunk)

    return {
        "file_id": file_id,
        "filename": safe_name,
        "stored_as": dest.name,
    }


@app.post("/analyze/{file_id}")
def analyze(file_id: str) -> dict:
    matches = list(UPLOAD_DIR.glob(f"{file_id}__*"))
    if not matches:
        raise HTTPException(status_code=404, detail="File not found")
    if len(matches) > 1:
        raise HTTPException(status_code=409, detail="Multiple files found for file_id")

    path = matches[0]
    try:
        text = extract_text(path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Extract failed: {e}") from e

    analysis = analyze_contradictions(text)
    report = build_report(file_id=file_id, filename=path.name.split("__", 1)[-1], extracted_text=text, analysis=analysis)
    saved = save_report(OUTPUT_DIR, report)

    return {
        "file_id": file_id,
        "report": saved,
        "analysis": analysis,
    }


@app.get("/reports/{report_filename}")
def get_report(report_filename: str) -> FileResponse:
    # report_filename examples: report_<id>.json / report_<id>.md
    safe = Path(report_filename).name
    path = OUTPUT_DIR / safe
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(str(path))

