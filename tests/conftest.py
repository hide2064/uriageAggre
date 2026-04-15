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
