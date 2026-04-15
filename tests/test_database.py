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
