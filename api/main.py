
from __future__ import annotations
from fastapi import FastAPI, File, HTTPException, UploadFile, Header
import os
from dataclasses import asdict
from io import BytesIO
from pathlib import Path
import secrets
from fastapi import Header
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi import FastAPI, File, HTTPException, UploadFile, Header, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware

from src.ingestion.loader import DatasetLoadError, load_dataset
from src.profiling.profiler import profile_dataset
from src.quality.engine import run_quality_audit
from src.visualization.dataset_intelligence import (
    analyse_dataset_intelligence,
)

MAX_UPLOAD_BYTES = 5 * 1024 * 1024

app = FastAPI(
    title="MASH LABS Data Audit API",
    description="Backend API for the MASH LABS Data Audit Engine",
    version="0.1.0",
)

def require_beta_access(authorization: str | None = Header(default=None)):
    expected_token = os.getenv("BETA_API_TOKEN")

    if not expected_token:
        raise HTTPException(
            status_code=503,
            detail="Private beta access is not configured.",
        )

    scheme, separator, provided_token = (authorization or "").partition(" ")

    if (
        not separator
        or scheme.lower() != "bearer"
        or not secrets.compare_digest(provided_token, expected_token)
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing beta access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Local development origins only.

# Browser origins permitted to access the API.
DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

configured_origins = os.getenv("ALLOWED_ORIGINS", "")

allowed_origins = (
    [origin.strip() for origin in configured_origins.split(",") if origin.strip()]
    if configured_origins
    else DEFAULT_ALLOWED_ORIGINS
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)




@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "MASH LABS Data Audit Engine",
        "version": "0.1.0",
    }


@app.post("/api/audit", dependencies=[Depends(require_beta_access)])
async def audit_dataset(file: UploadFile = File(...)):
    filename = Path(file.filename or "").name
    extension = Path(filename).suffix.lower()

    if extension not in {".csv", ".xlsx"}:
        raise HTTPException(
            status_code=415,
            detail="Only CSV and XLSX files are supported.",
        )

    try:
        content = await file.read(MAX_UPLOAD_BYTES + 1)
    finally:
        await file.close()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Maximum upload size is 5 MB.",
        )

    try:
        ingestion = load_dataset(
            BytesIO(content),
            filename,
        )

        dataframe = ingestion.dataframe

        profile = profile_dataset(dataframe)

        quality = run_quality_audit(
            dataframe,
            profile,
        )

        intelligence = analyse_dataset_intelligence(
            dataframe
        )

        return jsonable_encoder(
            {
                "filename": filename,
                "rows": int(dataframe.shape[0]),
                "columns": int(dataframe.shape[1]),
                "quality": asdict(quality),
                "recommendations": intelligence,
            }
        )

    except DatasetLoadError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
