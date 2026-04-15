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
