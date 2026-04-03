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
        <div class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-10">
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
          <div class="bg-white border border-ink/10 p-5">
            <p class="section-label text-muted mb-1">Revenue</p>
            <p class="font-display font-extrabold text-3xl text-accent">${{ revenue }}</p>
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="mb-10">
          <h2 class="font-display font-bold text-xl mb-4">Quick Actions</h2>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <a
              :href="outsystemsListingUrl"
              target="_blank"
              rel="noopener"
              class="bg-white border border-ink/10 p-6 hover:border-accent/40 hover:shadow-sm transition-all group cursor-pointer block"
            >
              <div class="flex items-center gap-3 mb-3">
                <div class="w-10 h-10 bg-accent/10 flex items-center justify-center text-lg">📦</div>
                <p class="font-display font-bold text-base group-hover:text-accent transition-colors">Manage Listings</p>
              </div>
              <p class="text-xs text-muted font-mono leading-relaxed">Create, edit, and manage your product listings on the marketplace.</p>
              <p class="text-xs text-accent font-mono mt-3 opacity-0 group-hover:opacity-100 transition-opacity">Opens listing portal →</p>
            </a>
            <router-link
              to="/seller/orders"
              class="bg-white border border-ink/10 p-6 hover:border-accent/40 hover:shadow-sm transition-all group block"
            >
              <div class="flex items-center gap-3 mb-3">
                <div class="w-10 h-10 bg-amber-50 flex items-center justify-center text-lg">📋</div>
                <p class="font-display font-bold text-base group-hover:text-accent transition-colors">View Orders</p>
              </div>
              <p class="text-xs text-muted font-mono leading-relaxed">Track active orders, manage deliveries, and view order history.</p>
              <p class="text-xs text-accent font-mono mt-3 opacity-0 group-hover:opacity-100 transition-opacity">View all orders →</p>
            </router-link>
            <router-link
              to="/seller/disputes"
              class="bg-white border border-ink/10 p-6 hover:border-accent/40 hover:shadow-sm transition-all group block"
            >
              <div class="flex items-center gap-3 mb-3">
                <div class="w-10 h-10 bg-red-50 flex items-center justify-center text-lg">⚠</div>
                <div class="flex items-center gap-2">
                  <p class="font-display font-bold text-base group-hover:text-accent transition-colors">Disputes</p>
                  <span v-if="pendingDisputeCount > 0" class="bg-red-100 text-red-600 text-xs font-mono px-2 py-0.5">{{ pendingDisputeCount }} pending</span>
                </div>
              </div>
              <p class="text-xs text-muted font-mono leading-relaxed">Respond to buyer disputes and view resolution outcomes.</p>
              <p class="text-xs text-accent font-mono mt-3 opacity-0 group-hover:opacity-100 transition-opacity">View disputes →</p>
            </router-link>
          </div>
        </div>

        <!-- Two-column layout: Recent Orders + Recent Disputes -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">

          <!-- Recent Orders -->
          <div>
            <div class="mb-4 flex items-center justify-between">
              <h2 class="font-display font-bold text-xl">Recent Orders</h2>
              <router-link to="/seller/orders" class="text-sm font-mono text-accent hover:underline">View all →</router-link>
            </div>

            <div v-if="loading" class="text-center py-16 text-muted font-mono text-sm">Loading orders...</div>

            <div v-else class="space-y-3">
              <div
                v-for="order in recentOrders"
                :key="order.order_id"
                class="bg-white border border-ink/10 p-4 hover:border-ink/30 transition-colors cursor-pointer group"
                @click="$router.push(`/seller/orders/${order.order_id}`)"
              >
                <div class="flex items-center justify-between gap-3">
                  <div class="flex items-center gap-3 min-w-0">
                    <div class="w-10 h-10 bg-cream overflow-hidden flex-shrink-0 flex items-center justify-center">
                      <img v-if="listingImages[order.listing_id]" :src="listingImages[order.listing_id]" class="w-full h-full object-cover" />
                      <span v-else class="text-lg">🛍</span>
                    </div>
                    <div class="min-w-0">
                      <div class="flex items-center gap-2 mb-0.5">
                        <span class="font-mono text-xs text-muted">#{{ order.order_id }}</span>
                        <span class="status-badge text-xs font-mono" :class="badgeClass(order.status)">{{ order.status }}</span>
                      </div>
                      <p class="font-display font-semibold text-sm group-hover:text-accent transition-colors truncate">
                        {{ order.order_details || `Listing #${order.listing_id}` }}
                      </p>
                    </div>
                  </div>
                  <p class="font-display font-bold text-accent flex-shrink-0">${{ order.agreed_price }}</p>
                </div>
              </div>

              <div v-if="orders.length === 0" class="text-center py-12">
                <p class="font-display font-semibold text-lg text-ink/30">No orders yet</p>
              </div>
            </div>
          </div>

          <!-- Recent Disputes -->
          <div>
            <div class="mb-4 flex items-center justify-between">
              <h2 class="font-display font-bold text-xl">Recent Disputes</h2>
              <router-link to="/seller/disputes" class="text-sm font-mono text-accent hover:underline">View all →</router-link>
            </div>

            <div class="space-y-3">
              <div
                v-for="dispute in recentDisputes"
                :key="dispute.id"
                class="bg-white border border-ink/10 p-4 hover:border-ink/30 transition-colors cursor-pointer group"
                @click="$router.push(`/seller/disputes/${dispute.id}`)"
              >
                <div class="flex items-center justify-between gap-3">
                  <div class="min-w-0">
                    <div class="flex items-center gap-2 mb-0.5">
                      <span class="font-mono text-xs text-muted">{{ dispute.id }}</span>
                      <span
                        class="inline-flex items-center px-2 py-0.5 text-xs font-mono font-medium uppercase tracking-wider"
                        :class="disputeBadgeClass(dispute.status)"
                      >{{ dispute.status }}</span>
                    </div>
                    <p class="font-display font-semibold text-sm group-hover:text-accent transition-colors truncate">
                      {{ dispute.listing }}
                    </p>
                    <p class="text-xs text-muted font-mono mt-0.5">{{ dispute.buyerName }} · {{ dispute.raisedAt }}</p>
                  </div>
                  <div class="text-right flex-shrink-0">
                    <p class="font-display font-bold text-accent">${{ dispute.amount }}</p>
                    <p class="text-xs font-mono mt-0.5" :class="dispute.sellerResponse ? 'text-sage' : 'text-amber-400'">
                      {{ dispute.sellerResponse ? 'Responded' : 'Needs response' }}
                    </p>
                  </div>
                </div>
              </div>

              <div v-if="sellerDisputes.length === 0" class="text-center py-12">
                <p class="font-display font-semibold text-lg text-ink/30">No disputes</p>
                <p class="text-xs text-muted font-mono mt-1">Great — no disputes raised against your listings!</p>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import SellerNavbar from '../../components/SellerNavbar.vue'
import { mockSeller, mockDisputes } from '../../data/mockData.js'
import { getOrdersBySeller } from '../../services/api.js'
import { getMergedDisputes } from '../../data/disputeStore.js'

const outsystemsListingUrl = 'https://personal-8vnud50n.outsystemscloud.com/Listing/rest/Listing/listing/'

const orders  = ref([])
const loading = ref(true)
const listingImages = ref({})
const sellerDisputes = ref([])

const pendingCount   = computed(() => orders.value.filter(o => o.status === 'RESERVED').length)
const completedCount = computed(() => orders.value.filter(o => o.status === 'COMPLETED').length)
const disputedCount  = computed(() => orders.value.filter(o => o.status === 'DISPUTED').length)
const revenue        = computed(() => orders.value.filter(o => o.status === 'COMPLETED').reduce((sum, o) => sum + (o.agreed_price || 0), 0))
const recentOrders   = computed(() => orders.value.slice(0, 5))
const recentDisputes = computed(() => sellerDisputes.value.slice(0, 3))
const pendingDisputeCount = computed(() => sellerDisputes.value.filter(d => d.status === 'PENDING').length)

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

  // Load disputes for this seller
  const allDisputes = getMergedDisputes(mockDisputes)
  sellerDisputes.value = allDisputes.filter(d =>
    d.sellerName === mockSeller.name ||
    d.sellerName === `Seller #${mockSeller.id}`
  )
})

function badgeClass(status) {
  return {
    RESERVED:  'bg-amber-100 text-amber-700',
    COMPLETED: 'bg-sage/20 text-sage',
    DISPUTED:  'bg-red-100 text-red-700',
    REFUNDED:  'bg-purple-100 text-purple-700',
  }[status] || 'bg-cream text-ink'
}

function disputeBadgeClass(status) {
  return {
    PENDING:  'bg-amber-100 text-amber-700',
    APPROVED: 'bg-sage/20 text-sage',
    REJECTED: 'bg-red-100 text-red-600',
  }[status] || 'bg-ink/10 text-slate'
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-SG', { day: 'numeric', month: 'short', year: 'numeric' })
}
</script>
