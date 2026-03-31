import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: () => import('./views/buyer/Login.vue') },
  { path: '/profile', component: () => import('./views/buyer/Profile.vue') },
  { path: '/listings', component: () => import('./views/buyer/ProductList.vue') },
  { path: '/listings/:id', component: () => import('./views/buyer/ProductDetail.vue') },
  { path: '/orders', component: () => import('./views/buyer/OrderHistory.vue') },
  { path: '/orders/:id', component: () => import('./views/buyer/OrderDetail.vue') },
  { path: '/messages/:id', component: () => import('./views/buyer/Messages.vue') },
  { path: '/purchase/:id', component: () => import('./views/buyer/Purchase.vue') },
  { path: '/orders/:id/dispute', component: () => import('./views/buyer/RaiseDispute.vue') },
  { path: '/admin', component: () => import('./views/admin/Login.vue') },
  { path: '/admin/disputes', component: () => import('./views/admin/Disputes.vue') },
  { path: '/admin/disputes/:id', component: () => import('./views/admin/DisputeDetail.vue') },
  // Catch-all
  { path: '/:pathMatch(.*)*', redirect: '/listings' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
