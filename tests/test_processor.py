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
