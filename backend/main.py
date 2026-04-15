"""
main.py — FastAPI アプリケーション & デスクトップ起動エントリポイント
=======================================================================
役割:
  - FastAPI で REST API を提供する
  - Vue 3 のビルド成果物 (frontend/dist) を静的ファイルとして配信する
  - pywebview でブラウザウィンドウをデスクトップアプリとして起動する
  - PyInstaller でパッケージング済みの場合も動作するようパス解決を行う

起動方法 (開発):
  uvicorn backend.main:app --reload --port 8765

起動方法 (デスクトップ):
  python backend/main.py  →  start_desktop() が呼ばれる

API エンドポイント一覧:
  GET  /api/summary                 ダッシュボード用サマリー
  POST /api/import                  ファイルアップロード & ETL
  GET  /api/data                    ページネーション付きレコード取得
  GET  /api/config/{type}           設定 CSV の読み込み
  PUT  /api/config/{type}           設定 CSV の上書き保存
  POST /api/export                  Excel ファイル生成
  GET  /api/export/download         生成済み Excel のダウンロード
"""

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
from pydantic import BaseModel

from backend.database import export_to_excel, get_records, get_summary, save_dataframe
from backend.processor import (
    load_header_mapping,
    load_value_mapping,
    process_files,
)


# ---------------------------------------------------------------------------
# リクエストボディ定義
# ---------------------------------------------------------------------------

class ConfigUpdateBody(BaseModel):
    """PUT /api/config/{type} のリクエストボディ。

    content フィールドが必須であることを Pydantic が保証する。
    未指定時は HTTP 422 (Unprocessable Entity) が自動返却される。
    """
    content: str  # 設定 CSV の全文テキスト


# ---------------------------------------------------------------------------
# FastAPI アプリケーションの初期化
# ---------------------------------------------------------------------------

app = FastAPI(title="Sales Data Aggregator")

# CORS ミドルウェア
# pywebview はローカルの組み込みブラウザで動作するため、
# デスクトップアプリとして使用する場合はオリジン制限が不要。
# 開発時の Vite dev server (localhost:5173) からのアクセスも許可する。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # 全オリジンを許可 (デスクトップアプリ用途)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# パス解決ユーティリティ
# ---------------------------------------------------------------------------

def _get_base_dir() -> Path:
    """プロジェクトルートディレクトリを返す。

    PyInstaller でパッケージング済みの場合は sys._MEIPASS (展開先一時ディレクトリ)、
    開発時は このファイルの 2 階層上 (= プロジェクトルート) を返す。
    """
    if getattr(sys, "frozen", False):
        # PyInstaller の onedir モード: 実行時に _MEIPASS に全リソースが展開される
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    # 開発時: backend/main.py → backend/ → プロジェクトルート
    return Path(__file__).parent.parent


# モジュールロード時にベースディレクトリを確定する
_BASE_DIR = _get_base_dir()


def _config_dir() -> Path:
    """設定ファイルディレクトリのパスを返す。

    優先順位:
      1. 環境変数 CONFIG_DIR (テスト時に一時ディレクトリを注入できる)
      2. カレントディレクトリ / config  (uvicorn をプロジェクトルートから起動した場合)
      3. _BASE_DIR / config             (PyInstaller パッケージ内)
    """
    env = os.environ.get("CONFIG_DIR")
    if env:
        return Path(env)
    cwd_config = Path.cwd() / "config"
    if cwd_config.exists():
        return cwd_config
    return _BASE_DIR / "config"


def _export_dir() -> Path:
    """Excel エクスポート先ディレクトリを返す。ディレクトリが存在しない場合は作成する。

    優先順位:
      1. 環境変数 EXPORT_DIR
      2. _BASE_DIR / exports
    """
    env = os.environ.get("EXPORT_DIR")
    d = Path(env) if env else _BASE_DIR / "exports"
    d.mkdir(parents=True, exist_ok=True)  # 初回アクセス時にディレクトリを自動生成
    return d


# ---------------------------------------------------------------------------
# API ルート
# ---------------------------------------------------------------------------

@app.get("/api/summary")
def api_summary():
    """ダッシュボード用サマリーを返す。

    Response:
        {record_count, last_import, files, columns}
    """
    return get_summary()


@app.post("/api/import")
async def api_import(files: List[UploadFile] = File(...)):
    """アップロードされたファイルを ETL パイプラインで処理して DB に保存する。

    処理フロー:
      1. アップロードファイルを一時ディレクトリに保存
      2. mapping_config.csv からヘッダーマッピングを読み込む
      3. value_mapping_config.csv からマスタ照合設定を読み込む (任意)
      4. process_files() で正規化・エンリッチメント・結合
      5. save_dataframe() で DB に保存
      ※ 一時ディレクトリは with ブロック終了時に自動削除される

    Response:
        {"success": true, "record_count": N, "errors": [...]}

    Raises:
        HTTPException 400: 全ファイルが失敗してデータが空の場合
    """
    # 一時ディレクトリにアップロードファイルを保存
    with tempfile.TemporaryDirectory() as tmpdir:
        saved: List[str] = []
        for upload in files:
            # Path(...).name でディレクトリトラバーサル攻撃を防ぐ
            # (例: "../../etc/passwd" → "passwd" に変換)
            safe_name = Path(upload.filename or "file").name or "file"
            dest = Path(tmpdir) / safe_name
            dest.write_bytes(await upload.read())
            saved.append(str(dest))

        # ヘッダーマッピング設定を読み込む
        header_mapping = load_header_mapping(str(_config_dir() / "mapping_config.csv"))

        # マスタ照合設定を読み込む (ファイルが存在する場合のみ)
        value_mapping = None
        key_col = new_col = None
        vm_path = _config_dir() / "value_mapping_config.csv"
        if vm_path.exists():
            key_col, new_col, value_mapping = load_value_mapping(str(vm_path))

        # ETL パイプライン実行
        df, errors = process_files(saved, header_mapping, value_mapping, key_col, new_col)

    # 一時ディレクトリが削除された後に DB 保存を行う (DataFrame はメモリ上にある)
    if df.empty:
        raise HTTPException(
            status_code=400,
            detail={"message": "No data processed", "errors": errors},
        )

    count = save_dataframe(df, [f.filename for f in files])
    return {"success": True, "record_count": count, "errors": errors}


@app.get("/api/data")
def api_data(page: int = 1, page_size: int = 100):
    """ページネーション付きで sales_records を返す。

    Query params:
        page      : ページ番号 (1 始まり、デフォルト 1)
        page_size : 1 ページあたりの件数 (デフォルト 100)

    Response:
        {data: [...], total: N, page: N, page_size: N}
    """
    return get_records(page=page, page_size=page_size)


@app.get("/api/config/{config_type}")
def api_get_config(config_type: str):
    """設定 CSV ファイルの内容をテキストとして返す。

    Path params:
        config_type: "mapping" または "value_mapping" のみ許可 (ホワイトリスト)

    Response:
        {"content": "<CSV テキスト全文>"}
    """
    # ホワイトリストによるパストラバーサル防止
    if config_type not in ("mapping", "value_mapping"):
        raise HTTPException(status_code=404, detail="Unknown config type")
    path = _config_dir() / f"{config_type}_config.csv"
    if not path.exists():
        return {"content": ""}
    # utf-8-sig: BOM 付き UTF-8 (Excel 保存) にも対応
    return {"content": path.read_text(encoding="utf-8-sig")}


@app.put("/api/config/{config_type}")
def api_put_config(config_type: str, body: ConfigUpdateBody):
    """設定 CSV ファイルを上書き保存する。

    Path params:
        config_type: "mapping" または "value_mapping" のみ許可

    Request body:
        {"content": "<新しい CSV テキスト全文>"}

    Response:
        {"success": true}
    """
    if config_type not in ("mapping", "value_mapping"):
        raise HTTPException(status_code=404, detail="Unknown config type")
    path = _config_dir() / f"{config_type}_config.csv"
    # UTF-8 (BOM なし) で保存。次回読み込み時は utf-8-sig で BOM があっても対応できる
    path.write_text(body.content, encoding="utf-8")
    return {"success": True}


@app.post("/api/export")
def api_export():
    """sales_records を Excel ファイルに出力する。

    生成先: EXPORT_DIR/export.xlsx (毎回上書き)
    ダウンロードは GET /api/export/download で行う。

    Response:
        {"success": true, "download_url": "/api/export/download"}
    """
    output_path = str(_export_dir() / "export.xlsx")
    try:
        export_to_excel(output_path)
        return {"success": True, "download_url": "/api/export/download"}
    except Exception:
        # 内部パスやエラー詳細はクライアントに露出させない
        raise HTTPException(
            status_code=500,
            detail="Export failed. Check that data has been imported first.",
        )


@app.get("/api/export/download")
def api_export_download():
    """生成済みの Excel ファイルをダウンロードさせる。

    事前に POST /api/export を実行していない場合は 404 を返す。

    Response:
        FileResponse (application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)
    """
    path = _export_dir() / "export.xlsx"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Run export first.")
    return FileResponse(str(path), filename="export.xlsx")


# ---------------------------------------------------------------------------
# 静的ファイル配信 (本番: Vue ビルド成果物)
# ---------------------------------------------------------------------------

_FRONTEND_DIST = _BASE_DIR / "frontend" / "dist"

if _FRONTEND_DIST.exists():
    # Vue SPA のビルド成果物が存在する場合のみマウント
    # html=True: index.html へのフォールバックルーティングを有効化 (SPA に必要)
    # ※ API ルートより後に登録することで API が優先される
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="static")


# ---------------------------------------------------------------------------
# デスクトップ起動エントリポイント
# ---------------------------------------------------------------------------

def start_desktop() -> None:
    """uvicorn サーバーをバックグラウンドで起動し、pywebview ウィンドウを開く。

    アーキテクチャ:
      - uvicorn はデーモンスレッドで動作 (メインスレッドが終了すると自動停止)
      - pywebview がメインスレッドを占有し、ウィンドウを管理する
      - ウィンドウを閉じると pywebview.start() が戻り、プロセスが終了する

    Note:
        webview をここでインポートする理由:
        テスト実行時は pywebview が不要であり、インストールされていない環境でも
        モジュール自体をインポートできるようにするため。
    """
    import webview  # 遅延インポート: テスト環境で pywebview がなくてもエラーにならない

    def _run_server():
        """uvicorn を起動するスレッド関数。"""
        uvicorn.run(app, host="127.0.0.1", port=8765, log_level="error")

    # uvicorn をデーモンスレッドで起動 (メインスレッド終了時に自動停止)
    threading.Thread(target=_run_server, daemon=True).start()

    # pywebview でデスクトップウィンドウを作成・起動
    webview.create_window(
        "Sales Data Aggregator",    # ウィンドウタイトル
        "http://127.0.0.1:8765",    # uvicorn が配信する URL
        width=1280,
        height=800,
        resizable=True,
    )
    webview.start()  # ここでメインスレッドをブロック (ウィンドウが閉じられるまで)


# ---------------------------------------------------------------------------
# スクリプト直接実行時のエントリポイント
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # python backend/main.py で実行するとデスクトップアプリとして起動
    start_desktop()
