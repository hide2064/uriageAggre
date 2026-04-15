<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-800 mb-6">ダッシュボード</h2>

    <!-- Stats row -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
      <div class="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
        <p class="text-sm text-gray-500">総レコード数</p>
        <p class="text-3xl font-bold text-primary-600 mt-1">
          {{ summary.record_count.toLocaleString() }}
        </p>
      </div>
      <div class="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
        <p class="text-sm text-gray-500">最終インポート</p>
        <p class="text-base font-semibold text-gray-700 mt-1">{{ formattedDate }}</p>
      </div>
      <div class="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
        <p class="text-sm text-gray-500">ファイル数</p>
        <p class="text-3xl font-bold text-green-600 mt-1">{{ summary.files.length }}</p>
      </div>
    </div>

    <!-- Column chips -->
    <div
      v-if="summary.columns.length"
      class="bg-white rounded-xl shadow-sm p-5 border border-gray-100 mb-6"
    >
      <h3 class="text-sm font-semibold text-gray-600 mb-3">データカラム</h3>
      <div class="flex flex-wrap gap-2">
        <span
          v-for="col in summary.columns"
          :key="col"
          class="px-3 py-1 bg-blue-50 text-blue-700 text-xs font-medium rounded-full"
        >{{ col }}</span>
      </div>
    </div>

    <!-- File list -->
    <div
      v-if="summary.files.length"
      class="bg-white rounded-xl shadow-sm p-5 border border-gray-100"
    >
      <h3 class="text-sm font-semibold text-gray-600 mb-3">インポート済みファイル</h3>
      <ul class="space-y-1">
        <li
          v-for="file in summary.files"
          :key="file"
          class="flex items-center gap-2 text-sm text-gray-700"
        >
          <span class="text-green-500">✓</span>{{ file }}
        </li>
      </ul>
    </div>

    <!-- Empty state -->
    <div
      v-if="!loading && summary.record_count === 0"
      class="text-center py-16 text-gray-400"
    >
      <p class="text-5xl mb-4">📂</p>
      <p class="text-lg font-medium">データがありません</p>
      <p class="text-sm mt-1">「インポート」からファイルを読み込んでください</p>
    </div>

    <div v-if="error" class="mt-4 p-4 bg-red-50 text-red-700 rounded-lg text-sm">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
/**
 * Dashboard.vue — ダッシュボード画面
 * ====================================
 * GET /api/summary を呼び出し、インポート状況を表示する。
 *
 * 表示内容:
 *   - 統計カード (総レコード数 / 最終インポート日時 / ファイル数)
 *   - データカラム一覧 (チップ形式)
 *   - インポート済みファイル一覧
 *   - データが空の場合のエンプティステート
 */
import { ref, computed, onMounted } from 'vue'
import { getSummary } from '../api/index.js'

/** サマリーデータ (API レスポンス形式に合わせた初期値) */
const summary = ref({ record_count: 0, last_import: null, files: [], columns: [] })
const loading = ref(true)   // ローディング中フラグ (エンプティステート表示制御に使用)
const error   = ref(null)   // エラーメッセージ

/**
 * last_import (ISO 8601 文字列) を日本語ロケールの日時表記に変換する。
 * 例: "2024-01-15T12:34:56+00:00" → "2024/1/15 21:34:56"
 */
const formattedDate = computed(() =>
  summary.value.last_import
    ? new Date(summary.value.last_import).toLocaleString('ja-JP')
    : '—'
)

/** コンポーネントマウント時にサマリーを取得する */
onMounted(async () => {
  try {
    const res = await getSummary()
    summary.value = res.data
  } catch (e) {
    error.value = 'データの取得に失敗しました: ' + e.message
  } finally {
    loading.value = false
  }
})
</script>
