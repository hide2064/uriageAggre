import os
import sys
import tempfile
import threading
from pathlib import Path
from typing import List

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel

from backend.database import export_to_excel, get_records, get_summary, save_dataframe
from backend.processor import (
    load_header_mapping,
    load_value_mapping,
    process_files,
)


class ConfigUpdateBody(BaseModel):
    content: str


app = FastAPI(title="Sales Data Aggregator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_base_dir() -> Path:
    """Return base dir — handles both development and PyInstaller frozen mode."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).parent.parent


_BASE_DIR = _get_base_dir()


def _config_dir() -> Path:
    env = os.environ.get("CONFIG_DIR")
    if env:
        return Path(env)
    cwd_config = Path.cwd() / "config"
    if cwd_config.exists():
        return cwd_config
    return _BASE_DIR / "config"


def _export_dir() -> Path:
    env = os.environ.get("EXPORT_DIR")
    d = Path(env) if env else _BASE_DIR / "exports"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── API routes ────────────────────────────────────────────────────────────────

@app.get("/api/summary")
def api_summary():
    return get_summary()


@app.post("/api/import")
async def api_import(files: List[UploadFile] = File(...)):
    with tempfile.TemporaryDirectory() as tmpdir:
        saved: List[str] = []
        for upload in files:
            safe_name = Path(upload.filename or "file").name or "file"
            dest = Path(tmpdir) / safe_name
            dest.write_bytes(await upload.read())
            saved.append(str(dest))

        header_mapping = load_header_mapping(str(_config_dir() / "mapping_config.csv"))

        value_mapping = None
        key_col = new_col = None
        vm_path = _config_dir() / "value_mapping_config.csv"
        if vm_path.exists():
            key_col, new_col, value_mapping = load_value_mapping(str(vm_path))

        df, errors = process_files(saved, header_mapping, value_mapping, key_col, new_col)

    if df.empty:
        raise HTTPException(
            status_code=400,
            detail={"message": "No data processed", "errors": errors},
        )

    count = save_dataframe(df, [f.filename for f in files])
    return {"success": True, "record_count": count, "errors": errors}


@app.get("/api/data")
def api_data(page: int = 1, page_size: int = 100):
    return get_records(page=page, page_size=page_size)


@app.get("/api/config/{config_type}")
def api_get_config(config_type: str):
    if config_type not in ("mapping", "value_mapping"):
        raise HTTPException(status_code=404, detail="Unknown config type")
    path = _config_dir() / f"{config_type}_config.csv"
    if not path.exists():
        return {"content": ""}
    return {"content": path.read_text(encoding="utf-8-sig")}


@app.put("/api/config/{config_type}")
def api_put_config(config_type: str, body: ConfigUpdateBody):
    if config_type not in ("mapping", "value_mapping"):
        raise HTTPException(status_code=404, detail="Unknown config type")
    path = _config_dir() / f"{config_type}_config.csv"
    path.write_text(body.content, encoding="utf-8")
    return {"success": True}


@app.post("/api/export")
def api_export():
    output_path = str(_export_dir() / "export.xlsx")
    try:
        export_to_excel(output_path)
        return {"success": True, "download_url": "/api/export/download"}
    except Exception:
        raise HTTPException(status_code=500, detail="Export failed. Check that data has been imported first.")


@app.get("/api/export/download")
def api_export_download():
    path = _export_dir() / "export.xlsx"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Run export first.")
    return FileResponse(str(path), filename="export.xlsx")


# ── Static file serving (production Vue build) ────────────────────────────────

_FRONTEND_DIST = _BASE_DIR / "frontend" / "dist"

if _FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="static")


# ── Desktop entry point ───────────────────────────────────────────────────────

def start_desktop() -> None:
    import webview  # imported lazily to avoid issues during testing

    def _run_server():
        uvicorn.run(app, host="127.0.0.1", port=8765, log_level="error")

    threading.Thread(target=_run_server, daemon=True).start()
    webview.create_window(
        "Sales Data Aggregator", "http://127.0.0.1:8765",
        width=1280, height=800, resizable=True,
    )
    webview.start()


if __name__ == "__main__":
    start_desktop()
