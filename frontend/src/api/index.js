/**
 * api/index.js — バックエンド API クライアント
 * =============================================
 * Axios インスタンスをベースに、各 API エンドポイントへのラッパーをエクスポートする。
 *
 * ベース URL は /api → Vite 開発時は vite.config.js のプロキシが
 * http://127.0.0.1:8765/api へ転送する。
 * 本番 (pywebview) では FastAPI が直接 /api を処理する。
 */
import axios from 'axios'

// Axios インスタンス: 全リクエストに共通設定を適用
const api = axios.create({
  baseURL: '/api',    // FastAPI のプレフィックスに合わせる
  timeout: 30000,     // 通常リクエストのタイムアウト: 30秒
})

/**
 * GET /api/summary — ダッシュボード用サマリーを取得する。
 * @returns {Promise<{data: {record_count, last_import, files, columns}}>}
 */
export const getSummary = () => api.get('/summary')

/**
 * GET /api/data — ページネーション付きで売上レコードを取得する。
 * @param {number} page     - ページ番号 (1始まり)
 * @param {number} pageSize - 1ページあたりの件数
 * @returns {Promise<{data: {data, total, page, page_size}}>}
 */
export const getData = (page = 1, pageSize = 100) =>
  api.get('/data', { params: { page, page_size: pageSize } })

/**
 * POST /api/import — ファイルをアップロードして ETL パイプラインを実行する。
 * multipart/form-data でファイルを送信する。
 * @param {File[]} files - アップロードするファイルの配列
 * @returns {Promise<{data: {success, record_count, errors}}>}
 */
export const importFiles = (files) => {
  const form = new FormData()
  // 複数ファイルを同一キー "files" で追加 (FastAPI の List[UploadFile] に対応)
  for (const f of files) form.append('files', f)
  return api.post('/import', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,  // 大容量ファイルのアップロード・処理に最大2分を許容
  })
}

/**
 * GET /api/config/{type} — 設定 CSV ファイルの内容を取得する。
 * @param {'mapping'|'value_mapping'} type - 設定種別
 * @returns {Promise<{data: {content: string}}>}
 */
export const getConfig = (type) => api.get(`/config/${type}`)

/**
 * PUT /api/config/{type} — 設定 CSV ファイルを上書き保存する。
 * @param {'mapping'|'value_mapping'} type - 設定種別
 * @param {string} content - 保存する CSV テキスト全文
 * @returns {Promise<{data: {success: boolean}}>}
 */
export const updateConfig = (type, content) => api.put(`/config/${type}`, { content })

/**
 * POST /api/export — sales_records を Excel ファイルに出力する。
 * @returns {Promise<{data: {success, download_url}}>}
 */
export const triggerExport = () => api.post('/export')

/**
 * Excel ファイルをブラウザ (または pywebview) でダウンロードさせる。
 * window.open で新しいタブを開くことでブラウザのダウンロード機能を利用する。
 */
export const downloadExport = () => window.open('/api/export/download', '_blank')
