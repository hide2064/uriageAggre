# Sales Data Aggregator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a pywebview desktop application that ingests multiple CSV/Excel files, normalizes headers, enriches data via master lookup, stores results in SQLite, and exports aggregated data to Excel.

**Architecture:** Python FastAPI backend handles ETL logic (pandas), SQLite persistence (SQLAlchemy), and serves the Vue 3 SPA as static files; pywebview wraps the whole stack into a single desktop window; PyInstaller bundles it into a standalone `.exe`.

**Tech Stack:** Python 3.10+, FastAPI, uvicorn, pywebview, pandas, openpyxl, SQLAlchemy, python-multipart, pytest, httpx; Vue 3, Vite, Tailwind CSS, Axios, Vue Router; SQLite; PyInstaller

---

## File Map

```
/
├── backend/
│   ├── __init__.py
│   ├── processor.py     # Pure ETL functions: load_header_mapping, load_value_mapping,
│   │                    # normalize_headers, enrich_data, process_files
│   ├── database.py      # SQLAlchemy + pandas: save_dataframe, get_summary,
│   │                    # get_records, export_to_excel
│   └── main.py          # FastAPI app + pywebview entry point (start_desktop)
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── src/
│       ├── main.js
│       ├── style.css
│       ├── App.vue          # Sidebar layout + RouterView
│       ├── router/index.js  # Hash-mode routes for 4 views
│       ├── api/index.js     # Axios wrappers for all API endpoints
│       └── views/
│           ├── Dashboard.vue    # Summary stats + column list + file list
│           ├── Import.vue       # Drag-and-drop file picker + progress
│           ├── ConfigManager.vue # Tab editor for both CSV configs
│           └── Export.vue       # Generate + download xlsx
├── config/
│   ├── mapping_config.csv         # canonical,alias1,alias2,...
│   └── value_mapping_config.csv   # header row + key→value rows
├── sales_data/
│   └── sample.csv
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Shared pytest fixtures
│   ├── test_processor.py
│   ├── test_database.py
│   └── test_api.py
├── build.spec   # PyInstaller spec
├── build.py     # Helper: npm build + PyInstaller
└── requirements.txt
```

---

## Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `backend/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `config/mapping_config.csv`
- Create: `config/value_mapping_config.csv`
- Create: `sales_data/sample.csv`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.115.0
uvicorn==0.32.0
pywebview==5.3.2
pandas==2.2.3
openpyxl==3.1.5
sqlalchemy==2.0.36
python-multipart==0.0.12
pytest==8.3.3
httpx==0.27.2
```

- [ ] **Step 2: Create directory structure and empty init files**

```bash
mkdir -p backend config sales_data tests docs/superpowers/plans
touch backend/__init__.py tests/__init__.py
```

- [ ] **Step 3: Create config/mapping_config.csv**

```csv
date,日付,Date,transaction_date,売上日
amount,金額,Amount,売上金額,revenue,売上
client,取引先,Client,顧客名,customer
product_code,商品コード,ProductCode,item_code
quantity,数量,Quantity,個数,qty
```

- [ ] **Step 4: Create config/value_mapping_config.csv**

```csv
商品コード,カテゴリ
A001,電化製品
A002,電化製品
B001,食品
B002,食品
C001,衣料品
```

- [ ] **Step 5: Create sales_data/sample.csv**

```csv
日付,売上金額,取引先,商品コード,数量
2024-01-15,50000,株式会社ABC,A001,10
2024-01-16,30000,XYZ商会,B001,5
2024-01-17,80000,株式会社ABC,C001,2
2024-01-18,45000,山田商店,A002,8
2024-01-19,25000,XYZ商会,B002,3
```

- [ ] **Step 6: Create tests/conftest.py**

```python
import pytest


@pytest.fixture
def sample_mapping_config(tmp_path):
    config = tmp_path / "mapping_config.csv"
    config.write_text(
        "date,日付,Date,transaction_date\n"
        "amount,金額,Amount,売上金額\n"
        "client,取引先,Client\n"
        "product_code,商品コード,ProductCode\n",
        encoding="utf-8",
    )
    return str(config)


@pytest.fixture
def sample_value_mapping_config(tmp_path):
    config = tmp_path / "value_mapping_config.csv"
    config.write_text(
        "商品コード,カテゴリ\n"
        "A001,電化製品\n"
        "B001,食品\n",
        encoding="utf-8",
    )
    return str(config)


@pytest.fixture
def sample_csv(tmp_path):
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text(
        "日付,売上金額,取引先,商品コード\n"
        "2024-01-01,50000,顧客A,A001\n"
        "2024-01-02,30000,顧客B,B001\n"
        "2024-01-03,45000,顧客C,X999\n",
        encoding="utf-8",
    )
    return str(csv_file)
```

- [ ] **Step 7: Install Python dependencies**

```bash
pip install -r requirements.txt
```

Expected: All packages install without error.

- [ ] **Step 8: Commit**

```bash
git add requirements.txt backend/__init__.py tests/ config/ sales_data/
git commit -m "chore: project setup — config files, sample data, test fixtures"
```

---

## Task 2: ETL Processor — Core Transform Functions

**Files:**
- Create: `backend/processor.py`
- Create: `tests/test_processor.py`

- [ ] **Step 1: Write failing tests for normalize_headers and enrich_data**

Create `tests/test_processor.py`:

```python
import pytest
import pandas as pd
from backend.processor import normalize_headers, enrich_data


class TestNormalizeHeaders:
    def test_renames_alias_to_canonical(self):
        df = pd.DataFrame({"売上金額": [100], "取引先": ["ABC"]})
        mapping = {
            "amount": ["金額", "Amount", "売上金額"],
            "client": ["取引先", "Client"],
        }
        result = normalize_headers(df, mapping)
        assert "amount" in result.columns
        assert "client" in result.columns

    def test_leaves_unknown_columns_unchanged(self):
        df = pd.DataFrame({"extra_col": [1], "売上金額": [100]})
        mapping = {"amount": ["売上金額"]}
        result = normalize_headers(df, mapping)
        assert "extra_col" in result.columns

    def test_canonical_name_in_source_stays(self):
        df = pd.DataFrame({"amount": [100]})
        mapping = {"amount": ["売上金額", "Amount"]}
        result = normalize_headers(df, mapping)
        assert "amount" in result.columns

    def test_strips_whitespace_from_column_names(self):
        df = pd.DataFrame({" 売上金額 ": [100]})
        mapping = {"amount": ["売上金額"]}
        result = normalize_headers(df, mapping)
        assert "amount" in result.columns

    def test_does_not_mutate_input(self):
        df = pd.DataFrame({"売上金額": [1]})
        mapping = {"amount": ["売上金額"]}
        normalize_headers(df, mapping)
        assert "売上金額" in df.columns


class TestEnrichData:
    def test_adds_new_column_from_mapping(self):
        df = pd.DataFrame({"product_code": ["A001", "B001"]})
        mapping = {"A001": "電化製品", "B001": "食品"}
        result = enrich_data(df, mapping, "product_code", "category")
        assert list(result["category"]) == ["電化製品", "食品"]

    def test_uses_na_for_missing_keys(self):
        df = pd.DataFrame({"product_code": ["A001", "UNKNOWN"]})
        mapping = {"A001": "電化製品"}
        result = enrich_data(df, mapping, "product_code", "category")
        assert list(result["category"]) == ["電化製品", "N/A"]

    def test_missing_key_column_sets_all_na(self):
        df = pd.DataFrame({"other_col": ["A001"]})
        mapping = {"A001": "電化製品"}
        result = enrich_data(df, mapping, "product_code", "category")
        assert list(result["category"]) == ["N/A"]

    def test_does_not_mutate_input(self):
        df = pd.DataFrame({"product_code": ["A001"]})
        original_cols = list(df.columns)
        enrich_data(df, {"A001": "電化製品"}, "product_code", "category")
        assert list(df.columns) == original_cols
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_processor.py -v
```

Expected: `ImportError: cannot import name 'normalize_headers' from 'backend.processor'`

- [ ] **Step 3: Create backend/processor.py with normalize_headers and enrich_data**

```python
import csv
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def normalize_headers(
    df: pd.DataFrame,
    header_mapping: Dict[str, List[str]],
) -> pd.DataFrame:
    """Rename df columns to canonical names using header_mapping.

    header_mapping: {canonical_name: [alias1, alias2, ...]}
    Columns not in any alias list are left unchanged.
    """
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    rename_map: Dict[str, str] = {}
    for col in df.columns:
        for canonical, aliases in header_mapping.items():
            if col == canonical or col in aliases:
                rename_map[col] = canonical
                break
    return df.rename(columns=rename_map)


def enrich_data(
    df: pd.DataFrame,
    value_mapping: Dict[str, str],
    key_col: str,
    new_col: str,
) -> pd.DataFrame:
    """Add new_col by looking up key_col values in value_mapping.

    Missing keys → 'N/A'. Missing key_col → all 'N/A'.
    """
    df = df.copy()
    if key_col not in df.columns:
        df[new_col] = "N/A"
        return df
    df[new_col] = df[key_col].astype(str).map(value_mapping).fillna("N/A")
    return df
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_processor.py -v
```

Expected: All 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/processor.py tests/test_processor.py
git commit -m "feat: normalize_headers and enrich_data with tests"
```

---

## Task 3: ETL Processor — Config Loaders & File Processing

**Files:**
- Modify: `backend/processor.py`
- Modify: `tests/test_processor.py`

- [ ] **Step 1: Write failing tests for config loaders**

Append to `tests/test_processor.py`:

```python
from backend.processor import (
    normalize_headers, enrich_data,
    load_header_mapping, load_value_mapping, process_files,
)


class TestLoadHeaderMapping:
    def test_loads_canonical_with_aliases(self, sample_mapping_config):
        mapping = load_header_mapping(sample_mapping_config)
        assert "amount" in mapping
        assert "売上金額" in mapping["amount"]
        assert "Amount" in mapping["amount"]

    def test_handles_utf8_bom(self, tmp_path):
        config = tmp_path / "mapping.csv"
        config.write_bytes(
            b"\xef\xbb\xbf" + "amount,売上金額,Amount\n".encode("utf-8")
        )
        mapping = load_header_mapping(str(config))
        assert "amount" in mapping

    def test_strips_whitespace_from_aliases(self, tmp_path):
        config = tmp_path / "m.csv"
        config.write_text("amount, 売上金額 , Amount \n", encoding="utf-8")
        mapping = load_header_mapping(str(config))
        assert "売上金額" in mapping["amount"]


class TestLoadValueMapping:
    def test_returns_key_col_new_col_and_data(self, sample_value_mapping_config):
        key_col, new_col, mapping = load_value_mapping(sample_value_mapping_config)
        assert key_col == "商品コード"
        assert new_col == "カテゴリ"
        assert mapping["A001"] == "電化製品"
        assert mapping["B001"] == "食品"

    def test_header_only_file_returns_empty_mapping(self, tmp_path):
        config = tmp_path / "empty.csv"
        config.write_text("キー,値\n", encoding="utf-8")
        key_col, new_col, mapping = load_value_mapping(str(config))
        assert key_col == "キー"
        assert new_col == "値"
        assert mapping == {}


class TestProcessFiles:
    def test_normalizes_headers_and_enriches(
        self, sample_csv, sample_mapping_config, sample_value_mapping_config
    ):
        hm = load_header_mapping(sample_mapping_config)
        key_col, new_col, vm = load_value_mapping(sample_value_mapping_config)
        df, errors = process_files([sample_csv], hm, vm, key_col, new_col)
        assert errors == []
        assert "amount" in df.columns
        assert "client" in df.columns
        assert new_col in df.columns
        assert len(df) == 3

    def test_unknown_keys_become_na(
        self, sample_csv, sample_mapping_config, sample_value_mapping_config
    ):
        hm = load_header_mapping(sample_mapping_config)
        key_col, new_col, vm = load_value_mapping(sample_value_mapping_config)
        df, errors = process_files([sample_csv], hm, vm, key_col, new_col)
        # X999 not in mapping → N/A
        assert df[new_col].eq("N/A").sum() == 1

    def test_adds_source_file_column(self, sample_csv, sample_mapping_config):
        hm = load_header_mapping(sample_mapping_config)
        df, errors = process_files([sample_csv], hm)
        assert "_source_file" in df.columns

    def test_collects_errors_for_bad_files(self, sample_mapping_config):
        hm = load_header_mapping(sample_mapping_config)
        df, errors = process_files(["/nonexistent/file.csv"], hm)
        assert len(errors) == 1
        assert "file" in errors[0]
        assert "error" in errors[0]

    def test_combines_multiple_files(self, tmp_path, sample_mapping_config):
        f1 = tmp_path / "f1.csv"
        f2 = tmp_path / "f2.csv"
        f1.write_text("売上金額\n100\n200\n", encoding="utf-8")
        f2.write_text("売上金額\n300\n", encoding="utf-8")
        hm = load_header_mapping(sample_mapping_config)
        df, errors = process_files([str(f1), str(f2)], hm)
        assert len(df) == 3
        assert errors == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_processor.py::TestLoadHeaderMapping tests/test_processor.py::TestLoadValueMapping tests/test_processor.py::TestProcessFiles -v
```

Expected: `ImportError: cannot import name 'load_header_mapping'`

- [ ] **Step 3: Implement config loaders and process_files — append to backend/processor.py**

```python
def load_header_mapping(config_path: str) -> Dict[str, List[str]]:
    """Load mapping_config.csv.

    Format per row: canonical_name,alias1,alias2,...
    Returns: {canonical_name: [alias1, alias2, ...]}
    """
    mapping: Dict[str, List[str]] = {}
    with open(config_path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or not row[0].strip():
                continue
            canonical = row[0].strip()
            aliases = [a.strip() for a in row[1:] if a.strip()]
            mapping[canonical] = aliases
    return mapping


def load_value_mapping(config_path: str) -> Tuple[str, str, Dict[str, str]]:
    """Load value_mapping_config.csv.

    Row 1 (header): key_col_name,new_col_name
    Row 2+:         key_value,mapped_value
    Returns: (key_col, new_col, {key_value: mapped_value})
    """
    with open(config_path, encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))

    if not rows or len(rows[0]) < 2:
        return "", "", {}

    key_col = rows[0][0].strip()
    new_col = rows[0][1].strip()
    mapping: Dict[str, str] = {}
    for row in rows[1:]:
        if len(row) >= 2 and row[0].strip():
            mapping[row[0].strip()] = row[1].strip()
    return key_col, new_col, mapping


def _read_file(file_path: str) -> pd.DataFrame:
    """Read CSV, TSV, TXT or Excel file into a DataFrame."""
    suffix = Path(file_path).suffix.lower()
    if suffix in (".csv", ".txt", ".tsv"):
        for encoding in ("utf-8-sig", "cp932", "utf-8"):
            try:
                return pd.read_csv(file_path, encoding=encoding)
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Cannot decode {file_path} with known encodings")
    elif suffix in (".xlsx", ".xls"):
        return pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def process_files(
    file_paths: List[str],
    header_mapping: Dict[str, List[str]],
    value_mapping: Optional[Dict[str, str]] = None,
    key_col: Optional[str] = None,
    new_col: Optional[str] = None,
) -> Tuple[pd.DataFrame, List[dict]]:
    """Process and combine multiple files.

    Returns: (combined_df, errors)
    errors is a list of {'file': path, 'error': message}.
    """
    dfs: List[pd.DataFrame] = []
    errors: List[dict] = []

    for file_path in file_paths:
        try:
            df = _read_file(file_path)
            df = normalize_headers(df, header_mapping)
            if value_mapping and key_col and new_col:
                df = enrich_data(df, value_mapping, key_col, new_col)
            df["_source_file"] = Path(file_path).name
            dfs.append(df)
        except Exception as exc:
            errors.append({"file": file_path, "error": str(exc)})

    if not dfs:
        return pd.DataFrame(), errors

    return pd.concat(dfs, ignore_index=True), errors
```

- [ ] **Step 4: Run all processor tests**

```bash
pytest tests/test_processor.py -v
```

Expected: All 17 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/processor.py tests/test_processor.py
git commit -m "feat: ETL config loaders and multi-file processing with tests"
```

---

## Task 4: Database Layer

**Files:**
- Create: `backend/database.py`
- Create: `tests/test_database.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_database.py`:

```python
import os
import importlib
import pandas as pd
import pytest


@pytest.fixture(autouse=True)
def use_temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/test.db")
    import backend.database
    importlib.reload(backend.database)
    yield


def test_save_returns_row_count():
    from backend.database import save_dataframe
    df = pd.DataFrame({"col_a": ["x", "y"], "col_b": [1, 2]})
    assert save_dataframe(df, ["test.csv"]) == 2


def test_summary_empty_when_no_data():
    from backend.database import get_summary
    s = get_summary()
    assert s["record_count"] == 0
    assert s["last_import"] is None


def test_summary_reflects_last_save():
    from backend.database import save_dataframe, get_summary
    df = pd.DataFrame({"amount": [100, 200, 300]})
    save_dataframe(df, ["sales.csv"])
    s = get_summary()
    assert s["record_count"] == 3
    assert "sales.csv" in s["files"]
    assert "amount" in s["columns"]


def test_get_records_returns_saved_rows():
    from backend.database import save_dataframe, get_records
    df = pd.DataFrame({"name": ["Alice", "Bob"]})
    save_dataframe(df, ["people.csv"])
    result = get_records(page=1, page_size=10)
    assert result["total"] == 2
    names = {r["name"] for r in result["data"]}
    assert names == {"Alice", "Bob"}


def test_get_records_paginates():
    from backend.database import save_dataframe, get_records
    df = pd.DataFrame({"val": list(range(10))})
    save_dataframe(df, ["data.csv"])
    p1 = get_records(page=1, page_size=4)
    p2 = get_records(page=2, page_size=4)
    assert len(p1["data"]) == 4
    assert len(p2["data"]) == 4
    assert p1["total"] == 10


def test_export_to_excel_creates_valid_file(tmp_path):
    from backend.database import save_dataframe, export_to_excel
    df = pd.DataFrame({"product": ["A", "B"], "qty": [10, 20]})
    save_dataframe(df, ["products.csv"])
    out = str(tmp_path / "out.xlsx")
    export_to_excel(out)
    assert os.path.exists(out)
    loaded = pd.read_excel(out)
    assert list(loaded["product"]) == ["A", "B"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_database.py -v
```

Expected: `ImportError: cannot import name 'save_dataframe' from 'backend.database'`

- [ ] **Step 3: Create backend/database.py**

```python
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
```

- [ ] **Step 4: Run database tests**

```bash
pytest tests/test_database.py -v
```

Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/database.py tests/test_database.py
git commit -m "feat: SQLite database layer with import log and Excel export"
```

---

## Task 5: FastAPI Backend

**Files:**
- Create: `backend/main.py`
- Create: `tests/test_api.py`

- [ ] **Step 1: Write failing API tests**

Create `tests/test_api.py`:

```python
import importlib
import io
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def setup_env(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/test.db")
    monkeypatch.setenv("CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("EXPORT_DIR", str(tmp_path / "exports"))

    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "mapping_config.csv").write_text(
        "date,日付\namount,売上金額\nclient,取引先\nproduct_code,商品コード\n",
        encoding="utf-8",
    )
    (cfg / "value_mapping_config.csv").write_text(
        "商品コード,カテゴリ\nA001,電化製品\n", encoding="utf-8"
    )

    import backend.database
    importlib.reload(backend.database)
    import backend.main
    importlib.reload(backend.main)


@pytest.fixture
def client():
    from backend.main import app
    return TestClient(app)


def test_summary_empty_initially(client):
    res = client.get("/api/summary")
    assert res.status_code == 200
    assert res.json()["record_count"] == 0


def test_import_single_csv(client):
    csv_bytes = "日付,売上金額,取引先,商品コード\n2024-01-01,50000,顧客A,A001\n".encode("utf-8")
    res = client.post(
        "/api/import",
        files={"files": ("sales.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["record_count"] == 1


def test_get_data_after_import(client):
    csv_bytes = "日付,売上金額,取引先\n2024-01-01,100,A\n2024-01-02,200,B\n".encode("utf-8")
    client.post(
        "/api/import",
        files={"files": ("t.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    res = client.get("/api/data")
    assert res.status_code == 200
    assert res.json()["total"] == 2


def test_get_config_mapping(client):
    res = client.get("/api/config/mapping")
    assert res.status_code == 200
    assert "amount" in res.json()["content"]


def test_get_config_value_mapping(client):
    res = client.get("/api/config/value_mapping")
    assert res.status_code == 200
    assert "商品コード" in res.json()["content"]


def test_put_config_updates_file(client):
    res = client.put("/api/config/mapping", json={"content": "new_col,新カラム\n"})
    assert res.status_code == 200
    assert res.json()["success"] is True
    # verify round-trip
    res2 = client.get("/api/config/mapping")
    assert "new_col" in res2.json()["content"]


def test_export_endpoint(client):
    csv_bytes = "売上金額\n100\n200\n".encode("utf-8")
    client.post(
        "/api/import",
        files={"files": ("t.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    res = client.post("/api/export")
    assert res.status_code == 200
    assert res.json()["success"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_api.py -v
```

Expected: `ImportError: cannot import name 'app' from 'backend.main'`

- [ ] **Step 3: Create backend/main.py**

```python
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

from backend.database import export_to_excel, get_records, get_summary, save_dataframe
from backend.processor import (
    load_header_mapping,
    load_value_mapping,
    process_files,
)

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
            dest = Path(tmpdir) / (upload.filename or "file")
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
def api_put_config(config_type: str, body: dict):
    if config_type not in ("mapping", "value_mapping"):
        raise HTTPException(status_code=404, detail="Unknown config type")
    path = _config_dir() / f"{config_type}_config.csv"
    path.write_text(body.get("content", ""), encoding="utf-8")
    return {"success": True}


@app.post("/api/export")
def api_export():
    output_path = str(_export_dir() / "export.xlsx")
    try:
        export_to_excel(output_path)
        return {"success": True, "path": output_path}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


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
```

- [ ] **Step 4: Run API tests**

```bash
pytest tests/test_api.py -v
```

Expected: All 7 tests PASS.

- [ ] **Step 5: Run full test suite**

```bash
pytest tests/ -v
```

Expected: All tests PASS (no failures).

- [ ] **Step 6: Commit**

```bash
git add backend/main.py tests/test_api.py
git commit -m "feat: FastAPI backend with import, export, config, and data endpoints"
```

---

## Task 6: Frontend Setup (Vue 3 + Vite + Tailwind)

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/style.css`
- Create: `frontend/src/main.js`
- Create: `frontend/src/router/index.js`
- Create: `frontend/src/api/index.js`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/views/Dashboard.vue` (placeholder)
- Create: `frontend/src/views/Import.vue` (placeholder)
- Create: `frontend/src/views/ConfigManager.vue` (placeholder)
- Create: `frontend/src/views/Export.vue` (placeholder)

- [ ] **Step 1: Create frontend/package.json**

```json
{
  "name": "sales-aggregator-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "axios": "^1.7.7",
    "vue": "^3.5.12",
    "vue-router": "^4.4.5"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.1.4",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.14",
    "vite": "^5.4.10"
  }
}
```

- [ ] **Step 2: Create frontend/vite.config.js**

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8765',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
```

- [ ] **Step 3: Create frontend/tailwind.config.js**

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50:  '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
      },
    },
  },
  plugins: [],
}
```

- [ ] **Step 4: Create frontend/postcss.config.js**

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 5: Create frontend/index.html**

```html
<!DOCTYPE html>
<html lang="ja">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Sales Data Aggregator</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
```

- [ ] **Step 6: Create frontend/src/style.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 7: Create frontend/src/router/index.js**

```javascript
import { createRouter, createWebHashHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Import from '../views/Import.vue'
import ConfigManager from '../views/ConfigManager.vue'
import Export from '../views/Export.vue'

export default createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/',        component: Dashboard },
    { path: '/import',  component: Import },
    { path: '/config',  component: ConfigManager },
    { path: '/export',  component: Export },
  ],
})
```

- [ ] **Step 8: Create frontend/src/api/index.js**

```javascript
import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 30000 })

export const getSummary  = ()            => api.get('/summary')
export const getData     = (page = 1, pageSize = 100) =>
  api.get('/data', { params: { page, page_size: pageSize } })

export const importFiles = (files) => {
  const form = new FormData()
  for (const f of files) form.append('files', f)
  return api.post('/import', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  })
}

export const getConfig    = (type)          => api.get(`/config/${type}`)
export const updateConfig = (type, content) => api.put(`/config/${type}`, { content })

export const triggerExport  = ()  => api.post('/export')
export const downloadExport = ()  => window.open('/api/export/download', '_blank')
```

- [ ] **Step 9: Create frontend/src/main.js**

```javascript
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './style.css'

createApp(App).use(router).mount('#app')
```

- [ ] **Step 10: Create frontend/src/App.vue**

```vue
<template>
  <div class="min-h-screen bg-gray-50 flex">
    <!-- Sidebar -->
    <aside class="w-56 bg-white shadow-md flex flex-col shrink-0">
      <div class="p-4 border-b">
        <h1 class="text-lg font-bold text-primary-700">売上集計</h1>
        <p class="text-xs text-gray-400">Sales Aggregator</p>
      </div>
      <nav class="flex-1 p-3 space-y-1">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="$route.path === item.to
            ? 'bg-primary-600 text-white'
            : 'text-gray-600 hover:bg-gray-100'"
        >
          <span>{{ item.icon }}</span>{{ item.label }}
        </RouterLink>
      </nav>
    </aside>
    <!-- Main -->
    <main class="flex-1 p-6 overflow-auto">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
const navItems = [
  { to: '/',       icon: '📊', label: 'ダッシュボード' },
  { to: '/import', icon: '📥', label: 'インポート' },
  { to: '/config', icon: '⚙️',  label: '設定管理' },
  { to: '/export', icon: '📤', label: 'エクスポート' },
]
</script>
```

- [ ] **Step 11: Create placeholder view files**

`frontend/src/views/Dashboard.vue`:
```vue
<template><div><p class="text-gray-400">Loading Dashboard...</p></div></template>
```

`frontend/src/views/Import.vue`:
```vue
<template><div><p class="text-gray-400">Loading Import...</p></div></template>
```

`frontend/src/views/ConfigManager.vue`:
```vue
<template><div><p class="text-gray-400">Loading Config...</p></div></template>
```

`frontend/src/views/Export.vue`:
```vue
<template><div><p class="text-gray-400">Loading Export...</p></div></template>
```

- [ ] **Step 12: Install dependencies and verify dev server**

```bash
cd frontend && npm install && npm run dev
```

Expected: Vite starts at `http://localhost:5173`. Open in browser — sidebar shows 4 nav items. Stop server with Ctrl+C.

```bash
cd ..
```

- [ ] **Step 13: Commit**

```bash
git add frontend/
git commit -m "feat: Vue 3 + Vite + Tailwind scaffold with router, API client, App shell"
```

---

## Task 7: Dashboard View

**Files:**
- Modify: `frontend/src/views/Dashboard.vue`

- [ ] **Step 1: Replace Dashboard.vue with full implementation**

```vue
<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-800 mb-6">ダッシュボード</h2>

    <!-- Stats row -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
      <div class="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
        <p class="text-sm text-gray-500">総レコード数</p>
        <p class="text-3xl font-bold text-primary-600 mt-1">
          {{ summary.record_count.toLocaleString() }}
        </p>
      </div>
      <div class="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
        <p class="text-sm text-gray-500">最終インポート</p>
        <p class="text-base font-semibold text-gray-700 mt-1">{{ formattedDate }}</p>
      </div>
      <div class="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
        <p class="text-sm text-gray-500">ファイル数</p>
        <p class="text-3xl font-bold text-green-600 mt-1">{{ summary.files.length }}</p>
      </div>
    </div>

    <!-- Column chips -->
    <div
      v-if="summary.columns.length"
      class="bg-white rounded-xl shadow-sm p-5 border border-gray-100 mb-6"
    >
      <h3 class="text-sm font-semibold text-gray-600 mb-3">データカラム</h3>
      <div class="flex flex-wrap gap-2">
        <span
          v-for="col in summary.columns"
          :key="col"
          class="px-3 py-1 bg-blue-50 text-blue-700 text-xs font-medium rounded-full"
        >{{ col }}</span>
      </div>
    </div>

    <!-- File list -->
    <div
      v-if="summary.files.length"
      class="bg-white rounded-xl shadow-sm p-5 border border-gray-100"
    >
      <h3 class="text-sm font-semibold text-gray-600 mb-3">インポート済みファイル</h3>
      <ul class="space-y-1">
        <li
          v-for="file in summary.files"
          :key="file"
          class="flex items-center gap-2 text-sm text-gray-700"
        >
          <span class="text-green-500">✓</span>{{ file }}
        </li>
      </ul>
    </div>

    <!-- Empty state -->
    <div
      v-if="!loading && summary.record_count === 0"
      class="text-center py-16 text-gray-400"
    >
      <p class="text-5xl mb-4">📂</p>
      <p class="text-lg font-medium">データがありません</p>
      <p class="text-sm mt-1">「インポート」からファイルを読み込んでください</p>
    </div>

    <div v-if="error" class="mt-4 p-4 bg-red-50 text-red-700 rounded-lg text-sm">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getSummary } from '../api/index.js'

const summary = ref({ record_count: 0, last_import: null, files: [], columns: [] })
const loading = ref(true)
const error = ref(null)

const formattedDate = computed(() =>
  summary.value.last_import
    ? new Date(summary.value.last_import).toLocaleString('ja-JP')
    : '—'
)

onMounted(async () => {
  try {
    const res = await getSummary()
    summary.value = res.data
  } catch (e) {
    error.value = 'データの取得に失敗しました: ' + e.message
  } finally {
    loading.value = false
  }
})
</script>
```

- [ ] **Step 2: Verify in browser**

Start backend: `uvicorn backend.main:app --reload --port 8765`
Start frontend: `cd frontend && npm run dev`

Open `http://localhost:5173`. Dashboard shows empty state with instructions.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/Dashboard.vue
git commit -m "feat: Dashboard view with stats, column chips, and file list"
```

---

## Task 8: Import View

**Files:**
- Modify: `frontend/src/views/Import.vue`

- [ ] **Step 1: Replace Import.vue**

```vue
<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-800 mb-6">インポート</h2>

    <!-- Drop zone -->
    <div
      class="border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors mb-6"
      :class="isDragging
        ? 'border-primary-500 bg-blue-50'
        : 'border-gray-300 hover:border-primary-400'"
      @dragover.prevent="isDragging = true"
      @dragleave="isDragging = false"
      @drop.prevent="onDrop"
      @click="fileInput.click()"
    >
      <p class="text-4xl mb-3">📁</p>
      <p class="text-gray-600 font-medium">ファイルをドロップ、またはクリックして選択</p>
      <p class="text-gray-400 text-sm mt-1">CSV, TXT, XLSX, XLS に対応</p>
      <input
        ref="fileInput"
        type="file"
        multiple
        accept=".csv,.txt,.tsv,.xlsx,.xls"
        class="hidden"
        @change="onFileSelect"
      />
    </div>

    <!-- Selected files -->
    <div
      v-if="selectedFiles.length"
      class="bg-white rounded-xl shadow-sm border border-gray-100 mb-6"
    >
      <div class="p-4 border-b flex justify-between items-center">
        <h3 class="font-semibold text-gray-700">選択ファイル ({{ selectedFiles.length }}件)</h3>
        <button class="text-sm text-red-500 hover:text-red-700" @click="selectedFiles = []">
          クリア
        </button>
      </div>
      <ul class="divide-y">
        <li
          v-for="(file, i) in selectedFiles"
          :key="i"
          class="px-4 py-3 flex justify-between text-sm"
        >
          <span class="text-gray-700">{{ file.name }}</span>
          <span class="text-gray-400">{{ fmtSize(file.size) }}</span>
        </li>
      </ul>
    </div>

    <!-- Import button -->
    <button
      v-if="selectedFiles.length"
      :disabled="importing"
      class="w-full py-3 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 text-white font-semibold rounded-xl transition-colors"
      @click="doImport"
    >
      {{ importing ? '処理中...' : `${selectedFiles.length}件をインポート` }}
    </button>

    <!-- Result -->
    <div v-if="result" class="mt-6">
      <div
        class="p-4 rounded-xl border"
        :class="result.success
          ? 'bg-green-50 border-green-200 text-green-800'
          : 'bg-red-50 border-red-200 text-red-800'"
      >
        <p class="font-semibold">
          {{ result.success ? '✅ インポート完了' : '❌ インポート失敗' }}
        </p>
        <p v-if="result.success" class="text-sm mt-1">
          {{ result.record_count.toLocaleString() }}件のレコードを取り込みました
        </p>
        <ul v-if="result.errors?.length" class="mt-2 text-sm space-y-1">
          <li v-for="(e, i) in result.errors" :key="i" class="text-red-600">
            ⚠ {{ e.file }}: {{ e.error }}
          </li>
        </ul>
      </div>
    </div>

    <div v-if="error" class="mt-4 p-4 bg-red-50 text-red-700 rounded-lg text-sm">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { importFiles } from '../api/index.js'

const fileInput = ref(null)
const selectedFiles = ref([])
const isDragging = ref(false)
const importing = ref(false)
const result = ref(null)
const error = ref(null)

const fmtSize = (b) => b < 1024 ? `${b} B`
  : b < 1024 * 1024 ? `${(b / 1024).toFixed(1)} KB`
  : `${(b / (1024 * 1024)).toFixed(1)} MB`

const onFileSelect = (e) => {
  selectedFiles.value = Array.from(e.target.files)
  result.value = error.value = null
}

const onDrop = (e) => {
  isDragging.value = false
  selectedFiles.value = Array.from(e.dataTransfer.files).filter(
    (f) => /\.(csv|txt|tsv|xlsx|xls)$/i.test(f.name)
  )
  result.value = error.value = null
}

const doImport = async () => {
  importing.value = true
  result.value = error.value = null
  try {
    const res = await importFiles(selectedFiles.value)
    result.value = res.data
    selectedFiles.value = []
  } catch (e) {
    error.value = e.response?.data?.detail?.message || e.message || 'インポートエラー'
  } finally {
    importing.value = false
  }
}
</script>
```

- [ ] **Step 2: Test import with sample file**

With both servers running, open `http://localhost:5173/#/import`.
Drag `sales_data/sample.csv` into the drop zone → click the import button.

Expected: "✅ インポート完了 — 5件のレコードを取り込みました"

Navigate to Dashboard: `record_count` should be 5.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/Import.vue
git commit -m "feat: Import view with drag-and-drop and result feedback"
```

---

## Task 9: Config Manager View

**Files:**
- Modify: `frontend/src/views/ConfigManager.vue`

- [ ] **Step 1: Replace ConfigManager.vue**

```vue
<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-800 mb-6">設定管理</h2>

    <!-- Tab buttons -->
    <div class="flex gap-2 mb-6">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        :class="activeTab === tab.key
          ? 'bg-primary-600 text-white'
          : 'bg-white text-gray-600 border hover:bg-gray-50'"
        @click="switchTab(tab.key)"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Description banner -->
    <div class="mb-4 p-4 bg-blue-50 rounded-lg text-sm text-blue-800">
      <strong>{{ meta.title }}</strong><br />{{ meta.description }}
    </div>

    <!-- Text editor card -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div class="flex justify-between items-center px-4 py-3 border-b bg-gray-50">
        <span class="text-sm font-mono text-gray-500">{{ meta.filename }}</span>
        <button
          :disabled="saving"
          class="px-4 py-1.5 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 text-white text-sm font-semibold rounded-lg transition-colors"
          @click="saveConfig"
        >
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </div>
      <textarea
        v-model="content"
        class="w-full h-80 p-4 font-mono text-sm text-gray-800 focus:outline-none resize-none"
        placeholder="CSVを直接編集できます..."
        spellcheck="false"
      />
    </div>

    <!-- Save feedback -->
    <div
      v-if="saveResult"
      class="mt-4 p-3 rounded-lg text-sm"
      :class="saveResult.ok ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'"
    >
      {{ saveResult.ok ? '✅ 保存しました' : '❌ 保存に失敗しました: ' + saveResult.msg }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getConfig, updateConfig } from '../api/index.js'

const tabs = [
  { key: 'mapping',       label: '項目名マッピング' },
  { key: 'value_mapping', label: 'マスタ照合' },
]

const tabMeta = {
  mapping: {
    title: '項目名マッピング設定',
    description: '1列目: 正規カラム名、2列目以降: ファイル上の列名候補（複数可）',
    filename: 'mapping_config.csv',
  },
  value_mapping: {
    title: 'マスタ照合設定',
    description: '1行目ヘッダー: キー列名,追加列名  /  2行目以降: キー値,マッピング値',
    filename: 'value_mapping_config.csv',
  },
}

const activeTab  = ref('mapping')
const content    = ref('')
const saving     = ref(false)
const saveResult = ref(null)

const meta = computed(() => tabMeta[activeTab.value])

const loadConfig = async (type) => {
  try { content.value = (await getConfig(type)).data.content }
  catch (_) { content.value = '' }
}

const switchTab = async (key) => {
  activeTab.value = key
  saveResult.value = null
  await loadConfig(key)
}

const saveConfig = async () => {
  saving.value = true
  saveResult.value = null
  try {
    await updateConfig(activeTab.value, content.value)
    saveResult.value = { ok: true }
    setTimeout(() => { saveResult.value = null }, 3000)
  } catch (e) {
    saveResult.value = { ok: false, msg: e.message }
  } finally {
    saving.value = false
  }
}

onMounted(() => loadConfig('mapping'))
</script>
```

- [ ] **Step 2: Test Config Manager in browser**

Open `http://localhost:5173/#/config`.
Expected: `mapping_config.csv` content appears. Switch tab → `value_mapping_config.csv` loads.
Edit a line, click Save → "✅ 保存しました" toast for 3 seconds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/ConfigManager.vue
git commit -m "feat: Config Manager view with tab editor for both config CSVs"
```

---

## Task 10: Export View

**Files:**
- Modify: `frontend/src/views/Export.vue`

- [ ] **Step 1: Replace Export.vue**

```vue
<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-800 mb-6">エクスポート</h2>

    <!-- Record count card -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6 flex items-center gap-6">
      <span class="text-5xl">📊</span>
      <div>
        <p class="text-gray-500 text-sm">エクスポート対象レコード数</p>
        <p class="text-4xl font-bold text-primary-600">
          {{ summary.record_count.toLocaleString() }}
        </p>
      </div>
    </div>

    <!-- Generate button -->
    <button
      :disabled="exporting || summary.record_count === 0"
      class="w-full py-4 bg-green-600 hover:bg-green-700 disabled:bg-gray-300 text-white font-bold text-lg rounded-xl transition-colors mb-4"
      @click="doExport"
    >
      {{ exporting ? '生成中...' : 'Excelファイルを生成' }}
    </button>

    <!-- Download button (appears after successful export) -->
    <button
      v-if="exportDone"
      class="w-full py-4 bg-primary-600 hover:bg-primary-700 text-white font-bold text-lg rounded-xl transition-colors"
      @click="downloadExport()"
    >
      📥 ダウンロード (export.xlsx)
    </button>

    <!-- Status message -->
    <div
      v-if="statusMsg"
      class="mt-4 p-4 rounded-xl text-sm"
      :class="statusOk ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'"
    >
      {{ statusMsg }}
    </div>

    <!-- No-data warning -->
    <div
      v-if="summary.record_count === 0"
      class="mt-6 p-4 bg-yellow-50 text-yellow-700 rounded-lg text-sm"
    >
      ⚠️ データがありません。先に「インポート」からファイルを読み込んでください。
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getSummary, triggerExport, downloadExport } from '../api/index.js'

const summary    = ref({ record_count: 0 })
const exporting  = ref(false)
const exportDone = ref(false)
const statusMsg  = ref(null)
const statusOk   = ref(true)

const doExport = async () => {
  exporting.value = true
  statusMsg.value = null
  try {
    await triggerExport()
    exportDone.value = true
    statusOk.value   = true
    statusMsg.value  = 'ファイルを生成しました。ダウンロードボタンを押してください。'
  } catch (e) {
    statusOk.value  = false
    statusMsg.value = 'エクスポートに失敗しました: ' + (e.response?.data?.detail || e.message)
  } finally {
    exporting.value = false
  }
}

onMounted(async () => {
  try { summary.value = (await getSummary()).data } catch (_) {}
})
</script>
```

- [ ] **Step 2: Test Export view end-to-end**

With sample data imported, open `http://localhost:5173/#/export`.
Expected: record count 5 shown. Click "Excelファイルを生成" → success message + Download button appear.
Click Download → browser saves `export.xlsx`. Open in Excel — verify 5 rows, all columns including `カテゴリ` enrichment.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/Export.vue
git commit -m "feat: Export view with Excel generation and file download"
```

---

## Task 11: Production Build & PyInstaller Config

**Files:**
- Modify: `backend/main.py` (frozen-mode path fix — already included in Task 5)
- Create: `build.spec`
- Create: `build.py`

- [ ] **Step 1: Build Vue frontend**

```bash
cd frontend && npm run build && cd ..
```

Expected: `frontend/dist/` created with `index.html` and hashed asset files.

- [ ] **Step 2: Verify static serving in production mode**

```bash
uvicorn backend.main:app --port 8765
```

Open `http://127.0.0.1:8765` in a browser. Vue app must load from static files (sidebar visible, routes work). Stop server.

- [ ] **Step 3: Create build.spec**

```python
# PyInstaller spec — Sales Data Aggregator
from PyInstaller.utils.hooks import collect_all

block_cipher = None

webview_datas, webview_binaries, webview_hiddenimports = collect_all('webview')

a = Analysis(
    ['backend/main.py'],
    pathex=['.'],
    binaries=webview_binaries,
    datas=[
        ('frontend/dist', 'frontend/dist'),
        ('config',        'config'),
        *webview_datas,
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops', 'uvicorn.loops.auto',
        'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
        'uvicorn.lifespan', 'uvicorn.lifespan.off',
        'uvicorn.main',
        'fastapi',
        'sqlalchemy', 'sqlalchemy.dialects.sqlite',
        'pandas', 'openpyxl',
        *webview_hiddenimports,
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SalesAggregator',
    debug=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='SalesAggregator',
)
```

- [ ] **Step 4: Create build.py**

```python
#!/usr/bin/env python3
"""Build: compile Vue then package with PyInstaller."""
import subprocess
import sys
from pathlib import Path


def build_frontend():
    print("▶ Building Vue frontend...")
    subprocess.run(["npm", "run", "build"], cwd=Path(__file__).parent / "frontend", check=True)
    print("✓ Frontend built.")


def build_exe():
    print("▶ Running PyInstaller...")
    subprocess.run(
        [sys.executable, "-m", "PyInstaller", "build.spec", "--clean"],
        check=True,
    )
    print("✓ Executable built in dist/SalesAggregator/")


if __name__ == "__main__":
    build_frontend()
    build_exe()
    print("\n🎉 Build complete: dist/SalesAggregator/SalesAggregator.exe")
```

- [ ] **Step 5: Build the executable**

```bash
python build.py
```

Expected: `dist/SalesAggregator/SalesAggregator.exe` created without errors.

- [ ] **Step 6: Smoke-test the executable**

```bash
dist/SalesAggregator/SalesAggregator.exe
```

Expected: pywebview window opens, Vue app loads. Import `sales_data/sample.csv`, check Dashboard, generate export, download xlsx. All features work without a running Python environment.

- [ ] **Step 7: Commit**

```bash
git add build.spec build.py
git commit -m "feat: PyInstaller build config and helper build script"
```

---

## Self-Review Checklist

**Spec coverage:**
- ✅ `processor.py` — Tasks 2, 3 (header normalization, data enrichment, file integration)
- ✅ `database.py` — Task 4 (SQLite CRUD, Excel export)
- ✅ `main.py` FastAPI + pywebview — Task 5 + Task 11 desktop entry
- ✅ `mapping_config.csv` driven normalization — Tasks 2, 3
- ✅ `value_mapping_config.csv` driven enrichment — Tasks 2, 3
- ✅ Dashboard UI — Task 7
- ✅ Import UI (folder/multi-file) — Task 8
- ✅ Config Management UI — Task 9
- ✅ Export UI — Task 10
- ✅ PyInstaller `.exe` build — Task 11

**No placeholders found** — all steps contain complete code or runnable commands.

**Type consistency verified:**
- `process_files` → `Tuple[pd.DataFrame, List[dict]]` — consistent across Tasks 3, 5
- `load_value_mapping` → `Tuple[str, str, Dict[str, str]]` — destructured as `key_col, new_col, vm` consistently
- `save_dataframe(df, source_files)` → `int` — consistent across Tasks 4, 5
- `get_records()` → `{data, total, page, page_size}` — consistent across Tasks 4, 5, frontend api
