<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-800 mb-6">インポート</h2>

    <!-- Drop zone -->
    <div
      class="border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors mb-6"
      :class="isDragging
        ? 'border-primary-500 bg-blue-50'
        : 'border-gray-300 hover:border-primary-400'"
      @dragover.prevent="isDragging = true"
      @dragleave="isDragging = false"
      @drop.prevent="onDrop"
      @click="fileInput.click()"
    >
      <p class="text-4xl mb-3">📁</p>
      <p class="text-gray-600 font-medium">ファイルをドロップ、またはクリックして選択</p>
      <p class="text-gray-400 text-sm mt-1">CSV, TXT, XLSX, XLS に対応</p>
      <input
        ref="fileInput"
        type="file"
        multiple
        accept=".csv,.txt,.tsv,.xlsx,.xls"
        class="hidden"
        @change="onFileSelect"
      />
    </div>

    <!-- Selected files -->
    <div
      v-if="selectedFiles.length"
      class="bg-white rounded-xl shadow-sm border border-gray-100 mb-6"
    >
      <div class="p-4 border-b flex justify-between items-center">
        <h3 class="font-semibold text-gray-700">選択ファイル ({{ selectedFiles.length }}件)</h3>
        <button class="text-sm text-red-500 hover:text-red-700" @click="selectedFiles = []">
          クリア
        </button>
      </div>
      <ul class="divide-y">
        <li
          v-for="(file, i) in selectedFiles"
          :key="i"
          class="px-4 py-3 flex justify-between text-sm"
        >
          <span class="text-gray-700">{{ file.name }}</span>
          <span class="text-gray-400">{{ fmtSize(file.size) }}</span>
        </li>
      </ul>
    </div>

    <!-- Import button -->
    <button
      v-if="selectedFiles.length"
      :disabled="importing"
      class="w-full py-3 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 text-white font-semibold rounded-xl transition-colors"
      @click="doImport"
    >
      {{ importing ? '処理中...' : `${selectedFiles.length}件をインポート` }}
    </button>

    <!-- Result -->
    <div v-if="result" class="mt-6">
      <div
        class="p-4 rounded-xl border"
        :class="result.success
          ? 'bg-green-50 border-green-200 text-green-800'
          : 'bg-red-50 border-red-200 text-red-800'"
      >
        <p class="font-semibold">
          {{ result.success ? '✅ インポート完了' : '❌ インポート失敗' }}
        </p>
        <p v-if="result.success" class="text-sm mt-1">
          {{ result.record_count.toLocaleString() }}件のレコードを取り込みました
        </p>
        <ul v-if="result.errors?.length" class="mt-2 text-sm space-y-1">
          <li v-for="(e, i) in result.errors" :key="i" class="text-red-600">
            ⚠ {{ e.file }}: {{ e.error }}
          </li>
        </ul>
      </div>
    </div>

    <div v-if="error" class="mt-4 p-4 bg-red-50 text-red-700 rounded-lg text-sm">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { importFiles } from '../api/index.js'

const fileInput = ref(null)
const selectedFiles = ref([])
const isDragging = ref(false)
const importing = ref(false)
const result = ref(null)
const error = ref(null)

const fmtSize = (b) => b < 1024 ? `${b} B`
  : b < 1024 * 1024 ? `${(b / 1024).toFixed(1)} KB`
  : `${(b / (1024 * 1024)).toFixed(1)} MB`

const onFileSelect = (e) => {
  selectedFiles.value = Array.from(e.target.files)
  result.value = error.value = null
}

const onDrop = (e) => {
  isDragging.value = false
  selectedFiles.value = Array.from(e.dataTransfer.files).filter(
    (f) => /\.(csv|txt|tsv|xlsx|xls)$/i.test(f.name)
  )
  result.value = error.value = null
}

const doImport = async () => {
  importing.value = true
  result.value = error.value = null
  try {
    const res = await importFiles(selectedFiles.value)
    result.value = res.data
    selectedFiles.value = []
  } catch (e) {
    error.value = e.response?.data?.detail?.message || e.message || 'インポートエラー'
  } finally {
    importing.value = false
  }
}
</script>
