<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-800 mb-6">設定管理</h2>

    <!-- Tab buttons -->
    <div class="flex gap-2 mb-6">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        :class="activeTab === tab.key
          ? 'bg-primary-600 text-white'
          : 'bg-white text-gray-600 border hover:bg-gray-50'"
        @click="switchTab(tab.key)"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Description banner -->
    <div class="mb-4 p-4 bg-blue-50 rounded-lg text-sm text-blue-800">
      <strong>{{ meta.title }}</strong><br />{{ meta.description }}
    </div>

    <!-- Text editor card -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div class="flex justify-between items-center px-4 py-3 border-b bg-gray-50">
        <span class="text-sm font-mono text-gray-500">{{ meta.filename }}</span>
        <button
          :disabled="saving"
          class="px-4 py-1.5 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 text-white text-sm font-semibold rounded-lg transition-colors"
          @click="saveConfig"
        >
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </div>
      <textarea
        v-model="content"
        class="w-full h-80 p-4 font-mono text-sm text-gray-800 focus:outline-none resize-none"
        placeholder="CSVを直接編集できます..."
        spellcheck="false"
      />
    </div>

    <!-- Save feedback -->
    <div
      v-if="saveResult"
      class="mt-4 p-3 rounded-lg text-sm"
      :class="saveResult.ok ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'"
    >
      {{ saveResult.ok ? '✅ 保存しました' : '❌ 保存に失敗しました: ' + saveResult.msg }}
    </div>
  </div>
</template>

<script setup>
/**
 * ConfigManager.vue — 設定管理画面
 * ===================================
 * 2 種類の設定 CSV をブラウザ上で直接編集・保存する。
 *
 * タブ構成:
 *   mapping       → mapping_config.csv       (列名マッピング設定)
 *   value_mapping → value_mapping_config.csv (マスタ照合設定)
 *
 * API:
 *   GET /api/config/{type}  : ファイル内容を取得
 *   PUT /api/config/{type}  : ファイル内容を上書き保存
 */
import { ref, computed, onMounted } from 'vue'
import { getConfig, updateConfig } from '../api/index.js'

/** タブ定義 */
const tabs = [
  { key: 'mapping',       label: '項目名マッピング' },
  { key: 'value_mapping', label: 'マスタ照合' },
]

/** 各タブの説明メタデータ */
const tabMeta = {
  mapping: {
    title:       '項目名マッピング設定',
    description: '1列目: 正規カラム名、2列目以降: ファイル上の列名候補（複数可）',
    filename:    'mapping_config.csv',
  },
  value_mapping: {
    title:       'マスタ照合設定',
    description: '1行目ヘッダー: キー列名,追加列名  /  2行目以降: キー値,マッピング値',
    filename:    'value_mapping_config.csv',
  },
}

const activeTab  = ref('mapping')  // 現在アクティブなタブのキー
const content    = ref('')         // テキストエリアに表示中の CSV テキスト
const saving     = ref(false)      // 保存処理中フラグ
const saveResult = ref(null)       // 保存結果 ({ok: boolean, msg?: string})

/** アクティブタブのメタデータを返す computed */
const meta = computed(() => tabMeta[activeTab.value])

/** 指定タブの設定 CSV を API から読み込んでテキストエリアに反映する */
const loadConfig = async (type) => {
  try { content.value = (await getConfig(type)).data.content }
  catch (_) { content.value = '' }  // 読み込み失敗時は空欄にする
}

/** タブ切り替え: 選択したタブの設定を読み込む */
const switchTab = async (key) => {
  activeTab.value   = key
  saveResult.value  = null
  await loadConfig(key)
}

/** 保存ボタンのクリックハンドラ */
const saveConfig = async () => {
  saving.value     = true
  saveResult.value = null
  try {
    await updateConfig(activeTab.value, content.value)
    saveResult.value = { ok: true }
    // 3秒後に保存結果を非表示にする (自動フェードアウト)
    setTimeout(() => { saveResult.value = null }, 3000)
  } catch (e) {
    saveResult.value = { ok: false, msg: e.message }
  } finally {
    saving.value = false
  }
}

/** 初期表示時に mapping タブの内容を読み込む */
onMounted(() => loadConfig('mapping'))
</script>
