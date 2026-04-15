import json
import os
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


def _get_database_url() -> str:
    return os.environ.get("DATABASE_URL", "sqlite:///./sales_data.db")


def _make_engine():
    url = _get_database_url()
    return create_engine(url, connect_args={"check_same_thread": False})


class Base(DeclarativeBase):
    pass


class ImportLog(Base):
    __tablename__ = "import_log"
    id = Column(Integer, primary_key=True, index=True)
    files = Column(Text, nullable=False)        # JSON list of filenames
    record_count = Column(Integer, nullable=False)
    imported_at = Column(DateTime, default=datetime.utcnow)


def save_dataframe(df: pd.DataFrame, source_files: List[str]) -> int:
    """Replace sales_records table with df and log the import. Returns row count."""
    engine = _make_engine()
    Base.metadata.create_all(bind=engine)

    df.to_sql("sales_records", engine, if_exists="replace", index=False)

    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        session.add(
            ImportLog(
                files=json.dumps(source_files, ensure_ascii=False),
                record_count=len(df),
                imported_at=datetime.utcnow(),
            )
        )
        session.commit()
    finally:
        session.close()
    return len(df)


def get_summary() -> Dict[str, Any]:
    """Return dashboard summary dict."""
    engine = _make_engine()
    Base.metadata.create_all(bind=engine)

    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        log = (
            session.query(ImportLog)
            .order_by(ImportLog.imported_at.desc())
            .first()
        )
    finally:
        session.close()

    if log is None:
        return {"record_count": 0, "last_import": None, "files": [], "columns": []}

    try:
        sample = pd.read_sql("SELECT * FROM sales_records LIMIT 1", engine)
        columns = [c for c in sample.columns if not c.startswith("_")]
    except Exception:
        columns = []

    return {
        "record_count": log.record_count,
        "last_import": log.imported_at.isoformat(),
        "files": json.loads(log.files),
        "columns": columns,
    }


def get_records(page: int = 1, page_size: int = 100) -> Dict[str, Any]:
    """Return paginated records from sales_records table."""
    engine = _make_engine()
    try:
        total = int(
            pd.read_sql("SELECT COUNT(*) AS cnt FROM sales_records", engine)
            .iloc[0]["cnt"]
        )
        offset = (page - 1) * page_size
        df = pd.read_sql(
            f"SELECT * FROM sales_records LIMIT {page_size} OFFSET {offset}",
            engine,
        )
        return {
            "data": df.to_dict(orient="records"),
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    except Exception:
        return {"data": [], "total": 0, "page": page, "page_size": page_size}


def export_to_excel(output_path: str) -> str:
    """Export all sales_records to Excel, excluding internal _ columns."""
    engine = _make_engine()
    df = pd.read_sql("SELECT * FROM sales_records", engine)
    df = df[[c for c in df.columns if not c.startswith("_")]]
    df.to_excel(output_path, index=False)
    return output_path
