import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/listings' },
  { path: '/listings', component: () => import('./views/buyer/ProductList.vue') },
  { path: '/orders', component: () => import('./views/buyer/OrderHistory.vue') },
  { path: '/purchase/:id', component: () => import('./views/buyer/Purchase.vue') },
  { path: '/orders/:id/dispute', component: () => import('./views/buyer/RaiseDispute.vue') },
  // Catch-all
  { path: '/:pathMatch(.*)*', redirect: '/listings' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
