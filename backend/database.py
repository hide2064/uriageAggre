"""
database.py — データ永続化レイヤー
====================================
役割:
  - SQLite データベースへの売上データ保存 / 取得
  - インポート履歴 (import_log テーブル) の管理
  - Excel エクスポート

テーブル構成:
  sales_records  : インポートされた売上データ (スキーマ動的: インポートごとに再作成)
  import_log     : インポート履歴 (インポート日時・ファイル名・件数)

テスト分離:
  DATABASE_URL 環境変数でDB先を切り替えられる。
  テストでは monkeypatch + importlib.reload でこの環境変数を上書きして
  一時 SQLite DB を使用する。
"""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

import pandas as pd
from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# ---------------------------------------------------------------------------
# エンジンファクトリ
# ---------------------------------------------------------------------------

def _get_database_url() -> str:
    """接続先 DB URL を返す。

    環境変数 DATABASE_URL が設定されていればそれを使う。
    未設定時はカレントディレクトリの sales_data.db に接続する。
    テスト時は monkeypatch で一時 DB パスを注入する。
    """
    return os.environ.get("DATABASE_URL", "sqlite:///./sales_data.db")


def _make_engine():
    """SQLAlchemy エンジンを生成して返す。

    モジュールレベルでキャッシュせず毎回生成することで、
    テスト中に DATABASE_URL が変更された際も確実に新しい接続先を参照できる。

    check_same_thread=False: SQLite デフォルトは同一スレッドのみ許可だが、
    FastAPI の非同期スレッドプールからアクセスするため無効化する。
    """
    url = _get_database_url()
    return create_engine(url, connect_args={"check_same_thread": False})


# ---------------------------------------------------------------------------
# ORM モデル定義
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    """SQLAlchemy 2.x スタイルの宣言的基底クラス。"""
    pass


class ImportLog(Base):
    """インポート履歴テーブル。

    インポートのたびに 1 レコード追加される。
    sales_records が上書きされても履歴は蓄積され続ける。
    """
    __tablename__ = "import_log"

    id           = Column(Integer, primary_key=True, index=True)
    files        = Column(Text, nullable=False)        # JSON 配列: ["file1.csv", "file2.csv"]
    record_count = Column(Integer, nullable=False)     # インポートされた総レコード数
    imported_at  = Column(
        DateTime(timezone=True),                       # タイムゾーン付き日時 (UTC 保存)
        default=lambda: datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# データ保存
# ---------------------------------------------------------------------------

def save_dataframe(df: pd.DataFrame, source_files: List[str]) -> int:
    """売上 DataFrame を DB に保存してインポート件数を返す。

    sales_records テーブルは毎回 REPLACE (全件置換) される。
    これはアプリが「累積」ではなく「最新セット」を管理する設計のため。

    Args:
        df:           保存する売上 DataFrame
        source_files: インポート元ファイル名のリスト (import_log に記録)

    Returns:
        保存されたレコード数 (= len(df))
    """
    engine = _make_engine()

    # テーブルが未作成の場合は自動作成 (初回起動時など)
    Base.metadata.create_all(bind=engine)

    # if_exists="replace": 既存テーブルを DROP → CREATE → INSERT する
    # スキーマが動的に変わる (列名がファイルによって異なる) ため毎回再作成が安全
    df.to_sql("sales_records", engine, if_exists="replace", index=False)

    # インポート履歴を記録
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        session.add(
            ImportLog(
                files=json.dumps(source_files, ensure_ascii=False),  # 日本語ファイル名を保持
                record_count=len(df),
                imported_at=datetime.now(timezone.utc),
            )
        )
        session.commit()
    finally:
        session.close()  # try/finally で必ずセッションをクローズ

    return len(df)


# ---------------------------------------------------------------------------
# サマリー取得 (ダッシュボード向け)
# ---------------------------------------------------------------------------

def get_summary() -> Dict[str, Any]:
    """ダッシュボードに表示するサマリー情報を返す。

    Returns:
        {
          "record_count": int,        最新インポートのレコード数
          "last_import":  str | None, 最終インポート日時 (ISO 8601)
          "files":        list[str],  最終インポートのファイル名リスト
          "columns":      list[str],  _ で始まる内部列を除いたカラム名リスト
        }
        インポート履歴が存在しない場合は record_count=0, last_import=None を返す。
    """
    engine = _make_engine()
    Base.metadata.create_all(bind=engine)

    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        # 最新のインポートログを1件取得
        log = (
            session.query(ImportLog)
            .order_by(ImportLog.imported_at.desc())
            .first()
        )
    finally:
        session.close()

    # まだ1回もインポートされていない場合の初期値
    if log is None:
        return {"record_count": 0, "last_import": None, "files": [], "columns": []}

    # sales_records のカラム名を1件サンプリングして取得
    try:
        sample = pd.read_sql("SELECT * FROM sales_records LIMIT 1", engine)
        # "_source_file" などの内部管理列 (_ 始まり) はUIに表示しない
        columns = [c for c in sample.columns if not c.startswith("_")]
    except Exception:
        # テーブルが存在しない場合などは空リスト
        columns = []

    return {
        "record_count": log.record_count,
        "last_import":  log.imported_at.isoformat(),
        "files":        json.loads(log.files),
        "columns":      columns,
    }


# ---------------------------------------------------------------------------
# ページネーション付きレコード取得
# ---------------------------------------------------------------------------

def get_records(page: int = 1, page_size: int = 100) -> Dict[str, Any]:
    """sales_records テーブルからページネーション付きでレコードを返す。

    Args:
        page:      1 始まりのページ番号
        page_size: 1 ページあたりの件数

    Returns:
        {
          "data":      list[dict],  該当ページのレコード
          "total":     int,         全件数
          "page":      int,         現在ページ
          "page_size": int,         ページサイズ
        }

    Raises:
        TypeError:  page / page_size が int 型でない場合
        ValueError: page / page_size が 1 未満の場合
    """
    # ── 入力バリデーション ──────────────────────────────────────────────────
    # FastAPI の型アノテーションだけでは Python ランタイムで保証されないため
    # 明示的に型チェックを行いSQLインジェクションリスクを排除する
    if not isinstance(page, int) or not isinstance(page_size, int):
        raise TypeError("page and page_size must be integers")
    if page < 1 or page_size < 1:
        raise ValueError("page and page_size must be positive integers")

    engine = _make_engine()
    try:
        # 全件数を取得 (ページネーション用)
        total = int(
            pd.read_sql("SELECT COUNT(*) AS cnt FROM sales_records", engine)
            .iloc[0]["cnt"]
        )

        # OFFSET = (ページ番号 - 1) × ページサイズ
        offset = (page - 1) * page_size
        df = pd.read_sql(
            f"SELECT * FROM sales_records LIMIT {page_size} OFFSET {offset}",
            engine,
        )
        return {
            "data":      df.to_dict(orient="records"),
            "total":     total,
            "page":      page,
            "page_size": page_size,
        }
    except Exception as exc:
        # "no such table": インポート前は sales_records が存在しないため正常ケース
        if "no such table" in str(exc).lower():
            return {"data": [], "total": 0, "page": page, "page_size": page_size}
        raise  # それ以外のエラーは上位へ伝播させる


# ---------------------------------------------------------------------------
# Excel エクスポート
# ---------------------------------------------------------------------------

def export_to_excel(output_path: str) -> str:
    """sales_records の全データを Excel ファイルに出力する。

    内部管理列 (_ 始まり、例: _source_file) はエクスポートから除外する。

    Args:
        output_path: 出力先 Excel ファイルパス (.xlsx)

    Returns:
        output_path (呼び出し元の確認用)

    Raises:
        OperationalError: sales_records テーブルが存在しない場合 (未インポート時)
    """
    engine = _make_engine()

    # 全件取得 (エクスポートは件数制限なし)
    df = pd.read_sql("SELECT * FROM sales_records", engine)

    # _ で始まる内部管理列を除去してからエクスポート
    df = df[[c for c in df.columns if not c.startswith("_")]]

    # index=False: DataFrame のインデックス列 (0,1,2...) は出力しない
    df.to_excel(output_path, index=False)
    return output_path
