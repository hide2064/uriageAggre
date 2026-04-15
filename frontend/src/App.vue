<!--
  App.vue — アプリケーションシェル
  ==================================
  役割:
    - 左サイドバー (ナビゲーション) と右メインエリアのレイアウトを定義する
    - RouterView でアクティブなビューコンポーネントをメインエリアに描画する
    - RouterLink でサイドバーのナビゲーションを実装する

  レイアウト構造:
    <div.flex>
      <aside>  サイドバー (幅 14rem 固定)
        ロゴ
        <nav>  RouterLink × 4
      <main>   RouterView (残りの幅をすべて使う)
-->
<template>
  <div class="min-h-screen bg-gray-50 flex">
    <!-- ── サイドバー ──────────────────────────────────────────── -->
    <aside class="w-56 bg-white shadow-md flex flex-col shrink-0">

      <!-- ロゴ / アプリ名 -->
      <div class="p-4 border-b">
        <h1 class="text-lg font-bold text-primary-700">売上集計</h1>
        <p class="text-xs text-gray-400">Sales Aggregator</p>
      </div>

      <!-- ナビゲーションリンク -->
      <!-- :class 条件: アクティブ時は青背景 (bg-primary-600)、非アクティブ時はホバーでグレー -->
      <nav class="flex-1 p-3 space-y-1">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="$route.path === item.to
            ? 'bg-primary-600 text-white'
            : 'text-gray-600 hover:bg-gray-100'"
        >
          <span>{{ item.icon }}</span>{{ item.label }}
        </RouterLink>
      </nav>
    </aside>

    <!-- ── メインコンテンツエリア ──────────────────────────────── -->
    <!-- RouterView がアクティブなビューコンポーネントをここに描画する -->
    <main class="flex-1 p-6 overflow-auto">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
/**
 * サイドバーのナビゲーション項目定義。
 * to: Vue Router のルートパス
 * icon: 絵文字アイコン
 * label: 表示テキスト
 */
const navItems = [
  { to: '/',       icon: '📊', label: 'ダッシュボード' },
  { to: '/import', icon: '📥', label: 'インポート' },
  { to: '/config', icon: '⚙️',  label: '設定管理' },
  { to: '/export', icon: '📤', label: 'エクスポート' },
]
</script>
