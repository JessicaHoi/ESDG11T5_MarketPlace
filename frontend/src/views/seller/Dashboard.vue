<template>
  <div class="min-h-screen bg-paper">
    <SellerNavbar :seller="mockSeller" />

    <div class="pt-16">
      <div class="bg-ink text-paper py-10 px-6">
        <div class="max-w-5xl mx-auto">
          <p class="section-label text-white/40 mb-2">Welcome back</p>
          <h1 class="font-display font-extrabold text-4xl">{{ mockSeller.name }}'s Dashboard</h1>
        </div>
      </div>

      <div class="max-w-5xl mx-auto px-6 py-8">

        <!-- Stats -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
          <div class="bg-white border border-ink/10 p-5">
            <p class="section-label text-muted mb-1">Total Orders</p>
            <p class="font-display font-extrabold text-3xl">{{ orders.length }}</p>
          </div>
          <div class="bg-white border border-ink/10 p-5">
            <p class="section-label text-muted mb-1">Pending</p>
            <p class="font-display font-extrabold text-3xl text-amber-500">{{ pendingCount }}</p>
          </div>
          <div class="bg-white border border-ink/10 p-5">
            <p class="section-label text-muted mb-1">Completed</p>
            <p class="font-display font-extrabold text-3xl text-sage">{{ completedCount }}</p>
          </div>
          <div class="bg-white border border-ink/10 p-5">
            <p class="section-label text-muted mb-1">Disputes</p>
            <p class="font-display font-extrabold text-3xl text-red-500">{{ disputedCount }}</p>
          </div>
        </div>

        <!-- Recent orders -->
        <div class="mb-4 flex items-center justify-between">
          <h2 class="font-display font-bold text-xl">Recent Orders</h2>
          <router-link to="/seller/orders" class="text-sm font-mono text-accent hover:underline">View all →</router-link>
        </div>

        <div v-if="loading" class="text-center py-16 text-muted font-mono text-sm">Loading orders...</div>

        <div v-else class="space-y-3">
          <div
            v-for="order in recentOrders"
            :key="order.order_id"
            class="bg-white border border-ink/10 p-5 hover:border-ink/30 transition-colors cursor-pointer group"
            @click="$router.push(`/seller/orders/${order.order_id}`)"
          >
            <div class="flex items-center justify-between flex-wrap gap-4">
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 bg-cream overflow-hidden flex-shrink-0 flex items-center justify-center">
                  <img v-if="listingImages[order.listing_id]" :src="listingImages[order.listing_id]" class="w-full h-full object-cover" />
                  <span v-else class="text-xl">🛍</span>
                </div>
                <div>
                  <div class="flex items-center gap-2 mb-0.5">
                    <span class="font-mono text-xs text-muted">Order #{{ order.order_id }}</span>
                    <span class="status-badge text-xs font-mono" :class="badgeClass(order.status)">{{ order.status }}</span>
                  </div>
                  <p class="font-display font-semibold text-sm group-hover:text-accent transition-colors">
                    {{ order.order_details || `Listing #${order.listing_id}` }}
                  </p>
                  <p class="text-xs text-muted font-mono">Buyer ID: {{ order.buyer_id }} · {{ formatDate(order.created_at) }}</p>
                </div>
              </div>
              <div class="text-right">
                <p class="font-display font-bold text-lg text-accent">${{ order.agreed_price }}</p>
                <p class="text-xs text-muted font-mono">→</p>
              </div>
            </div>
          </div>

          <div v-if="orders.length === 0" class="text-center py-16">
            <p class="font-display font-semibold text-2xl text-ink/30">No orders yet</p>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import SellerNavbar from '../../components/SellerNavbar.vue'
import { mockSeller } from '../../data/mockData.js'
import { getOrdersBySeller } from '../../services/api.js'

const orders  = ref([])
const loading = ref(true)
const listingImages = ref({})

const pendingCount   = computed(() => orders.value.filter(o => o.status === 'RESERVED').length)
const completedCount = computed(() => orders.value.filter(o => o.status === 'COMPLETED').length)
const disputedCount  = computed(() => orders.value.filter(o => o.status === 'DISPUTED').length)
const recentOrders   = computed(() => orders.value.slice(0, 5))

onMounted(async () => {
  try {
    const [ordersData, listingsData] = await Promise.all([
      getOrdersBySeller(mockSeller.id),
      fetch('/tmp.json').then(r => r.json()).catch(() => null),
    ])
    orders.value = Array.isArray(ordersData) ? ordersData : (ordersData.orders ?? [])
    const listings = listingsData?.data?.listings ?? []
    listings.forEach(l => {
      if (l.listingImgUrl && l.listingImgUrl.length > 5) {
        listingImages.value[l.listingID] = l.listingImgUrl
      }
    })
  } catch (err) {
    console.error('Failed to load seller orders:', err)
  } finally {
    loading.value = false
  }
})

function badgeClass(status) {
  return {
    RESERVED:  'bg-amber-100 text-amber-700',
    COMPLETED: 'bg-sage/20 text-sage',
    DISPUTED:  'bg-red-100 text-red-700',
    REFUNDED:  'bg-purple-100 text-purple-700',
  }[status] || 'bg-cream text-ink'
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-SG', { day: 'numeric', month: 'short', year: 'numeric' })
}
</script>
