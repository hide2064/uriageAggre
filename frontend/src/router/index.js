import { createRouter, createWebHashHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Import from '../views/Import.vue'
import ConfigManager from '../views/ConfigManager.vue'
import Export from '../views/Export.vue'

export default createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/',        component: Dashboard },
    { path: '/import',  component: Import },
    { path: '/config',  component: ConfigManager },
    { path: '/export',  component: Export },
  ],
})
