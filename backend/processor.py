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

    # Resolve key_col to its canonical name if it appears as an alias
    resolved_key_col = key_col
    if key_col:
        for canonical, aliases in header_mapping.items():
            if key_col == canonical or key_col in aliases:
                resolved_key_col = canonical
                break

    for file_path in file_paths:
        try:
            df = _read_file(file_path)
            df = normalize_headers(df, header_mapping)
            if value_mapping and resolved_key_col and new_col:
                df = enrich_data(df, value_mapping, resolved_key_col, new_col)
            df["_source_file"] = Path(file_path).name
            dfs.append(df)
        except Exception as exc:
            errors.append({"file": file_path, "error": str(exc)})

    if not dfs:
        return pd.DataFrame(), errors

    return pd.concat(dfs, ignore_index=True), errors
