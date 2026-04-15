# 売上集計アプリケーション 設計書

## 1. システム概要

複数の売上ファイル（CSV / Excel）を読み込み、列名を正規化してマスタ照合を行い、SQLite に蓄積して Excel 出力するデスクトップ業務アプリ。

- **フロントエンド**: Vue 3 SPA（Vite + Tailwind CSS）
- **バックエンド**: Python FastAPI（uvicorn で起動）
- **デスクトップ**: pywebview でウィンドウ表示（本番）
- **DB**: SQLite（sqlalchemy + pandas）
- **パッケージング**: PyInstaller（.exe 単体配布）

---

## 2. ディレクトリ構成

```
uriageAggre/
├── backend/
│   ├── __init__.py
│   ├── processor.py    # ETL: 読込 / 正規化 / エンリッチメント
│   ├── database.py     # DB 操作: 保存 / 取得 / エクスポート
│   └── main.py         # FastAPI アプリ + pywebview 起動
├── frontend/
│   ├── package.json
│   ├── vite.config.js  # 開発プロキシ (/api → :8765)
│   └── src/
│       ├── App.vue           # レイアウト（サイドバー + RouterView）
│       ├── router/index.js   # ハッシュヒストリー 4 ルート
│       ├── api/index.js      # Axios ラッパー
│       └── views/
│           ├── Dashboard.vue     # サマリー表示
│           ├── Import.vue        # ファイルアップロード
│           ├── ConfigManager.vue # 設定 CSV 編集
│           └── Export.vue        # Excel 出力
├── config/
│   ├── mapping_config.csv       # 列名マッピング定義
│   └── value_mapping_config.csv # マスタ照合定義
├── tests/
│   ├── conftest.py
│   ├── test_processor.py  (20 テスト)
│   ├── test_database.py   (6 テスト)
│   └── test_api.py        (8 テスト)
├── sales_data/
│   └── sample.csv         # サンプルデータ
├── build.spec  # PyInstaller 設定
├── build.py    # ビルドスクリプト
├── debug.bat   # 開発起動スクリプト
└── start.bat   # 本番起動スクリプト（pywebview）
```

---

## 3. コンポーネント間関係

```
┌─────────────────────────────────────────────────────┐
│  pywebview (デスクトップウィンドウ)                    │
│  ┌───────────────────────────────────────────────┐   │
│  │  Vue 3 SPA  http://127.0.0.1:8765             │   │
│  │  Dashboard / Import / Config / Export          │   │
│  └───────────────┬───────────────────────────────┘   │
│                  │ HTTP /api/*                        │
│  ┌───────────────▼───────────────────────────────┐   │
│  │  FastAPI (uvicorn :8765)                       │   │
│  │  ┌──────────────┐  ┌──────────────────────┐   │   │
│  │  │ processor.py │  │ database.py           │   │   │
│  │  │ ETL Pipeline │  │ SQLite / Excel        │   │   │
│  │  └──────────────┘  └──────────────────────┘   │   │
│  └───────────────────────────────────────────────┘   │
│                  │                                    │
│  ┌───────────────▼─────────┐                         │
│  │  sales_data.db (SQLite) │                         │
│  └─────────────────────────┘                         │
└─────────────────────────────────────────────────────┘
```

---

## 4. データベーステーブル

### sales_records（動的スキーマ）

インポートのたびに DROP → CREATE → INSERT される。列名はインポートファイルの正規化後の列に依存する。

| 列名 | 型 | 備考 |
|---|---|---|
| date | TEXT | 正規化後の日付列 |
| amount | REAL | 正規化後の金額列 |
| client | TEXT | 正規化後の取引先列 |
| product_code | TEXT | 正規化後の商品コード列 |
| _source_file | TEXT | 元ファイル名（エクスポート除外） |
| ※ 任意の列 | - | ファイル内容により変動 |

### import_log

| 列名 | 型 | 備考 |
|---|---|---|
| id | INTEGER PK | 自動採番 |
| files | TEXT | JSON 配列（ファイル名リスト） |
| record_count | INTEGER | 取込件数 |
| imported_at | DATETIME | UTC タイムスタンプ |

---

## 5. 設定ファイル仕様

### config/mapping_config.csv

列名の正規化ルールを定義する。

```
フォーマット: 正規名,別名1,別名2,...
例:
  amount,金額,Amount,売上金額,revenue,売上
  date,日付,Date,transaction_date,売上日
```

### config/value_mapping_config.csv

マスタ照合ルールを定義する。

```
フォーマット:
  1行目: キー列名,追加列名        ← ヘッダー
  2行目以降: キー値,マッピング値  ← データ

例:
  商品コード,カテゴリ
  A001,電化製品
  B001,食品
```

---

## 6. ETL パイプライン詳細

```
ファイル群
  │
  ▼  _read_file()
  DataFrame（生データ）
  │  エンコーディング試行順: UTF-8-BOM → CP932 → UTF-8
  │
  ▼  normalize_headers()
  DataFrame（列名正規化済）
  │  マッピングに一致した列名を正規名に変換
  │  例: "売上金額" → "amount"
  │
  ▼  enrich_data()        ※ value_mapping_config.csv がある場合のみ
  DataFrame（マスタ列追加済）
  │  key_col の値でマスタ辞書を引いて new_col を追加
  │  未一致は "N/A"
  │
  ▼  "_source_file" 列追加
  DataFrame（完成）
  │
  ▼  pd.concat()（複数ファイルの場合）
  結合 DataFrame
  │
  ▼  save_dataframe()
  SQLite (sales_records)
```

---

## 7. API エンドポイント一覧

| メソッド | パス | 説明 |
|---|---|---|
| GET | /api/summary | ダッシュボード用サマリー |
| POST | /api/import | ファイルアップロード＆ETL実行 |
| GET | /api/data | ページネーション付きレコード取得 |
| GET | /api/config/{type} | 設定CSV取得（mapping / value_mapping） |
| PUT | /api/config/{type} | 設定CSV上書き保存 |
| POST | /api/export | Excel生成（exports/export.xlsx） |
| GET | /api/export/download | 生成済みExcelダウンロード |

---

## 8. シーケンス図

### 8-1. アプリケーション起動（pywebview モード）

```mermaid
sequenceDiagram
    participant User as ユーザー
    participant EXE  as SalesAggregator.exe
    participant UV   as uvicorn スレッド
    participant WV   as pywebview ウィンドウ
    participant Vue  as Vue SPA

    User->>EXE: 実行
    EXE->>UV: Thread(uvicorn :8765).start()
    EXE->>WV: webview.create_window("http://127.0.0.1:8765")
    WV->>UV: GET / → frontend/dist/index.html
    UV-->>WV: index.html + assets
    WV->>Vue: Vue アプリ起動
    Vue->>UV: GET /api/summary
    UV-->>Vue: {record_count:0, ...}
    Vue-->>User: ダッシュボード表示
```

### 8-2. ファイルインポート

```mermaid
sequenceDiagram
    participant U   as ユーザー
    participant Vue as Import.vue
    participant API as FastAPI /api/import
    participant P   as processor.py
    participant DB  as database.py
    participant DB2 as SQLite

    U->>Vue: ファイルをドロップ or 選択
    U->>Vue: インポートボタンクリック
    Vue->>API: POST /api/import (multipart)
    API->>API: 一時ディレクトリへ保存
    API->>P: load_header_mapping(mapping_config.csv)
    P-->>API: {amount:[売上金額,...], ...}
    API->>P: load_value_mapping(value_mapping_config.csv)
    P-->>API: (商品コード, カテゴリ, {A001:電化製品,...})
    API->>P: process_files(paths, header_mapping, value_mapping)
    P->>P: _read_file() × N ファイル
    P->>P: normalize_headers()
    P->>P: enrich_data()
    P->>P: pd.concat()
    P-->>API: (DataFrame, errors)
    API->>DB: save_dataframe(df, filenames)
    DB->>DB2: df.to_sql("sales_records", replace)
    DB->>DB2: INSERT import_log
    DB-->>API: record_count
    API-->>Vue: {success:true, record_count:N, errors:[]}
    Vue-->>U: "✅ N件インポート完了"
```

### 8-3. ダッシュボード表示

```mermaid
sequenceDiagram
    participant U   as ユーザー
    participant Vue as Dashboard.vue
    participant API as FastAPI /api/summary
    participant DB  as database.py
    participant DB2 as SQLite

    U->>Vue: ダッシュボード画面を開く
    Vue->>API: GET /api/summary
    API->>DB: get_summary()
    DB->>DB2: SELECT * FROM import_log ORDER BY imported_at DESC LIMIT 1
    DB2-->>DB: 最新インポートログ
    DB->>DB2: SELECT * FROM sales_records LIMIT 1
    DB2-->>DB: カラム名サンプル
    DB-->>API: {record_count, last_import, files, columns}
    API-->>Vue: JSON レスポンス
    Vue-->>U: 統計カード・カラムチップ・ファイルリスト表示
```

### 8-4. 設定管理（読み込み＆保存）

```mermaid
sequenceDiagram
    participant U   as ユーザー
    participant Vue as ConfigManager.vue
    participant API as FastAPI /api/config

    U->>Vue: 設定管理画面を開く
    Vue->>API: GET /api/config/mapping
    API->>API: config/mapping_config.csv を読込 (UTF-8-BOM)
    API-->>Vue: {content: "date,日付,...\n..."}
    Vue-->>U: テキストエリアに CSV を表示

    U->>Vue: CSV を編集
    U->>Vue: 「保存」ボタンクリック
    Vue->>API: PUT /api/config/mapping {content:"..."}
    API->>API: config/mapping_config.csv を上書き (UTF-8)
    API-->>Vue: {success: true}
    Vue-->>U: "✅ 保存しました" (3秒後に消える)
```

### 8-5. Excel エクスポート＆ダウンロード

```mermaid
sequenceDiagram
    participant U   as ユーザー
    participant Vue as Export.vue
    participant API as FastAPI /api/export
    participant DB  as database.py
    participant DB2 as SQLite
    participant FS  as exports/export.xlsx

    U->>Vue: エクスポート画面を開く
    Vue->>API: GET /api/summary
    API-->>Vue: {record_count: N}
    Vue-->>U: "N件をエクスポート" ボタンを表示

    U->>Vue: 「Excelファイルを生成」クリック
    Vue->>API: POST /api/export
    API->>DB: export_to_excel("exports/export.xlsx")
    DB->>DB2: SELECT * FROM sales_records
    DB2-->>DB: 全レコード
    DB->>DB: _ 列を除外
    DB->>FS: df.to_excel()
    DB-->>API: ファイルパス
    API-->>Vue: {success:true, download_url:"/api/export/download"}
    Vue-->>U: ダウンロードボタンを表示

    U->>Vue: 「ダウンロード」クリック
    Vue->>API: GET /api/export/download (window.open)
    API->>FS: ファイル読み込み
    API-->>U: FileResponse (export.xlsx)
    U-->>U: ファイル保存ダイアログ
```

---

## 9. テスト構成

| ファイル | 対象 | テスト数 |
|---|---|---|
| tests/test_processor.py | ETL ロジック (normalize_headers, enrich_data, loaders, process_files) | 20 |
| tests/test_database.py | DB 操作 (save/get/export) | 6 |
| tests/test_api.py | FastAPI エンドポイント (E2E) | 8 |
| **合計** | | **34** |

テスト実行: `pytest tests/ -v`

---

## 10. ビルド & 配布

```
開発環境:
  uvicorn backend.main:app --reload --port 8765
  cd frontend && npm run dev

本番ビルド:
  pip install pyinstaller
  python build.py
  → dist/SalesAggregator/SalesAggregator.exe

配布物:
  dist/SalesAggregator/ フォルダ全体を zip して配布
  ※ config/ フォルダをユーザーが編集できるよう .exe と同階層に置くこと
```
