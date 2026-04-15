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

    Missing keys -> 'N/A'. Missing key_col -> all 'N/A'.
    Key column values are coerced to str before lookup; value_mapping keys must be strings.
    """
    df = df.copy()
    if key_col not in df.columns:
        df[new_col] = "N/A"
        return df
    df[new_col] = df[key_col].astype(str).map(value_mapping).fillna("N/A")
    return df
