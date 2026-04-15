"""
processor.py — ETL (Extract / Transform / Load) パイプライン
=============================================================
役割:
  1. 複数の売上ファイル (CSV / Excel) を読み込む
  2. 列名をユーザー定義マッピングに従い正規化する
     例: "売上金額" → "amount"
  3. マスタ照合によって新しい列を付加する
     例: 商品コード "A001" → カテゴリ "電化製品"
  4. 全ファイルを結合して単一の DataFrame を返す

外部依存:
  - pandas      : DataFrame 操作
  - csv (標準)  : CSV / BOM 処理
"""

import csv
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# ヘッダー正規化
# ---------------------------------------------------------------------------

def normalize_headers(
    df: pd.DataFrame,
    header_mapping: Dict[str, List[str]],
) -> pd.DataFrame:
    """DataFrame の列名を正規名 (canonical name) に変換する。

    Args:
        df:             変換対象の DataFrame (元データは変更しない)
        header_mapping: {正規名: [別名1, 別名2, ...]} の辞書
                        例: {"amount": ["売上金額", "金額", "Amount"]}

    Returns:
        列名が正規化された新しい DataFrame。
        マッピングに該当しない列はそのまま残る。

    Note:
        同じ別名が複数の正規名に登録されている場合は、
        辞書の挿入順で最初に一致した正規名が使われる。
    """
    # 元 DataFrame を変更しないようコピーを作成
    df = df.copy()

    # 列名の前後の空白を除去 (Excel やメモ帳で誤って入力されがちな全角スペースも除去される)
    df.columns = [c.strip() for c in df.columns]

    # {現在の列名: 正規名} のリネームマップを構築
    rename_map: Dict[str, str] = {}
    for col in df.columns:
        for canonical, aliases in header_mapping.items():
            # 既に正規名と同じ列名の場合、またはエイリアスに含まれる場合はリネーム対象
            if col == canonical or col in aliases:
                rename_map[col] = canonical
                break  # 先に一致したものを採用して次の列へ

    return df.rename(columns=rename_map)


# ---------------------------------------------------------------------------
# マスタ照合 (データエンリッチメント)
# ---------------------------------------------------------------------------

def enrich_data(
    df: pd.DataFrame,
    value_mapping: Dict[str, str],
    key_col: str,
    new_col: str,
) -> pd.DataFrame:
    """キー列の値をマスタ辞書で引いて新しい列を追加する。

    Args:
        df:            変換対象の DataFrame (元データは変更しない)
        value_mapping: {キー値: 付加値} の辞書
                       例: {"A001": "電化製品", "B001": "食品"}
        key_col:       照合に使うキー列名 (正規名であること)
        new_col:       追加する列名

    Returns:
        new_col が追加された新しい DataFrame。

    Note:
        - キー列が存在しない場合は new_col を全て "N/A" で埋める。
        - マスタに存在しないキー値も "N/A" になる。
        - key_col の値は str に変換してから照合する。
          value_mapping のキーは必ず文字列にすること。
    """
    df = df.copy()

    # キー列が存在しない場合 (列名の正規化漏れなど) は全行 N/A
    if key_col not in df.columns:
        df[new_col] = "N/A"
        return df

    # map() でベクトル一括変換し、未一致は fillna で N/A に置換
    df[new_col] = df[key_col].astype(str).map(value_mapping).fillna("N/A")
    return df


# ---------------------------------------------------------------------------
# 設定ファイルローダー
# ---------------------------------------------------------------------------

def load_header_mapping(config_path: str) -> Dict[str, List[str]]:
    """mapping_config.csv を読み込んで列名マッピング辞書を返す。

    CSV フォーマット (BOM あり UTF-8 対応):
        正規名,別名1,別名2,...
        例: amount,売上金額,金額,Amount,revenue

    Args:
        config_path: mapping_config.csv のパス

    Returns:
        {正規名: [別名1, 別名2, ...]} の辞書
        正規名自体はエイリアスリストに含まれない点に注意。
    """
    mapping: Dict[str, List[str]] = {}
    # utf-8-sig: Excel が出力する UTF-8 BOM (EF BB BF) を自動除去する
    with open(config_path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            # 空行またはコメント行 (先頭が空) をスキップ
            if not row or not row[0].strip():
                continue
            canonical = row[0].strip()
            # 2列目以降がエイリアス。空文字は除外する
            aliases = [a.strip() for a in row[1:] if a.strip()]
            mapping[canonical] = aliases
    return mapping


def load_value_mapping(config_path: str) -> Tuple[str, str, Dict[str, str]]:
    """value_mapping_config.csv を読み込んでマスタ辞書を返す。

    CSV フォーマット:
        1行目 (ヘッダー行): キー列名,追加列名
            例: 商品コード,カテゴリ
        2行目以降 (データ行): キー値,マッピング値
            例: A001,電化製品

    Args:
        config_path: value_mapping_config.csv のパス

    Returns:
        (key_col, new_col, {キー値: マッピング値}) のタプル
        ファイルが空またはヘッダーのみの場合は ("", "", {}) を返す。
    """
    with open(config_path, encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))

    # ファイルが空または列数不足の場合は空を返す
    if not rows or len(rows[0]) < 2:
        return "", "", {}

    # 1行目からキー列名と追加列名を取得
    key_col = rows[0][0].strip()
    new_col = rows[0][1].strip()

    # 2行目以降をキー → 値 の辞書に変換
    mapping: Dict[str, str] = {}
    for row in rows[1:]:
        if len(row) >= 2 and row[0].strip():
            mapping[row[0].strip()] = row[1].strip()

    return key_col, new_col, mapping


# ---------------------------------------------------------------------------
# 内部ユーティリティ: ファイル読み込み
# ---------------------------------------------------------------------------

def _read_file(file_path: str) -> pd.DataFrame:
    """CSV / TSV / TXT / Excel ファイルを DataFrame として読み込む。

    エンコーディング戦略 (テキスト系):
        1. utf-8-sig: BOM 付き UTF-8 (Excel の CSV 保存が該当)
        2. cp932   : Windows 日本語環境の標準エンコーディング (Shift-JIS 上位互換)
        3. utf-8   : BOM なし UTF-8

    Args:
        file_path: 読み込むファイルのパス

    Returns:
        読み込んだ DataFrame

    Raises:
        ValueError: サポートしない拡張子、またはすべてのエンコーディングで失敗した場合
    """
    suffix = Path(file_path).suffix.lower()

    if suffix in (".csv", ".txt", ".tsv"):
        # エンコーディングを順番に試してみる
        for encoding in ("utf-8-sig", "cp932", "utf-8"):
            try:
                return pd.read_csv(file_path, encoding=encoding)
            except UnicodeDecodeError:
                continue  # 次のエンコーディングを試す
        raise ValueError(f"Cannot decode {file_path} with known encodings")

    elif suffix in (".xlsx", ".xls"):
        # Excel ファイルはエンコーディング不要 (openpyxl / xlrd が処理)
        return pd.read_excel(file_path)

    else:
        raise ValueError(f"Unsupported file type: {suffix}")


# ---------------------------------------------------------------------------
# メイン処理: 複数ファイルの処理と結合
# ---------------------------------------------------------------------------

def process_files(
    file_paths: List[str],
    header_mapping: Dict[str, List[str]],
    value_mapping: Optional[Dict[str, str]] = None,
    key_col: Optional[str] = None,
    new_col: Optional[str] = None,
) -> Tuple[pd.DataFrame, List[dict]]:
    """複数のファイルを読み込み、正規化・エンリッチメント後に結合して返す。

    処理フロー:
        1. key_col をマッピングで正規名に解決
        2. 各ファイルを _read_file() で読み込む
        3. normalize_headers() で列名を正規化
        4. enrich_data() でマスタ照合列を追加 (設定がある場合)
        5. _source_file 列 (元ファイル名) を追加
        6. 全 DataFrame を pd.concat で縦結合

    Args:
        file_paths:     処理対象ファイルパスのリスト
        header_mapping: load_header_mapping() の戻り値
        value_mapping:  load_value_mapping() の戻り値[2] (省略可)
        key_col:        マスタ照合に使う列名 — CSV の元の列名でも可
                        (内部でヘッダーマッピングを使って正規名に変換する)
        new_col:        マスタ照合で追加する列名

    Returns:
        (結合済み DataFrame, エラーリスト) のタプル。
        エラーリストの各要素は {'file': パス, 'error': メッセージ}。
        全ファイルが失敗した場合は空の DataFrame を返す。
    """
    dfs: List[pd.DataFrame] = []
    errors: List[dict] = []

    # ── key_col の正規名解決 ────────────────────────────────────────────────
    # value_mapping_config.csv のヘッダー行から得た key_col (例: "商品コード") は
    # ファイル上の生の列名であり、ヘッダー正規化後は "product_code" になっている。
    # enrich_data() に渡す前に正規名へ変換しなければ列が見つからずすべて N/A になる。
    resolved_key_col = key_col
    if key_col:
        for canonical, aliases in header_mapping.items():
            if key_col == canonical or key_col in aliases:
                resolved_key_col = canonical
                break
        else:
            # for-else: break されずにループ完了 → マッピングに key_col が存在しない
            errors.append({
                "file": "__config__",
                "error": f"key_col '{key_col}' not found in header_mapping; enrichment column will be all N/A",
            })

    # ── 各ファイルの処理 ────────────────────────────────────────────────────
    for file_path in file_paths:
        try:
            df = _read_file(file_path)
            df = normalize_headers(df, header_mapping)

            # マスタ照合は value_mapping, resolved_key_col, new_col がすべて揃った場合のみ実行
            if value_mapping and resolved_key_col and new_col:
                df = enrich_data(df, value_mapping, resolved_key_col, new_col)

            # 元ファイル名を内部列 (_source_file) に記録 (エクスポート時には除外される)
            df["_source_file"] = Path(file_path).name
            dfs.append(df)

        except Exception as exc:
            # 1 ファイルが失敗しても他ファイルの処理を継続する
            errors.append({"file": file_path, "error": str(exc)})

    # ── 結合 ───────────────────────────────────────────────────────────────
    if not dfs:
        # すべてのファイルが失敗した場合は空 DataFrame を返す
        return pd.DataFrame(), errors

    # ignore_index=True: 各 DataFrame のインデックスをリセットして連番に振り直す
    return pd.concat(dfs, ignore_index=True), errors
