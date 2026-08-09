import { createRouter, createWebHistory } from 'vue-router'
import ScreenerView from '../views/ScreenerView.vue'
import LiveMonitorView from '../views/LiveMonitorView.vue'
import StrategyView from '../views/StrategyView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/screener'
    },
    {
      path: '/screener',
      name: 'screener',
      component: ScreenerView
    },
    {
      path: '/monitor',
      name: 'monitor',
      component: LiveMonitorView
    },
    {
      path: '/strategy',
      name: 'strategy',
      component: StrategyView
    }
  ]
})

export default router
