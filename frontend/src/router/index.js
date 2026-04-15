/**
 * router/index.js — Vue Router 設定
 * ===================================
 * ハッシュヒストリーモードを使用する理由:
 *   - pywebview や静的ファイル配信 (FastAPI StaticFiles) では
 *     HTML5 History API を使うとリロード時に 404 が発生する。
 *   - ハッシュモード (#/) を使うとすべてのルーティングがクライアント側で完結する。
 */
import { createRouter, createWebHashHistory } from 'vue-router'
import Dashboard    from '../views/Dashboard.vue'
import Import       from '../views/Import.vue'
import ConfigManager from '../views/ConfigManager.vue'
import Export       from '../views/Export.vue'

export default createRouter({
  history: createWebHashHistory(),  // URL 形式: http://localhost:5173/#/import
  routes: [
    { path: '/',        component: Dashboard },     // ダッシュボード
    { path: '/import',  component: Import },         // ファイルインポート
    { path: '/config',  component: ConfigManager },  // 設定管理
    { path: '/export',  component: Export },         // Excel エクスポート
  ],
})
