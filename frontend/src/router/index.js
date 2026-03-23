import { createRouter, createWebHistory } from 'vue-router'

// Buyer views
import BuyerLogin from '../views/buyer/Login.vue'
import Listings from '../views/buyer/Listings.vue'
import ListingDetail from '../views/buyer/ListingDetail.vue'
import Purchase from '../views/buyer/Purchase.vue'
import OrderHistory from '../views/buyer/OrderHistory.vue'
import RaiseDispute from '../views/buyer/RaiseDispute.vue'
import Messages from '../views/buyer/Messages.vue'

// Admin views
import AdminLogin from '../views/admin/Login.vue'
import AdminDisputes from '../views/admin/Disputes.vue'
import AdminDisputeDetail from '../views/admin/DisputeDetail.vue'

const routes = [
  { path: '/', redirect: '/login' },

  // Buyer
  { path: '/login', component: BuyerLogin, meta: { layout: 'auth' } },
  { path: '/listings', component: Listings, meta: { requiresAuth: true, role: 'buyer' } },
  { path: '/listings/:id', component: ListingDetail, meta: { requiresAuth: true, role: 'buyer' } },
  { path: '/messages/:id', component: Messages, meta: { requiresAuth: true, role: 'buyer' } },
  { path: '/purchase/:id', component: Purchase, meta: { requiresAuth: true, role: 'buyer' } },
  { path: '/orders', component: OrderHistory, meta: { requiresAuth: true, role: 'buyer' } },
  { path: '/orders/:id/dispute', component: RaiseDispute, meta: { requiresAuth: true, role: 'buyer' } },

  // Admin
  { path: '/admin/login', component: AdminLogin, meta: { layout: 'auth' } },
  { path: '/admin/disputes', component: AdminDisputes, meta: { requiresAuth: true, role: 'admin' } },
  { path: '/admin/disputes/:id', component: AdminDisputeDetail, meta: { requiresAuth: true, role: 'admin' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

export default router
