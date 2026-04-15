<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-800 mb-6">エクスポート</h2>

    <!-- Record count card -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6 flex items-center gap-6">
      <span class="text-5xl">📊</span>
      <div>
        <p class="text-gray-500 text-sm">エクスポート対象レコード数</p>
        <p class="text-4xl font-bold text-primary-600">
          {{ summary.record_count.toLocaleString() }}
        </p>
      </div>
    </div>

    <!-- Generate button -->
    <button
      :disabled="exporting || summary.record_count === 0"
      class="w-full py-4 bg-green-600 hover:bg-green-700 disabled:bg-gray-300 text-white font-bold text-lg rounded-xl transition-colors mb-4"
      @click="doExport"
    >
      {{ exporting ? '生成中...' : 'Excelファイルを生成' }}
    </button>

    <!-- Download button (appears after successful export) -->
    <button
      v-if="exportDone"
      class="w-full py-4 bg-primary-600 hover:bg-primary-700 text-white font-bold text-lg rounded-xl transition-colors"
      @click="downloadExport()"
    >
      📥 ダウンロード (export.xlsx)
    </button>

    <!-- Status message -->
    <div
      v-if="statusMsg"
      class="mt-4 p-4 rounded-xl text-sm"
      :class="statusOk ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'"
    >
      {{ statusMsg }}
    </div>

    <!-- No-data warning -->
    <div
      v-if="summary.record_count === 0"
      class="mt-6 p-4 bg-yellow-50 text-yellow-700 rounded-lg text-sm"
    >
      ⚠️ データがありません。先に「インポート」からファイルを読み込んでください。
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getSummary, triggerExport, downloadExport } from '../api/index.js'

const summary    = ref({ record_count: 0 })
const exporting  = ref(false)
const exportDone = ref(false)
const statusMsg  = ref(null)
const statusOk   = ref(true)

const doExport = async () => {
  exporting.value = true
  statusMsg.value = null
  try {
    await triggerExport()
    exportDone.value = true
    statusOk.value   = true
    statusMsg.value  = 'ファイルを生成しました。ダウンロードボタンを押してください。'
  } catch (e) {
    statusOk.value  = false
    statusMsg.value = 'エクスポートに失敗しました: ' + (e.response?.data?.detail || e.message)
  } finally {
    exporting.value = false
  }
}

onMounted(async () => {
  try { summary.value = (await getSummary()).data } catch (_) {}
})
</script>
