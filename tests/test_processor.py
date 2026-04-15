import pytest
import pandas as pd
from backend.processor import (
    normalize_headers, enrich_data,
    load_header_mapping, load_value_mapping, process_files,
)


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
        assert list(result.columns) == ["amount"]

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
        # Verify actual enriched values (proves canonical key resolution round-trip worked)
        cat_values = set(df[new_col].tolist())
        assert "電化製品" in cat_values
        assert "食品" in cat_values

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

    def test_all_files_fail_returns_empty_df(self, sample_mapping_config):
        hm = load_header_mapping(sample_mapping_config)
        df, errors = process_files(["/bad1.csv", "/bad2.csv"], hm)
        assert df.empty
        assert len(errors) == 2
