<template>
  <div class="min-h-screen bg-gray-50 flex">
    <!-- Sidebar -->
    <aside class="w-56 bg-white shadow-md flex flex-col shrink-0">
      <div class="p-4 border-b">
        <h1 class="text-lg font-bold text-primary-700">売上集計</h1>
        <p class="text-xs text-gray-400">Sales Aggregator</p>
      </div>
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
    <!-- Main -->
    <main class="flex-1 p-6 overflow-auto">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
const navItems = [
  { to: '/',       icon: '📊', label: 'ダッシュボード' },
  { to: '/import', icon: '📥', label: 'インポート' },
  { to: '/config', icon: '⚙️',  label: '設定管理' },
  { to: '/export', icon: '📤', label: 'エクスポート' },
]
</script>
